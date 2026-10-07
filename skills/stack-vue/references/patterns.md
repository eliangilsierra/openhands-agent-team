# Vue and Nuxt patterns: reference

Load this file for store design, data fetching, Nuxt server routes or testing details. It
complements [the stack skill](../SKILL.md).

## Pinia setup store

```ts
export const useCartStore = defineStore("cart", () => {
  const lines = ref<CartLine[]>([]);
  const total = computed(() => lines.value.reduce((sum, l) => sum + l.price * l.quantity, 0));
  function add(line: CartLine) {
    const existing = lines.value.find((l) => l.sku === line.sku);
    if (existing) existing.quantity += line.quantity;
    else lines.value.push(line);
  }
  return { lines, total, add };
});

// In a component: keep reactivity when destructuring
const cart = useCartStore();
const { lines, total } = storeToRefs(cart);
```

## Composable with cleanup and stale-response protection

```ts
export function useSearch(query: Ref<string>) {
  const results = ref<Result[]>([]);
  const error = ref<Error | null>(null);
  watch(query, async (q, _old, onCleanup) => {
    const controller = new AbortController();
    onCleanup(() => controller.abort());
    try {
      results.value = await api.search(q, { signal: controller.signal });
      error.value = null;
    } catch (e) {
      if (!controller.signal.aborted) error.value = e as Error;
    }
  }, { immediate: true });
  return { results, error };
}
```

## Nuxt data fetching

| API | Use |
| --- | --- |
| `useFetch(url, { key })` | Fetch from an API route during SSR and hydrate on the client |
| `useAsyncData(key, fn)` | Any async function; key must be unique and stable |
| `$fetch` | Inside event handlers and server routes; not for SSR-time data in components |
| `refresh()` / `refreshNuxtData(key)` | Re-fetch after a mutation |

- Always provide a key when the same composable fetches different resources.
- `server/api/orders/[id].get.ts` with `defineEventHandler`; validate with
  `getValidatedRouterParams`/`readValidatedBody` and a schema; check the session first.
- `useRuntimeConfig()` exposes `public` to the client only; secrets stay in the private keys.

## Provide and inject

```ts
export const ThemeKey: InjectionKey<Ref<Theme>> = Symbol("theme");
provide(ThemeKey, theme);
const theme = inject(ThemeKey); // typed; handle undefined if optional
```

## Testing recipes

| Need | Recipe |
| --- | --- |
| Mount with stores | `mount(Comp, { global: { plugins: [createTestingPinia({ stubActions: false })] } })` |
| Router | `createRouter({ history: createMemoryHistory(), routes })`, `await router.isReady()` |
| Async UI | `await flushPromises()` then assert |
| Emitted events | `expect(wrapper.emitted("select")?.[0]).toEqual([item])` |
| Nuxt | `@nuxt/test-utils` with `mountSuspended` |

## Common review findings

| Finding | Typical severity |
| --- | --- |
| `const { count } = reactive(...)` or store destructure without `storeToRefs` | MEDIUM (silent bug) |
| `v-html` with user content | BLOCKER |
| Mutating a prop | MEDIUM |
| Watcher fetching without cancellation | LOW to MEDIUM |
| Private runtime config used in a component | HIGH |
