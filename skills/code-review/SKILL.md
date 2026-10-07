---
name: code-review
description: Review a Pull Request semantically in a fixed order - requirements, correctness, architecture, security, error handling, data integrity, performance, maintainability, tests, observability, documentation, regression risk - and report evidence-based findings with Severity, Location, Problem, Evidence, Impact and Recommendation on the BLOCKER/HIGH/MEDIUM/LOW/NIT scale. Use after QA has passed, in parallel with the security review.
---

# Code Review

## Purpose

Find the defects and risks that deterministic CI cannot: wrong behaviour, missed requirements,
design violations, unsafe error handling, data corruption, maintainability traps — and report
them so precisely that the Developer can act without a follow-up conversation.

## When to use

- A Pull Request is labelled `agent:reviewer` (QA verdict `PASS`).
- A Developer pushed fixes for your earlier findings (re-review).
- The Architect is asked for an architectural consistency review (uses dimensions 1, 3, 8, 12).

## Inputs

- Pull Request description, diff, commit history and CI results.
- Linked task Issue and parent feature Issue (requirements and acceptance criteria).
- Architecture document and Accepted ADRs relevant to the changed components.
- QA report on the Pull Request.
- The surrounding code: callers, callees, existing tests and conventions.

## Procedure

1. **Understand intent first.** Read the task's objective, scope, acceptance criteria and the PR
   description before the diff. Note what the change *should* do.
2. **Survey the diff.** List changed files and classify them (source, tests, config, migrations,
   docs, generated). Decide what is out of review scope (for example generated lockfiles) and say so.
   Load the stack skill of every stack the diff touches (`stack-java-spring`, `stack-react`, ...;
   the module's specialist is in the Pull Request's task `Stack:` line or in
   [stack-routing](../stack-routing/SKILL.md)) and use its quality checklist and "common review
   findings" as stack-specific questions inside the dimensions below.
3. **Check out and explore.** Check out the branch in the sandbox. Open the surrounding code for
   every non-trivial hunk: callers, error paths, data flow.
