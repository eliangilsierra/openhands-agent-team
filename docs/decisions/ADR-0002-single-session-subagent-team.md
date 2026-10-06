# ADR-0002: Run the team as one coordinator session with Claude Code subagents

## Status

Accepted

| Field | Value |
| --- | --- |
| Date proposed | 2026-10-05 |
| Date decided | 2026-10-05 |
| Decided by | Repository owner, by merging the Pull Request that introduces this ADR |
| Related Issue | #7 |
| Supersedes | None. Amends [ADR-0001](ADR-0001-agent-team-architecture.md): one Agent Profile per role and the OpenHands/ACP split per role are replaced |
| Related ADRs | ADR-0001 |

## Context

ADR-0001 mapped every role to its own OpenHands Agent Profile. In practice:

- OpenHands fixes the profile when a conversation starts, so every stage needs a new conversation. Each
  one creates a new workspace, clones and installs again, reloads the same context, and needs a person to
  open it and paste a message. The team cannot run on its own.
- One profile playing every role in one context was tried and failed: it mixed twelve tasks in one branch,
  merged locally into `main` and reviewed its own work (first run on `agent-sandbox`).
- ACP profiles have no field for role instructions, and `launch_child_conversation` neither selects a
  profile nor is offered to ACP profiles (checked in the OpenHands source, October 2026).
- Claude Code subagents run inside one session with their own context window, system prompt, model,
  tools, skills and optional git worktree; hooks run in every permission mode and inside subagents
  (Claude Code documentation, October 2026). Claude Code "agent teams" need an interactive session and
  do not start under the Agent SDK that the ACP adapter uses.
- The person wants the team to stop only for decisions that are theirs: accepting architecture decisions
  and merging Pull Requests.

## Decision

We will run the whole team in **one OpenHands conversation** with a single ACP Agent Profile, `team`
(Claude Code):

- The main session is the **coordinator** (the Orchestrator role, skill `orchestration`). It reads
  GitHub and a team board, delegates every stage with a brief and never does a role's work.
- Every other role is a **Claude Code subagent** generated from `config/agents.yaml` into
  `templates/runtime/claude/agents/` and installed in `~/.claude/agents/`: its own model, effort, turn
  limit, tools, preloaded skills and user-scope memory; developers run in their own git worktrees.
- **Restriction levels** R0–R4 are enforced by Claude Code hooks (`PreToolUse` for Bash and file
  writes) and by git hooks (`commit-msg`, `pre-push`), in addition to GitHub branch protection.
- **Autonomy rules** live in `config/workflow.yaml` (`autonomy`): human gates only for ADR acceptance
  and merges, gates per work item, at most 4 subagents at once, 2 developers on disjoint `Touches`
  sets, code and security reviews in parallel after QA, model escalation on stalls or exhausted turns,
  checkpoints in `.agent-state/` mirrored to GitHub comments.
- Operational hook scripts (`templates/runtime/claude/hooks/*.mjs`) are allowed in this repository as an
  exception to "no application code": they are runtime configuration of the team, tested in CI.

## Alternatives

| Alternative | Why not chosen |
| --- | --- |
| Keep one profile per role and add a dispatcher that opens conversations through the OpenHands API | Works, but repeats clone, install and context loading per stage, needs the backend API key in an automation, and still splits the team across conversations |
| One profile playing all roles without subagents | No independence: the failure of the first run |
| Claude Code agent teams | Experimental and not available under the Agent SDK used by ACP |
| OpenHands-native sub-agents with an LLM profile | Valid, but billed per API usage instead of the existing Claude subscription; may be revisited |
| Running agents in GitHub Actions (`claude-code-action`) | Leaves the OpenHands platform and its workspaces |

## Consequences

**Positive**

- One message starts the work; the team continues until a human gate, and continues with other items
  while one waits.
- One clone and one install per conversation; reviewers read the pull request diff, not the history of the
  conversation.
- Independence is structural (separate contexts) and limits are deterministic (hooks), not only
  instructions.
- Models are tuned per role, with escalation when a cheaper model stalls.

**Negative**

- All subagents share the conversation's environment and the single GitHub identity: least privilege
  between roles relies on hooks, not on separate credentials.
- With one identity, reviewers cannot submit `REQUEST_CHANGES` on the author's pull request; the verdict
  uses a `COMMENT` review plus the `changes-requested` label checked by `pr-conventions`.
- A long conversation consumes the plan's usage faster; budgets and escalation must be watched in the pilot.
- Whether every Claude Code feature used here (agents directory, hooks, worktree isolation, background
  subagents) works through the ACP adapter is verified in the pilot, not assumed.

**Follow-up actions**

- Install the runtime files and create the `team` profile (docs/subagents.md).
- Pilot on `agent-sandbox`, then tune models, budgets and limits from the measurements.
- Consider machine-user identities so reviews can request changes and branch protection can require a
  human approval that agents cannot satisfy.

## Security considerations

- Hooks deny pushes to `main`, merges, approvals, branch-protection changes, force pushes, identity changes
  and writes outside each level's paths, in every permission mode; git hooks block pushes to `main`,
  non-conforming branch names and pushed secrets even outside Claude Code.
- The ACP session approves tool permissions automatically, so these external controls are the guard; the
  tests in `templates/runtime/claude/hooks/test-hooks.mjs` run in CI.
- Branch protection level 1 stays in force; with an administrator token an agent could still call the
  merge API from outside the denied patterns, which is why level 2 with machine users remains the target.
- `.agent-state/` is excluded from git; checkpoints must never contain secrets.

## Operational considerations

- Runtime files live in the persistent `~/.claude` volume of the OpenHands container: `agents/`,
  `hooks/`, `githooks/`, `settings.json` and `CLAUDE.md`; git hooks are activated with `GIT_CONFIG_*`
  environment variables of the deployment.
- The `team` profile uses `acp_prompt_timeout` 3600 seconds so long delegations are not cut.
- Recovery after an interruption uses the board and checkpoints (`continúa`, `reanuda #<n>`).
- The archive branch `archive/multi-profile-team` and tag `v0.1-multi-profile` keep the previous design.
