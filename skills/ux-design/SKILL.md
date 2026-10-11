---
name: ux-design
description: Design and review user interfaces for web and native Android (Kotlin, Jetpack Compose, Material 3) - turn requirements into a UX specification (flows, screens, components, states, design tokens, accessibility criteria) and review interface Pull Requests against prioritised, checkable rules with WCAG 2.2 contrast checks. Preloaded by ux-designer; read by the planner, developers, QA and reviewers for interface work.
---

# UX Design

## Purpose

Make every user-facing change usable, accessible and consistent before and after it is built: a UX
specification gives the Planner and developers concrete screens, states and acceptance criteria, and a
UX review checks the implementation against the same rules. Accessibility and interaction come first;
visual style serves the product, not trends.

## When to use

- **UX specification** (state `ux-design`): a feature changes or adds a user-facing interface (web
  pages, components, Android screens). Skip it when the feature has no interface change.
- **UX review** (state `ux-review`): a Pull Request changes interface files (components, screens,
  styles, layouts, strings, navigation) and QA passed. It runs in parallel with code and security
  review. Skip it when no interface file changed.
- Developers, QA and reviewers read the specification and run the checklist for their stack.

## Inputs

- The feature Issue: requirements, users, acceptance criteria, constraints.
- The stack profile (`.agent-state/stack-profile.json`): which modules are web (react, nextjs, vue,
  angular) or Android (`android`, `kotlin` with Compose).
- Existing UI: design system or theme files (Material theme, Tailwind config, tokens), components,
  screenshots or previews when available.
- Data and scripts in this skill (in the runtime: `$HOME/.claude/skills/ux-design/`):
  - `data/`: prioritised UX rules, web interface rules, charts, palettes, typography and stack rules
    (react, nextjs, vue, nuxtjs, react-native, html-tailwind, shadcn and the team's jetpack-compose
    for Android). Source and licence: [data/NOTICE.md](data/NOTICE.md).
  - `scripts/ux_search.py`: ranked rule search and checklists by platform or stack.
  - `scripts/contrast.py`: WCAG 2.2 contrast for text, large text and UI components.
- Deep reference for Android: [references/android-compose.md](references/android-compose.md).

## Procedure

### A. UX specification (`ux-design`)

1. **Understand the job.** From the requirements, list the users, their goal and the context (device,
   connectivity, frequency). Note what success looks like for each acceptance criterion.
2. **Choose the platform rules.** Web: `ux_search.py --checklist --platform web` plus
   `--stack <react|nextjs|vue|...>`. Android: `ux_search.py --checklist --platform android` (general
   mobile rules and Jetpack Compose). Keep the Critical and High rules that apply.
3. **Flows.** Describe each flow as numbered steps or a Mermaid `flowchart`: entry point, decisions,
   success, cancel and error paths, back navigation.
4. **Screens and states.** For every screen: purpose, layout regions, components (reuse the design
   system first; Material 3 components on Android), content priority, and the **loading, empty, error,
   partial and success** states. Android: phone and large-screen layout, edge-to-edge and keyboard.
5. **Design tokens.** Reuse the existing theme. When there is none, propose a minimal token set (color
   roles, type scale, spacing on a 4dp/4px grid, radius, elevation) and check every text and component
   color pair with `contrast.py` (text AA 4.5:1, large text and UI 3:1).
6. **Accessibility criteria.** Write them as testable criteria: names and roles for controls, focus or
   TalkBack order, touch targets (48dp Android, 44px web), text scaling, contrast, no color-only meaning,
   reduced motion.
7. **Copy.** Labels, errors and empty-state messages in plain language, ready for string resources.
8. **Publish.** Post the specification with [templates/ux-spec.md](../../templates/ux-spec.md) as a
   comment on the feature Issue (header `**UX specification** · UX Designer · state: ux-design`). List
   the UX acceptance criteria (`UX-AC-n`) the Planner must copy into the tasks. Hand off to
   `agent:architect` or `agent:planner` as the workflow says.

