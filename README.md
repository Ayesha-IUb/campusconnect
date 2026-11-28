# CampusConnect

**University Service Request Management System**  
CSE309 · Autumn 2026 · React + TypeScript · FastAPI · Supabase · Vercel

CampusConnect is a web application for university students to submit campus-service requests, staff to process requests, and administrators to manage users and service activity. It also supports shared groups with member-level permissions.

## Live deployment

| Resource | URL |
|---|---|
| Frontend | https://campusconnect-two-ivory.vercel.app/ |
| API documentation | https://campusconnect-two-ivory.vercel.app/api/docs |
| Health endpoint | https://campusconnect-two-ivory.vercel.app/api/health |
| Repository | https://github.com/Ayesha-IUb/campusconnect |

**Live check (28 November 2026):** the deployed frontend and API documentation loaded successfully. The health endpoint returned \`status: ok\` and \`database_configured: true\`. In this application, \`database_configured\` means the backend created its Supabase client from the configured URL and backend key. It does not, by itself, prove that every database table, migration, demo role, or user permission has been checked.

The production deployment is built from the repository's \`main\` branch. The older note about final features waiting on a separate branch/merge has been removed because it no longer describes the current deployment.

## Features

### Service requests
- Create, list, view, update and delete service requests.
- Students can see their own requests and can edit or delete only their own requests while the status is \`Pending\`.
- Staff can view all requests and update request status, but cannot create or delete requests.
- Administrators can manage requests.
- Request fields and status values are validated by Pydantic schemas; ownership and role rules are enforced by the backend.

### Authentication, profile and sessions
- Email/password signup and login are handled by the FastAPI backend and Supabase Auth.
- Supabase-issued signed access JWTs are verified on protected API requests.
- The backend checks the current profile, role, ban state and active server-side session.
- Refresh tokens are returned through an \`HttpOnly\`, \`SameSite=Lax\` cookie, rotated through the refresh endpoint, and stored in the database only as hashes.
- Logout and session revocation invalidate the server-side session record.
- Users can update their profile name, change their password after current-password verification, list sessions and revoke sessions.
- Failed login attempts are tracked by email/IP. Five failed attempts within 15 minutes trigger a temporary lockout.
- The backend applies a server-side HMAC password pepper before Supabase Auth performs password hashing.

**Token storage detail:** the frontend stores the short-lived access-token session in browser \`localStorage\`; the refresh token is kept in the backend-set HttpOnly cookie. Never copy either token into screenshots, issues, documentation or chat.

### Groups and shared requests
- Users can create groups, invite registered users and view groups they own or belong to.
- Group owners grant the independent \`can_create_requests\`, \`can_edit_requests\` and \`can_assign_requests\` permissions.
- Group membership allows viewing shared requests; create, edit and assign actions are checked separately by the backend.
- A member who assigns a request must also be allowed to create it when creating a new request with an assignee.
- Only the group owner can rename/delete the group, manage members or delete shared requests. Administrators have separate moderation endpoints.

### Administrator tools
- Dashboard overview counts for users, banned users, requests and groups.
- User search, role/banned filters, pagination and user detail (including sessions, groups, requests and recent activity).
- Role changes for eligible non-admin users.
- Ban/unban with a reason; banning revokes active sessions and subsequent protected requests are rejected.
- Request and group moderation, including bulk deletion.
- Activity log and security event views with filters and IP/account summaries.
- CSV exports for users, requests, groups and activity logs. Formula-triggering CSV cells are escaped.
- Activity-log retention cleanup with a bounded retention period.

## Roles and permissions

| Action | Student | Staff | Admin |
|---|---|---|---|
| Create personal request | Yes | No | Yes |
| View personal request list | Own requests | All requests | All requests |
| Edit request details | Own pending requests | No | Any request |
| Change request status | No | Yes | Yes |
| Delete personal request | Own pending requests | No | Any request |
| Access admin endpoints | No | No | Yes |

The backend is authoritative for authorization. Hiding a button in the frontend is not a security control.

## Demo accounts and group configuration

Demo account credentials were supplied privately through the course submission form. Passwords, access tokens and service keys are intentionally not published in this repository. The current role of each demo account should be checked on the live application before the demonstration; do not infer a role from an email address or an old screenshot.

The course submission form specifies this instructor-demo group setup:

| Group setting | Submitted configuration |
|---|---|
| Group name | CampusConnect Instructor Demo Group |
| Owner | cc-student01@example.com |
| Member | cc-student02@example.com: create and edit shared requests; view through group membership |
| Member | cc-student03@example.com: assign shared requests; view through group membership |

**Live configuration status:** the submitted configuration details are documented here, but the current production role assignments, group membership and permission flags still need to be checked in the deployed application. Verify each allowed and denied action before describing the group as live-tested.

## Architecture

### Frontend

    frontend/src/
    ├── components/       Reusable interface components and workspace sections
    ├── services/
    │   └── api.ts        API calls, refresh retry, logout and CSV download
    ├── types/            Shared TypeScript types
    ├── App.tsx            Application state and page coordination
    └── index.css          Application styles

The React application coordinates the main session and page state. Components render the interface, while \`services/api.ts\` handles API requests and refresh retry behavior.

### Backend

    backend/
    ├── routers/           HTTP endpoints: auth, users, requests, groups, admin
    ├── services/          Authentication, request, group and admin workflows
    ├── repositories/      Supabase persistence for request and group resources
    ├── migrations/        Ordered SQL schema changes
    ├── tests/             Authentication and RBAC tests
    ├── database.py        Supabase client and query helper
    ├── dependencies.py    JWT, profile, ban and active-session checks
    ├── rbac.py            Reusable request-role policies
    ├── models.py          Typed domain records
    ├── schemas.py         Pydantic input validation
    └── main.py            FastAPI app, middleware and router registration

Main request data flow: **HTTP request → Router → Service → Repository → Supabase PostgreSQL**. Authentication and admin workflows use service modules with the shared database helper because they coordinate multiple database tables and Supabase Auth.

## Technology

| Area | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | Python 3.11+, FastAPI |
| Authentication | Supabase Auth, signed JWT access token |
| Database | Supabase PostgreSQL |
| Validation | Pydantic |
| API documentation | FastAPI OpenAPI/Swagger |
| Tests and CI | pytest, GitHub Actions |
| Hosting | Vercel |

## Local setup

### 1. Database

1. Open the Supabase project SQL Editor.
2. Apply \`backend/migrations/001_auth_rbac.sql\` if it has not already been applied.
3. Apply \`backend/migrations/002_final_features.sql\` once, after migration 001.

Do not repeatedly reapply migrations without checking their current state.

### 2. Environment variables

Create \`backend/.env\` using \`backend/.env.example\`. The backend requires:

- \`SUPABASE_URL\`
- \`SUPABASE_SECRET_KEY\` (backend only)
- \`SUPABASE_ANON_KEY\` (or the documented \`VITE_SUPABASE_ANON_KEY\` fallback)
- \`PASSWORD_PEPPER\` (recommended; keep stable)
- \`FRONTEND_ORIGINS\`
- \`REFRESH_TOKEN_DAYS\` (optional; defaults to 7)

Create \`frontend/.env.local\` using \`frontend/.env.example\`. It should contain only:

- \`VITE_SUPABASE_URL\`
- \`VITE_SUPABASE_ANON_KEY\`

Never put a Supabase secret/service-role key or password pepper in a \`VITE_\` variable or commit real \`.env\` files.

Keep \`PASSWORD_PEPPER\` stable after accounts are created. Changing it can prevent existing users from signing in.

### 3. Backend (Windows PowerShell)

    cd backend
    python -m venv venv
    .\venv\Scripts\python.exe -m pip install -r requirements.txt
    .\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000

The local API documentation is http://127.0.0.1:8000/api/docs.

### 4. Frontend (a second terminal)

    cd frontend
    npm install
    npm.cmd run dev

Open http://localhost:5173. In PowerShell, \`npm.cmd\` avoids the common script-execution-policy issue with \`npm.ps1\`.

### 5. Automated checks

From the repository root, run:

    cd backend
    ..\backend\venv\Scripts\python.exe -m compileall -q .
    ..\backend\venv\Scripts\python.exe -m pytest tests -q
    cd ..\frontend
    npm.cmd run build

The GitHub Actions workflow at \`.github/workflows/ci.yml\` also runs the frontend production build, backend compile check, pytest suite and a FastAPI route-registration check on pushes and pull requests.

## Deployment and configuration checks

Vercel routes \`/api/*\` to the FastAPI backend and other paths to the Vite frontend through \`vercel.json\`.

The expected Vercel environment-variable names are:

| Scope | Variable names |
|---|---|
| Backend | \`SUPABASE_URL\`, \`SUPABASE_SECRET_KEY\`, \`SUPABASE_ANON_KEY\`, \`PASSWORD_PEPPER\`, \`FRONTEND_ORIGINS\`, optional \`REFRESH_TOKEN_DAYS\` |
| Frontend | \`VITE_SUPABASE_URL\`, \`VITE_SUPABASE_ANON_KEY\` |

The production health endpoint reported that the backend Supabase client is configured during the 28 November 2026 live check. **The Vercel environment-variable settings and values, Supabase migration state, and Supabase Auth JWT lifetime have not been independently verified for this README.** Check the variable names and deployment scopes in the Vercel project settings, keep values hidden in screenshots, confirm both migrations in Supabase, and configure the Supabase access-token/JWT lifetime to 900 seconds or less if required by the course rubric.

After changing Vercel environment variables, redeploy the project. Do not paste secret values into GitHub, screenshots or the course report.

## Documentation

- Product Requirements Document: [docs/PRD.md](docs/PRD.md)
- Software Requirements Specification: [docs/SRS.md](docs/SRS.md)
- Technical Design Document: [docs/TDD.md](docs/TDD.md)
- Final project report: [docs/FINAL_REPORT.md](docs/FINAL_REPORT.md)
- Supabase Auth, migration and deployment setup: [docs/AUTH_SETUP.md](docs/AUTH_SETUP.md)

## Course submission notes

- Live frontend and API health/docs check: completed on 28 November 2026 (see live-check details above).
- Code defence viva: completed on 26 November 2026.
- Live demo-account access, role assignments, group permissions and Vercel/Supabase configuration: verify against the deployed environment before final sign-off.
- Final report PDF, required screenshots and demo-video submission should be maintained as separate course deliverables; do not treat this README as evidence that those uploads are complete.

