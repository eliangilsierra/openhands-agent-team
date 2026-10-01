---
name: architecture
description: Design the simplest architecture that satisfies a feature's requirements and constraints - context, components, interfaces, APIs, data, security, reliability, observability, performance, scalability, deployment, cost - evaluate alternatives, document trade-offs and record hard-to-reverse decisions as ADRs. Use for new components, APIs, data models, trust boundaries or infrastructure.
---

# Architecture

## Purpose

Produce a design that a Planner can decompose and a Developer can implement without making
architectural decisions on the fly, and leave a written record of **why** each decision was made
so that future readers can revisit it with full context.

## When to use

- A feature or architecture Issue is labelled `agent:architect`.
- A change introduces a new component, external dependency, public API, data model change, trust
  boundary or infrastructure.
- A later stage reports a design gap (feedback loop `design-gap`).
- A reviewer asks for an architectural consistency review of a Pull Request.

Skip this Skill when the change fits inside existing components and introduces none of the above
(see `skip_when` for the `architecture` state in `config/workflow.yaml`).

## Inputs

- Requirements and acceptance criteria (feature Issue).
- Research reports.
- Existing system: code, configuration, deployment files, `docs/architecture/`, Accepted ADRs.
- Constraints: hosting, budget, team skills, compliance, deadlines (Issue or ADRs).

## Procedure

Work through the steps in order. Each step produces a section of
[templates/architecture.md](../../templates/architecture.md). Where a concern is unaffected, write
"No change" and the reason — never leave it blank.

1. **Requirements.** List the `FR`/`NFR` IDs the design must satisfy. Identify the
   architecturally significant ones: those that constrain structure (latency, availability,
   data residency, multi-tenancy, security boundaries).
2. **Constraints.** List fixed constraints with their source (ADR, hosting, budget, licence,
   compliance, existing contracts). Distinguish hard constraints from preferences.
3. **Existing system.** Describe the relevant current components, data flows and conventions,
   based on reading the code and documents. Note technical debt that affects the design.
4. **Context.** Draw the system context: users, the system, external systems, and the trust
   boundaries between them (Mermaid `flowchart`).
5. **Components.** Define each new or changed component: responsibility (one sentence), owned
   data, dependencies. Prefer extending an existing component over adding a new deployable.
6. **Interfaces and APIs.** For each interface: protocol, operation, request/response shape,
   errors and status codes, authentication, idempotency, pagination, limits, versioning and
   backward compatibility.
7. **Data.** Entities and fields, ownership, consistency requirements, indexes needed for known
   queries, migrations (forward and rollback), retention and deletion, personal data classification.
8. **Security.** Trust boundaries, authentication, authorization model, input validation points,
   secrets storage, encryption in transit and at rest, audit logging, abuse cases. Identify the
   top threats for the new attack surface (a lightweight STRIDE pass per boundary is enough).
9. **Reliability.** Failure modes of each dependency and the intended behaviour (timeouts,
   retries with backoff, idempotency, circuit breaking, degradation), data durability, backups.
10. **Observability.** Logs (events, fields, no secrets/PII), metrics (with names), traces, alerts
    tied to user-visible symptoms, and how to debug a failed request end to end.
11. **Performance.** Expected load and latency budget per operation, derived from NFRs; known
    hotspots; what will be measured to confirm.
12. **Scalability.** The first bottleneck at 10× current load and the planned response. Do not
    design for scale no requirement asks for.
13. **Deployment.** How the change is built, configured, deployed and rolled back; feature flags;
    migration ordering; configuration and secrets required at runtime.
14. **Cost.** Infrastructure, licence and operational cost (on-call, maintenance), at least as an
    order of magnitude, compared with the alternatives.
15. **Alternatives.** At least two credible alternatives, including the simplest possible one
    (often "extend the existing component" or "do nothing"). For each: how it would work, pros, cons.
