# SecureScan Dashboard

SecureScan Dashboard is a portfolio-grade defensive cybersecurity web dashboard. It scans a website for basic security posture signals such as security headers, SSL/TLS certificate status, HTTP-to-HTTPS redirects, exposed technology headers, open ports using safe Nmap settings, and basic frontend library hints.

## Important safety rule

Only scan websites you own or have permission to test. This project is intentionally defensive and lightweight. It does not include exploitation, brute forcing, password attacks, payload injection, SQL injection exploitation, directory brute forcing, aggressive fuzzing, vulnerability scripts, or offensive automation.

## Features

- Security headers checker
- SSL/TLS certificate checker
- HTTP-to-HTTPS redirect checker
- Server information leakage checker
- Safe Nmap open ports checker
- Basic outdated frontend library hints
- Cookie security inspection with Secure, HttpOnly, and SameSite checks
- PDF report export for completed scans
- Risk scoring from 0 to 100 with grades A to F
- Severity-based findings table
- SQLite scan history
- React dashboard UI with dark cybersecurity styling
- Responsive layout

## Tech stack

### Backend

- Python
- FastAPI
- Pydantic
- Requests
- SSL/socket libraries
- SQLite
- SQLAlchemy
- Safe subprocess execution for Nmap

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- React Router
- Lucide icons

## Project structure

```text
securescan-dashboard/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── utils.py
│   │   ├── scanner/
│   │   │   ├── __init__.py
│   │   │   ├── headers.py
│   │   │   ├── ssl_check.py
│   │   │   ├── redirects.py
│   │   │   ├── ports.py
│   │   │   ├── libraries.py
│   │   │   ├── scoring.py
│   │   │   └── recommendations.py
│   │   └── services/
│   │       ├── __init__.py
│   │       └── scan_service.py
│   ├── requirements.txt
│   └── README.md
└── frontend/
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx
    │   ├── lib/api.ts
    │   ├── pages/
    │   ├── components/
    │   └── types/scan.ts
    └── package.json
```

## Backend setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

macOS/Linux activation:

```bash
source venv/bin/activate
```

Backend URL:

```text
http://127.0.0.1:8000
```

API docs:

```text
http://127.0.0.1:8000/docs
```

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Frontend URL:

```text
http://localhost:5173
```

## API endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/health` | Backend health check |
| POST | `/scan` | Run a new defensive scan |
| GET | `/scans` | List scan history |
| GET | `/scans/{scan_id}` | Get full report by ID |
| GET | `/scans/{scan_id}/pdf` | Download the full report as a PDF |
| DELETE | `/scans/{scan_id}` | Delete scan history item |

## Screenshots

Add screenshots after running the project:

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
