**QA report** · QA Engineer · state: qa

# Test plan and QA report: PR #<n> — <title>

<!--
Owner: QA Engineer (Developer uses the plan part for self-validation) · Skill: skills/testing/SKILL.md
Persist as: comment on the Pull Request (bug reproduction: comment on the bug Issue).
Results use exactly: PASS, FAIL, BLOCKED, NOT APPLICABLE.
Verdict rule: FAIL if any FAIL; else BLOCKED if any required check is BLOCKED;
else PASS if every acceptance criterion has at least one PASS.
Write each fact once: short evidence for PASS rows, full detail only for FAIL and BLOCKED.
Omit an empty section; state it in the "Failures / Blocked / Flaky" line instead.
Cycle 2 and later: use the "Re-review (cycle ≥ 2)" format at the end instead of the full report.
-->

## Verdict

**<PASS | FAIL | BLOCKED>** — <n> PASS · <n> FAIL · <n> BLOCKED · <n> NOT APPLICABLE

PR #<n> at `<short sha>` · Task #<task> · Cycle <1 / 2 / 3> of 3 · <runtime versions, OS>

## Scope

- **Not tested and why:** <item — reason> or "None"
- **Affected areas beyond the criteria:** <callers, shared modules, migrations> or "None"

## Results

| ID | Check | Covers | Result | Evidence |
| --- | --- | --- | --- | --- |
| QA-1 | <AC-1 main case> | AC-1 | PASS | `<test file>: <test name>` |
| QA-2 | <AC-1 negative or boundary case> | AC-1 | PASS | `<test file>: <test name>` |
| QA-3 | Regression: <existing behaviour> | — | PASS | `<test file>: <test name>` |
| QA-4 | Validation: unit, lint, type check, build | all | PASS | `<install> && <lint> && <typecheck> && <test> && <build>` → all pass (<n> tests) |
| QA-5 | Security checks (dependency audit / secret scan) | all | NOT APPLICABLE | <one-line justification> |

Failures / Blocked / Flaky: none <!-- or the sections below, only those with content -->

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

<Check, number of runs, results per run>

## Hand-off

PASS → `agent:reviewer` + `agent:security` · FAIL → `agent:developer` · BLOCKED → keep `agent:qa`, add
`blocked` (+ `needs-human` if a human must act)

## Re-review (cycle ≥ 2)

```markdown
**QA report (cycle <n>)** · QA Engineer · state: qa

**<PASS | FAIL | BLOCKED>** at `<short sha>` · previous report: <link>

| ID | Result before → now | Evidence |
| --- | --- | --- |
| QA-<n> | FAIL → PASS | `<test file>: <test name>` |
| QA-<new> | new check: PASS | `<test file>: <test name>` |
| QA-4 | Validation re-run: PASS | `<commands>` → all pass (<n> tests) |

Unchanged checks: <IDs> PASS in the validation re-run (code they cover unchanged since `<previous sha>`).
Failures / Blocked / Flaky: none <!-- or full detail as in the cycle-1 format -->
```

## Bug reproduction (bug Issues only)

| Field | Value |
| --- | --- |
| Reported version / commit | <version> |
| Reproduced on reported version | yes / no |
| Reproduced on current `main` (`<sha>`) | yes / no |
| Result | PASS (reproduced) / FAIL (not reproduced) / BLOCKED |

Minimal reproduction steps:

1. <step>
