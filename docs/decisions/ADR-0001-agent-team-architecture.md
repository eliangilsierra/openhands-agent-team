# ADR-0001: Use GitHub, OpenHands, Agent Profiles, Skills, MCP, ACP / Claude Code and GitHub Actions as the agent team architecture

## Status

Accepted

| Field | Value |
| --- | --- |
| Date proposed | 2026-10-01 |
| Date decided | 2026-10-01 |
| Decided by | Repository owner, by merging the initial version of this repository |
| Related Issue | Initial repository setup |
| Supersedes | None |
| Related ADRs | None |

## Context

We want a self-hosted, multi-agent software engineering team in which specialised AI agents take
work from idea to Pull Request, while humans keep final approval over anything that reaches a
protected branch.

Forces:

- **Traceability.** Every requirement, decision, review and test result must be inspectable and
  auditable after the fact, by humans and by other agents.
- **Specialisation.** Roles (product, research, architecture, planning, development, QA, code
  review, security review, orchestration) need different instructions, tools and permissions.
- **Cost and capability.** Some roles need deep multi-file reasoning; others are routine and
  should run on cheaper, interchangeable models.
- **Operational simplicity.** A small team must be able to run, understand and debug the platform.
  Every additional service adds deployment, upgrades, monitoring, backup and security work.
- **Safety.** Agents must not be able to merge, push to `main` or exfiltrate secrets, and
  instructions must not be the only control.
- **Platform facts (verified against the OpenHands documentation on 2026-10-01):**
  - OpenHands Agent Canvas supports *Agent Profiles* configured under `Settings > Agent`, each
    running either the built-in OpenHands agent (with an LLM profile) or an *ACP* agent such as
    Claude Code; profiles can scope MCP servers and secrets.
  - OpenHands supports *Skills* as `SKILL.md` files with `name`/`description` frontmatter in
    repository, project, user and organisation scopes, and loads a repository's `AGENTS.md` as
    always-on context.
  - OpenHands supports MCP servers over SHTTP, SSE and stdio, configured through the UI, the CLI
    or the SDK.

## Decision

We will build the team from the following parts, and nothing more, in the initial phase:

| Part | Role in the architecture |
| --- | --- |
| **GitHub** | Source of truth for code, Issues, Pull Requests, reviews, labels (workflow state), documentation, ADRs and this team specification. |
| **OpenHands** | The single agent execution platform: one installation, sandboxed runtimes, conversations per work item. |
| **Agent Profiles** | One OpenHands Agent Profile per role in [config/agents.yaml](../../config/agents.yaml), configured in the OpenHands runtime to match the role files in [agents/](../../agents/README.md). |
| **Skills** | Reusable procedures in [skills/](../../skills/README.md), versioned here and installed into the runtime. |
| **MCP** | Tool integrations: GitHub, filesystem/repository, web/research — see [docs/mcp-integration.md](../mcp-integration.md). |
| **ACP + Claude Code** | Execution backend for the Architect, Developer and Code Reviewer profiles, which need deep multi-file reasoning. Other profiles stay model-agnostic on the built-in OpenHands agent. |
| **GitHub Actions** | Deterministic validation (lint, test, build, repository validation). Never depends on OpenHands being online. |
| **Humans** | Approve ADRs, risk acceptance, changes to team configuration, and every merge. |

The team's behaviour, process and permissions are specified in this repository as Markdown and
YAML. Runtime configuration (profiles, models, MCP connections, secrets) lives in OpenHands and is
configured to match the specification. Automation is introduced in phases, starting from manual
execution (see [docs/automation.md](../automation.md)).

## Alternatives

