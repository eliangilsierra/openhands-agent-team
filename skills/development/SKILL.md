---
name: development
description: Implement one ai-ready GitHub task Issue end to end - understand requirements, inspect repository, architecture and ADRs, create a convention-named branch (never main), implement, write tests, run tests, lint and build, review the diff, commit, push and open a Pull Request; then address QA and review findings. Use for any code change to an application repository.
---

# Development

## Purpose

Deliver exactly what a task Issue asks for as a Pull Request that is correct, tested, consistent
with the architecture, free of secrets, and easy to review — without bypassing any control.

## When to use

- A task Issue is labelled `ai-ready` and `agent:developer`.
- A Pull Request you own receives a QA `FAIL` or `CHANGES REQUESTED` review.

Do not use this Skill for tasks that are not `ai-ready`; ask the Planner instead.

One conversation implements **one** task Issue. Do not continue with another task, with QA or with
review in the same conversation, even when the remaining tasks look small (AGENTS.md section 16).

## Inputs

- Task Issue (all nine sections) and its parent feature Issue.
- Architecture document and Accepted ADRs referenced by the task.
- Target repository conventions: `AGENTS.md`, `CONTRIBUTING.md`, README, existing code and tests,
  CI workflows (they define the commands that must pass).
- Feedback: QA report and review findings on your Pull Request.

## Procedure

```text
Issue → Understand requirements → Inspect repository → Inspect architecture → Inspect ADRs
→ Create branch → Implement → Write/update tests → Run tests → Run lint → Run build
→ Review diff → Commit → Push → Open PR
```

1. **Issue.** Read the task Issue completely, including comments. Confirm it carries `ai-ready`.
2. **Understand requirements.** Read the parent feature Issue's referenced `FR`/`AC`. Restate the
   objective and acceptance criteria to yourself; list the cases you will test. If something is
   genuinely ambiguous *and* blocks a correct implementation, comment a precise question, add
   `blocked`, and stop. If it is a minor interpretation, proceed and document it in the PR.
3. **Inspect repository.** Find the code paths involved, their callers and tests. Identify the
   project's commands for test, lint, type check and build (from CI workflows, `package.json`,
   `Makefile`, `pyproject.toml`, etc.). Run the test suite once *before* changing anything to know
   the baseline.
4. **Inspect architecture.** Read the architecture document sections relevant to the task.
5. **Inspect ADRs.** Read every ADR referenced by the task and any ADR covering the components you
   touch. Your change must comply; if it cannot, stop and escalate to `agent:architect`.
6. **Create branch.** From an up-to-date `main`:

   ```bash
   git fetch origin
   git switch -c feature/<issue-number>-<short-description> origin/main
   ```

   | Prefix | Use |
   | --- | --- |
   | `feature/<issue-number>-<short-description>` | New functionality |
   | `bugfix/<issue-number>-<short-description>` | Defect correction |
   | `refactor/<issue-number>-<short-description>` | Behaviour-preserving restructuring |
   | `chore/<issue-number>-<short-description>` | Tooling, dependencies, build, CI |

   The branch number is the number of the task Issue you are implementing, not a counter and not a
   range (`feature/42-login-rate-limit`, never `task/5-11-ui`). Work in the conversation's current
   working directory: clone the repository there.

   Never work on `main`. If you find yourself on `main`, stop and switch before any edit.
   Remove the `ai-ready` label from the task Issue (keep `agent:developer`): the task is now
   `in-development`.
7. **Implement.** Make the smallest change that satisfies every acceptance criterion. Follow
   existing patterns for structure, naming, error handling, logging and configuration. Validate
   inputs at trust boundaries. Read configuration and secrets from the environment, never hard-code them.
8. **Write/update tests.** For each acceptance criterion add or update tests at the level named in
   the task's testing requirements. For a bug, write the failing regression test first, see it
   fail, then fix. Update tests whose expected behaviour legitimately changed and explain why.
9. **Run tests.** Run the full relevant suite, not only new tests. All must pass.
10. **Run lint.** Run the project's linters, formatters (in check mode) and type checkers.
11. **Run build.** Run the production build or package step if the project has one.
12. **Review diff.** Run `git diff origin/main...HEAD` and check: only task-scoped changes; no
    secrets, tokens, `.env`, credentials or personal data; no debug prints, commented-out code,
    stray files or large generated artefacts; error handling present; docs updated.
