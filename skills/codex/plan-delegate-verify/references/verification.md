# Verification Reference

Read this reference when deterministic evidence is insufficient, when work is
critical, or when deciding whether an independent verifier is worth its cost.

## Evidence hierarchy

Prefer primary and reproducible evidence:

1. automated tests / assertions;
2. typecheck / lint / build / static analysis;
3. runtime probes, queries, logs, schema checks;
4. direct artifact / diff / rendered-output inspection;
5. independent semantic review.

Never accept an executor summary as proof.

## Deterministic-first rule

If objective checks fully prove every done criterion, do not spend premium model
capacity on a redundant semantic verifier.

Examples:
- deterministic transformation with golden-file test;
- compilation + complete unit/integration tests;
- schema migration checked by authoritative query;
- exact calculation that can be independently recomputed.

## Semantic verification

Use semantic review when correctness involves architecture, nuanced requirements,
security reasoning, subtle regressions, complex analysis, or other properties
that deterministic checks do not fully establish.

When cost-effective, prefer an independent verifier with a higher capability
class than the executor:

- efficient executor → balanced verifier;
- balanced executor → strong verifier;
- strong executor → frontier verifier.

If the executor already used the strongest available model:
- use a fresh verification context;
- hide executor reasoning and tentative verdict;
- increase effort only when justified.

## Verifier isolation

Provide:
- specification;
- artifacts / relevant files;
- authoritative sources;
- done criteria;
- deterministic evidence.

Do not provide:
- executor rationale;
- executor confidence;
- orchestrator tentative verdict;
- expected answer.

Ask the verifier to try to falsify the result.

## Batch verification

Batch compatible lots when:
- contexts overlap;
- criteria remain independently identifiable;
- combined context remains manageable.

Require separate criterion-by-criterion verdicts.

Do not batch if it makes failures difficult to attribute.

## Verdict format

Every required criterion is:

- `PASS` — evidence proves it;
- `FAIL` — evidence contradicts it;
- `BLOCKED` — verification lacks a required input, authority, or external state.

A material lot is not complete while a required criterion is unverified.

## Downstream invalidation

After rework, rerun affected checks and invalidate downstream PASS results whose
evidence depended on the failed implementation.

A verification failure that changes architecture, assumptions, dependencies, or
scope triggers re-planning before further downstream material work.

## Critical work

For security, data-loss, financial, safety, irreversible-external-action, or
major architectural-lock-in risk:

- do not deliberately under-route merely to save quota;
- require deterministic evidence where possible;
- require independent semantic review when semantics matter;
- use fresh verifier context;
- resolve conflicting evidence from primary sources before proceeding.
