---
name: plan-delegate-verify
description: Persistently orchestrate substantial, decomposable work through a recursive, cost-aware Plan → Delegate → Verify → Re-plan loop built on the Claude Code Agent tool. Once explicitly activated, keep the workflow active until the user's global objective is DONE, BLOCKED, or CANCELLED. Define independent work lots with verifiable completion criteria, budget child-agent turns per cycle, route each lot across the Claude model tiers exposed by the Agent tool, execute in parallel within actual concurrency limits, verify every result against primary evidence, escalate one dimension at a time, and re-plan after every material wave. Use only when the user explicitly asks to “plan, delegate, and verify,” “orchestrate this task with subagents,” “use parallel agents,” « planifie, délègue et vérifie », « orchestre cette tâche avec des sous-agents », or otherwise explicitly requests multi-agent orchestration. Do not trigger merely because a task is large.
---

# Persistent Plan, Delegate, Verify

Use this skill only when the user explicitly requests multi-agent orchestration.

Once activated, this skill applies to the **entire global objective**. Do not
silently stop using it after the first plan, first wave, milestone, context
compaction, or exhausted cycle budget.

## Gate the workflow

Use this workflow only for an objective with at least two material work streams
that can run independently or in dependency-ordered waves. Prefer direct
execution for short, tightly coupled, sequential, or single-voice creative work.

When an explicitly requested orchestration is unsuitable, do not silently skip
it. Start the response with:
`Orchestration note: this task is too small or tightly coupled to benefit from subagents.`
Then execute directly unless the user insists on delegation.

## Non-negotiable loop

For as long as the objective is not `DONE`, `BLOCKED`, or `CANCELLED`:

1. **ASSESS** verified progress and remaining work from the ledger.
2. **PLAN** the next bounded execution horizon and its cycle budget.
3. **ROUTE** each material lot to the cheapest reliable model tier.
4. **DELEGATE** material execution to fresh child agents.
5. **VERIFY** every material result against primary evidence.
6. **INTEGRATE** verified outputs and invalidate stale downstream evidence.
7. **MEASURE** the cycle in telemetry and update the ledger.
8. **RE-PLAN** before starting further material work.

After every material execution wave, `VERIFY → UPDATE LEDGER → RE-PLAN` is
mandatory.

The orchestrator owns planning, routing, dependency management, integration,
verification strategy, escalation, telemetry, and final accountability.
Material execution stays delegated. The orchestrator may directly perform only
trivial glue, deterministic checks, tiny mechanical corrections, or work that
cannot technically be delegated. Record each such direct execution in telemetry
with role `orchestrator` and `--material yes`.

Never absorb remaining work because only a few lots remain, because the cycle
budget is exhausted, or because two reworks failed. Those are re-planning
triggers, not permission to execute locally.

## Discover runtime capabilities

Before the first routing decision, read what the session actually exposes:

- the `model` overrides accepted by the Agent tool, typically `haiku`, `sonnet`,
  `opus`, and `fable`, forming the capability ladder
  `haiku (efficient) → sonnet (balanced) → opus (strong) → fable (frontier)`;
- the specialized `subagent_type` profiles (for example `Explore` for read-only
  search, `Plan` for planning) and their declared tools;
- the concurrency limit for background subagents and how many slots are already
  occupied; the orchestrator counts against any limit that includes it;
- that a new Agent spawn starts **cold** with no conversation history, and that
  `SendMessage` continues a previously spawned agent with its context intact.

Claude Code exposes **no per-call reasoning-effort control** on the Agent tool.
Routing therefore has a single axis, the model tier. Never invent an effort
level, a model identifier, a concurrency figure, or token/credit usage. When the
session exposes a reduced model set, inherit it and state the limitation in the
plan.

Do not use the `Workflow` tool inside this skill. The loop relies on per-lot
diagnosis and incremental rework that a scripted workflow cannot provide.

For detailed routing and escalation rules, read `references/routing.md`
**only when a routing decision is non-obvious or a lot fails**.

