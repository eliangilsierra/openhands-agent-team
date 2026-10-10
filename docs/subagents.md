# Subagent Team

The team runs in **one OpenHands conversation** with the ACP Agent Profile `team` (Claude Code). The
main session is the **coordinator**; every role is a Claude Code **subagent** with its own context,
model, tools and skills. The decision and its trade-offs are in
[ADR-0002](decisions/ADR-0002-single-session-subagent-team.md); this document is the operating guide.

## 1. Overview

```mermaid
flowchart TB
    person([Person]) -->|"Build: idea / continúa / reanuda #n"| coord
    subgraph conv[One OpenHands conversation - profile team - one workspace]
        coord[Coordinator<br/>main session, skill orchestration]
        pm[product-manager]
        rs[researcher x3]
        ar[architect]
        pl[planner]
        dev[developer specialists x3<br/>own worktrees]
        qa[qa-engineer]
        cr[code-reviewer]
        sr[security-reviewer]
        state[(.agent-state<br/>board, checkpoints, heartbeats)]
    end
    coord --> pm & rs & ar & pl & dev & qa & cr & sr
    coord <--> state
    conv <-->|Issues, PRs, comments, reviews, labels| gh[(GitHub)]
    gh -->|ADR to accept / PR to merge| person
```

The person writes one message; the coordinator delegates stage after stage and stops only at the human
gates: **accepting an ADR** (merging its docs Pull Request) and **merging a Pull Request**. Gates are per
work item: while one item waits, independent items continue.

## 2. Catalogue

Canonical values are `runtime` in [config/agents.yaml](../config/agents.yaml); the subagent files in
[templates/runtime/claude/agents/](../templates/runtime/claude/agents/) are generated from them and the
validator checks that they agree.

| Agent | Model | Effort | Turns | Budget (min) | Escalation | Level | Parallel |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Coordinator (orchestrator) | sonnet | medium | — | — | — | R0 | 1 |
| product-manager | haiku | medium | 30 | 10 | sonnet | R2 | 1 |
| researcher | sonnet | high | 40 | 20 | opus | R1 | 3 |
| architect | opus | medium | 60 | 30 | — (failure → `needs-human`) | R3 | 1 |
| planner | sonnet | high | 40 | 15 | opus | R2 | 1 |
| developer (and its 10 specialists, section 3) | sonnet (opus for `Complexity: L`) | high | 120 | 45 | opus | R4 | 3 in total (worktrees) |
| qa-engineer | haiku | medium | 50 | 20 | sonnet | R1 | 2 |
| code-reviewer | sonnet | high | 50 | 20 | opus | R1 | 2 |
| security-reviewer | sonnet | high | 50 | 20 | opus | R1 | 2 |
| ux-designer | sonnet | high | 40 | 20 | opus | R2 | 1 |

Every subagent preloads only its skills, keeps lessons in user-scope memory
(`~/.claude/agent-memory/<agent>/MEMORY.md`) and ends with the **result contract**:

```text
STATUS: DONE | BLOCKED | PARTIAL | FAILED
ARTIFACTS: links
EVIDENCE: commands and results
NEXT: what the coordinator should do next
CHECKPOINT: .agent-state/items/<n>.md
```

## 3. Developer specialists

The Developer role runs as the generalist `developer` or as one of ten stack specialists
([ADR-0003](decisions/ADR-0003-stack-specialist-developers.md)). They are variants of one role: same
label, states, permissions (R4), limits and Definition of Done; they differ in the stack skills they
preload and in their memory. The catalogue is [config/specialists.yaml](../config/specialists.yaml).

| Subagent | Stack keys it owns | Preloaded stack skills |
| --- | --- | --- |
| `developer` | none (fallback, cross-stack tasks that cannot be split) | loads `stack-*` on demand |
| `developer-typescript` | `node`, `typescript`, `javascript` | `stack-typescript` |
| `developer-react` | `react`, `react-native` | `stack-react`, `stack-typescript` |
| `developer-nextjs` | `nextjs` | `stack-nextjs`, `stack-react` |
| `developer-angular` | `angular` | `stack-angular`, `stack-typescript` |
| `developer-vue` | `vue` | `stack-vue`, `stack-typescript` |
| `developer-java-spring` | `spring`, `java` | `stack-java-spring` |
| `developer-kotlin-android` | `android`, `kotlin` | `stack-kotlin-android` |
| `developer-python` | `python` | `stack-python` |
| `developer-go` | `go` | `stack-go` |
| `developer-dotnet` | `dotnet` | `stack-dotnet` |

**Routing** (skill [stack-routing](../skills/stack-routing/SKILL.md)):

