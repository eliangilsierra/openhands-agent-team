---
name: product-management
description: Turn an idea, feature request or business problem into evidence-based, testable product requirements (problem, users, goals, scope, FR/NFR, Given/When/Then acceptance criteria, risks) and a GitHub feature Issue. Use when defining or refining what should be built, not how.
---

# Product Management

## Purpose

Produce requirements that are clear, bounded, traceable and testable, so that every later stage
(research, architecture, planning, development, QA) works from the same understanding of the
problem without re-interviewing the requester.

## When to use

- A new feature Issue is labelled `agent:product`.
- A bug report needs its expected behaviour defined before it can be planned.
- A later stage reports a requirement gap (feedback loop `requirement-gap`).
- A human asks to refine, split or re-scope an existing feature Issue.

Do not use this Skill to choose technologies, design components or write tasks.

## Inputs

- The original request (Issue body, linked conversation, human message).
- Current product behaviour: target repository README, docs, related closed Issues.
- Accepted ADRs that constrain the product.
- Answers to clarifying questions posted on the Issue.

## Procedure

The process follows a fixed sequence. Do not skip a step; if a step has no content, write why.

```text
Idea → Problem → Users → Goals → Scope → Requirements → Acceptance Criteria → Risks → GitHub Issue
```

1. **Idea.** Quote the original request verbatim at the bottom of the Issue so it is never lost.
2. **Problem.** Write one paragraph: who has the problem, in which situation, what happens today,
   and why it matters. If the request is a solution ("add CSV export"), ask "what does the user
   need the solution for?" and write that problem; keep the proposed solution as an option.
3. **Users.** List each user type or stakeholder and their need. Use roles that exist in the
   product (from docs, code or Issues). Do not invent personas.
4. **Goals.** Write 1–3 outcome goals and, where data exists, a measurable success signal
   (`G-1: Support agents can find a customer's last order in under 10 s`). If no metric is known,
   write the goal and mark the metric as an open question.
5. **Scope.** Write *In scope* and *Out of scope* lists. Every item that a reasonable reader might
   assume is included but is not, goes to *Out of scope*.
6. **Requirements.**
   - Functional requirements `FR-n`: "The system shall …", one behaviour each, user-observable.
   - Non-functional requirements `NFR-n`: performance, availability, security, privacy,
     accessibility, compatibility, compliance — only those that apply, each with a measurable
     threshold or a reference to an existing standard in the project.
   - For each requirement record its **source** (requester quote, existing behaviour, ADR, law
     cited by a human). A requirement without a source is an assumption, not a requirement.
7. **Acceptance criteria.** For each `FR-n`, write one or more `AC-n` in Given/When/Then form,
   referencing the requirement: `AC-3 (FR-2): Given a user without the "admin" role, when they
   open /settings/billing, then they receive HTTP 403 and no billing data is returned.` Include at
   least one negative or boundary case per requirement where one exists.
8. **Risks, assumptions, dependencies, open questions.** Assumptions are labelled `A-n` and say
   how to verify them. Risks state likelihood, impact and mitigation. Open questions `Q-n` name who
   can answer.
9. **GitHub Issue.** Write the result into the Issue body using `templates/requirements.md`, post
   blocking questions as a numbered comment, and decide the next stage:
   - open technical or market questions → `agent:research`;
   - new component, API, data model, trust boundary or infrastructure → `agent:architect`;
   - otherwise → `agent:planner`.
   Replace `agent:product` with the next label and post a hand-off comment with the reason.

## Rules

**Avoiding vague requirements**

- Ban unmeasurable words unless quantified: *fast, easy, intuitive, robust, scalable, secure,
  user-friendly, seamless, etc.* Replace with a threshold or an observable behaviour.
- One requirement = one behaviour. Split sentences containing "and/or".
- Name the actor and the observable result in every requirement.

**Avoiding scope creep**

