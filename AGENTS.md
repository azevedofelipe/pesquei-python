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

## Policy: tests and CI are mandatory

- **Every new endpoint or model change must ship with tests in the same PR.**
  `tests/conftest.py` already provides everything needed — `client`,
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

## Known issues / gotchas

- **`CatchCreate.date_caught` default is a bug**: `schemas/catch.py` sets
  `date_caught: datetime = datetime.now()`. That default is evaluated once,
  at import time (class definition), not per-request — every catch created
  without an explicit `date_caught` gets the timestamp of when the server
  started, not when the request happened. Fix is `Field(default_factory=datetime.now)`.
  Not yet fixed as of 2026-09-27.
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
- `POST /lure/` and `POST /catch/` have no `response_model` and no explicit
  `status_code` — they return a bare `200` with whatever the SQLAlchemy
  object serializes to, unlike `POST /auth/register` which declares
  `response_model=UserResponse, status_code=201`. Found independently by two
  agents while writing tests 2026-09-28; functionally harmless (tests
  accept 200) but worth cleaning up for consistency at some point.

## Decisions

- 2026-09-27: Project is shifting from "write everything by hand to learn
  backend" to "use AI agents to build it, learn agentic workflows instead."
  `Pesquei_Backend_Roadmap.md` was restructured to reflect actual repo state
  (done/in-progress/not-started) rather than being a static plan; this file
  (`AGENTS.md`) was added as the place for cross-session working memory.

## Log

<!-- Newest entries at the top. Format: `- YYYY-MM-DD: <what happened/learned, why it matters>` -->
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
