---
name: stack-vue
description: Senior Vue engineering for the Developer role - Composition API with script setup, typed props and emits, reactivity pitfalls, composables, Pinia stores, Vue Router and Nuxt data fetching, and Vitest with Vue Test Utils or Testing Library. Preloaded by developer-vue together with stack-typescript; loaded by QA and reviewers for Vue and Nuxt changes.
---

# Stack: Vue and Nuxt

## Purpose

Deliver Vue features with predictable reactivity, typed component contracts, logic extracted into
composables, and shared state in Pinia, following the project's version and Nuxt conventions when
Nuxt is used. Adds framework knowledge to the [development](../development/SKILL.md) procedure.

## When to use

- The task's module has stack `vue` in the stack profile (Vue or Nuxt).
- QA or a reviewer checks a Pull Request that changes `.vue` files, composables, stores or Nuxt
  server routes.

## Inputs

- Vue and Nuxt versions from the stack profile. Vue 3.4 adds `defineModel`; 3.5 adds reactive props
  destructure and `useTemplateRef`. Vue 2 code (Options API, `Vue.extend`) follows its own rules:
  keep the area's style.
- Pinia stores, router configuration, the UI library, i18n setup, `nuxt.config.*`.
- Deep reference: [references/patterns.md](references/patterns.md).

## Procedure

1. **Follow the area's API style.** New components use `<script setup lang="ts">` unless the
   touched area is Options API and the task is not a migration.
2. **Contracts.** `defineProps<{...}>()` with types and defaults, `defineEmits<{...}>()` with typed
   payloads, `defineModel()` for two-way bindings. Props are read-only.
3. **Reactivity.** `ref` for primitives and replaced values, `reactive` only for objects you never
   replace or destructure, `computed` for derived values, `watch` with explicit sources for side
   effects, `watchEffect` sparingly. Use `toRefs`/`storeToRefs` when destructuring.
4. **Composables.** Extract reusable logic into `useXxx()` functions returning refs and functions;
   clean up listeners in `onScopeDispose`/`onUnmounted`.
5. **State and data.** Shared state in a Pinia setup store; server data through the project's
   fetching approach (Nuxt `useFetch`/`useAsyncData` with keys, TanStack Vue Query, or a service
   layer). Handle pending and error states.
6. **Nuxt specifics.** Server routes in `server/api` validate input (`readValidatedBody` with a
   schema) and authorise; runtime configuration through `useRuntimeConfig`, with secrets only in
   the private part.
7. **Test.** Vitest with `@vue/test-utils` (`mount`, `await wrapper.setProps`, `flushPromises`) or
   `@testing-library/vue`; `createTestingPinia` for stores; `@nuxt/test-utils` for Nuxt.
8. **Validate.** `run_checks.py`: lint (ESLint with `eslint-plugin-vue`), `vue-tsc --noEmit` (or the
   project's type check), tests, build.

## Rules

- Never destructure a `reactive` object or a store without `toRefs`/`storeToRefs`; you lose
  reactivity.
- Never mutate props; emit an event or use `defineModel`.
- `v-if` and `v-for` never on the same element; every `v-for` has a stable `:key`.
- No `v-html` with unsanitised content.
- Do not put business logic in templates; use `computed`.
- Watchers that fetch data cancel or ignore stale responses (`onCleanup` / abort controller).
- No global event bus; use props, emits, provide/inject with typed keys, or a store.
- In Nuxt, never expose private runtime config to the client and never call internal server routes
  with absolute URLs from the server side when a direct function call exists.

## Required outputs

- Components with typed props and emits, composables for reusable logic, stores for shared state.
- Tests for rendered behaviour, emitted events and store actions.
- A passing type check with `vue-tsc` (or the project's equivalent) and build.

## Quality checklist

- [ ] No lost reactivity (destructured reactive objects or stores without `toRefs`/`storeToRefs`).
- [ ] Props are never mutated; two-way bindings use `defineModel` or `update:` events.
- [ ] Every `v-for` has a stable key; no `v-if` with `v-for` on one element.
- [ ] Side effects clean up; data watchers handle stale responses.
- [ ] Pending and error states are rendered and tested.
- [ ] Type check, lint, tests and build pass.

## Failure conditions

- The change requires Vue 2 to 3 or Nuxt major migration work → stop; propose a separate task.
- The project has no type check for `.vue` files and the task depends on types → note it in the
  Pull Request and rely on tests; do not add tooling without the plan.
- SSR hydration mismatches appear → isolate client-only parts (`<ClientOnly>`, `onMounted`) and
  document the cause in the Pull Request.

## Examples

**Typed component with `defineModel` and a composable:**

```vue
<script setup lang="ts">
const props = withDefaults(defineProps<{ items: Item[]; pageSize?: number }>(), { pageSize: 20 });
const page = defineModel<number>("page", { required: true });
const emit = defineEmits<{ select: [item: Item] }>();
const { visible, pageCount } = usePagination(() => props.items, () => props.pageSize, page);
</script>

<template>
  <ul>
    <li v-for="item in visible" :key="item.id">
      <button type="button" @click="emit('select', item)">{{ item.name }}</button>
    </li>
  </ul>
  <p>Page {{ page }} of {{ pageCount }}</p>
</template>
```
