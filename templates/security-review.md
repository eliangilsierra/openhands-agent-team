**Security review** · Security Reviewer · state: security-review

# Security review: PR #<n> — <title>

<!--
Owner: Security Reviewer · Skill: skills/security-review/SKILL.md
Persist as: the body of a Pull Request review (event REQUEST_CHANGES or COMMENT, never APPROVE).
Never include a secret value anywhere in this review; report locations only.
Severity: BLOCKER, HIGH, MEDIUM, LOW, NIT. Outcome: CHANGES REQUESTED, NO BLOCKING FINDINGS, BLOCKED.
-->

## Outcome

**<CHANGES REQUESTED | NO BLOCKING FINDINGS | BLOCKED>** — <n> BLOCKER · <n> HIGH · <n> MEDIUM · <n> LOW · <n> NIT

| Field | Value |
| --- | --- |
| Pull Request | #<n> at commit `<sha>` |
| Task / requirements | #<task> · #<feature> |
| Architecture / trust boundaries | <link> or "None" |
| Review cycle | <1 / 2 / 3> of 3 |

This review reports issues found in the reviewed scope with the methods listed below. It is not a
statement that the system is secure.

## Attack surface

| Entry point / change | Type | Trust boundary | Data classification | Authentication |
| --- | --- | --- | --- | --- |
| <GET /api/…, worker, workflow, Dockerfile> | <HTTP / queue / CLI / file / CI / infra> | <boundary> | <public / internal / personal / secret> | <mechanism or none> |

New or updated dependencies: <package@version — reason> or "None".

## Review areas

| Area | Result | What was checked |
| --- | --- | --- |
| Authentication | <No issue found / SR-n / Not applicable — reason> | |
| Authorization | | |
| IDOR | | |
| Privilege escalation | | |
| Secrets | | |
| Input validation | | |
| Injection (SQL, command, template) | | |
| XSS | | |
| CSRF | | |
| SSRF | | |
| Path traversal | | |
| File uploads | | |
| Dependencies | | |
| Sensitive information | | |
| Logging | | |
| Encryption | | |
| CORS | | |
| Security headers | | |
| Containers | | |
| CI/CD | | |
| Infrastructure | | |
| Insecure defaults | | |

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

## Limitations

- <areas not reviewed, tools unavailable, environment differences> or "None"

## Risk acceptance (if any)

| Finding | Accepted by | Link to written acceptance | Follow-up Issue |
| --- | --- | --- | --- |
| SR-<n> (HIGH) | @<human> | <comment link> | #<n> |

## Hand-off

- NO BLOCKING FINDINGS → `needs-human` (awaiting human approval)
- CHANGES REQUESTED → `agent:developer`
- BLOCKED → `<role>` with reason
