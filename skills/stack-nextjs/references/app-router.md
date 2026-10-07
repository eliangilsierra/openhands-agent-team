# Next.js App Router: reference

Load this file for routing, data, caching, authentication or deployment questions. It complements
[the stack skill](../SKILL.md). Behaviour differs between major versions: confirm against the
version in the stack profile and the official documentation for that version.

## File conventions

| File | Role |
| --- | --- |
| `layout.tsx` | Shared UI that persists across navigation; receives `children` |
| `page.tsx` | The route's UI; receives `params` and `searchParams` |
| `loading.tsx` | Suspense fallback for the segment |
| `error.tsx` | Error boundary for the segment (must be a Client Component); `global-error.tsx` for the root |
| `not-found.tsx` | UI for `notFound()` |
| `route.ts` | Route handler (`GET`, `POST`, ...) returning `Response` |
| `template.tsx` | Like layout but re-mounted on navigation |
| `(group)/` | Route group, not part of the URL |
| `[id]/`, `[...slug]/`, `[[...slug]]/` | Dynamic segments |
| `@slot/` | Parallel routes; `(.)segment` intercepting routes |
| `middleware.ts` (renamed `proxy.ts` in Next.js 16) | Runs before routing; keep it light |

## Data and caching checklist

1. Where does the data come from (database, internal API, third party)?
2. Is it per user? Then it is dynamic or cached per user key, never shared.
3. How fresh must it be? Static, time-based revalidation, or tag revalidation after mutations.
4. Which mutation invalidates it? Name the `revalidateTag`/`revalidatePath` call.
5. Does the page become dynamic because it reads `cookies()`/`headers()`/`searchParams`? That is
   fine when intended; state it.

- Deduplicate repeated reads in one request with React `cache()` around the data function.
- `unstable_cache`, the `use cache` directive and cache components are version-dependent opt-ins;
  use only what the project already enabled.
- `generateStaticParams` pre-renders known dynamic segments; combine with `dynamicParams` to decide
  what happens for unknown ones.

## Authentication and authorisation

- Check the session in the data layer or a `requireUser()` helper used by pages, actions and route
  handlers alike. Middleware/proxy checks are an optimisation, not the security boundary.
- Server actions are reachable with a crafted POST: validate and authorise inside each action.
- Return only the fields the client needs from Server Components to Client Components; props are
  serialised into the page.

## Route handlers

- Validate the body (`await request.json()` then schema parse), return `Response.json(data, { status })`.
- Set caching headers deliberately for `GET` handlers.
- For webhooks: verify the signature with the raw body before parsing; respond quickly and defer work.

## Performance

- Stream slow sections with `Suspense`; keep the shell fast.
- Keep Client Components small; large libraries used only on the server stay out of the bundle.
- Use `next/dynamic` for heavy client-only widgets.
- Images: correct `sizes`, priority only for the largest above-the-fold image.

## Testing

| Layer | Approach |
| --- | --- |
| Client Components | Testing Library + Vitest/Jest with `next/navigation` mocked through the project's helper |
| Server actions | Call the function; fake the data layer and `requireUser`; assert revalidation calls |
| Route handlers | Build a `Request`, call the exported handler, assert the `Response` |
| Full flows | Playwright against `next build && next start` if the project has an E2E suite |

## Common review findings

| Finding | Severity guide |
| --- | --- |
| Server action without authorisation check | BLOCKER or HIGH (security) |
| Per-user data in a shared cache | HIGH |
| `"use client"` on a layout to make a hook work | MEDIUM |
| Fetching own route handler from a Server Component | LOW |
| Missing `loading.tsx`/`error.tsx` for a slow or failing route | MEDIUM |
