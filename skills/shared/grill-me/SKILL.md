---
name: grill-me
description: Grill the user relentlessly about a plan, decision, or idea until a shared understanding is reached, walking down every branch of the decision tree. Use when the user wants to stress-test their thinking, validate a design, or uses any 'grill' trigger phrase. Can also be invoked by other skills to conduct a scoped interview on their behalf.
---

# Grill me

Interview me relentlessly about every aspect of this until we reach a shared
understanding. Walk down each branch of the decision tree, resolving
dependencies between decisions one-by-one. For each question, provide your
recommended answer.

If a *fact* can be found by exploring the environment (filesystem, tools, etc.),
look it up rather than asking me. The *decisions*, though, are mine — put each
one to me and wait for my answer.

Do not act on it until I confirm we have reached a shared understanding.

Reply in the language the user is writing in.

## Rhythm

By default, ask the questions **one at a time**, waiting for feedback on each
before continuing. Asking many unrelated questions at once is bewildering.

A calling skill may override this — see *Scoping* below.

## Scoping

Another skill may invoke this one with a scope block. When it does, honour it
strictly. A scope may set:

- **`profil`** — what the user knows. Any decision beyond their competence must
  be *decided for them*, stated as decided, and explained in plain terms rather
  than put to them as a question.
- **`max_questions_par_salve`** — overrides the one-at-a-time default. Never
  exceed it.
- **`sujets`** — the exhaustive list of topics this session must cover. Do not
  wander outside it; other topics belong to other phases.
- **`verrouille`** — decisions already settled. Never reopen them, and treat
  them as constraints on everything that follows.
- **`vocabulaire`** — when set to plain language, define every technical term at
  first use or avoid it entirely.

When no scope block is given, behave as an unrestricted grilling session.

Never name a specific model or agent product in your questions: this skill runs
on more than one platform.