16. **Trade-offs.** Explain why the chosen design wins for *these* requirements and what it gives up.
17. **ADR.** For every decision that is expensive to reverse (data store, framework, API contract,
    trust boundary, deployment topology, new infrastructure), write an ADR from
    [templates/adr.md](../../templates/adr.md) with status `Proposed`, following
    [docs/decisions/README.md](../../docs/decisions/README.md).
18. **Work packages.** List the implementation slices the Planner should consider, in dependency
    order, without writing task Issues.

Deliver the architecture document and ADRs on a `docs/<issue>-<slug>` branch, open a Pull
Request, summarise the design on the Issue and request human acceptance of each ADR.

## Rules

- **Simplicity first.** Choose the simplest design that satisfies the requirements. Every
  additional component, service, queue, cache, database or vendor must cite the requirement that
  needs it. "It might be useful later" is not a justification.
- **Explain why.** Every decision states the requirement or constraint that drives it and the
  alternative that was rejected.
- **Consistency.** Reuse existing patterns, libraries and conventions unless a requirement forces
  a change; a deliberate deviation needs an ADR.
- **Testability.** Interfaces are specified precisely enough for QA to derive tests.
- **Diagrams match text.** Every box in a diagram is described in the text and vice versa.
- **Security by design.** Every trust boundary has an authentication and authorization decision.
- **No silent requirement changes.** If the design cannot meet an NFR, say so and return to the
  Product Manager.
- **ADR status is human-controlled.** The Architect writes `Proposed`; a human sets `Accepted`.

## Required outputs

- `docs/architecture/<issue>-<slug>.md` from [templates/architecture.md](../../templates/architecture.md).
- `docs/decisions/ADR-NNNN-<slug>.md` for each significant decision, status `Proposed`.
- A `docs/` branch Pull Request containing both.
- A design summary comment on the Issue with links, the decisions needing human acceptance, and
  the hand-off to `agent:planner` once ADRs are accepted.

## Quality checklist

- [ ] Every architecturally significant `FR`/`NFR` is mapped to a component or decision.
- [ ] The existing system was inspected and is described accurately (file paths cited).
- [ ] Context diagram shows trust boundaries; diagrams and text agree.
- [ ] Every interface lists errors, authentication and compatibility behaviour.
- [ ] Data section covers ownership, migration and rollback, retention, personal data.
- [ ] Security, reliability, observability, performance, scalability, deployment and cost are concrete
      or explicitly "No change — reason".
- [ ] At least two alternatives, including the simplest one, are compared.
- [ ] Every new piece of infrastructure cites the requirement that needs it.
- [ ] Every hard-to-reverse decision has an ADR in status `Proposed`.
- [ ] Work packages are listed in dependency order.

## Failure conditions

- An NFR is not measurable or two requirements conflict → `agent:product` with the conflict.
- A decision depends on an unverified claim with material impact → open a research Issue,
  `agent:research`, `blocked`.
- No design meets the constraints → present the closest options with the constraint each violates,
  `needs-human`.
- The simplest viable design needs a paid service or new infrastructure → `needs-human` with cost
  and operational impact before proceeding.
- An Accepted ADR prevents the requirement → draft a superseding ADR, `needs-human`.

## Examples

**Requirement:** FR-1/NFR-1 from the login-throttling example in the product-management Skill.

**Alternatives considered:**

| Option | How | Pros | Cons |
| --- | --- | --- | --- |
| A. Counter columns on the existing `users` table | `failed_attempts`, `last_failed_at` updated in the login transaction | No new infrastructure; transactional; trivial to test | Write on every failed login; per-account only |
| B. New Redis instance | Key per account with TTL | Fast; TTL built in | New infrastructure to operate, secure and back up; no requirement needs its speed |
| C. Reverse-proxy rate limiting | Per-IP limit at the proxy | No app change | Does not satisfy FR-1 (per-account); distributed attacks bypass it |

**Decision:** Option A. It satisfies FR-1 and NFR-1 with no new infrastructure; the login endpoint
handles under 5 requests/s (measured from access logs), so the extra write is negligible. Option
B is rejected because no requirement needs sub-millisecond counters and it adds an operated
service. ADR-0007 "Store login throttling state in the primary database" is proposed.
