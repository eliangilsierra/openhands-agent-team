# Agents

This directory defines the role of every agent in the AI engineering team. Each file is the
behavioural specification for one **OpenHands Agent Profile**.

All agents inherit the global contract in [AGENTS.md](../AGENTS.md). A role file adds what is
specific to that role and never relaxes the global contract.

## The team

| Agent | File | Backend | Skills | Label |
| --- | --- | --- | --- | --- |
| Product Manager | [product-manager.md](product-manager.md) | OpenHands | product-management | `agent:product` |
| Researcher | [researcher.md](researcher.md) | OpenHands | research | `agent:research` |
| Architect | [architect.md](architect.md) | ACP · Claude Code | architecture, research | `agent:architect` |
| Planner | [planner.md](planner.md) | OpenHands | planning | `agent:planner` |
| Developer | [developer.md](developer.md) | ACP · Claude Code | development, testing | `agent:developer` |
| QA Engineer | [qa-engineer.md](qa-engineer.md) | OpenHands | testing | `agent:qa` |
| Code Reviewer | [code-reviewer.md](code-reviewer.md) | ACP · Claude Code | code-review | `agent:reviewer` |
| Security Reviewer | [security-reviewer.md](security-reviewer.md) | OpenHands | security-review | `agent:security` |
| Orchestrator | [orchestrator.md](orchestrator.md) | OpenHands | orchestration | — |

The machine-readable version of this table is [config/agents.yaml](../config/agents.yaml); access
boundaries are in [config/permissions.yaml](../config/permissions.yaml). The validation script
fails if these files disagree.

## Structure of a role file

Every role file contains these sections, in this order:

| Section | Content |
| --- | --- |
| Role | One-paragraph identity and position in the lifecycle |
| Mission | The single outcome the agent is accountable for |
| Responsibilities | What the agent does |
| Inputs | What it needs before starting, and where each input lives |
| Outputs | What it produces, with template and persistence location |
| Required skills | Skills the Agent Profile must load |
| Allowed tools | Tools and MCP capabilities the profile may use |
| Forbidden actions | Role-specific prohibitions on top of AGENTS.md |
| GitHub permissions | Read / modify / create / never-modify boundaries |
| Expected behavior | How the agent works and communicates |
| Definition of Done | When the agent's stage is complete |
| Escalation rules | When and how to stop and hand off |
| Activation prompt | The first message used to start a conversation with this profile |

## Activation prompts

OpenHands Agent Profiles select *which agent and configuration* runs a conversation; for Claude
Code (ACP) profiles there is no field to store role instructions, so the role behaviour is delivered
through context. Each role file therefore ends with an **activation prompt**: the first message a
human (or, later, an automation) sends when starting a conversation with that profile. The message
is written in Spanish for the people who send it; the files it points to are in English.

Rules of the standard message, identical for every role:

| Rule | Why |
| --- | --- |
| The first line is `Rol: <id>`, and the profile chosen in the chat launcher has the same name | The profile fixes the model and the secrets; the line fixes the role |
| The work item is named and the message says "SOLO este trabajo" | One stage and one work item per conversation (AGENTS.md section 16) |
| Work happens in the conversation's current directory; the team repository is read with `gh api` | The OpenHands interface shows that workspace |
| The agent stops after the "Siguiente paso" comment | A different conversation does each following stage |

Values in double braces are filled in at activation time:

| Variable | Meaning |
| --- | --- |
| `{{team_repo}}` | URL of this repository, for example `https://github.com/<owner>/openhands-agent-team` |
| `{{target_repo}}` | `owner/name` of the application repository being worked on |
| `{{work_item}}` | Issue or Pull Request number of the work item, for example `#12` |

## Ownership boundaries at a glance

| Agent | Writes code | Writes docs | Creates Issues | Opens PRs | Reviews PRs | Labels |
| --- | --- | --- | --- | --- | --- | --- |
| Product Manager | no | no | yes | no | no | handoff |
| Researcher | no | `docs/research/` | no | docs only | no | handoff |
| Architect | no | `docs/architecture/`, `docs/decisions/` | no | docs only | comment | handoff |
| Planner | no | no | yes | no | no | handoff, `ai-ready` |
| Developer | feature branches | with the change | no | yes | no | handoff |
| QA Engineer | no (tests only when assigned) | no | no | no | comment | handoff |
| Code Reviewer | no | no | no | no | comment / request changes | handoff |
| Security Reviewer | no | no | no | no | comment / request changes | handoff |
| Orchestrator | no | no | no | no | no | manage |

No agent merges, approves or writes to `main`.

## Adding or changing an agent

Follow [CONTRIBUTING.md](../CONTRIBUTING.md#adding-an-agent). A new agent requires a role file,
entries in all relevant `config/*.yaml` files, an ADR when it changes the team architecture, and
a matching Agent Profile in the OpenHands runtime.
