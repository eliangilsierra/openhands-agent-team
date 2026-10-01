---
name: testing
description: Define and execute a test strategy (unit, integration, E2E, regression, static analysis, lint, build, security checks) for a change or bug, and report every check as PASS, FAIL, BLOCKED or NOT APPLICABLE with reproducible evidence. Use when validating a Pull Request, reproducing a bug, or writing tests during development.
---

# Testing

## Purpose

Establish, with evidence anyone can reproduce, whether a change does what its acceptance
criteria say and whether it breaks anything that worked before.

## When to use

- A Pull Request is labelled `agent:qa` (QA Engineer: plan and execute validation).
- A bug Issue is labelled `agent:qa` (QA Engineer: reproduce).
- A Developer writes tests and runs validation before opening a Pull Request.

## Inputs

- Acceptance criteria and testing requirements from the task Issue and its parent feature.
- The Pull Request diff and description (including the Developer's validation evidence).
- The project's test, lint, analysis and build commands (CI workflows, README, CONTRIBUTING).
- CI check results on the Pull Request.

## Procedure

1. **Collect expectations.** List every `AC` (and `T-AC`) for the change. Read the diff to find
   affected areas that the criteria do not mention (callers, shared utilities, migrations).
2. **Plan.** Fill the plan part of [templates/test-plan.md](../../templates/test-plan.md): one row per
   check, with ID, level, what is verified, and how. Cover:

   | Level | What it covers | When required |
   | --- | --- | --- |
   | Unit | Single function/class behaviour, boundaries, error branches | Every behaviour change |
   | Integration | Interaction with real database, filesystem, HTTP layer, queues | Changes crossing a component or persistence boundary |
   | E2E | User-visible flow through the running application | User-facing flows, when an E2E suite or a runnable app exists |
   | Regression | Previously working behaviour in affected areas; the bug's reproduction | Every bug fix; every change to shared code |
   | Static analysis / type check | Type errors, dead code, unsafe patterns | When the project configures it |
   | Lint | Project style and correctness rules | Always, when configured |
   | Build | The deliverable builds/packages | Always, when the project has a build |
   | Security checks | Dependency audit, secret scan, SAST configured in the project | When dependencies, inputs or auth change, or when configured in CI |

   For each `AC` add: the main case, at least one negative case and the relevant boundaries.
3. **Prepare.** Check out the PR branch in the sandbox, install dependencies with the lockfile,
   start required local services (never shared or production ones).
4. **Execute.** Run every check. Record the exact command, the relevant output (trimmed, never
   paraphrased into something it did not say), and the result. For manual/E2E checks record the
   steps, input data, expected and observed result; capture screenshots or response bodies when
   useful.
5. **Classify** each check:

   | Result | Meaning | Evidence required |
   | --- | --- | --- |
   | `PASS` | Executed; observed matches expected | Command or steps + observed result |
   | `FAIL` | Executed; observed differs from expected | Reproduction steps, input, expected vs observed, output/log excerpt, commit SHA, environment |
   | `BLOCKED` | Could not be executed | Exact cause (error message), what was tried, what would unblock it |
   | `NOT APPLICABLE` | Check does not apply to this change | One-line justification |

6. **Verdict.** Compute the overall QA verdict:
   - `FAIL` if any check is `FAIL`;
   - else `BLOCKED` if any required check is `BLOCKED`;
   - else `PASS` if every acceptance criterion has at least one `PASS`.
7. **Report and hand off.** Post the report on the Pull Request. `PASS` → label `agent:reviewer`.
   `FAIL` → label `agent:developer`. `BLOCKED` → add `blocked` (and `needs-human` if a human must act),
   keep `agent:qa`.

**Bug reproduction variant:** the single check is "the reported behaviour reproduces". Follow the
reporter's steps on the version they used and on current `main`. Report `PASS` when the reported
behaviour is reproduced (with minimal reproduction steps), `FAIL` when it is not reproduced (with
everything that was tried), or `BLOCKED` when the environment cannot be recreated. Hand off
reproduced bugs to `agent:planner`; non-reproduced bugs go back to the reporter with
`needs-human`.

## Rules

- A result is only `PASS` if the check was **executed** in this session. Reading code is not testing.
- Every `FAIL` must be reproducible by someone else from the report alone.
- Never change production code while validating. Test authoring by QA requires explicit assignment
  and is committed separately.
- Never delete, skip or loosen a test to obtain a result.
- Run tests against local or ephemeral environments only.
- Flaky tests: run up to 3 times, report each result, label the check `FAIL` if it fails at least
  once without an external cause, and mention the flakiness explicitly.
- Do not report the Developer's numbers as your own; re-run them.
- Keep test data synthetic. Never use real personal data or production credentials.

## Required outputs

- Test plan and QA report following [templates/test-plan.md](../../templates/test-plan.md) on the Pull
  Request (or bug Issue).
- Updated labels according to the verdict.

## Quality checklist

- [ ] Every acceptance criterion has at least one executed check.
- [ ] Negative and boundary cases are included where they exist.
- [ ] Build, lint and existing test suites have results.
- [ ] Each result is one of `PASS`, `FAIL`, `BLOCKED`, `NOT APPLICABLE`.
- [ ] Every `FAIL` has reproduction steps, expected vs observed and evidence.
- [ ] Every `BLOCKED` names the cause and the unblocking action.
- [ ] Every `NOT APPLICABLE` has a justification.
- [ ] Verdict follows the rule in step 6.
- [ ] Commands and environment (OS, runtime versions, commit SHA) are recorded.

## Failure conditions

- The project has no runnable test setup and the change is not trivially verifiable → verdict
  `BLOCKED`, propose a task to add tests, `needs-human`.
- Required services or credentials are unavailable → `BLOCKED` with the exact error.
- Acceptance criteria are untestable as written → `agent:planner` with a proposed rewording.
- A check reveals a security problem → include it, mention `agent:security`, `needs-human` if it
  already affects `main`.

## Examples

**QA report (excerpt):**

```markdown
**QA report** · QA Engineer · state: qa
PR #145 at 9f3c2e1 · Node 20.17 · Ubuntu 24.04 sandbox
Verdict: FAIL (6 PASS, 1 FAIL, 0 BLOCKED, 1 NOT APPLICABLE)

| ID | Check | Level | Result | Evidence |
| --- | --- | --- | --- | --- |
| QA-1 | AC-1 6th attempt rejected after 5 failures | Integration | PASS | `npm run test:int -- login` → 12 passed |
| QA-2 | AC-2 counter resets on success | Integration | FAIL | see below |
| QA-3 | Lint | Lint | PASS | `npm run lint` → 0 problems |
| QA-4 | E2E login page | E2E | NOT APPLICABLE | Change is API-only; UI unchanged |

### QA-2 FAIL
Steps: create user; 4 failed logins; 1 successful login; 1 failed login; 1 login with correct password.
Expected: last login succeeds (counter reset to 0 then 1).
Observed: HTTP 429 "Too many attempts". `failed_attempts` = 5 in the database after the sequence.
Evidence: `scripts/qa/repro-qa2.http` output attached below; `AuthService.ts:57` resets
`last_failed_at` but not `failed_attempts`.
```
