# SecureScan Dashboard Backend

SecureScan Dashboard is a defensive cybersecurity API that performs lightweight website security checks for sites you own or have permission to test.

## Safety disclaimer

This project is for defensive security learning, auditing, and portfolio use only. Only scan websites you own or are authorized to test. The scanner intentionally avoids exploitation, brute forcing, payload injection, SQL injection exploitation, directory brute forcing, aggressive fuzzing, vulnerability scripts, and other offensive techniques.

## Network safety and production status

HTTP targets are limited to ports 80 and 8080; HTTPS targets are limited to 443 and 8443. The scanner rejects non-public IP addresses and DNS responses containing any non-public address. HTTP redirects are followed manually and revalidated, HTTP requests do not inherit system proxy settings, and validated IP addresses are pinned for HTTP, TLS, and Nmap connections. HTTP response bodies are capped at 1 MB.

The current API does not authenticate users, verify domain ownership, or enforce organization-level authorization. Therefore, these transport protections do not authorize scans: use the scanner only for targets you are explicitly permitted to assess, and do not expose this API publicly. Production use is blocked until authentication, tenant isolation, ownership and scan authorization, durable migrations, execution limits, and tenant-scoped reporting are implemented and tested. See [`docs/requirements-traceability.md`](../docs/requirements-traceability.md) for evidence and outstanding requirements.

## Features

- Security headers checker
- SSL/TLS certificate checker
- HTTP-to-HTTPS redirect checker
- Server information leakage checker
- Safe Nmap top-ports checker
- Basic frontend library hints
- Risk score and grade engine
- SQLite scan history
- Clean FastAPI endpoints
- SSRF protection against private/local/internal targets

## Tech stack

- Python
- FastAPI
- Pydantic
- Requests
- SSL/socket libraries
- SQLite
- SQLAlchemy
- Nmap through safe subprocess execution

## Setup

Use Python 3.13 for the backend dependencies. The pinned Pydantic version does not build with Python 3.14.

Windows PowerShell (install Python 3.13 first):

```powershell
py -3.13 --version
py -3.13 -m venv venv313
.\venv313\Scripts\python.exe -m pip install -r requirements.txt
.\venv313\Scripts\python.exe -m uvicorn app.main:app --reload
```

macOS/Linux:

```bash
python3.13 -m venv venv313
source venv313/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

The API will run at:

```text
http://127.0.0.1:8000
```

Interactive API docs:

```text
http://127.0.0.1:8000/docs
```

## Optional environment variables

Copy `.env.example` to `.env` and edit values if needed.

```bash
SECURESCAN_DB_URL=sqlite:///./securescan.db
SECURESCAN_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
SECURESCAN_REQUEST_TIMEOUT=8
SECURESCAN_NMAP_TIMEOUT=60
```

## API endpoints

### GET `/health`

Returns backend status.

### POST `/scan`

Runs a full defensive scan.

Request:

```json
{
  "target_url": "https://example.com"
}
```

### GET `/scans`

Returns scan history.

### GET `/scans/{scan_id}`

Returns a full scan report by ID.

### DELETE `/scans/{scan_id}`

Deletes a scan from history.

## Nmap note

The project only uses this safe lightweight command:

```bash
nmap -T3 --top-ports 20 <hostname>
```

If Nmap is not installed, the API still works and returns a clear Nmap error inside the ports check.

## Screenshots

Add screenshots here after running the React dashboard:

- Dashboard page
- New scan page
- Report page
- Scan history page

## Future improvements

- Authentication
- Supabase/PostgreSQL support
- PDF report export
- Scheduled scans
- Email alerts
- Domain ownership verification
- More advanced dependency detection
- Organization/team accounts
