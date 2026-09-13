"""Unit tests for telemetry.py (v4).

Run from the skill directory:
    python -m unittest discover -s scripts -p "test_*.py"
"""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import telemetry as t  # noqa: E402


def ev(**kw):
    base = {"timestamp": "2026-09-13T12:00:00+00:00", "material": "yes", "result": "PASS"}
    base.update(kw)
    return base


class CoalesceTests(unittest.TestCase):
    def test_explicit_open_close_is_one_turn(self):
        events = [
            ev(cycle=1, lot="L1", role="executor", model="opus", phase="open", result="UNKNOWN"),
            ev(cycle=1, lot="L1", role="executor", model="opus", phase="close", result="PASS",
               timestamp="2026-09-13T12:10:00+00:00"),
        ]
        turns, merged = t.coalesce_turns(events)
        self.assertEqual(merged, 1)
        self.assertEqual(len(turns), 1)
        self.assertEqual(turns[0]["result"], "PASS")
        self.assertEqual(turns[0]["opened_at"], "2026-09-13T12:00:00+00:00")
        self.assertEqual(turns[0]["closed_at"], "2026-09-13T12:10:00+00:00")

    def test_legacy_unknown_then_result_is_one_turn(self):
        events = [
            ev(cycle=2, lot="L5", role="executor", model="opus", result="UNKNOWN"),
            ev(cycle=2, lot="L5", role="executor", model="opus", result="PASS"),
        ]
        turns, merged = t.coalesce_turns(events)
        self.assertEqual((len(turns), merged), (1, 1))

    def test_legacy_distinct_turns_stay_distinct(self):
        events = [
            ev(cycle=1, lot="L1", role="executor", model="sonnet", result="FAIL"),
            ev(cycle=1, lot="L1", role="rework", model="sonnet", result="PASS", rework_mode="sendmessage"),
        ]
        turns, merged = t.coalesce_turns(events)
        self.assertEqual((len(turns), merged), (2, 0))

    def test_close_without_open_counts_as_turn(self):
        turns, merged = t.coalesce_turns([ev(cycle=1, lot="L1", role="executor", model="haiku", phase="close")])
        self.assertEqual((len(turns), merged), (1, 0))


class DelegationTests(unittest.TestCase):
    def test_authorized_only_cycle_leaves_denominator(self):
        events = [
            ev(cycle=0, lot="L0", role="orchestrator", exec_class="authorized", exec_reason="single-browser"),
            ev(cycle=1, lot="L1", role="executor", model="sonnet"),
            ev(cycle=1, lot="L7", role="orchestrator", exec_class="authorized", exec_reason="user-gate"),
        ]
        r = t.aggregate(events)
        d = r["delegation"]
        self.assertEqual(d["continuity_pct"], 100.0)
        self.assertEqual(d["cycles_authorized_only"], ["0"])
        self.assertEqual(d["fallback_events"], 0)
        self.assertEqual(d["orchestrator_by_class"], {"authorized": 2})
        self.assertFalse(any(x.startswith(("Possible orchestration collapse", "Orchestration collapse risk")) for x in r["diagnostics"]))

    def test_fallback_counts_as_collapse(self):
        events = [
            ev(cycle=1, lot="L1", role="executor", model="sonnet"),
            ev(cycle=2, lot="L2", role="orchestrator", exec_class="fallback", exec_reason="fallback"),
        ]
        r = t.aggregate(events)
        self.assertEqual(r["delegation"]["continuity_pct"], 50.0)
        self.assertTrue(any("fallback orchestrator" in x for x in r["diagnostics"]))

    def test_legacy_unclassified_is_conservative_and_flagged(self):
        events = [ev(cycle=1, lot="L0", role="orchestrator")]
        r = t.aggregate(events)
        self.assertEqual(r["delegation"]["unclassified_events"], 1)
        self.assertEqual(r["delegation"]["continuity_pct"], 0.0)
        self.assertTrue(any("Classification gap" in x for x in r["diagnostics"]))


class BudgetTests(unittest.TestCase):
    def test_cap_formula(self):
        self.assertEqual(t.top_tier_cap(0), 2)
        self.assertEqual(t.top_tier_cap(1), 2)
        self.assertEqual(t.top_tier_cap(3), 4)

    def test_three_critical_lots_allow_three_opus_turns(self):
        events = [ev(cycle=2, lot=f"L{i}", role="executor", model="opus", risk="critical") for i in range(3)]
        r = t.aggregate(events)
        c = r["by_cycle"]["2"]
        self.assertEqual((c["critical_lots"], c["top_tier_cap"], c["top_tier_turns"]), (3, 4, 3))
        self.assertFalse(any(x.startswith("Budget") for x in r["diagnostics"]))

    def test_cap_overrun_flagged(self):
        events = [ev(cycle=1, lot=f"L{i}", role="executor", model="opus", risk="standard") for i in range(3)]
        r = t.aggregate(events)
        self.assertTrue(any("above its cap of 2" in x for x in r["diagnostics"]))


