# Kotlin and Android patterns: reference

Load this file for architecture, Compose performance, persistence, Gradle or Kotlin-on-the-JVM
details. It complements [the stack skill](../SKILL.md).

## Architecture layers

| Layer | Contains | Depends on |
| --- | --- | --- |
| UI | Composables or Views, screen state collection, navigation | ViewModel |
| ViewModel | `UiState`, user event handling, calls to use cases or repositories | Domain/data |
| Domain (optional) | Use cases with one public `operator fun invoke` | Repositories (interfaces) |
| Data | Repositories, data sources (Room, Retrofit/Ktor, DataStore), mappers | Platform libraries |

- Repositories are the single source of truth: the UI observes the database flow; network results
  are written to the database.
- Inject dispatchers with a qualifier (`@IoDispatcher`) so tests can replace them.

## Compose essentials

| Concern | Practice |
| --- | --- |
| State hoisting | `@Composable fun NoteRow(note: Note, onToggle: (String) -> Unit)` |
| Recomposition cost | Pass stable, immutable types; use `key` in `LazyColumn` items; avoid allocating in composition |
| Derived values | `remember(input) { compute(input) }` or `derivedStateOf` for frequently changing inputs |
| Side effects | `LaunchedEffect(key)` for suspend work tied to composition; `DisposableEffect` with cleanup |
| Semantics | `contentDescription`, `Modifier.semantics { }`, touch targets of at least 48 dp |
| Theming | Material 3 tokens from the theme, no hard-coded colours |

## Coroutines and Flow

- `StateFlow` for state, `SharedFlow` for broadcasts; avoid `LiveData` in new code unless the area uses it.
- `flowOn(io)` in the data layer; never `flowOn` in the UI.
- Combine sources with `combine`; react to latest input with `flatMapLatest`.
- Handle errors with `catch` in the stream; `retryWhen` with backoff for transient network errors.
- `supervisorScope` when one child's failure must not cancel siblings.

## Room

```kotlin
val MIGRATION_3_4 = object : Migration(3, 4) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("ALTER TABLE notes ADD COLUMN pinned INTEGER NOT NULL DEFAULT 0")
    }
}
```

- `exportSchema = true` and the schema directory under version control; test with
  `MigrationTestHelper`.
- DAOs return `Flow<List<T>>` for observation and `suspend` for one-shot operations.

## Networking

- Retrofit or Ktor client with timeouts, a single configured client, and an interceptor or plugin for
  authentication.
- Map HTTP errors to a sealed `Result`/error type at the data layer; the UI never sees HTTP codes.
- Use `kotlinx.serialization` or the project's converter consistently.

## Gradle

- Dependencies through `libs.versions.toml` aliases (`implementation(libs.androidx.room.ktx)`).
- Convention plugins in `build-logic/` hold shared configuration; change them only in a `chore/` task.
- KSP for annotation processing (Room, Hilt) unless the project still uses kapt.

## Kotlin on the JVM (Ktor and libraries)

- Ktor routes in `Application.module()` extension functions per feature; `install(ContentNegotiation)`,
  `StatusPages` for error mapping, request validation plugin for input.
- `testApplication { }` for route tests.
- Prefer `Result`/sealed types for expected failures and exceptions for programmer errors.
- Public library APIs: explicit visibility and return types (`explicitApi()` when enabled).

## Testing recipes

| Need | Recipe |
| --- | --- |
| Main dispatcher | A JUnit rule or extension that calls `Dispatchers.setMain(StandardTestDispatcher())` |
| Flows | Turbine `test { awaitItem() }` |
| Compose UI | `composeTestRule.setContent { }`, `onNodeWithText("Save").performClick()`, `assertIsDisplayed()` |
| Android framework in JVM tests | Robolectric |
| Time | Inject a `Clock`/`TimeSource`; `advanceTimeBy` in `runTest` |

## Common review findings

| Finding | Typical severity |
| --- | --- |
| Activity context held in a singleton | HIGH (leak) |
| `GlobalScope.launch` | MEDIUM |
| Flow collected without lifecycle awareness | MEDIUM |
| `fallbackToDestructiveMigration()` in release | HIGH (data loss) |
| API secret in `BuildConfig` | BLOCKER if it is a real secret |
| Missing content descriptions on actionable icons | LOW to MEDIUM |
