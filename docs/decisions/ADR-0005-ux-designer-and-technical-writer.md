# ADR-0005: Add a UX Designer and a Technical Writer to the team

## Status

Proposed

| Field | Value |
| --- | --- |
| Date proposed | 2026-10-10 |
| Date decided | — |
| Decided by | Repository owner, by merging the Pull Request that introduces this ADR |
| Related Issue | #23 (research), #24 (UX Designer), #25 (Technical Writer) |
| Supersedes | None |
| Related ADRs | ADR-0002, ADR-0003, ADR-0004 |

## Context

- Nobody owns the user experience: interfaces are designed implicitly by developers and reviewed only
  for code quality and security. The owner will build native Android apps in Kotlin, so web-only
  guidance is not enough.
- The UI UX Pro Max skill (aitmpl, `davila7/claude-code-templates`, MIT) offers a useful, prioritised
  and checkable rule catalogue with a standard-library search, but no Android or Compose rules and no
  design process (research #23).
- Developers update the documentation of their own change, but nobody owns the project README or a
  coherent, professionally structured `docs/`.
- Every role added to the team costs usage; both roles must be conditional and skip work that does not
  need them.

## Decision

**UX Designer** (`ux-designer`, label `agent:ux`, level R2, Sonnet at high effort):

- Conditional state `ux-design`: for features that change a user-facing interface, after product
  definition or research and before architecture or planning. Output: a UX specification comment on the
  feature Issue (`templates/ux-spec.md`) with flows, screens, states, tokens, accessibility criteria and
  numbered `UX-AC-n` items that the Planner copies into tasks.
- Conditional state `ux-review`: for Pull Requests that change interface files, after QA `PASS`, in
  parallel with code and security review. Output: a review (`templates/ux-review.md`) with the shared
  severities and outcomes; `changes-requested` when blocking.
- Skill `ux-design`: the team's procedure, a curated copy of the MIT data (with notice and source commit),
  team-written Jetpack Compose and Material 3 rules for Android, and tested scripts (`ux_search.py`,
  `contrast.py`). It writes only comments and reviews, so it adds no new human gate.

**Technical Writer** (`technical-writer`, label `agent:docs`, level R3 limited to `README.md`,
`CHANGELOG.md` and `docs/**`, Sonnet at medium effort):

- Conditional state `documentation`: when the last task Pull Request of a feature is merged, one `docs/`
  Pull Request updates the README and `docs/` (Diátaxis guides and reference, an arc42 and C4
  architecture overview, consolidated UX specifications in `docs/design/`, indexes). It goes through QA
  and reviews like any Pull Request and never changes code or an accepted ADR's decision text.

Pull Request checks accept `agent:reviewer`, `agent:security` and `agent:ux` together during parallel
review; any other combination of agent labels still fails.

## Alternatives

| Alternative | Why not chosen |
| --- | --- |
| Install UI UX Pro Max unchanged | No Android rules, trend-driven style catalogue, its own installation steps; it is a reference, not a process |
| Give UX rules to developers only | Nobody specifies states and accessibility before coding, and nobody independent checks them |
| A UX stage on every feature and Pull Request | Pays for UX on back-end and tooling changes; both stages are conditional instead |
| UX specifications as `docs/` Pull Requests | Adds a human merge gate before planning; comments carry the specification and the Technical Writer consolidates it |
| Documentation inside each task Pull Request only | Keeps local docs current but no project-level structure, index or overview |
| Documentation on demand only | The README and `docs/` drift until someone notices |

## Consequences

**Positive**

- Interfaces are specified and reviewed against concrete, checkable rules, including Android.
- Accessibility becomes a testable acceptance criterion instead of a review afterthought.
- The README and `docs/` follow one professional structure across projects.

**Negative**

- Two more roles to install and maintain; interface Pull Requests get a third parallel review.
- The vendored rule data must be refreshed from its source deliberately.
- Usage rises for features with interfaces and for each finished feature; the usage ledger measures it.

## Security considerations

- The UX Designer writes no files; the Technical Writer writes only `README.md`, `CHANGELOG.md` and
  `docs/**` on `docs/` branches, enforced by the hooks.
- Both publish through the existing redact-before-publishing checks; specifications and docs never
  contain real personal data or screenshots with it.
- Vendored data is plain CSV, checked by the secret scanners like every file.

## Operational considerations

- Re-install `~/.claude/agents/`, `~/.claude/skills/` and `~/.claude/hooks/lib.mjs` after each merge.
- Create the labels `agent:ux` and `agent:docs` in existing repositories; template projects get them
  from `bootstrap.sh`.
- Measure both roles with `usage_report.py --by agent` during the pilot and revisit the skip rules if the
  cost outweighs the findings.
