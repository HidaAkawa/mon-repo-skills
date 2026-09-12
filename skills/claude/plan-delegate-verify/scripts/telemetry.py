#!/usr/bin/env python3
"""Lightweight append-only routing telemetry for plan-delegate-verify (Claude Code).

Stores JSONL in the session scratchpad (or the system temp directory) and
produces compact aggregate reports. Standard-library only.

Claude Code specifics: a single routing axis (model tier), no reasoning-effort
field, no platform token/credit usage, and an explicit rework mode that
distinguishes SendMessage follow-ups from fresh spawns.
"""

from __future__ import annotations

import argparse
import json
import tempfile
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROLES = ("planner", "executor", "verifier", "rework", "replacement", "orchestrator")
EXEC_ROLES = {"executor", "rework", "replacement"}
RESULTS = ("PASS", "FAIL", "BLOCKED", "CANCELLED", "UNKNOWN")
CAPABILITIES = ("efficient", "balanced", "strong", "frontier", "unknown")
TOP_TIERS = {"strong", "frontier"}
MODEL_TIER = {"haiku": "efficient", "sonnet": "balanced", "opus": "strong", "fable": "frontier"}
MATERIAL = ("yes", "no", "unknown")
REWORK_MODES = ("sendmessage", "fresh_same_tier", "tier_up", "spec_fix")
ESCALATION_REASONS = (
    "instruction_miss", "context_failure", "capability_failure",
    "specification_failure", "other",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_path(base_dir: str | None) -> Path:
    base = Path(base_dir).expanduser() if base_dir else Path(tempfile.gettempdir())
    base = base / "plan-delegate-verify"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{uuid.uuid4().hex}.jsonl"


def append_event(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")


def load_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"Telemetry file not found: {path}")
    events = []
    with path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise SystemExit(f"Invalid JSONL at line {lineno}: {e}") from e
    return events


def pct(n: int | float, d: int | float) -> float | None:
    return None if not d else round(100.0 * n / d, 1)


def tier_of(model: str | None, explicit: str | None) -> str:
    if explicit and explicit != "unknown":
        return explicit
    return MODEL_TIER.get((model or "").lower(), "unknown")


def aggregate(events: list[dict[str, Any]]) -> dict[str, Any]:
    by_model = Counter()
    by_capability = Counter()
    by_role = Counter()
    by_subagent = Counter()
    by_result = Counter()
    by_rework_mode = Counter()
    escalation_matrix = Counter()
    escalation_reasons = Counter()
    top_tier_by_cycle = Counter()
    turns_by_cycle = Counter()

    lot_events: dict[str, list[dict[str, Any]]] = defaultdict(list)
    cycles_with_material = set()
    cycles_with_delegated_material = set()
    orchestrator_material = 0
    child_turns = 0

    for e in events:
        role = e.get("role") or "unknown"
        cap = tier_of(e.get("model"), e.get("capability"))
        by_role[role] += 1
        by_result[e.get("result") or "UNKNOWN"] += 1
        cycle = e.get("cycle")

        if role != "orchestrator":
            child_turns += 1
            by_model[e.get("model") or "unknown"] += 1
            by_capability[cap] += 1
            by_subagent[e.get("subagent_type") or "unknown"] += 1
            if cycle is not None:
                turns_by_cycle[str(cycle)] += 1
                if cap in TOP_TIERS:
                    top_tier_by_cycle[str(cycle)] += 1

        if e.get("lot"):
            lot_events[str(e["lot"])].append(e)

        if e.get("rework_mode"):
            by_rework_mode[e["rework_mode"]] += 1
        if e.get("escalation_reason"):
            escalation_reasons[e["escalation_reason"]] += 1
        src, dst = e.get("escalation_from"), e.get("escalation_to")
        if src and dst:
            escalation_matrix[f"{src} -> {dst}"] += 1

        material = e.get("material", "unknown")
        if material == "yes" and cycle is not None:
            cycles_with_material.add(str(cycle))
            if role in EXEC_ROLES:
                cycles_with_delegated_material.add(str(cycle))
        if role == "orchestrator" and material == "yes":
            orchestrator_material += 1

    completed_lots = 0
    lots_with_exec = 0
    first_pass_pass = 0
    retried_lots = 0
    escalated_lots = 0
    over_reworked_lots = []
    replacement_without_sendmessage = []
    first_pass_by_model = defaultdict(lambda: [0, 0])

    for lot, es in lot_events.items():
        execs = [e for e in es if e.get("role") in EXEC_ROLES]
        if not execs:
            continue
        lots_with_exec += 1
        if any(e.get("result") == "PASS" for e in execs):
            completed_lots += 1

        first = execs[0]
        passed_first = first.get("result") == "PASS"
        fm = first.get("model") or "unknown"
        first_pass_by_model[fm][1] += 1
        if passed_first:
            first_pass_pass += 1
            first_pass_by_model[fm][0] += 1

        reworks = execs[1:]
        if reworks:
            retried_lots += 1
        if len(reworks) > 2:
            over_reworked_lots.append(lot)
        if any(e.get("escalation_from") and e.get("escalation_to") for e in reworks):
            escalated_lots += 1
        modes = [e.get("rework_mode") for e in reworks]
        if any(e.get("role") == "replacement" for e in reworks) and "sendmessage" not in modes:
            replacement_without_sendmessage.append(lot)

    def success_map(d):
        return {
            k: {"passed": v[0], "total": v[1], "rate_pct": pct(v[0], v[1])}
            for k, v in sorted(d.items())
        }

    top_tier = sum(by_capability[t] for t in TOP_TIERS)

    report = {
        "events": len(events),
        "child_turns": child_turns,
        "lots": lots_with_exec,
        "completed_lots": completed_lots,
        "by_model": dict(by_model),
        "by_capability": dict(by_capability),
        "by_role": dict(by_role),
        "by_subagent_type": dict(by_subagent),
        "by_result": dict(by_result),
        "by_cycle": {
            c: {"child_turns": turns_by_cycle[c], "top_tier_turns": top_tier_by_cycle[c]}
            for c in sorted(turns_by_cycle, key=lambda x: (len(x), x))
        },
        "first_pass": {
            "passed": first_pass_pass,
            "total": lots_with_exec,
            "rate_pct": pct(first_pass_pass, lots_with_exec),
            "by_model": success_map(first_pass_by_model),
        },
        "retry": {
            "lots": retried_lots,
            "rate_pct": pct(retried_lots, lots_with_exec),
            "by_mode": dict(by_rework_mode),
            "over_reworked_lots": over_reworked_lots,
            "replacement_without_sendmessage": replacement_without_sendmessage,
        },
        "escalation": {
            "lots": escalated_lots,
            "rate_pct": pct(escalated_lots, lots_with_exec),
            "matrix": dict(escalation_matrix),
            "reasons": dict(escalation_reasons),
        },
        "delegation": {
            "cycles_with_material": len(cycles_with_material),
            "cycles_with_delegated_material": len(cycles_with_delegated_material),
            "continuity_pct": pct(len(cycles_with_delegated_material), len(cycles_with_material)),
            "orchestrator_material_events": orchestrator_material,
        },
        "top_tier_share_pct": pct(top_tier, child_turns),
        "platform_usage": "not exposed by the Claude Code Agent tool",
    }
    report["diagnostics"] = diagnostics(report)
    return report


def diagnostics(r: dict[str, Any]) -> list[str]:
    out = []
    fp = r["first_pass"]["rate_pct"]
    er = r["escalation"]["rate_pct"]
    dc = r["delegation"]["continuity_pct"]

    if fp is not None and fp < 65:
        out.append("Possible under-routing: overall first-pass success is below 65%.")
    if er is not None and er > 25:
        out.append("Possible under-routing: more than 25% of lots escalated.")
    if dc is not None and dc < 90:
        out.append("Possible orchestration collapse: delegation continuity is below 90%.")
    if r["delegation"]["orchestrator_material_events"] > 0:
        out.append(
            f"Orchestration collapse risk: {r['delegation']['orchestrator_material_events']} "
            "orchestrator material-execution event(s); material work should remain delegated."
        )
    for m, stats in r["first_pass"]["by_model"].items():
        if stats["total"] >= 3 and stats["rate_pct"] is not None and stats["rate_pct"] < 60:
            out.append(
                f"Possible under-routing for model '{m}': first-pass success "
                f"{stats['rate_pct']}% across {stats['total']} lots; consider starting similar lots one tier up."
            )
    for lot in r["retry"]["over_reworked_lots"]:
        out.append(f"Rework discipline: lot '{lot}' exceeded two rework attempts; it should have been re-planned.")
    for lot in r["retry"]["replacement_without_sendmessage"]:
        out.append(f"Rework discipline: lot '{lot}' spawned a replacement without trying a SendMessage rework first.")
    for c, s in r["by_cycle"].items():
        if s["top_tier_turns"] > 2:
            out.append(f"Budget: cycle {c} used {s['top_tier_turns']} top-tier turns, above the critical cap of 2.")
    if not out:
        out.append("No obvious routing anomaly detected from the recorded telemetry.")
    return out


def print_report(r: dict[str, Any]) -> None:
    print("ROUTING AUDIT")
    print("=" * 60)
    print(f"Events: {r['events']}  | Child turns: {r['child_turns']}  | "
          f"Lots: {r['lots']}  | Completed: {r['completed_lots']}")
    print()

    def section(title: str, data: dict[str, Any]):
        if not data:
            return
        print(title)
        print("-" * len(title))
        for k, v in sorted(data.items(), key=lambda kv: (-kv[1], kv[0]) if isinstance(kv[1], int) else kv[0]):
            print(f"{k:28} {v}")
        print()

    section("By model", r["by_model"])
    section("By tier", r["by_capability"])
    section("By role", r["by_role"])
    section("By subagent_type", r["by_subagent_type"])

    print("By cycle")
    print("-" * 8)
    for c, s in r["by_cycle"].items():
        print(f"cycle {c:<6} child turns {s['child_turns']:<4} top-tier {s['top_tier_turns']}")
    print()

    fp = r["first_pass"]
    print("Routing quality")
    print("-" * 15)
    print(f"First-pass success: {fp['passed']}/{fp['total']} ({fp['rate_pct']}%)")
    print(f"Retry rate: {r['retry']['rate_pct']}%  modes: {r['retry']['by_mode']}")
    print(f"Escalation rate: {r['escalation']['rate_pct']}%  reasons: {r['escalation']['reasons']}")
    print(f"Top-tier share of child turns: {r['top_tier_share_pct']}%")
    print()

    section("Escalation matrix", r["escalation"]["matrix"])

    d = r["delegation"]
    print("Delegation")
    print("-" * 10)
    print(f"Continuity: {d['cycles_with_delegated_material']}/{d['cycles_with_material']} "
          f"material cycles ({d['continuity_pct']}%)")
    print(f"Orchestrator material events: {d['orchestrator_material_events']}")
    print()

    print("Platform usage")
    print("-" * 14)
    print(f"Token/credit consumption: {r['platform_usage']}.")
    print()

    print("Diagnostics")
    print("-" * 11)
    for item in r["diagnostics"]:
        print(f"- {item}")


def cmd_init(args):
    path = Path(args.file).expanduser() if args.file else default_path(args.dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    print(path)


def cmd_record(args):
    if args.role in EXEC_ROLES | {"planner", "verifier"} and not args.model:
        raise SystemExit("--model is required for child-agent roles")
    if args.role in {"rework", "replacement"} and not args.rework_mode:
        raise SystemExit("--rework-mode is required for rework/replacement events")
    event = {
        "timestamp": now(),
        "cycle": args.cycle,
        "lot": args.lot,
        "role": args.role,
        "category": args.category,
        "risk": args.risk,
        "material": args.material,
        "model": args.model,
        "capability": tier_of(args.model, args.capability) if args.model else None,
        "subagent_type": args.subagent_type,
        "initial_model": args.initial_model,
        "result": args.result,
        "verification": args.verification,
        "rework_mode": args.rework_mode,
        "escalation_from": args.escalation_from,
        "escalation_to": args.escalation_to,
        "escalation_reason": args.escalation_reason,
        "routing_reason": args.routing_reason,
        "note": args.note,
    }
    event = {k: v for k, v in event.items() if v is not None}
    append_event(Path(args.file).expanduser(), event)


def cmd_report(args):
    r = aggregate(load_events(Path(args.file).expanduser()))
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print_report(r)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("init", help="Create an empty telemetry JSONL file.")
    s.add_argument("--file", help="Optional explicit JSONL path.")
    s.add_argument("--dir", help="Base directory (use the session scratchpad); defaults to the system temp dir.")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("record", help="Append one telemetry event.")
    s.add_argument("--file", required=True)
    s.add_argument("--cycle", type=int)
    s.add_argument("--lot")
    s.add_argument("--role", required=True, choices=ROLES)
    s.add_argument("--category")
    s.add_argument("--risk", choices=("standard", "demanding", "critical"))
    s.add_argument("--material", default="unknown", choices=MATERIAL)
    s.add_argument("--model", help="Exact Agent tool model override: haiku | sonnet | opus | fable")
    s.add_argument("--capability", default="unknown", choices=CAPABILITIES,
                   help="Only needed for a model the script does not know.")
    s.add_argument("--subagent-type")
    s.add_argument("--initial-model")
    s.add_argument("--result", default="UNKNOWN", choices=RESULTS)
    s.add_argument("--verification", choices=("none", "deterministic", "semantic", "both"))
    s.add_argument("--rework-mode", choices=REWORK_MODES)
    s.add_argument("--escalation-from")
    s.add_argument("--escalation-to")
    s.add_argument("--escalation-reason", choices=ESCALATION_REASONS)
    s.add_argument("--routing-reason")
    s.add_argument("--note")
    s.set_defaults(func=cmd_record)

    s = sub.add_parser("report", help="Aggregate telemetry.")
    s.add_argument("--file", required=True)
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_report)

    return p


def main():
    args = parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
