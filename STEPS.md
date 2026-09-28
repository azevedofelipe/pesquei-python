# Steps

A single, chronological build order for the project — what to do, in what
sequence, and why that order. Check items off as they land.

This file is the *sequence*; it doesn't duplicate detail that lives
elsewhere:
- Stack, current status snapshot, and long-term phase groupings →
  `Pesquei_Backend_Roadmap.md`
- Gotchas, conventions, and cross-session learnings → `AGENTS.md`

---

## 1. Environment & tooling

- [x] Git repo + GitHub remote
- [x] First commit
- [ ] `README.md` (what the project is, how to run it)
- [x] Pin dependencies (`pyproject.toml`) — dependency list only, no
      lockfile/`uv` workflow yet, and the local `venv` was broken until
      2026-09-28 (see `AGENTS.md`; fixed by rebuilding from Python 3.12)
- [ ] Configure Ruff (`ruff.toml`/`pyproject.toml` section)
- [ ] Configure Pyright

*Why first: everything after this is easier to review and reproduce once the
environment itself is pinned and linted.*

## 2. API skeleton

- [x] FastAPI app boots (`main.py`)
- [ ] `GET /health`

## 3. Database foundation

- [x] PostgreSQL running locally
- [x] SQLAlchemy engine/session (`database.py`)
- [x] Alembic configured, migrations for `user`, `lure`, `catch`
- [x] `User`, `Lure`, `Catch` models + Pydantic schemas

## 4. Round out basic CRUD

- [x] `GET /catch` and `GET /lure` list endpoints (scoped to the caller's own
      records)
- [x] `PUT`/`PATCH` and `DELETE` for catch and lure — implemented as PATCH
      (partial update, `exclude_unset=True`) + DELETE (204)
- [x] `users` router: `GET /user/{id}` only, scoped to your own record —
      creation lives at `POST /auth/register` instead

## 5. Authentication

- [x] Password hashing (bcrypt) on user creation (`POST /auth/register`)
- [x] `POST /auth/login` issuing a JWT (OAuth2 password flow)
- [x] `get_current_user` dependency; catch/lure/user routes all protected and
      scoped to the caller's own records
- [ ] Refresh tokens

## 6. Frontend (rough MVP)

- [x] React + TypeScript + Vite scaffold, `frontend/`, wired to a Vite dev
      proxy (no CORS needed) — see `AGENTS.md` for the shared `api.ts`
      contract every page builds on
- [x] Login/register page (`Login.tsx`)
- [x] Lures page: create + view (`Lures.tsx`)
- [x] Catches page: create + view, with an optional lure link (`Catches.tsx`)
- [x] `frontend-build` CI job (`npm ci && npm run build`, type-check + build)

*Deliberately rough — no edit/delete UI (backend supports it, frontend
doesn't expose it yet), no pagination, minimal shared styling. See step 13.*

## 7. Testing

- [x] pytest + FastAPI `TestClient` setup, test DB fixture (`tests/conftest.py`,
      dedicated `pesquei_test` Postgres database, `make_user` fixture)
- [x] Endpoint tests — 35 tests across `test_user.py`/`test_lure.py`/
      `test_catch.py`, covering CRUD, auth requirements, and cross-user
      ownership isolation
- [x] Auth flow tests (register/login success + failure paths)
- [x] CI: full suite runs against a real ephemeral Postgres container on
      every PR, required status check on `main`
- [ ] Frontend tests (none yet — no Vitest/RTL setup). Not blocking, but
      worth adding once the frontend has more than 3 pages.

## 8. Fix known backend bugs (do this before step 10)

Four bugs accumulated across earlier sessions, logged in `AGENTS.md`. Fixing
them now because step 10 (weather/tide lookups keyed on catch date + location)
would otherwise be built on top of an already-known-broken timestamp.

- [x] `CatchCreate.date_caught` default (`schemas/catch.py`) is evaluated
      once at import time, not per-request — `Field(default_factory=datetime.now)`
      instead of `datetime.now()` (landed as an aware
      `Field(default_factory=lambda: datetime.now(timezone.utc))`, see
      `AGENTS.md` Log for why aware over bare `datetime.now()`)
- [x] `Catch.date_caught` shifts by the server's local UTC offset when
      round-tripped through Postgres — the column is a naive `DateTime`
      with no stated timezone convention. Likely fix: migrate the column to
      `DateTime(timezone=True)` and be explicit about UTC end-to-end (store
      UTC, convert to local only for display in the frontend) — migration
      `b671f9a295a9` landed; frontend display-side conversion still open,
      see `AGENTS.md` Log
- [x] `POST /lure/` and `POST /catch/` have no `response_model`/`status_code`
      — add `response_model=LureResponse`/`CatchResponse`, `status_code=201`,
      matching `POST /auth/register`'s pattern
- [x] `LureResponse.weight`/`size` are typed `Decimal` (serializes as a JSON
      *string*) while `Catch`'s equivalent fields are `float` (serializes as
      a JSON *number*) — pick one convention for both, most likely `float`
      to match `Catch` and simplify the frontend (`frontend/src/api.ts`'s
      `Lure.weight`/`size` types can drop the `| string` once this lands)

## 9. Automatic GPS location on catch creation

Requested explicitly: right now `latitude`/`longitude` on the catch form are
plain manual number inputs. They should auto-populate from the device's
actual location instead.

