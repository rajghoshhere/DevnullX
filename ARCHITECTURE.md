# Fleet Owner & Truck Onboarding Platform — Architecture

## 1. Goals

- Low-cost startup architecture
- AWS-first deployment without AWS lock-in
- Modular monolith first
- PostgreSQL as canonical transactional store
- Object storage for documents/raw responses
- OIDC/OAuth2 authentication
- Async verification
- Deterministic enrichment
- Strong provenance and auditability
- Clear migration path to Azure/GCP/self-hosted

## 2. Logical Architecture

```text
Fleet Owner App
      |
    HTTPS
      |
  FastAPI API/BFF
      |
Application Services
      |
Domain Services
      |
+-----+---------+----------+
|               |          |
Fleet        Vehicle   Onboarding
Domain       Domain      Domain
      \        |        /
       +-------+-------+
               |
          Ports / Interfaces
               |
+--------------+--------------+----------------+
|              |              |                |
DB Port    Storage Port    Auth Port       Queue Port
|              |              |                |
PostgreSQL  Object Store   OIDC/OAuth2    Queue/Event
```

## 3. Physical AWS MVP

```text
CloudFront / WAF
       |
Web App
       |
API Gateway
       |
ECS Fargate / Docker
       |
+------+----------------------+
|                             |
v                             v
Application              Background Worker
Service                       |
|                             |
+-------------+---------------+
              |
        RDS PostgreSQL
              |
       +------+------+
       |             |
       v             v
      S3            SQS
                     |
                     v
              Verification Worker
                     |
                     v
             External Vehicle API
```

AWS services should be implementations of cloud-neutral interfaces.

## 4. Recommended AWS MVP Services

| Capability | AWS MVP | Portable abstraction |
|---|---|---|
| Compute | ECS Fargate | Docker |
| DB | RDS PostgreSQL | PostgreSQL |
| Files | S3 | ObjectStorage |
| Auth | Cognito | OIDC/OAuth2 |
| Async | SQS | Queue |
| Events | optional EventBridge | EventPublisher |
| Workflow | DB state + worker first | WorkflowEngine |
| Secrets | Secrets Manager | SecretProvider |
| Observability | CloudWatch + OTel | OpenTelemetry |
| IaC | Terraform | Terraform |

Avoid EventBridge/Step Functions until workflow complexity justifies them.

## 5. Architecture Style

Use Ports and Adapters / Hexagonal Architecture.

### Domain
Business rules and entities only.

No:
- boto3
- Cognito SDK
- SQS SDK
- API Setu parsing
- AWS event types

### Application
Use-case orchestration and transaction boundaries.

### Adapters
Infrastructure implementations:
- PostgreSQL
- S3
- SQS
- Cognito/OIDC
- API Setu
- email/SMS

### API
HTTP validation, authentication context, response formatting, API versioning.

## 6. Suggested Repository Layout

```text
src/
├── domain/
│   ├── owner/
│   ├── fleet/
│   ├── vehicle/
│   ├── truck/
│   ├── onboarding/
│   └── verification/
│
├── application/
│   ├── commands/
│   ├── queries/
│   └── services/
│
├── ports/
│   ├── repositories.py
│   ├── storage.py
│   ├── auth.py
│   ├── queue.py
│   ├── event_bus.py
│   ├── workflow.py
│   └── vehicle_provider.py
│
├── adapters/
│   ├── postgres/
│   ├── aws/
│   │   ├── s3.py
│   │   ├── sqs.py
│   │   └── secrets.py
│   ├── auth/
│   │   ├── cognito.py
│   │   └── oidc.py
│   └── vehicle_providers/
│       └── api_setu.py
│
├── api/
│   ├── routes/
│   ├── schemas/
│   └── dependencies.py
│
├── workers/
│   ├── verification_worker.py
│   ├── enrichment_worker.py
│   └── document_worker.py
│
├── config/
│   └── settings.py
│
└── main.py
```

