---
name: plan-delegate-verify
description: Persistently orchestrate substantial, decomposable work through a recursive, cost-aware Plan → Delegate → Verify → Re-plan loop built on the Claude Code Agent tool. Once explicitly activated, keep the workflow active until the user's global objective is DONE, BLOCKED, or CANCELLED. Define independent work lots with verifiable completion criteria, declare required authorizations and exclusive resources up front, budget child-agent turns per cycle, route each lot across the Claude model tiers exposed by the Agent tool, execute in parallel within actual concurrency limits, verify every result against primary evidence, escalate one dimension at a time, and re-plan after every material wave. Use only when the user explicitly asks to “plan, delegate, and verify,” “orchestrate this task with subagents,” “use parallel agents,” « planifie, délègue et vérifie », « orchestre cette tâche avec des sous-agents », or otherwise explicitly requests multi-agent orchestration. Do not trigger merely because a task is large.
---

# Persistent Plan, Delegate, Verify (v4)

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

1. **ASSESS** verified progress and remaining work from the ledger. On a
   fresh or resumed objective, start with a parallel read-only discovery wave
   (`Explore` agents) before writing any plan.
2. **PLAN** the next bounded execution horizon, its authorizations, its
   exclusive resources, and its cycle budget.
3. **ROUTE** each material lot to the cheapest reliable model tier.
4. **DELEGATE** material execution to fresh child agents.
5. **VERIFY** every material result against primary evidence replayed by the
   orchestrator.
6. **INTEGRATE** verified outputs and invalidate stale downstream evidence.
7. **MEASURE** the cycle in telemetry and update the ledger.
8. **RE-PLAN** before starting further material work.

After every material execution wave, `VERIFY → UPDATE LEDGER → RE-PLAN` is
mandatory.

The orchestrator owns planning, routing, dependency management, integration,
verification strategy, escalation, telemetry, and final accountability.
Material execution stays delegated, with one explicit exception:

- **Authorized orchestrator execution**: work that cannot be delegated by
  construction. Recognized reasons are `single-browser` (the user's own
  browser session, which agents cannot share), `user-gate` (an act the user
  must authorize at the moment it happens: repository variables, publication
  trigger, production promotion, external forms), `non-delegable-tool`, and
  `trivial-glue`. Declare it in the plan as a lot and record it with
  `--exec-class authorized --exec-reason <reason>`.
- **Fallback execution**: any other orchestrator execution of delegable work.
  Record it with `--exec-class fallback`. It is the only thing the
  `orchestration collapse` diagnostic counts.

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
  `SendMessage` continues a previously spawned agent with its context intact;
- the permission mode and its classifier: in auto mode, some commands and some
  prompt wordings are refused without the user seeing them.

Claude Code exposes **no per-call reasoning-effort control** on the Agent tool.
Routing therefore has a single axis, the model tier. Never invent an effort
level, a model identifier, a concurrency figure, or token/credit usage.

Do not use the `Workflow` tool inside this skill. The loop relies on per-lot
diagnosis and incremental rework that a scripted workflow cannot provide.

For detailed routing and escalation rules, read `references/routing.md`
**only when a routing decision is non-obvious or a lot fails**.

## Rolling-horizon planning

Maintain a high-level roadmap, but plan detailed lots only far enough ahead to
form one useful execution horizon.

Resolve the specification first: inspect files, tools, and repository guidance
before asking the user. Define the objective, constraints, non-goals, expected
artifacts, global acceptance criteria, and any destructive, sensitive, or
external action requiring approval.

Plan locally by default. Spawn a fresh planning agent (`subagent_type: "Plan"`,
strongest suitable model) only at the start of a high-consequence or ambiguous
objective, or when a material discovery invalidates the decomposition.

Every plan carries an **Authorizations and tools** step before its first wave:
the permission rules to request from the user now (SSH hosts, `gh` write
commands, remote scripts), the tools each lot needs, and the prompt wordings to
avoid. Details in `references/planning.md`.

For every material lot define:

1. **Mission** — one action-oriented sentence.
2. **Inputs** — exact files, data, tools, and relevant predecessor outputs.
3. **Write scope** — exact files or artifacts the agent may create or edit.
4. **Done criteria** — two to four observable pass/fail checks.
5. **Dependencies** — predecessor lots or `none`.
6. **Routing** — model tier and `subagent_type`, with a short reason, or
   `orchestrator (authorized: <reason>)`.
7. **Verification route** — deterministic checks, orchestrator review, or
   independent verifier.
8. **Risk** — `standard | demanding | critical`, with the reason.
9. **Exclusive resource** — a shared resource this lot holds while it runs
   (repository, `main` branch, environment), or `none`.

Create the fewest useful lots. Merge lots that must edit the same lines; never
let concurrent agents modify overlapping resources. Preserve pre-existing user
changes.

Show the lot plan, the authorizations, and the routing before delegation.
Continue automatically unless an unresolved decision materially changes the
result, the next action is destructive or externally consequential, or the user
asked for plan approval. Track the orchestration with `TaskCreate` /
`TaskUpdate`, keeping at most one step `in_progress`.

## Exclusivity windows

A lot that declares an exclusive resource **holds** it from its spawn until the
orchestrator records its result. While it is held, no other lot and no
orchestrator action writes to that resource: no merge, no push, no deploy, no
variable change. Lots that would write to a held resource wait for the next
wave. Typical holds: an open approval or promotion pull request holds the
target branch; a server install holds the host; a publication holds the
release channel. Record the hold with `--exclusive <resource>` and other lots'
writes with `--writes <resource>`; the report flags any overlap.

