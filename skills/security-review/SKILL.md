---
name: security-review
description: Perform a practical application security review of a Pull Request - attack surface mapping, then authentication, authorization, secrets, input validation, injection, XSS, CSRF, SSRF, IDOR, path traversal, file uploads, dependencies, sensitive data, logging, encryption, CORS, security headers, containers, CI/CD, infrastructure, privilege escalation and insecure defaults - and report actionable findings by severity. Use after QA has passed, in parallel with the code review, before human approval.
---

# Security Review

## Purpose

Find exploitable weaknesses introduced or exposed by a change before it is merged, and give
remediation a Developer can implement and test. A clean review means "no issues found in the
reviewed scope with the methods used" — never "the system is secure".

## When to use

- A Pull Request is labelled `agent:security` (code review outcome `NO BLOCKING FINDINGS`).
- A QA or code review finding flags a possible security problem.
- An architecture document introduces a new trust boundary (review on request, design level).

## Inputs

- Pull Request diff, description, QA report and code review.
- Architecture document (trust boundaries, data classification) and Accepted ADRs.
- Dependency manifests and lockfiles; Dockerfiles; CI workflows; infrastructure configuration.
- Security tooling the project provides (audit commands, SAST configuration) and any GitHub
  security alerts the token can read.

## Procedure

1. **Map the attack surface.** From the diff, list: new or changed entry points (HTTP routes,
   message handlers, CLI args, file parsers), data stores touched, trust boundaries crossed,
   identities and permissions involved, new dependencies, configuration and infrastructure changes.
   Classify data handled (public, internal, personal, secret).
2. **Trace untrusted input.** For each entry point, follow input from source to every sink
   (database query, shell, filesystem, HTML output, outbound request, deserialiser, log).
3. **Review each area** below. Record for every area: finding(s), "no issue found" with what was
   checked, or "not applicable" with the reason.
4. **Run tooling** available in the sandbox: dependency audit for the ecosystem
   (`npm audit`, `pip-audit`, `cargo audit`, `govulncheck`, …), the project's SAST if configured,
   a secret scan over the diff. Treat tool output as leads; verify each before reporting.
5. **Rate severity** by exploitability (who can reach it, preconditions) and impact (what an
   attacker gains) *in this system*.
6. **Write findings** in the format below with concrete remediation and how to test the fix.
7. **Decide the outcome** — `CHANGES REQUESTED` if any `BLOCKER`/`HIGH` is open; otherwise
   `NO BLOCKING FINDINGS`; `BLOCKED` if the review could not be completed.
8. **Submit** one review using [templates/security-review.md](../../templates/security-review.md)
   (`REQUEST_CHANGES` or `COMMENT`). You run in parallel with the code reviewer; the coordinator moves
   the labels once both outcomes are in.
   When the agents use the same GitHub identity as the Pull Request author, GitHub does not accept
   `REQUEST_CHANGES` on your own Pull Request: submit `COMMENT` with the outcome in the body and, for
   `CHANGES REQUESTED`, add the label `changes-requested` (it makes the Pull Request check fail).
   Never submit `APPROVE`.

### Review areas

| Area | What to check |
| --- | --- |
| Authentication | Every new endpoint requires authentication unless explicitly public; session/token validation (signature, expiry, audience); password and reset flows; brute-force protection |
| Authorization | Checks on every path, server-side, deny by default; role and tenant scoping; no reliance on client-supplied roles |
| IDOR | Object references (IDs in paths, bodies, queries) are checked against the caller's ownership/tenant |
| Privilege escalation | Users cannot change their own role, tenant or ownership fields (mass assignment); admin functions isolated |
| Secrets | No secrets in code, config, tests, logs, error messages or client bundles; loaded from environment/secret store; rotated if exposed |
| Input validation | Type, length, range, format and allow-list validation at trust boundaries; canonicalisation before validation |
| Injection (SQL, NoSQL, command, LDAP, template) | Parameterised queries; no string-built queries or shell commands with input; safe APIs instead of `shell=True`/`eval` |
| XSS | Context-aware output encoding; no unsafe HTML injection APIs with untrusted data; Content-Security-Policy where applicable |
| CSRF | State-changing requests protected (SameSite cookies, CSRF tokens) when cookie-based auth is used |
| SSRF | Outbound requests to user-influenced URLs restricted by allow-list; internal address ranges and metadata endpoints blocked; redirects controlled |
| Path traversal | File paths built from input are normalised and confined to a base directory |
| File uploads | Size and type limits, content validation, storage outside web root, generated names, malware scanning where required |
| Dependencies | New/updated packages: known vulnerabilities, maintenance, licence, typosquatting, pinned via lockfile |
| Sensitive information | Personal data minimised, not returned unnecessarily, retention respected; error messages leak no internals |
| Logging | Security events logged (auth failures, permission denials); no secrets, tokens or unnecessary personal data in logs; log injection prevented |
| Encryption | TLS for data in transit; approved algorithms and libraries; no custom crypto; keys from a secret store; at-rest encryption where required |
| CORS | No wildcard origins with credentials; allow-list of origins; minimal methods/headers |
| Security headers | HSTS, CSP, `X-Content-Type-Options`, frame protections, cache control on sensitive responses — as applicable to the app type |
| Containers | Minimal, pinned base images; non-root user; no secrets in layers or build args; only required ports |
| CI/CD | Workflow permissions minimal; no untrusted input interpolated into `run:`; `pull_request_target` used safely or not at all; third-party actions pinned; secrets not exposed to forks |
| Infrastructure | Least-privilege IAM, no public storage or databases, network exposure minimal, infrastructure-as-code reviewed for insecure defaults |
| Insecure defaults | Debug modes off, default credentials absent, features fail closed, secure cookie flags, safe framework defaults not overridden |

