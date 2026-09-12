# Verification Reference (Claude Code)

Read this reference when deterministic evidence is insufficient, when work is
critical, or when deciding whether an independent verifier is worth a child
turn.

## Evidence hierarchy

Prefer primary and reproducible evidence:

1. automated tests / assertions;
2. typecheck / lint / build / static analysis;
3. runtime probes, queries, logs, schema checks;
4. direct artifact / diff / rendered-output inspection;
5. independent semantic review.

Never accept an executor summary as proof.

## Deterministic-first rule

If objective checks fully prove every done criterion, do not spend a child turn
on a redundant semantic verifier.

Examples:
- deterministic transformation with golden-file test;
- compilation plus complete unit/integration tests;
- schema migration checked by authoritative query;
- exact calculation independently recomputed by the orchestrator.

## Orchestrator baseline verification

The orchestrator verifies every lot itself first: inspect produced files,
recalculate values, compare against sources, run relevant tests, open rendered
outputs when layout matters. For each criterion, ask what observable evidence
would prove it failed, then perform that check.

Verification is orchestrator work, not material execution. It does not count as
absorbing a lot.

## Independent verifier triggers

Spawn a fresh independent verifier only when at least one holds:

- a failure could cause serious data loss, security exposure, financial harm,
  unsafe behavior, or an irreversible external effect;
- the orchestrator cannot verify a critical criterion from primary evidence
  with high confidence;
- sources or verification results materially conflict.

Do not spawn a verifier merely because a lot was reworked.

## Verifier routing

Route the verifier one tier above the executor:

- `haiku` executor → `sonnet` verifier;
- `sonnet` executor → `opus` verifier;
- `opus` executor → `fable` verifier when exposed.

If the executor already used the strongest available tier, use the same tier in
a fresh context with the executor's reasoning hidden.

The verifier counts against the cycle budget and its top-tier cap.

## Verifier isolation

Provide:
- specification;
- artifacts / relevant files with absolute paths;
- authoritative sources;
- done criteria;
- deterministic evidence already gathered.

Do not provide:
- executor rationale or confidence;
- orchestrator tentative verdict;
- expected answer.

Ask the verifier to try to falsify the result and to return criterion-by-
criterion findings with evidence. Instruct it not to spawn subagents and not to
modify files.

## Batch verification

Batch compatible critical lots into one verifier turn when:
- contexts overlap;
- criteria remain independently identifiable;
- combined context remains manageable.

Require separate criterion-by-criterion verdicts. Do not batch if it makes
failures hard to attribute.

## Verdict format

Every required criterion is:

- `PASS` — evidence proves it;
- `FAIL` — evidence contradicts it;
- `BLOCKED` — verification lacks a required input, authority, or external state.

A material lot is not complete while a required criterion is unverified.
Adjudicate conflicts between orchestrator and verifier by checking primary
evidence directly.

## Downstream invalidation

After rework, rerun affected checks and invalidate downstream `PASS` results
whose evidence depended on the failed implementation.

A verification failure that changes architecture, assumptions, dependencies, or
scope triggers re-planning before further downstream material work.

## Critical work

For security, data-loss, financial, safety, irreversible-external-action, or
major architectural-lock-in risk:

- do not deliberately under-route to save quota;
- require deterministic evidence where possible;
- require independent semantic review when semantics matter;
- use a fresh verifier context;
- resolve conflicting evidence from primary sources before proceeding;
- obtain user approval before any destructive or externally consequential step.
