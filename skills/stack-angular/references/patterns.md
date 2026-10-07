# Angular patterns: reference

Load this file for RxJS operator choice, state management, routing, forms or testing details. It
complements [the stack skill](../SKILL.md).

## Choosing the flattening operator

| Operator | Behaviour | Use for |
| --- | --- | --- |
| `switchMap` | Cancels the previous inner stream | Search-as-you-type, route parameter changes |
| `concatMap` | Queues in order | Ordered writes, sequential saves |
| `mergeMap` | Runs in parallel | Independent requests with bounded concurrency (`mergeMap(fn, 4)`) |
| `exhaustMap` | Ignores new values while busy | Submit buttons, login |

Handle errors inside the inner stream (`catchError` returning a fallback) so one failure does not
complete the outer stream.

## Signals and RxJS together

- `toSignal(obs$, { initialValue })` in an injection context; it unsubscribes automatically.
- `toObservable(signal)` when a signal must drive an RxJS pipeline.
- `rxResource`/`resource` (version-dependent) for request-driven async state when the project uses it.
- `linkedSignal` (19+) for state that resets when a source changes.

## State management options

| Option | When |
| --- | --- |
| Signals in a feature service | Most features; simple and testable |
| NgRx SignalStore | Feature state with computed selectors and methods, if the project uses NgRx |
| NgRx Store + Effects | Large apps already built on it; follow its actions/reducers/selectors conventions |

## Routing

```ts
export const routes: Routes = [
  {
    path: "orders",
    canActivate: [authGuard],
    loadChildren: () => import("./orders/orders.routes").then((m) => m.ORDER_ROUTES),
  },
];

export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  return auth.isLoggedIn() ? true : inject(Router).createUrlTree(["/login"]);
};
```

- Use `withComponentInputBinding()` to bind route params to component inputs when the project enables it.
- Resolvers only for data that must exist before render; otherwise load in the component with a
  loading state.

## Forms

- `fb.nonNullable.group({...})` for typed forms; custom validators are pure functions returning
  `ValidationErrors | null`.
- Cross-field validation on the group; async validators debounce and cancel.
- Show errors after `touched` or submit; link messages with `aria-describedby`.

## HTTP

- Interceptors are functional (`HttpInterceptorFn`) in modern code, registered with
  `provideHttpClient(withInterceptors([...]))`.
- Map API DTOs to view models in the service, not in templates.

## Performance

- `@defer (on viewport)` for heavy below-the-fold components (17+).
- `track` expressions in `@for` with a stable id; `trackBy` with `*ngFor`.
- Avoid impure pipes and template method calls; prefer `computed`.

## Testing recipes

| Need | Recipe |
| --- | --- |
| Standalone component | `TestBed.configureTestingModule({ imports: [MyComponent], providers: [...] })` |
| HTTP | `provideHttpClient(), provideHttpClientTesting()` + `HttpTestingController.expectOne` |
| Router | `provideRouter([])` + `RouterTestingHarness` |
| Timers | `fakeAsync` + `tick`; or Jest/Vitest fake timers if the runner is not Karma |
| Material components | Component harnesses (`MatButtonHarness`) |
| User-centric queries | `@testing-library/angular` if present |

## Common review findings

| Finding | Typical severity |
| --- | --- |
| Subscription without cleanup in a long-lived component | MEDIUM |
| `bypassSecurityTrustHtml` on user content | BLOCKER |
| Nested `subscribe` with lost error handling | MEDIUM |
| Default change detection with heavy template calls | LOW to MEDIUM |
| Eagerly loaded feature route | LOW |
