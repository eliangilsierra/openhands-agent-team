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

### 3.3 LLM profiles (OpenHands-type agents)

- [ ] Create at least one LLM profile for routine roles (Product Manager, Planner, QA Engineer,
      Orchestrator) and, if desired, a stronger one for Researcher and Security Reviewer.

### 3.4 MCP servers

- [ ] Configure the initial MCP servers described in [mcp-integration.md](mcp-integration.md).

### 3.5 Agent Profiles

Create one profile per row. Secrets come from `secrets` in
[config/permissions.yaml](../config/permissions.yaml); MCP references implement the `github` and
`web` capabilities in `mcp` of [config/agents.yaml](../config/agents.yaml).

| Profile name | Agent type | LLM / ACP | OpenHands MCP server references | Secrets (scope: Selected) |
| --- | --- | --- | --- | --- |
| `product-manager` | OpenHands | routine LLM profile | github | `GITHUB_TOKEN` |
| `researcher` | OpenHands | research LLM profile | github (+ fetch, if configured) | `GITHUB_TOKEN` |
| `architect` | ACP | Claude Code | configured in Claude Code (see ACP doc) | `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`* |
| `planner` | OpenHands | routine LLM profile | github | `GITHUB_TOKEN` |
| `developer` | ACP | Claude Code | configured in Claude Code (see ACP doc) | `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`* |
| `qa-engineer` | OpenHands | routine LLM profile | github | `GITHUB_TOKEN` |
| `code-reviewer` | ACP | Claude Code | configured in Claude Code (see ACP doc) | `GITHUB_TOKEN`, `ANTHROPIC_API_KEY`* |
| `security-reviewer` | OpenHands | strong LLM profile | github (+ fetch, if configured) | `GITHUB_TOKEN` |
| `orchestrator` | OpenHands | routine LLM profile | github | `GITHUB_TOKEN` |

\* Only when Claude Code is not authenticated with a subscription login in the runtime.

The filesystem/repository capability is provided by the runtime's built-in file and shell tools
for OpenHands-type agents and by Claude Code's own tools for ACP agents; no separate filesystem MCP
server is needed initially (see [mcp-integration.md](mcp-integration.md)).

- [ ] If your agent server does not support per-profile secret scoping, note that every profile
      receives every secret, and compensate by keeping the secret set minimal (one GitHub token
      with least privilege).

### 3.6 Skills

- [ ] Install the Skills (section 4).
- [ ] Start a conversation with each profile and ask it to list the Skills it can see. Record the
      result. For ACP profiles, see the known limitation in
      [acp-integration.md](acp-integration.md#10-skills-and-agentsmd-for-acp-profiles).

### 3.7 Smoke test

- [ ] Run the manual phase-1 workflow from [automation.md](automation.md) on a small task in a test
      repository and confirm that branch protection prevents the agent identity from merging.

## 4. Installing Skills

Every directory in [skills/](../skills/README.md) is a self-contained `SKILL.md` package whose
frontmatter `name` equals the directory name, as OpenHands requires for portable skills. Choose
one installation scope (*Official* scopes; *Convention* for which one to pick):

| Scope | Location | When to use |
| --- | --- | --- |
| User (runtime-wide) | `~/.agents/skills/<name>/SKILL.md` in the OpenHands runtime | Recommended for a single self-hosted installation: all target repositories get the same team Skills |
| Organisation | Organisation skills, where your OpenHands edition supports them | Teams using organisation-level management |
| Repository / project | `<target-repo>/.agents/skills/<name>/SKILL.md` | When a target repository must pin a specific Skill version |

Installing at user scope (run inside the environment whose home directory the agent server uses):

```bash
git clone --depth 1 https://github.com/<owner>/openhands-agent-team.git /tmp/openhands-agent-team
mkdir -p ~/.agents/skills
cp -R /tmp/openhands-agent-team/skills/*/ ~/.agents/skills/
```

`skills/README.md` is not a Skill and is not copied (the glob copies directories only).

Re-run the copy after every change to `skills/` on `main`. *Convention:* record the commit SHA
you installed in the runtime notes so drift can be detected.

## 5. Target repository setup

Each application repository the team works on should contain:

| File | Content |
| --- | --- |
| `AGENTS.md` | Project facts (stack, commands for test/lint/build, structure, conventions) followed by the team contract: either a copy of this repository's [AGENTS.md](../AGENTS.md) or a short section that states it applies and links to it. *Official:* OpenHands loads the repository root `AGENTS.md` as always-on context. |
| `CLAUDE.md` | For ACP profiles: Claude Code reads `CLAUDE.md` natively. Make it import the shared contract with a line containing only `@AGENTS.md`, so both backends receive the same rules. |
| `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md` | Copied from this repository. |
| `.github/CODEOWNERS` | Human owners. |
| `docs/decisions/`, `docs/architecture/` | Created by the Architect when first needed. |
| CI workflows | Build, lint and test jobs used as required status checks. |

## 6. Starting work (phase 1)

1. Pick the work item (Issue or Pull Request) and identify its owner from the `agent:*` label.
2. Start a new conversation in OpenHands using the Agent Profile with the same name, on the
   target repository.
3. Paste the activation prompt from the role file (for example
   [agents/developer.md](../agents/developer.md#activation-prompt)) with the variables filled in.
4. Let the agent finish its stage. Check that it persisted its artifact and handed off the label.

## 7. Keeping runtime and specification aligned

- Changes to `config/agents.yaml`, `config/permissions.yaml` or `skills/` require a matching
  runtime change. The Pull Request description must list the runtime steps, and the human merging
  it performs them (or opens an Issue to do so).
- Review the runtime against the checklist in section 3 after every OpenHands upgrade.
