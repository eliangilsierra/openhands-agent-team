# ADR-0003: Run the Developer role as stack specialists chosen by the coordinator

## Status

Accepted

| Field | Value |
| --- | --- |
| Date proposed | 2026-10-07 |
| Date decided | 2026-10-07 |
| Decided by | Repository owner, by merging the Pull Request that introduces this ADR (#12) |
| Related Issue | #11 |
| Supersedes | None. Extends [ADR-0002](ADR-0002-single-session-subagent-team.md) |
| Related ADRs | ADR-0001, ADR-0002 |

## Context

- The Developer role (ADR-0002) is one generic subagent that preloads only `development` and
  `testing`. Stack knowledge (Spring Boot transactions, Angular change detection, Compose state,
  Next.js caching, ...) depends on what the model recalls, so quality varies between stacks and
  between runs.
- The same subagent rebuilds the same routine by hand on every task: finding the project's
  commands, taking a baseline, mapping the code, reviewing its own diff, writing the checkpoint and
  the Pull Request body. That costs turns and tokens and produces inconsistent evidence.
- Claude Code subagents can each preload different skills and keep their own memory; skills follow
  the Agent Skills layout, where `references/` and `scripts/` are loaded only when needed
  (progressive disclosure). Specialist catalogues of this kind are common practice in the Claude
  Code ecosystem (October 2026).
- Claude Code allows nested subagents up to a depth limit, but background subagents do not receive
  the `Agent` tool, the hooks enforce restriction levels by subagent name (`agent_type`), and
  AGENTS.md section 16 says only the coordinator schedules work. The team sets
  `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1`.

## Decision

We will run the Developer role as **one of eleven subagents**: the generalist `developer` and ten
stack specialists (`developer-typescript`, `developer-react`, `developer-nextjs`,
`developer-angular`, `developer-vue`, `developer-java-spring`, `developer-kotlin-android`,
`developer-python`, `developer-go`, `developer-dotnet`).

- **Variants, not roles.** Specialists inherit the Developer's label, workflow states, permissions,
  restriction level (R4), runtime limits and Definition of Done. They differ only in the stack skills
  they preload and in their memory. The catalogue is `config/specialists.yaml`.
- **Flat routing by the coordinator.** The coordinator profiles the repository with
  `detect_stack.py` and chooses the specialist per task with `select_specialist.py` from the task's
  `Touches:` and `Stack:` lines. The developer never spawns subagents; nesting stays disabled.
- **One task, one stack.** The Planner splits slices that span several stacks; a task that cannot be
  split goes to the generalist with every stack skill involved.
- **Stack skills** `skills/stack-<x>/` hold senior conventions, anti-patterns, testing approach and
  commands, with deeper `references/` loaded on demand. QA and reviewers load the same skills for the
  stacks a Pull Request touches.
- **Helper scripts** (Python 3.10+, standard library only, unit-tested) in
  `skills/development/scripts/` and `skills/stack-routing/scripts/` make the routine deterministic:
  `run_checks.py`, `repo_map.py`, `impact_scan.py`, `diff_guard.py`, `checkpoint.py`, `pr_body.py`,
  `deps_check.py`, `detect_stack.py`, `select_specialist.py`.
- **Generated runtime.** `scripts/generate_runtime.py` generates every subagent file, the runtime
  copy of the catalogue and the specialist entries of the hooks' level table from `config/`; the
  validator fails when they drift.
- Developer parallelism rises from 2 to 3 across all specialists; the global limit of 4 subagents
  stays.

## Alternatives

| Alternative | Why not chosen |
| --- | --- |
| Keep one developer and load stack skills on demand only | Relies on the model choosing to load the right skill; no per-stack memory; the generalist remains for this case |
| The developer spawns stack subagents itself | Background subagents have no `Agent` tool; nested agents escape the coordinator's board, budgets and parallelism rules; contradicts AGENTS.md section 16 |
| One specialist per framework version or per library (dozens of agents) | Catalogue too large to route and maintain; versions are handled inside each stack skill |
| Install a third-party agent collection | Prompts do not follow this team's contract, result format or permissions; licensing and maintenance outside our control |
| Route with the model's judgement instead of scripts | Non-deterministic and not reviewable; the scripts give the same answer for the same inputs |

## Consequences

**Positive**

- Each task is implemented with the conventions of its stack, and QA and reviewers check it against
  the same conventions.
- Evidence (baseline, checks, regressions, Pull Request body) has one format across stacks.
- Specialist memories accumulate stack lessons separately instead of mixing them.
- Adding a stack is a catalogue entry, a skill and a regeneration, checked by the validator.

**Negative**

- More runtime files to install (eleven developer subagents, eleven new skills).
- The quality of routing depends on accurate `Touches:` lines from the Planner.
- Repositories with stacks outside the catalogue fall back to the generalist.
- Stack skills must be kept current as frameworks evolve; they are reviewed like any other change.

## Security considerations

- Specialists have exactly the Developer's permissions; the hooks list them by name, so an unknown
  `developer-*` subagent is read-only (R1).
- The scripts read manifests and git data only and never execute project code; `run_checks.py` runs
  only commands derived from the project's manifests or given explicitly, and redacts token patterns
  in its output.
- `diff_guard.py` blocks secrets, secret-bearing files, weakened tests and out-of-scope files before
  a push; it complements, not replaces, the git hooks and the Security Reviewer.
- `deps_check.py` sends only a package name and version to public APIs (deps.dev, OSV.dev).

## Operational considerations

- Re-install `~/.claude/agents/`, `~/.claude/skills/` and `~/.claude/hooks/lib.mjs` in the runtime
  after merge (docs/subagents.md section 10). The runtime needs Python 3.10+ on `PATH`.
- `.agent-state/stack-profile.json` is runtime state, refreshed after merges that change build files.
- Optional extras (LSP code-intelligence plugins, a documentation lookup service) are documented and
  off by default; enabling them is a separate human decision.
