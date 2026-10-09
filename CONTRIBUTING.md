# Contributing

This repository is the canonical specification of the AI engineering team. Changes to it change
how every agent behaves, so they follow the same discipline as production code: an Issue, a
branch, a Pull Request, deterministic validation and human review.

## General process

1. **Open an Issue** describing the problem with the current specification (use the task or
   architecture form). Agents may propose changes; humans approve them.
2. **Create a branch** following [AGENTS.md](AGENTS.md#6-branching-rules), usually
   `docs/<issue-number>-<short-description>` or `chore/<issue-number>-<short-description>`.
3. **Make the change consistently** across every file that describes the same concept (see the
   checklists below). The configuration files in `config/` are canonical; documentation must agree
   with them.
4. **Validate locally:**

   ```bash
   python -m pip install pyyaml
   python scripts/generate_runtime.py --check
   python scripts/validate_repository.py
   python -m unittest discover -s tests
   node templates/runtime/claude/hooks/test-hooks.mjs
   npx --yes markdownlint-cli2@0.23.3 "**/*.md"
   ```

5. **Open a Pull Request** using the [template](.github/pull_request_template.md). In
   *Architecture impact*, list any OpenHands runtime change required to keep the runtime aligned
   with the specification.
6. **Human review.** A human code owner reviews and merges. Changes to protected paths
   (`AGENTS.md`, `SECURITY.md`, `config/permissions.yaml`, `config/workflow.yaml`, `.github/workflows/`,
   `.github/CODEOWNERS`) always require explicit human review.
7. **Apply runtime changes.** After merge, the human who merged performs (or tracks in an Issue) the
   OpenHands changes listed in the Pull Request, for example re-installing Skills.

## Adding an agent

1. Write an ADR (adding a role changes the team architecture) from [templates/adr.md](templates/adr.md).
2. Create `agents/<agent-id>.md` with all sections in [agents/README.md](agents/README.md#structure-of-a-role-file),
   including the delegation brief. Make it specific — do not copy another role's text.
3. Add the agent to [config/agents.yaml](config/agents.yaml): name, profile file, label,
   execution backend, mission, responsibilities, skills, MCP capabilities, outputs, hand-offs.
4. Add its access boundaries to [config/permissions.yaml](config/permissions.yaml) using the shared
   field vocabulary.
5. If it owns a stage: add the state, transitions, feedback loops and label to
   [config/workflow.yaml](config/workflow.yaml), and update [docs/workflow.md](docs/workflow.md).
6. Reference the agent's Skills in [config/skills.yaml](config/skills.yaml) (`agents` / `consumers`).
7. Update the tables in [README.md](README.md), [AGENTS.md](AGENTS.md#4-agent-responsibilities),
   [agents/README.md](agents/README.md) and [docs/architecture.md](docs/architecture.md).
8. If it needs a new label, add it to `config/workflow.yaml` and the label commands in
   [docs/github-integration.md](docs/github-integration.md#2-labels).
9. Add its `runtime` and `subagent` blocks in `config/agents.yaml`, run
   `python scripts/generate_runtime.py` to create its subagent file in
   `templates/runtime/claude/agents/<id>.md`, add it to `LEVELS` in
   `templates/runtime/claude/hooks/lib.mjs`, and update the catalogue in
   [docs/subagents.md](docs/subagents.md).
10. Run the validator and `node templates/runtime/claude/hooks/test-hooks.mjs`. In the PR, list the
    runtime files to reinstall in the `~/.claude` volume.

## Adding or changing a Developer specialist

Specialists are variants of the Developer role (ADR-0003), not new roles: no new label, state or
permission entry.

1. Add or change the entry in [config/specialists.yaml](config/specialists.yaml): id
   `developer-<kebab>`, title, expertise, the stack keys it owns and its skills. Add new stack keys to
   `routing.priority` in the right place (more specific frameworks first).
2. If the stack is new, teach `skills/stack-routing/scripts/detect_stack.py` to report its key, add a
   fixture repository under `tests/fixtures/` and a test in `tests/test_detect_stack.py`.
3. Create or update `skills/stack-<name>/SKILL.md` (all Skill sections, senior conventions,
   anti-patterns, testing, commands, review checklist) with deep material in `references/`, and
   register it in [config/skills.yaml](config/skills.yaml) with `agents: []` and `specialists`.
4. Run `python scripts/generate_runtime.py`: it writes the subagent file, `specialists.json` and the
   specialist block of `hooks/lib.mjs`. Never edit those by hand.
5. Document the specialist in the tables of [agents/developer.md](agents/developer.md),
   [docs/subagents.md](docs/subagents.md#3-developer-specialists) and [README.md](README.md); the
   validator checks the first two.
6. Run the validation below. In the PR, list the runtime files to reinstall.

## Changing the secret policy

1. Edit [config/secret-patterns.tsv](config/secret-patterns.tsv) only; keep to the regex subset its
   header describes, so `grep -E`, JavaScript and Python read it the same way.
2. Run `python scripts/generate_runtime.py` to refresh the copies in `hooks/`, `githooks/` and
   `skills/development/scripts/`.
3. Add cases to `tests/test_secret_scan.py` and `templates/runtime/claude/hooks/test-hooks.mjs`: one
   value the rule must catch and one legitimate value it must let through. Build fake secrets by
   concatenation so no scanner sees a literal.
4. Never add an allow rule to make a real finding pass: remove the value and rotate the credential.

## Updating the project template

The public template repository is generated from `templates/target-repo/` (ADR-0004). After a change
to the kit is merged:

```bash
gh repo clone <owner>/agent-team-project-template /path/to/template && cd /path/to/template
git switch -c chore/<issue-number>-sync-kit origin/develop
python <team-repo>/scripts/build_project_template.py --out . --owner <owner> --holder "<name>"
git add -A && git commit -m "chore: sync with the team kit" && git push -u origin HEAD
gh pr create --base develop --fill
```

## Adding a helper script

- Place it in `skills/<skill>/scripts/<name>.py`: Python 3.10+, standard library only, a docstring
  with usage, `main(argv)` returning an exit code, no network unless it is the script's purpose, and
  never print secret values.
- Add unit tests in `tests/` (fixtures under `tests/fixtures/`), and document the script in the
  Skill's procedure.

## Modifying an agent

- Keep the section structure. Change responsibilities, inputs, outputs or forbidden actions in the
  role file **and** in `config/agents.yaml` / `config/permissions.yaml` in the same PR.
- Changing an agent's execution backend (OpenHands ↔ ACP) requires an ADR.
- Widening permissions requires a justification in the PR and human approval; prefer adding a hard
  control (GitHub or OpenHands setting) over relying on instructions.

## Adding a Skill

1. Create `skills/<skill-name>/SKILL.md`. The directory name is lowercase kebab-case and equals the
   frontmatter `name`.
2. Use the structure in [skills/README.md](skills/README.md#format): frontmatter (`name`,
   `description`) and the sections Purpose, When to use, Inputs, Procedure, Rules, Required outputs,
   Quality checklist, Failure conditions, Examples.
3. Make it operational: numbered steps, binary checklist items, concrete failure actions and a
   realistic example using the shared vocabulary.
4. Register it in [config/skills.yaml](config/skills.yaml) and add it to the `skills` of the agents
   that load it in [config/agents.yaml](config/agents.yaml) and their role files' *Required skills*.
5. Add a template under `templates/` if the Skill produces a document, and reference it.
6. Update [skills/README.md](skills/README.md) and [README.md](README.md).
7. After merge, update the Skills in the runtime, through the installation route you use
   ([docs/openhands-integration.md](docs/openhands-integration.md#4-installing-skills)).

## Modifying a Skill

- Keep procedures backward compatible with in-flight work where possible; if an output format
  changes, update the template and every document that shows an example of it.
- Do not weaken a Rule or Quality checklist item without stating why in the PR.
- Re-install Skills in the runtime after merge.

## Modifying the workflow

1. Change [config/workflow.yaml](config/workflow.yaml) first (states, transitions, feedback loops,
   approval points, labels or vocabularies).
2. Update [docs/workflow.md](docs/workflow.md) diagrams and tables, the affected role files and
   Skills, the Issue forms and [.github/workflows/ai-workflow.yml](.github/workflows/ai-workflow.yml)
   if checked sections or labels change.
3. Removing a human approval point, or adding automatic transitions that start agents, requires an
   ADR. Automatic merging is out of scope for this repository.

## Creating ADRs

Follow [docs/decisions/README.md](docs/decisions/README.md): next free number,
`ADR-NNNN-kebab-case-title.md`, the seven required sections, status `Proposed` until a human
accepts it, and an index entry. Superseding never edits the old decision text; only its status line
changes.

## Changing permissions

1. Edit [config/permissions.yaml](config/permissions.yaml) using only the documented field values.
2. Keep role files' *GitHub permissions* tables consistent.
3. State in the PR which boundaries are **hard** (GitHub/OpenHands settings) and which are **soft**
   (instructions), and which runtime or GitHub settings must change.
4. Never grant merge, `main` write or `APPROVE` to any agent. The validator rejects
   `main_branch_write: true` and `merge: true`.

## Pull Request requirements

- Linked Issue with exactly one closing keyword; branch name per convention, with the same Issue
  number.
- Pull Request title and commits in Conventional Commits form (`docs: explain squash merging`,
  `feat(validator): check plugin.json`). The `ai-workflow` check verifies the title and the commits.
- All template sections completed.
- Terminology from `config/workflow.yaml` used exactly (states, labels, severities, QA results,
  review outcomes, research classifications).
- No application source code. Executable files are limited to `scripts/` (validator, generator,
  workflow tests), the runtime hooks, `skills/<name>/scripts/*.py` and `tests/`.
- No secrets ([SECURITY.md](SECURITY.md)).

## Validation requirements

The [validate-repository](.github/workflows/validate-repository.yml) workflow must pass. It runs:

| Check | Tool |
| --- | --- |
| Required files and directories, non-empty files | `scripts/validate_repository.py` |
| YAML and JSON syntax | `scripts/validate_repository.py` |
| Internal Markdown links and anchors | `scripts/validate_repository.py` |
| Mermaid block structure | `scripts/validate_repository.py` |
| Role file, Skill, ADR, Issue form and PR template structure | `scripts/validate_repository.py` |
| Consistency of `config/agents.yaml`, `skills.yaml`, `workflow.yaml`, `permissions.yaml` | `scripts/validate_repository.py` |
| Shared vocabulary | `scripts/validate_repository.py` |
| `plugin.json` schema, name and version | `scripts/validate_repository.py` |
| Secret patterns, secret-bearing files, placeholder markers, application source | `scripts/validate_repository.py` |
| Generated runtime files match `config/` | `scripts/generate_runtime.py --check` (also run by the validator) |
| Secrets in the whole history | gitleaks (pinned, checksum-verified) with [.gitleaks.toml](.gitleaks.toml) |
| Secret policy used everywhere, no duplicated pattern lists | `scripts/validate_repository.py` with [config/secret-patterns.tsv](config/secret-patterns.tsv) |
| Developer specialists agree with skills, hooks and docs | `scripts/validate_repository.py` |
| Unit tests of the skill scripts, generator and validator | `python -m unittest discover -s tests` |
| Markdown style | `markdownlint-cli2` with [.markdownlint-cli2.yaml](.markdownlint-cli2.yaml) |
| Workflow syntax | `actionlint` |

If you add a new kind of file or concept, extend the validator in the same Pull Request.