### Finding format

```markdown
Severity: BLOCKER | HIGH | MEDIUM | LOW | NIT
Location: path/to/file.ext:line (endpoint, workflow, image)
Risk: the weakness and the vulnerability class (e.g. IDOR, CWE-639)
Evidence: the source-to-sink trace, request example, configuration line or tool output (verified)
Impact: what an attacker can achieve, who can exploit it, preconditions
Recommended remediation: the concrete control, where it goes, and how to test that it works
```

Severity uses the shared scale. Security guidance: `BLOCKER` — exploitable by an unauthenticated
or low-privileged attacker with significant impact, or any exposed secret; `HIGH` — exploitable
with preconditions or significant impact; `MEDIUM` — defence-in-depth gap with plausible
exploitation; `LOW` — hardening with limited impact; `NIT` — informational.

## Rules

- Never claim a system or change is secure because a checklist passed. State scope and limits.
- Never repeat a secret value. Report its location; secrets found are `BLOCKER` and must be rotated
  by a human even after removal from the branch.
- Never run active attacks against deployed or shared environments; verify in the sandbox only.
- Never publish exploit details for a vulnerability already on `main` in a public channel; follow
  [SECURITY.md](../../SECURITY.md).
- Findings must be actionable: no "consider security best practices".
- Do not modify files or push commits; never submit `APPROVE`.
- Risk acceptance for `HIGH` findings is a human decision recorded on the Pull Request.

## Required outputs

- One Pull Request review following [templates/security-review.md](../../templates/security-review.md)
  with the attack surface, area results, findings, tooling used, limitations and outcome.
- Line comments for line-specific findings.
- Updated labels.

## Quality checklist

- [ ] Attack surface is mapped (entry points, boundaries, data classes, dependencies).
- [ ] Every review area has a result with what was checked or why it is not applicable.
- [ ] Every injection-type finding includes a source-to-sink trace.
- [ ] Every finding has all six fields and a severity from the shared scale.
- [ ] Tool output was verified before being reported.
- [ ] No secret value appears in the review.
- [ ] Limitations (unreviewed areas, unavailable tools) are stated.
- [ ] Review event is `REQUEST_CHANGES` or `COMMENT`, never `APPROVE`.

## Failure conditions

- Secret discovered anywhere → `BLOCKER`, `needs-human` immediately, location only.
- Vulnerability present on `main` independent of this PR → private report per SECURITY.md, `needs-human`.
- Required context missing (no architecture for a new trust boundary) → `BLOCKED`, `agent:architect`.
- Remediation requires architectural change → finding + `agent:architect` mention + `needs-human`.

## Examples

```markdown
Severity: BLOCKER
Location: src/api/invoices.ts:34 (GET /api/invoices/:id)
Risk: Insecure direct object reference (CWE-639)
Evidence: Handler loads `Invoice.findById(req.params.id)` and returns it; no check of
`invoice.tenantId === req.user.tenantId`. Sandbox test: user of tenant A requested an invoice ID of
tenant B and received HTTP 200 with the invoice body.
Impact: Any authenticated user can read every tenant's invoices (personal and financial data) by
enumerating IDs.
Recommended remediation: Scope the query: `Invoice.findOne({ id, tenantId: req.user.tenantId })`,
return 404 when not found; add an integration test asserting 404 for a cross-tenant ID.
```

```markdown
Severity: MEDIUM
Location: .github/workflows/ci.yml:22
Risk: Script injection in CI via untrusted PR title
Evidence: `run: echo "${{ github.event.pull_request.title }}"` interpolates attacker-controlled
text into a shell command.
Impact: A crafted PR title executes commands in the CI runner with the workflow's token permissions.
Recommended remediation: Pass the value through an environment variable
(`env: TITLE: ${{ github.event.pull_request.title }}` then `echo "$TITLE"`); test with a title
containing `"; id; "`.
```
