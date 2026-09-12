# Routing Telemetry Reference

Telemetry audits whether persistent delegation and adaptive routing actually work
without keeping large histories in model context.

## Storage

When writable temporary storage is available, use:

`scripts/telemetry.py`

Default storage should be outside the user's repository, ideally under the
runtime temporary directory.

Never add telemetry files to the repository unless explicitly requested.

Initialize once per long-running objective:

```bash
python scripts/telemetry.py init
```

The command prints the telemetry file path. Reuse that exact path through the
session, for example:

```bash
python scripts/telemetry.py record --file <path> \
  --cycle 1 --lot L1 --role executor \
  --model <exact-model> --capability efficient \
  --effort low --result PASS \
  --category mechanical
```

Use `--help` for the complete command schema.

## Required events

Record every:
- planner child turn;
- executor child turn;
- independent verifier;
- retry/rework;
- replacement agent.

Roles:
`planner | executor | verifier | rework | replacement`

Results:
`PASS | FAIL | BLOCKED | CANCELLED | UNKNOWN`

For escalations, record:
- `--initial-model`;
- `--initial-effort`;
- `--escalation-from`;
- `--escalation-to`;
- `--escalation-reason`.

Recommended escalation reasons:
`instruction_miss | reasoning_failure | capability_failure | context_failure | specification_failure | other`

Record platform usage fields only when explicitly supplied by the runtime:
- input tokens;
- cached input tokens;
- output tokens;
- total tokens;
- credits.

Never estimate them.

## Reports

At an epoch boundary or on user request:

```bash
python scripts/telemetry.py report --file <path>
```

For machine-readable output:

```bash
python scripts/telemetry.py report --file <path> --json
```

## Core metrics

The report should expose:

- child turns by model;
- child turns by capability;
- child turns by reasoning effort;
- child turns by role;
- first-pass success rate;
- first-pass success by initial model/capability;
- retry rate;
- capability/model escalation rate;
- effort escalation rate when inferable;
- escalation matrix;
- material delegation rate when materiality metadata is recorded;
- delegation continuity by cycle;
- orchestrator direct-execution events when explicitly recorded;
- available token/credit totals.

## Routing diagnostics

Interpret telemetry; do not merely print numbers.

Flag:

### Possible under-routing
- low first-pass success for a recurring route;
- repeated escalation from the same starting capability;
- repeated multi-level jumps after failure.

### Possible over-routing
- strong/frontier use on clearly mechanical deterministic lots;
- high/xhigh effort where deterministic evidence was sufficient.

### Possible orchestration collapse
- later material cycles without executor delegation;
- increasing orchestrator material execution;
- first wave delegated but subsequent waves executed locally.

### Possible excessive verification
- premium semantic verification where deterministic checks already proved the
  criterion.

Do not enforce arbitrary target percentages.

## Final Routing Audit

At `DONE`, `BLOCKED`, or `CANCELLED`, include a concise audit:

1. number of cycles / material lots;
2. usage by model, effort, capability, and role;
3. first-pass success;
4. retries and escalation matrix;
5. verification summary;
6. delegation continuity;
7. routing anomalies / recommendations;
8. exact platform tokens/credits if available;
9. otherwise state explicitly that platform token/credit usage was not exposed.

The audit supports tuning future routing; it must not replace the actual outcome
and verification report.
