---
name: stack-go
description: Senior Go engineering for the Developer role - idiomatic package design, small interfaces at the consumer, explicit error handling with wrapping, context propagation, goroutines and channels without leaks or races, net/http services, database/sql, structured logging with slog, and table-driven tests with the race detector. Preloaded by developer-go; loaded by QA and reviewers for Go changes.
---

# Stack: Go

## Purpose

Deliver Go code that is simple, explicit and safe under concurrency: packages with clear
responsibilities, errors handled where they happen, contexts passed through every call that can
block, and table-driven tests. Adds stack knowledge to the [development](../development/SKILL.md)
procedure.

## When to use

- The task's module has stack `go` in the stack profile.
- QA or a reviewer checks a Pull Request that changes `.go` files, `go.mod` or `go.sum`.

## Inputs

- From the stack profile: Go version in `go.mod` (1.22 changed loop variable scoping and added
  method and wildcard patterns to `http.ServeMux`; 1.23 added range-over-func iterators), router or
  framework (standard library, chi, gin, echo), linters (`golangci-lint` configuration).
- The project layout (`cmd/`, `internal/`, `pkg/`), error conventions, logger (`log/slog` or other),
  database layer (`database/sql`, sqlc, pgx, GORM).
- Deep reference: [references/go-patterns.md](references/go-patterns.md).

## Procedure

1. **Place the code.** Business code under `internal/<domain>`; binaries under `cmd/<name>`. Name
   packages by what they provide (`orders`, not `utils`); avoid import cycles by depending on
   interfaces defined by the consumer.
2. **Design the API.** Accept interfaces, return concrete types; keep interfaces small (one to three
   methods) and defined where they are used. Constructors (`NewService(deps...)`) take explicit
   dependencies.
3. **Errors.** Return errors as the last value; wrap with context (`fmt.Errorf("load order %s: %w",
   id, err)`); define sentinel errors (`var ErrNotFound = errors.New(...)`) or typed errors for
   conditions callers branch on, and check them with `errors.Is`/`errors.As`.
4. **Context.** `ctx context.Context` is the first parameter of every function that does I/O or may
   block; never store it in a struct; respect cancellation in loops and goroutines.
5. **Concurrency.** Every goroutine has a clear owner and exit path; use `errgroup.Group` (with
   context) for fan-out, `sync.WaitGroup` for fire-and-wait, channels for ownership transfer, mutexes
   for shared state. Bound concurrency.
6. **HTTP.** Handlers decode and validate input, call the service, encode the response; set
   timeouts on servers (`ReadHeaderTimeout`, `ReadTimeout`, `WriteTimeout`) and clients
   (`http.Client{Timeout: ...}`); close response bodies.
7. **Test.** Table-driven tests with `t.Run` subtests, `t.Parallel()` where safe, `httptest` for
   handlers and clients, fakes implementing the consumer interfaces, `t.Cleanup`, golden files when
   the project uses them. Run with `-race` when cgo is available.
8. **Validate.** `run_checks.py`: `go vet`/`golangci-lint run`, `go test ./...` (add `-race`),
   `go build ./...`; `gofmt`/`goimports` produce no diff.

## Rules

- Never ignore an error (`_ = f()` only with a comment explaining why it is safe).
- No `panic` for expected failures; panics only for programmer errors at initialisation.
- No goroutine without a way to stop; no unbounded goroutine creation from request input.
- No shared state without synchronisation; data races are bugs even when tests pass.
- Do not use `init()` for logic with side effects beyond registration; no global mutable state.
- SQL uses placeholders; `rows.Close()` deferred and `rows.Err()` checked.
- `defer` inside loops only when the loop body is a function; otherwise resources pile up.
- Log with structured fields (`slog.Info("order created", "order_id", id)`); never log secrets.
- Keep dependencies minimal; prefer the standard library; new modules go through `deps_check.py
  --ecosystem go`, and `go mod tidy` keeps `go.mod`/`go.sum` consistent.

## Required outputs

- Packages and functions following the project's layout, with wrapped errors and context passing.
- Table-driven tests for each acceptance criterion and error path.
- Evidence of vet or lint, tests (with `-race` when possible) and build.

## Quality checklist

- [ ] Every error is handled or returned with context; sentinel or typed errors for branching.
- [ ] Every blocking call receives a context; cancellation ends goroutines and loops.
- [ ] No data races (`go test -race` passes when available); no leaked goroutines.
- [ ] Interfaces are small and owned by the consumer.
- [ ] HTTP servers and clients have timeouts; response bodies are closed.
- [ ] Tests are table-driven with subtests; no sleeps for synchronisation.
- [ ] `gofmt`, vet or lint, tests and build pass.

## Failure conditions

- cgo is unavailable so `-race` cannot run → run tests without it and state it in the evidence.
- The change requires a new module major version (`/v2`) or a public API break → stop and escalate to
  `agent:architect`.
- `go.sum` verification fails on `main` → report `BLOCKED` with the output.

## Examples

**Handler, service and table-driven test:**

```go
func (h *Handler) GetOrder(w http.ResponseWriter, r *http.Request) {
    order, err := h.orders.Get(r.Context(), r.PathValue("id"))
    switch {
    case errors.Is(err, orders.ErrNotFound):
        http.Error(w, "order not found", http.StatusNotFound)
        return
    case err != nil:
        h.log.ErrorContext(r.Context(), "get order", "err", err)
        http.Error(w, "internal error", http.StatusInternalServerError)
        return
    }
    writeJSON(w, http.StatusOK, order)
}

func TestAvailable(t *testing.T) {
    tests := []struct {
        name            string
        stock, quantity int
        want            bool
    }{
        {"enough stock", 5, 3, true},
        {"exact stock", 3, 3, true},
        {"not enough", 2, 3, false},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            t.Parallel()
            if got := Available(tt.stock, tt.quantity); got != tt.want {
                t.Errorf("Available(%d, %d) = %v, want %v", tt.stock, tt.quantity, got, tt.want)
            }
        })
    }
}
```
