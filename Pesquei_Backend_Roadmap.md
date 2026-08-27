# Pesquei Backend Roadmap

## Useful commands to remember

- Update models.py with sqlacodegen pulling from DB
´sqlacodegen postgresql://postgres:password@localhost:5432/pesquei | Out-File -Encoding utf8 models.py´

- Create a new alembic revision and then upgrade head
´alembic revision -m "Message"´
´alembic upgrade head´

- Start fastapi dev server
´fastapi dev main.py´

## Goal
Build a production-style backend while learning technologies in the order they become useful.

## Stack
- Python 3.13+
- FastAPI — https://fastapi.tiangolo.com/
- Uvicorn — https://www.uvicorn.org/
- uv (package manager) — https://docs.astral.sh/uv/
- Ruff — https://docs.astral.sh/ruff/
- Pyright — https://github.com/microsoft/pyright
- PostgreSQL — https://www.postgresql.org/docs/
- SQLAlchemy 2 — https://docs.sqlalchemy.org/en/20/
- Alembic — https://alembic.sqlalchemy.org/
- Pydantic v2 — https://docs.pydantic.dev/
- httpx — https://www.python-httpx.org/
- Redis — https://redis.io/docs/
- RabbitMQ — https://www.rabbitmq.com/docs
- Celery — https://docs.celeryq.dev/
- Docker — https://docs.docker.com/
- Docker Compose — https://docs.docker.com/compose/
- pytest — https://docs.pytest.org/
- GitHub Actions — https://docs.github.com/actions
- AWS (later) — https://docs.aws.amazon.com/

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
- Create GitHub repo
- Create README.md
- Configure Ruff and Pyright
- First commit

---

# Phase 1 – FastAPI

Build:
- GET /health
- CRUD for fish catches (in memory)

Research:
- REST APIs
- HTTP methods
- Status codes
- Dependency Injection
- OpenAPI/Swagger

---

# Phase 2 – PostgreSQL

Install PostgreSQL.

Research:
- Primary Keys
- Foreign Keys
- One-to-many
- Many-to-many
- Indexes
- Normalization

Tables:
- users
- catches
- species
- lures
- catch_lures

Use:
- SQLAlchemy
- Alembic

---

# Phase 3 – Authentication

Research:
- JWT
- OAuth2 Password Flow
- Password hashing
- Refresh tokens

Implement:
- Register
- Login
- Protected routes

---

# Phase 4 – Docker

Containerize:
- API
- PostgreSQL

Research:
- Dockerfile
- docker-compose
- Volumes
- Networks

---

# Phase 5 – Fishing Features

Implement:
- Catch log
- Species
- Lure inventory
- Photos
- GPS coordinates

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

