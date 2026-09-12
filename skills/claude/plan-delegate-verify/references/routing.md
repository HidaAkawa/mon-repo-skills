# Routing and Escalation Reference (Claude Code)

Read this reference when a routing decision is non-obvious, when a lot fails,
or when telemetry suggests systematic under- or over-routing.

## Goal

Minimize expected total cost:

`execution_cost + verification_cost + P(failure)*rework_cost + P(undetected_failure)*consequence_cost`

Do not optimize for a predetermined model distribution.

## Capability ladder

Claude Code routes on a **single axis**: the `model` override of the Agent
tool. Use only identifiers the session actually accepts.

| Tier | Model | Profile |
|---|---|---|
| efficient | `haiku` | fastest and cheapest; mechanical, well-specified work |
| balanced | `sonnet` | default for bounded code, analysis, structured writing |
| strong | `opus` | ambiguous, multi-file, nuanced, or costly-to-redo work |
| frontier | `fable` | strongest available when exposed; critical or exceptionally hard work |

There is no per-call reasoning-effort control. Never pin, request, or record an
effort level for a child agent.

The `subagent_type` is a second, orthogonal choice: prefer a specialized
profile (`Explore` for read-only search, `Plan` for planning) when its declared
tools and purpose fit better than `general-purpose`. It does not change the
capability tier.

## Initial route

| Lot profile | Starting route |
|---|---|
| Mechanical, deterministic, repetitive, easy to test | `haiku` |
| Bounded code, structured analysis, normal documentation | `sonnet` |
| Non-trivial multi-file implementation or debugging | `sonnet` or `opus` |
| Ambiguous, nuanced, costly to redo | `opus` |
| Critical security, irreversible effect, dependency bottleneck | strongest suitable |
| Exceptionally difficult after evidence-backed failures | `fable` when exposed |

Input size alone is not a reason to upgrade.

A stronger first pass is justified when downstream rework is expensive enough
that an underpowered attempt has a higher expected total cost.

Top-tier child turns (`opus`, `fable`) are capped by the cycle budget in
`SKILL.md`. Plan initial routes so the cap is not consumed before rework needs
it, unless the initial lot is itself critical.

## Escalation diagnosis

### Specification/input failure
Examples: wrong requirement, stale file, missing dependency, invalid assumption.

Action: correct the source of truth, then reroute. Do not upgrade automatically.

### Narrow instruction miss
The model appears capable but missed a bounded instruction.

Action: `SendMessage` to the same agent (its context is intact), same model,
with the failed criterion and concrete evidence. This is the cheapest rework
and the one Claude Code makes uniquely easy.

### Context failure
The agent appears confused by accumulated or irrelevant context, or the
`SendMessage` retry repeated the same mistake.

Action: fresh spawn, same model, tightened self-contained prompt.

### Capability failure
Evidence indicates the current tier is unreliable for this lot: the fresh spawn
failed the same way, or the failure is a reasoning error rather than an
oversight.

Action: fresh spawn, one tier up.

## Escalation discipline

Prefer one-dimensional steps, in this order:

`fix spec → SendMessage same agent → fresh spawn same tier → fresh spawn next tier`

Do not jump from `haiku` straight to `fable` unless consequence cost or direct
evidence clearly warrants it. Do not spawn a replacement when a `SendMessage`
follow-up would address the diagnosed cause.

Record every escalation in telemetry with `--rework-mode` and
`--escalation-reason`.

## Session-local adaptation

Use repeated evidence from similar lots to adjust later routing:

- if similar `haiku` lots repeatedly escalate, start later equivalents at
  `sonnet`;
- if `sonnet` lots consistently pass cheaply with deterministic checks,
  consider starting later mechanical equivalents at `haiku`.

Require multiple genuinely similar observations before adapting. One failure is
not enough.

## Orchestrator route

The orchestrator stays capable enough to plan, route, integrate, and diagnose
failures. It must not perform substantial executor work because its own model
is stronger or because the cycle budget ran out. Treat orchestrator context as
scarce too: read references only when needed and keep the ledger compact.
