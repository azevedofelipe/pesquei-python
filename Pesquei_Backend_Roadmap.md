# Pesquei Backend Roadmap

## About this project

Pesquei started as a manual, learn-every-line backend project (FastAPI + PostgreSQL)
to learn backend fundamentals. It's now shifting focus: instead of writing every
change by hand, development happens with AI coding agents (Claude Code and similar).
The learning goal shifts too — from "how do I write a REST API" to "how do I direct,
review, and collaborate with an agent building one."

Practical implications of that shift:
- This file is the source of truth for **what exists**, **what's next**, and
  **what stack we're on** — an agent should be able to read this file cold and
  know where the project stands, without re-deriving it from scratch every time.
- Keep it updated as work lands. When a phase's status changes, update it here
  in the same session — don't let this drift from the actual code.
- Prefer small, reviewable steps. Since Felipe isn't hand-writing every line
  anymore, code review (reading diffs, understanding *why*) is the primary way
  he stays in control of the project and keeps learning.

## Useful commands to remember

- Update models.py with sqlacodegen pulling from DB
´sqlacodegen postgresql://postgres:password@localhost:5432/pesquei | Out-File -Encoding utf8 models.py´

- Create a new alembic revision and then upgrade head
´alembic revision -m "Message"´
´alembic upgrade head´

- Start fastapi dev server
´fastapi dev main.py´

---

## Stack

### Actually in use (installed, imported in code)
- Python 3.13
- FastAPI 0.141 — https://fastapi.tiangolo.com/
- Uvicorn (via `fastapi dev`) — https://www.uvicorn.org/
- SQLAlchemy 2.0 (declarative models, `Session`) — https://docs.sqlalchemy.org/en/20/
- Alembic 1.19 (migrations) — https://alembic.sqlalchemy.org/
- Pydantic v2 (request/response schemas) — https://docs.pydantic.dev/
- psycopg2-binary (Postgres driver)
- python-dotenv (loads `DATABASE_URL` from `.env`)
- PostgreSQL (local, connection via `DATABASE_URL`)
- sqlacodegen (regenerates `models.py` from the live DB schema)

- PyJWT (JWT signing for auth)
- bcrypt (password hashing)

### Installed but not wired into the project yet
- Ruff — installed, no `pyproject.toml`/`ruff.toml` config, not run in CI
- httpx — installed (FastAPI dependency), not used for outbound calls yet

### Planned, not started
- Pyright (no config)
- uv (a `pyproject.toml` exists now, but nothing installs from it yet — the
  `venv` is still populated by hand with matching versions)
- Redis, RabbitMQ, Celery
- Docker / Docker Compose
- pytest
- GitHub Actions (no `.github/workflows`)
- AWS / Railway deployment

---

## Current state (as of 2026-09-28)

### What exists
- **Models** (`models.py`, SQLAlchemy 2.0 style): `User`, `Lure`, `Catch`.
  - `Lure` and `Catch` each have a required FK to `User` (`user_id`) — every
    catch/lure belongs to exactly one user.
  - `Catch` also has a nullable FK to `Lure` (`lure_id`).
  - No `species` or `catch_lures` tables yet — `Catch.species` is just a free-text
    column, not a foreign key to a species table.
- **Migrations** (`alembic/versions/`): create user table, create catch table,
  update catch table (lat/long, notes, depth, lure FK), create lure table,
  add `user_id` to lure and catch.
- **Schemas** (`schemas/`): `UserCreate`/`UserResponse`, `CatchCreate`/`CatchResponse`/`CatchUpdate`,
  `LureCreate`/`LureResponse`/`LureUpdate`, `Token` (auth) — all Pydantic v2,
  `from_attributes=True` on responses.
- **Routers** (`routers/`):
  - `auth.py`: `POST /auth/register`, `POST /auth/login` (OAuth2 password
    flow, returns a JWT)
  - `catches.py`: `GET /catch/{catch_id}`, `GET /catch/` (list, own catches
    only), `POST /catch/`, `PATCH /catch/{catch_id}`, `DELETE /catch/{catch_id}`
    — all require auth and are scoped to the caller's own records (someone
    else's catch 404s, it doesn't 403 — same as a nonexistent one)
  - `lures.py`: same set of five, same auth/ownership scoping, for `Lure`
  - `users.py`: `GET /user/{user_id}` — auth required, only your own record
    (no create endpoint here; `POST /auth/register` is how a user is created)
- **Auth** (`security.py`): `get_current_user` (JWT `Depends`),
  `hash_password`/`verify_password` (bcrypt), `create_access_token` (PyJWT).
  `SECRET_KEY` lives in `.env`.
- **App wiring** (`main.py`): FastAPI app includes the auth, catches, lures,
  and users routers. No `/health` endpoint.
- **DB access** (`database.py`): SQLAlchemy engine + `SessionLocal`, `get_db()`
  dependency reads `DATABASE_URL` from `.env`.
- **`pyproject.toml`** exists (dependency list only, no lockfile yet).

