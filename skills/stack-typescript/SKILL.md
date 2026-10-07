---
name: stack-typescript
description: Senior TypeScript and Node.js engineering for the Developer role - strict typing, module and package hygiene, async correctness, error handling, Express/Fastify/NestJS services, and Vitest/Jest/node:test testing. Preloaded by developer-typescript (and by the React, Angular and Vue specialists for the language layer); loaded by QA and reviewers for TypeScript or JavaScript changes.
---

# Stack: TypeScript and Node.js

## Purpose

Write TypeScript and JavaScript the way a senior engineer of the stack would: types that make
invalid states unrepresentable, explicit async and error flows, small modules with clear
boundaries, and tests that pin behaviour rather than implementation. This skill adds stack
knowledge on top of the [development](../development/SKILL.md) procedure; it never replaces it.

## When to use

- The task's module has stack `node`, `typescript` or `javascript` in the stack profile.
- A React, Angular or Vue task needs language-level guidance (types, async, modules).
- QA or a reviewer checks a Pull Request that changes `.ts`, `.tsx`, `.js`, `.mjs` or `.cjs` files.

## Inputs

- The module entry of `.agent-state/stack-profile.json`: package manager, Node and TypeScript
  versions, test runner, linters and the exact commands.
- `tsconfig*.json` (strictness flags, `module`/`moduleResolution`, path aliases), `package.json`
  (`type`, `exports`, `engines`), ESLint/Biome/Prettier configuration.
- Existing code around the change: error types, logger, validation library, configuration loader.
- Deep reference: [references/node-services.md](references/node-services.md).

## Procedure

1. **Read the toolchain.** Note `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`,
   the module system (`"type": "module"` or CommonJS) and the Node version. Write code that compiles
   under the existing flags; never loosen them.
2. **Find the seams.** Run `repo_map.py --focus "<touched globs>"` and read the modules you will
   change, their callers (`grep` the exported names) and their tests.
3. **Model the data first.** Define or extend types at the boundary: discriminated unions for
   variants, `readonly` for values that must not change, branded types for identifiers that must
   not be mixed. Parse untrusted input once at the edge with the project's validator (zod, valibot,
   class-validator, TypeBox) and pass typed values inward.
4. **Implement.** Keep functions small and pure where possible; isolate I/O behind the existing
   service or repository abstractions. Propagate errors with the project's error types; never
   swallow them. Await or return every promise.
5. **Test.** Use the project's runner (Vitest, Jest, `node:test`, Mocha). Unit tests for logic,
   integration tests through the HTTP layer (supertest, Fastify `inject`, Nest testing module) when
   a route changes. Test failure paths and boundaries, not only the happy path. Use fake timers for
   time, not sleeps.
6. **Validate.** `run_checks.py` with the profile: lint, type check (`tsc --noEmit` or the project
   script), tests, build. A type error is a failure even when tests pass.
7. **Self-review** with the quality checklist below, then `diff_guard.py`.

## Rules

- Never use `any` to make code compile. Use `unknown` and narrow it, generics, or a precise type.
  `as` casts need a comment explaining why the compiler cannot know; `!` non-null assertions only
  after a check the compiler cannot follow.
- Never disable a lint rule or add `@ts-ignore`; `@ts-expect-error` only with a reason and only in
  tests that assert a type error.
- No floating promises: every promise is awaited, returned, or explicitly handled with `.catch`.
  Never mix callbacks and promises in one API; never `async` inside `Array.forEach`.
- Errors are `Error` subclasses with a cause (`new AppError("...", { cause })`); never throw strings
  or plain objects. Do not log and rethrow the same error at every layer.
- Validate all external input (HTTP bodies, query strings, environment variables, messages, files)
  at the boundary. Configuration is read once, validated, and typed.
- No new dependency for something the standard library or an existing dependency does (`fetch`,
  `crypto.randomUUID`, `structuredClone`, `node:test`, `AbortController`). New dependencies go
  through `deps_check.py`.
- Respect the module system: ESM imports with file extensions where the project requires them; no
  `require` in ESM packages; no default exports if the codebase uses named exports.
- Use the existing logger with structured fields; no `console.log` in production code.
- Avoid shared mutable module state; it breaks tests and concurrency.

## Required outputs

- Code that passes the project's type check, lint and tests with the existing strictness.
- Tests at the level the task requires, including error paths.
- A Pull Request note listing any new type, public export or configuration variable.

## Quality checklist

- [ ] No `any`, `@ts-ignore`, disabled lint rule or loosened `tsconfig` flag in the diff.
- [ ] Every promise is awaited or returned; no `async` callbacks inside `forEach`.
- [ ] External input is validated at the boundary with the project's validator.
- [ ] Errors are typed, carry a cause, and are handled once.
- [ ] Public types and exports are intentional and documented where the project documents them.
- [ ] Tests cover success, failure and boundary cases; no real network or clock in unit tests.
- [ ] Type check, lint, tests and build pass with the commands from the profile.

## Failure conditions

- The project's type check fails on `main` before your change → report `BLOCKED` with the output;
  do not fix unrelated type errors inside the task.
- The task needs a new runtime dependency the plan did not foresee → run `deps_check.py`, propose it
  in the Pull Request, and continue only if the task allows new dependencies.
- The module system or build setup blocks the change (for example a CommonJS package that must import
  an ESM-only library) → stop and escalate to `agent:architect` with the options.

## Examples

**Typed boundary with zod and an exhaustive union:**

```ts
const CreateOrder = z.object({
  customerId: z.string().uuid(),
  lines: z.array(z.object({ sku: z.string().min(1), quantity: z.number().int().positive() })).min(1),
});
type CreateOrder = z.infer<typeof CreateOrder>;

type PaymentResult =
  | { status: "captured"; transactionId: string }
  | { status: "declined"; reason: "insufficient_funds" | "fraud" }
  | { status: "error"; retryable: boolean };

function toHttp(result: PaymentResult): number {
  switch (result.status) {
    case "captured": return 201;
    case "declined": return 402;
    case "error": return result.retryable ? 503 : 500;
    default: { const never: never = result; throw new Error(`unhandled ${String(never)}`); }
  }
}
```

**Test with fake timers instead of sleeping:**

```ts
it("expires the session after 15 minutes", () => {
  vi.useFakeTimers();
  const session = createSession();
  vi.advanceTimersByTime(15 * 60 * 1000);
  expect(session.isExpired()).toBe(true);
});
```