- [ ] Frontend: call the browser's `navigator.geolocation.getCurrentPosition()`
      when the catch form loads (or behind a "Use my location" button — decide
      based on how intrusive the permission prompt feels in practice), fill
      `latitude`/`longitude` from the result
- [ ] Keep the fields manually editable/overridable — geolocation can be
      denied, inaccurate (especially indoors), or the angler may be logging
      a catch after the fact from a different location
- [ ] Handle the permission-denied and unsupported-browser cases gracefully
      (fall back to the current manual inputs, don't block form submission)
- [ ] No backend change needed — `latitude`/`longitude` already exist on
      `Catch`

*Why before step 10, not after: the weather/tide lookups in step 10 need a
real lat/long to query against, and it's a much smaller, self-contained
frontend-only change — good to land and verify independently first.*

## 10. External APIs

- [x] Shared `httpx` async client wrapper (`clients/http.py` — a single
      place for base URL, timeout, and retry config per external API)
- [x] Open-Meteo weather lookup (free, no API key — good first integration).
      `clients/open_meteo.py`, using both `api.open-meteo.com/v1/forecast`
      (recent/near-future dates) and `archive-api.open-meteo.com/v1/archive`
      (older dates), whichever the date needs.
- [x] Sunrise/sunset lookup — confirmed one Open-Meteo call's `daily` block
      covers this too, no separate API needed (see AGENTS.md log entry).
- [ ] Tide API for the target region — **deliberately deferred, not
      forgotten**. No genuinely free, no-paid-tier-risk tide API could be
      confirmed for a region this app is actually targeting (NOAA CO-OPS is
      free but US-coastal-only). See AGENTS.md's 2026-09-28 log entry.
- [x] Store a weather snapshot on `Catch` at creation time — new nullable
      columns `temperature`/`conditions`/`sunrise`/`sunset` (no `tide_state`,
      see above) + migration `0b19934327fb_add_weather_snapshot_columns_to_catch.py`.
      Fetched synchronously in `POST /catch/` (now `async def`), never blocks
      catch creation on lookup failure (logs a warning, leaves fields null).
- [x] Research: async/await patterns in FastAPI route handlers, timezones,
      retries/backoff — `POST /catch/` awaits the lookup directly; retries are
      connection-level only via `clients/http.py`'s `httpx.AsyncHTTPTransport(retries=...)`,
      deliberately not retrying on 4xx/5xx to avoid hammering a bad request.
- [ ] Tests: mock the external HTTP calls (e.g. `httpx`'s `MockTransport` or
      monkeypatching) rather than hitting real APIs in CI — real network
      calls in a CI run are slow, flaky, and can hit rate limits. Not written
      yet (qa-tester's job, not backend-dev's) — flagged in the handoff report.

*Depends on step 9 (needs real coordinates to query) and benefits from step 8
being done first (accurate, timezone-correct `date_caught` to query weather
"at the time of the catch" rather than "at import time" or shifted hours off).*

## 11. Caching (Redis)

- [ ] Redis running locally
- [ ] Cache weather/tide lookups by (rounded lat/long, date) — same
      catch logged twice nearby on the same day shouldn't re-hit the
      external API
- [ ] Cache species reference data once step 12 adds a species table
- [ ] TTL / invalidation strategy

*Natural follow-up to step 10 once real external-API traffic exists to
justify caching — premature before that.*

## 12. Data model growth

- [ ] `species` table (currently `Catch.species` is free text, not a
      relation)
- [ ] `catch_lures` join table if a catch can reference more than one lure
- [ ] Photos: storage decision + multipart upload endpoint
- [ ] Decide UUID vs. int PKs before the schema has more foreign keys
      pointing at it

## 13. Frontend polish

- [ ] Edit/delete UI for lures and catches (backend `PATCH`/`DELETE` already
      exist, see step 4 — just not exposed in the UI yet)
- [ ] Pagination or at least a reasonable limit on the list views (backend
      already supports `skip`/`limit`)
- [ ] Species picker (once step 12's species table exists) instead of free text
- [ ] Display weather/tide snapshot on a catch (once step 10 exists)
- [ ] General visual pass — current styling is intentionally minimal/rough

## 14. Background jobs (RabbitMQ + Celery)

- [ ] RabbitMQ running locally
- [ ] Celery worker setup
- [ ] Move image processing (step 12's photo uploads) to a background task
- [ ] Revisit step 10's weather fetch as an async job here if synchronous
      fetching turns out to be too slow/flaky in practice
- [ ] Notifications job

## 15. Containerization

- [ ] Dockerfile for the API
- [ ] `docker-compose` for API + Postgres + Redis + RabbitMQ
- [ ] Volumes and networks

*Why this late: containerizing before the service list (Postgres, Redis,
RabbitMQ) stabilizes just means rewriting the compose file repeatedly.*

## 16. CI/CD

- [x] GitHub Actions: backend tests + frontend build on every PR, required
      status checks on `main`
- [ ] Add lint + typecheck to the same workflow once Ruff/Pyright are
      configured (step 1)
- [ ] Deploy to Railway
- [ ] Later: AWS

## 17. Future / stretch

- Social feed, comments, followers
- Maps
- ML lure recommendations, spot recommendations
- Mobile app
