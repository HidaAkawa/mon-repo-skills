#!/usr/bin/env python3
"""Lightweight append-only routing telemetry for plan-delegate-verify (Claude Code, v4).

Stores JSONL in the session scratchpad (or the system temp directory) and
produces compact aggregate reports. Standard-library only.

Claude Code specifics: a single routing axis (model tier), no reasoning-effort
field, no platform token/credit usage, and an explicit rework mode that
distinguishes SendMessage follow-ups from fresh spawns.

v4 additions, all optional and backward compatible with v3 files:
- ``exec_class`` / ``exec_reason``: an orchestrator material execution is either
  ``authorized`` (declared in the plan: single browser, user authorization gate,
  non-delegable tool, trivial glue) or ``fallback`` (undeclared absorption of
  delegable work). Only ``fallback`` counts toward orchestration collapse.
  Legacy events without ``exec_class`` are ``unclassified`` and treated as
  fallback, with a dedicated diagnostic asking to classify them.
- ``block_kind``: why a BLOCKED result happened (``permission`` marks the lot
  status BLOCKED-PERMISSION).
- ``exclusive`` / ``writes``: the shared resource a lot holds exclusively, and
  the resources an event writes to. The report flags writes on a resource
  while another lot holds it.
- ``phase``: ``open`` at spawn, ``close`` at result. A close merges into its
  open so one turn is counted once. Legacy files (no phase) get a heuristic:
  a result ``UNKNOWN`` event followed by a same-key event is one turn.
- top-tier cap per cycle = max(2, C + 1) where C is the number of distinct
  critical lots executed by child agents in that cycle.
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
REWORK_MODES = ("sendmessage", "fresh_same_tier", "tier_up", "spec_fix", "reword")
ESCALATION_REASONS = (
    "instruction_miss", "context_failure", "capability_failure",
    "specification_failure", "permission_block", "other",
)
EXEC_CLASSES = ("authorized", "fallback")
EXEC_REASONS = (
    "single-browser", "user-gate", "non-delegable-tool", "trivial-glue", "fallback",
)
BLOCK_KINDS = ("permission", "dependency", "user-decision", "external", "other")
PHASES = ("open", "close")
BASE_TOP_TIER_CAP = 2


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


def top_tier_cap(critical_lots: int) -> int:
    """Cycle cap on opus/fable child turns: max(2, C + 1)."""
    return max(BASE_TOP_TIER_CAP, critical_lots + 1)


def _turn_key(e: dict[str, Any]) -> tuple:
    return (
        str(e.get("cycle")), str(e.get("lot")), e.get("role"),
        e.get("model"), e.get("rework_mode"),
    )


def _as_list(v: Any) -> list[str]:
    if v is None:
        return []
    if isinstance(v, str):
        return [v]
    return [str(x) for x in v]


def coalesce_turns(events: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Merge open/close pairs into single turns, in file order.

    Explicit: ``phase: open`` then ``phase: close`` with the same key.
    Legacy heuristic: an event without phase whose result is UNKNOWN is a
    pending open; the next same-key event without phase closes it.
    Returns (turns, number_of_merged_close_events).
    """
    turns: list[dict[str, Any]] = []
    pending: dict[tuple, dict[str, Any]] = {}
    merged = 0
    for raw in events:
        e = dict(raw)
        key = _turn_key(e)
        phase = e.get("phase")
        if phase == "open":
            e["opened_at"] = e.get("timestamp")
            turns.append(e)
            pending[key] = e
            continue
        if phase == "close":
            target = pending.pop(key, None)
            if target is None:
                turns.append(e)
                continue
            _merge_close(target, e)
            merged += 1
            continue
        # legacy heuristic
        target = pending.get(key)
        if target is not None and target.get("phase") is None:
            pending.pop(key)
            _merge_close(target, e)
            merged += 1
            continue
        turns.append(e)
        if e.get("result", "UNKNOWN") == "UNKNOWN":
            e["opened_at"] = e.get("timestamp")
            pending[key] = e
    return turns, merged


def _merge_close(target: dict[str, Any], close: dict[str, Any]) -> None:
    for k, v in close.items():
        if k in ("phase", "timestamp"):
            continue
        if v is not None:
            target[k] = v
    target["closed_at"] = close.get("timestamp")
    target["phase"] = "closed"