## 7. Core Database Model

```text
tenant
  |
  +-- fleet_owner
  |
  +-- fleet
         |
         +-- vehicle
                |
                +-- vehicle_document
                +-- verification_case
                +-- vehicle_attribute_provenance
                +-- external_api_response
```

Truck taxonomy:

```text
manufacturer
truck_model
truck_variant
regulatory_category
truck_segment
truck_configuration
body_type
axle_configuration
powertrain
truck_application
```

Key relationships:

```text
manufacturer 1 --- * truck_model
truck_model 1 --- * vehicle
fleet 1 --- * vehicle
vehicle 1 --- * vehicle_document
vehicle 1 --- * verification_case
vehicle 1 --- * attribute_provenance
```

One `truck_model` represents what a truck is; one `vehicle` represents an actual registered truck.

## 8. Vehicle Processing Pipeline

```text
External Vehicle API
       |
Provider Adapter
       |
Raw Response Persistence
       |
Canonical DTO
       |
Normalization
       |
Validation
       |
Rule Engine
       |
Canonical Vehicle
       |
Verification / Manual Review
       |
APPROVED
```

## 9. Raw Response Storage

S3/object-store layout:

```text
raw/
  {provider}/
    {yyyy}/{mm}/{dd}/
      {tenant_id}/
        {vehicle_id}/
          {correlation_id}.xml
```

DB metadata:

```text
external_api_response
---------------------
response_id
tenant_id
vehicle_id
provider
request_id
response_status
object_key
sha256
received_at
```

Raw data is immutable evidence, not the canonical operational source.

## 10. Rule Engine

Rules are data-driven:

```text
rule_master
-------------------
rule_id
name
version
rule_type
expression
priority
active
effective_from
effective_to
```

Examples:
- GVW -> N1/N2/N3
- body text -> canonical body type
- OEM aliases -> canonical manufacturer
- GVW - unladen weight -> estimated payload

Every derived attribute stores rule ID, version, source, and confidence.

## 11. Onboarding Workflow

```text
DRAFT  (fleet + registration number)
  |
populate (provider + rules)
  |
  +----> MANUAL_REVIEW  (provider failed; retry populate allowed)
  |              |
  |              v
  |        APPROVED / REJECTED
  |
READY_FOR_REVIEW
  |
APPROVED / REJECTED
```

Internal populate chain (not a human step):

```text
DRAFT -> SUBMITTED -> VERIFICATION_PENDING
  -> VERIFIED -> ENRICHMENT_PENDING -> READY_FOR_REVIEW
```

or `VERIFICATION_PENDING -> MANUAL_REVIEW`.

Example:

```text
POST /v1/vehicles/{id}/populate
        |
        v
Vehicle provider (API Setu adapter, fake, or local mock)
        |
        v
Canonical attributes on the vehicle
        |
        v
Rule engine + provenance
        |
        v
READY_FOR_REVIEW or MANUAL_REVIEW

POST /v1/vehicles/{id}/review  { "decision": "APPROVE" | "REJECT" }
```

Domain and application layers never see API Setu XML. The HTTP adapter maps `rc_*` tags to `VerifiedVehicleAttributes`. A local mock server (`scripts/run_mock_api_setu.py`) speaks the same XML contract for testing.

## 12. Idempotency

Use:
```text
tenant_id + normalized_registration_number
```
as the uniqueness boundary for active vehicles.

Use idempotency keys for verification requests.

Never allow duplicate processing of the same verification event.

## 13. Security

Authentication:
```text
User -> OIDC Provider -> JWT -> FastAPI
```

Authorization:
- tenant authorization
- role authorization
- domain authorization

Sensitive data:
- encrypt at rest
- TLS in transit
- mask in logs
- audit high-risk changes
- never commit secrets

## 14. Observability

OpenTelemetry for:
- HTTP
- DB
- queues
- external API calls
- workers

