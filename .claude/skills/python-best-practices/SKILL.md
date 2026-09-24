---
name: python-best-practices
description: Enterprise Python coding standard for AI agents. Load BEFORE writing, modifying, or reviewing any Python code (.py files, FastAPI routes, SQLAlchemy models, pytest tests, Pydantic schemas, async code, Alembic migrations). Covers architecture layering, naming, type safety, error handling, logging, security, DB access, FastAPI, async, performance, testing, tooling (ruff/black/mypy), and a review checklist.
---

# Python Best Practices (Enterprise Standard)

Opinionated synthesis of the sources catalogued and attributed per rule in references/sources.md,
including the places where this document deliberately diverges from them.
Target runtime: **Python 3.12+**. When this document conflicts with an existing
in-repo convention, follow the repo and say so.

## 1. General Philosophy

- **Readability over cleverness; optimize only with a measurement in hand; delete rather than comment out; prefer the boring stdlib/framework idiom over a novel abstraction.**
- **Explicit over implicit.** No hidden globals, no magic monkey-patching, no `**kwargs` pass-through where real parameters belong.
- **Single Responsibility.** A module has one reason to change — one actor or business function requests changes to it. Applied to functions and classes as a sizing heuristic (this document's extension).
- **Small units.** If you cannot name it precisely, it does too much.
- **Fail loudly, early.** Validate at boundaries; trust data inside the core.
- **Dependencies point inward.** Domain logic never imports web/DB frameworks.

## 2. Project Structure

```
app/
  main.py            # ASGI app factory, middleware, router registration only
  api/               # HTTP layer: routers, dependencies, error handlers
    v1/routes/
    deps.py
  services/          # Use cases / business logic. Orchestrates repositories.
  repositories/      # All persistence access. Only layer that touches Session.
  models/            # SQLAlchemy ORM entities (persistence shape)
  schemas/           # Pydantic request/response DTOs (wire shape)
  domain/            # Pure business types, value objects, domain exceptions (no I/O)
  core/              # Settings, logging config, security, constants
  db/                # Engine/session factory, base metadata, migrations/ (Alembic)
  clients/           # Outbound HTTP/queue/third-party adapters
  utils/             # Small, generic, dependency-free helpers
tests/
  unit/  integration/  e2e/  conftest.py  factories/
```

**Layer rules (enforced in review):**

| Layer | May depend on | Must never |
|---|---|---|
| `api` | `schemas`, `services`, `deps` | touch `Session`, ORM models, or SQL |
| `services` | `repositories`, `domain`, `clients` | import FastAPI, `Request`, or `HTTPException` |
| `repositories` | `models`, `db` | contain business rules |
| `domain` | stdlib only | import SQLAlchemy, FastAPI, Pydantic-web concerns |
| `utils` | stdlib | import `app.*` |

- `models` ≠ `schemas`. Never return an ORM object from a route; map to a response schema.
- One module per aggregate/feature, not one per pattern, once a layer exceeds ~10 files
  (`services/orders/`, `services/invoicing/`).

**Deliberate departures from strict Clean Architecture/DDD** (sources in references/sources.md):

- `services` may depend on `repositories` and receive ORM objects — trading strict dependency
  inversion for far less mapping code. `domain` still imports nothing outward, and ports are
  Protocols owned by the inner layer (§7).
- `models/` is *not* framework-independent; entity behaviour that must be unit-tested without a
  database belongs in `domain/`.
- `services/` means **application** services (use cases). A domain operation that belongs to the
  model but not to a single entity or value object goes in `domain/`, named in the ubiquitous language.

## 3. Naming Conventions

| Kind | Convention | Good | Bad |
|---|---|---|---|
| Module / package | `snake_case`, singular noun | `order_service.py` | `OrderUtils.py`, `helpers2.py` |
| Class | `PascalCase` noun | `CreditLimitPolicy` | `credit_mgr`, `DoStuff` |
| Function / method | `snake_case` verb phrase | `reserve_inventory()` | `inventory()`, `handleIt()` |
| Boolean | `is_/has_/can_/should_` | `is_credit_blocked` | `flag`, `status2` |
| Variable | `snake_case`, domain word | `unpaid_invoices` | `data`, `tmp`, `l`, `res` |
| Constant | `UPPER_SNAKE` at module top | `MAX_RETRY_ATTEMPTS` | `maxRetries` |
| Enum | `PascalCase` class, `UPPER_SNAKE` members | `OrderStatus.AWAITING_CREDIT` | `OrderStatus.s1` |
| Private | leading `_` | `_normalize_gstin()` | `normalizeGSTIN2()` |
| Type alias | `PascalCase` | `type OrderId = int` | `orderid_t` |
| Test | `test_<unit>_<scenario>_<expected>` | `test_reserve_inventory_when_out_of_stock_raises()` | `test_1()` |

- Never rebind a builtin in a scope that also uses it (`type`, `list`, `input`, `dict`, `filter`);
  the fix for a keyword clash is a trailing underscore (`class_`). `id` as a model attribute, dict
  key, or path parameter is the accepted exception: there it reads as the domain word, not the builtin.
- Don't encode the type in the name (`id_to_name_dict`, `order_list`).
- Units and currency belong in the name: `timeout_seconds`, `amount_inr_paise`.

## 4. Imports

- **Absolute imports only** for first-party code: `from app.services.orders import OrderService`.
  Relative imports are acceptable only inside a tightly-cohesive package (`from .policy import ...`).
- Import ordering enforced by ruff/isort; one import per line for modules. No wildcard imports (F403).
- Import modules or explicit names, not "everything from a barrel". Keep `__init__.py` thin;
  re-export a curated public API only, and define `__all__` when you do.
- `if TYPE_CHECKING:` for import-only-for-annotations; combine with `from __future__ import annotations`
  when needed for forward refs.
- **Circular dependencies are a design smell, not an import problem.** Fix by moving the shared
  type into `domain/`, or by depending on a Protocol defined in the inner layer and implemented
  outward. Local (function-scoped) imports are a last resort and must carry a comment saying why.
- No side effects at import time: no DB connections, no network calls, no `load_dotenv()` in library modules.

## 5. Functions

- **Target ≤ 30 lines, ≤ 4 parameters, cyclomatic complexity ≤ 8.** Past that, extract. House
  numbers; nothing in the §16 gate counts parameters, and complexity is measured only via `C90` (§16).
- **Type hints are mandatory** on every parameter and return value, including `-> None`.
- Keyword-only for optional/boolean parameters: `def send(*, dry_run: bool = False) -> None:`.
  Never pass a bare boolean positionally.
- Return early; avoid deep nesting. Prefer a guard clause over `else`.
- One return type. Don't return `Order | None | bool` — raise instead of returning a sentinel.
- **Prefer pure functions** for calculation; isolate I/O in thin shells ("functional core, imperative shell").
- No output parameters (don't mutate caller-owned arguments) unless the name says so (`_in_place`).

```python
def allocate_credit(
    order: Order,
    profile: CreditProfile,
    *,
    allow_override: bool = False,
) -> CreditDecision:
    """Decide how much credit to grant for an order.

    Args:
        order: Order awaiting credit clearance.
        profile: Customer's current credit standing.
        allow_override: Permit exceeding the sanctioned limit for priority accounts.

    Returns:
        The granted amount and the reason code driving the decision.

    Raises:
        CreditProfileStaleError: If the profile snapshot predates the order.
    """
```

## 6. Classes

- Create a class when behaviour and state travel together, or to satisfy a Protocol/port.
  **A class with one method and no state should be a function.**
- **One class per file.** Each class lives in its own module, named after the class in
  snake_case (`OrderService` → `order_service.py`); five classes means five files. The only
  exception is a private helper (e.g. a small frozen dataclass) used exclusively by the
  class it sits next to.
- `@dataclass(frozen=True, slots=True)` for value objects; Pydantic `BaseModel` only at
  I/O boundaries (validation/serialization); plain classes for services with injected collaborators.
- **Composition over inheritance.** Inherit only for genuine `is-a` or to implement an ABC.
  Depth ≤ 2. No mixin stacks that share mutable state.
- **Dependency Injection via `__init__`.** Never construct collaborators (sessions, HTTP clients,
  settings) inside a class — accept them. This is what makes tests cheap.
- No God objects: a class over ~200 lines or with >7 public methods is being split.
- `@property` for cheap derived reads only; anything with I/O or cost is a method.
- Define `__repr__` for debuggability; never put secrets in it.

```python
class OrderService:
    def __init__(
        self,
        orders: OrderRepository,
        credit: CreditPolicy,
        events: EventPublisher,
    ) -> None:
        self._orders = orders
        self._credit = credit
        self._events = events
```

## 7. Type Safety

- Annotate everything public. mypy runs in **strict** mode — `strict = true` under `[tool.mypy]` in
  `pyproject.toml`, or `mypy --strict` — and new code must not add ignores. Pin the mypy version (§16).
- Modern syntax: `list[str]`, `dict[str, int]`, `str | None`, `type Alias = ...` (PEP 695).
  Not `List`, `Dict`, `Optional[str]`, `Union[...]`.
- `X | None` means "genuinely absent". Don't use it to dodge error handling.
- **`Protocol` for ports** (structural typing) instead of ABCs, so the inner layer owns the interface
  and outer adapters satisfy it without importing it.
- Generics via PEP 695: `class Repository[T]: ...`, `def first[T](items: Sequence[T]) -> T | None: ...`.
- `TypedDict` for fixed-shape dicts crossing boundaries (external JSON); `NewType` for IDs
  (`CustomerId = NewType("CustomerId", int)`) to stop mixing them up. `NewType` is not a type alias:
  the PEP 695 `type` statement cannot express it, and you cannot `isinstance()`, `issubclass()`, or
  subclass the result.
- `Literal` + `Enum` instead of magic strings. `Final` for module constants.
- **`Any` requires a comment justifying it.** `object` + narrowing, or `cast()` at a single
  well-marked seam, is preferred. `# type: ignore[code]` must name the error code and a reason.
  A review rule, not a tool result — `mypy --strict` does not ban explicit `Any`; enforce it
  mechanically via mypy's `disallow_any_explicit` (outside `--strict`) or Ruff's `ANN401` (§16).
- Narrow with `assert isinstance(...)` only in tests; in production use explicit checks that raise.

## 8. Error Handling

- Define a small exception hierarchy per bounded context, rooted in one app base:

```python
class AppError(Exception):
    """Base for all application errors."""


class DomainError(AppError):
    """Business rule violated — caller's input is semantically wrong."""


class CreditLimitExceededError(DomainError):
    def __init__(self, requested: Decimal, available: Decimal) -> None:
        super().__init__(f"requested {requested} exceeds available {available}")
        self.requested = requested
        self.available = available
```

- **Raise domain exceptions from services; translate to HTTP only in the API layer**
  (`@app.exception_handler`). Services must not know status codes.
- Catch the **narrowest** exception type. `except Exception` is permitted only at a top-level
  boundary (request handler, worker loop, CLI entrypoint) and must log with `exc_info=True` and re-raise or fail the unit of work.
- **Never swallow.** If an error is truly ignorable, log at `debug` and comment why.
- **Always chain:** `raise OrderNotFoundError(order_id) from exc`. Use `from None` only to
  deliberately hide an internal cause from a caller.
- Error messages: state what failed and the identifying value; **never** include secrets, tokens,
  PII, or raw SQL.
- `try` blocks wrap the smallest possible statement set. Cleanup via `finally` or context managers,
  not duplicated code.
- Retries only for genuinely transient faults, with bounded attempts + jittered backoff + idempotency.

## 9. Logging

- One module-level logger: `logger = logging.getLogger(__name__)`. **`print()` is banned** in
  application code (CLI user-facing output excepted).
- **Structured logging** — key/value extras, not string concatenation, so logs are queryable:
  `logger.info("order_credit_blocked", extra={"order_id": order.id, "shortfall": str(gap)})`.
- Use lazy `%s` formatting (`logger.info("synced %s rows", n)`) — never f-strings in log calls.
- **Correlation IDs**: generate/propagate a request ID in middleware, store in a `ContextVar`,
  inject into every log record via a `logging.Filter`, and forward it on outbound calls
  (`X-Request-ID`).
- **Mask sensitive data** at the logging layer (a redacting filter), not by trusting call sites.
  Never log: passwords, tokens, API keys, full card/bank numbers, OTPs, auth headers, full request bodies.
- **Log security events, not only business ones:** authentication successes *and* failures,
  authorization failures, input-validation failures, and access to sensitive data — each with the
  actor, the source, and the correlation ID (OWASP requires all four).
- Levels: `DEBUG` dev detail · `INFO` business milestones · `WARNING` recoverable/degraded ·
  `ERROR` failed operation needing attention · `CRITICAL` process-level failure. No `INFO` inside loops.
- Configure handlers/format **once** at app startup (`core/logging.py`); libraries and modules
  never call `basicConfig`.

## 10. Security (OWASP)

- **Injection:** parameterized queries / ORM constructs only. Never f-string or `%` user input into
  SQL, shell, LDAP, or template strings. If raw SQL is unavoidable, use `text()` with bound params.
- **Command execution:** `subprocess.run([...], shell=False)` with a list argv. `shell=True`,
  `os.system`, `eval`, `exec`, `pickle.loads` on untrusted data are banned.
- **Secrets:** a secret manager wherever one exists, environment variables otherwise, loaded through
  a typed `Settings` (`pydantic-settings`). **No hardcoded credentials, keys, or connection strings**
  — not even in tests, defaults, or comments. Never commit `.env`. Use `SecretStr`, keep secrets out
  of `repr`/logs/tracebacks, and **rotate on a schedule**.
- **Input validation** at the boundary with Pydantic: exact types, `constr`/`Field` bounds,
  `extra="forbid"`, allow-lists over deny-lists. File uploads: **allow-list the permitted extensions**,
  confirm the **content matches that extension** (magic bytes, or a content-validation library), and
  enforce a **size limit**. Never trust the client-supplied `Content-Type` — it is trivial to spoof.
- **AuthN:** vetted libraries only. Password hashing in OWASP's stated order of preference:
  **Argon2id** (m ≥ 19 MiB, t = 2, p = 1; ASVS Appendix C's approved setting is t = 1, m ≥ 46 MiB,
  p = 1 — take the stricter); **scrypt** (N ≥ 2^17, r = 8, p = 1) if Argon2id is unavailable;
  **bcrypt** (cost ≥ 10, 72-byte input limit) for legacy systems only; and **PBKDF2-HMAC-SHA-256 at
  ≥ 600,000 iterations** (or SHA-512 at ≥ 210,000) where FIPS-140 compliance is required. Never a
  *bare* fast hash (MD5, SHA-1, plain SHA-2) — the ban is on the bare fast hash, not on PBKDF2.
  A hash named without its work factor is not reviewable.
- **Credential policy:** minimum 8 characters, 15 strongly recommended where MFA is absent; permit at
  least 64; no composition rules; bind the failed-login counter to the account rather than the source
  IP; constant-time comparison; generic login errors; MFA where feasible.
- JWTs: verify signature + `alg` + `aud` + `iss` + `exp`; short TTL; no secrets in the payload. Use
  `secrets`, never `random`, for tokens; compare with `hmac.compare_digest`.
- **AuthZ:** enforce on every endpoint via a dependency; **deny by default**. Check object-level
  ownership/tenancy in the service or repository query (`WHERE tenant_id = :tenant`), not just role —
  IDOR is the default bug otherwise.
- **Output encoding:** let the framework serialize JSON; autoescape templates; never build HTML by
  concatenation. Set security headers — HSTS, a CSP with `frame-ancestors`,
  `X-Content-Type-Options: nosniff`, `Referrer-Policy` — and a strict CORS allow-list: **no wildcard
  origin on any response carrying sensitive data** (a stricter bar than "not with credentials"), and
  never `allow_origins=["*"]` with credentials.
- **Transport & data:** TLS with certificate verification on (never `verify=False`), encrypt sensitive
  data at rest, minimize PII collected and retained.
- **SSRF/path traversal:** validate and allow-list outbound URLs; resolve and confine file paths
  (`Path.resolve().is_relative_to(base)`).
- Generic error responses to clients; details to logs. No stack traces or SQL in API responses;
  `DEBUG=False` in production.
- Pin dependencies with a lockfile; run `pip-audit`/`safety` and `ruff`'s security rules (`S`, i.e. bandit) in CI.

## 11. Database (SQLAlchemy 2.0 + Alembic)

- **Repository pattern:** repositories expose intent-named methods
  (`find_unpaid_by_customer(customer_id)`), return domain/ORM objects, and are the **only** place
  `Session`/`select()` appears. No `Session` in routers or services' signatures beyond passing it to repos.
  A house layering rule (§2), **not** a framework one — FastAPI's own SQL tutorial injects the session
  straight into the path operation. Follow it because it keeps services testable without a database.
- **2.0 style:** `select()` executed via `session.scalars(stmt)` (or the equivalent
  `session.execute(stmt).scalars()`). `DeclarativeBase` with `Mapped[...]` / `mapped_column(...)`.
  Avoid legacy `Query` and implicit autoflush surprises.
- **Transactions:** one transaction per unit of work, owned by the **service** (or a
  `unit_of_work` context manager) — repositories never commit. Use `with session.begin():` and let
  exceptions roll back. Never `commit()` inside a loop over records. A unit of work touching many
  aggregates is a review signal — the aggregate boundaries are probably wrong, and cross-aggregate
  consistency should be asynchronous.
- **Session lifecycle:** one session per request via a FastAPI dependency — `yield` inside
  `with Session(engine) as session:` (the shape the current FastAPI tutorial uses) or the older
  `try` / `yield` / `finally: close()`; both are documented, pick one per repo. Never a module-global
  session; sessions are not thread/task-safe.
- **Pooling:** configure `pool_size`, `max_overflow`, `pool_pre_ping=True`, `pool_recycle` — with
  stated values, and only where they apply. `pool_size` and `max_overflow` are `QueuePool`
  (`AsyncAdaptedQueuePool` under `create_async_engine`) settings: `max_overflow` "is only used with
  QueuePool", and neither means anything on `NullPool` or on the `SingletonThreadPool` used for SQLite
  `:memory:` — a common test configuration. SQLAlchemy 2.0 defaults you are overriding: `pool_size=5`,
  `max_overflow=10`, `pool_recycle=-1`, `pool_pre_ping` off.
- **Parameterized always.** `text("... WHERE id = :id")` with `{"id": id}`.
- **Relationships:** set `lazy="raise"` by default so N+1 fails loudly, and load explicitly with
  `selectinload`/`joinedload`. `raise_on_sql` is a *different* documented value, not a synonym — read
  the loading-techniques page before choosing it. The guarantee is not total: raise-loading "does not
  apply within the unit of work flush process", so a lazy load that `Session.flush()` needs in order
  to finish its work still goes through. Always define `back_populates` and an explicit
  `cascade`/`passive_deletes` policy.
- **Concurrency:** use `with_for_update()` or optimistic versioning (`version_id_col`) for
  read-modify-write on money/stock. Make writes idempotent where retries are possible.
- **Migrations:** every schema change ships a reviewed Alembic revision with a working, tested
  `downgrade()` — autogenerate then **hand-edit**. Backfills are separate, batched, idempotent scripts.
  Expand → migrate → contract for zero-downtime: never rename/drop a column in the same release that
  stops using it, and no destructive DDL without an explicit sign-off note.
- Money as `Numeric`/`Decimal` (or integer minor units) — never `float`; timestamps timezone-aware UTC.
  Index every FK and hot `WHERE`/`ORDER BY` column; `UNIQUE` for real business keys; constraints in
  the DB, not only in Python.

## 12. FastAPI

- **Thin routers.** A handler validates input via schema, calls one service method, returns a
  response model. Target ≤ 15 lines and **zero** business logic, `if` chains, or SQL.
- **Never touch the database from a router.** Route → service → repository, always (§2, §11).
- **Dependency Injection** for session, current user, settings, and services (`Annotated[X, Depends(...)]`).
  Use `dependencies=[Depends(require_role(...))]` at router level for cross-cutting auth.
- **Response models** on every route: annotate the return type (`-> OrderOut`) — that buys editor and
  mypy checking on top of FastAPI's filtering — and use `response_model=OrderOut` only where the
  response genuinely differs from what the function returns (`response_model` wins if both are
  present). Always set `status_code=...` explicitly, and `response_model_exclude_none` where useful.
  Separate `...In` / `...Out` / `...Patch` schemas — never accept the same model you emit, and never
  expose ORM objects or internal fields.
- Register `@app.exception_handler` for `DomainError`, validation errors, and a catch-all → RFC-7807
  style JSON. Don't scatter `HTTPException` through services.
- `async def` handlers when the work is I/O-bound and awaitable — **and also when the handler does no
  I/O at all** (plain `def` is worse for trivial compute-only handlers). Use **plain `def` when the
  work is blocking** (FastAPI runs it in a threadpool) — a blocking call inside `async def` stalls
  the loop. Unsure: plain `def`.
- **BackgroundTasks** only for short, fire-and-forget, failure-tolerant work (emails, cache warm).
  Anything retryable, long, or business-critical goes to a real queue/worker — `BackgroundTasks` has
  no retry, no visibility, and dies with the process.
- Pagination (`limit`/`offset` or cursor) and explicit `max` bounds on every list endpoint.
- Lifespan context manager for startup/shutdown; version the API (`/api/v1`); tag and document routes.
- Middleware for request ID, timing, and error boundary — not for business rules.

## 13. Async Programming

- Async for **I/O-bound concurrency** (HTTP, DB, queues). CPU-bound work goes to
  `ProcessPoolExecutor` or a worker, never inline in the event loop.
- **Never block the loop:** no `time.sleep`, `requests`, blocking DB drivers, or heavy file I/O in
  `async def`. Use `asyncio.sleep`, `httpx.AsyncClient`, async drivers (`asyncpg`), or wrap legacy
  blocking calls in `await asyncio.to_thread(...)`.
- **Don't mix stacks.** One project, one choice: sync SQLAlchemy + sync routes, or `AsyncSession` +
  async routes. `AsyncSession` is not shareable across concurrent tasks.
- Concurrency with `asyncio.TaskGroup` (3.11+) — it propagates errors and cancels siblings.
  `gather(..., return_exceptions=True)` only when you deliberately handle partial failure.
- Never fire-and-forget a bare `asyncio.create_task` — keep a reference, await it, or use a TaskGroup,
  or it gets garbage-collected and its exception vanishes.
- Every outbound call gets a timeout (`asyncio.timeout()` / client timeout). Treat
  `asyncio.CancelledError` as cancellation: clean up and re-raise, never swallow it.
- Reuse one `AsyncClient`/pool for the app lifetime; use `async with` for all async resources.
- Guard shared mutable state with `asyncio.Lock`; use `ContextVar` (not globals) for request-scoped context.

## 14. Performance

- **N+1 is the default bug.** Eager-load with `selectinload`, or fetch parents then children in one
  `IN` query. `lazy="raise"` makes violations impossible to miss.
- Select only the columns you need for wide tables (`select(Order.id, Order.total)`) — on the **read**
  path only. DDD warns that unconstrained queries "may pull specific fields from objects, breaching
  encapsulation" and leave "the entities and value objects … mere data containers", so confine partial
  selects to read models and projections that feed a response schema, and never mutate through one:
  writes go through a fully loaded aggregate. (`lazy="raise"` also forecloses the lazy-proxy
  repository option DDD explicitly permits — a deliberate trade for loud N+1 detection.)
- **Bulk operations** for volume: `insert().values([...])`, `session.execute(update(...))`,
  `bulk_insert_mappings`, `COPY` for very large loads. Never a per-row loop with a commit.
- **Pagination everywhere** — keyset/cursor pagination for large or deep result sets (`OFFSET` degrades linearly).
- **Stream, don't accumulate:** generators, `yield`, `session.stream()`/`yield_per()`, chunked file
  reads, `StreamingResponse` for large exports. Never `.all()` an unbounded table into memory.
- **Cache** with an explicit key, TTL, and invalidation story: `functools.lru_cache`/`cache` for pure
  in-process functions, Redis for shared/cross-process. Never cache per-user data under a global key.
- Prefer set/dict lookups over list scans in loops; hoist invariant work out of loops; use
  `__slots__`/frozen dataclasses for high-cardinality objects.
- Measure before optimizing (`cProfile`, `EXPLAIN ANALYZE`, timing logs) and state the numbers in
  the PR. Add an index before adding a cache.

## 15. Testing

- **pytest** only. `tests/` mirrors `app/`. `test_<module>.py`, `test_<unit>_<scenario>_<expected>()`.
- **AAA structure** (arrange/act/assert), one behaviour per test, assert on outcomes not internals.
- **Unit tests** for services/domain: fast, no DB, no network — fake repositories via Protocols.
- **Integration tests** for repositories/migrations/routes: real DB (testcontainers or a disposable
  schema), transaction-rollback fixtures for isolation, `TestClient`/`httpx.ASGITransport` for the app.
- **Mock at the boundary you own** (repository, client interface) — not deep internals, and never
  mock the thing under test. Prefer fakes/stubs over `MagicMock` for anything with behaviour.
  `respx`/`responses` for HTTP; never hit real third parties.
- **Cover the edges:** empty, one, many; boundary values; `None`/missing; duplicates; unicode;
  Decimal rounding; timezone/DST; concurrent update; permission denied; upstream timeout;
  and every raised exception path.
- Deterministic: freeze time (`freezegun`/injected clock), seed randomness, no `sleep`, no ordering
  dependence between tests, no shared mutable module state.
- `pytest.mark.parametrize` instead of copy-pasted cases. Factories/builders (`factory_boy` or plain
  helpers) instead of giant literal fixtures. Markers for `slow`/`integration` — and **register every
  custom marker** in `[tool.pytest.ini_options] markers = [...]`, with strict marker validation on:
  pytest "will always emit a warning" for an unregistered mark, so §16's zero-warnings gate fails
  otherwise.
- **Coverage: ≥ 85% overall (house number), ~100% on services/domain**, and every bug fix ships a
  regression test that fails before the fix. Coverage is a floor — assertions matter more than lines.

## 16. Code Quality Gates

Before code is "complete", all of these pass locally and in CI:

```bash
ruff format .                 # formatting (or: black .)
ruff check --fix .            # local: lint + safe autofixes only
ruff check .                  # CI: no --fix; a clean --fix run is not a passing gate
mypy --strict app             # strict: no new ignores, no untyped defs
pytest --cov=app --cov-fail-under=85 -q   # --cov* come from pytest-cov; declare that dependency
pip-audit                     # known CVEs in dependencies
alembic upgrade head          # migrations apply cleanly (+ downgrade tested)
```

- **Rule selection:** `E,F,I,N,UP,B,S,SIM,C4,RET,ARG,PTH,ASYNC,ANN`, plus `C90` with
  `[tool.ruff.lint.mccabe] max-complexity = 8` if you want §5's complexity limit actually measured.
  The `select` list earns its keep: `ANN` is off by default and `S` is only partly on. Two caveats.
  Ruff's formatter docs name `E111`, `E114`, `E117`, `W191` and `E501` as conflicting with the
  formatter, so either narrow `E` to `E4,E7,E9` or add those five codes to `lint.ignore` — otherwise
  the gate lints against the formatter this section just made authoritative. Ruff's own default set
  goes further than either fix: it enables no `E4` rule at all and takes only `E722` and `E902` from
  pycodestyle, "omitting any stylistic rules that overlap with the use of a formatter". So `E4,E7,E9`
  is a wider selection than the default, not a copy of it. And most `S` and `ANN` findings have no
  safe fix, so `--fix` will not clear them: run `--fix` locally, plain `ruff check .` in CI.
- **Config lives in `pyproject.toml`. Line length 100** (or the repo's existing value; 88 is a
  perfectly good default). Set it explicitly under `[tool.ruff]` / `[tool.black]`, or the mandated
  commands quietly enforce 88 instead. Ruff documents `line-length` as "not a hard upper bound", so
  `E501` at the same number can still fail a formatted file.
- Keep comments and docstrings visibly narrower than code by hand — the formatters do not reflow prose.
- Black/ruff-format is the sole authority on **code** formatting — never hand-format or argue with it.
- Pin the ruff, black, and mypy versions in `pyproject.toml`. mypy states that the flag set behind
  `--strict` "may change over time", so an unpinned type-check gate is not reproducible across
  upgrades.
- Pre-commit hooks run format, lint, type-check, and secret detection.
- **Zero warnings, zero skipped tests, zero new `# noqa`/`# type: ignore` without a reason comment.**
  A failing gate is not "unrelated" until proven so.

## 17. Documentation

- **Docstrings on every public module, class, and function — and on public methods, including
  `__init__`.** One-line summary in the **imperative** mood ("Return that", not "Returns that"), then
  `Args:` / `Returns:` (or `Yields:`) / `Raises:` sections. The sections may be omitted where the
  name and signature are informative enough, and a trivial function may skip the docstring.
- Document every exception that is **part of the function's contract** — not every exception it can
  raise: the `ValueError` from an argument precondition stays out of `Raises`.
- Docstrings say **why and what contract**; the code already says how. Never restate the signature.
- **Inline comments only for non-obvious rationale** — a business rule, a workaround with a link, a
  deliberate perf trade-off. Delete commented-out code and "TODO" without an owner/ticket.
- Update the README/`docs/` when you add a setup step, env var, command, or service. New env vars are
  documented in `.env.example` in the same change.
- FastAPI: `summary`, `description`, `response_model`, `responses={...}` and schema `Field(examples=...)`
  so OpenAPI is the API doc. Keep it truthful — a stale example is worse than none.
- Record non-obvious architectural decisions as a short ADR in `docs/adr/`.
- Type hints replace type documentation; keep both consistent or drop the prose.

## 18. AI Agent Rules

When writing or modifying Python, the agent **must**:

1. **Read before writing.** Inspect neighbouring modules and match existing patterns, naming, and libraries.
2. **Never invent business rules.** If credit limits, tax treatment, rounding, statuses, or SLAs are ambiguous, **ask** — do not guess and do not silently pick a default.
3. **State assumptions explicitly** in the response when proceeding under uncertainty, and mark them in code with a comment only where they affect behaviour.
4. **Keep changes minimal and focused.** No drive-by refactors, no reformatting untouched files, no renaming public APIs unasked. One logical change per commit, imperative subject line, and no commits unless the user asked.
5. **Preserve backward compatibility** on public APIs and DB schemas; if a break is unavoidable, say so loudly and propose the expand/contract path.
6. **Do not add dependencies** without saying why and confirming; prefer stdlib.
7. **Run the gates** (format, lint, mypy, tests) and report real output. Never claim verification you didn't perform; if a gate fails, say so with the output.
8. **Delete dead code you create**; don't leave scaffolding or debug output behind. Never edit an applied Alembic revision.
9. **Flag anything security-relevant** you touch (auth, tenancy, input handling, SQL, file paths, outbound URLs) in the summary.

## 19. Review Checklist

For an AI reviewer. Flag only real defects; cite `file:line` and state the failure scenario.

**Architecture** — layer boundaries respected? DB only from repositories? services free of framework imports? no circular deps? one class per file, module named after it? units within house limits (function ≤30 lines, class ≤200)? duplication to extract — or premature abstraction?

**Security** — any string-interpolated SQL/shell/path? secrets or tokens hardcoded or logged? input validated at the boundary with bounds and `extra="forbid"`? authn *and* object-level authz (tenant/owner) enforced on every new endpoint? `verify=False`, `shell=True`, `eval`, `pickle`? errors leaking internals to clients?

**Type safety** — full annotations? new `Any`/`cast`/`# type: ignore` justified? `X | None` handled at every use? `mypy --strict` clean (it does not flag explicit `Any`)?

**Error handling** — narrowest exception caught? nothing swallowed? chained with `from`? domain errors mapped to HTTP once, in the API layer? messages free of secrets/PII?

**Logging** — no `print`? structured extras, lazy formatting? correlation ID present? sensitive fields masked? security events (authn success/failure, authz failure, validation failure, sensitive-data access) logged? level appropriate and not logging inside hot loops?

**Database** — transaction boundary owned by the service, one per unit of work? no commit in a loop? session lifecycle bound to the request? migration included with a real `downgrade`? indexes/constraints for new columns and FKs? `Decimal` for money, UTC-aware datetimes? concurrent-update safety on balances/stock?

**Performance** — N+1 introduced? unbounded query or `.all()` on a large table? missing pagination? per-row loop that should be bulk? cache key/TTL/invalidation sound? large payload streamed?

**Testing** — new logic covered, including error paths and edge cases? tests deterministic (no time/random/sleep/order dependence)? asserting behaviour, not implementation? mocks at owned boundaries only? regression test present for a bug fix?

**Readability** — names precise, domain-accurate, no shadowed builtins? magic numbers/strings replaced by constants/enums? nesting shallow, early returns? dead code, stray debug, commented-out blocks removed?

**Backward compatibility** — public API/response shape/schema changes? nullable-vs-required flips? default behaviour changes? expand/contract path for destructive DDL?

**Documentation** — docstrings on new public surfaces, `Raises` listing the contract's exceptions and no more? new env vars in `.env.example`? README/OpenAPI updated? comments explain *why*?

**Linting** — format/ruff/mypy/pytest all green; no new suppressions without a reason.
