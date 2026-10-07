---
name: stack-angular
description: Senior Angular engineering for the Developer role - standalone components, signals and computed state, RxJS without leaks, dependency injection, routing with guards and resolvers, typed reactive forms, OnPush change detection, and TestBed/Testing Library tests. Preloaded by developer-angular together with stack-typescript; loaded by QA and reviewers for Angular changes.
---

# Stack: Angular

## Purpose

Deliver Angular features that follow the framework's current idioms for the project's version:
standalone components, signals for state, RxJS for streams of events, dependency injection for
everything shared, and templates that stay simple. Adds framework knowledge to the
[development](../development/SKILL.md) procedure.

## When to use

- The task's module has stack `angular` in the stack profile.
- QA or a reviewer checks a Pull Request that changes Angular components, services, routes or
  `angular.json`.

## Inputs

- The Angular version from the stack profile. Key milestones: signals (16+), built-in control flow
  `@if`/`@for`/`@switch` and deferrable views (17+), standalone by default (19+), signal inputs,
  `model()`, `output()` and signal queries (17.1+ to 19), zoneless change detection (opt-in, check
  `provideZonelessChangeDetection` in the bootstrap).
- `angular.json`, ESLint (`@angular-eslint`), the test runner (Karma/Jasmine, Jest or Vitest),
  state library (NgRx Store, NgRx SignalStore, services with signals) and UI library (Angular
  Material, PrimeNG, ...).
- Deep reference: [references/patterns.md](references/patterns.md).

## Procedure

1. **Match the project's era.** If the codebase uses NgModules, follow them in that area; if it is
   standalone, never add an NgModule. Use the template syntax the codebase uses (`@if` versus
   `*ngIf`) unless the task is a migration.
2. **Generate consistently.** Prefer `ng generate` (or the project's schematics) so file names,
   selectors and test files follow the conventions.
3. **State.** Component state in `signal()`; derived values in `computed()`; side effects that
   synchronise with non-Angular APIs in `effect()` (sparingly). Streams of events (HTTP, websockets,
   router events, debounced input) stay in RxJS; bridge with `toSignal`/`toObservable`.
4. **Components.** `ChangeDetectionStrategy.OnPush`, inputs via `input()`/`input.required()` (or
   `@Input` in older code), outputs via `output()`, `inject()` for dependencies. Templates contain
   no business logic and no function calls that do work on every check; use `computed` or pure pipes.
5. **Services and HTTP.** Shared logic in `@Injectable({ providedIn: "root" })` services or
   route-level providers; `HttpClient` with typed responses and the project's interceptors for
   authentication and errors.
6. **Forms.** Typed reactive forms (`FormGroup<{...}>`, `nonNullable`), validators close to the form,
   error messages tied to controls with `aria-describedby`.
7. **Test.** TestBed with standalone imports or Angular Testing Library; `HttpTestingController` for
   HTTP; harnesses for Angular Material components; `fakeAsync`/`tick` for timers.
8. **Validate.** `run_checks.py`: `ng lint`, tests in single-run mode (`--watch=false`), and
   `ng build` (catches template type errors with strict templates).

## Rules

- Every manual subscription is cleaned up: prefer the `async` pipe or `toSignal`; otherwise
  `takeUntilDestroyed()`. No nested `subscribe` calls; compose with `switchMap`, `concatMap`,
  `mergeMap` or `exhaustMap` chosen deliberately.
- Never mutate an input or a signal's object value in place; set a new value (`update(v => ...)`).
- No direct DOM access (`document`, `ElementRef.nativeElement` writes) when a binding, directive or
  the CDK can do it; never bypass sanitisation (`bypassSecurityTrust*`) without a security review.
- Do not disable strict template checking or `strict` TypeScript flags.
- Lazy-load feature routes (`loadComponent`/`loadChildren`); guards and resolvers are functional
  (`CanActivateFn`) in modern code.
- Keep `effect()` for synchronisation only; never use it to set other signals that `computed` could
  derive.
- Do not add a state library for one feature; follow the project's existing state approach.

## Required outputs

- Components, services and routes following the project's structure and naming
  (`feature/feature.component.ts`, `feature.service.ts`).
- Tests for components (rendered behaviour), services (logic and HTTP) and guards.
- A successful production build in the evidence.

## Quality checklist

- [ ] Components use OnPush (or the project's zoneless setup) and have no work-heavy template calls.
- [ ] No leaked subscriptions; no nested `subscribe`.
- [ ] Signals hold state, `computed` derives it, `effect` only synchronises.
- [ ] New routes are lazy-loaded and protected by the right guards.
- [ ] Forms are typed; errors are accessible.
- [ ] Tests run once (`--watch=false`) and pass; `ng build` passes with strict templates.

## Failure conditions

- The change needs an Angular or library major upgrade → stop; propose it as a separate task.
- NgModule and standalone patterns conflict in the touched area → follow the area's pattern and
  note the debt in the Pull Request; ask `agent:architect` if the task requires mixing them.
- Tests need a browser that is not available (Karma with Chrome) → report `BLOCKED` with the error
  and the command; do not switch test runners inside the task.

## Examples

**Signal-based component with an RxJS bridge:**

```ts
@Component({
  selector: "app-order-search",
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [ReactiveFormsModule, OrderListComponent],
  template: `
    <label for="q">Search orders</label>
    <input id="q" [formControl]="query" />
    @if (results(); as orders) { <app-order-list [orders]="orders" /> } @else { <p>Searching…</p> }
  `,
})
export class OrderSearchComponent {
  private readonly api = inject(OrderApi);
  readonly query = new FormControl("", { nonNullable: true });
  readonly results = toSignal(
    this.query.valueChanges.pipe(debounceTime(300), distinctUntilChanged(), switchMap((q) => this.api.search(q))),
  );
}
```
