# Routing and Escalation Reference

Read this reference when the current routing decision is non-obvious, when a lot
fails, or when telemetry suggests systematic under- or over-routing.

## Goal

Minimize expected total cost:

`execution_cost + verification_cost + P(failure)*rework_cost + P(undetected_failure)*consequence_cost`

Do not optimize for a predetermined model distribution.

## Capability profiles

Build the ladder dynamically from the models exposed by the runtime:

`efficient → balanced → strong → frontier`

Use only actual model identifiers supported by the collaboration tool.

Reasoning effort is a separate ladder:

`low → medium → high → xhigh`

Use only effort levels actually supported.

## Initial route

| Lot profile | Starting route |
|---|---|
| Mechanical, deterministic, repetitive, easy to test | Efficient / low |
| Bounded code, structured analysis, normal documentation | Efficient or balanced / low-medium |
| Non-trivial multi-file implementation or debugging | Balanced / medium-high |
| Ambiguous, nuanced, costly to redo | Strong / medium-high |
| Critical security, irreversible effect, major dependency bottleneck | Strongest suitable / high |
| Exceptionally difficult after evidence-backed failures | Frontier / justified effort |

Input size alone is not a reason to upgrade.

A stronger first pass is justified when downstream rework is expensive enough
that an underpowered attempt has higher expected total cost.

## Escalation diagnosis

### Specification/input failure
Examples: wrong requirement, stale file, missing dependency, invalid assumption.

Action: correct the source of truth, then reroute. Do not upgrade automatically.

### Narrow instruction miss
The model appears capable but missed a bounded instruction.

Action: same model, same effort, targeted retry with concrete failure evidence.

### Reasoning-depth failure
The model understood the problem but reasoning was insufficient.

Action: keep model, raise effort one supported step.

### Capability failure
Evidence indicates the current capability is unreliable for this lot.

Action: move one model capability step up, with appropriate effort.

### Context failure
The agent appears confused by accumulated or irrelevant context.

Action: fresh context, same capability first.

## Escalation discipline

Prefer one-dimensional steps:

`efficient-low → efficient-medium → balanced-low → balanced-medium → strong-medium → strong-high → frontier-medium → frontier-high`

Do not jump from an efficient route straight to frontier/high unless consequence
cost or direct evidence clearly warrants it.

Record every model or effort escalation in telemetry.

## Session-local adaptation

Use repeated evidence from similar lots to adjust later routing:

- if similar `efficient` lots repeatedly escalate, start later equivalents higher;
- if `balanced` lots consistently pass cheaply with deterministic checks, consider
  starting later equivalents lower.

Require multiple genuinely similar observations before adapting. One failure is
not enough.

## Orchestrator route

The orchestrator should remain capable enough to plan, route, integrate, and
diagnose failures. It should not perform substantial executor work simply because
its own model is stronger.

Treat orchestrator compute as scarce too.
