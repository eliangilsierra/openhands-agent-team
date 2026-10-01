# Requirements: <feature name>

<!--
Owner: Product Manager · Skill: skills/product-management/SKILL.md
Persist as: the body of the feature Issue. Keep the original request quoted in "Original request".
Replace every <angle-bracket> value. Never delete a section: write "None" and why.
IDs: G-n goals, FR-n functional, NFR-n non-functional, AC-n acceptance criteria,
A-n assumptions, R-n risks, Q-n open questions. IDs are never reused after deletion.
-->

**Status:** Draft | Ready for sign-off | Signed off by @<human> on <YYYY-MM-DD>
**Next stage:** research | architecture | planning — <one-line reason>

## Problem

<Who has the problem, in which situation, what happens today, and why it matters. No solution.>

## Users and stakeholders

| User / stakeholder | Need | Source |
| --- | --- | --- |
| <role that exists in the product> | <what they need from this change> | <Issue, comment, doc link> |

## Goals

| ID | Goal (outcome) | Success signal | Source |
| --- | --- | --- | --- |
| G-1 | <outcome for the user or business> | <measurable signal, or "unknown — see Q-n"> | <link> |

## Scope

**In scope**

- <capability included>

**Out of scope**

- <capability a reader might expect but is excluded> — <reason or follow-up Issue #n>

## Functional requirements

| ID | Requirement ("The system shall …") | Source |
| --- | --- | --- |
| FR-1 | <one user-observable behaviour> | <link or quote> |

## Non-functional requirements

| ID | Category | Requirement with measurable threshold | Source |
| --- | --- | --- | --- |
| NFR-1 | <performance / availability / security / privacy / accessibility / compatibility / compliance> | <threshold, e.g. "p95 < 300 ms at 50 req/s"> | <link> |

## Acceptance criteria

| ID | Requirement | Given | When | Then |
| --- | --- | --- | --- | --- |
| AC-1 | FR-1 | <precondition> | <action> | <observable outcome> |
| AC-2 | FR-1 | <boundary or negative precondition> | <action> | <observable outcome> |

## Assumptions

| ID | Assumption | How to verify | Owner |
| --- | --- | --- | --- |
| A-1 | <statement believed true but not verified> | <check> | <role or @human> |

## Risks

| ID | Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- | --- |
| R-1 | <what could go wrong> | Low / Medium / High | Low / Medium / High | <action> |

## Dependencies

- <other Issue, team, external system, or "None">

## Open questions

| ID | Question | Who can answer | Blocks |
| --- | --- | --- | --- |
| Q-1 | <precise question> | <@human or role> | <FR/AC IDs or stage> |

## Traceability

| Requirement | Acceptance criteria |
| --- | --- |
| FR-1 | AC-1, AC-2 |

## Original request

> <verbatim original request, with author and date>