```mermaid
flowchart LR
    repo[(Target repository)] -->|manifests, CI| detect[detect_stack.py]
    detect --> profile[(.agent-state/stack-profile.json)]
    task[Task Issue<br/>Touches + Stack] --> select[select_specialist.py]
    profile --> select
    select -->|single / explicit| spec[developer-&lt;stack&gt;]
    select -->|split| planner[planner splits the task]
    select -->|fallback| gen[developer]
```

1. The coordinator profiles the repository once per run (and after merges that change build files).
2. The Planner writes `Touches:` and `Stack:` in every task and splits slices that span several stacks.
3. Before delegating, the coordinator runs `select_specialist.py --issue <n>` and adds a
   `Specialist:` line to the brief. Escalation re-delegates to the same specialist with the next model.

**Helper scripts** (Python 3.10+, standard library only, tested in `tests/`):

| Script | Skill | Purpose |
| --- | --- | --- |
| `detect_stack.py` | stack-routing | Modules, stacks, versions, commands and CI steps of a repository |
| `select_specialist.py` | stack-routing | Specialist for a task from the profile and its `Touches`/`Stack` lines |
| `run_checks.py` | development | Run lint, type check, tests and build; baseline and regression comparison; PR evidence rows |
| `repo_map.py` | development | Compact map of files and symbols, focused on the task's paths |
| `impact_scan.py` | development | Tests related to the change; changed files without tests |
| `diff_guard.py` | development | Self-review: secrets, weakened tests, scope, conflict markers, debug code |
| `checkpoint.py` | development | Checkpoint file and its GitHub comment |
| `pr_body.py` | development | Pull Request body that follows the template with the evidence |
| `deps_check.py` | development | Licence, maintenance and advisories of a new dependency (deps.dev, OSV.dev) |

**Generated files.** `python scripts/generate_runtime.py` writes every file in
`templates/runtime/claude/agents/`, `skills/stack-routing/specialists.json` and the specialist block of
`hooks/lib.mjs` from `config/agents.yaml` and `config/specialists.yaml`; `--check` (run by the
validator) fails when they drift. Never edit them by hand.

**Optional extras (off by default).** Both need a human decision and a change to the runtime image or
settings, not to this repository:

- *Code intelligence:* Claude Code's LSP plugins (TypeScript, Java, Kotlin, Python, Go, C#) give
  go-to-definition, references and type errors after each edit. Install the plugin for each stack
  from the plugin marketplace and its language server binary in the runtime image.
- *Current library documentation:* a documentation lookup MCP server or CLI (for example Context7)
  reduces outdated API usage. It sends library names and queries to an external service, so it is a
  data-sharing decision; developers already have `WebFetch` for official documentation.

## 4. Models, usage and context

**Models.** The aliases resolve to pinned versions in `settings.json` (`ANTHROPIC_DEFAULT_SONNET_MODEL`
`claude-sonnet-5-5`, `ANTHROPIC_DEFAULT_OPUS_MODEL` `claude-opus-5-5`, `ANTHROPIC_DEFAULT_HAIKU_MODEL`
`claude-haiku-5-5`); changing a version is one line. Defaults: Sonnet at `high` effort, Opus at `medium`,
Haiku for the product manager and QA, the coordinator at `medium`. Escalation changes only the model
(Claude Code sets effort per subagent definition). The team **never uses Fable**: the validator rejects it
and the `guard-agent` hook denies it on every delegation.

**Task complexity.** The Planner writes `Complexity: S|M|L` in every task. `select_specialist.py` returns
the model: S and M run on the role's model (Sonnet), L on Opus. L means concurrency, security-sensitive
code, data migrations, changes across several modules, or a task that already failed once.

**Usage ledger.** The `usage-ledger` hook appends one line per subagent run (at `SubagentStop`) and per
coordinator turn (at `Stop`, `PreCompact` and `SessionEnd`) to `~/.claude/usage/ledger.jsonl`: agent,
agent id, repository, work item, stage, status, start, end, duration, models, API calls, tool calls,
compactions, input, output, cache-read and cache-write tokens, the last context size, and an
API-equivalent cost from [config/model-pricing.yaml](../config/model-pricing.yaml). It stores numbers and
identifiers only, counts each API request once, and records incrementally so nothing is counted twice.
`~/.claude` is a persistent volume, so the ledger survives conversations. Every line is also copied to
`.agent-state/usage.jsonl` in the conversation's workspace, next to the board and the checkpoints: easy
to find, excluded from git, and lost with the workspace; the global file is the complete history.

