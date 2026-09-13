# Planning Reference (Claude Code, v4)

Read this reference when writing the plan of a new horizon: authorizations,
exclusivity windows, budget with several critical lots, and authorized
orchestrator execution.

## Authorizations and tools step

Before the first wave of every horizon, write a short block in the plan and in
the ledger:

```text
Authorizations and tools
- Rules to request now: ssh root@<host> ; gh variable set ; gh pr merge ; <script>
- Already granted (date, scope): ...
- Tools per lot: L4 gh + git ; L5 ssh + systemctl ; L7 user's browser (orchestrator)
- Wording to avoid in prompts: secret values, "token", "credential", raw keys
- Lots that need the user at the moment of the act: L13 (promotion), L14 (form)
```

Rules of thumb:

- Ask the user for the permission rules **once, before the wave**, in one
  message that lists every command family the lots will need. Piecemeal
  refusals during execution cost a child turn each.
- In auto mode the classifier reads the executor prompt too. A prompt that
  mentions a secret by value, or uses words like token, credential, password,
  API key, can be refused before the agent even starts. Name the variable and
  its location instead: `the value stored in RELEASE_TRUST_ANCHOR on the
  repository`, `the file /etc/app/service.env on the host`.
- Tell every executor to stop and report `BLOCKED-PERMISSION` with the exact
  refused command. Working around a refusal (another tool, another path, a
  copy of the secret) is a contract breach, not initiative.
- When a refusal repeats after a rule request, the act belongs to the user or
  becomes an authorized orchestrator execution with reason `user-gate`.

## Authorized orchestrator execution

Some acts cannot be delegated by construction. Declare each as a lot with
routing `orchestrator (authorized: <reason>)` **in the plan**, before the
wave, and record it with `--exec-class authorized --exec-reason <reason>`:

| Reason | Meaning | Examples |
|---|---|---|
| `single-browser` | a browser session only the orchestrator holds | user's Chrome, Access-protected pages, visual acceptance |
| `user-gate` | the user must authorize the act at the moment it happens | repository variables, publication trigger, production promotion, external forms |
| `non-delegable-tool` | a tool the Agent tool does not expose to children | session-only connectors |
| `trivial-glue` | one-line mechanical corrections after verification | fixing a path in a ledger, re-running a check |

Anything else the orchestrator executes is a **fallback** and must be recorded
with `--exec-class fallback`. The telemetry report counts only fallbacks as
orchestration collapse. An authorized lot still gets done criteria, a risk
level, verification, and telemetry like any other lot.

Do not turn a delegable lot into an authorized one because it is late in the
session or because a child failed twice; that is a fallback.

## Exclusivity windows

A shared resource is anything two lots or the orchestrator could write to:
a repository, its `main` branch, a release channel, an environment, a host,
a set of repository variables.

- A lot **claims** a resource in its plan entry (`Exclusive resource`) and in
  telemetry (`--exclusive <resource>` on its open event).
- The hold lasts from spawn until the orchestrator records the close event.
- While held, **no other lot and no orchestrator action** writes to the
  resource. Merging an unrelated documentation PR into a branch that an open
  approval PR is measured against breaks the approval guard: the base is
  frozen at PR creation. That is the failure this rule prevents.
- Lots that write to a held resource are scheduled after the release of the
  hold, or declare `--writes <resource>` so the report can show the overlap.
- The ledger keeps a `Held resources` line updated at every cycle boundary:
  `demarches-app:main held by L13 since 16:35 (approval PR #159 open)`.
- The orchestrator's own writes obey the same rule. Before any merge, push,
  deploy, or variable change, check the `Held resources` line.

## Budget with several critical lots

The critical cycle budget stays `N + min(2, N) + 2` turns. The top-tier cap is
`max(2, C + 1)` where `C` is the number of critical lots in the cycle:

| C | cap on `opus`/`fable` child turns |
|---|---|
| 0 or 1 | 2 |
| 2 | 3 |
| 3 | 4 |

Each critical lot gets its own top-tier first pass plus one shared reserve for
rework or verification. Three independent critical lots may share a cycle when
they touch different resources; splitting them into three cycles would only
serialize work that can run in parallel. Do not inflate `C` by marking lots
critical to buy budget: a critical lot has an irreversible effect, a security
consequence, or sits on the dependency bottleneck.

## Recording turns once

Record `--phase open` when spawning and `--phase close` when the result is
verified, with the same cycle, lot, role, model, and rework mode. The report
merges the pair into one turn. Without phases, a spawn recorded as `UNKNOWN`
and later re-recorded with its result is counted twice by v3 and merged by a
heuristic in v4; the report then prints a recording warning.
