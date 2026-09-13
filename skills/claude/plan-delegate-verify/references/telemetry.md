# Routing Telemetry Reference (Claude Code, v4)

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

Record each turn twice with the same key (cycle, lot, role, model, rework
mode): `--phase open` at spawn and `--phase close` with the result. The report
merges the pair into one turn. A single event without phase is one atomic
turn.

```bash
python <skill>/scripts/telemetry.py record --file <path> --cycle 2 --lot L5 --phase open \
  --role executor --model opus --risk critical --material yes --exclusive host:srv1116117
python <skill>/scripts/telemetry.py record --file <path> --cycle 2 --lot L5 --phase close \
  --role executor --model opus --risk critical --material yes --result PASS --verification deterministic
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

With `--result BLOCKED`, add `--block-kind` among
`permission | dependency | user-decision | external | other`; `permission`
gives the lot status `BLOCKED-PERMISSION` in the report.

Orchestrator material executions require `--exec-class`:
- `authorized` with `--exec-reason single-browser | user-gate | non-delegable-tool | trivial-glue`,
  for a lot declared in the plan as orchestrator-executed;
- `fallback` for any other orchestrator execution of delegable work.

Exclusive resources: `--exclusive <resource>` on the open event of the lot that
holds it (repeatable); `--writes <resource>` on any turn that writes to a
shared resource. Name resources stably, for example `demarches-app:main`,
`host:srv1116117`, `release:content`.

Models: exactly the `model` value passed to the Agent tool (`haiku`, `sonnet`,
`opus`, `fable`). The script derives the capability tier automatically; pass
`--capability` only for a model it does not know.

Rework modes (`--rework-mode`), one per rework or replacement event:
`sendmessage | fresh_same_tier | tier_up | spec_fix | reword`
(`reword` = the spawn was refused by the classifier and re-issued with a
reworded prompt).

For escalations, record:
- `--initial-model`;
- `--escalation-from` and `--escalation-to` (model names);
- `--escalation-reason` among
  `instruction_miss | context_failure | capability_failure | specification_failure | permission_block | other`.

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
- delegation continuity, computed over cycles that require delegation (a
  cycle whose only material work is authorized orchestrator execution is
  excluded from the denominator and listed separately);
- orchestrator material-execution events by class (`authorized`, `fallback`,
  `unclassified` for legacy files) and by reason;
- per-cycle top-tier turns against the cap `max(2, C + 1)`;
- lot statuses, `BLOCKED` by kind, `BLOCKED-PERMISSION` lots;
- exclusive resources held and any write on a held resource;
- merged open/close pairs;
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
- later material cycles without executor delegation, excluding cycles made
  only of authorized orchestrator executions;
- any `fallback` orchestrator material-execution event;
- `unclassified` orchestrator events (legacy files): treated as fallback until
  classified;
- first wave delegated but subsequent waves executed locally.

### Permissions and sequencing
- any `BLOCKED-PERMISSION` lot: the rule should have been requested in the
  plan's `Authorizations and tools` step;
- any `Exclusivity breach`: a write on a resource while another lot held it.

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
7. delegation continuity, authorized orchestrator executions by reason, and
   fallback events;
8. permission blocks, exclusive resources held, and any breach;
9. routing anomalies and recommendations;
10. the explicit statement that platform token/credit usage is not exposed by
    the Agent tool.

The audit supports tuning future routing; it never replaces the outcome and
verification report.
