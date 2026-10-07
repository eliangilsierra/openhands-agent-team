---
name: stack-dotnet
description: Senior C# and .NET engineering for the Developer role - ASP.NET Core minimal APIs and controllers, dependency injection lifetimes, options pattern, async/await with cancellation, nullable reference types, Entity Framework Core queries and migrations, ProblemDetails errors, and xUnit, NUnit or MSTest with WebApplicationFactory and Testcontainers. Preloaded by developer-dotnet; loaded by QA and reviewers for .NET changes.
---

# Stack: C# and .NET

## Purpose

Deliver .NET services that use the platform's built-in patterns correctly: dependency injection
with the right lifetimes, typed options, asynchronous code end to end with cancellation, nullable
reference types respected, EF Core queries shaped for their use, and consistent error responses.
Adds stack knowledge to the [development](../development/SKILL.md) procedure.

## When to use

- The task's module has stack `dotnet` in the stack profile.
- QA or a reviewer checks a Pull Request that changes `.cs` files, `.csproj`/`.sln`,
  `Directory.Build.props`, `appsettings*.json` or EF Core migrations.

## Inputs

- From the stack profile: target framework (`net8.0` and `net10.0` are LTS), the solution file,
  test framework, and the commands (`dotnet restore`, `build`, `test`, `format --verify-no-changes`).
- `Directory.Build.props`/`.editorconfig` (nullable, warnings as errors, analyzers), central package
  management (`Directory.Packages.props`), the API style (minimal APIs or controllers), validation
  library (DataAnnotations, FluentValidation), data access (EF Core, Dapper).
- Deep reference: [references/aspnetcore-patterns.md](references/aspnetcore-patterns.md).

## Procedure

1. **Read the build settings.** Respect `<Nullable>enable</Nullable>`,
   `TreatWarningsAsErrors` and analyzer severities; new code compiles without new warnings.
2. **Endpoint.** Follow the project's style: minimal API groups (`MapGroup`) with typed results
   (`Results<Ok<T>, NotFound>`), or `[ApiController]` controllers. Validate input; map domain errors
   to `ProblemDetails` through the project's exception handler (`IExceptionHandler` on .NET 8+).
3. **Services and DI.** Register with the right lifetime: `Scoped` for anything using a `DbContext`,
   `Singleton` only for thread-safe stateless services, `Transient` for lightweight stateless ones.
   Never inject a scoped service into a singleton.
4. **Configuration.** Options pattern: a settings class bound with
   `AddOptions<T>().BindConfiguration("Section").ValidateDataAnnotations().ValidateOnStart()`;
   inject `IOptions<T>`/`IOptionsMonitor<T>`. Secrets from user secrets locally and the environment
   or a vault elsewhere.
5. **Data.** EF Core queries with `AsNoTracking()` for reads, projections (`Select`) to DTOs,
   `Include` only for what is needed, pagination for lists. Schema changes with
   `dotnet ef migrations add <Name>`; review the generated migration.
6. **Async.** `async` all the way down, `CancellationToken` accepted by endpoints and passed to every
   I/O call; `ConfigureAwait(false)` in libraries if the project does so.
7. **Test.** xUnit (or the project's framework) with FluentAssertions or the project's assertions;
   `WebApplicationFactory<Program>` for API tests; Testcontainers for the real database engine;
   `TimeProvider` (.NET 8+) or an injected clock for time; NSubstitute/Moq for collaborators.
8. **Validate.** `run_checks.py`: `dotnet format --verify-no-changes`, `dotnet build`, `dotnet test`.

## Rules

- No `.Result`, `.Wait()` or `GetAwaiter().GetResult()` on tasks in application code; no
  `async void` except event handlers.
- Respect nullability: no `!` (null-forgiving) without a preceding guarantee; validate public inputs
  (`ArgumentNullException.ThrowIfNull`).
- Never return EF entities from endpoints; return DTOs or records.
- No string-concatenated SQL (`FromSqlRaw` with interpolation); use `FromSql`/parameters or LINQ.
- Do not create `HttpClient` per call; use `IHttpClientFactory` or typed clients with timeouts and
  resilience handlers if the project uses them.
- Do not catch `Exception` to hide failures; log with structured templates
  (`logger.LogInformation("Order {OrderId} created", id)`), never with interpolated strings or secrets.
- Do not suppress analyzer warnings without a justification comment and reviewer agreement.
- Package versions through central package management when present; new packages go through
  `deps_check.py --ecosystem nuget`.

## Required outputs

- Endpoints, services, options and migrations following the project's structure.
- Unit and API tests for each acceptance criterion, including validation and not-found paths.
- Evidence of format verification, build without new warnings, and tests.

## Quality checklist

- [ ] DI lifetimes are correct; no scoped service captured by a singleton.
- [ ] Async end to end with `CancellationToken`; no sync-over-async.
- [ ] Nullable warnings are zero for new code; no unjustified `!`.
- [ ] Endpoints return DTOs and `ProblemDetails` errors with correct status codes.
- [ ] EF Core reads use `AsNoTracking` and projections; lists paginate; migrations reviewed.
- [ ] Options are validated on start; no secret in `appsettings*.json`.
- [ ] `dotnet format --verify-no-changes`, build and tests pass.

## Failure conditions

- The SDK version in `global.json` is not installed in the sandbox → report `BLOCKED` with the
  `dotnet --list-sdks` output; do not change `global.json` inside the task.
- Docker is unavailable for Testcontainers → run unit tests, report integration tests `BLOCKED`, and
  never replace a relational engine with the in-memory provider for query behaviour.
- The change requires a target framework upgrade → stop; propose a separate task.

## Examples

**Minimal API group with typed results and validation:**

```csharp
public static class OrderEndpoints
{
    public static RouteGroupBuilder MapOrders(this IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/orders").RequireAuthorization();
        group.MapGet("/{id:guid}", GetOrder);
        return group;
    }

    private static async Task<Results<Ok<OrderDto>, NotFound>> GetOrder(
        Guid id, OrdersDbContext db, ClaimsPrincipal user, CancellationToken ct)
    {
        var order = await db.Orders.AsNoTracking()
            .Where(o => o.Id == id && o.OwnerId == user.GetUserId())
            .Select(o => new OrderDto(o.Id, o.Total, o.Status))
            .SingleOrDefaultAsync(ct);
        return order is null ? TypedResults.NotFound() : TypedResults.Ok(order);
    }
}
```

**API test with WebApplicationFactory:**

```csharp
public class OrderApiTests(ApiFactory factory) : IClassFixture<ApiFactory>
{
    [Fact]
    public async Task Unknown_order_returns_404()
    {
        var client = factory.CreateAuthenticatedClient();
        var response = await client.GetAsync($"/api/orders/{Guid.NewGuid()}");
        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
    }
}
```