### Notable gaps vs. what a "done" phase would look like
- No refresh tokens (Phase 3's last item).
- No `/health` endpoint (called for in Phase 1).
- No tests anywhere in the repo.
- No lint/type-check config despite Ruff and (eventually) Pyright being on
  the intended stack.
- `pyproject.toml` exists but nothing installs from it yet (no `uv`/lockfile
  workflow) — the local `venv` is still hand-populated to match it.
- No README.md.
- No CI (`.github/workflows` doesn't exist).

---

## Next up (short-term backlog)

Roughly in the order it makes sense to tackle them:

1. ~~Fix the local `venv/`~~ — done 2026-09-28 (rebuilt from Python 3.12).
2. ~~Pin dependencies~~ — `pyproject.toml` merged in from
   `azevedofelipe/link-records-to-user` 2026-09-28 (still no lockfile/`uv`
   workflow, but the dependency list exists and is accurate).
3. ~~Add `GET /catch`, `GET /lure` (list) and `DELETE`/`PATCH` for both
   resources~~ — done 2026-09-28.
4. ~~Add a `users` router~~ — done 2026-09-28, reshaped: fetch-only, since
   ~~Start Phase 3 (auth)~~ landed the same day via a merged branch and
   `POST /auth/register` already covers user creation.
5. Fix `CatchCreate.date_caught` default (see `AGENTS.md` — still not done).
6. Add `/health`.
7. Basic Ruff config + a first pass of lint cleanup.
8. Refresh tokens (the one piece of Phase 3 still missing).
9. Introduce pytest with at least endpoint-level tests for existing routes
   before adding much more surface area — now unblocked, since the venv
   works and the whole auth + catch/lure/user surface has been manually
   verified once already (register/login/CRUD/ownership checks all passed
   2026-09-28).

The phase list below is the longer-term roadmap and stays mostly as originally
planned — it's ordering *by topic*, not a strict sequence, and it's fine to
pull earlier items (like testing or Docker) forward if that's what a given
agent session is working on.

---

# Phase 0 – Environment

Learn:
- Git basics
- GitHub
- VS Code debugging
- uv
- Ruff
- Pyright

Research:
- virtual environments
- semantic versioning
- Conventional Commits
- .gitignore

Tasks:
- [x] Create GitHub repo
- [ ] Create README.md
- [ ] Configure Ruff and Pyright
- [x] First commit

---

# Phase 1 – FastAPI

Build:
- [ ] GET /health
- [x] CRUD for fish catches — full: GET (by id + list), POST, PATCH, DELETE,
      no in-memory stage (went straight to DB-backed)

Research:
- REST APIs
- HTTP methods
- Status codes
- Dependency Injection
- OpenAPI/Swagger

---

# Phase 2 – PostgreSQL

Install PostgreSQL. — done (local instance in use)

Research:
- Primary Keys
- Foreign Keys
- One-to-many
- Many-to-many
- Indexes
- Normalization

Tables:
- [x] users
- [x] catches
- [ ] species
- [x] lures
- [ ] catch_lures

Use:
- [x] SQLAlchemy
- [x] Alembic

---

# Phase 3 – Authentication

Status: done except refresh tokens (merged in from
`azevedofelipe/link-records-to-user` 2026-09-28). JWT via PyJWT, bcrypt
password hashing, OAuth2 password flow, catch/lure/user routes all require
auth and are scoped to the caller's own records.

Research:
- JWT
- OAuth2 Password Flow
- Password hashing
- Refresh tokens

Implement:
- [x] Register (`POST /auth/register`)
- [x] Login (`POST /auth/login`)
- [x] Protected routes (catch, lure, user routes all require a valid token)
- [ ] Refresh tokens

---

# Phase 4 – Docker

Containerize:
- [ ] API
- [ ] PostgreSQL

Research:
- Dockerfile
- docker-compose
- Volumes
- Networks

---

# Phase 5 – Fishing Features

Implement:
- [x] Catch log (basic)
- [ ] Species (as its own table/relation, not a free-text field)
- [x] Lure inventory (basic)
- [ ] Photos
- [x] GPS coordinates (lat/long columns exist on Catch)

Research:
- Multipart uploads
- UUIDs

---

# Phase 6 – External APIs

Use:
- Open-Meteo
- Sunrise/Sunset API
- Tide API for your region

Research:
- async/await
- httpx
- Timezones
- Rate limiting
- Retries

Store weather snapshot with each catch.

---

# Phase 7 – Redis

Cache:
- Weather
- Species
- Frequent lookups

Research:
- Cache invalidation
- TTL

---

# Phase 8 – RabbitMQ

Move slow tasks:
- Image processing
- Notifications
- Future ML jobs

Research:
- Message queues
- Producers/Consumers
- Celery workers

---

# Phase 9 – Testing

Learn:
- pytest
- Fixtures
- Mocking
- Integration tests

Aim for endpoint tests.

---

# Phase 10 – CI/CD

GitHub Actions:
- Lint
- Type check
- Tests

Deploy to Railway, later AWS.

---

# Future

- Social feed
- Comments
- Followers
- Maps
- ML lure recommendations
- Spot recommendations
- Mobile app
