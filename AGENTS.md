# AGENTS.md

Shared, running memory for AI agents working on this repo. Read this before
starting work. Update it as you go — this file is only useful if it stays
current.

## How to use this file

- Before starting a task: skim **Known issues / gotchas** and **Decisions**
  so you don't re-discover the same thing or contradict a past choice.
- While working: if you hit something non-obvious (a bug, a footgun, a "why
  is this like this"), or make a decision that isn't obvious from the diff
  alone, add a short dated entry to **Log**. One or two lines. Say what
  happened and why it matters, not a transcript of the debugging.
- Don't log routine work (a normal CRUD endpoint added as expected). Log the
  things that would otherwise cost the next agent time to re-learn.
- If an entry in **Known issues** gets fixed, move it out (delete it or note
  it as resolved) instead of leaving stale info.
- For what's built / what's next, see `Pesquei_Backend_Roadmap.md` — this
  file is for *how* to work in this codebase, not the feature roadmap.

## Agent pipeline

Four custom subagents live in `.claude/agents/`, each scoped to one part of
the pipeline. The orchestrating session (whoever's driving Claude Code
directly with the user) dispatches to these rather than doing everything
itself or using generic agents for specialized work:

- **`backend-dev`** — FastAPI/SQLAlchemy/Alembic. Implements endpoints,
  models, migrations. Self-verifies via curl against a `pesquei_test`-
  pointed server. Doesn't write tests, doesn't touch git.
- **`frontend-dev`** — React/TypeScript/Vite. Implements pages/components
  against the `api.ts` contract. Self-verifies via `npm run build` +
  curl (no browser access). Doesn't write tests, doesn't touch git.
- **`qa-tester`** — pytest. Writes/runs tests using `tests/conftest.py`'s
  fixtures, verifies persistence via `db_session`, confirms the full suite
  still passes. Doesn't implement features, doesn't touch git.
- **`release-manager`** — git/GitHub packaging. Takes verified work sitting
  in the working tree, branches, commits, pushes, captures a real-browser
  screenshot for user-facing changes, opens the PR, and *confirms CI
  actually goes green* (not just that a PR exists). Never merges — that
  stays a human decision.

Typical flow for a feature that touches both ends: `backend-dev` builds the
endpoint → `qa-tester` writes tests for it → `frontend-dev` builds the UI
against it → `release-manager` packages the result into a PR. Steps can run
in parallel when they don't depend on each other's output (e.g. `qa-tester`
and `frontend-dev` can often start once `backend-dev` reports its endpoint
contract, without waiting for each other). The orchestrating session is
still responsible for deciding shared-infrastructure changes itself (e.g. a
new pytest fixture everyone will use, a new `api.ts` export pattern) rather
than delegating them, for the same reason `tests/conftest.py` and
`frontend/src/api.ts` were built centrally rather than by parallel agents
in the first place — shared foundations shouldn't be invented three times
inconsistently.

Added 2026-09-28 at the user's request, to make the agent-driven workflow
this project already used ad hoc (see the Log entries below) into something
reusable instead of re-deriving each session.

## Policy: tests and CI are mandatory

- **Any agent that adds a new table, a new endpoint, or changes an existing
  model must do two things in the same PR: (1) write new pytest tests
  covering what it added, and (2) make sure every existing test still
  passes.** Both, not either — new tests alone aren't enough if you broke
  something that was already covered, and a clean existing suite isn't
  enough if the new feature has zero coverage. New table → new
  `tests/test_<table>.py` (or additions to an existing one if it extends a
  table that already has a file). New endpoint on an existing table → add
  cases to that table's existing test file, don't create a parallel one.
- `tests/conftest.py` already provides everything needed — `client`,
  `db_session`, and a `make_user` factory fixture that creates a throwaway
  user via the real `/auth/register`+`/auth/login` flow and cleans up after
  itself (including that user's catches/lures, in FK-safe order). Use it
  instead of hand-rolling setup/teardown. Don't add new top-level fixtures to
  `conftest.py` without a good reason — it's shared by every test file, so an
  incompatible change there breaks everyone at once.
- Tests run against a dedicated `pesquei_test` Postgres database (see
  `conftest.py`'s `TEST_DATABASE_URL` — it's the real `DATABASE_URL` with the
  db name swapped), never the real dev database. Assertions should verify
  persistence via `db_session` (a fresh, independent session/query), not just
  trust the API's JSON response — that's the whole point of an integration
  test here.
- **CI (`.github/workflows/ci.yml`) runs the full `pytest` suite against a
  real ephemeral Postgres service container on every PR and every push to
  `main`.** It must be green before a PR is merged — this is enforced as a
  required status check on `main` (branch protection), not just a suggestion.
  If you add a dependency the app needs at runtime, update **both**
  `pyproject.toml` and the `pip install` step in `ci.yml` — there's no
  packaging/build-system set up yet (see Known issues), so CI installs an
  explicit list rather than `pip install .`, and the two lists can drift if
  you only update one.
- Before opening/updating a PR: run `venv/Scripts/python.exe -m pytest -v`
  locally yourself. Don't rely on CI to be your first signal that something
  broke — CI is the backstop, not the primary check.

## Project quick facts

- FastAPI + SQLAlchemy 2.0 (pinned `<2.1`, see Known issues) + Alembic +
  PostgreSQL + Pydantic v2. `pyproject.toml` exists (added 2026-09-28) but
  there's no lockfile/`uv` usage yet — the local `venv` is still populated by
  hand with matching versions, not by installing from the pyproject file.
- Run dev server: `fastapi dev main.py`
- New migration: `alembic revision -m "Message"` then `alembic upgrade head`
- Regenerate `models.py` from the live DB: see command in
  `Pesquei_Backend_Roadmap.md`
- `.env` (gitignored) holds `DATABASE_URL` and `SECRET_KEY` (JWT signing key,
  added 2026-09-28 — `security.py` reads it via `os.getenv` with no
  validation, so a missing key fails at token-creation time, not at startup).
  Both loaded via `python-dotenv`.
- Layout: `models.py` (SQLAlchemy models, flat file) → `schemas/<resource>.py`
  (Pydantic Create/Response pairs) → `routers/<resource>.py` (APIRouter,
  wired into `main.py`). Auth: `security.py` has `get_current_user` (JWT
  `Depends`), `hash_password`/`verify_password`; `routers/auth.py` has
  `POST /auth/register` and `POST /auth/login` (OAuth2 password flow).
- **Catch and Lure are user-owned**: both have a `user_id` FK, every
  catch/lure route requires `Depends(get_current_user)`, and lookups check
  `record.user_id == current_user.id` — a record that exists but belongs to
  someone else returns 404 (not 403), same pattern used for `GET /user/{id}`
  (you can only fetch your own user record). Follow this pattern for any new
  catch/lure/user route.
- **Frontend** (added 2026-09-28): React + TypeScript + Vite, in `frontend/`.
  `frontend/src/api.ts` is the single source of truth for talking to the
  backend — token storage, a typed `apiFetch` wrapper (401 → redirect to
  `/login`, throws `ApiError` otherwise), and TS interfaces mirroring the
  backend's Pydantic schemas. Page components (`frontend/src/pages/`) should
  import from `api.ts` rather than calling `fetch()` directly. Routing is
  `react-router-dom` (`frontend/src/App.tsx`), with a `RequireAuth` guard on
  protected routes. In dev, `vite.config.ts` proxies `/auth`, `/catch`,
  `/lure`, `/user` to the FastAPI dev server on port 8000 — no CORS needed.
  Those proxy rules are anchored regexes (`^/lure(/|$)`, not a plain `/lure`
  string) on purpose: a plain prefix silently swallows the frontend's own
  `/lures` route into the backend proxy. Run it: `cd frontend && npm run
  dev` (needs the backend running separately on port 8000). CI runs
  `npm ci && npm run build` (`tsc -b && vite build`) as a required check,
  same as the backend's pytest job.

## Known issues / gotchas

- Router handlers mix Portuguese and English names (`novo_catch`, `novo_lure`,
  `resultado`) — existing style in the two routers that exist so far; not a
  hard rule, just don't be surprised by it or "fix" it as a drive-by.
- No lint/type-check config (Ruff and Pyright are installed/intended but
  unconfigured) — don't assume `ruff check` enforces anything yet.
- This project lives under a OneDrive-synced folder. `venv/` is gitignored
  but still gets synced across machines as a plain folder, and a venv baked
  for one machine's Python install is not portable to another (see the
  resolved venv issue below, kept as a warning) — **always check
  `venv/pyvenv.cfg`'s interpreter path actually exists on the current machine
  before trusting a synced `venv/`.**
- `pyproject.toml`'s dependency list had `psycopg[binary]>=3.2` (psycopg3),
  but `database.py` builds a bare `postgresql://` URL, which SQLAlchemy 2.0
  resolves to **psycopg2**, not psycopg3 — installing straight from the old
  pyproject.toml would have pulled the wrong driver package. Fixed
  2026-09-28 to `psycopg2-binary>=2.9` and `sqlalchemy>=2.0,<2.1` (see next
  point for why the sqlalchemy upper bound matters). If this project ever
  deliberately moves to psycopg3, `database.py`'s URL needs
  `postgresql+psycopg://` too, not just a pyproject.toml change.
- **Pin sqlalchemy `<2.1`** — 2.1.x changes default driver resolution for a
  bare `postgresql://` URL in a way that breaks this project's psycopg2
  setup.
- `ci.yml`'s dependency install list and `pyproject.toml`'s dependency list
  are two separate, manually-kept-in-sync lists (no `[build-system]`/`pip
  install .` set up yet, since the repo isn't laid out as an installable
  package). Update both when adding a runtime dependency, or CI will pass
  locally-installed code that doesn't actually match what CI tested.
- **pytest needs `pythonpath = ["."]`** in `pyproject.toml`'s
  `[tool.pytest.ini_options]` — without it, `tests/conftest.py`'s `from main
  import app` only resolves when pytest is invoked as `python -m pytest`
  (which prepends cwd to `sys.path`), not with a bare `pytest` command. CI
  runs bare `pytest`, so this broke CI on the first run (2026-09-28) despite
  passing locally — always sanity-check a new CI workflow actually goes
  green on GitHub, don't assume "passes locally" implies "passes in CI."
- **(Resolved 2026-09-28)** `POST /lure/` and `POST /catch/` now declare
  `response_model=LureResponse`/`CatchResponse` + `status_code=201`,
  matching `POST /auth/register`'s pattern. Also fixed: `CatchCreate
  .date_caught`'s import-time default (now `Field(default_factory=lambda:
  datetime.now(timezone.utc))`); `Lure.weight`/`size` now typed `float`
  everywhere (dropped `Decimal`) so both endpoints serialize as JSON
  numbers consistently; `Catch.date_caught` is now `DateTime(timezone=True)`
  (migration `b671f9a295a9`), storing/reading UTC explicitly instead of a
  naive column with no stated convention. Verified via curl against
  `pesquei_test`: sending `date_caught: "...T11:30:00.000Z"` now round-trips
  through `POST`/`GET /catch/` as `08:30:00-03:00` — the same instant,
  explicitly offset-tagged, rather than a silently-shifted naive value.
  **Fallout for whoever touches tests next**: 4 pre-existing tests in
  `tests/test_catch.py` now fail because they compare the (now
  timezone-aware) `row.date_caught`/response value against a naive
  `datetime.fromisoformat(...)` — Python raises/mismatches on aware-vs-naive
  comparison. These tests' own docstring/comments still reference the old
  "known bug" as unfixed; both the comparisons and that comment need
  updating (e.g. compare via `.astimezone(timezone.utc)` on both sides, or
  assert equality of the resolved instant rather than the raw string).
  `tests/test_lure.py`'s `Decimal(...)` comparisons were unaffected by the
  `Lure.weight`/`size` float change (string-based `Decimal(str(x))`
  comparison works either way).

## Decisions

- 2026-09-27: Project is shifting from "write everything by hand to learn
  backend" to "use AI agents to build it, learn agentic workflows instead."
  `Pesquei_Backend_Roadmap.md` was restructured to reflect actual repo state
  (done/in-progress/not-started) rather than being a static plan; this file
  (`AGENTS.md`) was added as the place for cross-session working memory.

## Log

<!-- Newest entries at the top. Format: `- YYYY-MM-DD: <what happened/learned, why it matters>` -->
- 2026-09-28: **Fixed all four known backend bugs from STEPS.md step 8**
  (`CatchCreate.date_caught` import-time default, `Catch.date_caught`
  UTC-offset shift, missing `response_model`/`status_code` on `POST
  /lure/`+`POST /catch/`, `Lure.weight`/`size` `Decimal`-vs-`float`
  inconsistency) — see the (now-resolved, trimmed) Known issues entries
  above for detail on each. New migration `b671f9a295a9` makes
  `catch.date_caught` `TIMESTAMP WITH TIME ZONE`, using `AT TIME ZONE 'UTC'`
  in the `USING` clause on both `upgrade`/`downgrade` so existing naive
  values are reinterpreted as the UTC they were always meant to represent,
  rather than relying on Postgres's session `timezone` GUC (the exact
  ambiguity that caused the original bug). Chose `datetime.now(timezone
  .utc)` (aware) over a bare `datetime.now()` (naive/local) for the new
  `default_factory`, matching the aware-UTC convention `security.py`
  already used for JWT `exp` — a naive default would have reintroduced the
  same "no stated timezone convention" ambiguity bug #2 was fixing, just in
  the default-value path instead of the column. One behavior worth
  flagging: responses now show `date_caught` with the server's local
  offset (e.g. `08:30:00-03:00`) rather than `Z`/`+00:00`, because Postgres
  always converts `timestamptz` output to the connection's session
  `timezone` GUC before returning it — this is still the *same instant* (any
  correct ISO-8601 parser resolves it identically to the UTC value), just a
  different display offset; flagging in case a future agent assumes the
  API always emits `Z`. `pesquei_test`'s schema doesn't go through Alembic
  at all (`tests/conftest.py` uses `Base.metadata.create_all(checkfirst=
  True)` against `models.py` directly, and only ever *adds* missing tables)
  — so verifying the column-type change there required a direct `ALTER
  TABLE ... USING date_caught AT TIME ZONE 'UTC'` mirroring the migration,
  not `alembic upgrade head`. Left that altered state in place afterward
  since it now matches `models.py` and is what the next `pytest` run needs
  anyway. Did **not** run `alembic upgrade head` against the real dev
  database as part of this work — migrations exist in `alembic/versions/`
  ready to apply, but landing them on `pesquei` (vs. just `pesquei_test`)
  was left for whoever next runs the app against the real dev DB, per this
  task's "never touch the real dev database" boundary.
- 2026-09-28: **Phase 6 / STEPS.md step 10: Open-Meteo weather + sunrise/sunset
  snapshot on `Catch`, tide deliberately skipped.** Added `clients/http.py`
  (shared `httpx.AsyncClient` factory: base URL, timeout, connection-retry
  config in one place) and `clients/open_meteo.py`. Confirmed directly
  against the live API (not just docs) that a single Open-Meteo call
  requesting both `hourly=temperature_2m,weathercode` and `daily=sunrise,sunset`
  returns everything needed — no separate sunrise/sunset API required, matching
  the roadmap's guess. Two Open-Meteo endpoints are used: `api.open-meteo.com/v1/forecast`
  (recent past ~90 days / near-future) and `archive-api.open-meteo.com/v1/archive`
  (older dates the forecast endpoint 400s on) — the client tries forecast
  first and falls back to archive automatically. Both are free, unauthenticated,
  no paid tier, confirmed by hitting them directly.
  **Tide was deliberately skipped, not forgotten**: the only genuinely free,
  no-API-key tide API found is NOAA CO-OPS, which only covers US NOAA
  stations — nothing in this codebase indicates the app's target region is
  US coastal waters, and no other tide API could be confirmed free with no
  paid-tier risk. Per explicit instruction, integrating something with cost
  risk was worse than shipping without tide, so `Catch` has no `tide_state`
  column. Revisit once the target region is confirmed and/or a confirmed-free
  tide source for it is found.
  `POST /catch/` is now `async def` and awaits the weather lookup
  synchronously (per the roadmap's stated default) using whatever
  `latitude`/`longitude`/`date_caught` the request already has; skips the
  lookup entirely (no external call at all) if either coordinate is missing;
  and never blocks catch creation on lookup failure — `get_weather_snapshot()`
  catches its own `httpx` errors, logs a warning, and returns `None`, leaving
  the four new columns null. New nullable `Catch` columns: `temperature`
  (`Numeric(5,2)`, same convention as `weight`/`length`), `conditions`
  (`String(100)`, a label derived from Open-Meteo's WMO `weathercode`),
  `sunrise`/`sunset` (naive `DateTime`, matching `date_caught`'s existing
  naive-datetime convention rather than fixing that separately-tracked bug).
  Migration `0b19934327fb_add_weather_snapshot_columns_to_catch.py`, applied
  and curl-verified against `pesquei_test` only — **not applied to the real
  dev DB** (a concurrent worktree may also be migrating it; left for
  release-manager/whoever merges first to run `alembic upgrade head` there,
  resolving any two-heads conflict if another concurrent migration also
  branched from `e25a6a259344`). Added `httpx` explicitly to `pyproject.toml`
  and `ci.yml` (it was already an indirect dependency via `fastapi[standard]`
  for `TestClient`, but this is the first *direct* runtime use of it).
- 2026-09-28: **Built the first frontend (rough MVP): React + TypeScript +
  Vite, three pages.** Chose that stack deliberately (most common pairing
  with a FastAPI backend, plus a chance to pick up TypeScript). Built shared
  scaffolding centrally first — `frontend/src/api.ts`, `App.tsx` router
  shell, `Nav.tsx`, `vite.config.ts` proxy, shared CSS — same reasoning as
  the pytest `conftest.py` decision below: three agents building
  Login/Lures/Catches in parallel needed one consistent foundation, not
  three incompatible ones. Caught a real bug in that scaffolding myself
  before delegating: a plain `/lure` string in the Vite proxy config
  prefix-matches the frontend's own `/lures` route, silently routing it to
  the (404-ing) backend instead of the SPA — fixed with anchored regexes
  (`^/lure(/|$)`). Since the three page-agents couldn't reliably share the
  same dev server ports, each verified its own page's API contract via
  `curl` directly against its own backend instance on a dedicated port
  (8000/8001/8002) rather than fighting over the shared Vite proxy target —
  a useful pattern when the "shared harness" itself can't be triple-run.
  Did a final real-browser pass myself afterward (register → login → create
  lure → create catch linked to that lure) to get PR screenshots and catch
  anything curl-only checks would miss. Also decided: three separate PRs,
  not three commits in one — matches "one page, one reviewable/mergeable
  unit," at the cost of a merge-order dependency (login's PR carries the
  shared scaffolding, so it should merge before lures/catches).
- 2026-09-28: **Added the first test suite (35 tests) and CI.** Built
  `tests/conftest.py` centrally first (dedicated `pesquei_test` Postgres db,
  `client`/`db_session`/`make_user` fixtures) rather than letting three
  parallel agents each invent their own scaffolding — shared test
  infrastructure is exactly the kind of thing that shouldn't be duplicated
  three times. Then ran three agents in parallel, one per table
  (`test_user.py` 10 tests, `test_lure.py` 12, `test_catch.py` 13), each only
  touching its own file. All 35 pass together. Added
  `.github/workflows/ci.yml`: spins up a real ephemeral Postgres service
  container and runs the full suite on every PR/push to `main`, set as a
  required status check via branch protection. Landed as more commits on the
  already-open PR for the catch/lure CRUD + users router work, since those
  are the endpoints being tested and hadn't merged yet.

## Testing

- Run the full suite locally: `venv/Scripts/python.exe -m pytest -v` (or
  just `pytest -v` if the venv's `Scripts` dir is on `PATH`).
- Run one table's tests: `pytest tests/test_lure.py -v`.
- See `tests/conftest.py` for the fixtures every test file should build on.
- 2026-09-28: **Discovered and merged an unmerged auth branch that predated
  today's work.** Two agents built catch/lure CRUD roundout + a users router
  on `main`, unaware that a branch `azevedofelipe/link-records-to-user` (3
  commits, also on `origin`) already had full JWT auth (`routers/auth.py`,
  `security.py`, register/login) plus a migration adding `user_id` to
  `lure`/`catch` — and that migration had *already been applied* to the
  shared local Postgres DB even though `main` never merged the branch. This
  surfaced as a `NotNullViolation` on `user_id` the moment `POST /lure/` was
  actually tested against the real DB — first time anyone could run the app
  end-to-end on this machine, see the venv entry below. Root cause: `main`'s
  migration history and the live DB had silently diverged.
  Resolution: fast-forward merged `main` onto that branch (it turned out
  `main`'s tip was the branch's exact merge-base, so no true git conflict),
  then reconciled today's new code on top of the auth pattern —
  `list_catches`/`list_lures` now filter by `current_user.id`; the new
  PATCH/DELETE endpoints do the same `record.user_id != current_user.id` →
  404 check the branch already used for `GET`/`POST`. Dropped the
  independently-built `POST /user/` entirely since `POST /auth/register`
  already did the same job (password hashing + duplicate handling) —
  `routers/users.py` now only has `GET /user/{id}`, scoped to your own
  record. Added a `SECRET_KEY` to `.env` (JWT signing; the branch's
  `security.py` reads it but nothing had ever set it). **Lesson: before
  building on `main`, check for unmerged branches/PRs that touch the same
  models/tables — `git log --all` and `git branch --all`, not just `git log`
  on the current branch — especially on a shared dev DB where another
  branch's migration can already be live.**
- 2026-09-28: Round out CRUD (catch/lure) and add the users router were built
  by two agents working in parallel on non-overlapping files (routers/schemas
  for catch+lure vs. users.py+main.py). Neither could run the app on this
  machine due to the venv being broken at the time (see below) — one
  verified with `py_compile` + manual cross-checking only, the other built a
  throwaway venv off Python 3.12 to actually run `TestClient` against the
  real local Postgres DB. Worth remembering as a pattern: when the venv is
  unusable, a disposable venv is a viable way to still get real verification
  instead of settling for a syntax check.
- 2026-09-28: **Fixed the broken `venv/`.** `pyvenv.cfg` pointed at a Python
  3.13 interpreter path from a different user/machine
  (`C:\Users\fafel\...\Python313\`) that didn't exist here, while only Python
  3.12 was installed locally — every compiled package (psycopg2,
  pydantic-core, sqlalchemy cyextensions) was built for `cp313` and unusable.
  Moved it aside to `venv_broken_py313/` and rebuilt from
  `C:\Python312\python.exe`, then reinstalled matching versions: fastapi
  0.141.1, sqlalchemy 2.0.52, alembic 1.19.1, psycopg2-binary 2.9.12,
  python-dotenv 1.2.3, bcrypt 5.0.0, pyjwt 2.15.0 (python-multipart came
  along with `fastapi[standard]`). Verified by importing the app and running
  a full `TestClient` pass (register/login/CRUD/ownership checks) against
  the real DB.
- 2026-09-28: Catch/lure update endpoints implemented as PATCH (partial
  update via `model_dump(exclude_unset=True)`, all-Optional `*Update`
  schemas) rather than PUT full-replace — chosen because these are edit
  forms where sending one changed field shouldn't null out the rest. DELETE
  returns `204 No Content` for both resources, consistent between them.
- 2026-09-28: Users router hashes passwords with `bcrypt` directly (no
  passlib). `password_hash`/`created_at` are set inline in the request
  handler, not as Pydantic/class-level defaults, specifically to avoid
  repeating the `CatchCreate.date_caught` import-time-default bug above.
