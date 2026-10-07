# Skills

A **Skill** is reusable, operational knowledge: the procedure, rules, outputs and quality bar for
one kind of work. Agent Profiles define *who* does the work; Skills define *how* it is done. An
agent that loads a Skill must be able to execute the process consistently without further
instructions.

## Catalogue

| Skill | Purpose | Loaded by | Template(s) |
| --- | --- | --- | --- |
| [product-management](product-management/SKILL.md) | Idea → testable requirements → feature Issue | Product Manager | [requirements.md](../templates/requirements.md) |
| [research](research/SKILL.md) | Question → classified, sourced evidence → recommendation | Researcher, Architect | [research.md](../templates/research.md) |
| [architecture](architecture/SKILL.md) | Requirements → simplest sufficient design + ADRs | Architect | [architecture.md](../templates/architecture.md), [adr.md](../templates/adr.md) |
| [planning](planning/SKILL.md) | Requirements + design → small, ordered task Issues | Planner | [implementation-plan.md](../templates/implementation-plan.md) |
| [development](development/SKILL.md) | Task Issue → branch → tested Pull Request, with helper scripts | Developer and every specialist | [pull_request_template.md](../.github/pull_request_template.md) |
| [stack-routing](stack-routing/SKILL.md) | Repository → stack profile; task → Developer specialist | Planner, Orchestrator | — |
| [testing](testing/SKILL.md) | Test strategy and PASS/FAIL/BLOCKED/NOT APPLICABLE reporting | QA Engineer, Developer | [test-plan.md](../templates/test-plan.md) |
| [code-review](code-review/SKILL.md) | Twelve-dimension semantic PR review | Code Reviewer | [code-review.md](../templates/code-review.md) |
| [security-review](security-review/SKILL.md) | Attack-surface-driven security review | Security Reviewer | [security-review.md](../templates/security-review.md) |
| [orchestration](orchestration/SKILL.md) | Route work, keep GitHub state consistent, escalate | Orchestrator | formats inside the Skill |

### Stack skills

Preloaded by the Developer stack specialists ([config/specialists.yaml](../config/specialists.yaml));
QA and reviewers load them for the stacks a Pull Request touches. Each has deep material in
`references/`, read only when needed.

| Skill | Stack | Preloaded by |
| --- | --- | --- |
| [stack-typescript](stack-typescript/SKILL.md) | TypeScript, JavaScript, Node.js | developer-typescript, developer-react, developer-angular, developer-vue |
| [stack-react](stack-react/SKILL.md) | React, React Native | developer-react, developer-nextjs |
| [stack-nextjs](stack-nextjs/SKILL.md) | Next.js | developer-nextjs |
| [stack-angular](stack-angular/SKILL.md) | Angular | developer-angular |
| [stack-vue](stack-vue/SKILL.md) | Vue, Nuxt | developer-vue |
| [stack-java-spring](stack-java-spring/SKILL.md) | Java, Spring Boot | developer-java-spring |
| [stack-kotlin-android](stack-kotlin-android/SKILL.md) | Kotlin, Android, Ktor | developer-kotlin-android |
| [stack-python](stack-python/SKILL.md) | Python | developer-python |
| [stack-go](stack-go/SKILL.md) | Go | developer-go |
| [stack-dotnet](stack-dotnet/SKILL.md) | C#, .NET | developer-dotnet |

### Scripts and references

A Skill directory may contain `scripts/` (Python 3.10+, standard library only, unit-tested in
`tests/`) and `references/` (Markdown read on demand), following the Agent Skills
progressive-disclosure layout: the frontmatter is always visible, the body loads with the Skill, and
these files load only when a step needs them. Scripts run from the installed skill directory, for
example `python "$HOME/.claude/skills/development/scripts/run_checks.py"`.

The canonical mapping is [config/skills.yaml](../config/skills.yaml). The `orchestration` Skill is
an addition to the eight Skills of the initial specification: the Orchestrator needs an
operational procedure just like every other role.

## Format

Each Skill is a directory containing one `SKILL.md`:

```markdown
---
name: <directory-name>
description: <what the skill does and when to use it, one paragraph>
---

# Skill Name

## Purpose
## When to use
## Inputs
## Procedure
## Rules
## Required outputs
## Quality checklist
## Failure conditions
## Examples
```

The YAML frontmatter (`name`, `description`) follows the portable Agent Skills format that
OpenHands documents for `.agents/skills/<name>/SKILL.md`: `name` must equal the directory name and
use lowercase letters, digits and hyphens. The same format is understood by Claude Code skills.
This keeps the Skills installable in both execution backends without conversion. Optional
OpenHands activation fields (`triggers`, `paths`) are intentionally not used: Skills are loaded by
role through the subagent definitions (`skills:` in templates/runtime/claude/agents/), not by keyword.

## How agents consume Skills

See [docs/agent-lifecycle.md](../docs/agent-lifecycle.md#3-consuming-skills) and
[docs/openhands-integration.md](../docs/openhands-integration.md#4-installing-skills). In short:

1. The Skills are installed where the runtime discovers them: as an OpenHands plugin (the repository
   root contains [plugin.json](../plugin.json)), in a user, project or organisation skills directory,
   or in the Claude Code skills directory for ACP profiles.
2. Each subagent definition preloads the Skills of its role (`skills:`); the coordinator loads `orchestration`.
3. If a Skill is not visible in the session (a known limitation for some ACP versions), the agent
   reads `SKILL.md` directly from this repository before starting.

## Writing a good Skill

- Procedures are numbered and executable; each step produces something checkable.
- Rules are prohibitions and invariants, not advice.
- The quality checklist is binary (each item is clearly true or false).
- Failure conditions say what to do, not only when to stop.
- Examples are realistic and consistent with the rest of the repository (labels, severities,
  states, IDs).
- Vocabulary comes from [config/workflow.yaml](../config/workflow.yaml).

To add or change a Skill, follow [CONTRIBUTING.md](../CONTRIBUTING.md#adding-a-skill).