## Cycle-local budgets

Budgets are per re-planning cycle, not global. Let `N` be the number of
execution lots in the cycle and `C` the number of critical lots; every spawn,
`SendMessage` follow-up, or replacement counts as one child-agent turn.
Classify the cycle by its highest lot risk:

- **Standard:** at most `N + 1` turns; no dedicated planner or verifier; no
  explicitly pinned top-tier model.
- **Demanding:** at most `N + min(2, N) + 1` turns; at most one planner or
  verifier; at most one top-tier (`opus`/`fable`) child turn.
- **Critical:** at most `N + min(2, N) + 2` turns; at most one planner and one
  batched verifier; top-tier child turns capped at `max(2, C + 1)`.

Independent critical lots may share a cycle: each gets its own top-tier turn
plus one shared reserve. State `N`, `C`, and the resulting budget in the plan.
Spend the reserve only on failed criteria or evidence gaps. When a budget is
exhausted with required work remaining, re-plan the horizon or obtain user
approval for additional turns. Never treat exhaustion as permission for the
orchestrator to execute the rest.

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
downstream work. Do not upgrade solely because the input is large.

## Delegation

Spawn executors as fresh agents, never `fork`, so irrelevant history is
excluded and the `model` override applies. Issue the Agent calls for all
independent lots of a wave in a single turn so they run in parallel, up to the
free capacity; run dependency-aware waves beyond that.

Every executor prompt is self-contained and includes:

- mission, absolute input paths, allowed write scope, done criteria;
- required output format: the actual deliverable or exact artifact paths plus
  test evidence, never a summary;
- relevant constraints and repository instructions; preserve unrelated user
  changes; do not spawn further subagents;
- the **executor contract**: end with a deliverable or an explicit
  `BLOCKED` report, never with a pending wait; when an external event must
  happen (CI checks, a merge, a deployment), wait for it inside the turn with a
  blocking, time-bounded command, never a background monitor; on a permission
  refusal, report `BLOCKED-PERMISSION` with the exact refused command, never
  work around it.

Word prompts without the classifier's trigger words: name secrets by their
variable names and where they live, never by value or by "token" wording.
Full template in `references/executor-contract.md`.

Do not leak the expected answer, tentative verdicts, or another executor's
reasoning. Do not duplicate an executor's work while it runs. You are
re-invoked when a background agent finishes; do not poll.

## Verification

Treat every executor response as a claim until checked. Use deterministic
evidence first: tests, lint, typecheck, builds, diffs, runtime probes, queries,
recalculations, schema validation, rendered outputs. The orchestrator replays
the decisive check for every lot itself and tries to falsify each criterion.

Spawn a fresh independent verifier only when a failure could cause serious
data loss, security exposure, financial harm, unsafe behavior, or an
irreversible external effect; when a critical criterion cannot be verified from
primary evidence with high confidence; or when sources or results materially
conflict. Route the verifier one tier above the executor and isolate it from
executor rationale. Read `references/verification.md` **only when
deterministic evidence is insufficient or work is critical**.

Every required criterion ends as `PASS`, `FAIL`, or `BLOCKED` with evidence.

## Lot statuses and failure handling

A lot ends `DONE`, `FAIL`, `BLOCKED`, `BLOCKED-PERMISSION`, or `CANCELLED`.
`BLOCKED-PERMISSION` means a permission rule or the classifier refused a
required action; the fix is a rule request to the user or a reworded prompt,
recorded with `--block-kind permission`, never a tier change.

Otherwise diagnose before spending a child turn, then change one dimension:

- **specification/input failure** → fix the source, reroute without upgrading;
- **narrow instruction miss** → `SendMessage` to the same agent, same model;
- **context failure** → fresh spawn, same model;
- **capability failure** → fresh spawn, one tier up.

Allow at most two targeted rework attempts for the same diagnosed failure mode,
then re-plan the lot. A failure that changes assumptions, dependencies, or
downstream validity is a re-planning trigger. After every correction, rerun
affected checks and invalidate dependent downstream `PASS` results.

## Persistent ledger

Maintain `ledger.md` in the session scratchpad, next to the telemetry file,
never in the user's repository. It is the source of truth across cycles and
context compactions. It holds the global objective and acceptance criteria,
verified milestones with evidence pointers, current lots with dependencies,
cycle budget, **granted authorizations**, **held exclusive resources**,
material discoveries, routing and rework history, and the remaining objective.

Update it at every cycle boundary. After any context compaction or resumption,
re-read it before acting.

## Telemetry

When Python and writable storage are available, record every child-agent turn
and every orchestrator material execution through `scripts/telemetry.py` in
the session scratchpad. Record a turn as `--phase open` at spawn and
`--phase close` at result so it is counted once. Read
`references/telemetry.md` **when initializing telemetry, when diagnosing
routing, or when producing the final audit**.

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
- `BLOCKED`: a concrete missing dependency, authority, permission, resource,
  external state, or user decision prevents progress;
- `CANCELLED`: the user explicitly stops or redirects the objective.

Report in the user's language. Lead with the actual outcome: what was produced
or changed with exact paths, which criteria passed with evidence, which lots
were reworked and how routing escalated, planned versus consumed budget per
cycle, authorized orchestrator executions, and any open or blocked item. Then
append the concise Routing Audit from telemetry.

Never claim completion while a required criterion is failed, blocked without
disclosure, or unverified.

The persistent operating invariant is:

> **Assess → Plan → Route → Delegate → Verify → Integrate → Measure → Re-plan**
>
> until the complete user objective is demonstrably finished.
