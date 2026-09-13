# Executor Contract Reference (Claude Code, v4)

Read this reference when writing an executor prompt, when an executor returned
without a deliverable, or when a spawn was refused by the permission
classifier.

## The contract, verbatim in every executor prompt

```text
Contract
1. Finish with one of: the deliverable and its evidence, or a BLOCKED report.
   Never finish with "waiting for", "will check later", or "once X happens".
2. If an external event must happen before you can finish (CI checks, a merge,
   a deployment, a job), wait for it inside this turn with a blocking,
   time-bounded command. Do not start a background monitor, a cron, a watcher,
   or a scheduled wake-up, and do not return early to "let the orchestrator
   know".
3. If a command or an action is refused by the permission system, stop, and
   report BLOCKED-PERMISSION with the exact command and the exact refusal.
   Do not work around it with another tool, another path, or a copy of a
   secret.
4. If an input is missing or contradictory, report BLOCKED with what is
   missing. Do not guess.
5. Do not spawn subagents. Do not modify anything outside your write scope.
   Preserve unrelated changes in the working tree.
6. Output format: <exact artifact paths>, then the evidence (command and
   output for each done criterion), then any BLOCKED item. No summary.
```

## Waiting for external events

Bounded waits that keep the turn alive and return a verdict:

```bash
gh pr checks <number> --watch --fail-fast
```

```bash
gh run watch <run-id> --exit-status
```

```bash
timeout 900 bash -c 'until gh pr view <number> --json mergedAt -q .mergedAt | grep -q .; do sleep 30; done'
```

Rules:

- One bounded wait per turn, sized to the real duration of the event (a CI run
  that takes eight minutes gets a fifteen-minute bound, not an hour).
- When the bound expires, report `BLOCKED` with the last observed state and
  the command to resume. That is a deliverable; "waiting" is not.
- Never poll with unbounded loops, and never rely on being re-invoked: a child
  agent is not.

## Wording that gets past the classifier

Auto mode classifies the prompt before the agent starts. Refused spawns cost a
turn and leave no trace unless recorded with `--rework-mode reword`.

| Avoid | Write instead |
|---|---|
| "use the token `ghp_...`" | "use the value of `RELEASE_TRUST_RECORD` already set on the repository" |
| "here is the API key" | "the key lives in `/etc/app/service.env` on the host; do not print it" |
| "log in with the password" | "the session is already authenticated; if not, report BLOCKED-PERMISSION" |
| "bypass the check if it fails" | "if the check fails, report FAIL with the output" |

Give the executor the **name and location** of every secret it needs, the
statement that it must never print or copy it, and the instruction to report
instead of improvising.

## What the orchestrator does with a returned wait

An executor that returned "waiting for CI" without a deliverable has not
delivered. Diagnose it as a narrow instruction miss: `SendMessage` to the same
agent with the contract lines 1 and 2 and the bounded wait command to run. If
it repeats, fresh spawn, same tier, with the contract at the top of the prompt.
Do not escalate the tier for a contract breach.

## What the orchestrator does with BLOCKED-PERMISSION

1. Record the turn with `--result BLOCKED --block-kind permission`.
2. Add the rule to the `Authorizations and tools` block and ask the user for
   it in one message with every other pending rule.
3. Resume the **same agent** with `SendMessage` once the rule is granted; its
   context is intact. If the act stays refused, it becomes an authorized
   orchestrator execution with reason `user-gate`, or the user performs it.
