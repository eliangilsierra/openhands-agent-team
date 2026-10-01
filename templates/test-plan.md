**QA report** · QA Engineer · state: qa

# Test plan and QA report: PR #<n> — <title>

<!--
Owner: QA Engineer (Developer uses the plan part for self-validation) · Skill: skills/testing/SKILL.md
Persist as: comment on the Pull Request (bug reproduction: comment on the bug Issue).
Results use exactly: PASS, FAIL, BLOCKED, NOT APPLICABLE.
Verdict rule: FAIL if any FAIL; else BLOCKED if any required check is BLOCKED;
else PASS if every acceptance criterion has at least one PASS.
-->

## Verdict

**<PASS | FAIL | BLOCKED>** — <n> PASS · <n> FAIL · <n> BLOCKED · <n> NOT APPLICABLE

| Field | Value |
| --- | --- |
| Pull Request | #<n> at commit `<sha>` |
| Task / requirements | #<task> · #<feature> (AC-…) |
| Environment | <OS, runtime versions, database version, browser> |
| Date | <YYYY-MM-DD> |
| QA cycle | <1 / 2 / 3> of 3 |

## Scope

- **Acceptance criteria under test:** <AC-1, AC-2, …>
- **Affected areas beyond the criteria:** <callers, shared modules, migrations>
- **Not tested and why:** <item — reason> or "None"

## Test plan and results

| ID | Check | Level | Covers | Result | Evidence |
| --- | --- | --- | --- | --- | --- |
| QA-1 | <AC-1 main case> | Integration | AC-1 | PASS | `<command>` → <observed> |
| QA-2 | <AC-1 boundary/negative case> | Unit | AC-1 | PASS | `<command>` → <observed> |
| QA-3 | Regression: <existing behaviour> | Regression | — | PASS | `<command>` → <observed> |
| QA-4 | Unit test suite | Unit | all | PASS | `<command>` → <n passed, 0 failed> |
| QA-5 | Lint | Lint | all | PASS | `<command>` → <0 problems> |
| QA-6 | Static analysis / type check | Static analysis | all | PASS | `<command>` → <result> |
| QA-7 | Build | Build | all | PASS | `<command>` → <result> |
| QA-8 | Security checks (dependency audit / secret scan) | Security | all | NOT APPLICABLE | <justification, e.g. no dependency changes and not configured in CI> |
| QA-9 | E2E: <flow> | E2E | AC-<n> | BLOCKED | <cause, unblock action> |

## Failures

### QA-<n> — FAIL

- **Steps to reproduce:**
  1. <step>
  2. <step>
- **Input data:** <synthetic data used>
- **Expected:** <behaviour from AC-n>
- **Observed:** <actual behaviour>
- **Evidence:**

  ```text
  <trimmed command output, log or response body>
  ```

- **Suspected location (optional):** `<path:line>`

## Blocked checks

| ID | Cause (exact error) | What was tried | What would unblock it | Who |
| --- | --- | --- | --- | --- |
| QA-<n> | <error> | <attempts> | <action> | <role or @human> |

## Flaky behaviour

<Check, number of runs, results per run — or "None observed">

## Hand-off

- PASS → `agent:reviewer`
- FAIL → `agent:developer`
- BLOCKED → keep `agent:qa`, add `blocked` (+ `needs-human` if a human must act)

## Bug reproduction (bug Issues only)

| Field | Value |
| --- | --- |
| Reported version / commit | <version> |
| Reproduced on reported version | yes / no |
| Reproduced on current `main` (`<sha>`) | yes / no |
| Result | PASS (reproduced) / FAIL (not reproduced) / BLOCKED |

Minimal reproduction steps:

1. <step>