- Everything not traceable to the stated problem goes to *Out of scope* or a separate Issue.
- "While we're at it" ideas are recorded as follow-up Issues and linked, never merged into scope.
- Any scope increase after sign-off requires a comment explaining why and human confirmation.

**Avoiding invented requirements**

- Every `FR`/`NFR` cites a source. If you cannot cite one, write it as an assumption or question.
- Never invent metrics, user counts, deadlines, legal obligations or business rules.

**Avoiding untestable acceptance criteria**

- Each `AC` must be executable by QA and yield `PASS` or `FAIL` without interpretation.
- Avoid "should work correctly", "handles errors gracefully", "performs well". State the input,
  the action and the exact observable outcome.

**Avoiding unnecessary implementation detail**

- Describe *what* and *why*, not *how*. Technology names appear only as constraints with a source
  ("must authenticate through the existing Keycloak realm — ADR-0004").
- UI wording, field names and API shapes are included only when the requester specified them or
  they are externally visible contracts.

## Required outputs

- Feature Issue body following [templates/requirements.md](../../templates/requirements.md).
- Clarifying-questions comment when open questions block the next stage.
- Hand-off comment naming the next owner and why.

## Quality checklist

- [ ] The problem statement contains no solution.
- [ ] Every user type exists in the product or is confirmed by the requester.
- [ ] Every goal is outcome-based; metrics are either sourced or listed as open questions.
- [ ] *Out of scope* is not empty, or explains why nothing is excluded.
- [ ] Every `FR`/`NFR` has a source; none uses an unquantified vague adjective.
- [ ] Every `FR` has ≥ 1 `AC`; every `AC` references an `FR`/`NFR` and is Given/When/Then.
- [ ] At least one negative/boundary `AC` exists where applicable.
- [ ] Assumptions are labelled and have a verification method.
- [ ] No technology choice appears except as a sourced constraint.
- [ ] The next stage is chosen using the rule in step 9 and the label is updated.

## Failure conditions

Stop and escalate (see AGENTS.md section 13) instead of completing when:

- The requester cannot be reached and the problem itself is unclear → `blocked`, `needs-human`.
- Two stakeholders give contradictory requirements → `needs-human` with both versions quoted.
- The request implies legal, privacy, safety or financial obligations not stated anywhere → `needs-human`.
- The request conflicts with an Accepted ADR → hand off to `agent:architect` with the ADR link.
- The request contains several independent features → propose a split; wait for confirmation.

## Examples

**Vague input:** "Make login more secure."

**Bad requirement:** "FR-1: Login shall be secure and use Redis rate limiting."
(unmeasurable, invents a solution, no source)

**Good result (excerpt):**

```markdown
## Problem
Support reports (#311, #318) show repeated password-guessing attempts against customer accounts.
Today the login endpoint accepts unlimited attempts, so an attacker can try passwords indefinitely.

## Requirements
- FR-1: The system shall temporarily block login for an account after 5 consecutive failed
  attempts within 15 minutes. Source: security incident #318, requester comment 2026-09-12.
- NFR-1: A blocked account shall be unblocked automatically 15 minutes after the last failed
  attempt. Source: requester comment 2026-09-12.

## Acceptance criteria
- AC-1 (FR-1): Given an account with 4 failed attempts in the last 15 minutes, when a 5th attempt
  fails, then the 6th attempt with the correct password is rejected with the message
  "Too many attempts. Try again later."
- AC-2 (FR-1): Given an account with 4 failed attempts, when the 5th attempt succeeds, then login
  succeeds and the failure counter resets.
- AC-3 (NFR-1): Given a blocked account, when 15 minutes pass after the last failed attempt, then
  login with the correct password succeeds.

## Out of scope
- CAPTCHA, multi-factor authentication, IP-based blocking (separate Issue #330).

## Assumptions
- A-1: Thresholds 5/15 min are acceptable to support. Verify: confirm with support lead.
```

Next stage: `agent:architect` — the failure counter needs storage and a decision on where
throttling state lives.
