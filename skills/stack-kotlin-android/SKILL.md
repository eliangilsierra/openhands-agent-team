---
name: stack-kotlin-android
description: Senior Kotlin and Android engineering for the Developer role - idiomatic Kotlin, null safety, coroutines and Flow with structured concurrency, Jetpack Compose with state hoisting, ViewModel and unidirectional data flow, Hilt, Room, Gradle Kotlin DSL and version catalogs, Ktor on the JVM, and JUnit, MockK, Turbine, Robolectric and Compose UI tests. Preloaded by developer-kotlin-android; loaded by QA and reviewers for Kotlin or Android changes.
---

# Stack: Kotlin and Android

## Purpose

Deliver Kotlin code that is null-safe, concurrent without leaks, and testable, and Android features
that follow the platform's architecture guidance: UI that renders state, ViewModels that own it,
repositories that hide data sources, and lifecycle-aware collection. Also covers Kotlin on the JVM
(Ktor, libraries, multiplatform). Adds stack knowledge to the [development](../development/SKILL.md)
procedure.

## When to use

- The task's module has stack `android` or `kotlin` in the stack profile.
- QA or a reviewer checks a Pull Request that changes `.kt`/`.kts` files, Android resources or
  manifests, or Gradle build logic of a Kotlin project.

## Inputs

- From the stack profile: Android Gradle Plugin, Kotlin version (K2 compiler in Kotlin 2.x),
  `compileSdk`/`minSdk`, Compose usage, DI (Hilt, Koin), persistence (Room, DataStore), networking
  (Retrofit, Ktor client), lint tools (Android Lint, ktlint, detekt).
- The module structure (`:app`, `:core:*`, `:feature:*`), version catalog `gradle/libs.versions.toml`,
  and convention plugins.
- Deep reference: [references/android-patterns.md](references/android-patterns.md).

## Procedure

1. **Respect the module graph.** Put code in the feature or core module the architecture names;
   never add a dependency from a core module to a feature module. Dependencies are added through the
   version catalog.
2. **State model.** One immutable `UiState` per screen (data class or sealed interface), exposed by
   the ViewModel as `StateFlow` (`stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), initial)`).
   One-off events are modelled as state the UI consumes, not as fire-and-forget channels, unless
   the codebase has another established pattern.
3. **Compose UI.** Stateless composables receiving state and lambdas (state hoisting); a thin
   screen-level composable collects with `collectAsStateWithLifecycle()`. `remember`/`rememberSaveable`
   for UI-only state, stable keys in lazy lists, previews for new components when the project uses them.
4. **Concurrency.** Coroutines launched in an owned scope (`viewModelScope`, `lifecycleScope`, an
   injected application scope); dispatchers injected, not hard-coded; `withContext(io)` at the data
   layer boundary; cancellation respected (never catch `CancellationException` without rethrowing).
5. **Data layer.** Repositories expose `Flow` or `suspend` functions and map DTOs and entities to
   domain models. Room migrations for every schema change, with a migration test.
6. **Test.** JUnit + MockK (or fakes) for ViewModels and repositories, `kotlinx-coroutines-test`
   (`runTest`, `StandardTestDispatcher`, `Dispatchers.setMain`), Turbine for Flows, Robolectric or
   Compose UI tests (`createComposeRule`) for UI behaviour, Room in-memory database for DAOs.
7. **Validate.** `run_checks.py`: `testDebugUnitTest`, `lintDebug` (and ktlint/detekt), `assembleDebug`.
   Instrumented tests need an emulator: report them `BLOCKED` when none is available.

## Rules

- No `!!` except where a preceding check makes null impossible and the compiler cannot see it; prefer
  `?.let`, `requireNotNull` with a message, or a better type.
- No `GlobalScope`, no `runBlocking` on the main thread or in production code paths.
- Never collect flows in the UI without lifecycle awareness (`collectAsStateWithLifecycle`,
  `repeatOnLifecycle`).
- Never hold an `Activity`, `View` or `Context` (other than the application context) in a ViewModel,
  singleton or long-lived object.
- No network or disk I/O on the main thread; no blocking calls inside coroutines without switching
  to an I/O dispatcher.
- Strings shown to users come from resources; no hard-coded user-facing text; content descriptions
  for meaningful images and icons.
- Secrets never in the APK (`BuildConfig`, resources or code); API keys that must ship are treated
  as public and restricted server-side.
- Room schema changes need a migration and an exported schema; never `fallbackToDestructiveMigration`
  in production builds.
- Do not raise `minSdk`, change `targetSdk` or add permissions unless the task asks for it.

## Required outputs

- Screen state, ViewModel, repository and UI changes in the right modules.
- Unit tests for ViewModels and repositories, UI tests for interactive behaviour when the project
  has them, migration tests for schema changes.
- Evidence of unit tests, lint and debug assembly.

## Quality checklist

- [ ] UI state is immutable and exposed as `StateFlow`; the UI only renders it and sends events.
- [ ] Every coroutine has an owner scope; dispatchers are injected; cancellation is not swallowed.
- [ ] Flows are collected lifecycle-aware.
- [ ] No leaked `Context`/`Activity`; no I/O on the main thread.
- [ ] Composables are stateless where possible; lazy lists have stable keys.
- [ ] Schema changes include a migration and its test.
- [ ] `testDebugUnitTest`, lint and `assembleDebug` pass.

## Failure conditions

- The Android SDK or an emulator is missing in the sandbox → run JVM unit tests and lint if
  possible; report the rest as `BLOCKED` with the exact error.
- The change needs a new permission, a `minSdk` change or a Play policy-relevant behaviour → stop and
  ask on the Issue (`needs-human`).
- Gradle configuration or convention plugins must change beyond the task → propose a separate
  `chore/` task.

## Examples

**ViewModel with StateFlow and a coroutine test:**

```kotlin
@HiltViewModel
class NotesViewModel @Inject constructor(private val repository: NotesRepository) : ViewModel() {
    val state: StateFlow<NotesUiState> = repository.observeNotes()
        .map<List<Note>, NotesUiState> { NotesUiState.Loaded(it) }
        .catch { emit(NotesUiState.Error(it.message ?: "unknown")) }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), NotesUiState.Loading)
}

@Test
fun `emits loaded notes`() = runTest {
    val repository = FakeNotesRepository(listOf(Note("1", "Buy milk")))
    val viewModel = NotesViewModel(repository)
    viewModel.state.test {
        assertEquals(NotesUiState.Loading, awaitItem())
        assertEquals(NotesUiState.Loaded(listOf(Note("1", "Buy milk"))), awaitItem())
    }
}
```
