# Routing Telemetry Reference (Claude Code)

Telemetry audits whether persistent delegation and adaptive routing actually
work, without keeping large histories in model context.

## Storage

When Python 3 and writable storage are available, use `scripts/telemetry.py`.

Default storage is the session scratchpad directory named in the system prompt
(`--dir <scratchpad>`), falling back to the system temporary directory. Never
add telemetry files to the user's repository unless explicitly requested.

Initialize once per objective:

```bash
python <skill>/scripts/telemetry.py init --dir <scratchpad>
```

The command prints the JSONL path. Reuse that exact path for the whole
objective and note it in `ledger.md`. Record events like:

```bash
python <skill>/scripts/telemetry.py record --file <path> \
  --cycle 1 --lot L1 --role executor \
  --model sonnet --subagent-type general-purpose \
  --result PASS --category bounded-code --risk standard \
  --material yes --verification deterministic
```

Use `--help` for the complete command schema.

## Required events

Record every:
- planner child turn;
- executor child turn;
- independent verifier turn;
- `SendMessage` rework;
- fresh replacement spawn;
- orchestrator direct execution of material work.

Roles:
`planner | executor | verifier | rework | replacement | orchestrator`

Results:
`PASS | FAIL | BLOCKED | CANCELLED | UNKNOWN`

Models: exactly the `model` value passed to the Agent tool (`haiku`, `sonnet`,
`opus`, `fable`). The script derives the capability tier automatically; pass
`--capability` only for a model it does not know.

Rework modes (`--rework-mode`), one per rework or replacement event:
`sendmessage | fresh_same_tier | tier_up | spec_fix`

For escalations, record:
- `--initial-model`;
- `--escalation-from` and `--escalation-to` (model names);
- `--escalation-reason` among
  `instruction_miss | context_failure | capability_failure | specification_failure | other`.

There is no `--effort` field. The Agent tool exposes no reasoning-effort
control and no token or credit usage; never estimate or record them.

## Reports

At a cycle boundary or on user request:

```bash
python <skill>/scripts/telemetry.py report --file <path>
```

For machine-readable output add `--json`.

## Core metrics

The report exposes:

- child turns by model, tier, role, and `subagent_type`;
- first-pass success rate, overall and by initial model;
- retry rate and rework-mode distribution;
- escalation rate and escalation matrix;
- delegation continuity by cycle;
- orchestrator material-execution events;
- top-tier (`opus`/`fable`) share of child turns.

## Routing diagnostics

Interpret telemetry; do not merely print numbers.

### Possible under-routing
- low first-pass success for a recurring route;
- repeated escalation from the same starting model;
- repeated multi-tier jumps after failure.

### Possible over-routing
- `opus`/`fable` on clearly mechanical deterministic lots;
- independent verifiers where deterministic evidence already proved the
  criterion.

### Possible orchestration collapse
- later material cycles without executor delegation;
- any orchestrator material-execution event;
- first wave delegated but subsequent waves executed locally.

### Rework discipline
- replacements spawned where a `sendmessage` rework was never tried;
- more than two reworks for one lot.

Do not enforce arbitrary target percentages.

## Final Routing Audit

At `DONE`, `BLOCKED`, or `CANCELLED`, include a concise audit after the actual
outcome:

1. number of cycles and material lots;
2. child turns by model, tier, role, and `subagent_type`;
3. planned versus consumed budget per cycle, including top-tier turns;
4. first-pass success;
5. retries, rework modes, and escalation matrix;
6. verification summary;
7. delegation continuity and orchestrator material events;
8. routing anomalies and recommendations;
9. the explicit statement that platform token/credit usage is not exposed by
   the Agent tool.

The audit supports tuning future routing; it never replaces the outcome and
verification report.