4. **Review in this order.** For each dimension, ask the questions and record findings.

   | # | Dimension | Key questions |
   | --- | --- | --- |
   | 1 | Requirements | Is every acceptance criterion implemented? Anything implemented that was not asked? Out-of-scope changes? |
   | 2 | Correctness | Does the logic do what it claims for all inputs, including empty, null, boundary, concurrent and repeated calls? Off-by-one, time zones, units, encoding? |
   | 3 | Architecture | Does it follow the architecture document and Accepted ADRs? Right layer, right component, no new coupling or duplicate abstractions? |
   | 4 | Security | Untrusted input validated? Authorization checked on every path? Secrets handled correctly? (Deep review is the Security Reviewer's; flag what you see.) |
   | 5 | Error handling | Are errors caught at the right level, surfaced with useful messages, not swallowed? Resources released? Partial failures handled? |
   | 6 | Data integrity | Transactions, idempotency, race conditions, migrations reversible, constraints enforced, no data loss on failure? |
   | 7 | Performance | N+1 queries, unbounded loops or result sets, missing pagination or indexes, blocking calls in hot paths — relative to the stated NFRs? |
   | 8 | Maintainability | Clear naming and structure consistent with the codebase? Duplication? Complexity justified? Dead code? |
   | 9 | Tests | Do tests cover each acceptance criterion and the risky branches? Would they fail if the code were wrong? Are they deterministic? |
   | 10 | Observability | Can failures be diagnosed from logs/metrics? Are log levels right? No secrets or personal data logged? |
   | 11 | Documentation | Are README, API docs, configuration docs, changelog and ADRs updated for behaviour changes? |
   | 12 | Regression risk | What existing behaviour could break? Are callers and backward compatibility covered? Is rollout/rollback safe? |

5. **Verify before reporting.** For each suspected defect produce evidence: a code path walk-through
   with line references, a failing input, a scratch test run in the sandbox (never committed), or a
   reference to the ADR/requirement violated. Drop suspicions you cannot substantiate, or report
   them as a question at `LOW`.
6. **Write findings** using the format below; assign severity by impact, not by effort to fix.
7. **Decide the outcome.**
   - `CHANGES REQUESTED` — any open `BLOCKER` or `HIGH` finding.
   - `NO BLOCKING FINDINGS` — no open `BLOCKER`/`HIGH`. Never phrase this as approval to merge.
   - `BLOCKED` — the review cannot be completed (PR too large, missing context, branch does not build).
8. **Submit.** Post one review using [templates/code-review.md](../../templates/code-review.md):
   event `REQUEST_CHANGES` for `CHANGES REQUESTED`, otherwise `COMMENT`. Place line-specific
   findings as review comments on the exact lines. You run in parallel with the security reviewer;
   the coordinator moves the labels once both outcomes are in.
   When the agents use the same GitHub identity as the Pull Request author, GitHub does not accept
   `REQUEST_CHANGES` on your own Pull Request: submit `COMMENT` with the outcome in the body and, for
   `CHANGES REQUESTED`, add the label `changes-requested` (it makes the Pull Request check fail).
   Never submit `APPROVE`.

**Re-review.** Verify each earlier finding and mark it `fixed` / `not fixed` / `disputed`, review
only the new changes for new problems, and recompute the outcome.

### Finding format

```markdown
Severity: BLOCKER | HIGH | MEDIUM | LOW | NIT
Location: path/to/file.ext:line (or function / commit)
Problem: what is wrong, in one or two sentences
Evidence: the code path, failing input, test output or violated requirement/ADR that proves it
Impact: what happens to users, data, security or maintainers if merged as is
Recommendation: the concrete change that resolves it
```

### Severity scale

| Severity | Meaning | Merge effect |
| --- | --- | --- |
| `BLOCKER` | Incorrect, unsafe, data-losing, requirement-breaking or secret-exposing | Must be fixed |
| `HIGH` | Significant defect or risk likely to cause failures or major maintenance cost | Must be fixed unless a human accepts the risk in writing |
| `MEDIUM` | Real problem with limited impact | Fix in this PR or link a follow-up Issue |
| `LOW` | Minor improvement with clear benefit | Optional |
| `NIT` | Optional remark | Never blocks |

## Rules

- No subjective style comments. Formatting and style belong to linters; comment on style only when
  it breaks a written project convention or materially harms readability or correctness.
- Every finding has all six fields. No evidence → no finding.
- Do not inflate severity to force a preference, or deflate it to be agreeable.
- Report everything you see in the first pass; do not drip-feed findings across cycles.
- Never push commits, apply suggestions or edit files; never submit `APPROVE`.
- Distinguish facts from questions: if you are unsure, ask a question rather than assert a defect.
- Acknowledge explicitly which areas were not reviewed and why.

## Required outputs

- One Pull Request review per cycle following [templates/code-review.md](../../templates/code-review.md),
  with a dimension summary table, findings and the outcome.
- Line comments for line-specific findings.
- Updated label.

## Quality checklist

- [ ] Intent (task, AC) was read before the diff.
- [ ] All twelve dimensions have a one-line result in the summary.
- [ ] Every finding has Severity, Location, Problem, Evidence, Impact, Recommendation.
- [ ] Severities follow the shared scale; outcome follows step 7.
- [ ] No style-only comments without a written convention behind them.
- [ ] Out-of-scope / not-reviewed areas are stated.
- [ ] Review event is `REQUEST_CHANGES` or `COMMENT`, never `APPROVE`.

## Failure conditions

- PR is too large or mixes unrelated concerns → `BLOCKED`, ask `agent:planner` to split.
- Linked task or requirements are missing → `BLOCKED`, `agent:planner`.
- Branch does not build or QA report is missing → `BLOCKED`, return to `agent:qa`/`agent:developer`.
- A disputed `BLOCKER`/`HIGH` is not resolved after one exchange → `needs-human`.

## Examples

```markdown
Severity: HIGH
Location: src/auth/AuthService.ts:57
Problem: A successful login resets `last_failed_at` but not `failed_attempts`, so the counter keeps
growing across successful logins.
Evidence: AC-2 (#120) requires the counter to reset on success. Walk-through: login() → onSuccess()
→ `update users set last_failed_at = null` (line 57); `failed_attempts` untouched. QA-2 in the QA
report reproduces this (HTTP 429 after a successful login).
Impact: Legitimate users are locked out after 5 lifetime failures; support load and user lockouts.
Recommendation: Reset `failed_attempts = 0` in the same update and add a unit test asserting the reset.
```

```markdown
Severity: NIT
Location: src/auth/AuthService.ts:41
Problem: Magic number 5 duplicates `MAX_FAILED_ATTEMPTS` defined in `src/auth/config.ts:12`.
Evidence: Both values must change together; the project's CONTRIBUTING requires named constants.
Impact: Future threshold changes may update one place only.
Recommendation: Use `MAX_FAILED_ATTEMPTS`.
```