```bash
python "$HOME/.claude/skills/orchestration/scripts/usage_report.py" --by agent          # or model, item, repo, day, stage
python "$HOME/.claude/skills/orchestration/scripts/usage_report.py" --item 43 --format github
python "$HOME/.claude/skills/orchestration/scripts/usage_report.py" --ledger .agent-state/usage.jsonl   # this workspace only
```

GitHub gets only the one-line `--format github` summary: in the item's Checkpoint comment and on the
feature Issue when it finishes. The detail stays local.

**Context.** A long session re-sends its whole context on every turn; with 1M-token windows,
auto-compaction used to start too late (a measured session averaged ~425K tokens per call and never
compacted). Now:

| Control | Value | Effect |
| --- | --- | --- |
| `CLAUDE_CODE_AUTO_COMPACT_WINDOW` / `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` | 200000 / 70 | Auto-compaction near 140K tokens; the `PreCompact` and `SessionStart` hooks keep the board across it |
| `BASH_MAX_OUTPUT_LENGTH` | 15000 | Long command output stays out of the context |
| `context-guard` (`PostToolUse`) | `runtime.context_budget_tokens` per role (60K-120K) | Above the budget, the subagent checkpoints and returns `PARTIAL`; the coordinator continues with a fresh subagent on the same model |
| Coordinator discipline | skill orchestration | Board and result contracts only; `gh --json --jq` with the fields needed; never full diffs |

Agents cannot run `/compact` themselves (slash commands are user-only) and no hook can start a
compaction, so these thresholds and the context guard are the automatic mechanism.

## 5. Restriction levels and harness

| Level | Agents | May write | Blocked by hooks |
| --- | --- | --- | --- |
| R0 | coordinator | `.agent-state/` | Any git write, merges, approvals |
| R1 | researcher, qa-engineer, code-reviewer, security-reviewer | Own memory and `.agent-state/` | Any git write; files elsewhere |
| R2 | product-manager, planner, ux-designer | Own memory and `.agent-state/` (Issues and comments through `gh`) | Any git write; files elsewhere |
| R3 | architect | `docs/architecture/`, `docs/decisions/`, `docs/research/` | Pushes other than `docs/*` branches |
| R4 | developer and its specialists | Task files in its worktree | `.github/workflows/`, secret files, pushes other than `feature/`, `bugfix/`, `refactor/` or `chore/` branches |

For everyone, the hooks deny: pushes to `main` or `master`, force pushes, `git merge` while on `main`,
`gh pr merge`, approvals, merge or branch-protection API calls, git identity changes, `--no-verify` and
recursive deletes of `/` or the home directory. Unknown subagents (for example `Explore`) are treated
as R1.

**Harness** ([templates/runtime/claude/settings.json](../templates/runtime/claude/settings.json)):

| Setting | Value | Why |
| --- | --- | --- |
| `autoMemoryEnabled` | `true` | Required for subagent memory |
| `fallbackModel` | sonnet, haiku | Overload or unavailability of a model (one turn) |
| `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` | 1 | Subagents never spawn subagents |
| `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` | 4 | Global parallelism cap |
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | 0 | Named subagents stay subagents |
| `TEAM_REPO` | `<owner>/openhands-agent-team` | Where agents read rules and templates |
| Hooks | see section 10 | Deterministic limits and state |

## 6. Parallelism

| Allowed in parallel | Condition |
| --- | --- |
| Up to 3 researchers | Independent questions |
| 3 developers (any specialists) | No unmet dependency and disjoint `Touches:` sets (declared by the planner), own worktree and branch |
| code-reviewer with security-reviewer (and ux-designer for interface changes) | Same Pull Request, after QA `PASS` |
| Reviews of one Pull Request while a developer works on another task | Always |

Never in parallel: product definition, architecture and planning of one feature; two agents on one
branch; a task that depends on an unmerged Pull Request; QA or reviews of an outdated commit.

## 7. Time budgets and model escalation

Claude Code has no built-in "switch model after N minutes", so the coordinator applies this policy:

1. The `PostToolUse` hook writes `.agent-state/heartbeat/<agent_id>.json` on every tool call.
2. Escalate when the result is `PARTIAL`, no heartbeat arrives for 10 minutes (stop it with `TaskStop`),
   the budget is exceeded without checkpoint progress, or the same validation fails twice.
3. Continue the same subagent with `SendMessage` when it is alive; otherwise delegate the same brief again
   with the invocation `model` parameter set to the next model of the role's `escalation` list. The brief
   points to the checkpoint and the branch, so work continues instead of restarting.
4. One escalation per item; a second failure becomes `blocked` + `needs-human`.
5. API or usage-limit errors: the `StopFailure` hook writes `.agent-state/paused.json`; the next start
   resumes from the checkpoints.

