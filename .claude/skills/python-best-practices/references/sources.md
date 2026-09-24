# Python Best Practices (Enterprise Standard) — Sources

Provenance for [`../SKILL.md`](../SKILL.md). This file is deliberately kept
out of the skill body so it costs no tokens at load time; read it to verify a
rule, not to follow one. Repository-wide provenance tiers and known gaps:
[SOURCES.md](../../../SOURCES.md).

Throughout this file, "this document" and section references like §4 point to
`../SKILL.md`, whose rules these sources support. This text was moved out of that
file verbatim, so "the rules above" likewise means the rules there.


This document was written on **2026-07-31** as a synthesis of established standards, from practice and
memory: no URLs were captured, and no page was open while it was written. The references below were
retrieved and read on **2026-08-20** to put that provenance on a verifiable footing. Every page listed
here was actually opened on that date; nothing is listed on the strength of a search result. That pass
also exposed places where this document diverges from a source it names — those are now stated at the
rule itself, not smoothed over here.

**Language and style**

- [PEP 8 — Style Guide for Python Code](https://peps.python.org/pep-0008/) — the casing conventions in
  §3 ("function names should be lowercase, with words separated by underscores", "class names should
  normally use the CapWords convention", constants "written in all capital letters with underscores"),
  the `l`/`O`/`I` single-character prohibition, and the trailing-underscore remedy for keyword clashes
  ("`class_` is better than `clss`"). Also the source §16 diverges from: 79 characters for code, 72 for
  comments and docstrings, 99 only by team agreement. It supplies nothing in §17 beyond the existence
  of docstrings, and does **not** define `Args`/`Returns`/`Raises`. A living "Active" PEP with no
  version number; page footer read "Last modified: 2025-04-04". Checked 2026-08-20.
- [PEP 257 — Docstring Conventions](https://peps.python.org/pep-0257/) — §17's three real PEP 257
  rules: docstrings on modules, on everything a module exports, and on public methods including
  `__init__`; the imperative-mood requirement; the one-line-summary shape; and "the one-line docstring
  should NOT be a 'signature' reiterating the function/method parameters". Its documentation
  requirement is content-level only — summarize behaviour and document arguments, return values, side
  effects and exceptions — with **no** named-section syntax. Footer read "Last modified: 2024-04-17".
  Checked 2026-08-20.
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) — the actual source of
  §17's docstring *format* (3.8.3: `Args:`, `Returns:`/`Yields:`, `Raises:`, the mandatory-docstring
  trigger, the "not every exception" rule), §3's naming table and "names to avoid" (3.16.1, 3.16.2,
  3.19.6 for CapWords type aliases), §5's mutable-default ban (2.12.4), and §17's TODO-needs-a-ticket
  rule (3.12). Also the 80-character limit §16 diverges from, and the "about 40 lines" soft guidance
  §5 tightens to 30. The page publishes no version or revision date; it was dated indirectly from the
  upstream `google/styleguide` commit for `pyguide.md` (latest `ff7ea9c951eb`, 2025-02-24), so treat
  "current" with that caveat. Note it recommends pylint as the linter, which this document does not
  use. Checked 2026-08-20.

**Formatting, linting, typing**

- [Black — The Black code style: Current style](https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html)
  — Black's default line length of 88 and its rationale, its explicit caution about lines beyond 100
  characters, and "style configuration options are deliberately limited and rarely added", which is
  what backs §16's "the formatter is the sole authority". Docs "stable" channel, self-reported Black
  26.5.1. Checked 2026-08-20.
