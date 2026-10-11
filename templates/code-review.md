**Code review** · Code Reviewer · state: code-review

# Code review: PR #<n> — <title>

<!--
Owner: Code Reviewer · Skill: skills/code-review/SKILL.md
Persist as: the body of a Pull Request review (event REQUEST_CHANGES or COMMENT, never APPROVE).
Line-specific findings are also posted as review comments on the exact lines.
Severity: BLOCKER, HIGH, MEDIUM, LOW, NIT. Outcome: CHANGES REQUESTED, NO BLOCKING FINDINGS, BLOCKED.
NO BLOCKING FINDINGS is not merge approval: a human code owner approves and merges. Do not restate this
in the review.
Consider all twelve dimensions; list a row only for dimensions with findings or a note worth reading.
Do not repeat validation results that the QA report gives for the same commit: link it.
Cycle 2 and later: use the "Re-review (cycle ≥ 2)" format at the end instead of the full review.
-->

## Outcome

**<CHANGES REQUESTED | NO BLOCKING FINDINGS | BLOCKED>** — <n> BLOCKER · <n> HIGH · <n> MEDIUM · <n> LOW · <n> NIT

PR #<n> at `<short sha>` · Task #<task> · Design: <ADR-NNNN, architecture §n> or "None" · QA: <link> ·
Cycle <1 / 2 / 3> of 3

## Scope

- **Reviewed:** <files / areas>
- **Not reviewed and why:** <generated files, lockfiles, vendored code> or "None"

## Dimensions

| Dimension | Result |
| --- | --- |
| <Correctness> | <CR-1, CR-2 / note> |

Other dimensions (requirements, correctness, architecture, security, error handling, data integrity,
performance, maintainability, tests, observability, documentation, regression risk): no findings.

## Findings

### CR-1

- **Severity:** <BLOCKER | HIGH | MEDIUM | LOW | NIT>
- **Location:** `<path/to/file.ext:line>`
- **Problem:** <what is wrong>
- **Evidence:** <code path, failing input, test output, violated AC/ADR>
- **Impact:** <consequence if merged as is>
- **Recommendation:** <concrete change>

## Follow-up suggestions

- <MEDIUM/LOW items deferred to a linked follow-up Issue> (omit the section when there are none)

## Hand-off

NO BLOCKING FINDINGS → `agent:security` · CHANGES REQUESTED → `agent:developer` · BLOCKED → `<role>`
with reason

## Re-review (cycle ≥ 2)

```markdown
**Code review (cycle <n>)** · Code Reviewer · state: code-review

**<CHANGES REQUESTED | NO BLOCKING FINDINGS | BLOCKED>** at `<short sha>` · previous review: <link>

| Finding | Severity | Status | Note |
| --- | --- | --- | --- |
| CR-<n> | <severity> | fixed in `<sha>` / not fixed / disputed | <note> |

New changes reviewed: <files>. New findings: none <!-- or CR-<n> in the full finding format -->
```
