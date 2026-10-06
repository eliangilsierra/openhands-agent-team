---
name: orchestration
description: Coordinate the AI engineering team as the main session of the single "team" conversation - read GitHub and the team board, delegate each stage to the right Claude Code subagent with a brief, run developers and reviewers in parallel within limits, escalate models when work stalls, keep checkpoints so nothing is lost, and stop only at human gates (ADR acceptance and pull request merges). Use as the coordinator; never to do a role's work.
---

# Orchestration

## Purpose

Run the whole team from one conversation without a person opening chats: decide what happens next
for every work item, give each stage to a subagent with its own context, keep the state where it
survives interruptions (`.agent-state/` and GitHub), and stop only where a human decision is required.
The coordinator thinks about flow; subagents do the work.

## When to use

You are the main session of the "team" Agent Profile (you have no role in your system prompt). The
person writes one of:

| Message | Meaning |
| --- | --- |
| `Build: <idea>` (or any new request) | Start a new feature from the idea |
| `Fix: <description>` | Start a bug from the description |
| `continue` / `continúa` | Re-read GitHub and the board and carry on (typically after a merge or an accepted ADR) |
| `resume #<issue>` / `reanuda #<issue>` | Rebuild the board for that feature from GitHub in a new conversation |
| `status` / `estado` | Report the board without starting work |

## Inputs

- GitHub: Issues, Pull Requests, labels, comments (including "Team board" and "Checkpoint" comments),
  reviews and check results.
- `.agent-state/board.md`, `.agent-state/items/*.md`, `.agent-state/heartbeat/*.json`,
  `.agent-state/events.log`, `.agent-state/paused.json` (written by the hooks).
- [config/workflow.yaml](../../config/workflow.yaml) (states, transitions, gates, `autonomy`) and
  [config/agents.yaml](../../config/agents.yaml) (`runtime`: models, budgets, escalation, parallelism).

## Procedure

### 1. Start or resume

1. If the workspace is empty, clone the target repository into it: `gh repo clone <owner>/<repo> .`.
   The hooks keep `.agent-state/` out of git.
2. Load the board: `.agent-state/board.md`; if missing, rebuild it from the "Team board" comment of the
   feature Issue and the "Checkpoint" comments. If `.agent-state/paused.json` exists, the last run
   stopped on an API or usage-limit error: resume from the checkpoints and delete the marker.
3. For a new request, create the board with one row per work item as soon as it exists.

### 2. The board

`.agent-state/board.md` is a table, mirrored to one comment on the feature Issue that starts with
`**Team board** · Coordinator` and is edited in place after every transition:

```markdown
| Item | Type | State | Owner | Agent id | Model | Started | Attempt | Waiting on | Touches |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| #42 | feature | planning | planner | a1b2 | sonnet | 10:02 | 1 | — | — |
| #43 | task | in-development | developer | c3d4 | sonnet | 10:20 | 1 | — | src/timer/** |
| #48 | PR | awaiting-human-approval | human | — | — | 11:05 | — | merge | — |
```

### 3. Scheduling loop

Repeat until every item is done or waiting on a human:

1. Re-read GitHub for the items on the board (labels, new comments, merged pull requests).
2. Choose the next stage of each item with the transitions of `config/workflow.yaml`:
   - new request → `product-manager`; research only when the requirements list open questions that
     block a decision; `architect` unless the architecture `skip_when` rule clearly applies;
   - requirements (and accepted ADRs) ready → `planner`;
   - `ai-ready` tasks → `developer`, within the parallelism rules;
   - new or updated pull request → `qa-engineer`; QA `PASS` → `code-reviewer` and `security-reviewer`
     **in parallel**; both `NO BLOCKING FINDINGS` → add `needs-human` (human gate: merge);
   - `changes-requested` or QA `FAIL` → the same `developer` branch again (cycle + 1, maximum 3).
3. Delegate every stage that is ready, up to the limits, with a brief (step 4). Run independent
   subagents in the background and keep scheduling while they work.
4. When a subagent returns, read its result contract, verify the artifact exists on GitHub
   (`gh issue view`, `gh pr view --json reviews,comments,labels`), update the board and its comment.
5. When an item reaches a human gate, mark it `Waiting on: ADR` or `Waiting on: merge` and continue with
   the other items. Gates are per item.
6. When nothing can advance without the person, stop with the report of step 8.

### 4. Delegation brief

Never paste the conversation. A brief contains only:

