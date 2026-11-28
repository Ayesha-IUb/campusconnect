# CampusConnect

**University Service Request Management System**  
CSE309 · Autumn 2026 · React + TypeScript · FastAPI · Supabase · Vercel

CampusConnect helps university students submit service requests, lets staff process them, and gives administrators tools to manage accounts and campus-service content. The application includes session controls, shared groups, fine-grained group permissions, administration, audit records and security monitoring.

> **Deployment status (28 Nov 2026):** Final authentication, groups and admin features were merged to \`main\` in PR #12. The current production deployment is READY and was built from main commit \`92701f5690e73b20b4743a5ef1c5d84bf4a0de57\`. PR #13 is still an open draft for a further frontend page-structure refactor and signup payload correction; it is not part of production.

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
- Server-managed \`HttpOnly\` refresh cookie with refresh-token rotation and logout revocation.
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
    ├── App.tsx           Main application state and navigation
    └── index.css         Application styles

The page/application coordinates state, components render interface pieces, and \`services/api.ts\` owns network calls.

### Backend
    backend/
    ├── app/
    │   ├── activity/     Activity repository and service
    │   ├── admin/        Admin router, schemas, service and repository
    │   ├── auth/         Auth router, schemas, service and repository
    │   ├── core/         Database, dependencies, models and shared types
    │   ├── groups/       Group router, schemas, service and repository
    │   ├── rbac/         Reusable role and permission policies
    │   ├── requests/     Request router, schemas, service and repository
    │   └── users/        User/profile router, schemas, service and repository
    ├── migrations/       SQL schema changes
    ├── tests/            Automated authentication and RBAC tests
    └── main.py           FastAPI app and feature-router registration

Main data flow: **HTTP request → Feature Router → Feature Service → Feature Repository/Core Database → Supabase PostgreSQL**.

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
2. Run \`backend/migrations/001_auth_rbac.sql\` if it has not already been applied.
3. Run \`backend/migrations/002_final_features.sql\` once, after migration 001.

### 2. Environment variables

Create \`backend/.env\` using \`backend/.env.example\`. Keep the backend secret and password pepper server-side only.

Create \`frontend/.env.local\` using \`frontend/.env.example\`. Only the public Supabase URL/key belong in frontend variables.

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

- Production frontend: https://campusconnect-two-ivory.vercel.app/
- Production API docs: https://campusconnect-two-ivory.vercel.app/api/docs
- Production health: https://campusconnect-two-ivory.vercel.app/api/health
- Current preview frontend: https://campusconnect-elaj4c1k7-sdceg.vercel.app/

The production health endpoint currently returns \`{"status":"ok","database_configured":true}\`. This verifies backend reachability and database configuration, not every authenticated workflow.

Vercel backend variables: \`SUPABASE_URL\`, \`SUPABASE_SECRET_KEY\`, \`SUPABASE_ANON_KEY\` (or \`VITE_SUPABASE_ANON_KEY\` fallback), and a stable \`PASSWORD_PEPPER\`. Configure \`FRONTEND_ORIGINS\` to the deployed frontend origin. Frontend variables are \`VITE_SUPABASE_URL\` and \`VITE_SUPABASE_ANON_KEY\`. Never put a service-role/secret key in a \`VITE_\` variable.

In Supabase Auth settings, configure the access-token/JWT lifetime to 900 seconds or less for the course requirement. Keep the password pepper stable after accounts have been created; changing it prevents existing peppered passwords from verifying.

## Demo accounts and shared-group evidence

The hosted database contains two Admin demo profiles and three Student demo profiles. Their UUIDs and roles are recorded in the final report appendix. Passwords are not stored in this public repository; provide them only through the instructor's private submission channel.

Configured group: **CampusConnect Instructor Demo Group**
- Owner: Demo Student 1.
- Demo Student 2: Create + Edit permissions.
- Demo Student 3: Assign permission.

The project owner's normal Student account is not a member of this demo group, so the group list is empty in that account's dashboard.

## Documentation

- PRD: docs/PRD.md
- SRS: docs/SRS.md
- TDD: docs/TDD.md
- Final project report: docs/FINAL_REPORT.md
- Supabase Auth, migration and deployment setup: docs/AUTH_SETUP.md

## Evidence checklist before final submission

- [x] Final auth/groups/admin implementation merged to main.
- [x] Production deployment READY; health endpoint confirms database configured.
- [x] Five demo accounts (2 Admin + 3 Student) and a mixed-permission group exist in Supabase.
- [x] Frontend build, backend compile/import and 13 RBAC unit tests passed.
- [ ] Verify login, refresh, logout, profile update and session revoke on production.
- [ ] Verify student/staff/admin restrictions and mixed group permissions live.
- [ ] Verify admin overview, user management, ban/unban, activity/security logs and CSV export live.
- [ ] Add genuine, unedited screenshots S1–S21 to the report PDF.
- [ ] Record the 5–8 minute demo video on the deployed URL.
- [ ] Submit the GitHub, Vercel, report PDF and video links through the course form.

Passwords and secrets must never be committed to GitHub.
