# ADR-0004: Target the repository's integration branch and start projects from a template

## Status

Proposed

| Field | Value |
| --- | --- |
| Date proposed | 2026-10-09 |
| Date decided | — |
| Decided by | Repository owner, by merging the Pull Request that introduces this ADR |
| Related Issue | #17 |
| Supersedes | None. Amends the "Pull Requests reach `main`" rules of AGENTS.md sections 5, 6 and 14 |
| Related ADRs | ADR-0002, ADR-0003 |

## Context

- Every project so far had one long-lived branch, `main`, and the team's rules, skills, hooks and
  checks hard-coded it as the target of task Pull Requests.
- The owner wants new projects to keep `main` for released code only and to integrate development in
  `develop`, both protected.
- GitHub closes an Issue from a `Closes #n` keyword only when the Pull Request merges into the
  repository's **default branch**; a project that integrates in `develop` must make `develop` its default.
- Squash-merging a release from `develop` into `main` would leave `main` with commits `develop` does
  not have, so every later release would show the whole history again; release merges must keep
  `develop` an ancestor of `main`.
- GitHub templates copy files only: settings, labels, rulesets, security features and extra branches
  must be applied after a repository is created.
- Existing single-branch repositories (for example `agent-sandbox`) must keep working unchanged.

## Decision

- **The integration branch is the repository's default branch**, read from the repository
  (`origin/HEAD`, `skills/development/scripts/branches.py`), never assumed. Agents branch from it and
  open task Pull Requests against it. In single-branch projects it is `main`; in projects created from
  the template it is `develop`.
- **Two-branch projects:** task Pull Requests are squash-merged into `develop` by a human. A release
  is a Pull Request from `develop` to `main` that only a human opens and merges, with a merge commit.
  Rulesets enforce the merge method per branch (`develop`: squash and linear history; `main`: merge
  commits), plus pull requests, required checks (`pr-conventions`, `ci`, `secret-scan`), no force
  pushes and no deletion on both.
- **`develop` is protected like `main`** in the hooks and git hooks: no direct push and no local merge.
- **`pr-conventions`** requires task Pull Requests to target the default branch and accepts the
  release Pull Request `develop` → `main` (Conventional Commits title only).
- **Project template:** the public repository `agent-team-project-template` is built from
  `templates/target-repo/` by `scripts/build_project_template.py`, with an MIT licence, and is never
  edited by hand. `scripts/bootstrap.sh`, run once by a human in each new project, applies what GitHub
  does not copy: personalised files, CI for the stack, `develop` as default branch, labels, merge
  settings, rulesets, secret scanning, push protection, Dependabot alerts and read-only Actions
  permissions.

## Alternatives

| Alternative | Why not chosen |
| --- | --- |
| Keep `main` as the only branch | Does not separate released code from integration, which the owner asked for |
| Hard-code `develop` everywhere | Breaks existing single-branch projects; the default branch already says which branch integrates |
| Keep `main` as default and target `develop` | `Closes #n` would not close Issues on merge into `develop`; every task would need manual closing |
| Squash releases into `main` | `main` and `develop` diverge, and every release Pull Request repeats the history |
| Copy the kit by hand into each project | Settings and protections are forgotten; files drift from the team's forms |
| A template edited directly on GitHub | Drifts from the team repository; this repository stays the single source |

## Consequences

**Positive**

- New projects start complete and protected with one script; released code is separate from
  integration.
- Existing projects need no change.
- The template cannot drift from the kit: it is generated from it.

**Negative**

- Releases are a human step (a Pull Request from `develop` to `main`), outside the agents' workflow.
- With one GitHub identity, rulesets require 0 approvals; requiring a human approval still needs a
  separate machine user for the agents (docs/github-integration.md, level 2).
- The template is synchronised by hand: rebuild it and open a Pull Request in the template repository
  when the kit changes.

## Security considerations

- Both long-lived branches are protected by rulesets without bypass actors and by the hooks.
- `bootstrap.sh` enables secret scanning and push protection (free on public repositories) and
  read-only Actions permissions; it needs an administrator and runs only when a human starts it.
- The template ships the secret-scan workflow, `.gitleaks.toml` and a `.gitignore` for secret files.

## Operational considerations

- Projects created from the template: run `bash scripts/bootstrap.sh --dry-run`, then without
  `--dry-run`, as described in the template's README.
- When `templates/target-repo/` changes: `python scripts/build_project_template.py --out <clone of the
  template repository> --owner <owner> --holder "<name>"`, then commit on a branch and open a Pull
  Request into the template repository's `develop`.
- Re-install the runtime hooks and git hooks after merge (`develop` protection).
