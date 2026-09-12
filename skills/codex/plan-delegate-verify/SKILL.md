---
name: plan-delegate-verify
description: >
  Persistently orchestrate substantial or long-running work through a recursive,
  cost-aware Plan → Delegate → Verify → Re-plan loop. Once explicitly activated,
  keep this workflow active until the user's global objective is DONE, BLOCKED,
  CANCELLED, or redirected. Delegate material execution, route each lot to the
  cheapest suitable model and reasoning effort, verify results with evidence,
  escalate only when needed, and continuously re-plan after each material wave.
---

# Persistent Plan, Delegate, Verify

Use this skill only when the user explicitly requests multi-agent orchestration,
for example “plan, delegate, and verify”, “use subagents”, or equivalent wording.

Once activated, this skill applies to the **entire global objective**. Do not
silently stop using it after the first plan, first wave, milestone, context
compaction, or initial agent budget.

## Non-negotiable loop

For as long as the objective is not `DONE`, `BLOCKED`, or `CANCELLED`:

1. **ASSESS** verified progress and remaining work.
2. **PLAN** the next bounded execution horizon.
3. **ROUTE** each material lot to the cheapest reliable model/effort.
4. **DELEGATE** material execution to child agents.
5. **VERIFY** every material result against evidence.
6. **INTEGRATE** verified outputs and invalidate stale evidence if needed.
7. **RE-PLAN** before starting further material work.

After every material execution wave, `VERIFY → UPDATE STATE → RE-PLAN` is
mandatory.

The orchestrator owns planning, routing, dependency management, integration,
verification strategy, escalation, telemetry, and final accountability.
Material execution remains delegated except for trivial glue, deterministic
checks, tiny mechanical corrections, or work that cannot technically be
delegated.

Do not absorb remaining work merely because only a few tasks remain.

## Rolling-horizon planning

Do not create a speculative many-hour implementation plan unless dependencies
are unusually stable.

Maintain a high-level roadmap, but plan detailed lots only far enough ahead to
create a useful next execution horizon.

For every material lot define:

- mission;
- exact inputs and relevant predecessor outputs;
- write scope;
- 2–4 observable done criteria;
- dependencies;
- routing profile;
- verification route;
- risk: `standard | demanding | critical`.

Prevent concurrent agents from modifying overlapping resources unless explicitly
safe.

## Discover runtime capabilities

Before routing, inspect the collaboration tool contract and determine:

- available child-agent models and declared profiles;
- supported reasoning-effort levels;
- concurrency limits and occupied slots;
- clean-context / fork requirements;
- relevant file/tool access.

Never invent model names, effort levels, concurrency, tokens, or credits.

Build a capability ladder dynamically from the current runtime, conceptually:

`efficient → balanced → strong → frontier`

Treat model capability and reasoning effort as separate dimensions.

For detailed routing and escalation rules, read
`references/routing.md` **only when needed**.

## Routing objective

Choose the route that minimizes expected total cost, not merely first-call cost:

`execution + verification + P(failure) × rework + P(undetected failure) × consequence`

Prefer the weakest configuration expected to pass reliably, but use a stronger
first pass when cheap failure would invalidate expensive downstream work.

Do not route all lots to one model by default.

## Delegation

Use dependency-aware waves and parallelize only independent work.

Executor prompts must be self-contained and include:

- mission;
- exact inputs / source paths;
- allowed write scope;
- done criteria;
- constraints and relevant repository instructions;
- required evidence / tests;
- instruction to preserve unrelated user changes;
- instruction not to spawn further subagents.

Prefer fresh child contexts when supported and useful for routing.

## Verification

Treat every executor response as a claim until checked.

Use deterministic evidence first: tests, lint, typecheck, builds, diffs, runtime
probes, queries, calculations, schema validation, rendered outputs, or equivalent.

Use semantic verification only when deterministic evidence is insufficient.
When economically justified, use an independent verifier with stronger
capability than the executor. Batch compatible verification when it remains
clear and independently attributable.

For detailed verification policy, read
`references/verification.md` **only when needed**.

Every required criterion must end as `PASS`, `FAIL`, or `BLOCKED` with evidence.

## Failure handling

Diagnose before escalating:

- specification/input failure → fix specification/input; do not upgrade blindly;
- narrow instruction miss → retry same model and effort with failure evidence;
- reasoning-depth failure → raise effort one supported step;
- capability failure → raise model capability one step;
- context failure → use a fresh context before upgrading.

Change one dimension at a time unless evidence clearly justifies more.

Allow at most two targeted rework attempts for the same diagnosed failure mode
before re-planning the lot or decomposition.

Material failure is also a re-planning trigger when it changes assumptions,
dependencies, architecture, or downstream validity.

## Cycle-local budgets

For long objectives, agent-turn budgets are per cycle, not global.

A new re-planning cycle receives a new local budget. Maintain cumulative counts
for reporting, but never interpret exhaustion of one cycle budget as permission
for the orchestrator to execute all remaining work directly.

## Persistent state

Maintain a compact orchestration ledger containing:

- global objective and acceptance criteria;
- verified milestones;
- current lots and dependencies;
- material discoveries / changed assumptions;
- relevant artifacts and verification evidence;
- routing / retry / escalation history;
- remaining objective.

At epoch boundaries compact the ledger rather than carrying full child-agent
transcripts forward.

## Telemetry

Record every child-agent planner, executor, verifier, retry, and replacement
through `scripts/telemetry.py` when writable temporary storage is available.
Keep telemetry outside the user's repository unless explicitly requested.

Telemetry must track routing behavior without inflating the model context.

For the schema, commands, metrics, anomaly rules, and final audit format, read
`references/telemetry.md` **when initializing telemetry, when diagnosing routing,
or when producing a usage report**.

Never estimate platform token/credit usage. Record it only if explicitly exposed
by the runtime.

## Mandatory continuation gate

After every material wave ask:

**Are all global acceptance criteria satisfied by verified evidence?**

- If `NO`: the next material action is `RE-PLAN`, not local implementation.
- If `YES`: run final system-level verification against the original objective.
- If final verification finds missing material work: return to
  `ASSESS → PLAN → ROUTE → DELEGATE → VERIFY`.

## Completion

Terminate only as:

- `DONE`: every global acceptance criterion has verified evidence;
- `BLOCKED`: a concrete missing dependency, authority, resource, external state,
  or user decision prevents further progress;
- `CANCELLED`: the user explicitly stops or redirects the objective.

At termination, produce the actual outcome first, then a concise Routing Audit
from telemetry. If exact token/credit data was unavailable, say so explicitly.

The persistent operating invariant is:

> **Assess → Plan → Route → Delegate → Verify → Integrate → Measure → Re-plan**
>
> until the complete user objective is demonstrably finished.
