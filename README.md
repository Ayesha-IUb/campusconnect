# CampusConnect

**University Service Request Management System**  
CSE309 · Autumn 2026 · React + TypeScript · FastAPI · Supabase · Vercel

CampusConnect helps university students submit service requests, lets staff process them, and gives administrators tools to manage accounts and campus-service content. The final development branch adds session controls, shared groups, fine-grained group permissions, administration, audit records and security monitoring.

> **Deployment note:** Final features are developed on `final-viva-2026`. Before merging/deploying this branch, apply `backend/migrations/002_final_features.sql` in the Supabase SQL Editor and configure the environment variables below. Production continues to run the currently deployed `main` branch until the final PR is merged and redeployed.

## Features

### Service requests
- Create, list, view, update and delete service requests.
- Students see and manage their own pending requests.
- Staff can view requests and update status only.
- Administrators can manage requests.
- Backend validation and role checks protect the REST API.

### Authentication and profile
- Email/password signup and login through FastAPI and Supabase Auth.
- Supabase-issued signed access JWTs, verified on protected requests.
- Server-managed `HttpOnly` refresh cookie with refresh-token rotation and logout revocation.
- Per-device session listing and revocation.
- Profile name update and current-password-verified password change.
- Five failed login attempts per email/IP within 15 minutes trigger a temporary lockout.
- Server-side password pepper before Supabase Auth applies its salted password hashing.

### Groups and shared requests
- Create groups and invite registered users by email.
- Group owners control member permissions: create, edit and assign requests.
- Members see shared group requests; permitted members can create/edit/assign.
- Only the owner can rename/delete the group, manage members and delete shared requests.

### Administrator tools
- Overview statistics for users, banned users, requests, groups and recent activity.
- Search/filter/paginate users and view user profile, requests, groups, sessions and recent activity.
- Change student/staff roles; ban/unban accounts with a reason.
- Ban/unban selected users in bulk; banning revokes active refresh sessions and protected requests are rejected.
- Search and moderate service requests and groups, including bulk deletion APIs.
- Review activity logs and security events, including IP/account summaries.
- Export users, requests, groups and activity as CSV; formula-like cells are escaped.
- Purge older activity records using a bounded retention period.

## Architecture

### Frontend
    frontend/src/
    ├── components/       Reusable UI: AuthForm, RequestForm, RequestList, Sidebar, ...
    ├── services/api.ts   HTTP calls, token refresh retry and CSV download
    ├── types/            Shared TypeScript types
    ├── App.tsx            Main application state and navigation
    └── index.css          Application styles

The page/application coordinates state, components render interface pieces, and services/api.ts owns network calls.

### Backend
    backend/
    ├── routers/          HTTP endpoints (auth, users, requests, groups, admin)
    ├── services/         Application rules, authorization and workflows
    ├── repositories/     Supabase persistence for requests and groups
    ├── migrations/       SQL schema changes
    ├── tests/            Automated RBAC policy tests
    ├── database.py       Supabase client and safe query helper
    ├── dependencies.py   JWT, active-session and ban verification
    ├── rbac.py           Reusable role/permission policy
    ├── models.py         Typed domain records
    ├── schemas.py        Pydantic request-validation schemas
    └── main.py           FastAPI app, CORS, security headers and router registration

Main data flow: **HTTP request → Router → Service → Repository → Supabase PostgreSQL**. Authentication and administration services also use the shared database helper for their specialized workflows.

## Technology

| Area | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | Python 3.11+, FastAPI |
| Authentication | Supabase Auth, signed JWT |
| Database | Supabase PostgreSQL |
| API | REST, JSON, OpenAPI/Swagger |
| Hosting | Vercel |
| Tests | pytest, GitHub Actions |

## Local setup

### 1. Database
1. Open the Supabase project SQL Editor.
2. Run backend/migrations/001_auth_rbac.sql if it has not already been applied.
3. Run backend/migrations/002_final_features.sql once, after migration 001.

### 2. Environment variables

Create backend/.env using backend/.env.example. Keep the backend secret and password pepper server-side only.

Create frontend/.env.local using frontend/.env.example. Only the public Supabase URL/key belong in frontend variables.

### 3. Backend (PowerShell terminal 1)
    cd backend
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    fastapi dev main.py

If PowerShell blocks activation, use Command Prompt:
    cd backend
    venv\Scripts\activate.bat
    pip install -r requirements.txt
    fastapi dev main.py

### 4. Frontend (PowerShell terminal 2)
    cd frontend
    npm install
    npm.cmd run dev

Open http://localhost:5173. Local API docs: http://127.0.0.1:8000/api/docs.

### 5. Automated checks

From the repository root:
    cd frontend
    npm.cmd run build
    cd ..
    .\backend\venv\Scripts\python.exe -m compileall -q backend
    .\backend\venv\Scripts\python.exe -m pytest backend\tests -q

## Deployment

- Frontend: https://campusconnect-two-ivory.vercel.app/
- API docs: https://campusconnect-two-ivory.vercel.app/api/docs
- Health: https://campusconnect-two-ivory.vercel.app/api/health

Vercel must have backend variables SUPABASE_URL, SUPABASE_SECRET_KEY, SUPABASE_ANON_KEY (or VITE_SUPABASE_ANON_KEY fallback), and a stable PASSWORD_PEPPER (the current code has a server-secret fallback). Configure FRONTEND_ORIGINS to the deployed frontend origin. Frontend variables are VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY. Never put a service-role/secret key in a VITE_ variable.

In Supabase Auth settings, configure the access-token/JWT lifetime to 900 seconds or less for the course requirement. Keep the password pepper stable after accounts have been created; changing it prevents existing peppered passwords from verifying.

## Demo accounts and shared-group evidence

Create demo accounts in Supabase Auth and promote trusted accounts using the Supabase SQL Editor. Record actual user IDs and roles here after creation. Do not put passwords in this public README; provide demo passwords only in the private submission form/report as the instructor directs.

| Demo account | User ID | Role |
|---|---|---|
| Demo admin 1 | Fill with real UUID | admin |
| Demo admin 2 | Fill with real UUID | admin |
| Demo user 1 | Fill with real UUID | student |
| Demo user 2 | Fill with real UUID | student |
| Demo user 3 | Fill with real UUID | student |

Shared group evidence to complete after live setup:
- Group name: fill with actual group name.
- Owner: fill with actual owner UUID.
- Member A: create requests only.
- Member B: edit requests only.
- Member C: assign requests only.

## Documentation

- PRD: docs/PRD.md
- SRS: docs/SRS.md
- TDD: docs/TDD.md
- Final project report: docs/FINAL_REPORT.md
- Supabase Auth, migration and deployment setup: docs/AUTH_SETUP.md

## Evidence checklist before final submission

- [ ] Apply migration 002 in the hosted Supabase database.
- [ ] Deploy the final branch only after migration and environment variables are ready.
- [ ] Verify user login, refresh, logout, profile update and session revoke on the deployed URL.
- [ ] Verify student/staff/admin restrictions and a group with mixed permissions.
- [ ] Verify admin overview, user management, ban/unban, activity/security logs and CSV export.
- [ ] Add actual, unedited screenshots of the running app to the report PDF.
- [ ] Record the 5–8 minute demo video yourself on the deployed URL.
- [ ] Fill in real demo account UUIDs, roles and shared-group details.
- [ ] Submit the GitHub, Vercel, report PDF and video links through the course form.

Passwords and secrets must never be committed to GitHub.
