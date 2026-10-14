# SecureWatch KE Requirements Traceability

## Assessment scope

This records the current state of the existing SecureScan repository after the first security increment. `PASS` means the stated requirement has evidence in this repository; existing code alone is not sufficient. `BLOCKED` means implementation or required environment/design work is still missing. `FAIL` means a verified acceptance criterion is currently unmet. `NOT_ASSESSED` means no reliable assessment was made.

This repository is currently a local, single-user SecureScan application, not a production-ready multi-tenant SecureWatch KE service. Domain verification, authentication, tenant authorization, and durable PostgreSQL migrations are not implemented. Do not expose the current scan endpoints as a commercial or public scanning service.

## Baseline and current API

Baseline verification before the security changes:

- `cd backend; .\venv313\Scripts\python.exe -m unittest discover -s tests -q` — 1 test passed.
- `cd frontend; npm run build` — TypeScript build and Vite production build passed.
- `pytest` was unavailable in the configured backend environment; the repository's existing test is `unittest`-based.

Existing endpoints and response models in `backend/app/main.py`:

| Method | Endpoint | Existing response |
| --- | --- | --- |
| GET | `/health` | `HealthResponse` |
| POST | `/scan` | `ScanReport`, HTTP 201 |
| GET | `/scans` | `List[ScanHistoryItem]` |
| GET | `/scans/{scan_id}` | `ScanReport` or 404 |
| DELETE | `/scans/{scan_id}` | `DeleteResponse` or 404 |
| GET | `/scans/{scan_id}/pdf` | PDF file or JSON error |

Existing scan checks are registered in `backend/app/services/scan_service.py`: TLS, HTTP security headers, cookies, HTTP-to-HTTPS redirect, server-header leakage, Nmap top-20 ports, and frontend library hints. SQLite history is stored in `ScanResult` with a JSON report. PDF generation is in `backend/app/services/pdf_service.py`.

## Master prompt requirements