### B. UX review (`ux-review`)

1. Read the task, the UX specification and `gh pr diff`; list the changed screens and components.
2. Run the checklist for the changed stack (`--stack jetpack-compose`, `--stack react`, ...) and check
   every Critical and High rule against the diff; search for specific concerns with `ux_search.py
   "<query>"`.
3. Check every new or changed color pair with `contrast.py`; check the states the specification
   requires, copy, touch targets, semantics and responsive or adaptive behaviour.
4. Run the app or previews when the sandbox allows it (web dev server, Compose previews or screenshot
   tests); otherwise review from code and say so.
5. Submit one review with [templates/ux-review.md](../../templates/ux-review.md) through
   `gh pr review --comment`. Every finding has Severity, Location, Problem, Evidence (rule id or
   contrast ratio), Impact and Recommendation. Outcome `CHANGES REQUESTED` adds `changes-requested`.

## Rules

- Accessibility and touch interaction are never traded for style. A failing contrast ratio, a missing
  accessible name or a touch target under the platform minimum is at least `HIGH`.
- Reuse the project's design system and platform components before proposing new ones; propose tokens
  only when none exist.
- Android follows Material 3 and the Android accessibility guidance; web follows WCAG 2.2 AA. Do not
  port iOS or web patterns to Android (for example hamburger-only navigation or custom back buttons).
- Every async screen specifies loading, empty and error states, and every destructive action a
  confirmation or undo.
- Specifications describe behaviour and structure, not pixel-perfect mockups; never invent brand assets,
  real user data or copy that legal or marketing must approve.
- UX artefacts are comments and reviews; never edit code or commit files. Never `APPROVE`.
- Redact before publishing: no real emails, names or screenshots with personal data.

## Required outputs

- `ux-design`: one UX specification comment on the feature Issue with flows, screens, states, tokens,
  accessibility criteria and `UX-AC-n` items.
- `ux-review`: one Pull Request review with findings and an outcome (`CHANGES REQUESTED`,
  `NO BLOCKING FINDINGS` or `BLOCKED`).

## Quality checklist

- [ ] Every screen lists its loading, empty, error and success states.
- [ ] Every interactive element has an accessible name, role and a platform-sized touch target.
- [ ] Every text and component color pair was checked with `contrast.py` and the ratios are reported.
- [ ] The Critical and High rules of the platform checklist were applied or marked not applicable.
- [ ] Android specifications cover edge-to-edge, keyboard, back navigation, font scaling and large screens.
- [ ] UX acceptance criteria are testable and numbered `UX-AC-n`.

## Failure conditions

- Requirements do not say who uses the interface or what success means → comment the question, hand
  back to `agent:product`, add `blocked`.
- The design needs a new design system, brand or platform decision → recommend an ADR and hand off to
  `agent:architect`.
- The app cannot run in the sandbox → review from code and previews, report the runtime checks as
  `BLOCKED` with the error, and do not claim visual verification.

## Examples

**UX acceptance criteria (Android order list):**

```text
UX-AC-1: Each order row is one TalkBack stop announcing number, status and date, with a 48dp min height.
UX-AC-2: Loading shows a progress indicator; empty shows "No orders yet" with a "Create order" action;
         errors show the message and a Retry button.
UX-AC-3: Status chips use text plus color; status text contrast is at least 4.5:1 in light and dark theme.
UX-AC-4: The list keeps its scroll position and filter after rotation (rememberSaveable).
```

**Contrast finding in a review:**

```text
Severity: HIGH · Location: ui/order/OrderRow.kt:42 · Problem: secondary text #9E9E9E on #FFFFFF
Evidence: contrast.py 2.68:1 (text AA requires 4.5:1) · Impact: unreadable for low-vision users
Recommendation: use MaterialTheme.colorScheme.onSurfaceVariant (5.6:1 on surface in the theme)
```
