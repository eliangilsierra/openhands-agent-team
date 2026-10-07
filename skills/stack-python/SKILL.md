---
name: stack-python
description: Senior Python engineering for the Developer role - typed, idiomatic code, packaging with uv, Poetry or pip, FastAPI and Django services, Pydantic validation, SQLAlchemy sessions and Alembic migrations, async correctness, logging, and pytest with fixtures, parametrisation and mocks at the boundaries, plus ruff and mypy. Preloaded by developer-python; loaded by QA and reviewers for Python changes.
---

# Stack: Python

## Purpose

Deliver Python that reads clearly, is typed where the project types it, validates data at the
edges, manages resources explicitly, and is tested with focused pytest suites. Adds stack knowledge
to the [development](../development/SKILL.md) procedure.

## When to use

- The task's module has stack `python` in the stack profile.
- QA or a reviewer checks a Pull Request that changes `.py` files, `pyproject.toml`, requirements
  or migrations.

## Inputs

- From the stack profile: Python version (`requires-python`), package manager and the command
  prefix (`uv run`, `poetry run`), frameworks, ruff/black/mypy/pyright configuration, test command.
- The project's layout (`src/` layout or flat), settings management (pydantic-settings, Django
  settings), database access (SQLAlchemy, Django ORM), migrations (Alembic, Django).
- Deep reference: [references/python-services.md](references/python-services.md).

## Procedure

1. **Use the project's environment.** Install with the profile's command (`uv sync --frozen`,
   `poetry install`, `pip install -r ...`) and run everything through the same prefix. Never install
   packages globally or edit the lockfile by hand.
2. **Read the typing bar.** If mypy or pyright runs in strict mode, every new function is fully
   annotated. Use modern syntax allowed by the version (`list[str]`, `X | None`, `match`,
   `typing.Self`, PEP 695 generics on 3.12+).
3. **Validate at the edges.** Pydantic models (or Django forms/serialisers) for request bodies,
   messages and configuration; internal code receives validated, typed objects.
4. **Implement.** Small functions, explicit exceptions (custom exception classes deriving from a
   project base), context managers for resources (`with`), `pathlib` for paths, `logging` with the
   project's logger (no `print`).
5. **Persistence.** Schema changes through a new Alembic revision or Django migration; one session
   per request or unit of work; avoid lazy-loading in loops (`selectinload`, `select_related`,
   `prefetch_related`).
6. **Async.** In async code, never call blocking I/O (use async drivers or `asyncio.to_thread`);
   `asyncio.TaskGroup` (3.11+) for concurrent tasks; timeouts with `asyncio.timeout`.
7. **Test.** pytest with fixtures in `conftest.py`, `@pytest.mark.parametrize` for cases, `tmp_path`,
   `monkeypatch`, `freezegun`/`time-machine` or an injected clock, `httpx.AsyncClient`/`TestClient`
   for FastAPI, Django's test client and `pytest-django` fixtures. Mock only at system boundaries.
8. **Validate.** `run_checks.py`: `ruff check`, `ruff format --check` (or black), mypy/pyright,
   pytest.

## Rules

- No bare `except:` and no `except Exception: pass`; catch the specific exception and handle or
  re-raise with context (`raise DomainError(...) from exc`).
- No mutable default arguments; no module-level mutable state used as a cache without bounds and
  thread-safety thought.
- No SQL built with f-strings or `%` formatting; use bound parameters or the ORM.
- No `eval`/`exec`, `pickle` on untrusted data, `yaml.load` without `SafeLoader`, or
  `subprocess(..., shell=True)` with input.
- Secrets and settings come from the environment through the settings object; never hard-coded.
- Do not add `# type: ignore` or `# noqa` without a specific code and a reason.
- Respect the async/sync boundary: no `asyncio.run` inside running loops; no sync DB driver in async
  endpoints.
- Timezone-aware datetimes (`datetime.now(tz=UTC)`); `Decimal` for money.

## Required outputs

- Code that passes ruff, the type checker and pytest with the project's configuration.
- Tests for each acceptance criterion with parametrised edge cases and error paths.
- Migrations for schema changes, with upgrade and downgrade when the project writes downgrades.

## Quality checklist

- [ ] New code is fully annotated to the project's mypy/pyright level; no unexplained ignores.
- [ ] External data is validated with Pydantic or the framework's validation.
- [ ] Exceptions are specific and chained; nothing is silently swallowed.
- [ ] Resources are managed with context managers; sessions are scoped per unit of work.
- [ ] No blocking calls in async code paths.
- [ ] Tests use fixtures and parametrisation; mocks only at boundaries; no network in unit tests.
- [ ] Lint, format check, type check and tests pass through the project's runner prefix.

## Failure conditions

- The lockfile is out of sync with `pyproject.toml` on `main` → report `BLOCKED` with the command
  output; do not regenerate the lockfile inside the task unless it asks for dependency changes.
- A required service (database, broker) is unavailable for integration tests → run unit tests,
  report the rest `BLOCKED`, and do not replace a real database with SQLite when SQL dialect matters.
- The change needs a Python version bump → stop; propose a separate task.

## Examples

**FastAPI endpoint with Pydantic and dependency injection:**

```python
class CreateInvoice(BaseModel):
    customer_id: UUID
    lines: list[InvoiceLine] = Field(min_length=1)


@router.post("/invoices", status_code=status.HTTP_201_CREATED)
async def create_invoice(
    body: CreateInvoice,
    service: Annotated[InvoiceService, Depends(get_invoice_service)],
    user: Annotated[User, Depends(current_user)],
) -> InvoiceOut:
    try:
        return await service.create(body, owner=user.id)
    except CustomerNotFound as exc:
        raise HTTPException(status_code=404, detail="customer not found") from exc
```

**Parametrised pytest:**

```python
@pytest.mark.parametrize(
    ("lines", "expected"),
    [([10, 20], Decimal("30")), ([0], Decimal("0"))],
)
def test_invoice_total(lines: list[int], expected: Decimal) -> None:
    assert invoice_total([Decimal(v) for v in lines]) == expected


def test_negative_line_is_rejected() -> None:
    with pytest.raises(InvoiceError, match="negative"):
        invoice_total([Decimal("-1")])
```
