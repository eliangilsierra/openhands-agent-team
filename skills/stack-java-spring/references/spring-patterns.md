# Spring Boot patterns: reference

Load this file for persistence, transactions, security, messaging, configuration or test slicing
questions. It complements [the stack skill](../SKILL.md).

## Test slices

| Annotation | Loads | Use for |
| --- | --- | --- |
| none (plain JUnit) | Nothing | Domain logic, services with mocked collaborators |
| `@WebMvcTest(OrderController.class)` | MVC layer, advice, converters, security filters | Request mapping, validation, status codes, JSON shape |
| `@DataJpaTest` | JPA, repositories, Flyway/Liquibase | Queries, mappings, constraints (with Testcontainers) |
| `@JsonTest` | Jackson | Serialisation contracts |
| `@SpringBootTest(webEnvironment = RANDOM_PORT)` | Whole context | End-to-end through HTTP with real infrastructure |

- Mock collaborators in slices with `@MockitoBean` (Boot 3.4+) or `@MockBean` in older versions.
- Reuse containers across tests (`static` containers or a shared base class) to keep the suite fast.
- Security in MVC tests: `@WithMockUser` or `SecurityMockMvcRequestPostProcessors.jwt()`.

## JPA and performance

| Problem | Symptom | Fix |
| --- | --- | --- |
| N+1 | One query per row when touching an association | `JOIN FETCH`, `@EntityGraph`, `@BatchSize`, or a projection |
| Eager everything | Slow queries, huge joins | Associations `LAZY` by default; fetch per use case |
| `LazyInitializationException` | Access after the transaction | Fetch what the use case needs inside the service; do not enable open-in-view to hide it |
| Large result sets | Memory spikes | Pagination (`Pageable`), streaming with `Stream` in a transaction, or keyset pagination |
| Lost updates | Concurrent edits overwrite | `@Version` optimistic locking; map `OptimisticLockException` to `409` |

- `equals`/`hashCode` on entities: based on the identifier with care for transient entities, or not
  overridden; never on all fields with Lombok `@Data`.
- Enable SQL logging only in tests or local profiles to count queries.

## Transactions

- Default propagation `REQUIRED`; use `REQUIRES_NEW` only for work that must commit independently
  (audit logs), knowing it needs a second connection.
- Checked exceptions do not roll back by default; declare `rollbackFor` when the project throws them.
- Publish domain events after commit (`@TransactionalEventListener(phase = AFTER_COMMIT)`) when other
  systems must not see uncommitted state; for reliable messaging use the outbox pattern if present.

## Web layer

- Return `ResponseEntity` with the right status: `201` + `Location` for creation, `204` for empty
  success, `409` for conflicts, `422` or `400` for validation per the project's convention.
- Enable `spring.mvc.problemdetails.enabled` or the project's advice; one format for all errors.
- Pagination responses: do not serialise `PageImpl` directly; map to a stable DTO.
- Idempotency for retries on `POST` where the domain requires it (idempotency key header).

## Security

- `SecurityFilterChain` bean with explicit `requestMatchers` rules; deny by default.
- Ownership checks in the service or with `@PreAuthorize("@orderAccess.canRead(#id, authentication)")`.
- CSRF stays enabled for cookie-based sessions; stateless JWT APIs disable it deliberately.
- Passwords with `PasswordEncoder` (`DelegatingPasswordEncoder`); never custom hashing.
- CORS configured centrally with explicit origins, never `*` with credentials.

## Configuration

```java
@ConfigurationProperties(prefix = "billing")
@Validated
public record BillingProperties(@NotNull URI providerUrl, @DurationMin(seconds = 1) Duration timeout) {}
```

- Register with `@EnableConfigurationProperties` or `@ConfigurationPropertiesScan`.
- Profiles for environment differences; no `if (env == "prod")` in code.

## Outbound calls

- `RestClient` (Boot 3.2+) or `WebClient` with timeouts; Resilience4j for retries and circuit
  breakers if already present. Never retry non-idempotent calls blindly.
- Map remote errors to domain exceptions at the client boundary.

## Build hygiene

- Maven: run through `./mvnw -B`; dependency versions from the parent BOM; `mvn -B dependency:tree`
  to explain a transitive dependency. Gradle: version catalogs (`libs.versions.toml`) when present.
- Keep Java `release` consistent with the toolchain in CI.

## Common review findings

| Finding | Typical severity |
| --- | --- |
| Entity returned from controller | MEDIUM (data exposure risk can raise it) |
| Missing authorisation on a new endpoint | BLOCKER |
| N+1 on a list endpoint | MEDIUM to HIGH |
| Edited applied migration | HIGH |
| Field injection, mutable singletons | LOW to MEDIUM |
| `catch (Exception e) { return ResponseEntity.ok() }` | HIGH |