def exclusivity_breaches(turns: list[dict[str, Any]]) -> list[str]:
    """Detect writes on a resource while another lot holds it exclusively.

    Uses opened_at/closed_at when present. A turn without timing holds its
    resource only at its own instant, so single-event lots are not flagged
    unless another lot writes the same resource in the same cycle.
    """
    holds: list[tuple[str, str, str, str | None, str]] = []  # (resource, lot, open, close, cycle)
    for t in turns:
        for r in _as_list(t.get("exclusive")):
            holds.append((r, str(t.get("lot")), t.get("opened_at") or t.get("timestamp") or "",
                          t.get("closed_at") or (None if t.get("opened_at") else t.get("timestamp")),
                          str(t.get("cycle"))))
    out = []
    for t in turns:
        touched = set(_as_list(t.get("writes"))) | set(_as_list(t.get("exclusive")))
        if not touched:
            continue
        at = t.get("opened_at") or t.get("timestamp") or ""
        for r, lot, o, c, cyc in holds:
            if r not in touched or lot == str(t.get("lot")):
                continue
            inside = (o <= at and (c is None or at <= c)) or (c is None and cyc == str(t.get("cycle")))
            if inside:
                out.append(f"'{t.get('lot')}' ({t.get('role')}) wrote '{r}' while '{lot}' held it")
    return sorted(set(out))


