# Fleet Owner & Truck Onboarding Platform — Requirements

## 1. Purpose

Build a logistics startup platform for onboarding fleet owners and their trucks.

The platform must:
- onboard fleet owners and fleets;
- capture and verify truck registration details;
- integrate with authorized vehicle-verification providers such as API Setu/VAHAN;
- preserve raw provider responses;
- normalize vehicle data into a canonical truck model;
- derive missing taxonomy attributes with deterministic rules;
- maintain provenance for derived attributes;
- support manual review;
- be low-cost for an MVP;
- remain portable across AWS, Azure, GCP, and self-hosted environments.

## 2. MVP Scope

### In scope
- Fleet owner registration/authentication
- Tenant/company creation
- Fleet creation
- Truck/vehicle onboarding
- Registration number capture
- External vehicle verification
- Raw response storage
- Vehicle normalization
- Rule-based enrichment
- Truck classification
- Document upload and metadata
- Manual review
- Audit trail
- Fleet/vehicle search
- Basic operational APIs
- Logging, metrics, tracing, error handling

### Out of scope
- Driver marketplace
- Route optimization
- Freight matching
- Payments
- GPS/telematics
- Predictive maintenance
- Full AI-first onboarding

## 3. Roles

### Fleet Owner
Register, manage fleet, add vehicles, submit verification, upload documents, view status.

### Fleet Admin
Manage fleet and vehicles, documents, users.

### Verification Agent
Review failed/ambiguous cases, approve/reject, override derived fields with reason.

### Platform Admin
Manage tenants, taxonomy, rules, integrations, and audit information.

## 4. Multi-Tenancy

Core tenant-owned entities must contain `tenant_id`.

Entities:
- tenant
- fleet_owner
- fleet
- vehicle
- vehicle_document
- onboarding_case
- verification_case
- audit_event

Tenant isolation is mandatory.

## 5. Vehicle Onboarding Workflow

Operators do not type RC fields. They create a draft with a fleet and registration number, populate from the vehicle provider and rules, then review the result.

```text
Create DRAFT (fleet + registration number)
 -> POST /v1/vehicles/{id}/populate
 -> Provider lookup (API Setu or fake/mock)
 -> Persist canonical attributes
 -> Apply deterministic rules
 -> READY_FOR_REVIEW  (provider + rules succeeded)
    or MANUAL_REVIEW  (provider failed; retry populate is allowed)
 -> Human review: APPROVE or REJECT
```

Realtime populate:

```text
POST /v1/vehicles/{vehicle_id}/populate
```

Batch populate (bulk-upload follow-up; max 100 ids; one failure does not abort the batch):

```text
POST /v1/vehicles/populate-batch
{ "vehicle_ids": ["..."] }
```

Human review:

```text
POST /v1/vehicles/{vehicle_id}/review
{ "decision": "APPROVE" | "REJECT" }
```

`/verify` and `/verify-batch` remain as aliases of populate.

Vehicle states:
- DRAFT
- SUBMITTED
- VERIFICATION_PENDING
- VERIFIED
- ENRICHMENT_PENDING
- READY_FOR_REVIEW
- MANUAL_REVIEW
- APPROVED
- REJECTED
- SUSPENDED

Populate chains DRAFT → SUBMITTED → VERIFICATION_PENDING, then either MANUAL_REVIEW or VERIFIED → ENRICHMENT_PENDING → READY_FOR_REVIEW. Humans decide from READY_FOR_REVIEW or MANUAL_REVIEW.

Transitions must be controlled and auditable.

## 6. Vehicle Data

Capture when available:
- registration number/date/status
- registration authority
- manufacturer
- model
- variant
- manufacturing month/year
- chassis number
- engine number
- vehicle category
- vehicle class
- body type
- fuel type
- GVW
- unladen weight
- cylinder count
- engine displacement
- seating/sleeper/standing capacity
- wheelbase
- emission norm
- fitness validity
- tax validity
- insurance details
- PUC details
- blacklist/NOC details

Sensitive identifiers must be masked in logs and protected at rest.

## 7. Canonical Truck Taxonomy

Keep these concepts separate:

### Regulatory Category
Derived from GVW unless an authoritative regulatory field exists:
- N1: <= 3.5 tonnes
- N2: > 3.5 and <= 12 tonnes
- N3: > 12 tonnes

Thresholds must be configurable/versioned.

### Commercial Segment
Business-defined:
- LCV
- ICV
- M&HCV
- HCV

### Configuration
- RIGID
- TRACTOR
- TIPPER
- SPECIAL_PURPOSE
- TRACTOR_TRAILER

### Body Type
- OPEN
- FLATBED
- HIGH_SIDE
- CLOSED
- CONTAINER
- TANKER
- REFRIGERATED
- TIPPER
- CAR_CARRIER
- LOG_CARRIER
- CEMENT_MIXER
- SPECIAL_PURPOSE

### Axle Configuration
- 4X2
- 6X2
- 6X4
- 8X2
- 8X4