## Rolling-horizon planning

Maintain a high-level roadmap, but plan detailed lots only far enough ahead to
form one useful execution horizon. Do not write a speculative many-hour plan
unless dependencies are unusually stable.

Resolve the specification first: inspect files, tools, and repository guidance
before asking the user. Ask only for decisions that cannot be inferred safely
and that would materially change the result. Define the objective, constraints,
non-goals, expected artifacts, global acceptance criteria, and any destructive,
sensitive, or external action requiring approval.

Plan locally by default. Spawn a fresh planning agent (`subagent_type: "Plan"`
when its profile fits, strongest suitable model) only:

- at the start, when the objective is high-consequence or hard to reverse, when
  ambiguity spans several lots, or when the first local planning pass cannot
  produce independent lots with testable criteria;
- later, when a material discovery invalidates the architecture, assumptions,
  or decomposition.

Routine re-planning between cycles is orchestrator work, not a child turn.

For every material lot define:

1. **Mission** — one action-oriented sentence.
2. **Inputs** — exact files, data, tools, and relevant predecessor outputs.
3. **Write scope** — exact files or artifacts the agent may create or edit.
4. **Done criteria** — two to four observable pass/fail checks.
5. **Dependencies** — predecessor lots or `none`.
6. **Routing** — selected model tier and `subagent_type`, with a short reason.
7. **Verification route** — deterministic checks, orchestrator review, or
   independent verifier.
8. **Risk** — `standard | demanding | critical`, with the reason.

Create the fewest useful lots. Merge lots that must edit the same lines; never
let concurrent agents modify overlapping resources. Preserve pre-existing user
changes.

Show the lot plan and routing before delegation. Continue automatically unless
an unresolved decision materially changes the result, the next action is
destructive or externally consequential, or the user asked for plan approval.
Track the orchestration with `TaskCreate` / `TaskUpdate`, keeping at most one
step `in_progress`.

## Cycle-local budgets

Budgets are per re-planning cycle, not global. Let `N` be the number of
execution lots in the cycle; every spawn, `SendMessage` follow-up, or
replacement counts as one child-agent turn. Classify the cycle by its highest
lot risk:

- **Standard:** at most `N + 1` turns; no dedicated planner or verifier; no
  explicitly pinned top-tier model.
- **Demanding:** at most `N + min(2, N) + 1` turns; at most one planner or
  verifier; at most one top-tier (`opus`/`fable`) child turn.
- **Critical:** at most `N + min(2, N) + 2` turns; at most one planner, one
  batched verifier, and two top-tier child turns.

State the budget in the plan. Spend the reserve only on failed criteria or
evidence gaps. A new cycle receives a new budget; keep cumulative counts for the
final audit. When a cycle budget is exhausted with required work remaining,
re-plan the horizon or obtain user approval for additional turns. Never treat
exhaustion as permission for the orchestrator to execute the rest.

## Routing objective

Minimize expected total cost, not first-call cost:

`execution + verification + P(failure) × rework + P(undetected failure) × consequence`

| Lot profile | Starting tier |
|---|---|
| Mechanical, deterministic, easily checked | `haiku` |
| Standard analysis, bounded code, structured writing | `sonnet` (default) |
| Ambiguous, nuanced, multi-file, or costly to redo | `opus` |
| Critical, irreversible, or on the dependency bottleneck | strongest available |

Prefer a stronger first pass when a cheap failure would invalidate expensive
downstream work. Do not upgrade solely because the input is large. Do not route
every lot to one tier by default.

## Delegation

Spawn executors as fresh agents, never `fork`, so irrelevant history is
excluded and the `model` override applies. Issue the Agent calls for all
independent lots of a wave in a single turn so they run in parallel, up to the
free capacity; run dependency-aware waves beyond that.

Every executor prompt is self-contained and includes:

- mission;
- absolute input paths or exact source identifiers;
- allowed write scope;
- done criteria;
- required output format: actual deliverable or exact artifact paths plus test
  evidence, not a summary;
