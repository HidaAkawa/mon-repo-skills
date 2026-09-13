# Changelog — plan-delegate-verify (Claude Code)

## v4 — 2026-09-13

Source: post-mortem of the orchestration session of 2026-09-13 (audit resumed
on three repositories, publication and production promotion, eleven lots,
twelve real child turns recorded as fifteen). Each finding below has an
explicit answer or a motivated refusal.

### Finding 1 — delegation continuity 67 % with four legitimate orchestrator executions

Answer: the orchestrator's material executions are now split into two classes.
`authorized` covers work that cannot be delegated by construction, with a
declared reason (`single-browser`, `user-gate`, `non-delegable-tool`,
`trivial-glue`); it is declared in the plan as a lot and recorded with
`--exec-class authorized --exec-reason <reason>`. `fallback` covers any other
orchestrator execution. Delegation continuity now counts only cycles that
require delegation (a cycle whose only material work is authorized execution
leaves the denominator), and the `orchestration collapse` diagnostic counts
only fallback events. Legacy events without the field are reported as
`unclassified`, treated conservatively as fallback, with a dedicated
diagnostic asking to classify them. Replayed on the session file with the four
events annotated, continuity reads 100 % (4/4) instead of 67 % (4/6).
Files: `SKILL.md` (Non-negotiable loop), `references/planning.md`,
`references/telemetry.md`, `scripts/telemetry.py`.

### Finding 2 — cycle budget unfit for three independent critical lots

Answer: budget per critical lot, not one critical lot per cycle. The critical
cycle keeps `N + min(2, N) + 2` turns; the top-tier cap becomes
`max(2, C + 1)` where `C` is the number of critical lots executed in the
cycle. Each critical lot gets its own top-tier first pass plus one shared
reserve. The "one critical lot per cycle" alternative was refused: it would
serialize independent work that ran correctly in parallel. The report computes
`C` from the `risk` field already present in v3 files and prints
`top-tier k/cap` per cycle. Replayed on the session: cycle 2 shows 3/4 instead
of a breach of 2. Note that the five turns counted by v3 were three real turns
plus two double-recorded events (see the recording note below).
Files: `SKILL.md` (Cycle-local budgets), `references/planning.md`,
`scripts/telemetry.py`.

### Finding 3 — permission classifier blocks (SSH, `gh variable set`, refused spawn)

Answer: every plan now carries an `Authorizations and tools` step before its
first wave (rules to request in one message, tools per lot, wordings to
avoid, lots that need the user at the moment of the act). Executor prompts
name secrets by variable name and location, never by value or "token"
wording, and instruct the executor to report rather than work around. A lot
status `BLOCKED-PERMISSION` is introduced, recorded with
`--result BLOCKED --block-kind permission`; a reworded spawn is recorded with
`--rework-mode reword`; `permission_block` joins the escalation reasons. The
report lists permission-blocked lots and asks to add the rule to the plan
step. Global statuses stay `DONE / BLOCKED / CANCELLED`.
Files: `SKILL.md` (Rolling-horizon planning, Lot statuses), `references/planning.md`,
`references/executor-contract.md`, `references/routing.md`, `scripts/telemetry.py`.

### Finding 4 — executors returning "waiting for a notification" without delivering

Answer: an executor contract, quoted verbatim in every prompt, requires a
deliverable or an explicit `BLOCKED` report, forbids returning on a pending
wait, and specifies how to wait for an external event: one blocking,
time-bounded command inside the turn (`gh pr checks --watch`,
`gh run watch --exit-status`, a `timeout`-bounded loop), never a background
monitor or scheduled wake-up. A returned wait is diagnosed as a narrow
instruction miss and resumed by `SendMessage`, never by a tier change.
Files: `SKILL.md` (Delegation), `references/executor-contract.md`.

### Finding 5 — sequencing error: documentation merge while an approval PR was open

Answer: exclusivity windows. A lot may claim a shared resource (repository,
`main` branch, environment, host, release channel) in its plan entry and in
telemetry (`--exclusive <resource>`); it holds it from spawn until the
orchestrator records its close. While held, no other lot and no orchestrator
action writes to the resource. The ledger keeps a `Held resources` line; the
orchestrator checks it before any merge, push, deploy, or variable change.
Other lots declare `--writes <resource>` and the report flags overlaps.
Replayed on the annotated session file, the report prints
`Exclusivity breach: 'L9-docs-app' wrote 'demarches-app:main' while
'L13-promotion-et-search-console' held it`, which is the failure that cost the
#159 → #161 recreation.
Files: `SKILL.md` (Exclusivity windows, Persistent ledger), `references/planning.md`,
`references/verification.md`, `scripts/telemetry.py`.

### Finding 6 — practices to preserve

Answer: made explicit rather than left implicit. The `ASSESS` step now names
the initial parallel `Explore` discovery wave before any plan; routing keeps
"strongest available" for irreversible lots; `VERIFY` states that the
orchestrator replays the decisive deterministic check itself;
`SendMessage` to the same agent stays the first rework step before any model
change; the ledger is re-read after any compaction or resumption.
Files: `SKILL.md`, `references/routing.md`, `references/verification.md`.

### Additional finding — turns recorded twice

The session file records three turns (L1 rework, L4, L5) as an `UNKNOWN`
spawn event followed by a result event, so v3 counted fifteen child turns and
five top-tier turns in cycle 2 instead of twelve and three, and reported a
spurious "under-routing for opus" diagnostic. v4 adds `--phase open|close`:
a close merges into its open and the turn is counted once. Legacy files get a
heuristic (an `UNKNOWN` event followed by a same-key event is one turn) and a
recording warning in the report.
Files: `references/planning.md`, `references/telemetry.md`, `scripts/telemetry.py`.

### Compatibility and tests

- `scripts/telemetry.py` reads every v3 JSONL file unchanged; all new fields
  (`phase`, `exec_class`, `exec_reason`, `block_kind`, `exclusive`, `writes`)
  are optional. New validation only applies to new `record` calls: an
  orchestrator material event requires `--exec-class`; `--block-kind`
  requires `--result BLOCKED`.
- `scripts/test_telemetry.py`: 18 unit tests, run from the skill directory
  with `python -m unittest discover -s scripts -p "test_*.py"`.
- `Workflow` tool still excluded. Loop and global statuses unchanged.

## v3

Persistent loop (Assess → Plan → Route → Delegate → Verify → Integrate →
Measure → Re-plan), cycle-local budgets, single routing axis, `SendMessage`
rework ladder, ledger in the session scratchpad, JSONL telemetry.
