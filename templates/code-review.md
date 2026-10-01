**Code review** · Code Reviewer · state: code-review

# Code review: PR #<n> — <title>

<!--
Owner: Code Reviewer · Skill: skills/code-review/SKILL.md
Persist as: the body of a Pull Request review (event REQUEST_CHANGES or COMMENT, never APPROVE).
Line-specific findings are also posted as review comments on the exact lines.
Severity: BLOCKER, HIGH, MEDIUM, LOW, NIT. Outcome: CHANGES REQUESTED, NO BLOCKING FINDINGS, BLOCKED.
-->

## Outcome

**<CHANGES REQUESTED | NO BLOCKING FINDINGS | BLOCKED>** — <n> BLOCKER · <n> HIGH · <n> MEDIUM · <n> LOW · <n> NIT

| Field | Value |
| --- | --- |
| Pull Request | #<n> at commit `<sha>` |
| Task / requirements | #<task> · #<feature> |
| Design references | <architecture doc, ADR-NNNN> or "None" |
| QA report | <link> (verdict PASS) |
| Review cycle | <1 / 2 / 3> of 3 |

`NO BLOCKING FINDINGS` is not merge approval. A human code owner approves and merges.

## Scope

- **Reviewed:** <files / areas>
- **Not reviewed and why:** <generated files, lockfiles, vendored code> or "None"

## Dimension summary

| # | Dimension | Result |
| --- | --- | --- |
| 1 | Requirements | <OK / finding IDs / note> |
| 2 | Correctness | |
| 3 | Architecture | |
| 4 | Security | |
| 5 | Error handling | |
| 6 | Data integrity | |
| 7 | Performance | |
| 8 | Maintainability | |
| 9 | Tests | |
| 10 | Observability | |
| 11 | Documentation | |
| 12 | Regression risk | |

## Findings

### CR-1

- **Severity:** <BLOCKER | HIGH | MEDIUM | LOW | NIT>
- **Location:** `<path/to/file.ext:line>`
- **Problem:** <what is wrong>
- **Evidence:** <code path, failing input, test output, violated AC/ADR>
- **Impact:** <consequence if merged as is>
- **Recommendation:** <concrete change>

## Previous findings (re-review only)

| Finding | Severity | Status | Note |
| --- | --- | --- | --- |
| CR-<n> | <severity> | fixed in `<sha>` / not fixed / disputed | <note> |

## Follow-up suggestions

- <MEDIUM/LOW items deferred to a linked follow-up Issue, or "None">

## Hand-off

- NO BLOCKING FINDINGS → `agent:security`
- CHANGES REQUESTED → `agent:developer`
- BLOCKED → `<role>` with reason
