---
name: planning
description: Decompose a feature's requirements and architecture into small, dependency-ordered, traceable GitHub task Issues (Context, Objective, Scope, Out of scope, Technical approach, Dependencies, Acceptance criteria, Testing requirements, Definition of Done) and decide which are ai-ready. Use after requirements (and architecture, when needed) are complete.
---

# Planning

## Purpose

Turn "what" and "how, at the system level" into a sequence of tasks that each fit in one
reviewable Pull Request, can be implemented without reconstructing the whole feature history,
and trace back to requirements so nothing is lost and nothing is added.

## When to use

- A feature Issue is labelled `agent:planner` with complete requirements and, if required,
  an architecture document whose ADRs are Accepted.
- A Developer, QA Engineer or reviewer reports that a task is too large or under-specified.
- A bug report has defined expected behaviour and needs a fix task.

## Inputs

- Feature Issue: requirements (`FR`, `NFR`), acceptance criteria (`AC`), scope.
- Architecture document and its work packages; Accepted ADRs.
- Research reports referenced by the design.
- Target repository: module structure, test layout, build and test commands.

## Procedure

1. **Verify readiness of inputs.** Requirements pass the product-management checklist; any
   required ADR is `Accepted`. If not, stop and hand back (see Failure conditions).
2. **Identify affected components.** From the architecture and the code, list modules, services,
   data stores, configuration and documentation that change.
3. **Slice the work.** Start from the architecture's work packages. Prefer *vertical slices* — a
   thin, testable end-to-end behaviour — over layer-by-layer tasks. Typical slice order:
   1. Enabling changes (schema migration, configuration, interface definition) that are
      backward compatible and testable on their own.
   2. The core behaviour for the main acceptance criteria.
   3. Edge cases, error handling and non-functional requirements.
   4. Observability and documentation if not already part of earlier slices.
4. **Size check.** Each task should produce a Pull Request reviewable in one sitting (guide:
   < ~400 changed lines excluding generated code and fixtures; one primary concern). Split any
   task that touches unrelated components or needs more than one migration.
5. **Dependencies and order.** For each task list blocking tasks (`Depends on #n`) and mark tasks
   that can proceed in parallel. Avoid dependency chains longer than necessary. In the Technical
   approach of every task, add a line `Touches: <paths or globs>` with the files it is expected to
   change: the coordinator runs two developers in parallel only on tasks whose `Touches` sets do not
   overlap.
6. **Write each task Issue** with the sections below. Copy the minimum context needed and link the
   rest. Assign `AC` IDs from the feature (and task-specific ones, `T-AC-n`, where a task needs
   finer criteria).

   ```markdown
   ## Context
   ## Objective
   ## Scope
   ## Out of scope
   ## Technical approach
   ## Dependencies
   ## Acceptance criteria
   ## Testing requirements
   ## Definition of Done
   ```

7. **Traceability.** Build a matrix `FR/NFR → AC → task`. Every requirement maps to ≥ 1 task;
   every task maps to ≥ 1 requirement or reviewer finding.
8. **Readiness checklist.** Apply to each task:
   - [ ] All nine sections present and specific.
   - [ ] Objective is a single outcome.
   - [ ] Acceptance criteria are testable (Given/When/Then or an exact check).
   - [ ] Testing requirements name the test level(s) and the cases.
   - [ ] Technical approach is consistent with the architecture and Accepted ADRs.
   - [ ] Dependencies are closed or explicitly allow parallel work.
   - [ ] No open question remains that would block implementation.
   - [ ] Size fits one reviewable Pull Request.
9. **Publish.** Post the implementation plan (template
   [templates/implementation-plan.md](../../templates/implementation-plan.md)) on the feature
   Issue; create the task Issues; append a "Tasks" checklist to the feature Issue; label tasks
   that pass the checklist and have no open dependencies `ai-ready` + `agent:developer`; label
   the rest `agent:planner` (internal dependency) or `blocked` (external dependency, with a comment).
10. **Hand off.** Remove `agent:planner` from the feature Issue and comment the list of ready tasks.

## Rules

- A task is **small, testable, independently understandable, implementable and traceable**. If any
  of the five fails, the task is not ready.
- Never add scope. Improvements noticed during planning become separate Issues marked as such.
- Never plan against a `Proposed` ADR.
- The technical approach guides; it does not dictate line-by-line code. It names the components,
  interfaces and patterns to use, and the decisions already made.
- Testing requirements are concrete: "Unit tests for `ThrottleService.recordFailure` covering
  threshold, reset on success and window expiry; integration test for `POST /login` returning 429"
  — not "add tests".
- Each task's Definition of Done includes AGENTS.md section 12 plus task-specific items.
- Only the Planner (or a human) adds `ai-ready`.

## Required outputs

- Implementation plan comment on the feature Issue.
- One task Issue per slice, created from the [task form](../../.github/ISSUE_TEMPLATE/task.yml)
  structure, linked to the parent ("Part of #n" or as a sub-issue).
- Updated labels on tasks and on the feature Issue.

## Quality checklist

- [ ] Every `FR`/`NFR` appears in the traceability matrix with at least one task.
- [ ] No task lacks a requirement or reviewer-finding reference.
- [ ] Each task passes the readiness checklist or is labelled with why it is not ready.
- [ ] Dependency order has no cycles; parallel tasks are marked.
- [ ] Migrations and backward compatibility are sequenced safely (expand → migrate → contract).
- [ ] No task requires reading the whole feature history to understand it.
- [ ] Testing requirements are specific for each task.

## Failure conditions

- Requirements incomplete or untestable → `agent:product` with the gap.
- Architecture missing for a change that needs it, or ADR still `Proposed` → `agent:architect`
  (or `needs-human` for ADR acceptance).
- A slice cannot be made reviewable without a design change → `agent:architect`.
- The plan implies effort or cost the requester probably does not expect → summarise and add
  `needs-human` before creating Issues.

## Examples

**Feature:** login throttling (FR-1, NFR-1, AC-1..AC-3; ADR-0007 Accepted).

**Plan:**

| # | Task | Requirements | Depends on | Parallel |
| --- | --- | --- | --- | --- |
| 1 | Add `failed_attempts` and `last_failed_at` to `users` (migration + rollback) | FR-1 | — | — |
| 2 | Block login after 5 failures in 15 min; reset on success | FR-1, AC-1, AC-2 | 1 | — |
| 3 | Automatic unblock after 15 min; structured log event `login.throttled` | NFR-1, AC-3 | 2 | — |

**Task 2 (excerpt):**

```markdown
## Context
Part of #120 (login throttling). ADR-0007 stores throttling state in the users table; task #121
added the columns.

## Objective
Reject login for an account after 5 consecutive failed attempts within 15 minutes.

## Scope
- `AuthService.login` failure/success handling
- HTTP 429 response with message "Too many attempts. Try again later."

## Out of scope
- Automatic unblock timing (task #123), IP-based limits (#330)

## Acceptance criteria
- AC-1, AC-2 from #120 (copied verbatim)

## Testing requirements
- Unit: threshold reached at 5th failure; counter reset on success; failures older than 15 min ignored
- Integration: `POST /login` returns 429 on the 6th attempt; correct password still rejected while blocked
```
