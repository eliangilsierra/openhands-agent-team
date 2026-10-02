# Runtime files

Text to install in the OpenHands runtime. Nothing here is read from Git by OpenHands.

| File | Install as | Purpose |
| --- | --- | --- |
| [claude-user-memory.md](claude-user-memory.md) | `~/.claude/CLAUDE.md` of the user that runs the agent server | Global Claude Code memory for every ACP profile: where the team repository is, how the role is selected, the rules that must not be broken |

In the Docker setup `~/.claude` is a persistent volume, so the file is created once at the root of that
volume, owned by the container user (for example UID 10001), and survives redeployments. Replace
`<owner>` with the owner of the team repository before installing it.

Claude Code treats memory as context, not as enforced configuration, so the activation message in each
role file repeats the essential rules. See
[docs/openhands-integration.md](../../docs/openhands-integration.md#global-claude-code-memory).
