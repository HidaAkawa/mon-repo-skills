#!/usr/bin/env python3
"""Lightweight append-only routing telemetry for plan-delegate-verify.

Stores JSONL outside the repository by default and produces compact aggregate
reports. Standard-library only.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROLES = ("planner", "executor", "verifier", "rework", "replacement")
RESULTS = ("PASS", "FAIL", "BLOCKED", "CANCELLED", "UNKNOWN")
CAPABILITIES = ("efficient", "balanced", "strong", "frontier", "unknown")
MATERIAL = ("yes", "no", "unknown")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_path() -> Path:
    base = Path(tempfile.gettempdir()) / "plan-delegate-verify"
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


def aggregate(events: list[dict[str, Any]]) -> dict[str, Any]:
    by_model = Counter()
    by_capability = Counter()
    by_effort = Counter()
    by_role = Counter()
    by_result = Counter()
    escalation_matrix = Counter()

    token_totals = Counter()
    credit_total = 0.0
    credits_seen = False

    lot_events: dict[str, list[dict[str, Any]]] = defaultdict(list)
    cycles_with_material = set()
    cycles_with_delegated_material = set()
    orchestrator_material = 0

    for e in events:
        by_model[e.get("model") or "unknown"] += 1
        by_capability[e.get("capability") or "unknown"] += 1
        by_effort[e.get("effort") or "unknown"] += 1
        by_role[e.get("role") or "unknown"] += 1
        by_result[e.get("result") or "UNKNOWN"] += 1

        if e.get("lot"):
            lot_events[str(e["lot"])].append(e)

        src, dst = e.get("escalation_from"), e.get("escalation_to")
        if src and dst:
            escalation_matrix[f"{src} -> {dst}"] += 1

        for key in ("input_tokens", "cached_input_tokens", "output_tokens", "total_tokens"):
            val = e.get(key)
            if isinstance(val, (int, float)):
                token_totals[key] += val

        val = e.get("credits")
        if isinstance(val, (int, float)):
            credits_seen = True
            credit_total += float(val)

        material = e.get("material", "unknown")
        cycle = e.get("cycle")
        if material == "yes" and cycle is not None:
            cycles_with_material.add(str(cycle))
            if e.get("role") in {"executor", "rework", "replacement"}:
                cycles_with_delegated_material.add(str(cycle))

        if e.get("role") == "orchestrator" and material == "yes":
            orchestrator_material += 1

    completed_lots = 0
    first_pass_pass = 0
    retried_lots = 0
    escalated_lots = 0
    first_pass_by_model = defaultdict(lambda: [0, 0])
    first_pass_by_cap = defaultdict(lambda: [0, 0])

    for lot, es in lot_events.items():
        execs = [e for e in es if e.get("role") in {"executor", "rework", "replacement"}]
        if not execs:
            continue
        final_results = [e.get("result") for e in execs]
        if any(r == "PASS" for r in final_results):
            completed_lots += 1

        first = execs[0]
        passed_first = first.get("result") == "PASS"
        if passed_first:
            first_pass_pass += 1

        fm = first.get("model") or "unknown"
        fc = first.get("capability") or "unknown"
        first_pass_by_model[fm][1] += 1
        first_pass_by_cap[fc][1] += 1
        if passed_first:
            first_pass_by_model[fm][0] += 1
            first_pass_by_cap[fc][0] += 1

        if len(execs) > 1:
            retried_lots += 1
        if any(e.get("escalation_from") and e.get("escalation_to") for e in execs[1:]):
            escalated_lots += 1

    def success_map(d):
        return {
            k: {"passed": v[0], "total": v[1], "rate_pct": pct(v[0], v[1])}
            for k, v in sorted(d.items())
        }

    premium = by_capability["strong"] + by_capability["frontier"]

    report = {
        "events": len(events),
        "completed_lots": completed_lots,
        "by_model": dict(by_model),
        "by_capability": dict(by_capability),
        "by_effort": dict(by_effort),
        "by_role": dict(by_role),
        "by_result": dict(by_result),
        "first_pass": {
            "passed": first_pass_pass,
            "total": completed_lots,
            "rate_pct": pct(first_pass_pass, completed_lots),
            "by_model": success_map(first_pass_by_model),
            "by_capability": success_map(first_pass_by_cap),
        },
        "retry": {
            "lots": retried_lots,
            "rate_pct": pct(retried_lots, completed_lots),
        },
        "escalation": {
            "lots": escalated_lots,
            "rate_pct": pct(escalated_lots, completed_lots),
            "matrix": dict(escalation_matrix),
        },
        "delegation": {
            "cycles_with_material": len(cycles_with_material),
            "cycles_with_delegated_material": len(cycles_with_delegated_material),
            "continuity_pct": pct(
                len(cycles_with_delegated_material), len(cycles_with_material)
            ),
            "orchestrator_material_events": orchestrator_material,
        },
        "premium_capability_share_pct": pct(premium, len(events)),
        "platform_usage": {
            **dict(token_totals),
            "credits": round(credit_total, 4) if credits_seen else None,
            "available": bool(token_totals or credits_seen),
        },
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
        out.append("Possible under-routing: more than 25% of completed lots escalated.")
    if dc is not None and dc < 90:
        out.append("Possible orchestration collapse: delegation continuity is below 90%.")
    if r["delegation"]["orchestrator_material_events"] > 0:
        out.append("Review orchestrator material-execution events; material work should normally remain delegated.")

    for cap, stats in r["first_pass"]["by_capability"].items():
        if stats["total"] >= 3 and stats["rate_pct"] is not None and stats["rate_pct"] < 60:
            out.append(
                f"Possible under-routing for capability '{cap}': "
                f"first-pass success {stats['rate_pct']}% across {stats['total']} lots."
            )

    if not out:
        out.append("No obvious routing anomaly detected from the recorded telemetry.")
    return out


def print_report(r: dict[str, Any]) -> None:
    print("ROUTING AUDIT")
    print("=" * 60)
    print(f"Events: {r['events']}  | Completed lots: {r['completed_lots']}")
    print()

    def section(title: str, data: dict[str, Any]):
        print(title)
        print("-" * len(title))
        for k, v in sorted(data.items(), key=lambda kv: (-kv[1], kv[0]) if isinstance(kv[1], int) else kv[0]):
            print(f"{k:24} {v}")
        print()

    section("By model", r["by_model"])
    section("By capability", r["by_capability"])
    section("By effort", r["by_effort"])
    section("By role", r["by_role"])

    fp = r["first_pass"]
    print("Routing quality")
    print("-" * 15)
    print(f"First-pass success: {fp['passed']}/{fp['total']} ({fp['rate_pct']}%)")
    print(f"Retry rate: {r['retry']['rate_pct']}%")
    print(f"Escalation rate: {r['escalation']['rate_pct']}%")
    print(f"Premium capability share: {r['premium_capability_share_pct']}%")
    print()

    if r["escalation"]["matrix"]:
        section("Escalation matrix", r["escalation"]["matrix"])

    d = r["delegation"]
    print("Delegation")
    print("-" * 10)
    print(
        f"Continuity: {d['cycles_with_delegated_material']}/"
        f"{d['cycles_with_material']} cycles ({d['continuity_pct']}%)"
    )
    print(f"Orchestrator material events: {d['orchestrator_material_events']}")
    print()

    pu = r["platform_usage"]
    print("Platform usage")
    print("-" * 14)
    if pu["available"]:
        for k, v in pu.items():
            if k != "available" and v is not None:
                print(f"{k:24} {v}")
    else:
        print("Exact token/credit consumption was not exposed in recorded events.")
    print()

    print("Diagnostics")
    print("-" * 11)
    for item in r["diagnostics"]:
        print(f"- {item}")


def cmd_init(args):
    path = Path(args.file).expanduser() if args.file else default_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    print(path)


def cmd_record(args):
    event = {
        "timestamp": now(),
        "cycle": args.cycle,
        "epoch": args.epoch,
        "lot": args.lot,
        "role": args.role,
        "category": args.category,
        "risk": args.risk,
        "material": args.material,
        "model": args.model,
        "capability": args.capability,
        "effort": args.effort,
        "initial_model": args.initial_model,
        "initial_effort": args.initial_effort,
        "result": args.result,
        "verification": args.verification,
        "retry": args.retry,
        "escalation_from": args.escalation_from,
        "escalation_to": args.escalation_to,
        "escalation_reason": args.escalation_reason,
        "routing_reason": args.routing_reason,
        "input_tokens": args.input_tokens,
        "cached_input_tokens": args.cached_input_tokens,
        "output_tokens": args.output_tokens,
        "total_tokens": args.total_tokens,
        "credits": args.credits,
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
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("init", help="Create an empty telemetry JSONL file.")
    s.add_argument("--file", help="Optional explicit JSONL path.")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("record", help="Append one telemetry event.")
    s.add_argument("--file", required=True)
    s.add_argument("--cycle", type=int)
    s.add_argument("--epoch", type=int)
    s.add_argument("--lot")
    s.add_argument("--role", required=True,
                   choices=ROLES + ("orchestrator",))
    s.add_argument("--category")
    s.add_argument("--risk", choices=("standard", "demanding", "critical"))
    s.add_argument("--material", default="unknown", choices=MATERIAL)
    s.add_argument("--model")
    s.add_argument("--capability", default="unknown", choices=CAPABILITIES)
    s.add_argument("--effort")
    s.add_argument("--initial-model")
    s.add_argument("--initial-effort")
    s.add_argument("--result", default="UNKNOWN", choices=RESULTS)
    s.add_argument("--verification",
                   choices=("none", "deterministic", "semantic", "both"))
    s.add_argument("--retry", type=int, default=0)
    s.add_argument("--escalation-from")
    s.add_argument("--escalation-to")
    s.add_argument("--escalation-reason")
    s.add_argument("--routing-reason")
    s.add_argument("--input-tokens", type=int)
    s.add_argument("--cached-input-tokens", type=int)
    s.add_argument("--output-tokens", type=int)
    s.add_argument("--total-tokens", type=int)
    s.add_argument("--credits", type=float)
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
