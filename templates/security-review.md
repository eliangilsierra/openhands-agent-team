**Security review** · Security Reviewer · state: security-review

# Security review: PR #<n> — <title>

<!--
Owner: Security Reviewer · Skill: skills/security-review/SKILL.md
Persist as: the body of a Pull Request review (event REQUEST_CHANGES or COMMENT, never APPROVE).
Never include a secret value anywhere in this review; report locations only.
Severity: BLOCKER, HIGH, MEDIUM, LOW, NIT. Outcome: CHANGES REQUESTED, NO BLOCKING FINDINGS, BLOCKED.
This review reports issues found in the reviewed scope with the methods listed. It is not a statement
that the system is secure. Do not restate this in the review.
Consider every review area; list a row only for areas with findings or that the change touches, with
what was checked. Name the remaining areas in the two summary lines.
Do not repeat build or test results that the QA report gives for the same commit: link it.
Cycle 2 and later: use the "Re-review (cycle ≥ 2)" format at the end instead of the full review.
-->

## Outcome

**<CHANGES REQUESTED | NO BLOCKING FINDINGS | BLOCKED>** — <n> BLOCKER · <n> HIGH · <n> MEDIUM · <n> LOW · <n> NIT

PR #<n> at `<short sha>` · Task #<task> · Trust boundaries: <architecture link> or "None" · Cycle
<1 / 2 / 3> of 3

## Attack surface

| Entry point / change | Type | Trust boundary | Data classification | Authentication |
| --- | --- | --- | --- | --- |
| <GET /api/…, worker, workflow, Dockerfile> | <HTTP / queue / CLI / file / CI / infra> | <boundary> | <public / internal / personal / secret> | <mechanism or none> |

New or updated dependencies: <package@version — reason> or "None".

## Review areas

| Area | Result | What was checked |
| --- | --- | --- |
| <Input validation> | <No issue found / SR-n> | <the specific check> |

No issue found: <areas checked with no finding, comma-separated>.
Not applicable: <areas, comma-separated> (<one-line reason, e.g. no HTTP output, no file handling>).

Areas: authentication, authorization, IDOR, privilege escalation, secrets, input validation, injection
(SQL, command, template), XSS, CSRF, SSRF, path traversal, file uploads, dependencies, sensitive
information, logging, encryption, CORS, security headers, containers, CI/CD, infrastructure, insecure
defaults. <!-- reference list; do not copy into the review -->

## Findings

### SR-1

- **Severity:** <BLOCKER | HIGH | MEDIUM | LOW | NIT>
- **Location:** `<path/to/file.ext:line>` / <endpoint, workflow, image>
- **Risk:** <weakness and class, e.g. IDOR (CWE-639)>
- **Evidence:** <source-to-sink trace, request example, config line, verified tool output>
- **Impact:** <what an attacker gains, who can exploit, preconditions>
- **Recommended remediation:** <control, location, and how to test the fix>

## Tooling

| Tool / command | Result | Notes |
| --- | --- | --- |
| <npm audit --omit=dev / pip-audit / project SAST / secret scan> | <summary> | <verified findings → SR-n> |

Limitations: <areas not reviewed, tools unavailable, environment differences> or "None".

## Risk acceptance (only when a HIGH finding is accepted)

| Finding | Accepted by | Link to written acceptance | Follow-up Issue |
| --- | --- | --- | --- |
| SR-<n> (HIGH) | @<human> | <comment link> | #<n> |

## Hand-off

NO BLOCKING FINDINGS → `needs-human` (awaiting human approval) · CHANGES REQUESTED → `agent:developer` ·
BLOCKED → `<role>` with reason

## Re-review (cycle ≥ 2)

```markdown
**Security review (cycle <n>)** · Security Reviewer · state: security-review

**<CHANGES REQUESTED | NO BLOCKING FINDINGS | BLOCKED>** at `<short sha>` · previous review: <link>

| Finding | Severity | Status | Note |
| --- | --- | --- | --- |
| SR-<n> | <severity> | fixed in `<sha>` / not fixed / disputed | <how the fix was verified> |

New changes reviewed: <files>; attack surface changed: no <!-- or the new rows -->.
New findings: none <!-- or SR-<n> in the full finding format -->. Tooling re-run: <command> → <result>.
```
