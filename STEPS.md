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
      records, see step 5 — auth landed the same day as this work)
- [x] `PUT`/`PATCH` and `DELETE` for catch and lure — implemented as PATCH
      (partial update, `exclude_unset=True`) + DELETE (204)
- [x] `users` router: `GET /user/{id}` only, scoped to your own record —
      creation lives at `POST /auth/register` instead (see step 5); an
      earlier `POST /user/` was dropped as a duplicate once the auth branch
      (below) was merged in
- [ ] Fix `CatchCreate.date_caught` default (see `AGENTS.md` — evaluated once
      at import time, not per-request)

*Why now: this is the minimum surface a real client could build against, and
it's needed before auth (below) has anything worth protecting.*

## 5. Authentication

- [x] Password hashing (bcrypt) on user creation (`POST /auth/register`)
- [x] `POST /auth/login` issuing a JWT (OAuth2 password flow)
- [x] `get_current_user` dependency; catch/lure/user routes all protected and
      scoped to the caller's own records
- [ ] Refresh tokens

*Note: this landed 2026-09-28 via merging an already-built, previously
unmerged branch (`azevedofelipe/link-records-to-user`) that had auth done
before step 4's CRUD work started on `main` — see `AGENTS.md` Log for what
that reconciliation involved.*

## 6. Data model growth

- [ ] `species` table (currently `Catch.species` is free text, not a
      relation)
- [ ] `catch_lures` join table if a catch can reference more than one lure
- [ ] Photos: storage decision + multipart upload endpoint
- [ ] Decide UUID vs. int PKs before the schema has more foreign keys
      pointing at it

## 7. External APIs

- [ ] Shared `httpx` async client wrapper
- [ ] Open-Meteo weather lookup
- [ ] Sunrise/sunset lookup
- [ ] Tide API for the target region
- [ ] Store a weather snapshot on each catch at creation time

## 8. Testing

- [ ] pytest + FastAPI `TestClient` setup, test DB fixture
- [ ] Endpoint tests for everything built in steps 2-6 before adding much
      more surface area
- [ ] Auth flow tests

*Why here, not earlier: there's enough surface area now to make tests worth
writing, and doing it before Redis/Celery/Docker means those get built
against a codebase that already has a safety net.*

## 9. Caching (Redis)

- [ ] Redis running locally
- [ ] Cache weather lookups and species reference data
- [ ] TTL / invalidation strategy

## 10. Background jobs (RabbitMQ + Celery)

- [ ] RabbitMQ running locally
- [ ] Celery worker setup
- [ ] Move image processing to a background task
- [ ] Notifications job

## 11. Containerization

- [ ] Dockerfile for the API
- [ ] `docker-compose` for API + Postgres + Redis + RabbitMQ
- [ ] Volumes and networks

*Why this late: containerizing before the service list (Postgres, Redis,
RabbitMQ) stabilizes just means rewriting the compose file repeatedly.*

## 12. CI/CD

- [ ] GitHub Actions: lint + typecheck + test on every PR
- [ ] Deploy to Railway
- [ ] Later: AWS

## 13. Future / stretch

- Social feed, comments, followers
- Maps
- ML lure recommendations, spot recommendations
- Mobile app
