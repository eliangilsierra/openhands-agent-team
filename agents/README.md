# Agents

This directory defines the role of every agent in the AI engineering team. Each file is the
behavioural specification for one **OpenHands Agent Profile**.

All agents inherit the global contract in [AGENTS.md](../AGENTS.md). A role file adds what is
specific to that role and never relaxes the global contract.

## The team

| Agent | File | Backend | Skills | Label |
| --- | --- | --- | --- | --- |
| Product Manager | [product-manager.md](product-manager.md) | Subagent | product-management | `agent:product` |
| Researcher | [researcher.md](researcher.md) | Subagent | research | `agent:research` |
| Architect | [architect.md](architect.md) | Subagent | architecture, research | `agent:architect` |
| Planner | [planner.md](planner.md) | Subagent | planning, stack-routing | `agent:planner` |
| Developer (generalist and ten stack specialists) | [developer.md](developer.md) | Subagents | development, testing, `stack-*` | `agent:developer` |
| QA Engineer | [qa-engineer.md](qa-engineer.md) | Subagent | testing | `agent:qa` |
| Code Reviewer | [code-reviewer.md](code-reviewer.md) | Subagent | code-review | `agent:reviewer` |
| Security Reviewer | [security-reviewer.md](security-reviewer.md) | Subagent | security-review | `agent:security` |
| Orchestrator | [orchestrator.md](orchestrator.md) | Coordinator (main session) | orchestration, stack-routing | — |

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
| Delegation brief | Runtime settings (model, effort, turns, budget, level) and the brief the coordinator sends |

## How the roles run

All roles run in **one** OpenHands conversation with the ACP Agent Profile `team` (ADR-0002). The
Orchestrator is the main session (the coordinator); every other role is a Claude Code subagent
generated from [config/agents.yaml](../config/agents.yaml) into
[templates/runtime/claude/agents/](../templates/runtime/claude/agents/) and installed in
`~/.claude/agents/`. The coordinator delegates with the brief at the end of each role file; nobody
pastes prompts by hand. See [docs/subagents.md](../docs/subagents.md).

| Role | Model | Escalation | Level | Parallel |
| --- | --- | --- | --- | --- |
| Orchestrator | `sonnet` | — | R0 | 1 |
| Product Manager | `haiku` | sonnet | R2 | 1 |
| Researcher | `sonnet` | opus | R1 | 3 |
| Architect | `opus` | — | R3 | 1 |
| Planner | `sonnet` | opus | R2 | 1 |
| Developer (all specialists) | `sonnet` | opus | R4 | 3 |
| QA Engineer | `haiku` | sonnet | R1 | 2 |
| Code Reviewer | `sonnet` | opus | R1 | 2 |
| Security Reviewer | `sonnet` | opus | R1 | 2 |

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