## 8. Memory and context

| Layer | Where | What | Who |
| --- | --- | --- | --- |
| L1 GitHub | Issues, Pull Requests, comments, reviews | Requirements, plans, reports, verdicts | Everyone |
| L2 Checkpoint | `.agent-state/items/<n>.md` + a "Checkpoint" comment on the item | Goal, done, next, branch, last commit, validation, attempt, model | The working subagent |
| L3 Team board | `.agent-state/board.md` + a "Team board" comment on the feature Issue | Items, states, owners, agent ids, timings, waits | Coordinator |
| L4 Individual memory | `~/.claude/agent-memory/<agent>/MEMORY.md` | Lessons for the role across projects (≤ 200 lines) | Each subagent |
| L5 Project knowledge | The project's `AGENTS.md` | Commands, conventions, pitfalls | Through Pull Requests |

Context rules:

- The coordinator sends a **brief** (work item, directory, checkpoint, inputs, constraints, done-when),
  never the conversation.
- Subagents answer with the **result contract** (≤ 40 lines); the `SubagentStop` hook asks once for it
  when it is missing.
- The coordinator keeps only the board and reads full artifacts only to decide a transition.
- `.agent-state/` is excluded from git by the `SessionStart` hook (`.git/info/exclude`).

## 9. Recovery

| What stopped | How work continues |
| --- | --- |
| A subagent | `SendMessage` to resume it, or a new subagent from the checkpoint on the same branch |
| A developer before the end | Its draft Pull Request and pushed commits hold the work; the next developer starts from them |
| Context compaction | `PreCompact` snapshots the board; `SessionStart` re-injects it |
| Usage limit or API error | `paused.json` tells the next run to resume from checkpoints |
| The conversation | A new conversation with `reanuda #<issue>` rebuilds from the GitHub "Team board" and "Checkpoint" comments |

## 10. Validations and preventions

| Layer | File | Effect |
| --- | --- | --- |
| `PreToolUse` Bash | `hooks/guard-bash.mjs` | Global denials, per-level git limits, git safety-net bypasses, secrets in commands, secrets and private data in published text |
| `PreToolUse` Edit/Write | `hooks/guard-files.mjs` | Per-level write paths, no secret files, no workflow files, no secrets in content |
| `PreToolUse` MCP | `hooks/guard-publish.mjs` | Secrets in any MCP call; private data in GitHub writes |
| `PostToolUse` | `hooks/heartbeat.mjs`, `hooks/context-guard.mjs` | Stall detection; context budget per role |
| `PreToolUse` Agent | `hooks/guard-agent.mjs` | No Fable or Mythos model on any delegation |
| `SubagentStop`, `Stop`, `PreCompact`, `SessionEnd` | `hooks/usage-ledger.mjs` | Time and usage ledger |
| `SubagentStop` | `hooks/subagent-stop.mjs` | Result contract, event log |
| `SessionStart` | `hooks/session-start.mjs` | Excludes `.agent-state/`, re-injects the board |
| `PreCompact` | `hooks/pre-compact.mjs` | Board snapshot |
| `StopFailure` | `hooks/stop-failure.mjs` | Pause marker |
| git `pre-commit` | `githooks/pre-commit` | Staged secrets, secret files, files over 1 MB, conflict markers |
| git `commit-msg` | `githooks/commit-msg` | Conventional Commits, no `Co-Authored-By`, no secrets or private data |
| git `pre-push` | `githooks/pre-push` | Never `main`, branch names, secret scan of pushed commits |
| Policy | `config/secret-patterns.tsv` (copies in `hooks/`, `githooks/`, `skills/development/scripts/`) | One list of secret, private-data and allow rules for every layer |
| CI | gitleaks in `validate-repository` and the kit's `secret-scan` | Whole-history scan with an independent rule set |
| GitHub | branch protection, squash only, `pr-conventions`, `ci` | Pull Requests cannot merge with `changes-requested` or failing checks |

All of them are tested in CI: `node templates/runtime/claude/hooks/test-hooks.mjs`,
`node scripts/test_workflows.mjs` and `python -m unittest discover -s tests`. The hooks fail closed: if
the policy file is missing, they deny and ask to reinstall `~/.claude/hooks`. Set `TEAM_GITLEAKS=1` in
the runtime to add a local gitleaks scan to `pre-commit` and `pre-push` when the binary is installed.

## 11. Token use

- haiku for product management and QA, sonnet by default, opus for the architect, `Complexity: L` tasks
  and escalations; never fable. Measure with the usage ledger before changing a default.
