# Runtime files

Text to install in the OpenHands runtime. Nothing here is read from Git by OpenHands.

| File | Install as | Purpose |
| --- | --- | --- |
| [claude-user-memory.md](claude-user-memory.md) | `~/.claude/CLAUDE.md` of the user that runs the agent server | Shared rules loaded by the coordinator and every subagent; tells the main session it is the coordinator |
| [claude/agents/](claude/agents/) | `~/.claude/agents/` | The eight role subagents, generated from `config/agents.yaml` |
| [claude/settings.json](claude/settings.json) | `~/.claude/settings.json` | Harness: memory, fallback models, limits, hooks; set `TEAM_REPO` |
| [claude/hooks/](claude/hooks/) | `~/.claude/hooks/` | Claude Code hooks (Node.js) and their tests |
| [claude/githooks/](claude/githooks/) | `~/.claude/githooks/`, activated with `GIT_CONFIG_*` | `commit-msg` and `pre-push` |

Installation steps: [docs/subagents.md](../../docs/subagents.md#10-installing-the-runtime).

In the Docker setup `~/.claude` is a persistent volume, so the file is created once at the root of that
volume, owned by the container user (for example UID 10001), and survives redeployments.

Claude Code treats memory as context, not as enforced configuration, so the activation message in each
role file repeats the essential rules. See
[docs/openhands-integration.md](../../docs/openhands-integration.md#global-claude-code-memory).
