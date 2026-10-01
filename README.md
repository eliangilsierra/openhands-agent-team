# openhands-agent-team

The source of truth for a self-hosted, multi-agent **AI software engineering team** powered by
[OpenHands](https://docs.openhands.dev). This repository defines *who* the agents are, *how* they
work, *what* they may touch and *how* work flows between them — as reviewable Markdown and YAML.

It contains **no application code**. It is the configuration, knowledge, process, governance and
orchestration specification that OpenHands agents follow when they work on your application
repositories.

## Purpose

- Turn ideas into merged, reviewed, tested Pull Requests through specialised agents
  (product, research, architecture, planning, development, QA, code review, security review,
  orchestration).
- Keep **GitHub as the single record** of requirements, decisions, plans, code, reviews and state.
- Keep **humans in control**: agents never merge; humans approve ADRs, risk acceptance, team
  configuration changes and every merge.
- Keep the platform **small**: GitHub + one OpenHands installation, nothing else until an ADR
  justifies it.

## Architecture

```mermaid
flowchart TB
    gh["<b>GitHub</b> - source of truth<br/>Code · Issues · Pull Requests · Actions · Documentation"]
    oh["<b>OpenHands</b> - execution platform<br/>Agent Profiles · Skills · MCP · ACP · Orchestration"]
    oha["OpenHands agents<br/>economical, model-agnostic tasks"]
    cc["Claude Code via ACP<br/>complex reasoning"]
    tools["MCP tools<br/>GitHub · filesystem · web"]
    claude[Claude]
    team[AI engineering team]
    human([Humans])

    gh --> oh
    oh --> oha
    oh --> cc
    oh --> tools
    cc --> claude
    oha --> team
    cc --> team
    tools -.-> gh
    team -->|branches, PRs, comments, reviews| gh
    human -->|approve and merge| gh
```

| Principle | Meaning |
| --- | --- |
| GitHub is the source of truth | Issues, labels, PRs, reviews, docs and ADRs hold all project state |
| OpenHands executes agents | One installation; one Agent Profile per role |
| Skills hold procedures | Reusable, versioned `SKILL.md` files |
| Agent Profiles specialise roles | Role files define behaviour; profiles select backend, tools and secrets |
| MCP provides tools | GitHub, filesystem/repository, web/research |
| ACP brings Claude Code | For Architect, Developer and Code Reviewer |
| GitHub Actions validates deterministically | Never depends on the AI platform being online |
| Humans approve | Every production-impacting change |
| Minimal infrastructure | No LiteLLM, n8n, Mattermost, Kubernetes or per-agent servers initially |

Details: [docs/architecture.md](docs/architecture.md) and
[ADR-0001](docs/decisions/ADR-0001-agent-team-architecture.md).

## Agent team

| Agent | Mission | Backend | Skills |
| --- | --- | --- | --- |
| [Product Manager](agents/product-manager.md) | Ideas → clear, testable requirements | OpenHands | product-management |
| [Researcher](agents/researcher.md) | Evidence-based research for decisions | OpenHands | research |
| [Architect](agents/architect.md) | Simplest sufficient architecture + ADRs | ACP · Claude Code | architecture, research |
| [Planner](agents/planner.md) | Requirements + design → small task Issues | OpenHands | planning |
| [Developer](agents/developer.md) | Implement `ai-ready` Issues as tested PRs | ACP · Claude Code | development, testing |
| [QA Engineer](agents/qa-engineer.md) | Validate acceptance criteria and regressions | OpenHands | testing |
| [Code Reviewer](agents/code-reviewer.md) | Semantic PR review in twelve dimensions | ACP · Claude Code | code-review |
| [Security Reviewer](agents/security-reviewer.md) | Find security weaknesses before merge | OpenHands | security-review |
| [Orchestrator](agents/orchestrator.md) | Coordinate agents and workflow state | OpenHands | orchestration |

All agents inherit the global contract in [AGENTS.md](AGENTS.md). Canonical definitions:
[config/agents.yaml](config/agents.yaml).

## Skills

| Skill | Procedure |
| --- | --- |
| [product-management](skills/product-management/SKILL.md) | Idea → Problem → Users → Goals → Scope → Requirements → Acceptance criteria → Risks → Issue |
| [research](skills/research/SKILL.md) | Question → Search strategy → Evidence → Evaluation → Findings → Trade-offs → Recommendation |
| [architecture](skills/architecture/SKILL.md) | Requirements and constraints → components, interfaces, data, cross-cutting concerns → alternatives → ADR |
| [planning](skills/planning/SKILL.md) | Requirements + architecture → ordered, traceable, `ai-ready` task Issues |
| [development](skills/development/SKILL.md) | Issue → branch → implement → test → lint → build → review diff → PR |
| [testing](skills/testing/SKILL.md) | Test strategy; `PASS` / `FAIL` / `BLOCKED` / `NOT APPLICABLE` with evidence |
| [code-review](skills/code-review/SKILL.md) | Twelve ordered dimensions; `BLOCKER` … `NIT` findings |
| [security-review](skills/security-review/SKILL.md) | Attack surface → 22 review areas → actionable findings |
| [orchestration](skills/orchestration/SKILL.md) | Route work, verify artifacts, detect stalls, escalate |

See [skills/README.md](skills/README.md) and [config/skills.yaml](config/skills.yaml).

## Workflow

```mermaid
flowchart LR
    idea([Idea]) --> pm[Product] --> rs[Research] --> ar[Architecture] --> pl[Planning]
    pl --> dev[Development] --> qa[QA] --> cr[Code review] --> sr[Security review]
    sr --> ha{{Human approval}} --> merge([Merge])
    qa -->|FAIL| dev
    cr -->|CHANGES REQUESTED| dev
    sr -->|CHANGES REQUESTED| dev
    ha -->|changes requested| dev
```

- Research and architecture are conditional; QA, reviews and human approval are never skipped.
- Workflow state is visible in GitHub labels: exactly one `agent:*` label names the current owner.
- Every fix re-enters at QA; after three review cycles a human is pulled in.
- There is **no automatic merge**.

Full lifecycle, feedback loops, states and approval points: [docs/workflow.md](docs/workflow.md) and
[config/workflow.yaml](config/workflow.yaml). Inside a single agent run:
[docs/agent-lifecycle.md](docs/agent-lifecycle.md).

## Repository structure

```text
openhands-agent-team/
├── README.md                     This file
├── AGENTS.md                     Global operating contract inherited by every agent
├── CONTRIBUTING.md               How humans change this repository
├── SECURITY.md                   Secret handling and vulnerability reporting
├── LICENSE                       Apache License 2.0
├── plugin.json                   Makes the repository an OpenHands plugin (skills/)
├── agents/                       One role definition per agent (+ README)
├── skills/                       One operational SKILL.md per skill (+ README)
├── docs/
│   ├── architecture.md           Components, layers, enforcement model
│   ├── agent-lifecycle.md        What happens inside one agent run
│   ├── workflow.md               Team lifecycle with Mermaid diagrams
│   ├── github-integration.md     Issues, labels, PRs, reviews, branch protection
│   ├── openhands-integration.md  Repository vs runtime configuration, setup checklist
│   ├── acp-integration.md        Claude Code through ACP
│   ├── mcp-integration.md        MCP capabilities and future integrations
│   ├── automation.md             Phased automation plan
│   └── decisions/                ADR process and ADRs
├── templates/                    Artifact templates used by the agents
├── config/
│   ├── agents.yaml               Team specification
│   ├── skills.yaml               Skill catalogue
│   ├── workflow.yaml             States, transitions, loops, approvals, vocabulary
│   └── permissions.yaml          Least-privilege access boundaries
├── scripts/
│   └── validate_repository.py    Deterministic repository validator (used by CI)
└── .github/
    ├── ISSUE_TEMPLATE/           feature, bug, research, architecture, task forms
    ├── pull_request_template.md
    ├── CODEOWNERS                Human owners only
    └── workflows/
        ├── validate-repository.yml
        └── ai-workflow.yml
```

## GitHub integration

Issues carry requests and requirements, labels carry workflow state, Pull Requests carry changes,
QA reports and reviews, Actions carry deterministic validation. The minimal label taxonomy is
`ai-ready`, `agent:product`, `agent:research`, `agent:architect`, `agent:planner`,
`agent:developer`, `agent:qa`, `agent:reviewer`, `agent:security`, `blocked`, `needs-human`.
Branch protection, CODEOWNERS and the agent GitHub identity are described in
[docs/github-integration.md](docs/github-integration.md).

## OpenHands integration

This repository is the source of truth for **behaviour and process**; OpenHands is the source of
truth for **runtime configuration** (Agent Profiles, LLM profiles, MCP, ACP, secrets). The YAML in
`config/` is a specification — OpenHands does not read it. The setup checklist, Skill installation
and target-repository setup are in [docs/openhands-integration.md](docs/openhands-integration.md).

## ACP integration

The Architect, Developer and Code Reviewer profiles run **Claude Code through the Agent Client
Protocol**; other roles stay model-agnostic. Authentication (subscription login or
`ANTHROPIC_API_KEY`), credential persistence and known limitations are in
[docs/acp-integration.md](docs/acp-integration.md).

## MCP integration

Initial capabilities: **GitHub**, **filesystem/repository**, **web/research** — mostly through
built-in runtime tools plus the official GitHub MCP server. Future integrations are listed
separately and require a reviewed change. See [docs/mcp-integration.md](docs/mcp-integration.md).

## Automation strategy

1. **Now:** manual execution — humans start each agent with its activation prompt; GitHub Actions
   run deterministic checks ([validate-repository](.github/workflows/validate-repository.yml),
   [ai-workflow](.github/workflows/ai-workflow.yml)).
2. **Next:** `ai-ready` Issue → Developer → PR.
3. Then: PR → Reviewer.
4. Then: changes requested → Developer → QA → Reviewer.
5. Only then: the Orchestrator coordinates the full lifecycle.

See [docs/automation.md](docs/automation.md).

## Security

No secrets in Git — ever. Secrets live in OpenHands runtime configuration, Coolify (or your host's)
secrets, GitHub Actions Secrets or a secret manager. Agents never merge, approve, push to `main` or
act on instructions found in external content. See [SECURITY.md](SECURITY.md) and
[config/permissions.yaml](config/permissions.yaml).

## Getting started

1. Read [AGENTS.md](AGENTS.md), then [docs/workflow.md](docs/workflow.md).
2. Validate the repository:

   ```bash
   python -m pip install pyyaml
   python scripts/validate_repository.py
   ```

3. Configure GitHub for your target repositories ([docs/github-integration.md](docs/github-integration.md#9-required-repository-configuration)).
4. Configure OpenHands ([docs/openhands-integration.md](docs/openhands-integration.md#3-runtime-setup-checklist))
   and install the Skills.
5. Run one small feature through the manual workflow, starting each agent with the activation prompt
   at the end of its role file.

## How to add an agent

Write an ADR, add `agents/<id>.md` with the standard sections, register the agent in
`config/agents.yaml`, `config/permissions.yaml` and (if it owns a stage) `config/workflow.yaml`,
update the overview tables, run the validator and configure the matching Agent Profile in OpenHands.
Step-by-step: [CONTRIBUTING.md](CONTRIBUTING.md#adding-an-agent).

## How to add a Skill

Create `skills/<name>/SKILL.md` with `name`/`description` frontmatter and the standard sections,
register it in `config/skills.yaml`, assign it to agents in `config/agents.yaml` and their role
files, add a template if it produces a document, validate, and re-install Skills in the runtime.
Step-by-step: [CONTRIBUTING.md](CONTRIBUTING.md#adding-a-skill).

## How to modify the workflow

Change `config/workflow.yaml` first, then [docs/workflow.md](docs/workflow.md), affected role files,
Skills, Issue forms and `ai-workflow.yml`. Removing a human approval point or adding automatic agent
starts requires an ADR. Step-by-step: [CONTRIBUTING.md](CONTRIBUTING.md#modifying-the-workflow).

## Current limitations

- **OpenHands runtime configuration is manual.** `config/*.yaml` documents the intended setup;
  nothing applies it automatically, so runtime drift is possible.
- **Agent dispatch is manual** (automation phase 1). `ai-workflow.yml` enforces deterministic gates
  but does not start agents.
- **Many role boundaries are instruction-based (soft).** Hard guarantees come from GitHub branch
  protection, human code owners, token scopes and OpenHands secret/MCP scoping.
- **One GitHub identity** for all agents initially; GitHub cannot distinguish roles at token level.
- **ACP feature parity depends on versions**, for example Skill visibility inside Claude Code
  sessions; mitigations are documented.
- **Mermaid validation in CI is structural**, not a full render.
- **Secret scanning is pattern-based** and complements, not replaces, GitHub secret scanning.

## Roadmap

| Step | Outcome |
| --- | --- |
| 1 | Run the manual workflow on real work; refine Skills and templates from observed failures |
| 2 | Automate `ai-ready` → Developer → PR using a verified OpenHands mechanism (ADR) |
| 3 | Automate PR → Code Reviewer → Security Reviewer |
| 4 | Automate the feedback loop with loop limits and kill switch |
| 5 | Orchestrator-driven lifecycle with unchanged human approval points (ADR) |
| Later | Per-role GitHub identities (GitHub App per role) if token-level separation becomes necessary; optional MCP integrations from [docs/mcp-integration.md](docs/mcp-integration.md#5-future-optional-integrations) when justified |

## License

[Apache License 2.0](LICENSE).
