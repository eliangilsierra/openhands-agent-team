---
name: technical-writing
description: Keep a project's README and docs/ current and professionally structured after each feature - Diátaxis (tutorials, how-to, reference, explanation), an arc42 architecture overview with C4 diagrams in Mermaid, consolidated UX specifications, indexes and a changelog - with templates, a style guide and a tested docs audit (structure, README sections, links, orphans, stale paths, Mermaid). Use as the technical-writer in the documentation stage; architects and developers read it for page structure.
---

# Technical Writing

## Purpose

Give every project documentation that a new developer, an operator and a reviewer can rely on: a README
that answers "what, how to start, how to use, how to work on it", and a `docs/` tree organised by the
reader's need. Documentation is code: it lives in the repository, changes through Pull Requests, and is
checked by a script.

## When to use

- State `documentation`: the coordinator delegates it when the last task Pull Request of a feature is
  merged into the integration branch. Skip it when the feature changed no user-visible behaviour,
  public interface, configuration, architecture or operation.
- When the person asks for a documentation baseline of an existing repository.
- Architects and developers read the structure and templates when they add per-feature documents.

## Inputs

- The feature Issue (requirements), its merged Pull Requests (`gh pr list --search "Closes #<task>"`
  per task, `gh pr diff`), the implementation plan, the architecture document and ADRs.
- UX specification comments on the feature Issue (`**UX specification** · UX Designer`).
- The repository: `README.md`, `docs/`, the stack profile (`detect_stack.py`) for commands and modules,
  configuration files (`.env.example`, settings), public interfaces (routes, OpenAPI, CLI, screens).
- This skill's templates ([templates/docs/](../../templates/docs/)) and script
  (`$HOME/.claude/skills/technical-writing/scripts/docs_audit.py`); structure and style rules:
  [references/structure-and-style.md](references/structure-and-style.md).

## Procedure

1. **Baseline.** On a branch `docs/<feature-issue>-<short-description>` from the integration branch
   (`branches.py`), run `docs_audit.py .` and keep its output: these are existing gaps; fix the ones the
   feature touches and list the rest as follow-ups.
2. **Collect what changed.** From the merged Pull Requests and the feature Issue, list what a reader now
   needs: new behaviour, commands, configuration and environment variables, endpoints or screens,
   architecture changes, operational steps, breaking changes.
3. **Place each item** in exactly one Diátaxis section (references file): getting started →
   `docs/tutorials/`; a task (configure, deploy, troubleshoot) → `docs/how-to/`; exact facts (API,
   configuration, commands, data model) → `docs/reference/`; concepts and rationale →
   `docs/explanation/`; system structure → `docs/architecture/overview.md` (arc42 + C4); UX
   specification → `docs/design/<feature>-<slug>.md`. Update existing pages before creating new ones.
4. **Write** with the templates in `templates/docs/` and the style guide: task-first headings, short
   sentences, imperative steps, one idea per paragraph, code blocks with the language, real commands
   from the stack profile, placeholders such as `<token>` for secrets.
5. **README.** Keep the sections: overview (under the title), Getting started, Usage, Development,
   Documentation, Licence; update badges, commands and links. The README stays short and points into
   `docs/`.
6. **Architecture overview.** Update the arc42 sections the feature affects and the C4 diagrams
   (context, container, component) in Mermaid; link every ADR and per-feature architecture document.
   Never change an ADR's decision text or another role's per-feature document; link them.
7. **Indexes and changelog.** Update `docs/README.md` and each section index; add a `CHANGELOG.md`
   entry (Keep a Changelog: Added, Changed, Fixed, Removed, Security) when the project keeps one.
8. **Audit.** Run `docs_audit.py .` again: zero errors; explain any remaining warning in the Pull
   Request. Run the project's Markdown lint when it has one.
9. **Pull Request.** Commit (`docs(<scope>): ...`), push, open a Pull Request into the integration
   branch with the template, `Closes` the feature's documentation Issue or `Refs #<feature>`, and the
   audit output as evidence. Label `agent:qa`; it goes through QA and reviews like any change.

## Rules

- Write only `README.md` files, `CHANGELOG.md` and `docs/**` (the hooks enforce it); never code, tests,
  workflows or an ADR's decision text.
- Every statement is checked against the code, configuration or merged Pull Requests; no invented
  behaviour, endpoints, numbers or roadmaps. Unknowns become questions in the Pull Request.
- One page, one purpose: never mix tutorial, how-to, reference and explanation in one page.
- Prefer updating and linking over duplicating; one fact lives in one place.
- No secrets, real personal data, internal host names or screenshots with private data.
- Diagrams are Mermaid in Markdown (C4 for architecture), not binary images, unless the project already
  uses another source format.
- English on GitHub and in the documentation unless the project's documentation is in another language.

## Required outputs

- One `docs/` Pull Request per feature with the README and `docs/` updates, the audit output and a list
  of follow-up gaps.

## Quality checklist

- [ ] `docs_audit.py` reports zero errors; warnings are explained.
- [ ] The README has all required sections and current commands.
- [ ] Every new page is linked from its section index and `docs/README.md`.
- [ ] Each page has one Diátaxis purpose; architecture follows arc42 with C4 diagrams.
- [ ] Every fact was verified against code, configuration or merged Pull Requests.
- [ ] UX specifications of the feature are consolidated in `docs/design/`.
- [ ] No secrets or personal data; placeholders for credentials.

## Failure conditions

- Behaviour in the code contradicts the requirements or the architecture → do not document either
  version; comment the contradiction on the feature Issue and add `needs-human`.
- The repository has no `docs/` structure → create it from the kit's skeleton in the same Pull Request.
- A required fact cannot be verified in the sandbox (for example production configuration) → write the
  page with an explicit "to be confirmed" question in the Pull Request, not a guess.

## Examples

**How-to guide skeleton:**

```markdown
# Rotate the payment provider API key

Use this guide when the key expires or may have leaked.

## Before you start
- Access to the secret store; the new key from the provider dashboard.

## Steps
1. Store the new key as `PAYMENTS_API_KEY` in the secret store.
2. Restart the service: `kubectl rollout restart deploy/payments`.
3. Verify: `curl -fsS https://<host>/health/payments` returns `ok`.

## If something goes wrong
- `401` from the provider: the key was not reloaded; repeat step 2.
```

**Audit evidence in the Pull Request:**

```text
python docs_audit.py .  ->  docs_audit: 0 errors, 1 warnings
[WARNING] orphans docs/explanation/caching.md: not linked from any other page  (linked in this PR's follow-up)
```
