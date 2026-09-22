# MissionLens

MissionLens is a secure, full-stack mission intelligence workspace that helps analysts search multilingual reports, visualize geospatial events, organize evidence into cases, and route sensitive actions through human approval.

The project demonstrates end-to-end technical ownership across requirements discovery, architecture, implementation, security, deployment, testing, and sustainment.

## Problem

Mission teams may receive large amounts of information from different sources, locations, formats, and languages. Fragmented systems make it difficult to:

- Find relevant information quickly
- Connect reports involving the same location or event
- Establish the source and provenance of information
- Prioritize time-sensitive cases
- Control sensitive actions
- Maintain a complete audit history

MissionLens provides one controlled workflow for discovering, reviewing, connecting, and acting on mission-relevant information.

## Users

### Analyst

- Searches and filters reports
- Reviews source and location information
- Visualizes events on a map
- Creates investigation cases
- Submits proposed actions for approval

### Supervisor

- Reviews proposed actions and evidence
- Approves or rejects sensitive actions
- Adds decision explanations
- Reviews case and audit history

### Administrator

- Manages users and roles
- Configures system integrations
- Reviews security events
- Monitors system health

## MVP Workflow

1. Ingest a synthetic multilingual report.
2. Extract its language, source, timestamp, and location.
3. Store and index the normalized report.
4. Search reports by keyword, language, date, and location.
5. Display associated events on a map.
6. Add relevant reports to an investigation case.
7. Submit a proposed action for supervisor approval.
8. Approve or reject the action.
9. Record every important event in an audit trail.

## Technology Stack

### Frontend

- React
- TypeScript
- Vite
- MapLibre
- Vitest

### Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Pytest

### Data and Infrastructure

- PostgreSQL
- PostGIS
- Redis
- S3-compatible object storage
- Docker Compose

## Planned Architecture

- React analyst workspace for search, maps, cases, and approvals
- FastAPI service for reports, cases, approvals, users, and audit events
- PostgreSQL/PostGIS for relational and geospatial data
- Redis for caching, job status, rate limiting, and idempotency
- S3-compatible storage for original reports and multimedia
- Background worker for ingestion and metadata normalization
- Structured logging, health checks, metrics, and request correlation

## Security Principles

MissionLens will demonstrate:

- Role-based access control
- Least-privilege authorization
- Human approval for sensitive actions
- Traceable audit events
- Input validation
- Idempotent ingestion
- Secrets separation
- Dependency scanning
- Secure configuration defaults

## Success Criteria

- Every privileged endpoint verifies the user’s role.
- Every approval decision creates an audit event.
- Duplicate report ingestion is safely rejected or reused.
- The critical analyst-to-approval workflow is covered by automated tests.
- Search requests meet the documented performance target.
- The application can be started using documented commands.
- Failures are observable and supported by a recovery runbook.

## Project Phases

### Phase 1: Thin Vertical Slice

Build the report, map, case, approval, and audit workflow using synthetic data.

### Phase 2: Reliability and Scale

Add PostgreSQL/PostGIS, Redis, background processing, retries, idempotency, observability, and performance tests.

### Phase 3: Deployment Readiness

Add containerized deployment, monitoring, backup and recovery, identity and SIEM adapters, and operational documentation.

### Phase 4: RMF-Informed Documentation

Create a control responsibility matrix, system boundary, data-flow diagram, risk register, incident-response procedure, and evidence index.

## Important Boundaries

- This is an independent portfolio project.
- It is not affiliated any government organization.
- It does not use classified, controlled, or proprietary information.
- All demonstration data is synthetic or openly licensed.
- “RMF-informed” does not mean RMF-authorized or RMF-compliant.