Context:
- request_id
- correlation_id
- tenant_id
- user_id where appropriate

Core metrics:
- onboarding completion
- verification success/failure
- provider latency
- manual review rate
- onboarding time
- duplicate vehicle rate
- rule mismatch rate

## 15. Local Development

Use Docker Compose:

```text
docker-compose
  |
  +-- FastAPI
  +-- PostgreSQL
  +-- MinIO
  +-- Local worker
```

The same API/domain code should run locally and in AWS.

## 16. Deployment

### Dev
Docker Compose.

### Staging
- ECS Fargate
- RDS PostgreSQL
- S3
- SQS
- Cognito
- Terraform

### Production
Start small:
- 2 application tasks or equivalent baseline
- RDS PostgreSQL
- S3
- SQS
- Secrets Manager
- OpenTelemetry/CloudWatch
- WAF

Scale horizontally as usage grows.

## 17. Infrastructure as Code

Use Terraform:

```text
infra/
├── modules/
│   ├── network/
│   ├── postgres/
│   ├── object_storage/
│   ├── container_service/
│   ├── queue/
│   ├── identity/
│   └── observability/
│
├── environments/
│   ├── dev/
│   ├── staging/
│   └── prod/
│
└── aws/
```

Do not encode domain rules in Terraform.

## 18. Cloud Migration Strategy

### AWS -> Azure

```text
RDS PostgreSQL -> Azure PostgreSQL
S3             -> Azure Blob
SQS            -> Azure Service Bus
Cognito        -> Entra/Auth0
ECS            -> Azure Container Apps
```

### AWS -> GCP

```text
RDS PostgreSQL -> Cloud SQL PostgreSQL
S3             -> Cloud Storage
SQS            -> Pub/Sub
Cognito        -> Identity Platform/Auth0
ECS            -> Cloud Run
```

Domain/application code remains unchanged.

## 19. Architecture Decision Records

### ADR-001 — Modular Monolith First
Use a modular monolith to minimize cost and operational complexity.

### ADR-002 — PostgreSQL Canonical Store
Use PostgreSQL because the domain is relational and portability is important.

### ADR-003 — Object Store for Files/Raw Data
Use object storage for documents and immutable raw provider responses.

### ADR-004 — OIDC/OAuth2
Use standards-based authentication to avoid identity-provider lock-in.

### ADR-005 — Provider Adapter
External vehicle APIs are adapters behind a stable interface.

### ADR-006 — Rules Before AI
Use deterministic rules for explainable truck classification; AI only for ambiguous cases.

### ADR-007 — Containers
Package the backend as a Docker container so compute can move among ECS, Cloud Run, Azure Container Apps, Kubernetes, or VMs.

## 20. Recommended Stack

```text
Frontend        React / Next.js
Backend         Python + FastAPI
Validation      Pydantic v2
ORM             SQLAlchemy 2
Migrations      Alembic
Database        PostgreSQL
Storage         S3-compatible
Auth            OIDC/OAuth2
Queue           SQS-compatible
Compute         Docker
AWS runtime     ECS Fargate
IaC             Terraform
Testing         Pytest
Lint            Ruff
Typing          Pyright/MyPy
Observability   OpenTelemetry
Verification    API Setu adapter
```

## 21. Hard Rules for Cursor

1. Read `REQUIREMENTS.md` and `ARCHITECTURE.md` before implementing.
2. Never place AWS SDK code in domain/application services.
3. Never bypass repository/storage/auth/queue/provider interfaces.
4. Never put business logic in FastAPI route handlers.
5. Every schema change requires an Alembic migration.
6. Every new rule requires unit tests.
7. Every external provider adapter requires integration tests.
8. Keep external provider XML/JSON mapping inside adapters.
9. Do not log secrets or full sensitive identifiers.
10. Keep local Docker Compose development working.
11. Prefer the simplest production-safe design.
12. When architecture changes, update the ADR section.
