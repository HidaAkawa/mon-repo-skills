---
name: plan-delegate-verify
description: Orchestrate substantial, decomposable work through a cost-aware plan-delegate-verify workflow that defines independent work lots and verifiable completion criteria, budgets agent turns, routes each lot dynamically across the Claude models exposed by the Agent tool, executes in parallel within actual concurrency limits, and adversarially verifies deliverables with targeted escalation. Use only when the user explicitly asks to “plan, delegate, and verify,” “orchestrate this task with subagents,” “use parallel agents,” « planifie, délègue et vérifie », « orchestre cette tâche avec des sous-agents », or otherwise explicitly requests multi-agent orchestration. Do not trigger merely because a task is large.
---

# Plan, Delegate, Verify

Orchestrate complex work in three phases: create a testable plan, delegate independent lots to calibrated subagents, and verify every result against evidence. Keep ownership of the overall outcome; subagents execute bounded lots rather than replacing orchestration.

## Gate the workflow

Use this workflow only for a task with at least two material work streams that can run independently or in dependency-ordered waves. Prefer direct execution for short, tightly coupled, sequential, or single-voice creative work.

When an explicitly requested orchestration is unsuitable, do not silently skip the requested workflow. Start the response with: `Orchestration note: this task is too small or tightly coupled to benefit from subagents.` Then execute it directly unless the user insists on delegation or explicitly asks for no explanation.

## Phase 1 — Plan

### Resolve the specification

Inspect available files, tools, repository guidance, and other discoverable facts before asking the user. Ask only for decisions that cannot be inferred safely and that would materially change the result.

Define:

- the objective and scope;
- constraints and non-goals;
- expected artifacts or changes;
- acceptance criteria for the complete task;
- any sensitive, destructive, or external actions requiring approval.

### Discover orchestration capacity

Read what the current session actually exposes before assigning subagents. Identify:

- the model overrides available on the Agent tool — typically `haiku`, `sonnet`, `opus`, and `fable` — and their relative capability tiers (`haiku` fastest and cheapest, `sonnet` the balanced default, `opus` the strongest general model, `fable` the frontier model when exposed);
- that Claude Code exposes **no per-subagent reasoning-effort control** — routing therefore has a single axis, the model tier, so never invent an effort level to pin;
- the actual concurrency limit for background subagents and how many slots are currently occupied; the orchestrator itself counts against any limit that includes it;
- that subagents run in the background by default, and that a new Agent spawn starts **cold** with no conversation history, whereas `subagent_type: "fork"` inherits the parent context — executors use a fresh spawn, not a fork.

Never invent a model identifier. When the session exposes a different or reduced model set, inherit what is available and state the limitation in the plan.

### Select planning and verification capacity

Plan locally with the orchestrator by default. Do not spawn a planner merely because the orchestrator's exact model cannot be proven.

Spawn a fresh planning agent only when at least one condition holds:

- the task is high-consequence or difficult to reverse;
- ambiguity spans several lots or acceptance criteria remain hard to define;
- the dependency graph requires several waves or long-horizon reasoning;
- the orchestrator's first planning pass cannot produce independent lots with testable criteria.

Use the strongest suitable model for that planner (`opus`, or `fable` when exposed). Prefer the `Plan` subagent type when its profile fits. Use a fresh (non-fork) spawn, pass a self-contained brief, and review and own the proposed plan.

### Divide work into lots

Create the fewest useful lots. Make each lot independently executable and independently verifiable. Merge lots that need to edit the same lines or make tightly coupled decisions; otherwise sequence them in dependency-ordered waves.

For every lot, record:

1. **Mission** — one action-oriented sentence.
2. **Inputs** — exact files, data, links, tools, and assumptions.
3. **Write scope** — exact files or artifacts the subagent may create or edit.
4. **Done criteria** — two to four observable pass/fail checks.
5. **Dependencies** — predecessor lots or `none`.
6. **Routing** — selected model with a short reason.
7. **Risk** — standard or critical, with the reason for criticality.

Prevent concurrent subagents from editing overlapping files. Assign one owner, divide disjoint ranges or files, or serialize the dependent work. Preserve pre-existing user changes.

### Set an agent-turn budget

Classify the overall task as standard, demanding, or critical. Let `N` be the number of execution lots and count every spawn or follow-up as one child-agent turn.

- **Standard:** budget at most `N + 1` child-agent turns; use no dedicated planner or verifier and do not explicitly pin a top-tier model.
- **Demanding:** budget at most `N + min(2, N) + 1` turns; use at most one dedicated planner or verifier and at most one top-tier (`opus`/`fable`) child turn.
- **Critical:** budget at most `N + min(2, N) + 2` turns; use at most one planner, one batched verifier, and two top-tier child turns.

These limits bound orchestration overhead, not executor quality. Route every initial execution lot strongly enough to minimize expected total cost, including use of the strongest suitable model when justified. State the budget in the plan. Spend the reserve only on failed criteria or evidence gaps, not general polishing. When the budget is exhausted, complete the correction or verification locally when safe; otherwise obtain user approval before adding child-agent turns. Never stop with a required criterion silently unverified.

### Route dynamically

