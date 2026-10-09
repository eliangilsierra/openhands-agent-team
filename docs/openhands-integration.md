# OpenHands Integration

OpenHands is the agent execution platform. This repository is the **source of truth for agent
behaviour and process**; OpenHands is the **source of truth for runtime configuration**. This
document defines the boundary between the two and the steps to configure OpenHands so that it
matches this specification.

> **Verification note.** Statements marked *Official* were checked against the OpenHands
> documentation at <https://docs.openhands.dev> on 2026-10-01 (Agent Canvas release line 1.x).
> Statements marked *Convention* are rules of this repository. Statements marked *Conceptual*
> describe intent where exact fields depend on the installed OpenHands version — verify them in
> your installation before relying on them. No configuration file in this repository is read by
> OpenHands.

## 1. What belongs where

### Belongs in GitHub (this repository)

- Skills ([skills/](../skills/README.md))
- Agent role definitions ([agents/](../agents/README.md))
- Documentation ([docs/](architecture.md))
- Templates ([templates/](../templates/requirements.md))
- Workflow specification ([config/workflow.yaml](../config/workflow.yaml))
- Permission specification ([config/permissions.yaml](../config/permissions.yaml))
- ADRs ([docs/decisions/](decisions/README.md))
- Team conventions ([AGENTS.md](../AGENTS.md), [CONTRIBUTING.md](../CONTRIBUTING.md))

### Belongs in the OpenHands runtime

- Agent Profiles (one per role)
- Runtime configuration (sandbox, agent server, Agent Canvas settings)
- Model configuration (LLM profiles)
- MCP server configuration
- ACP configuration (Claude Code agent settings)
- Secrets and credentials

### Must never be stored in Git

- API keys (Anthropic, OpenAI, other LLM providers, search APIs)
- OAuth tokens
- Claude credentials (for example `~/.claude/.credentials.json`)
- GitHub tokens (personal access tokens, App private keys, installation tokens)
- Passwords
- Private keys and certificates
- `.env` files containing secrets
- Exported OpenHands settings or MCP files that embed tokens

See [SECURITY.md](../SECURITY.md). The validation workflow scans for common secret patterns, but
scanning is a safety net, not a permission.

## 2. Concepts and how they map

| Concept | What OpenHands provides | How this repository uses it |
| --- | --- | --- |
| **Agent Profile** | *Official:* reusable configuration selecting which agent runs a conversation — the built-in OpenHands agent (linked to an LLM profile) or an ACP agent such as Claude Code. Managed in Agent Canvas under `Settings > Agent`. A profile can scope MCP server access and (when the agent server supports it) the secrets it receives ("All", "None" or "Selected"). The profile cannot be switched during a conversation. | One profile per agent in [config/agents.yaml](../config/agents.yaml). *Convention:* the profile name equals the agent id (`developer`, `code-reviewer`, …). |
| **LLM profile** | *Official:* provider, model and credentials for OpenHands-type profiles (`Settings > LLM`). ACP profiles do not use it. | *Convention:* choose models per role cost/quality; record the choice in your runtime notes, not in Git. |
| **Skills** | *Official:* `SKILL.md` files with `name`/`description` frontmatter; discovered in repository (`AGENTS.md`, `.agents/skills/`), project (`.agents/skills/`), user (`~/.agents/skills/`) and organisation scopes; legacy `.openhands/skills/` and `.openhands/microagents/` remain supported. Root `AGENTS.md` is always-on context; `SKILL.md` content is loaded on demand from its description. | Skills are authored in [skills/](../skills/README.md) in that format and installed (section 4). |
| **MCP** | *Official:* SHTTP, SSE and stdio servers configured via Agent Canvas (`Customize > MCP Servers`), the CLI (`openhands mcp add`, stored in `~/.openhands/mcp.json`) or the SDK. Current releases no longer read the legacy `config.toml` `[mcp]` section. | See [mcp-integration.md](mcp-integration.md). |
| **ACP** | *Official:* Agent Profiles of ACP type run an external agent (Claude Code, Codex, Gemini CLI) over the Agent Client Protocol. | Architect, Developer, Code Reviewer. See [acp-integration.md](acp-integration.md). |
| **Secrets** | *Official:* `Settings > Secrets`; each secret has a name and value and is exported to the agent runtime as an environment variable of that name; values are not displayed after saving. | Secret names per role are in [config/permissions.yaml](../config/permissions.yaml) (`secrets`). |
| **Automations** | *Official:* scheduled and event-based automations; GitHub event triggers are documented for OpenHands Cloud with the OpenHands GitHub App. | Phase 2+ only. See [automation.md](automation.md). |

