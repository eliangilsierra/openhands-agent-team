---
name: stack-nextjs
description: Senior Next.js engineering for the Developer role - App Router layouts and routes, React Server and Client Components, server actions and route handlers, data fetching, caching and revalidation, metadata, runtime choice and testing. Preloaded by developer-nextjs together with stack-react; loaded by QA and reviewers for Next.js changes.
---

# Stack: Next.js

## Purpose

Deliver Next.js features that render in the right place (server or client), fetch and cache data
deliberately, keep secrets on the server, and stay fast. React itself is covered by
[stack-react](../stack-react/SKILL.md); this skill adds the framework layer to the
[development](../development/SKILL.md) procedure.

## When to use

- The task's module has stack `nextjs` in the stack profile.
- QA or a reviewer checks a Pull Request that changes `app/`, `pages/`, `middleware`/`proxy`,
  route handlers, server actions or `next.config.*`.

## Inputs

- The Next.js and React versions from the stack profile, and whether the project uses the App
  Router (`app/`), the Pages Router (`pages/`) or both.
- `next.config.*` (output mode, images, experimental flags such as cache components), the
  deployment target (Node server, standalone container, edge, static export).
- Existing data access layer, authentication helper and validation schemas.
- Deep reference: [references/app-router.md](references/app-router.md).

## Procedure

1. **Identify the router and version.** Never mix App Router patterns into a Pages Router page or
   the reverse. Since Next.js 15, `params`, `searchParams`, `cookies()` and `headers()` are
   asynchronous and `fetch` is not cached by default; check the version before relying on caching
   behaviour, and read `next.config.*` for opt-in caching features.
2. **Decide the rendering boundary.** Components are Server Components by default. Add `"use client"`
   only to the smallest leaf that needs state, effects, browser APIs or event handlers. Pass
   serialisable props across the boundary.
3. **Fetch on the server.** Read data in Server Components or the data layer with the user's
   authorisation checked there. Parallelise independent requests; wrap slow parts in `Suspense`
   with a `loading.tsx` or fallback.
4. **Mutate with server actions or route handlers.** Validate input with the project's schema,
   check authentication and authorisation inside the action (it is a public endpoint), then
   `revalidatePath`/`revalidateTag` (or the project's cache API) for the data that changed.
5. **Handle states.** `loading.tsx`, `error.tsx` (a Client Component), `not-found.tsx` and
   `notFound()`/`redirect()` where the route needs them. Set `metadata` or `generateMetadata`.
6. **Test.** Unit-test Client Components with Testing Library; test server actions and route
   handlers as functions with their dependencies faked; leave full flows to the project's E2E
   suite (Playwright) when it exists.
7. **Validate.** `run_checks.py`: lint (`next lint` or ESLint), type check, tests and
   `next build` (the build catches server/client boundary errors and invalid route exports).

## Rules

- Secrets and server-only modules never reach the client: import `server-only` in modules that
  read secrets or the database; only `NEXT_PUBLIC_*` variables may be used in client code.
- Every server action and route handler authenticates, authorises and validates on its own; never
  trust that the UI hid the button.
- Do not fetch your own route handlers from Server Components; call the data layer directly.
- Do not add `"use client"` to layouts or pages to fix an error; move the interactive part into a
  leaf component.
- Caching is explicit: state in the code (or the Pull Request) why a response is static, revalidated
  on a time window, tagged, or dynamic. Never cache per-user data in a shared cache.
- Use `next/image` with explicit dimensions or `fill` + `sizes`, `next/link` for navigation and
  `next/font` for fonts, unless the project deliberately does otherwise.
- Keep `middleware`/`proxy` logic small and fast (rewrites, redirects, cheap auth checks); no
  database calls there.
- Do not change `next.config.*`, the output mode or the runtime (`edge`/`nodejs`) unless the task
  asks for it.

## Required outputs

- Routes with the loading, error and not-found states the task requires.
- Server actions or route handlers with validation, authorisation and revalidation.
- A successful `next build` in the Pull Request evidence.

## Quality checklist

- [ ] `"use client"` appears only on leaf components that need it.
- [ ] No secret, database client or server-only import is reachable from a Client Component.
- [ ] Each server action and route handler validates input and checks authorisation.
- [ ] Every mutation revalidates exactly the data it changed.
- [ ] Caching of each new fetch or page is deliberate and safe for per-user data.
- [ ] Asynchronous request APIs (`params`, `cookies()`, `headers()`) are awaited on Next.js 15+.
- [ ] `next build` passes; metadata is set for new pages.

## Failure conditions

- The build fails with a server/client boundary error you cannot resolve without restructuring
  shared components → describe it and ask `agent:architect` before moving files across features.
- The task requires changing the deployment runtime or caching model → escalate to
  `agent:architect`.
- The Pages Router and App Router both serve the affected path → stop and ask on the Issue which
  one owns it.

## Examples

**Server Component with a client leaf and a validated server action:**

```tsx
// app/orders/[id]/page.tsx (Server Component)
export default async function OrderPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const order = await getOrderForCurrentUser(id); // authorises inside the data layer
  if (!order) notFound();
  return <OrderView order={order} cancel={<CancelButton orderId={order.id} />} />;
}

// app/orders/[id]/actions.ts
"use server";
const Input = z.object({ orderId: z.string().uuid() });
export async function cancelOrder(raw: unknown) {
  const { orderId } = Input.parse(raw);
  const user = await requireUser();
  await orders.cancel(orderId, user.id); // throws if the user does not own the order
  revalidatePath(`/orders/${orderId}`);
}
```