class BlockAndExclusivityTests(unittest.TestCase):
    def test_permission_block_status(self):
        events = [ev(cycle=1, lot="L4", role="executor", model="opus", result="BLOCKED", block_kind="permission")]
        r = t.aggregate(events)
        self.assertEqual(r["lot_status"]["L4"], "BLOCKED-PERMISSION")
        self.assertEqual(r["blocks"]["permission_blocked_lots"], ["L4"])
        self.assertTrue(any("BLOCKED-PERMISSION" in x for x in r["diagnostics"]))

    def test_plain_block_status(self):
        r = t.aggregate([ev(cycle=1, lot="L4", role="executor", model="opus", result="BLOCKED")])
        self.assertEqual(r["lot_status"]["L4"], "BLOCKED")
        self.assertEqual(r["blocks"]["by_kind"], {"unspecified": 1})

    def test_exclusivity_breach_detected_inside_window(self):
        events = [
            ev(cycle=3, lot="L13", role="orchestrator", exec_class="authorized", exec_reason="user-gate",
               phase="open", result="UNKNOWN", exclusive=["app:main"], timestamp="2026-09-13T13:00:00+00:00"),
            ev(cycle=3, lot="L9", role="executor", model="sonnet", writes=["app:main"],
               timestamp="2026-09-13T13:05:00+00:00"),
            ev(cycle=3, lot="L13", role="orchestrator", exec_class="authorized", exec_reason="user-gate",
               phase="close", result="PASS", timestamp="2026-09-13T13:30:00+00:00"),
        ]
        r = t.aggregate(events)
        self.assertEqual(len(r["exclusivity"]["breaches"]), 1)
        self.assertIn("L9", r["exclusivity"]["breaches"][0])
        self.assertEqual(r["exclusivity"]["resources"], {"app:main": ["L13"]})

    def test_no_breach_outside_window(self):
        events = [
            ev(cycle=3, lot="L13", role="orchestrator", exec_class="authorized", exec_reason="user-gate",
               phase="open", result="UNKNOWN", exclusive="app:main", timestamp="2026-09-13T13:00:00+00:00"),
            ev(cycle=3, lot="L13", role="orchestrator", exec_class="authorized", exec_reason="user-gate",
               phase="close", result="PASS", timestamp="2026-09-13T13:30:00+00:00"),
            ev(cycle=3, lot="L9", role="executor", model="sonnet", writes="app:main",
               timestamp="2026-09-13T13:35:00+00:00"),
        ]
        self.assertEqual(t.aggregate(events)["exclusivity"]["breaches"], [])


class CliTests(unittest.TestCase):
    def _run(self, *argv):
        args = t.parser().parse_args(list(argv))
        buf = io.StringIO()
        with redirect_stdout(buf):
            args.func(args)
        return buf.getvalue()

    def test_record_and_report_roundtrip_with_new_fields(self):
        with tempfile.TemporaryDirectory() as d:
            f = str(Path(d) / "t.jsonl")
            self._run("init", "--file", f)
            self._run("record", "--file", f, "--cycle", "1", "--lot", "L1", "--phase", "open",
                      "--role", "executor", "--model", "sonnet", "--material", "yes", "--exclusive", "repo:main")
            self._run("record", "--file", f, "--cycle", "1", "--lot", "L1", "--phase", "close",
                      "--role", "executor", "--model", "sonnet", "--material", "yes", "--result", "PASS")
            self._run("record", "--file", f, "--cycle", "1", "--lot", "L2", "--role", "orchestrator",
                      "--material", "yes", "--exec-class", "authorized", "--exec-reason", "single-browser",
                      "--result", "PASS")
            self._run("record", "--file", f, "--cycle", "1", "--lot", "L3", "--role", "executor",
                      "--model", "sonnet", "--material", "yes", "--result", "BLOCKED", "--block-kind", "permission")
            out = json.loads(self._run("report", "--file", f, "--json"))
            self.assertEqual(out["child_turns"], 2)
            self.assertEqual(out["merged_close_events"], 1)
            self.assertEqual(out["lot_status"], {"L1": "DONE", "L3": "BLOCKED-PERMISSION"})
            self.assertEqual(out["delegation"]["orchestrator_by_reason"], {"single-browser": 1})
            lines = Path(f).read_text(encoding="utf-8").splitlines()
            self.assertEqual(json.loads(lines[0])["exclusive"], ["repo:main"])
            text = self._run("report", "--file", f)
            self.assertIn("ROUTING AUDIT", text)

    def test_orchestrator_material_requires_exec_class(self):
        with tempfile.TemporaryDirectory() as d:
            f = str(Path(d) / "t.jsonl")
            with self.assertRaises(SystemExit):
                self._run("record", "--file", f, "--role", "orchestrator", "--material", "yes")

    def test_block_kind_requires_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            f = str(Path(d) / "t.jsonl")
            with self.assertRaises(SystemExit):
                self._run("record", "--file", f, "--role", "executor", "--model", "haiku",
                          "--result", "PASS", "--block-kind", "permission")

    def test_v3_file_still_reports(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "v3.jsonl"
            rows = [
                {"cycle": 1, "lot": "L1", "role": "executor", "model": "sonnet", "material": "yes", "result": "PASS"},
                {"cycle": 1, "lot": "L0", "role": "orchestrator", "model": "fable", "material": "yes", "result": "PASS"},
            ]
            f.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
            out = json.loads(self._run("report", "--file", str(f), "--json"))
            self.assertEqual(out["child_turns"], 1)
            self.assertEqual(out["delegation"]["unclassified_events"], 1)


if __name__ == "__main__":
    unittest.main()
