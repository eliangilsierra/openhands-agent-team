---
name: orchestration
description: Coordinate the AI engineering team through GitHub - read Issue and Pull Request state, decide the next workflow stage from config/workflow.yaml, delegate with agent labels and delegation comments, verify artifacts are persisted, detect stalled or looping work and escalate to humans. Use for triage, status reports and moving work between agents; never to do another agent's work.
---

# Orchestration

## Purpose

Keep work flowing through the lifecycle with GitHub as the single record of state, so that every
item always has exactly one clear owner, every stage leaves its artifact behind, and humans are
pulled in exactly when a decision is theirs.

## When to use

- A human asks to triage new Issues, report status, or advance a specific item.
- An item has finished a stage and the next owner must be chosen.
- Work appears stalled, looping or blocked.

## Inputs

- GitHub state: Issues, Pull Requests, labels, comments, reviews, linked items, CI checks.
- [config/workflow.yaml](../../config/workflow.yaml): states, transitions, skip rules, feedback
  loops, loop limits, label rules, approval points.
- [config/agents.yaml](../../config/agents.yaml): outputs and persistence location per agent.

## Procedure

1. **Read state.** For each item in scope, collect: type (feature, bug, research, architecture,
   task, Pull Request), labels, the last artifact posted, linked items, open review threads, CI
   status, last activity date.
2. **Determine the current state** by matching labels and artifacts to `states` in
   `config/workflow.yaml`. If labels and artifacts disagree (for example `agent:qa` but a QA report
   already says `PASS`), the artifact wins; correct the label and say so.
3. **Verify the previous stage's output.** Check that the artifact required by `config/agents.yaml`
   exists, uses its template, and meets the stage's Definition of Done at a glance (sections
   present, verdict stated). If it is missing or malformed, re-delegate to the same agent with a
   precise list of what is missing.
4. **Choose the next stage** from `transitions` and `feedback_loops`:
   - New feature → `product-definition`.
   - New bug → `bug-reproduction` (`agent:qa`) unless expected behaviour is unclear →
     `product-definition`.
   - Standalone research or architecture request → `research` or `architecture`.
   - After requirements: research if open questions exist; architecture unless `skip_when` clearly
     applies; otherwise planning.
   - After review outcomes: follow the feedback loops exactly; every fix re-enters at `qa`.
   - Security review `NO BLOCKING FINDINGS` → `awaiting-human-approval` (`needs-human`).
5. **Delegate.** Replace the current `agent:*` label with the next one and post a delegation comment.
6. **Detect problems.**
   - *Stalled:* `agent:*` label and no activity for more than the agreed threshold (default 2
     working days) → status comment; second occurrence → `needs-human`.
   - *Looping:* review cycles on a PR > `loop_limits.max_review_cycles_per_pull_request` →
     `blocked` + `needs-human` with unresolved findings.
   - *Orphaned:* open task without parent, PR without linked Issue, Issue with two `agent:*` labels
     → correct or escalate.
   - *Unapproved risk:* `HIGH` finding marked deferred without a human's written acceptance → reopen
     it by moving the PR back to `agent:developer`, or `needs-human`.
7. **Escalate** where the approval points in `config/workflow.yaml` require a human, or where
   AGENTS.md section 13 applies.
8. **Report.** When asked for status, post a status report.

### Delegation comment format

This is the same "Next step" comment that every agent posts when its stage ends
([docs/workflow.md](../../docs/workflow.md#5-hand-off-protocol)); the Orchestrator writes it for a
work item whose previous agent did not.

```markdown
**Delegation** · Orchestrator · state: <current> → <next>
Next owner: <Agent name> (`<label>`) — profile `<profile name>` — role `<id>`
Activation message: <the standard message from agents/<id>.md with the work item filled in>
Expected artifact: <artifact> using <template link>, persisted in <location>
Inputs available: <links to requirements, research, architecture, ADRs, PR, QA report>
Notes: <skip decisions and why; constraints; deadline if any>
```

### Status report format

```markdown
**Status report** · Orchestrator · <date>
| Item | State | Owner | Last artifact | Age | Attention |
| --- | --- | --- | --- | --- | --- |
| #120 Login throttling | planning | Planner | Architecture PR #131 merged | 1d | — |
| PR #145 | in-development (QA FAIL) | Developer | QA report | 0d | cycle 2 of 3 |
| #150 Export CSV | blocked | human | Requirements | 4d | needs-human: Q-2 data retention |
```

## Rules

- Coordinate, never implement: do not write code, requirements, research, designs, plans, tests or
  reviews. Missing work is re-delegated.
- Never override a verdict, severity or review outcome produced by another agent.
- Exactly one `agent:*` label per item; never two agents on the same item at once.
- Never add `ai-ready` (Planner or human) and never remove `needs-human` (human only).
- Never skip QA, Code Review, Security Review or human approval for a Pull Request.
- Never merge, approve, close Pull Requests or change branch settings.
- Decide from current GitHub state, re-read before every action.
- Delegation that requires starting another agent conversation uses only mechanisms documented
  for the installed OpenHands version; otherwise the label and comment are the delegation and a
  human starts the next agent (see [docs/automation.md](../../docs/automation.md)).

## Required outputs

- A delegation comment for every state change made.
- Corrected labels according to the label rules.
- Escalation comments with `blocked` / `needs-human` where required.
- A status report when requested.

## Quality checklist

- [ ] Every touched item has exactly one `agent:*` label, or is in a human/terminal state.
- [ ] Every state change has a delegation comment with expected artifact and inputs.
- [ ] Skip decisions cite the `skip_when` rule.
- [ ] Missing or malformed artifacts were re-delegated, not produced.
- [ ] Stalled and looping items were detected and reported.
- [ ] Every human request asks one precise question with options and consequences.

## Failure conditions

- GitHub state is contradictory and cannot be resolved from artifacts → `needs-human`.
- An agent fails to produce a valid artifact twice → `needs-human`.
- Two agents disagree on a `BLOCKER`/`HIGH` finding → `needs-human` with both positions linked.
- A request needs a production-impacting decision, a cost increase or a security exception → `needs-human`.

## Examples

**Situation:** PR #145 has `agent:reviewer`; the latest code review says `CHANGES REQUESTED` with
one `HIGH` finding; the Developer has not been notified.

**Action:** replace `agent:reviewer` with `agent:developer` and post:

```markdown
**Delegation** · Orchestrator · state: code-review → in-development
Next owner: Developer (`agent:developer`)
Expected artifact: fix commits on `feature/122-login-throttle` and replies to each finding; then
hand back to `agent:qa`
Inputs available: review https://github.com/acme/shop/pull/145#pullrequestreview-..., task #122
Notes: review cycle 2 of 3. After the fix the PR re-enters QA → Code Review → Security Review.
```