def aggregate(events: list[dict[str, Any]]) -> dict[str, Any]:
    turns, merged = coalesce_turns(events)

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
    critical_lots_by_cycle: dict[str, set] = defaultdict(set)
    block_kinds = Counter()
    permission_blocked_lots: list[str] = []
    exec_by_class = Counter()
    exec_by_reason = Counter()
    exclusive_resources: dict[str, set] = defaultdict(set)

    lot_events: dict[str, list[dict[str, Any]]] = defaultdict(list)
    cycles_with_material = set()
    cycles_with_delegated_material = set()
    cycles_with_fallback = set()
    cycles_authorized_only = set()
    orchestrator_material = 0
    fallback_events = 0
    unclassified_events = 0
    child_turns = 0

    for e in turns:
        role = e.get("role") or "unknown"
        cap = tier_of(e.get("model"), e.get("capability"))
        result = e.get("result") or "UNKNOWN"
        by_role[role] += 1
        by_result[result] += 1
        cycle = e.get("cycle")
        cyc = str(cycle) if cycle is not None else None

        if role != "orchestrator":
            child_turns += 1
            by_model[e.get("model") or "unknown"] += 1
            by_capability[cap] += 1
            by_subagent[e.get("subagent_type") or "unknown"] += 1
            if cyc is not None:
                turns_by_cycle[cyc] += 1
                if cap in TOP_TIERS:
                    top_tier_by_cycle[cyc] += 1
                if role in EXEC_ROLES and e.get("risk") == "critical" and e.get("lot"):
                    critical_lots_by_cycle[cyc].add(str(e["lot"]))

        if e.get("lot"):
            lot_events[str(e["lot"])].append(e)

        if e.get("rework_mode"):
            by_rework_mode[e["rework_mode"]] += 1
        if e.get("escalation_reason"):
            escalation_reasons[e["escalation_reason"]] += 1
        src, dst = e.get("escalation_from"), e.get("escalation_to")
        if src and dst:
            escalation_matrix[f"{src} -> {dst}"] += 1

        if result == "BLOCKED":
            kind = e.get("block_kind") or "unspecified"
            block_kinds[kind] += 1
            if kind == "permission" and e.get("lot"):
                permission_blocked_lots.append(str(e["lot"]))

        for r in _as_list(e.get("exclusive")):
            exclusive_resources[r].add(str(e.get("lot")))

        material = e.get("material", "unknown")
        if material == "yes" and cyc is not None:
            cycles_with_material.add(cyc)
            if role in EXEC_ROLES:
                cycles_with_delegated_material.add(cyc)
        if role == "orchestrator" and material == "yes":
            orchestrator_material += 1
            klass = e.get("exec_class") or "unclassified"
            exec_by_class[klass] += 1
            exec_by_reason[e.get("exec_reason") or "unspecified"] += 1
            if klass == "fallback":
                fallback_events += 1
            elif klass == "unclassified":
                unclassified_events += 1
            if klass != "authorized" and cyc is not None:
                cycles_with_fallback.add(cyc)

    # A cycle whose only material work is authorized orchestrator execution
    # does not require delegation and leaves the continuity denominator.
    for cyc in cycles_with_material:
        if cyc not in cycles_with_delegated_material and cyc not in cycles_with_fallback:
            cycles_authorized_only.add(cyc)
    continuity_den = cycles_with_material - cycles_authorized_only
    continuity_num = cycles_with_delegated_material & continuity_den

    completed_lots = 0
    lots_with_exec = 0
    first_pass_pass = 0
    retried_lots = 0
    escalated_lots = 0
    over_reworked_lots = []
    replacement_without_sendmessage = []
    first_pass_by_model = defaultdict(lambda: [0, 0])
    lot_status: dict[str, str] = {}

    for lot, es in lot_events.items():
        execs = [e for e in es if e.get("role") in EXEC_ROLES]
        if not execs:
            continue
        lots_with_exec += 1
        last = execs[-1]
        if any(e.get("result") == "PASS" for e in execs):
            completed_lots += 1
            lot_status[lot] = "DONE"
        elif last.get("result") == "BLOCKED":
            lot_status[lot] = "BLOCKED-PERMISSION" if last.get("block_kind") == "permission" else "BLOCKED"
        else:
            lot_status[lot] = last.get("result") or "UNKNOWN"

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
    cycles_sorted = sorted(turns_by_cycle, key=lambda x: (len(x), x))

    report = {
        "events": len(events),
        "merged_close_events": merged,
        "child_turns": child_turns,
        "lots": lots_with_exec,
        "completed_lots": completed_lots,
        "lot_status": lot_status,
        "by_model": dict(by_model),
        "by_capability": dict(by_capability),
        "by_role": dict(by_role),
        "by_subagent_type": dict(by_subagent),
        "by_result": dict(by_result),
        "by_cycle": {
            c: {
                "child_turns": turns_by_cycle[c],
                "top_tier_turns": top_tier_by_cycle[c],
                "critical_lots": len(critical_lots_by_cycle[c]),
                "top_tier_cap": top_tier_cap(len(critical_lots_by_cycle[c])),
            }
            for c in cycles_sorted
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
            "cycles_authorized_only": sorted(cycles_authorized_only, key=lambda x: (len(x), x)),
            "continuity_pct": pct(len(continuity_num), len(continuity_den)),
            "continuity_basis": f"{len(continuity_num)}/{len(continuity_den)}",
            "orchestrator_material_events": orchestrator_material,
            "orchestrator_by_class": dict(exec_by_class),
            "orchestrator_by_reason": dict(exec_by_reason),
            "fallback_events": fallback_events,
            "unclassified_events": unclassified_events,
        },
        "blocks": {
            "by_kind": dict(block_kinds),
            "permission_blocked_lots": sorted(set(permission_blocked_lots)),
        },
        "exclusivity": {
            "resources": {r: sorted(lots) for r, lots in sorted(exclusive_resources.items())},
            "breaches": exclusivity_breaches(turns),
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
    d = r["delegation"]
    dc = d["continuity_pct"]

    if r.get("merged_close_events"):
        out.append(
            f"Recording: {r['merged_close_events']} close event(s) merged into their open turn; "
            "prefer --phase open/close so turns are counted once."
        )
    if fp is not None and fp < 65:
        out.append("Possible under-routing: overall first-pass success is below 65%.")
    if er is not None and er > 25:
        out.append("Possible under-routing: more than 25% of lots escalated.")
    if dc is not None and dc < 90:
        out.append(
            f"Possible orchestration collapse: delegation continuity is below 90% "
            f"({d['continuity_basis']} cycles requiring delegation)."
        )
    if d["fallback_events"] > 0:
        out.append(
            f"Orchestration collapse risk: {d['fallback_events']} fallback orchestrator "
            "execution(s) of delegable work; material work should remain delegated."
        )
    if d["unclassified_events"] > 0:
        out.append(
            f"Classification gap: {d['unclassified_events']} orchestrator material event(s) without "
            "--exec-class (treated as fallback); record authorized executions with "
            "--exec-class authorized --exec-reason <single-browser|user-gate|non-delegable-tool|trivial-glue>."
        )
    auth = d["orchestrator_by_class"].get("authorized", 0)
    if auth:
        out.append(
            f"Authorized orchestrator executions: {auth} (declared in plan); not counted as collapse."
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
        if s["top_tier_turns"] > s["top_tier_cap"]:
            out.append(
                f"Budget: cycle {c} used {s['top_tier_turns']} top-tier turns, above its cap of "
                f"{s['top_tier_cap']} (max(2, critical lots {s['critical_lots']} + 1))."
            )
    for lot in r["blocks"]["permission_blocked_lots"]:
        out.append(
            f"Permission: lot '{lot}' ended BLOCKED-PERMISSION; add the rule to the "
            "'authorizations and tools' plan step before the next wave."
        )
    for b in r["exclusivity"]["breaches"]:
        out.append(f"Exclusivity breach: {b}.")
    if not out:
        out.append("No obvious routing anomaly detected from the recorded telemetry.")
    return out


def print_report(r: dict[str, Any]) -> None:
    print("ROUTING AUDIT")
    print("=" * 60)
    print(f"Events: {r['events']}  | Child turns: {r['child_turns']}  | "
          f"Lots: {r['lots']}  | Completed: {r['completed_lots']}")
    if r.get("merged_close_events"):
        print(f"(open/close pairs merged: {r['merged_close_events']})")
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
        print(f"cycle {c:<6} child turns {s['child_turns']:<4} top-tier {s['top_tier_turns']}/{s['top_tier_cap']} "
              f"(critical lots {s['critical_lots']})")
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
    print(f"Continuity: {d['continuity_basis']} cycles requiring delegation ({d['continuity_pct']}%)")
    if d["cycles_authorized_only"]:
        print(f"Cycles with authorized orchestrator execution only: {', '.join(d['cycles_authorized_only'])}")
    print(f"Orchestrator material events: {d['orchestrator_material_events']}  "
          f"by class: {d['orchestrator_by_class']}  by reason: {d['orchestrator_by_reason']}")
    print()

    if r["blocks"]["by_kind"] or r["exclusivity"]["resources"]:
        print("Blocks and exclusivity")
        print("-" * 22)
        if r["blocks"]["by_kind"]:
            print(f"BLOCKED by kind: {r['blocks']['by_kind']}  "
                  f"BLOCKED-PERMISSION lots: {r['blocks']['permission_blocked_lots']}")
        for res, lots in r["exclusivity"]["resources"].items():
            print(f"exclusive '{res}': held by {', '.join(lots)}")
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


def build_event(args) -> dict[str, Any]:
    if args.role in EXEC_ROLES | {"planner", "verifier"} and not args.model:
        raise SystemExit("--model is required for child-agent roles")
    if args.role in {"rework", "replacement"} and not args.rework_mode:
        raise SystemExit("--rework-mode is required for rework/replacement events")
    if args.exec_class and args.role != "orchestrator":
        raise SystemExit("--exec-class applies only to role orchestrator")
    if args.role == "orchestrator" and args.material == "yes" and not args.exec_class:
        raise SystemExit("--exec-class authorized|fallback is required for orchestrator material execution")
    if args.exec_class == "authorized" and (not args.exec_reason or args.exec_reason == "fallback"):
        raise SystemExit("--exec-reason single-browser|user-gate|non-delegable-tool|trivial-glue is required with --exec-class authorized")
    if args.block_kind and args.result != "BLOCKED":
        raise SystemExit("--block-kind requires --result BLOCKED")
    event = {
        "timestamp": now(),
        "cycle": args.cycle,
        "lot": args.lot,
        "phase": args.phase,
        "role": args.role,
        "category": args.category,
        "risk": args.risk,
        "material": args.material,
        "model": args.model,
        "capability": tier_of(args.model, args.capability) if args.model else None,
        "subagent_type": args.subagent_type,
        "initial_model": args.initial_model,
        "result": args.result,
        "block_kind": args.block_kind,
        "verification": args.verification,
        "rework_mode": args.rework_mode,
        "escalation_from": args.escalation_from,
        "escalation_to": args.escalation_to,
        "escalation_reason": args.escalation_reason,
        "exec_class": args.exec_class,
        "exec_reason": args.exec_reason,
        "exclusive": args.exclusive or None,
        "writes": args.writes or None,
        "routing_reason": args.routing_reason,
        "note": args.note,
    }
    return {k: v for k, v in event.items() if v is not None}


def cmd_record(args):
    append_event(Path(args.file).expanduser(), build_event(args))


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
    s.add_argument("--phase", choices=PHASES,
                   help="open at spawn, close at result; a close merges into its open (one turn).")
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
    s.add_argument("--block-kind", choices=BLOCK_KINDS,
                   help="With --result BLOCKED; 'permission' marks the lot BLOCKED-PERMISSION.")
    s.add_argument("--verification", choices=("none", "deterministic", "semantic", "both"))
    s.add_argument("--rework-mode", choices=REWORK_MODES)
    s.add_argument("--escalation-from")
    s.add_argument("--escalation-to")
    s.add_argument("--escalation-reason", choices=ESCALATION_REASONS)
    s.add_argument("--exec-class", choices=EXEC_CLASSES,
                   help="Orchestrator material execution: authorized (declared in plan) or fallback.")
    s.add_argument("--exec-reason", choices=EXEC_REASONS)
    s.add_argument("--exclusive", action="append", metavar="RESOURCE",
                   help="Shared resource held exclusively by this lot (repeatable).")
    s.add_argument("--writes", action="append", metavar="RESOURCE",
                   help="Shared resource this turn writes to (repeatable).")
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
