# Cursor Project Instructions

Before implementing any feature:
1. Read `REQUIREMENTS.md`.
2. Read `ARCHITECTURE.md`.
3. Preserve domain/application/infrastructure separation.

Core principles:
- Modular monolith first.
- FastAPI + PostgreSQL + Docker.
- Cloud-neutral domain and application logic.
- Provider-specific implementations belong in adapters.
- Use OIDC/OAuth2 interfaces rather than provider-specific auth logic.
- Use object-storage and queue interfaces.
- Store raw external responses and documents in object storage.
- Use deterministic rules before AI enrichment.
- Maintain attribute provenance for derived values.
- Create vehicles as drafts with fleet + registration; populate from the vehicle provider, then have a human approve or reject. Do not treat operator-entered RC fields as the source of truth.
- Vehicle provider XML (API Setu) stays in adapters. Use the local mock API Setu server for tests.
- Use asynchronous workers for slow/external verification when moving off the request path.
- Add migrations and tests for schema/rule changes.
- Never hard-code secrets or environment-specific URLs.

Prefer the simplest production-safe solution that preserves cloud portability.