| Alternative | Summary | Why not chosen now |
| --- | --- | --- |
| **LiteLLM** (LLM gateway/proxy) | Central proxy for model routing, budgets and keys across providers | OpenHands LLM profiles already select models per profile, and Claude Code manages its own model through ACP. A gateway adds a service to deploy, secure and monitor without solving a current requirement. Reconsider when we need cross-provider budget enforcement, central key management or usage reporting that OpenHands does not provide. |
| **n8n as primary orchestrator** | Visual workflow engine triggering agents on events | Workflow state would be split between n8n and GitHub, breaking the single source of truth. GitHub labels, Actions and OpenHands' own automation features cover the first automation phases. Reconsider if event routing grows beyond what GitHub Actions and OpenHands automations can express. |
| **Mattermost** (or another chat platform) | Chat-based coordination between humans and agents | Conversations in chat are hard to trace back to Issues and Pull Requests and duplicate GitHub notifications. GitHub comments and mentions are sufficient. Reconsider if humans need real-time interaction that GitHub cannot provide. |
| **Kubernetes** | Container orchestration for agent runtimes | One OpenHands installation with sandboxed runtimes does not need a cluster. Kubernetes would dominate operational effort. Reconsider when concurrency or isolation requirements exceed a single host. |
| **Separate server, container or OpenHands instance per agent** | Each role runs as its own long-lived service | Multiplies deployment, upgrades, credentials and monitoring by nine. Agent Profiles provide role separation inside one platform. Reconsider if a role needs hard isolation (different network, different credentials boundary) that profile-level secret scoping cannot provide. |
| **Separate project-management tool or agent database** | Track agent work outside GitHub | Duplicates GitHub Issues and creates synchronisation problems. |
| **Claude Code for every role** | All profiles use ACP | Higher cost and vendor coupling for routine roles that do not need it; keeps no model flexibility. |
| **No ACP; built-in agent for every role** | Only OpenHands agent with LLM profiles | Loses Claude Code's tooling and reasoning for the roles where it matters most (architecture, implementation, semantic review). |

None of these technologies is prohibited. Each can be introduced later through a new ADR that
supersedes or amends this one, when a documented requirement justifies the added operational cost.

## Consequences

**Positive**

- One place (GitHub) to understand the state of any work item; agents and humans read the same record.
- Minimal infrastructure: GitHub plus one OpenHands installation.
- Roles, procedures and permissions are reviewable, versioned text with Pull Request history.
- Model choice is per profile; Claude Code is used only where it adds value.
- CI remains meaningful when the AI platform is offline.

**Negative**

- OpenHands runtime configuration is manual and can drift from this specification; the specification
  cannot enforce itself. Mitigation: setup checklist in [docs/openhands-integration.md](../openhands-integration.md)
  and periodic human review.
- Many role boundaries are *soft* (instruction-based). Mitigation: hard controls in GitHub (branch
  protection, CODEOWNERS, no agent approvals) and OpenHands (secret and MCP scoping per profile),
  listed in [config/permissions.yaml](../../config/permissions.yaml).
- A single GitHub identity for agents (initially) cannot distinguish roles at the token level.
- ACP integration is evolving; feature parity (for example Skill visibility inside Claude Code
  sessions) depends on the installed versions.
- Full end-to-end automation is deferred; humans start agent conversations in the first phase.

**Follow-up actions**

- Configure the OpenHands Agent Profiles, MCP servers and secrets per the integration documents.
- Configure GitHub labels, branch protection and CODEOWNERS per [docs/github-integration.md](../github-integration.md).
- Run the manual workflow on real work items before automating (phase plan in [docs/automation.md](../automation.md)).

## Security considerations

- Secrets live only in OpenHands secrets, GitHub Actions secrets or another secret manager —
  never in Git ([SECURITY.md](../../SECURITY.md)).
- Agents operate inside OpenHands sandboxes and never against production systems.
- Agents cannot merge: branch protection requires a human code owner's approval; agents never
  submit approving reviews; auto-merge is disabled for agent Pull Requests.
- Agent Profiles receive only the secrets and MCP servers their role needs (secret scope
  "Selected", MCP references).
- External content (web pages, third-party Issues) is treated as data, not instructions, to reduce
  prompt-injection risk.
- Claude Code credentials (subscription login or API key) are runtime secrets; their persistence
  location must be protected like any credential (see [docs/acp-integration.md](../acp-integration.md)).

## Operational considerations

- Components to operate: one OpenHands installation (with its agent server and sandboxes) and the
  Claude Code ACP adapter it launches. GitHub and GitHub Actions are managed services.
- Upgrades: OpenHands and the ACP adapter must be upgraded deliberately; ACP and Skill behaviour
  must be re-verified after each upgrade.
- Cost: LLM usage per profile; Claude Code usage for three roles. Cost is observed through the
  providers' consoles until a requirement justifies a gateway.
- Failure mode: if OpenHands is down, work stops but no state is lost — everything is in GitHub,
  and CI continues to validate human changes.