Rank only the models exposed by the current session. Minimize expected total cost: `first-pass cost + failure probability × downstream rework cost`. Prefer a stronger first pass when a cheap failure would invalidate dependent lots or require expensive repetition.

| Lot profile | Starting model |
|---|---|
| Mechanical, deterministic, easily checked | `haiku` |
| Standard analysis, bounded code, structured writing | `sonnet` (default) |
| Ambiguous, nuanced, multi-step, or costly to redo | `opus` |
| Critical, high-risk, or on the dependency bottleneck | strongest available (`opus`, or `fable` when exposed) |

Treat these as capability tiers, not fixed guarantees. Prefer a specialized `subagent_type` (for example `Explore` for read-only search) when its declared profile is a better fit than the general-purpose agent. Do not upgrade solely because the input is large when the work and criteria are mechanical.

### Present and advance the plan

Show the lot plan and routing before delegation. Continue automatically unless:

- an unresolved decision materially changes the result;
- the next action is destructive, sensitive, or externally consequential;
- the user requested plan approval;
- applicable instructions require approval.

Use `TaskCreate` / `TaskUpdate` to track the orchestration and keep at most one step marked `in_progress`.

## Phase 2 — Delegate

### Build autonomous prompts

Spawn executors as fresh (non-fork) agents so irrelevant conversation history is excluded and the `model` routing applies. Pass the selected `model` on the Agent call. Make each prompt self-contained. Include:

- the mission;
- absolute input paths or exact source identifiers;
- the allowed write scope;
- the done criteria;
- the required output or handoff format;
- relevant constraints and repository instructions;
- a warning to preserve unrelated user changes;
- an instruction not to spawn further subagents;
- an instruction to return the actual deliverable or exact artifact paths plus test evidence, not a generic summary.

Do not leak the expected answer, hidden evaluation conclusions, or another executor's reasoning into the prompt.

### Execute in waves

Launch independent lots concurrently — issue their Agent calls in a single turn so they run in parallel in the background — up to the actual free-agent capacity. Account for the orchestrator in limits that include it. When lots exceed capacity, run dependency-aware waves and reuse freed slots.

Keep delegation centralized. Do not duplicate an executor's work while it runs. Perform only orchestration, dependency preparation, or unrelated integration work.

Track agents and wait efficiently for results; you are re-invoked when a background subagent finishes, so do not poll. Send concise progress updates during long runs without narrating unchanged status.

### Collect evidence

Treat agent messages as claims until checked. Record for each lot:

- produced or changed artifacts;
- tests or checks the executor ran;
- unresolved assumptions or blockers;
- the exact agent configuration used (model and `subagent_type`).

## Phase 3 — Verify

### Verify adversarially

Check every done criterion against primary evidence. Inspect produced files, recalculate values, compare against sources, run relevant tests, and open rendered outputs when layout matters. Never accept “looks good” or the executor's summary as proof.

For each criterion, record:

- `PASS` with the evidence that proves it;
- `FAIL` with the observed mismatch;
- `BLOCKED` with the missing authority, input, or external state.

Try to falsify the deliverable: ask what observable evidence would prove the criterion failed, then perform that check.

### Add independent verification when warranted

Have the orchestrator perform the baseline verification for every lot. Do not spawn an independent verifier merely because a lot was reworked.

Spawn a fresh independent verifier only when:

- a failure could cause serious data loss, security exposure, financial harm, unsafe behavior, or an irreversible external effect;
- the orchestrator cannot verify a critical criterion from primary evidence with high confidence;
- sources or verification results materially conflict.

Batch compatible critical lots into one verifier turn when the combined context remains clear. Use the strongest suitable model (`opus`, or `fable` when exposed) with a fresh (non-fork) spawn.

Give the verifier the specification, artifacts, sources, and criteria, but omit the executor's rationale and the orchestrator's tentative verdict. Ask for criterion-by-criterion findings with evidence. Adjudicate conflicts by checking primary evidence directly.

### Rework failures

Allow at most two targeted rework attempts per lot.

Diagnose the failure before spending another child-agent turn:

- **Specification or input failure:** correct the specification, dependency, or source first; do not upgrade the model.
- **Narrow instruction miss:** follow up with the same agent via `SendMessage` (its context is intact), keeping the same model, and pass the failed criterion and evidence.
- **Insufficient capability or reasoning depth:** escalate to the next more capable model (`haiku` → `sonnet` → `opus` → strongest available).

Use the smallest intervention that addresses the diagnosed cause. Spawn a fresh replacement only when a fresh context or a different model is materially useful. After two failed reworks, complete the lot directly when safe and feasible; otherwise report the concrete blocker. Do not hide an unresolved failure.

Apply a narrow, purely mechanical correction directly when a new agent round would be disproportionate. Record the correction and verify it afterward.

Re-run affected tests and re-check downstream lots after every correction.

## Report the outcome

Return the result in the user's language. Lead with the outcome, then state:

- what was produced or changed, with exact paths or links;
- which verification checks passed and the supporting evidence;
- which lots were reworked and how routing escalated;
- the planned and consumed child-agent-turn budget, including top-tier turns;
- any remaining blocked or open item;
- any dynamic-routing limitation encountered.

Never claim completion while a required criterion is failed, blocked without disclosure, or unverified.
