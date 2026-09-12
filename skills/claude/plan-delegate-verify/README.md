# `plan-delegate-verify` (Claude Code, v3)

**Compatibility: Claude Code only.** No external prerequisite: the skill relies
on the Agent tool, `SendMessage`, task tracking, and optionally Python 3 for
telemetry, all available in the session.

Native Claude counterpart of the Codex skill of the same name and version.
Structure, loop, and rigor are identical; only platform mechanics differ.

## What changed in v3

The skill is no longer a one-shot three-phase workflow. Once explicitly
activated it stays in charge of the **whole objective** through a persistent
loop:

> Assess → Plan → Route → Delegate → Verify → Integrate → Measure → Re-plan

until the objective is `DONE`, `BLOCKED`, or `CANCELLED`. After every material
wave a continuation gate forces a re-plan; the orchestrator never absorbs the
remaining work, even when a cycle budget is exhausted or two reworks failed.

## Trigger

Only on an explicit request for multi-agent orchestration, for example:

```text
Plan, delegate, and verify this migration with subagents.
```

```text
Planifie, délègue et vérifie cette tâche avec des agents en parallèle.
```

A short, sequential, or tightly coupled task is executed directly, with an
explicit `Orchestration note` instead of artificial lots.

## Claude Code mechanics

| Concern | Codex v3 | Claude v3 |
|---|---|---|
| Routing axes | model capability + reasoning effort | **model tier only** (`haiku → sonnet → opus → fable`) |
| Rework ladder | retry → effort up → model up → fresh context | fix spec → `SendMessage` same agent → fresh spawn same tier → fresh spawn next tier |
| Budget | per cycle, no top-tier cap | per cycle, formulas `N+1` / `N+min(2,N)+1` / `N+min(2,N)+2` with an `opus`/`fable` cap |
| Planner | unspecified | fresh `Plan` agent at start under conditions, or on assumption rupture |
| Verifier | one class above executor when semantic | Claude triggers (critical, unverifiable, conflicting) with one tier above executor |
| State | in-context ledger | `ledger.md` file in the session scratchpad, re-read after context compaction |
| Telemetry | JSONL in system temp | JSONL in session scratchpad, no effort or token fields, `rework_mode` and `subagent_type` added |
| Executor spawn | fresh context when supported | always fresh, never `fork` |
| `Workflow` tool | n/a | **excluded** in this version |

## Layout

```text
plan-delegate-verify/
├── SKILL.md                    # the loop, always loaded
├── README.md
├── references/
│   ├── routing.md              # read on non-obvious routing or lot failure
│   ├── verification.md         # read when deterministic evidence is insufficient
│   └── telemetry.md            # read at telemetry init, diagnosis, final audit
└── scripts/
    └── telemetry.py            # stdlib-only JSONL recorder and report
```

## Telemetry quick start

```bash
python ~/.claude/skills/plan-delegate-verify/scripts/telemetry.py init --dir <scratchpad>
python ~/.claude/skills/plan-delegate-verify/scripts/telemetry.py record --file <path> --cycle 1 --lot L1 --role executor --model sonnet --result PASS --material yes
python ~/.claude/skills/plan-delegate-verify/scripts/telemetry.py report --file <path>
```

The report flags under-routing, over-routing, orchestration collapse, rework
discipline breaches, and top-tier cap overruns. It never estimates tokens or
credits: the Agent tool does not expose them.

## Guarantees

- No agent replaces the orchestrator's accountability.
- Delegated prompts are self-contained and bound their write scope exactly.
- Every required criterion ends as `PASS`, `FAIL`, or `BLOCKED` with evidence.
- Reworks are diagnosed, one dimension at a time, at most two per failure mode.
- Material work is never completed by the orchestrator; direct executions are
  recorded and visible in the audit.
- Nothing is declared `DONE` while a required criterion is unverified.

## Later

The Claude Code `Workflow` tool (scripted parallel agents with structured
output) is a candidate for running purely parallel waves once telemetry has
stabilized. It is deliberately out of scope for v3 because it does not support
per-lot `SendMessage` rework or adaptive routing inside a wave.