- Effort per role; only the role's skills preloaded; fewer tools mean fewer tool schemas in context.
- Short briefs and result contracts; reviewers read `gh pr diff` and the touched files.
- One clone and one install per conversation; worktrees share the git objects.
- Code and security reviews in parallel instead of in sequence.
- Stack knowledge lives in skills preloaded only by the specialist that needs it, with deep
  `references/` loaded on demand; scripts summarise long command output instead of pasting it.

## 12. Installing the runtime

Run once per OpenHands deployment, as an administrator. `<VOL>` is the host path of the volume mounted at
`/home/openhands/.claude` (find it with `findmnt -T ~/.claude` inside the container), and `10001` the
container user.

1. Copy the files into the volume and give them to the container user:

   ```bash
   git clone --depth 1 https://github.com/<owner>/openhands-agent-team.git /tmp/team
   sudo cp -R /tmp/team/templates/runtime/claude/agents /tmp/team/templates/runtime/claude/hooks \
     /tmp/team/templates/runtime/claude/githooks /tmp/team/templates/runtime/claude/settings.json <VOL>/
   sudo cp /tmp/team/templates/runtime/claude-user-memory.md <VOL>/CLAUDE.md
   sudo mkdir -p <VOL>/skills && sudo cp -R /tmp/team/skills/*/ <VOL>/skills/
   sudo chmod 755 <VOL>/githooks/* <VOL>/skills/*/scripts/*.py
   sudo chown -R 10001:10001 <VOL>
   ```

   Then edit `TEAM_REPO` in `<VOL>/settings.json` (and `<owner>` in `<VOL>/CLAUDE.md` if present) to the real owner.
   The image needs Python 3.10+ on `PATH` for the skill scripts (no packages). Before copying,
   `python scripts/generate_runtime.py --check` must pass in the team repository.
2. In the deployment's environment variables (for example Coolify), activate the git hooks and keep the
   identity variables:

   ```text
   GIT_CONFIG_COUNT=1
   GIT_CONFIG_KEY_0=core.hooksPath
   GIT_CONFIG_VALUE_0=/home/openhands/.claude/githooks
   GIT_AUTHOR_NAME / GIT_AUTHOR_EMAIL / GIT_COMMITTER_NAME / GIT_COMMITTER_EMAIL
   ```

3. In OpenHands, create the Agent Profile `team`: type ACP, Claude Code, model `sonnet`,
   `acp_prompt_timeout` 3600, secret scope Selected with `GITHUB_TOKEN`. The previous per-role profiles
   are no longer needed.
4. In each target repository: labels from `config/workflow.yaml` (including `changes-requested`),
   `pr-conventions.yml` and `ci.yml` from [templates/target-repo/](../templates/target-repo/README.md),
   squash-only merging and branch protection.
5. Check: start a conversation with `team` and write `estado`. The coordinator must answer as
   coordinator and list the subagents.

## 13. Using the team

| You write | What happens |
| --- | --- |
| `Build: <idea>` | New feature: requirements, design, plan, tasks, pull requests |
| `Fix: <bug>` | Reproduction, task, fix |
| `continúa` | After you merged a Pull Request or accepted an ADR |
| `reanuda #<issue>` | In a new conversation, to continue a feature |
| `estado` | Board and pending human actions |

The coordinator ends every run with a list of what waits on you (ADR Pull Requests, Pull Requests to
merge, `needs-human` questions) and what is still running.

## 14. Pilot checklist

- One message reaches the ADR, and after accepting it the pull requests, without other questions.
- At most three developers at once, in different worktrees and branches; reviews run in parallel after QA.
- In a repository with two stacks, each task goes to the specialist `select_specialist.py` names, and the
  brief carries the `Specialist:` line.
- Every Pull Request: Conventional Commits, one `Closes`, `pr-conventions` and `ci` green, author is your
  identity, no co-author; nobody merged or pushed to `main`.
- Verdicts are review comments with headers and the `changes-requested` label when needed; reviewers did
  not edit files.
- Recovery drills: stop a developer mid-task, close the conversation and `reanuda`, force a low turn limit
  to see escalation.
- Asking an agent to `git push origin main` or `gh pr merge` is denied by a hook.

## 15. Known limits

- Whether the ACP adapter loads `~/.claude/agents`, hooks and settings, and supports worktree isolation
  and background subagents, is confirmed in the pilot; skills from `~/.claude/skills` are already loaded.
- With one GitHub identity, verdicts rely on the label and hooks; branch protection level 2 needs machine
  users.
- Usage of the subscription with opus in the architect and escalations is measured in the pilot.