| ID | Requirement | Existing implementation and files | Required change | Verification method | Status | Evidence and remaining limitations |
| --- | --- | --- | --- | --- | --- | --- |
| M-01 | Inspect and modify the existing repository; preserve current work and avoid a greenfield replacement. | Existing app under `backend/app` and `frontend/src`; repository status checked before changes. | Continue incremental changes in place and protect unrelated edits. | Review scoped Git diff and run targeted checks. | PASS | Existing application and routes were retained. |
| M-02 | Preserve scanner checks, API contracts, frontend pages, and configuration unless a change is necessary. | `backend/app/main.py`, `backend/app/services/scan_service.py`, `frontend/src/`. | Add regression coverage for each supported check and document any contract changes. | Backend regressions and frontend build. | BLOCKED | No routes or frontend files changed. Nmap's report `command` now names a vetted IP rather than a hostname; broad scanner regression coverage is still missing. |
| M-03A | PostgreSQL, SQLAlchemy models for users/organizations/domains/scans/findings/audit, constraints, UTC, and safe Alembic migrations. | `backend/app/database.py`, `backend/app/models.py`; current default is SQLite and startup uses `Base.metadata.create_all()`. | Design a backwards-compatible PostgreSQL model and migration path; do not reset existing SQLite data. | Migration review and clean plus representative-schema migration tests. | BLOCKED | No PostgreSQL driver, Alembic setup, new models, or migration tests. |
| M-03B | Organization-level tenant isolation for every resource and report, with cross-tenant tests. | No organization or membership model; API queries currently have no tenant scope. | Add centralized authorization and tenant-scoped data access before exposing organization resources. | Two-organization access tests for read, write, scan, and report operations. | BLOCKED | Current scan history is shared and unauthenticated; this is a production blocker. |
| M-03C | Secure registration, login, token/session validation, password hashing, and account lifecycle. | No authentication implementation or auth routes. | Select and implement a secure session strategy, credential lifecycle, and safe secret configuration. | Registration, login, malformed/expired credential and password-storage tests. | BLOCKED | No auth dependencies, routes, secrets configuration, or tests. |
| M-04 | Verify domain ownership with DNS TXT challenges before scans; distinguish ownership from scan authorization. | No domain model, DNS challenge, or authorization record. | Implement random expiring challenge lifecycle, DNS verification, scope authorization, and revocation. | Deterministic DNS fixture tests, expiry/replay tests, and unverified-scan rejection. | BLOCKED | Current `/scan` accepts any publicly resolving target. |
| M-05A | Preserve safe DNS/TLS/HTTP/header/redirect/authorized-port checks with structured results. | Existing modules in `backend/app/scanner/`; nested check payloads are not strict schemas. | Add DNS check, structured validation and affected-asset/scan linkage; retain existing checks. | Per-check deterministic tests and API schema contract checks. | BLOCKED | Existing checks remain wired; DNS check and consistent finding schema are absent. |
| M-05B | Prevent SSRF, DNS rebinding, private IPv4/IPv6 access, unsafe redirects, proxy bypass, and oversized/unbounded HTTP reads. | `backend/app/utils.py`; TLS in `backend/app/scanner/ssl_check.py`; ports in `backend/app/scanner/ports.py`. | Keep pinned transport and extend validation, authorization, resource, and deployment controls. | Mocked DNS and local HTTP fixture tests for direct, redirect, mixed-answer, IPv6, and rebinding cases. | BLOCKED | This increment pins HTTP/TLS/Nmap destinations, rejects non-public DNS answers and unsafe redirects, disables inherited proxies, restricts web ports, and caps HTTP response bodies at 1 MB. Domain authorization, global concurrency, a controlled resolver, and network-level egress restrictions are not implemented. |
| M-06 | Persistent scan lifecycle, partial check outcomes, safe failure handling, deduplication, cancellation and resource limits. | `backend/app/services/scan_service.py` executes synchronously and stores a whole report. | Add persistent lifecycle states, bounded execution and robust transaction handling. | Scan lifecycle, partial failure, duplicate submission, and restart tests. | BLOCKED | No queue or durable status model, concurrency cap, cancellation, or finding lifecycle. |
| M-07 | Authenticated, tenant-scoped and safely rendered PDF reports. | `/scans/{scan_id}/pdf` and `backend/app/services/pdf_service.py`. | Authorize each report operation; escape user-controlled text; enforce output limits and audit downloads. | PDF content/type tests and cross-tenant denial tests. | BLOCKED | PDF generation exists, but downloads are unauthenticated and not tenant-scoped. |
| M-08 | Integrate auth, organization, domains, verification and scan lifecycle into the existing React app. | Existing dashboard in `frontend/src/`; API client in `frontend/src/lib/api.ts`. | Add authenticated UX and keep API types aligned with actual schemas. | Frontend tests for auth, domain state, errors, scan flow and PDF download. | BLOCKED | Existing dashboard remains unchanged; there are no auth/domain screens or frontend tests. |
| M-09 | Windows setup, safe env templates, Git exclusions, migrations and operating instructions. | `README.md`, `backend/README.md`; current setup uses Python 3.13 and SQLite. | Document PostgreSQL, migrations, secrets, backup/restore, install/test/run commands, and templates. | Follow documented setup in a clean local environment. | BLOCKED | Current Windows run instructions exist, but PostgreSQL/migration and backup/restore instructions plus env templates are absent. |
| M-10 | Automated backend/frontend/security tests and verifiable acceptance flows. | `backend/tests/test_cookies.py`; frontend has no test script. | Add isolated integration tests and complete the acceptance flow without public DNS dependencies. | Run backend test suite and production build; record skipped tests. | BLOCKED | Current backend tests pass, but auth, tenant, verification, migrations, reporting isolation and frontend tests do not exist. |
| M-11 | Execute in milestones and do not claim production readiness without evidence. | Current code and this document. | Complete remaining milestones and release gate before deployment. | Traceability review against acceptance evidence. | BLOCKED | Only the SSRF transport increment is implemented; production release is blocked. |

## Addendum requirements