- relevant constraints and repository instructions;
- an instruction to preserve unrelated user changes;
- an instruction not to spawn further subagents.

Do not leak the expected answer, tentative verdicts, or another executor's
reasoning. Do not duplicate an executor's work while it runs. You are
re-invoked when a background agent finishes; do not poll.

## Verification

Treat every executor response as a claim until checked. Use deterministic
evidence first: tests, lint, typecheck, builds, diffs, runtime probes, queries,
recalculations, schema validation, rendered outputs. The orchestrator performs
baseline verification for every lot and tries to falsify each criterion.

Spawn a fresh independent verifier only when a failure could cause serious
data loss, security exposure, financial harm, unsafe behavior, or an
irreversible external effect; when a critical criterion cannot be verified from
primary evidence with high confidence; or when sources or results materially
conflict. Route the verifier one tier above the executor. Give it the
specification, artifacts, sources, criteria, and deterministic evidence; omit
executor rationale and tentative verdicts. Batch compatible lots when criteria
stay independently attributable.

For detailed verification policy, read `references/verification.md`
**only when deterministic evidence is insufficient or work is critical**.

Every required criterion ends as `PASS`, `FAIL`, or `BLOCKED` with evidence.

## Failure handling

Diagnose before spending a child turn, then change one dimension at a time:

- **specification/input failure** → fix the specification, dependency, or
  source; reroute without upgrading;
- **narrow instruction miss** → `SendMessage` to the same agent, same model,
  with the failed criterion and evidence;
- **context failure** → fresh spawn, same model;
- **capability failure** → fresh spawn, one tier up.

Allow at most two targeted rework attempts for the same diagnosed failure mode.
After that, re-plan the lot or its decomposition; do not complete it locally.
A failure that changes assumptions, dependencies, architecture, or downstream
validity is a re-planning trigger. After every correction, rerun affected checks
and invalidate downstream `PASS` results that depended on the failed work.

## Persistent ledger

Maintain `ledger.md` in the session scratchpad, next to the telemetry file,
never in the user's repository. It is the source of truth across cycles and
context compactions; `TaskCreate` entries are only the visible progress view.
It holds:

- global objective and acceptance criteria;
- verified milestones with evidence pointers;
- current lots, dependencies, and cycle budget;
- material discoveries and changed assumptions;
- routing, retry, and escalation history;
- remaining objective.

Update it at every cycle boundary. After any context compaction, re-read it
before acting. Compact the ledger rather than carrying child transcripts
forward.

## Telemetry

When Python and writable storage are available, record every child-agent turn
(planner, executor, verifier, rework, replacement) and every orchestrator
material execution through `scripts/telemetry.py`, stored in the session
scratchpad. Read `references/telemetry.md` **when initializing telemetry, when
diagnosing routing, or when producing the final audit**.

The Agent tool exposes no token or credit usage. Never estimate it.

## Mandatory continuation gate

After every material wave ask:

**Are all global acceptance criteria satisfied by verified evidence?**

- `NO` → the next material action is `RE-PLAN`, not local implementation.
- `YES` → run final system-level verification against the original objective.
  If it finds missing material work, return to `ASSESS`.

## Completion

Terminate only as:

- `DONE`: every global acceptance criterion has verified evidence;
- `BLOCKED`: a concrete missing dependency, authority, resource, external
  state, or user decision prevents progress;
- `CANCELLED`: the user explicitly stops or redirects the objective.

Report in the user's language. Lead with the actual outcome: what was produced
or changed with exact paths, which criteria passed with evidence, which lots
were reworked and how routing escalated, planned versus consumed budget per
cycle and cumulatively, and any open or blocked item. Then append the concise
Routing Audit from telemetry, stating that platform token/credit usage is not
exposed by the Agent tool.

Never claim completion while a required criterion is failed, blocked without
disclosure, or unverified.

The persistent operating invariant is:

> **Assess → Plan → Route → Delegate → Verify → Integrate → Measure → Re-plan**
>
> until the complete user objective is demonstrably finished.