Do not infer exact axle configuration from model name unless a trusted source/master confirms it.

### Powertrain
- DIESEL
- CNG
- LNG
- ELECTRIC
- HYDROGEN
- OTHER

## 8. Rule-Based Enrichment

Rules may derive missing values only when deterministic or sufficiently trusted.

Examples:

```text
GVW <= 3500                -> N1
3500 < GVW <= 12000        -> N2
GVW > 12000                -> N3
"TRUCK (OPEN BODY)"        -> OPEN
"TIPPER"/"DUMPER"          -> TIPPER
"TATA MOTORS LTD"          -> TATA_MOTORS
estimated_payload          -> GVW - unladen_weight
```

Estimated payload must be flagged as derived, not authoritative OEM capacity.

Rule metadata:
- rule_id
- name
- version
- type
- expression/logic
- priority
- active
- effective_from/to
- author
- timestamps

## 9. Data Provenance

Important canonical attributes must retain:
- source_system
- source_field
- source_record_id
- transformation_type
- rule_id
- rule_version
- confidence
- timestamp

Example:

```text
attribute = regulatory_category
value = N3
source = DERIVED
rule_id = RULE-GVW-N-CATEGORY-001
confidence = 1.0
```

## 10. External Vehicle API

Use an adapter interface:

```python
class VehicleVerificationProvider:
    async def verify_registration(
        self,
        registration_number: str,
        context: VerificationContext,
    ) -> VehicleVerificationResult:
        ...
```

Provider-specific XML/JSON parsing belongs only in the adapter.

Requirements:
- timeout
- retry with backoff
- idempotency
- rate limiting
- correlation/request ID
- error mapping
- raw response preservation

## 11. Documents

Initial document types:
- RC
- Insurance
- Fitness
- PUC
- Permit
- Owner KYC

Files go to object storage. PostgreSQL stores metadata.

Document metadata:
- document_id
- tenant_id
- vehicle_id
- document_type
- object_key
- version
- checksum
- uploaded_by
- uploaded_at
- verification_status

## 12. Manual Review

Trigger manual review for:
- provider failure
- incomplete response
- document mismatch
- conflicting sources
- low-confidence derivation
- suspicious information

Actions:
- approve
- reject
- override
- request correction

Overrides must capture old value, new value, reason, reviewer, timestamp.

## 13. API

Suggested endpoints:

```text
POST   /v1/owners
GET    /v1/owners/{owner_id}

POST   /v1/fleets
GET    /v1/fleets/{fleet_id}
PATCH  /v1/fleets/{fleet_id}

POST   /v1/vehicles
GET    /v1/vehicles/{vehicle_id}
PATCH  /v1/vehicles/{vehicle_id}

POST   /v1/vehicles/{vehicle_id}/populate
POST   /v1/vehicles/populate-batch
POST   /v1/vehicles/{vehicle_id}/review
POST   /v1/vehicles/{vehicle_id}/verify
GET    /v1/vehicles/{vehicle_id}/verification

POST   /v1/vehicles/{vehicle_id}/documents
GET    /v1/vehicles/{vehicle_id}/documents

POST   /v1/onboarding/{case_id}/submit
GET    /v1/onboarding/{case_id}

GET    /v1/truck-models
GET    /v1/master-data/*
```

## 14. Non-Functional Requirements

- p95 CRUD API <= 500 ms excluding external providers
- external verification is asynchronous
- 99.5% monthly MVP availability target
- idempotent external verification
- retries + dead-letter handling
- structured logs
- OpenTelemetry traces/metrics
- TLS everywhere
- encryption at rest
- least privilege
- no secrets in code
- sensitive fields masked in logs

## 15. Portability

The domain/application layers must not directly use AWS SDKs.

Provide interfaces for:
- DatabaseRepository
- ObjectStorage
- AuthProvider
- Queue
- EventPublisher
- WorkflowEngine
- SecretProvider
- VehicleVerificationProvider

Implement AWS adapters separately.

## 16. Recommended Baseline

- Python 3.12+
- FastAPI
- Pydantic v2
- SQLAlchemy 2
- Alembic
- PostgreSQL
- Docker
- Terraform
- Pytest
- Ruff
- Pyright/MyPy
- OpenTelemetry

## 17. Definition of Done for Vehicle Approval

A vehicle is APPROVED only when:
- owner active
- fleet active
- registration valid
- external/manual verification complete
- raw source response persisted
- canonical fields stored
- regulatory classification present
- provenance stored for derived fields
- required documents verified
- audit trail complete

## 18. Cursor Rules

Before implementation:
1. Read `REQUIREMENTS.md`.
2. Read `ARCHITECTURE.md`.
3. Preserve domain/application/infrastructure boundaries.
4. Never put AWS SDK calls in domain services.
5. Add migrations for schema changes.
6. Add tests for new rules and use cases.
7. Keep provider-specific transformations in adapters.
8. Keep local development runnable with Docker Compose.
9. Prefer the simplest production-safe approach.
10. Update requirements/architecture when a structural decision changes.