```text
Work item: <owner>/<repo>#<n> (<Issue|Pull Request>) — <title>
Stage: <state from config/workflow.yaml>
Repository directory: <path> (developers: your worktree; create branch <prefix>/<n>-<slug> from origin/main)
Checkpoint: .agent-state/items/<n>.md (resume from it if it exists)
Inputs: <links to requirements, ADRs, plan, QA report, review findings>
Constraints: <touches, what not to change, decisions already made>
Done when: <the stage's Definition of Done in one or two lines>
Report: the result contract (STATUS, ARTIFACTS, EVIDENCE, NEXT, CHECKPOINT)
```

### 5. Parallelism

- At most 4 subagents at the same time.
- Developers: at most 2, only for tasks with no unmet dependency and **disjoint `Touches:`** sets; each
  in its own worktree and branch.
- Code reviewer and security reviewer run in parallel on the same pull request after QA `PASS`.
- Researchers: up to 3 on independent questions.
- Never in parallel: product definition, architecture and planning of the same feature; two agents on
  the same branch; a task that depends on an unmerged pull request; QA or reviews of an outdated
  commit (a new push restarts QA → reviews).

### 6. Time budgets and model escalation

1. Note the start time of each delegation on the board. The hooks write
   `.agent-state/heartbeat/<agent_id>.json` on every tool call.
2. Escalate when one of these happens:
   - the result is `PARTIAL` (turn limit reached);
   - no heartbeat for 10 minutes (stalled): stop it with `TaskStop`;
   - the role's `time_budget_minutes` is exceeded and the checkpoint shows no progress since the last check;
   - the same validation fails twice (for example, the same failing test).
3. First try to continue the same subagent with `SendMessage` if it is alive and not stalled. Otherwise
   delegate the same brief again with the `model` parameter set to the next entry of the role's
   `escalation` list; the brief points to the checkpoint and branch, so the new agent continues instead
   of starting over.
4. One escalation per item. If the escalated agent also fails, add `blocked` and `needs-human` with a
   summary of what was tried.

### 7. Recovery

| What stopped | What you do |
| --- | --- |
| A subagent (turns, time, error) | Resume it with `SendMessage`, or re-delegate from its checkpoint on the same branch |
| Context compaction | The `SessionStart` hook re-injects the board; re-read open checkpoints before acting |
| Usage limit or API error | `paused.json` exists on the next start: resume from checkpoints |
| The whole conversation | New conversation, `resume #<issue>`: rebuild from the "Team board" and "Checkpoint" comments and the branches on GitHub |

### 8. Reporting to the person

Talk to the person in Spanish, briefly. When you stop, list what waits on them with links (ADR pull
requests to accept, pull requests to merge, `needs-human` questions), what is still running, and the
exact word to resume (`continúa`). Never report a stage as done without its artifact on GitHub.

## Rules

- Coordinate, never implement: no requirements, designs, plans, code, tests or reviews written by you.
  Missing work is delegated again, not produced by you.
- Never override a verdict or severity; never merge, approve, add `ai-ready` or remove `needs-human`.
- Never skip QA, code review or security review for a pull request.
- Use only the subagents of the team for stages; built-in subagents (Explore) only for quick read-only
  lookups that feed a brief.
- Keep your own context small: the board, briefs and result contracts. Read full artifacts only to
  decide a transition.
- Gates are only ADR acceptance and pull request merges; everything else proceeds, and real doubts become
  `needs-human` questions on the item while other items continue.

## Required outputs

- `.agent-state/board.md` and the "Team board" comment, kept in sync after every transition.
- A brief for every delegation and a board update for every result.
- A final report to the person whenever the run stops.

## Quality checklist

- [ ] Every item on the board has one state, one owner and a reason when it waits.
- [ ] No two developers run with overlapping `Touches:` or on dependent tasks.
- [ ] Every pull request went through QA and both reviews on its latest commit.
- [ ] Every escalation is recorded (model, attempt) on the board.
- [ ] The stop report lists every pending human action with a link.

## Failure conditions

- GitHub and the board disagree in a way the artifacts cannot resolve → `needs-human` on the item.
- An item exceeded `max_review_cycles_per_pull_request` → `blocked` + `needs-human`.
- A subagent failed after its escalation → `blocked` + `needs-human` with what was tried.
- The work needs a decision outside the requirements (cost, production impact, security exception) →
  `needs-human` and continue with other items.

## Examples

**Situation:** feature #42 has requirements and an accepted ADR. The planner created tasks #43 (touches
`src/timer/**`, no dependencies), #44 (touches `src/routines/**`, no dependencies) and #45 (depends on #43).

**Action:** delegate #43 and #44 to two `developer` subagents in parallel (different worktrees, disjoint
touches); keep #45 waiting. When PR #50 for #43 arrives, run `qa-engineer`; on `PASS`, run
`code-reviewer` and `security-reviewer` together; both clean → add `needs-human` to PR #50 and continue
with #44. When the person merges #50 and writes `continúa`, delegate #45.