13. **Commit.** Small, coherent commits in Conventional Commits form
    (`<type>(<scope>): <description>`, imperative, under 73 characters), with the Issue reference in
    the Pull Request title or body: `feat(auth): reject login after 5 failed attempts`. Do not change
    the git identity and do not add `Co-Authored-By` trailers.
14. **Push.** `git push -u origin <branch>`.
15. **Open PR.** Open a **draft** Pull Request using `.github/pull_request_template.md`, titled in
    Conventional Commits form (`feat(auth): reject login after 5 failed attempts (#122)`), with
    exactly one `Closes #<issue>`, the exact validation commands and their results, and any
    interpretation you made. When CI is green (or failures are proven unrelated), mark it ready, add
    label `agent:qa`, post the "Next step" comment and **stop**. Do not merge.

**Handling feedback.** For each QA `FAIL` or review finding: reproduce it, fix it on the same
branch in a new commit, and reply in the thread with the commit SHA — or dispute it with
evidence. Re-run steps 9–12, then move the label back to `agent:qa` (the whole chain QA → Code
Review → Security Review runs again). Never resolve another agent's thread without replying.

## Rules

- Never commit to, push to or merge into `main`, on GitHub or with a local `git merge`. Never
  enable auto-merge. To resolve conflicts, update your own branch and push it.
- One task Issue per branch and per Pull Request. If the task is too large, stop and ask the
  Planner to split it; do not batch several tasks together.
- Never skip, delete, `xfail`/`skip`-mark or weaken a test, linter rule or CI check to get green.
- Never silently modify requirements or deviate from an Accepted ADR.
- Never commit secrets, credentials, `.env` files or real personal data; use the project's
  example-config convention for new settings.
- Never add a dependency the architecture or task did not foresee without stating why in the PR;
  check its licence, maintenance and known vulnerabilities first.
- Never modify `.github/workflows/` unless the task explicitly requires it.
- Keep the PR to one task. Note unrelated problems as follow-up suggestions in the PR description.
- Report validation results exactly as observed. If a command could not be run, say so.

## Required outputs

- A branch named by convention containing the implementation and tests.
- A Pull Request following [.github/pull_request_template.md](../../.github/pull_request_template.md)
  with `Closes #<issue>`, verification evidence and label `agent:qa`.
- Replies to every finding in later cycles.

## Quality checklist

- [ ] Branch name matches `<prefix>/<issue-number>-<short-description>` with the number of the one
      task Issue; not on `main`.
- [ ] Commit messages and the Pull Request title follow Conventional Commits.
- [ ] The Pull Request has exactly one `Closes #<issue>`.
- [ ] Every acceptance criterion is implemented and covered by a test.
- [ ] Baseline tests were run before the change; full suite passes after it.
- [ ] Lint, type checks and build pass.
- [ ] Diff contains only task-scoped changes; no secrets, debug code or stray files.
- [ ] Public behaviour changes are reflected in documentation.
- [ ] PR template is complete; validation commands and outputs are listed.
- [ ] Architecture and ADR compliance stated in the PR.

## Failure conditions

- Task is not `ai-ready`, or acceptance criteria are contradictory → stop, comment, `blocked`,
  hand back to `agent:planner` or `agent:product`.
- Implementation needs an undocumented design decision → `agent:architect`.
- Baseline tests fail before any change → report `BLOCKED` with output; do not "fix" unrelated tests
  inside the task without approval.
- The change cannot fit a reviewable PR → propose a split to `agent:planner`.
- A required credential or service is unavailable in the sandbox → `blocked` (+ `needs-human`).
- Third feedback cycle on the same PR → `blocked` + `needs-human`.

## Examples

**Pull Request title and commits:**

```text
feat(auth): reject login after 5 failed attempts (#122)
test(auth): cover throttle reset on successful login
```

**Pull Request description (excerpt):**

```markdown
## Summary
Reject login for an account after 5 consecutive failed attempts within 15 minutes.

## Related Issue
Closes #122 · Part of #120 · ADR-0007

## Tests
- `npm test` → 412 passed, 0 failed (baseline before change: 405 passed)
- `npm run lint` → 0 problems
- `npm run build` → success
- New: `auth/throttle.test.ts` (threshold, reset, window), `login.int.test.ts` (429 on 6th attempt)

## Interpretation
AC-1 does not specify the HTTP status; 429 was used, matching the existing rate-limit response in
`api/errors.ts:88`.
```
