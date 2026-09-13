# `plan-delegate-verify` (Claude Code, v4)

**Compatibility: Claude Code only.** No external prerequisite: the skill relies
on the Agent tool, `SendMessage`, task tracking, and optionally Python 3 for
telemetry, all available in the session.

Native Claude counterpart of the Codex skill of the same name and version.
Structure, loop, and rigor are identical; only platform mechanics differ.

## What changed in v4

Post-mortem of a real production session (see `CHANGELOG.md`):

- **authorized orchestrator execution** (single browser, user gate,
  non-delegable tool, trivial glue) is declared in the plan and recorded with
  `--exec-class authorized`; only `fallback` executions count as collapse;
- **authorizations and tools** step in every plan; lot status
  `BLOCKED-PERMISSION`; prompt wording rules for the auto-mode classifier;
- **executor contract**: deliverable or explicit `BLOCKED`, bounded in-turn
  waits, no background monitors;
- **exclusivity windows** on shared resources (`--exclusive`, `--writes`),
  with breach detection in the report;
- top-tier cap per cycle `max(2, C + 1)` for `C` critical lots;
- turns recorded once with `--phase open|close`; legacy files coalesced.

## Since v3

The skill is not a one-shot three-phase workflow. Once explicitly
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

| Concern | Codex v3 | Claude v4 |
|---|---|---|
| Routing axes | model capability + reasoning effort | **model tier only** (`haiku → sonnet → opus → fable`) |
| Rework ladder | retry → effort up → model up → fresh context | fix spec → `SendMessage` same agent → fresh spawn same tier → fresh spawn next tier |
| Budget | per cycle, no top-tier cap | per cycle, formulas `N+1` / `N+min(2,N)+1` / `N+min(2,N)+2` ; top-tier cap `max(2, C+1)` |
| Planner | unspecified | fresh `Plan` agent at start under conditions, or on assumption rupture |
| Verifier | one class above executor when semantic | Claude triggers (critical, unverifiable, conflicting) with one tier above executor |
| State | in-context ledger | `ledger.md` file in the session scratchpad, re-read after context compaction |
| Telemetry | JSONL in system temp | JSONL in session scratchpad; `rework_mode`, `subagent_type`, `phase`, `exec_class`, `block_kind`, `exclusive`, `writes` |
| Orchestrator execution | forbidden | `authorized` (declared reason) or `fallback` (counted as collapse) |
| Shared resources | n/a | exclusivity windows held by a lot until its close event |
| Executor spawn | fresh context when supported | always fresh, never `fork` |
| `Workflow` tool | n/a | **excluded** in this version |

## Layout

```text
plan-delegate-verify/
├── SKILL.md                    # the loop, always loaded
├── README.md
├── CHANGELOG.md
├── references/
│   ├── planning.md             # authorizations step, exclusivity windows, budget with several critical lots
│   ├── executor-contract.md    # prompt contract, bounded waits, classifier-safe wording
│   ├── routing.md              # read on non-obvious routing or lot failure
│   ├── verification.md         # read when deterministic evidence is insufficient
│   └── telemetry.md            # read at telemetry init, diagnosis, final audit
└── scripts/
    ├── telemetry.py            # stdlib-only JSONL recorder and report
    └── test_telemetry.py       # python -m unittest discover -s scripts -p "test_*.py"
```

## Telemetry quick start

```bash
python ~/.claude/skills/plan-delegate-verify/scripts/telemetry.py init --dir <scratchpad>
python ~/.claude/skills/plan-delegate-verify/scripts/telemetry.py record --file <path> --cycle 1 --lot L1 --phase open --role executor --model sonnet --material yes
python ~/.claude/skills/plan-delegate-verify/scripts/telemetry.py record --file <path> --cycle 1 --lot L1 --phase close --role executor --model sonnet --material yes --result PASS
python ~/.claude/skills/plan-delegate-verify/scripts/telemetry.py record --file <path> --cycle 1 --lot L2 --role orchestrator --material yes --exec-class authorized --exec-reason single-browser --result PASS
python ~/.claude/skills/plan-delegate-verify/scripts/telemetry.py report --file <path>
```

The report flags under-routing, over-routing, orchestration collapse (fallback
executions only), rework discipline breaches, top-tier cap overruns,
permission blocks, and exclusivity breaches. It never estimates tokens or
credits: the Agent tool does not expose them.

## Guarantees

- No agent replaces the orchestrator's accountability.
- Delegated prompts are self-contained and bound their write scope exactly.
- Every required criterion ends as `PASS`, `FAIL`, or `BLOCKED` with evidence.
- Reworks are diagnosed, one dimension at a time, at most two per failure mode.
- Material work is never completed by the orchestrator except for declared
  authorized executions; both kinds are recorded and visible in the audit.
- Executors end with a deliverable or an explicit block, never a pending wait.
- A held shared resource is written by nobody else until its lot closes.
- Nothing is declared `DONE` while a required criterion is unverified.

## Later

The Claude Code `Workflow` tool (scripted parallel agents with structured
output) is a candidate for running purely parallel waves once telemetry has
stabilized. It is deliberately out of scope for v4 because it does not support
per-lot `SendMessage` rework or adaptive routing inside a wave.
