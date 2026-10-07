---
name: stack-java-spring
description: Senior Java and Spring Boot engineering for the Developer role - layered services, constructor injection, Spring Data JPA with correct transactions and fetching, Bean Validation, RFC 9457 error responses, Spring Security, configuration properties, Maven and Gradle builds, and JUnit 5, Mockito, MockMvc and Testcontainers tests. Preloaded by developer-java-spring; loaded by QA and reviewers for Java or Spring changes.
---

# Stack: Java and Spring Boot

## Purpose

Deliver Java services the way a senior Spring engineer would: thin controllers, transactional
services with clear boundaries, repositories that fetch exactly what is needed, validated input,
consistent error responses, configuration that is typed and safe, and tests at the right slice.
Adds stack knowledge to the [development](../development/SKILL.md) procedure.

## When to use

- The task's module has stack `spring` or `java` in the stack profile (Maven or Gradle).
- QA or a reviewer checks a Pull Request that changes `.java` files, `pom.xml`, Gradle build files
  or `application*.yml`/`.properties`.

## Inputs

- Java and Spring Boot versions from the stack profile. Spring Boot 3+ uses Jakarta EE
  (`jakarta.*` imports) and Java 17+; Spring Boot 4 moves to Spring Framework 7 and JSpecify
  null-safety annotations. Use the language features the configured release allows (records,
  sealed types, pattern matching, virtual threads on 21+ only if the project enables them).
- The build tool and wrapper (`./mvnw`, `./gradlew`), formatter (Spotless, Checkstyle), static
  analysis (Error Prone, SpotBugs, Sonar), migration tool (Flyway, Liquibase).
- The project's package structure (by layer or by feature), exception handling, mapping (MapStruct,
  manual), Lombok usage.
- Deep reference: [references/spring-patterns.md](references/spring-patterns.md).

## Procedure

1. **Read the module's conventions.** Package layout, how controllers map errors
   (`@RestControllerAdvice`), DTO and mapping style, whether Lombok is used. Follow them.
2. **Design the slice.** Controller (HTTP, validation, mapping) → service (business rules,
   `@Transactional`) → repository (persistence). Domain entities never leave the service as API
   responses; use DTOs or records.
3. **Persistence.** Change the schema only through a new migration (Flyway `V<n>__desc.sql` or a
   Liquibase changeset); never edit an applied migration. Design queries for the access pattern:
   fetch joins or entity graphs for needed associations, projections for read models, pagination for
   lists.
4. **Transactions.** `@Transactional` on service methods that write (and `readOnly = true` on
   reads when the project does so); no remote calls inside a transaction when avoidable; remember
   self-invocation bypasses the proxy.
5. **Input and errors.** `@Valid` on request bodies with Bean Validation constraints; domain errors
   as specific exceptions mapped once to `ProblemDetail` (RFC 9457) or the project's error format.
6. **Configuration.** New settings through `@ConfigurationProperties` records with validation, and
   documented defaults; secrets only from the environment or the secret store.
7. **Test.** Unit tests with JUnit 5 + AssertJ + Mockito for services; `@WebMvcTest` + MockMvc for
   controllers; `@DataJpaTest` or `@SpringBootTest` with Testcontainers for persistence and
   integration (with `@ServiceConnection` on Boot 3.1+). Never use H2 to test vendor-specific SQL.
8. **Validate.** `run_checks.py`: format check, tests, `verify`/`build` with the wrapper.

## Rules

- Constructor injection only (final fields); no field `@Autowired`.
- Never expose JPA entities in controllers or serialise them directly; never return
  `Optional` fields in DTOs.
- No N+1 queries: check every new association access in a loop; use fetch joins, `@EntityGraph`,
  batch fetching or projections.
- Do not catch `Exception` to return `200`; do not swallow exceptions; log once at the boundary
  with context, never with secrets or personal data.
- No string-concatenated JPQL/SQL; use parameters, Spring Data derived queries, or the Criteria API.
- Do not change `spring.jpa.hibernate.ddl-auto` away from `validate`/`none` outside local profiles.
- Security changes go through the existing `SecurityFilterChain`; never `permitAll()` a path to make
  a test pass; method security (`@PreAuthorize`) for ownership rules.
- Use `java.time` (`Instant`, `OffsetDateTime`), `BigDecimal` for money, and an injected `Clock`
  for testable time.
- New dependencies are managed by the Spring Boot BOM where possible (no version) and checked with
  `deps_check.py --ecosystem maven`.

## Required outputs

- Controller, service, repository and migration changes in the project's structure.
- Tests at the right slice for every acceptance criterion, including validation and error paths.
- Build evidence from the wrapper (`./mvnw -B verify` or `./gradlew build`).

## Quality checklist

- [ ] Constructor injection; no entities in the web layer.
- [ ] Every write runs in a service-level transaction; no remote calls inside it without a reason.
- [ ] No N+1 introduced; list endpoints paginate.
- [ ] Input validated with Bean Validation; errors mapped to the project's format with correct status.
- [ ] Schema changes are new migrations, never edits of applied ones.
- [ ] Configuration is typed and validated; no secret in `application*.yml`.
- [ ] Tests use the right slice; integration tests use Testcontainers, not H2, for real SQL.
- [ ] Format check and build pass with the wrapper.

## Failure conditions

- Docker is unavailable for Testcontainers in the sandbox → run the unit and slice tests, report the
  integration tests as `BLOCKED` with the error, and say so in the Pull Request; never replace them
  with H2 silently.
- The change requires a Spring Boot or Java major upgrade → stop; propose a separate task.
- A migration would rewrite or lock a large table → stop and escalate to `agent:architect`
  (data migration needs a human decision).

## Examples

**Controller → service with validation and ProblemDetail mapping:**

```java
@RestController
@RequestMapping("/api/orders")
class OrderController {
    private final OrderService orders;
    OrderController(OrderService orders) { this.orders = orders; }

    @PostMapping
    ResponseEntity<OrderResponse> create(@Valid @RequestBody CreateOrderRequest request, UriComponentsBuilder uri) {
        OrderResponse created = orders.create(request);
        return ResponseEntity.created(uri.path("/api/orders/{id}").build(created.id())).body(created);
    }
}

@RestControllerAdvice
class ApiErrors {
    @ExceptionHandler(OrderNotFoundException.class)
    ProblemDetail notFound(OrderNotFoundException e) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, e.getMessage());
    }
}

record CreateOrderRequest(@NotNull UUID customerId, @NotEmpty List<@Valid OrderLine> lines) {}
```

**Repository integration test with Testcontainers:**

```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Testcontainers
class OrderRepositoryTest {
    @Container @ServiceConnection
    static PostgreSQLContainer<?> db = new PostgreSQLContainer<>("postgres:16-alpine");

    @Autowired OrderRepository repository;

    @Test
    void findsOpenOrdersWithLinesInOneQuery() {
        // given saved orders, when fetching, then lines are loaded without extra queries
    }
}
```