## 3. Runtime setup checklist

Perform these steps as an OpenHands administrator. Exact menu names may differ between versions.

### 3.1 Platform

- [ ] Install OpenHands (self-hosted, for example as a Coolify service) following the official
      installation guide for your version.
- [ ] Confirm the agent server is reachable from Agent Canvas.
- [ ] Restrict access to the OpenHands UI to the team (authentication / network restrictions of
      your hosting platform).

### 3.2 Secrets

- [ ] Create a GitHub credential for the agent identity (see
      [github-integration.md](github-integration.md#agent-identity)) and provide it to OpenHands —
      through the Git provider integration if your version offers one, or as a secret named
      `GITHUB_TOKEN`. *Convention:* this document and `config/permissions.yaml` call it `GITHUB_TOKEN`.
- [ ] If ACP profiles use an Anthropic API key instead of a Claude subscription login, create a
      secret named `ANTHROPIC_API_KEY` (*Official:* the name must match the environment variable
      Claude Code reads).
- [ ] Create any MCP credentials (for example a search API key) as secrets.

### 3.3 LLM profiles

Not needed for the team: since ADR-0002 every role runs on Claude Code through the `team` profile.
Keep LLM profiles only for conversations outside the team.

### 3.4 MCP servers

- [ ] Configure the initial MCP servers described in [mcp-integration.md](mcp-integration.md).

### 3.5 Agent Profile

Since ADR-0002 the team needs **one** Agent Profile:

| Profile name | Agent type | ACP settings | Secrets (scope: Selected) |
| --- | --- | --- | --- |
| `team` | ACP | Claude Code, `acp_model` `sonnet`, `acp_prompt_timeout` 3600 | `GITHUB_TOKEN` |

Claude Code authenticates with the subscription login stored in the persistent `~/.claude` volume (or
`ANTHROPIC_API_KEY` if you prefer an API key; do not configure both). The roles are Claude Code
subagents installed in that volume; installation steps are in
[docs/subagents.md](subagents.md#12-installing-the-runtime). Per-role profiles from the previous design
(archive branch `archive/multi-profile-team`) can be deleted.

### 3.6 Skills

- [ ] Install the Skills with one route from section 4 (recommended order: A, then C).
- [ ] Start a conversation with each profile and ask it to list the Skills it can see. Record the
      result and the route used. For ACP profiles, see the known limitation in
      [acp-integration.md](acp-integration.md#10-skills-and-agentsmd-for-acp-profiles).

### 3.7 Smoke test

- [ ] Run the manual phase-1 workflow from [automation.md](automation.md) on a small task in a test
      repository and confirm that branch protection prevents the agent identity from merging.

## 4. Installing Skills

Every directory in [skills/](../skills/README.md) is a self-contained `SKILL.md` package whose
frontmatter `name` equals the directory name, as OpenHands requires for portable skills. The
repository root also contains [plugin.json](../plugin.json), which makes the whole repository a
plugin in the portable *Agent Plugins* format.

*Official* (OpenHands documentation, checked 2026-10-01): a root `plugin.json` with `$schema` and
`name` is the only mandatory file of an Agent Plugins package; skills are discovered
non-recursively at `skills/<name>/SKILL.md`, so `skills/README.md` and every other directory of this
repository are ignored by the plugin loader; roles in this repository's `agents/` are **not** loaded
as plugin agents (the portable format reads agents from `dev.openhands/agents/`). Agent Canvas lists
plugins on the **Plugins** page of the sidebar, where installed plugins can be inspected, enabled,
disabled and uninstalled, and plugins found in `~/.agents/plugins` or `~/.openhands/plugins` appear as
read-only **Local** plugins that must be confirmed. Enabled installed plugins are available to new
conversations on that backend automatically.

Choose **one** route at a time; installing the same Skills through two routes can duplicate them.

| Route | How | Documentation status | Use when |
| --- | --- | --- | --- |
| **A. Local plugin directory** | Clone this repository into `~/.agents/plugins/openhands-agent-team`, open **Plugins**, confirm the Local plugin | Directory and *Local* status are official; the exact confirmation flow depends on your version | First choice: no authentication needed in the UI, works with a private repository |
| **B. Install from a Git source** | In **Plugins**, install from a source such as `github:<owner>/openhands-agent-team`, optionally pinned to a tag (`#v0.1.0`) | Source syntax is official for loading plugins; the Agent Canvas steps for custom sources and private repositories are **not documented** | You want version pinning and updates from the UI; verify access to a private repository first |
| **C. User skills directory** | Copy the Skill directories into `~/.agents/skills/` (below) | Official | Fallback when plugins do not work in your version |

### Route A — local plugin directory

Run where the agent server's home directory lives. With the Docker image, mount the host directory
(never `~/.openhands/skills`, which would overwrite the public skills cache):

```bash
mkdir -p ~/.agents/plugins
git clone --depth 1 https://github.com/<owner>/openhands-agent-team.git ~/.agents/plugins/openhands-agent-team
```

```text
-v "$HOME/.agents/plugins:/home/openhands/.agents/plugins:ro"
```

Then open **Plugins**, find `openhands-agent-team` with status *Local*, and confirm it. Update it
with `git pull` in that directory and restart the backend if the Skills do not refresh.

### Route B — install from a Git source

Use the **Plugins** page. Pin to a release tag for reproducibility once the repository publishes
tags. If installing from a private repository fails, use route A or C.

### Route C — user skills directory

```bash
git clone --depth 1 https://github.com/<owner>/openhands-agent-team.git /tmp/openhands-agent-team
mkdir -p ~/.agents/skills
cp -R /tmp/openhands-agent-team/skills/*/ ~/.agents/skills/
```

`skills/README.md` is not a Skill and is not copied (the glob copies directories only). Other
scopes exist (*Official*): organisation skills, and `<target-repo>/.agents/skills/<name>/SKILL.md` when
a target repository must pin a Skill version. The `/add-skill <github-url>` chat command installs a
single Skill into the **workspace** `.agents/skills/` and uses `GITHUB_TOKEN` for private repositories.

### Verification

Re-run the update after every change to `skills/` on `main`, and record the commit SHA you
installed in the runtime notes so drift can be detected. After installing, start a conversation with
an OpenHands-type profile and ask it to list the Skills it can see.

*Known limitation:* the same applies to Skills delivered by plugins in ACP sessions: in versions
affected by [OpenHands/OpenHands#16905](https://github.com/OpenHands/OpenHands/issues/16905) enabled
Skills may not reach Claude Code. The mitigation in
[acp-integration.md](acp-integration.md#10-skills-and-agentsmd-for-acp-profiles) (read the `SKILL.md`
from this repository) works regardless of route.

## 5. Target repository setup

Each application repository the team works on should contain:

| File | Content |
| --- | --- |
| `AGENTS.md` | Project facts (stack, commands for test/lint/build, structure, conventions) followed by the team contract: either a copy of this repository's [AGENTS.md](../AGENTS.md) or a short section that states it applies and links to it. *Official:* OpenHands loads the repository root `AGENTS.md` as always-on context. |
| `CLAUDE.md` | For ACP profiles. *Official* (Claude Code memory documentation): Claude Code reads `AGENTS.md` directly only when the project has no `CLAUDE.md`, and only from version 2.1.277. A `CLAUDE.md` whose content is a line with `@AGENTS.md` works with every version and keeps the same rules for both backends. |
| `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md` | Copied from this repository. |
| `.github/CODEOWNERS` | Human owners. |
| `.github/workflows/pr-conventions.yml` | Deterministic check of branch name, Conventional Commits title and commits, and exactly one closing keyword. |
| `docs/decisions/`, `docs/architecture/` | Created by the Architect when first needed. |
| CI workflows | Build, lint and test jobs used as required status checks. |

Ready-made copies of the project `AGENTS.md`, `CLAUDE.md` and `pr-conventions.yml` are in
[templates/target-repo/](../templates/target-repo/README.md). Agents cannot add or change files under
`.github/workflows/`, so a human copies the workflow in.

### Workspace

*Official:* each conversation has a workspace, "the folder, repository, container mount, or cloud
sandbox the agent works in". The OpenHands interface shows the files and changes of that folder. In
the Docker setup the folder of a conversation looks like
`/home/openhands/workspace/project/<conversation-id>`.

*Convention* ([AGENTS.md](../AGENTS.md#16-conversation-scope-and-workspace)): the agent works in that
folder, clones the target repository there and reads the team repository with `gh api`. Cloning into
another directory (for example a shared `/projects` mount) hides the work from the interface and mixes
the work of different conversations. Every conversation starts with a fresh workspace, so GitHub is
the only state shared between stages.

### Git identity

OpenHands sets a default git identity (`OpenHands <openhands@anthropic.com>`). To make commits carry
a person's identity instead, define these four environment variables in the runtime of the OpenHands
deployment (for example Coolify environment variables) and redeploy. Git gives environment variables
precedence over any `user.name` and `user.email` configuration, so the setting reaches every process,
including the Claude Code subprocess:

```text
GIT_AUTHOR_NAME=<Your Name>
GIT_AUTHOR_EMAIL=<id>+<github-user>@users.noreply.github.com
GIT_COMMITTER_NAME=<Your Name>
GIT_COMMITTER_EMAIL=<id>+<github-user>@users.noreply.github.com
```

These values are not secrets, but they are runtime configuration and do not belong in Git. Because
commits then show the person as author, history no longer distinguishes what an agent wrote; the
Pull Request, its labels and its reviews remain the record of which agent did what.

### Global Claude Code memory

ACP profiles have no field for role instructions. Claude Code reads `~/.claude/CLAUDE.md` in every
session (*Official*), and in the Docker setup `~/.claude` is a persistent volume. A short file there
holds what is common to all roles: where the team repository is, how the role is selected, language
and GitHub authentication. [templates/runtime/claude-user-memory.md](../templates/runtime/claude-user-memory.md)
contains the text to install; copy it to the volume as `CLAUDE.md` owned by the container user.
Claude Code treats memory as context, not as enforced configuration, so the activation message
repeats the essential rules.

## 6. Starting work

1. Start a **new** conversation in OpenHands with the Agent Profile `team` (chat launcher, `+` menu,
   **Switch agent profile**).
2. Write one message: `Build: <idea>` for a new feature, `Fix: <bug>`, `continúa` after you merged a
   Pull Request or accepted an ADR, `reanuda #<issue>` to continue a feature in a new conversation, or
   `estado`.
3. The coordinator clones the target repository into the workspace, delegates each stage to a subagent
   and stops only for ADR acceptance and merges, with a list of what waits on you
   ([docs/subagents.md](subagents.md#13-using-the-team)).

## 7. Keeping runtime and specification aligned

- Changes to `config/agents.yaml`, `config/permissions.yaml` or `skills/` require a matching
  runtime change. The Pull Request description must list the runtime steps, and the human merging
  it performs them (or opens an Issue to do so).
- Review the runtime against the checklist in section 3 after every OpenHands upgrade.
