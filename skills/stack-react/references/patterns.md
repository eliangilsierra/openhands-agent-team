# React patterns: reference

Load this file for non-trivial state, data fetching, forms, performance or React Native work. It
complements [the stack skill](../SKILL.md).

## Where state lives

| Data | Home | Notes |
| --- | --- | --- |
| Data owned by the server | TanStack Query / SWR / RTK Query / Apollo cache | Query keys include every parameter; invalidate after mutations |
| Filters, pagination, selected tab | URL search params | Shareable and survives reload |
| Form fields and validation | React Hook Form (or the project's form library) with the schema validator | Avoid one `useState` per field in large forms |
| Cross-cutting client state (theme, auth session, cart) | Context with a small API, or the project's store | Split contexts so updates do not re-render everything |
| UI-only state (open, hovered, step) | `useState` / `useReducer` in the component | Lift only as far as needed |

## Effects: the decision table

| You want to | Use |
| --- | --- |
| Compute something from props or state | A variable during render (`useMemo` if expensive and measured) |
| React to a click or submit | The event handler |
| Reset state when a prop changes | A `key` on the component |
| Fetch data | The data library or framework loader, not a bare effect |
| Subscribe to an external store | `useSyncExternalStore` |
| Synchronise with a non-React widget, timer or socket | `useEffect` with cleanup |

## React 19 forms and actions

```tsx
function RenameForm({ id }: { id: string }) {
  const [state, action, pending] = useActionState(async (_prev: State, data: FormData) => {
    const result = await rename(id, String(data.get("name")));
    return result.ok ? { error: null } : { error: result.message };
  }, { error: null });
  return (
    <form action={action}>
      <label htmlFor="name">Name</label>
      <input id="name" name="name" required />
      <button disabled={pending}>Save</button>
      {state.error && <p role="alert">{state.error}</p>}
    </form>
  );
}
```

## Performance, when measured

- Profile with React DevTools before optimising; record the finding in the Pull Request.
- Virtualise long lists (`@tanstack/react-virtual` or the project's choice).
- Split code at route level (`lazy` + `Suspense`); avoid splitting tiny components.
- Keep context values stable (`useMemo` on the value object) when consumers are many.
- Move expensive work out of render, or to the server.

## Accessibility patterns

- Dialog: focus the first focusable element on open, trap focus, restore focus on close, close on
  Escape, `aria-modal="true"` and a labelled title. Prefer the design system's dialog.
- Form errors: associate with `aria-describedby`; announce summaries with `role="alert"`.
- Icon-only buttons: `aria-label`.
- Live updates: `aria-live="polite"` regions for asynchronous status messages.

## Testing recipes

| Need | Recipe |
| --- | --- |
| Async data | MSW handlers; assert with `await screen.findByText(...)` |
| Router | Render inside `MemoryRouter` (or the framework's test helper) with the initial entry |
| Query library | A fresh `QueryClient` per test with `retry: false` |
| Hooks alone | `renderHook` from Testing Library |
| React Native | `@testing-library/react-native`, `fireEvent.press`, `screen.getByRole` |

## React Native specifics

- Use `FlatList`/`SectionList` (or FlashList if present) for lists, never `map` inside `ScrollView`
  for long data.
- Platform differences go through `Platform.select` or `.ios.tsx`/`.android.tsx` files, following
  the project's convention.
- Do not block the JS thread with heavy computation; move it to native modules, workers or the
  server.
- Respect safe areas (`react-native-safe-area-context`) and dynamic type sizes.
