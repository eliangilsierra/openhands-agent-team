# Python services: reference

Load this file for framework, database, async, packaging or testing details. It complements
[the stack skill](../SKILL.md).

## Framework idioms

| Framework | Structure | Validation | Tests |
| --- | --- | --- | --- |
| FastAPI | Routers per resource, dependencies for sessions and auth, services below | Pydantic models in signatures | `TestClient` or `httpx.AsyncClient(transport=ASGITransport(app))`, `app.dependency_overrides` |
| Django | Apps per domain; views thin, logic in services or model methods | Forms, DRF serialisers | `pytest-django` (`client`, `db`), `APIClient` for DRF |
| Flask | Blueprints, application factory | marshmallow or Pydantic | `app.test_client()` |

- FastAPI: declare `response_model` (or return type) so output is filtered; never return ORM objects
  with relationships the client must not see.
- Django: `select_related` for foreign keys and `prefetch_related` for reverse/many-to-many in lists;
  `transaction.atomic()` for multi-step writes; `F()` expressions for race-free counters.

## SQLAlchemy 2.0

```python
async with session_factory() as session, session.begin():
    stmt = select(Order).where(Order.customer_id == customer_id).options(selectinload(Order.lines))
    orders = (await session.scalars(stmt)).all()
```

- Typed models with `Mapped[...]` and `mapped_column`.
- One session per request (dependency with `yield`), committed by the unit of work, never shared
  across threads or tasks.
- Alembic: `alembic revision --autogenerate -m "..."`, then read and fix the generated script; never
  edit an applied revision.

## Async

| Need | Use |
| --- | --- |
| Run independent coroutines | `async with asyncio.TaskGroup() as tg: tg.create_task(...)` |
| Timeout | `async with asyncio.timeout(5):` |
| Call blocking library | `await asyncio.to_thread(fn, *args)` |
| Bound concurrency | `asyncio.Semaphore(n)` |
| HTTP client | One shared `httpx.AsyncClient` with timeouts, closed on shutdown |

## Settings

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BILLING_", env_file=".env")
    database_url: PostgresDsn
    provider_timeout: float = 5.0
```

- Instantiate once (cached dependency); validate at startup; never read `os.environ` deep in code.

## Packaging

| Manager | Install | Add dependency | Run |
| --- | --- | --- | --- |
| uv | `uv sync --frozen` | `uv add <pkg>` | `uv run <cmd>` |
| Poetry | `poetry install` | `poetry add <pkg>` | `poetry run <cmd>` |
| pip + requirements | `python -m pip install -r requirements.txt` | edit the requirements file with a pinned version | `python -m <tool>` |

- New dependencies: `deps_check.py --ecosystem pypi --name <pkg>` first.
- Never commit virtual environments or `__pycache__`.

## pytest recipes

| Need | Recipe |
| --- | --- |
| Shared setup | Fixtures in `conftest.py` with the narrowest scope that works |
| Many cases | `@pytest.mark.parametrize` with ids |
| Files | `tmp_path` |
| Environment | `monkeypatch.setenv` |
| Time | `time-machine`/`freezegun` if present, or inject a clock |
| HTTP out | `respx` (httpx) or `responses` (requests) if present |
| Async tests | `pytest-asyncio` or `anyio` marker as configured |
| Database | Transactional fixture that rolls back; Testcontainers for real engines |

## Common review findings

| Finding | Typical severity |
| --- | --- |
| SQL via f-string | BLOCKER |
| `yaml.load`/`pickle` on untrusted input | BLOCKER |
| Blocking call in async endpoint | MEDIUM to HIGH |
| Bare `except` | MEDIUM |
| N+1 queries in list views | MEDIUM |
| Mutable default argument | LOW to MEDIUM |
