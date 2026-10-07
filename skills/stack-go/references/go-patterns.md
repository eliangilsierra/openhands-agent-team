# Go patterns: reference

Load this file for concurrency, HTTP, database, configuration or testing details. It complements
[the stack skill](../SKILL.md).

## Concurrency patterns

```go
g, ctx := errgroup.WithContext(ctx)
g.SetLimit(8) // bounded fan-out
for _, id := range ids {
    g.Go(func() error { // Go 1.22+: id is per-iteration
        return process(ctx, id)
    })
}
if err := g.Wait(); err != nil {
    return fmt.Errorf("process batch: %w", err)
}
```

| Need | Tool |
| --- | --- |
| Fan-out with first error cancelling the rest | `errgroup.WithContext` |
| Protect a map or counter | `sync.Mutex` / `sync.RWMutex` / `atomic` |
| One-time initialisation | `sync.OnceValue` / `sync.Once` |
| Worker pool | Buffered job channel + fixed workers + `WaitGroup`; close the channel from the producer |
| Rate limit | `golang.org/x/time/rate` if present |

- The sender closes a channel, never the receiver; never close a channel twice.
- `select` with `ctx.Done()` in every loop that waits.

## HTTP services

```go
srv := &http.Server{
    Addr:              ":8080",
    Handler:           mux,
    ReadHeaderTimeout: 5 * time.Second,
    ReadTimeout:       15 * time.Second,
    WriteTimeout:      15 * time.Second,
    IdleTimeout:       60 * time.Second,
}
```

- Go 1.22+ `ServeMux` patterns: `mux.HandleFunc("GET /orders/{id}", h.GetOrder)` and `r.PathValue("id")`.
- Limit request bodies (`http.MaxBytesReader`); decode with `json.NewDecoder(r.Body)` and
  `DisallowUnknownFields()` when the API is strict.
- Graceful shutdown: `srv.Shutdown(ctx)` on `SIGTERM` in `main`.
- Middleware is `func(http.Handler) http.Handler`; keep authentication and logging there.

## Database

- `database/sql` with a configured pool (`SetMaxOpenConns`, `SetConnMaxLifetime`); `QueryContext`
  with placeholders (`$1` for Postgres, `?` for MySQL/SQLite).
- Transactions: `tx, err := db.BeginTx(ctx, nil)`; `defer tx.Rollback()`; `tx.Commit()` at the end
  (rollback after commit is a no-op).
- sqlc: change the SQL and regenerate; never edit generated code.
- Map `sql.ErrNoRows` to the domain's `ErrNotFound` at the repository boundary.

## Configuration and logging

- Parse configuration once in `main` (flags or environment) into a typed struct; pass it down.
- `slog` with a JSON handler in production; add request ids through middleware and `slog.With`.

## Testing recipes

| Need | Recipe |
| --- | --- |
| Handler | `httptest.NewRecorder()` + `httptest.NewRequest`; or `httptest.NewServer` for clients |
| Fakes | Small structs implementing the consumer interface |
| Golden files | `testdata/` with an `-update` flag if the project uses it |
| Time | Inject a `func() time.Time` or a clock interface |
| Database | Testcontainers-go or the project's test database; transactions rolled back per test |
| Race detection | `go test -race ./...` |
| Fuzzing | `func FuzzParse(f *testing.F)` for parsers, when the task touches one |

## Common review findings

| Finding | Typical severity |
| --- | --- |
| Ignored error from I/O | MEDIUM to HIGH |
| Goroutine leak (no exit on cancel) | MEDIUM |
| Data race | HIGH |
| SQL string concatenation | BLOCKER |
| HTTP server without timeouts | MEDIUM |
| Context stored in a struct | LOW |
