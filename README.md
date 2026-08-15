# Fleet Owner & Truck Onboarding Platform

Python backend foundation for onboarding fleet owners and trucks.

This repository is a modular monolith with hexagonal (ports and adapters) boundaries. Domain and application code stay cloud-neutral. PostgreSQL, object storage, auth, queues, and vehicle providers are accessed through ports.

## Directory layout

| Path | Role |
| --- | --- |
| `src/domain/` | Entities, enums, and value objects. No infrastructure imports. |
| `src/application/` | Use cases and transaction orchestration (commands, queries, services). |
| `src/ports/` | Interfaces: repositories, object storage, queue, auth, vehicle verification. |
| `src/adapters/` | Infrastructure implementations. PostgreSQL is implemented; cloud providers are not. |
| `src/api/` | FastAPI routes, request/response schemas, and dependency injection. |
| `src/workers/` | Placeholders for async verification, enrichment, and document workers. |
| `src/config/` | Environment-backed settings and structured JSON logging. |
| `src/main.py` | ASGI entrypoint (`uvicorn main:app`). |
| `tests/` | API and repository tests. |
| `migrations/` | Alembic schema migrations. |
| `scripts/` | Container entrypoint (migrate, then start API). |

## Prerequisites

- Python 3.12+
- Docker and Docker Compose
- Copy environment variables: `cp .env.example .env`

Do not commit `.env`. Credentials come only from environment variables.

## Run locally (Docker Compose)

```bash
cp .env.example .env
make up
```

The API listens on `http://localhost:8000`.

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok"}`.

Compose also starts a mock API Setu service on `http://127.0.0.1:8099`. Start or rebuild only that service:

```bash
make mock-api-setu
```

That runs `docker compose --env-file .env up -d --build mock-api-setu`. Check it:

```powershell
Invoke-RestMethod http://127.0.0.1:8099/health
```

Expected: `{"status":"ok","provider":"mock-api-setu"}`. Logs: `make mock-api-setu-logs`.

To populate vehicles from the mock instead of the in-process fake, set in `.env` and recreate the API container:

```bash
# in .env
VEHICLE_VERIFICATION_PROVIDER=api_setu
API_SETU_BASE_URL=http://mock-api-setu:8099/vahan/rc
API_SETU_API_KEY=test-api-key
API_SETU_CLIENT_ID=test-client
```

Registrations containing `FAIL` return a provider error XML so you can exercise `MANUAL_REVIEW`.

Onboarding flow: create a tenant, fleet, and vehicle (registration number only), `POST /v1/vehicles/{id}/populate`, then `POST /v1/vehicles/{id}/review` with `APPROVE` or `REJECT`. Tenant-scoped routes require `X-Tenant-ID`.

Stop:

```bash
make down
```

## Run locally (host Python)

```bash
cp .env.example .env
make install
make migrate
PYTHONPATH=src .venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

PostgreSQL must be reachable at `DATABASE_URL`.

## Tests

Requires PostgreSQL (Compose `db` service or an equivalent instance) and `DATABASE_URL` in `.env`.

```bash
cp .env.example .env
docker compose --env-file .env up -d db
make install
make migrate
make test
```

Lint and types:

```bash
make lint
make typecheck
```

## Migrations

```bash
make migrate          # alembic upgrade head
make migrate-down     # alembic downgrade -1
make seed-taxonomy    # upsert truck taxonomy reference data
make seed-rules       # upsert enrichment rules
```

Inside Compose, the API container runs `alembic upgrade head` on startup. Taxonomy codes live in PostgreSQL reference tables (`body_types`, `powertrains`, and related tables), not in Python enums. Add new values by inserting rows or extending `src/adapters/postgres/data/taxonomy.json` and re-running the seed script.

## Ports (not implemented yet)

These interfaces exist so later adapters can plug in without touching domain code:

- `ObjectStorage`
- `Queue`
- `AuthProvider`
- `VehicleVerificationProvider`

PostgreSQL example: `TenantRepository` → `PostgresTenantRepository`.

See `REQUIREMENTS.md`, `ARCHITECTURE.md`, and `CURSOR.md` before adding features.
