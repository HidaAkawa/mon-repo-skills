---
document_id: "SDP-001"
document_type: "plan"
status: "draft"
version: "{{project_version}}"
owner: "{{owner}}"
approvers: []
created_at: "{{date}}"
updated_at: "{{date}}"
baseline: "git:{{commit_or_pending}}"
applicable_standards: ["ISO/IEC/IEEE 12207:2026", "ISO/IEC/IEEE 42010:2022", "ISO/IEC 27001:2022/Amd 1:2024", "NIST SP 800-218 SSDF 1.1"]
---

# Software development plan

## Delivery strategy

- MVP and increments:
- Working branch:
- Forge and PR/MR policy:
- Commit and release policy:

## Architecture

- System of interest and context:
- Components and responsibilities:
- Data and trust boundaries:
- External dependencies:
- Deployment:
- Significant decisions/ADRs:

## Security engineering

- Baseline controls:
- Identity and access:
- Secrets and keys:
- Dependency and supply-chain controls:
- Data protection and retention:
- Threats and treatments:

## Verification strategy

| Level/type | Scope | Tools | Gate | Evidence |
|---|---|---|---|---|

## Performance and capacity

- Budgets from baseline:
- Benchmark/load method:
- Regression threshold:
- Degradation behavior:

## Observability and operations

- Significant traced unit:
- Trace propagation and exporter:
- Logs, correlation and level control:
- Metrics, SLI/SLO and alerts:
- Forbidden telemetry data:
- Failure of telemetry backend:
- Runbooks and recovery:

## CI contract

| Required check | Local command | Forge job | Blocking condition |
|---|---|---|---|

## Build gate evidence

| Evidence ID | Commit | Command or execution | Environment/load | Result | Trace/artifact reference | SHA-256 | Date |
|---|---|---|---|---|---|---|---|

## Independent reviews

- Design milestone:
- Verification milestone:
- Counter-review budget:
- Report storage: `docs/reviews/` (Git ignored)
- Durable archive for elevated/critical:

| ID | Milestone | Result | Decision/status | SHA-256 | Archive reference | Counter-review number |
|---|---|---|---|---|---|---:|

## Risks, assumptions and derogations

| ID | Impact on plan | Treatment or validation | Owner | Due |
|---|---|---|---|---|