- [Ruff — Rules](https://docs.astral.sh/ruff/rules/) — confirms all fourteen rule families §16 selects
  exist and are what the comment claims (`E` pycodestyle, `F` Pyflakes, `I` isort, `N` pep8-naming,
  `UP` pyupgrade, `B` bugbear, `S` bandit, `SIM`, `C4` comprehensions, `RET`, `ARG`, `PTH`, `ASYNC`,
  `ANN`). No invented codes. Checked 2026-08-20.
- [Ruff — Settings](https://docs.astral.sh/ruff/settings/) — `line-length` defaults to 88, governs
  `E501` and where the formatter and isort wrap, and "isn't a hard upper bound, and formatted lines may
  exceed the line-length". Both facts are load-bearing in §16. Checked 2026-08-20.
- [Ruff — Default rules](https://docs.astral.sh/ruff/default-rules/) — what is on without
  configuration, and the reason §16's explicit `select` list is not redundant. The page publishes the
  default as an enumeration of individual codes (413 of them on this reading), not of families, so
  "family X is on by default" is nearly always false: isort contributes only `I001`, pep8-naming only
  `N999`, flake8-bandit only `S102`/`S110`/`S112`, flake8-return only `RET501`, flake8-use-pathlib only
  `PTH124`/`PTH210`, and `ANN` nothing at all. pycodestyle contributes only `E722` and `E902` — no `E4`
  rule, and none of the formatter-conflicting `E111`, `E114`, `E117`, `W191`, `E501`.
  Checked 2026-08-20.
- [Ruff — Tutorial](https://docs.astral.sh/ruff/tutorial/) — the page that actually carries the
  sentence §16 quotes about why the default set looks the way it does: Ruff enables its defaults
  "omitting any stylistic rules that overlap with the use of a formatter, like `ruff format` or Black".
  Recorded separately because the two pages are in tension: the tutorial summarises the default as the
  "`F`, `E`, `B`, `UP`, and `RUF` categories, as well as many more", which reads as whole families,
  while the Default rules page enumerates individual codes and takes almost nothing from `E`. Where
  they disagree, this document follows the enumeration. Checked 2026-08-20.
- [Ruff — Formatter](https://docs.astral.sh/ruff/formatter/) — `ruff format` as "a drop-in replacement
  for Black" with "near-identical output", which licenses §16's `ruff format .` / `black .` equivalence;
  and the list of lint rules to avoid alongside a formatter (`E111`, `E114`, `E117`, `W191`, plus the
  `E501` conflict), which is what §16's narrowed `E` selection responds to. Checked 2026-08-20.
- [Ruff — Linter](https://docs.astral.sh/ruff/linter/) — "by default, Ruff will fix all violations for
  which safe fixes are available", with unsafe fixes gated behind `--unsafe-fixes` because they "could
  lead to a change in runtime behavior, the removal of comments, or both". The basis for splitting
  §16's local `--fix` run from the CI `ruff check .`. Checked 2026-08-20.
- [Ruff — `complex-structure` (C901)](https://docs.astral.sh/ruff/rules/complex-structure/) —
  cyclomatic complexity is enforced by `C901` from the **mccabe** (`C90`) family, a different namespace
  from flake8-comprehensions (`C4`). This is why §5 now says the complexity limit is unmeasured unless
  `C90` is enabled. The page states no default value for `max-complexity`, so none is quoted anywhere
  here. Checked 2026-08-20.
- [mypy — Command line (`--strict`)](https://mypy.readthedocs.io/en/stable/command_line.html) — the
  exact flag set behind `--strict` (thirteen flags, from `--disallow-any-generics` to
  `--extra-checks`), the statement that it is "a defined subset of optional error-checking flags", and
  the warning that "the exact list of flags enabled by running `--strict` may change over time". Also
  the negative fact §7 now states: no flag in the strict set bans explicit `Any`. mypy 2.3.1 docs,
  checked 2026-08-20.
- [mypy — The mypy configuration file](https://mypy.readthedocs.io/en/stable/config_file.html) — that
  configuration may live in `pyproject.toml`, and `strict` = "enable all optional error checking
  flags", again with the may-change caveat. Backs §16's config location and version-pinning rule.
  mypy 2.3.1, checked 2026-08-20.
- [mypy — More types (`NewType`)](https://mypy.readthedocs.io/en/stable/more_types.html) — the contract
  §7's example previously broke: the string literal "must equal the name of the variable to which the
  new type is assigned", and you "cannot use `isinstance()` or `issubclass()` on the object returned by
  NewType, nor can you subclass" it. mypy 2.3.1, checked 2026-08-20.
- [mypy — Using mypy with an existing codebase](https://mypy.readthedocs.io/en/stable/existing_code.html)
  — context for §7's strict mandate: mypy advises incremental adoption, notes options "can be enabled
  on a per-module basis", singles out `disallow_untyped_defs` ("strongly recommend enabling this one as
  soon as you can"), and frames passing `--strict` as "an excellent goal to aim for" rather than a
  starting configuration. mypy 2.3.1, checked 2026-08-20.

**Testing**

- [pytest — How to parametrize fixtures and test functions](https://docs.pytest.org/en/stable/how-to/parametrize.html)
  — confirms §15's `@pytest.mark.parametrize` spelling and usage against the documented example. No
  error found. Docs "stable" (console output shows `pytest-9.x.y`), checked 2026-08-20.
- [pytest — How to mark test functions with attributes](https://docs.pytest.org/en/stable/how-to/mark.html)
  — the requirement §15 was missing: unregistered marks "will always emit a warning", and with the
  `strict_markers` configuration option set, unknown marks "will trigger an error". Checked 2026-08-20.
- [pytest — How to use fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html) — every
  fixture idiom §15 relies on: `@pytest.fixture`, sharing via `conftest.py`, `yield` fixtures for
  teardown (the mechanism behind transaction-rollback isolation), the scope list, and fixture
  parametrization via `params`. No error found. Checked 2026-08-20.
- [pytest-cov — Configuration](https://pytest-cov.readthedocs.io/en/latest/config.html) — `--cov` and
  `--cov-fail-under` are pytest-**cov** options, not pytest core ones, which is why §16 now says to
  declare the plugin. pytest-cov 7.1.0, checked 2026-08-20. Neither this page nor pytest recommends any
  coverage percentage; §15's 85% is a house floor.

**SQLAlchemy** (all pages SQLAlchemy 2.0.52, checked 2026-08-20)

- [ORM Quick Start](https://docs.sqlalchemy.org/en/20/orm/quickstart.html) — `DeclarativeBase`,
  `Mapped`, `mapped_column()` confirmed as the current 2.0 spelling for §11, and the docs' own
  `session.scalars(stmt)` execution idiom.
- [ORM Querying Guide — SELECT statements](https://docs.sqlalchemy.org/en/20/orm/queryguide/select.html)
  — both `session.execute(select(...))` and `session.scalars(select(...))` are documented, with
  `Session.scalars()` described as "the equivalent" of execute-then-scalars. Source of §11's corrected
  wording.
- [Session API](https://docs.sqlalchemy.org/en/20/orm/session_api.html) — `with session.begin():` as
  "begin a transaction, or nested transaction, on this Session, if one is not already begun". The
  commit-on-exit wording confirmed on this read was `sessionmaker.begin()`'s, so no precise
  commit-semantics quote for `Session.begin()` is attributed here.
- [ORM Querying Guide — Relationship Loading Techniques](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html)
  — `lazy="raise"`, `lazy="raise_on_sql"`, `raiseload()`, `selectinload`, `joinedload` all exist as
  documented; and the caveat §11 now carries: the raiseload strategies "do not apply within the unit of
  work flush process". No sentence distinguishing `raise` from `raise_on_sql` could be retrieved, which
  is why §11 says to read this page rather than treating them as synonyms.
- [Configuring a Version Counter](https://docs.sqlalchemy.org/en/20/orm/versioning.html) — §11's
  `version_id_col` is current, declared via `__mapper_args__`, and a mismatch raises `StaleDataError`.
- [Selectable API](https://docs.sqlalchemy.org/en/20/core/selectable.html) — confirms
  `with_for_update()` exists on `Select` in 2.0. Existence only: the render truncated before the method
  docstring, so nothing about `nowait`/`read`/`of`/`skip_locked` is attributed to this reading.
- [Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html) — the defaults §11 now
  states: `pool_size` 5, `max_overflow` 10, `pool_recycle` -1, `pool_pre_ping` as a checkout liveness
  ping; and which pool class each dialect uses (`QueuePool` by default, `SingletonThreadPool` for
  SQLite `:memory:`, `AsyncAdaptedQueuePool` under `create_async_engine`).
- [Engine Configuration](https://docs.sqlalchemy.org/en/20/core/engines.html) — the scoping sentences
  behind §11's pooling caveat: `max_overflow` "is only used with QueuePool"; `pool_size` is "used with
  QueuePool as well as SingletonThreadPool".

**FastAPI** (docs pages carry no version stamp; read 2026-08-20 against fastapi 0.141.1)

- [Response Model / Return Type](https://fastapi.tiangolo.com/tutorial/response-model/) — the
  return-type-first framing §12 now follows, and `response_model=` as the documented escape hatch that
  takes priority when both are present.
- [Reference — FastAPI class](https://fastapi.tiangolo.com/reference/fastapi/) — confirms every
  response-shaping parameter §12 names exists with that exact spelling: `response_model`,
  `response_model_exclude_none`, `status_code`, `dependencies`.
- [Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/) — `Annotated[X, Depends(...)]` is
  the docs' recommended form ("prefer to use the `Annotated` version if possible"). §12 matches the
  source here.
- [Dependencies in Path Operation Decorators](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/)
  — the router-level `dependencies=[Depends(...)]` pattern §12 mandates for cross-cutting auth,
  documented for dependencies whose return value you don't need. No conflict.
- [Dependencies with yield](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/)
  — the `try` / `yield` / `finally: close()` session shape, and the exception-propagation behaviour
  behind §11's let-it-roll-back rule.
- [SQL (Relational) Databases](https://fastapi.tiangolo.com/tutorial/sql-databases/) — backs §12's
  separate In/Out schemas (clients cannot set `id`; `secret_name` is never returned), and is the source
  of two divergences now stated in §11 and §12: the tutorial injects the session into the path
  operation and calls `select()` there, and it uses `with Session(engine)` rather than
  `finally: close()`. It is also written against SQLModel, not plain SQLAlchemy.
- [Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/) — `@app.exception_handler`
  registration, overriding `RequestValidationError`, and raising rather than returning `HTTPException`.
  §12's "don't scatter `HTTPException` through services" is a layering preference the docs neither
  state nor contradict.
- [Lifespan Events](https://fastapi.tiangolo.com/advanced/events/) — confirms §12's lifespan rule
  exactly, including that lifespan is "the recommended way to handle the startup and shutdown" over
  the older event handlers. No conflict.
- [Concurrency and async / await](https://fastapi.tiangolo.com/async/) — the threadpool mechanic §12
  cites, and the warning against plain `def` for trivial compute-only path operations that §12 now
  incorporates.
- [fastapi on PyPI](https://pypi.org/project/fastapi/) — used only to pin the unversioned docs pages
  above to a release: fastapi 0.141.1, released 2026-07-29. The release index is not the documentation;
  `fastapi.tiangolo.com` remains the canonical home.

**Security** (all checked 2026-08-20; none of the cheat sheets displays a version or revision date)

- [OWASP Top 10:2025](https://owasp.org/Top10/2025/) — the risk taxonomy §10 implicitly organises
  itself around. Mapping: parameterized queries and output encoding → A05 Injection; authz, IDOR and
  SSRF → A01 Broken Access Control (the introduction page, `/Top10/2025/0x00_2025-Introduction/`,
  states SSRF "has been rolled into this category" — that sentence is there, not on the landing page
  linked above); password, JWT and token rules → A07 Authentication Failures; TLS and encryption at rest →
  A04 Cryptographic Failures; `DEBUG=False`, CORS and headers → A02 Security Misconfiguration; lockfile
  and `pip-audit` → A03 Software Supply Chain Failures; generic error responses → A10 Mishandling of
  Exceptional Conditions. This mapping is a reconstruction: §10 named no edition and no artifact. Note
  the gaps it exposes — nothing here corresponds to A06 Insecure Design or A08 Software or Data
  Integrity Failures, and A09 is only partly covered even after §9's security-event rule.
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/) — the umbrella. This series, not any
  document called "OWASP Security Guidelines", is what actually supplies §10's prescriptive rules; cite
  the individual sheets below rather than the index.
- [Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
  — §10's hashing rule: the Argon2id → scrypt → bcrypt order of preference with parameters, the
  PBKDF2-HMAC-SHA-256 ≥ 600,000 carve-out for FIPS-140, and the narrower real objection to fast hashes
  ("they allow attackers to perform large numbers of guesses quickly"). The rendered page shows no
  revision date; the upstream markdown was last committed 2026-06-24, i.e. before this document was
  written, so the divergence corrected in §10 is not staleness.
- [SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html)
  — §10's injection rule and §11's "parameterized always": prepared statements with parameterized
  queries first, allow-list input validation, escaping "strongly discouraged", and table and column
  names coming from code rather than user parameters. No conflict.
- [Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
  — the credential-policy bullet added to §10: length floors, "maximum password length should be at
  least 64 characters", "there should be no password composition rules", the failed-login counter bound
  to the account rather than the source IP, constant-time comparison, and generic login errors.
- [Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
  — §10's deny-by-default and object-level checks: "perform access control checks on every request for
  the specific object or functionality being accessed". No conflict.
- [File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
  — "list allowed extensions", and the reason §10's upload rule was rewritten: the `Content-Type` "is
  provided by the user, and as such cannot be trusted, as it is trivial to spoof".
- [Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html) — §9's
  never-log list (session identifiers, access tokens, passwords, connection strings, keys, PII), the
  correlation-ID rule, and the security-event list §9 previously omitted.
- [Deserialization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html)
  — §10's ban on `pickle.loads` over untrusted data (the page also names PyYAML `load` and jsonpickle,
  which §10 does not). No conflict.
- [Server Side Request Forgery Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)
  — §10's outbound allow-list ("deny-lists are bypass-prone; prefer allow-lists"), plus two controls
  §10 still omits: disabling redirect-following, and re-resolving A/AAAA records against DNS rebinding.
- [Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
  — the rotation requirement now in §10, and the divergence §10 states plainly: environment variables
  are rated a fallback, "not recommended unless the other methods are not possible". It does not
  mention `.env` files, so §10's "never commit `.env`" is a house rule.
- [OWASP ASVS — project page](https://owasp.org/www-project-application-security-verification-standard/)
  — establishes the current release: ASVS 5.0.0, 30 May 2025.
- [OWASP ASVS 5.0.0 (standard text)](https://github.com/OWASP/ASVS/tree/v5.0.0/5.0/en) — the testable
  layer behind §10: V5.2.2 and V5.1.1/V5.2.1 (upload extension-plus-content and size limits), V6.2.1
  and V6.2.9 (password length), Appendix C (the approved hash parameters — Argon2id, scrypt, bcrypt
  cost ≥ 10, PBKDF2 iteration floors), V3.4.1–V3.4.8 (CORS allowlist and the specific security
  headers), and V16.3.1/V16.3.2/V16.3.4 plus V16.5.1 (log authentication and authorization outcomes;
  generic error messages). Chapters read: V3, V5, V6, V16, Appendix C. Note the algorithm parameters
  live in Appendix C, not in V6 — do not cite "ASVS V6" for them. Note also a real disagreement
  between two OWASP artifacts this document cites side by side: Appendix C's approved argon2id setting
  is "t = 1: m ≥ 47104 (46 MiB), p = 1", while the Password Storage Cheat Sheet's minimum is
  m = 19456 (19 MiB), t = 2, p = 1. §10 quotes the cheat sheet; nothing in this document attributes an
  argon2id figure to Appendix C.

**Architecture**

- [Robert C. Martin — The Clean Architecture (2012-08-13)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
  — the only public canonical statement of Clean Architecture, and the source of §1's "dependencies
  point inward" and §2's layer table: the Dependency Rule ("source code dependencies can only point
  inwards. Nothing in an inner circle can know anything at all about something in an outer circle"),
  the circles being schematic, "the Web is a detail. The database is a detail", and the
  boundary-crossing rule about simple data structures and not passing Entities or database rows — which
  §2 now records as a deliberate divergence. Checked 2026-08-20.
- [Robert C. Martin — The Single Responsibility Principle (2014-05-08)](https://blog.cleancoder.com/uncle-bob/2014/05/08/SingleReponsibilityPrinciple.html)
  — §1's SRP wording: "each software module should have one and only one reason to change", "this
  principle is about people", and the actor framing this document previously dropped. Checked
  2026-08-20.
- [Robert C. Martin — Solid Relevance (2020-10-18)](https://blog.cleancoder.com/uncle-bob/2020/10/18/Solid-Relevance.html)
  — the citable public enumeration of all five SOLID principles in the author's own words. Read
  primarily to establish what this document does *not* use: only SRP and dependency inversion appear
  anywhere in it. Checked 2026-08-20.
- [Clean Architecture: A Craftsman's Guide to Software Structure and Design — Robert C. Martin (Pearson, 2017)](https://www.informit.com/store/clean-architecture-a-craftsmans-guide-to-software-structure-9780134494166)
  — **a bibliographic entry, not a rule source.** The publisher's page was read for author, publisher,
  edition (1st, 10 September 2017) and ISBN-13 978-0-13-449416-6, on 2026-08-20. The book itself was
  not read. No rule, threshold, or wording in this document may be attributed to a chapter or page of
  it; where the architecture rules here can be sourced at all, they are sourced to the 2012 blog post
  above.
- [Domain-Driven Design: Tackling Complexity in the Heart of Software — Eric Evans (Addison-Wesley, 2003)](https://www.informit.com/store/domain-driven-design-tackling-complexity-in-the-heart-9780321125217)
  — **a bibliographic entry, not a rule source.** Publisher page read 2026-08-20 for author, publisher,
  edition (1st, 20 August 2003) and ISBN-13 978-0-321-12521-7. The book was not read; attribute no rule
  to a page or chapter of it. Use the DDD Reference below for any DDD wording.
- [Domain-Driven Design Reference: Definitions and Pattern Summaries — Eric Evans (2015-03, CC BY 4.0)](https://www.domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf)
  — the only primary DDD text actually read (downloaded and text-extracted 2026-08-20: 59 pages,
  © 2015 Eric Evans, "Creative Commons Attribution 4.0 International License" per the title page): the
  author's own summaries of Layered Architecture, Entities, Value Objects, Aggregates, Repositories,
  Services and Modules. It supplies the quotations behind the DDD divergences recorded in §2, §11 and
  §14, and each of those was checked word-for-word against the extracted text. By construction it is a
  summary rather than an argument — the subtitle is "Definitions and Pattern Summaries", and the
  acknowledgements describe the contents as the "brief summaries of each pattern" extracted from the
  2004 book — so it can settle what a pattern *says* but not the book's surrounding reasoning. It
  carries no disclaimer beyond that: it contains no sentence limiting its own scope, so do not quote
  one. Retrieval note: this host answers some automated fetchers with HTTP 403, so the PDF was pulled
  directly (HTTP 200, 484 KB) and text-extracted rather than read through a page-fetch tool.

**What rests on general practice, not on any source above**

The numeric thresholds are house rules. "Line length 100" (§16) matches no value in any cited source;
"≤ 4 parameters" and "cyclomatic complexity ≤ 8" (§5), "class over ~200 lines or >7 public methods" and
"inheritance depth ≤ 2" (§6), "~10 files per layer" (§2), "coverage ≥ 85%" (§15), and "route handler
≤ 15 lines" (§12) appear in none of them. Several resemble figures from Martin's *Clean Code*, a
different book that is not cited here and was not read. "Composition over inheritance" (§6) is not a
SOLID principle and comes from none of these sources; its usual provenance is the Gang of Four, which
this document does not cite.

Also general practice, stated from mechanics rather than quoted: §3's boolean prefixes, units-in-name
rule, singular-module rule, enum-member convention and test-name pattern; §8's exception-hierarchy
shape and retry guidance; §13's async rules as a whole (no page from `docs.python.org`, `httpx` or
`asyncio` was read in this pass); §11's "index every foreign key", the expand/migrate/contract
sequence, and the Alembic rules — Alembic is a separate project from SQLAlchemy and its documentation
was not checked; §12's pagination bounds; §14's caching and streaming rules; §15's mocking and
edge-case guidance; and §2's specific layer prohibitions. §11's `text("... WHERE id = :id")`
bound-parameter spelling was not checked against SQLAlchemy's textual-SQL documentation in this pass.

Two named influences could not be verified and support nothing here. Martin's 2000 paper "Design
Principles and Design Patterns", where the principles later acronymised as SOLID first appeared, could
not be retrieved on 2026-08-20 — objectmentor.com no longer serves it and the Internet Archive was
unreachable from this environment — so no URL for it is given and nothing rests on it. And "OWASP
Security Guidelines", named in the original framing, is not the title of any OWASP document; §10 is now
attributed to the specific artifacts above (Top 10:2025, nine Cheat Sheet Series pages, ASVS 5.0.0),
reconstructed after the fact rather than recorded at authoring time.
