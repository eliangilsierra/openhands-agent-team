# Node.js services: reference

Load this file when the task changes an HTTP service, a worker or a library published to a
registry. It complements [the stack skill](../SKILL.md).

## Framework idioms

| Framework | Structure | Validation | Testing an endpoint |
| --- | --- | --- | --- |
| Express | Router per resource, thin handlers, services injected through factories | zod or the project's middleware | `supertest(app).post("/orders").send(body)` |
| Fastify | Plugins with encapsulation, route `schema` for input and output | JSON Schema / TypeBox in the route definition | `await app.inject({ method: "POST", url: "/orders", payload })` |
| NestJS | Module → controller → provider; DTO classes | `class-validator` + global `ValidationPipe` | `Test.createTestingModule` + `supertest(app.getHttpServer())` |

- Express 5 forwards rejected promises from async handlers to the error middleware; on Express 4,
  wrap async handlers or use the project's wrapper. Check the version in the profile.
- One error-handling middleware or filter maps domain errors to status codes; handlers do not build
  error responses by hand.
- Return `404` for missing resources the caller may access, `403` for resources it may not access
  (or `404` when existence itself is sensitive), `409` for state conflicts, `422`/`400` for
  validation errors following the existing convention.

## Async and resources

- Pass an `AbortSignal` through long operations and outbound calls; set timeouts on every
  outbound request (`fetch(url, { signal: AbortSignal.timeout(5000) })`).
- Use `Promise.all` only for independent work that should fail together; use
  `Promise.allSettled` when partial results are acceptable.
- Bound concurrency for fan-out (`p-limit` if already present, or a small queue); never start an
  unbounded number of requests from user input.
- Close what you open: database clients, file handles, intervals. Register shutdown handlers
  (`SIGTERM`) in the existing bootstrap rather than adding new ones.
- Streams: use `pipeline` from `node:stream/promises` so errors propagate and resources close.

## Data and security

- Parameterised queries only (`$1`, `?`, query builders, ORM methods). Never interpolate input into
  SQL, shell commands or file paths. For paths, resolve and check the result stays inside the
  allowed base directory.
- Use `crypto.timingSafeEqual` for comparing secrets and tokens.
- Never log request bodies, tokens or personal data; log identifiers and outcomes.
- Prototype pollution: do not merge untrusted objects into existing ones with spread over
  `__proto__`-capable keys or naive deep-merge helpers; validate shape first.

## Packages and builds

- `package.json` `exports` defines the public surface of a library; adding a file there is a public
  API change. Keep `types` conditions first.
- Lockfiles change only through the package manager; never edit them by hand. Use the package
  manager from the profile (`npm`, `pnpm`, `yarn`, `bun`) and never mix them.
- Do not commit build output (`dist/`, `build/`) unless the repository already does so.

## Testing recipes

| Need | Recipe |
| --- | --- |
| Time | `vi.useFakeTimers()` / `jest.useFakeTimers()`; `node:test` has `mock.timers` |
| HTTP calls out | MSW (`setupServer`) or `nock` if already used; otherwise inject the client and fake it |
| Database | The project's test database or Testcontainers; never a shared environment |
| Environment variables | Set them in the test with cleanup (`vi.stubEnv`) |
| Snapshot tests | Only for stable serialised output; never as the only assertion of behaviour |

## Anti-patterns to flag in review

| Anti-pattern | Why it hurts | Instead |
| --- | --- | --- |
| `catch (e) {}` | Hides failures | Handle, map or rethrow with cause |
| `JSON.parse(input) as Order` | No runtime check | Validate with the schema |
| `await` in a loop over independent items | Serialises latency | `Promise.all` with bounded concurrency |
| Singletons importing configuration at module load | Untestable, order-dependent | Factories with injected configuration |
| Utility barrel files that import everything | Slow startup, cycles | Import from the module that owns the code |