| ID | Requirement | Existing implementation and files | Required change | Verification method | Status | Evidence and remaining limitations |
| --- | --- | --- | --- | --- | --- | --- |
| A-16 | Trace every master/addendum requirement; record APIs, scanner baseline, tests, failures, and regression evidence. | This document; `backend/app/main.py`; `backend/app/services/scan_service.py`; backend/frontend test commands. | Keep each row current as implementation proceeds and add evidence for new work. | Review this matrix and rerun documented commands. | PASS | Existing endpoints/checks and baseline tests are recorded. The matrix explicitly leaves incomplete work blocked. |
| A-17 | PostgreSQL migration safety, transactions, deletion rules, constraints, pool limits, backups and restore, representative schema tests. | `backend/app/database.py`, `backend/app/models.py`. | Add PostgreSQL/Alembic incrementally with migration review and backups. | Fresh and representative database migration plus restore verification. | BLOCKED | SQLite `create_all()` remains; no migration or backup procedure. |
| A-18 | Authentication lifecycle safeguards including normalized email, password policy, rate limits, reset, revocation and token claim validation. | No authentication code. | Implement lifecycle controls and document any unavailable delivery/rate-limit service. | Authentication lifecycle and abuse-rate tests. | BLOCKED | No authentication workflow or service interface exists. |
| A-19 | Explicit verified-host and scan authorization scope, expiry/revocation, challenge lifecycle, safe hostname normalization, and no implicit subdomain scope. | `backend/app/utils.py` has hostname normalization only; no ownership data model. | Add separately authorized scope with explicit host/subdomain policy and lifecycle. | Host-bound scan and challenge/revocation tests. | BLOCKED | URL normalization cannot substitute for ownership or authorization. |
| A-20 | SSRF boundary must bind validation to the contacted IP; cover IPv4/IPv6, mixed DNS, redirects, proxy settings, ports, timeouts, response bounds and internal-service access. | `backend/app/utils.py`; TLS and Nmap modules; `backend/tests/test_network_safety.py`, `backend/tests/test_cookies.py`. | Complete controlled-resolution, authorization, concurrency and network-egress controls; add TLS integration fixtures. | Current tests include a local HTTP fixture, private/mixed/mapped/unique-local addresses, unsafe redirect, DNS change, TLS IP/SNI, Nmap IP, port and response-size checks. Add controlled TLS and deployment-egress tests. | BLOCKED | The validated address is now pinned for HTTP and TLS sockets; HTTP requests do not inherit proxies or follow redirects automatically. The end-to-end HTTPS transport and infrastructure egress policy still need verification. |
| A-21 | Durable scan records, bounded concurrency/duration, retry/recovery/cancellation, duplicate-submission and per-check outcomes. | Synchronous `run_scan()` in `backend/app/services/scan_service.py`. | Build a persisted run lifecycle and execution limits without relying on in-memory tasks. | Restart, concurrency, interruption, cancellation, retry and partial-result tests. | BLOCKED | Scans run synchronously and have no durable lifecycle state or global/per-organization concurrency cap. |
| A-22 | Separate findings from check results; stable finding identity, first/last seen, occurrence, state, evidence, history, and safe resolution. | Findings currently live only inside each scan's JSON report. | Add finding persistence and transactional deduplication/resolution rules. | Repeated scan, changed issue, failed check and concurrent deduplication tests. | BLOCKED | No persistent finding records or resolution model. |
| A-23 | Structured security audit logs, protected audit records, operational health checks and incident/backup/migration documentation. | `/health` in `backend/app/main.py`; no audit service. | Add redacted structured events, separate liveness/readiness, retention/access rules and operations guide. | Health dependency tests, audit access tests and secret-redaction checks. | BLOCKED | Only a basic process health response exists; no readiness, audit trail or operating procedures. |
| A-24 | Practical CI for lint/type/tests/build/migrations/dependency and secret scanning. | No repository workflow or configured lint/type/test scripts identified. | Add CI that uses isolated credentials/databases and approval-gated migrations. | Run workflow on a clean branch and inspect each job. | BLOCKED | No CI workflow or security scanning configuration. |
| A-25 | Strict API contracts, uniform safe errors, input/body limits, CORS/security headers, CSRF where applicable and aligned TS types. | Pydantic request/response schemas in `backend/app/schemas.py`; CORS and errors in `backend/app/main.py`; TS types/API client in `frontend/src/types/scan.ts` and `frontend/src/lib/api.ts`. | Add strict nested schemas, safe error handling, security headers, auth/CSRF protections as appropriate, and contract tests. | API validation/error tests and generated/manual type compatibility checks. | BLOCKED | CORS is configurable and current request fields have limits, but nested scan results are permissive and there is no auth, CSRF or security-header middleware. |
| A-26 | Privacy/data retention/deletion/export/backups and jurisdictional legal review. | No privacy/retention policy or export workflow. | Document data categories, access, retention, deletion and breach handling; seek legal review before compliance claims. | Documentation and operational review. | BLOCKED | No privacy policy or retention implementation. No legal compliance claim is made. |
| A-27 | Deterministic end-to-end acceptance flow through registration, verification, scanning, findings, PDF, tenant isolation, SSRF and restart. | Only unit tests for cookies, TLS pin selection and network-safety primitives. | Implement the flow after auth, domain, tenant and persistence milestones. | Reproducible isolated integration suite. | BLOCKED | Current unit suite does not exercise auth, TXT verification, tenant isolation, persistence lifecycle or authenticated reports. |
| A-28 | Release checklist and production gate with evidence for all critical boundaries. | This document and current source. | Complete all critical controls and record release evidence before production. | Final checklist review and complete acceptance suite. | BLOCKED | Production readiness is explicitly blocked by missing auth, tenant isolation, domain authorization, migrations, scan limits, and report authorization. |

