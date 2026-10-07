---
name: stack-react
description: Senior React and React Native engineering for the Developer role - component and hook design, state and server-state management, effects discipline, accessibility, rendering performance and Testing Library tests. Preloaded by developer-react and developer-nextjs; loaded by QA and reviewers for React changes.
---

# Stack: React

## Purpose

Build React user interfaces that are correct under re-rendering, accessible by default, and easy
to change: components with one responsibility, state kept where it belongs, effects only for
synchronising with the outside world, and tests written from the user's point of view. Adds stack
knowledge to the [development](../development/SKILL.md) procedure.

## When to use

- The task's module has stack `react` or `react-native` in the stack profile (Next.js modules also
  load [stack-nextjs](../stack-nextjs/SKILL.md)).
- QA or a reviewer checks a Pull Request that changes `.tsx`/`.jsx` components or hooks.

## Inputs

- The module entry of the stack profile: React version, bundler (Vite, Next, Expo, Metro), test
  runner, linters, commands.
- The project's choices for state (local state, Context, Zustand, Redux Toolkit), server state
  (TanStack Query, SWR, RTK Query, Apollo), forms (React Hook Form, Formik), styling and routing.
- The design system or component library in use; existing components to reuse.
- Deep reference: [references/patterns.md](references/patterns.md).

## Procedure

1. **Read the version and conventions.** React 19 adds Actions (`useActionState`, `useOptimistic`,
   `<form action>`), `use()`, and `ref` as a prop; React 18 code uses `forwardRef`. Follow what the
   project's version supports and what its code already does.
2. **Reuse before you build.** Search the design system and `components/` for an existing component
   or hook. A new component that duplicates an existing one is a review finding.
3. **Place the state.** Decide for each piece of data: server state (query library cache), URL state
   (route params, search params), form state (form library), shared client state (store or
   Context), or local state. Derive values during render instead of storing copies.
4. **Implement components.** Props typed explicitly; keys stable and unique (never array indexes for
   reorderable lists); event handlers for user-caused changes; effects only to synchronise with
   external systems, each with a cleanup.
5. **Accessibility.** Semantic elements first (`button`, `label`, `nav`, headings in order), an
   accessible name for every control, keyboard operability, focus management for dialogs, and no
   information conveyed by colour alone. React Native: `accessibilityLabel`/`accessibilityRole`.
6. **Test.** Testing Library queries by role and name (`getByRole("button", { name: /save/i })`),
   `userEvent` for interaction, `findBy*` for async UI, MSW or the project's mocks for network.
   Test what the user sees, not internal state or implementation details.
7. **Validate** with `run_checks.py` (lint, type check, tests, build) and self-review with the
   checklist.

## Rules

- Never call hooks conditionally or in loops; respect `react-hooks/rules-of-hooks` and
  `exhaustive-deps` (fix the dependency, do not silence the rule).
- Do not use `useEffect` to derive state from props or state, to handle user events, or to fetch
  data when the project has a server-state library or a framework data API.
- Do not mutate state or props; produce new objects and arrays.
- No `dangerouslySetInnerHTML` with content that is not sanitised by the project's sanitiser.
- Memoisation (`useMemo`, `useCallback`, `React.memo`) only for a measured problem or a referential
  dependency that requires it; with the React Compiler enabled, do not add manual memoisation.
- Keep components presentational where possible; data access lives in hooks or the framework's
  data layer.
- Every list item has a stable `key`; every image has `alt` (empty for decorative ones).
- No inline object or array literals passed to memoised children or context providers on hot
  paths without need.

## Required outputs

- Components and hooks that follow the project's structure, styling and naming.
- Testing Library tests for each acceptance criterion visible in the UI, including loading, empty
  and error states.
- Pull Request note with screenshots or a description of the visible change when the task is UI.

## Quality checklist

- [ ] Each piece of state lives in exactly one place; nothing derivable is stored.
- [ ] No effect handles a user event or derives state; every effect has a cleanup when needed.
- [ ] Hook rules and exhaustive dependencies hold without disabled lint rules.
- [ ] Keys are stable; no array-index keys on dynamic lists.
- [ ] Controls have accessible names and are keyboard operable; dialogs manage focus.
- [ ] Loading, empty and error states exist and are tested.
- [ ] Tests query by role, label or text, not by class names or test ids unless no role exists.

## Failure conditions

- The design or copy for a visible state is missing from the task → implement the minimal
  accessible version, document the interpretation in the Pull Request; if it changes behaviour,
  ask on the Issue and add `blocked`.
- The required state library or data layer conflicts with the architecture → escalate to
  `agent:architect`.
- Tests depend on a browser feature jsdom lacks (layout, canvas) → test the logic separately and
  mark the visual check for QA's E2E run, explaining it in the Pull Request.

## Examples

**Derive instead of syncing state with an effect:**

```tsx
// Before: extra render and stale data risk
const [visible, setVisible] = useState<Task[]>([]);
useEffect(() => setVisible(tasks.filter((t) => !t.done)), [tasks]);

// After: derived during render
const visible = tasks.filter((t) => !t.done);
```

**User-centred test:**

```tsx
it("disables Save until the title is filled", async () => {
  const user = userEvent.setup();
  render(<TaskForm onSave={vi.fn()} />);
  const save = screen.getByRole("button", { name: /save/i });
  expect(save).toBeDisabled();
  await user.type(screen.getByLabelText(/title/i), "Write report");
  expect(save).toBeEnabled();
});
```
