# Technical Design Document (TDD)
## CampusConnect: University Service Request Management System

**Version:** 2.0 · **Status:** Final technical design

## 1. Architecture
CampusConnect uses a React/TypeScript frontend, FastAPI REST backend and Supabase Auth/PostgreSQL database. The frontend sends same-origin /api requests to Vercel's FastAPI service. The backend separates HTTP routing, application rules and persistence for service-request and group resources.

## 2. Technology stack
| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | Python 3.11+, FastAPI |
| Authentication | Supabase Auth, signed JWT access token, refresh-token cookie |
| Database | Supabase PostgreSQL |
| Persistence | Supabase Python client |
| Validation | Pydantic |
| API documentation | FastAPI OpenAPI/Swagger |
| Tests | pytest and GitHub Actions |
| Hosting | Vercel |

## 3. Project layout
    campusconnect/
    ├── backend/
    │   ├── routers/          # HTTP endpoints
    │   ├── services/         # use cases and business rules
    │   ├── repositories/     # persistence for request/group resources
    │   ├── migrations/       # Supabase SQL schema changes
    │   ├── tests/            # RBAC unit tests
    │   ├── database.py
    │   ├── dependencies.py
    │   ├── rbac.py
    │   ├── models.py
    │   ├── schemas.py
    │   └── main.py
    ├── frontend/
    │   └── src/
    │       ├── components/
    │       ├── services/
    │       ├── types/
    │       ├── App.tsx
    │       └── index.css
    ├── docs/
    ├── .github/workflows/ci.yml
    └── vercel.json

## 4. Layer responsibilities
- Router: receives HTTP input, injects the authenticated user and converts service results to HTTP responses.
- Service: enforces business rules, ownership and group/admin permissions.
- Repository: performs Supabase reads/writes for request and group resources.
- Database: constructs the Supabase client from backend-only environment variables and wraps database execution.
- Dependencies: verifies JWT claims, profile role/ban state and active session hash.
- Frontend service: owns fetch calls, refresh retry, logout and CSV download.

Authentication and administrative workflows use dedicated service modules and the shared database helper because they coordinate multiple Supabase tables and Auth REST operations.

## 5. Authentication sequence
1. Frontend sends email/password to /api/auth/login.
2. Backend applies the server-side pepper pre-hash and calls Supabase Auth.
3. Supabase returns an access JWT and refresh token.
4. Backend stores hashes of both tokens in app_sessions and sets the refresh token in an HttpOnly cookie.
5. Frontend stores the short-lived access token and sends it as a Bearer token.
6. Backend verifies signature/claims, loads current profile and checks ban status and active access-token hash.
7. If an API request returns 401, frontend calls /api/auth/refresh; backend validates stored refresh hash, asks Supabase to rotate the pair, and updates stored hashes.
8. Logout revokes the session and clears the cookie.

## 6. Authorization
- rbac.py centralizes role and request-level policies.
- dependencies.py supplies the authenticated CurrentUser only after JWT, profile, ban and active-session checks.
- group_service.py checks membership permission flags stored in PostgreSQL for every shared operation.
- Admin endpoints use the require_admin dependency; admin service blocks self-role changes, self-ban and moderation of another admin.

## 7. Data model and migrations
001_auth_rbac.sql creates profiles and links service requests to their owner. 002_final_features.sql creates groups, group_members, app_sessions, activity_logs, security_events and login_attempts; it adds ban metadata and group/assignee fields to service_requests. Apply migrations in order using the Supabase SQL Editor.

## 8. API organization
- routers/auth.py: signup/login/refresh/logout.
- routers/users.py: profile and session operations.
- routers/requests.py: personal request CRUD.
- routers/groups.py: groups, membership and shared requests.
- routers/admin.py: overview, users, moderation, activity, security and exports.

## 9. Security considerations
- Privileged Supabase credentials and password pepper remain backend environment variables.
- Supabase Auth performs password hashing; CampusConnect applies a keyed HMAC pre-hash before Auth receives the password.
- Only refresh-token hashes and access-token hashes are stored in app_sessions.
- Cookies are HttpOnly, SameSite=Lax and Secure over HTTPS.
- Active session hashes allow immediate revocation at the application API layer.
- CORS is allow-listed and the backend applies common browser security headers.
- Login lockout and security event records help detect repeated failures and rejected sessions.
- CSV exports escape cells beginning with formula-triggering characters.

## 10. Configuration and deployment
Backend environment: SUPABASE_URL, SUPABASE_SECRET_KEY, SUPABASE_ANON_KEY (or the existing VITE_SUPABASE_ANON_KEY fallback), PASSWORD_PEPPER (stable; server-only), FRONTEND_ORIGINS and REFRESH_TOKEN_DAYS.

Frontend environment: VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.

Vercel routes /api/* to FastAPI and other paths to Vite. Use Supabase PostgreSQL for persistent production data. Set the Supabase JWT lifetime to 900 seconds or less and apply database migrations before deploying code that requires the new tables.

## 11. Testing strategy
- pytest tests cover Student/Staff/Admin request authorization and ownership rules.
- CI compiles backend modules, imports FastAPI and verifies expected routes.
- CI installs frontend dependencies and runs TypeScript/Vite production build.
- Live acceptance tests must verify refresh/revoke, roles, group permissions, user moderation, activity/security and exports on the deployed Vercel URL.