## First security increment

Files changed:

- `backend/app/utils.py`: IDNA/literal normalization, explicit web-port allowlist, global-address checks including IPv4-mapped IPv6, mixed-answer rejection, pinned HTTP/HTTPS connection pools, proxy-environment isolation, manual redirect validation, and a 1 MB response cap.
- `backend/app/scanner/ssl_check.py`: validates and pins the TLS socket destination while preserving the hostname for TLS SNI and certificate validation.
- `backend/app/scanner/ports.py`: resolves and validates once, then passes the vetted numeric address to Nmap instead of allowing Nmap to resolve the hostname independently.
- `backend/app/scanner/redirects.py`: HTTPS targets on port 8443 now check the standard HTTP endpoint rather than attempting disallowed HTTP port 8443.
- `backend/tests/test_network_safety.py`: deterministic DNS, redirect, IPv6, pinning, local HTTP and Nmap target tests.
- `backend/tests/test_cookies.py`: custom-port TLS pin and server-name regression coverage.

The allowed URL ports are HTTP 80/8080 and HTTPS 443/8443. Nmap still performs the existing conservative `-T3 --top-ports 20` check against the pinned public IP. Because the app has no ownership authorization, this scan must remain limited to targets the operator is explicitly authorized to test.

## Verification after this increment

- `cd backend; .\venv313\Scripts\python.exe -m unittest discover -s tests -q` — 14 tests passed.
- `npm run build` passed at baseline. No frontend source or dependency files were changed in this increment.
- The backend emits an existing `RequestsDependencyWarning` because the local environment's `urllib3` version is outside Requests' declared tested range; it did not fail the tests. Dependency reconciliation is tracked under A-24.

## Production blockers and next work

1. Implement PostgreSQL configuration/models and reviewed Alembic migrations without dropping or rewriting the existing SQLite database.
2. Implement authentication, organization membership, tenant-scoped access and cross-tenant denial tests.
3. Implement DNS TXT ownership verification and separate, revocable scan authorization for exact hosts and check types.
4. Add persisted scan runs, findings lifecycle/deduplication, resource/concurrency limits and authenticated PDF access.
5. Add frontend flows, contract/integration tests, CI, backup/restore and privacy/operations documentation.
6. Extend network-boundary verification with end-to-end TLS fixtures and deployment-level outbound restrictions before any public release.

