# ASP.NET Core patterns: reference

Load this file for errors, data access, resilience, security or testing details. It complements
[the stack skill](../SKILL.md).

## Error handling (.NET 8+)

```csharp
builder.Services.AddProblemDetails();
builder.Services.AddExceptionHandler<DomainExceptionHandler>();
app.UseExceptionHandler();

internal sealed class DomainExceptionHandler(IProblemDetailsService problems) : IExceptionHandler
{
    public async ValueTask<bool> TryHandleAsync(HttpContext context, Exception exception, CancellationToken ct)
    {
        var status = exception switch
        {
            NotFoundException => StatusCodes.Status404NotFound,
            ConflictException => StatusCodes.Status409Conflict,
            _ => 0,
        };
        if (status == 0) return false;
        context.Response.StatusCode = status;
        return await problems.TryWriteAsync(new() { HttpContext = context, Exception = exception });
    }
}
```

## Dependency injection lifetimes

| Lifetime | Use for | Never |
| --- | --- | --- |
| Singleton | Stateless, thread-safe services, caches with synchronisation | Capture `DbContext` or other scoped services |
| Scoped | `DbContext`, unit of work, per-request state | Resolve from the root provider |
| Transient | Lightweight stateless helpers | Hold disposable resources without disposal |

- Background services (`BackgroundService`) create a scope per unit of work
  (`IServiceScopeFactory.CreateAsyncScope()`).
- Enable `ValidateScopes` and `ValidateOnBuild` in development to catch lifetime mistakes.

## EF Core

| Concern | Practice |
| --- | --- |
| Read queries | `AsNoTracking()`, project with `Select`, paginate with `Skip/Take` on a stable order |
| Related data | `Include` only what is needed; `AsSplitQuery()` for large collections |
| Concurrency | Concurrency token (`[Timestamp]`/`IsRowVersion`); map `DbUpdateConcurrencyException` to 409 |
| Migrations | `dotnet ef migrations add`, review the SQL (`dotnet ef migrations script`), never edit applied ones |
| Bulk changes | `ExecuteUpdateAsync`/`ExecuteDeleteAsync` (EF Core 7+) instead of loading entities |
| Raw SQL | `FromSql($"... {param}")` (parameterised), never `FromSqlRaw` with concatenation |

## Outbound HTTP

```csharp
builder.Services.AddHttpClient<PaymentsClient>(c =>
{
    c.BaseAddress = new Uri(builder.Configuration["Payments:BaseUrl"]!);
    c.Timeout = TimeSpan.FromSeconds(10);
}).AddStandardResilienceHandler(); // if Microsoft.Extensions.Http.Resilience is referenced
```

## Security

- Authentication and authorisation policies configured centrally; endpoints use
  `RequireAuthorization("policy")` or `[Authorize(Policy = ...)]`; resource ownership checked in the
  handler or with an authorisation handler.
- Anti-forgery for cookie-authenticated form posts; CORS with explicit origins.
- Data protection keys persisted for multi-instance deployments (configuration, not code, in most tasks).
- Never log tokens, passwords or full request bodies.

## Logging and observability

- Message templates with named placeholders; `LoggerMessage` source generators for hot paths.
- Activity/OpenTelemetry already configured by the project: add spans only for meaningful operations.

## Testing recipes

| Need | Recipe |
| --- | --- |
| API | `WebApplicationFactory<Program>`; override services in `ConfigureTestServices` |
| Authentication | A test authentication handler registered in the factory |
| Database | Testcontainers (`PostgreSqlBuilder`, `MsSqlBuilder`) with migrations applied in the fixture |
| Time | `FakeTimeProvider` (`Microsoft.Extensions.TimeProvider.Testing`) |
| Collaborators | NSubstitute or Moq, following the project |
| Shared setup | `IClassFixture<T>` / `ICollectionFixture<T>` (xUnit) |

## Common review findings

| Finding | Typical severity |
| --- | --- |
| Sync-over-async (`.Result`) in request path | MEDIUM to HIGH (thread pool starvation) |
| Scoped `DbContext` captured in a singleton | HIGH |
| Endpoint without authorisation | BLOCKER |
| Entity returned from API | MEDIUM |
| `new HttpClient()` per request | MEDIUM |
| Secret in `appsettings.json` | BLOCKER |
