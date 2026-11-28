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
    │   ├── app/
    │   │   ├── activity/     # activity repository and service
    │   │   ├── admin/        # admin router, schemas, service, repository
    │   │   ├── auth/         # auth router, schemas, service, repository
    │   │   ├── core/         # database, dependencies, models, shared types
    │   │   ├── groups/       # group router, schemas, service, repository
    │   │   ├── rbac/         # reusable role/permission policies
    │   │   ├── requests/     # request router, schemas, service, repository
    │   │   └── users/        # profile and session router/service/repository
    │   ├── migrations/       # Supabase SQL schema changes
    │   ├── tests/            # authentication and RBAC tests
    │   └── main.py           # FastAPI app and feature-router registration
    ├── frontend/
    │   └── src/
    │       ├── components/   # reusable interface components
    │       ├── pages/        # page-level screens
    │       ├── services/     # API client
    │       ├── types/        # shared TypeScript types
    │       └── App.tsx       # app entry and routing/state coordination
    ├── docs/
    ├── .github/workflows/
    └── vercel.json

## 4. Layer responsibilities
- Feature router: receives HTTP input, injects the authenticated user and maps service results to HTTP responses.
- Feature service: enforces business rules, ownership and group/admin permissions.
- Feature repository: performs Supabase reads/writes for its feature where repository separation is implemented.
- Core: provides shared database access, dependencies, typed models and shared types.
- RBAC: centralizes reusable role and permission policies.
- Frontend API service: owns fetch calls, refresh retry, logout and CSV download.

The backend is organized by feature under `backend/app/` rather than by one global routers/services/repositories directory. Authentication and administrative workflows coordinate multiple Supabase tables and Auth REST operations through dedicated feature services and the shared core database helper.

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
- `app/auth/router.py`: signup, login, refresh and logout.
- `app/users/router.py`: profile and session operations.
- `app/requests/router.py`: personal request CRUD.
- `app/groups/router.py`: groups, membership and shared requests.
- `app/admin/router.py`: overview, users, moderation, activity, security and exports.
- `app/activity/`: activity persistence and service logic.
- `app/core/`: database client, authentication dependencies, domain models and shared types.
- `app/rbac/permissions.py`: reusable role/permission rules.
- `main.py`: registers feature routers with the FastAPI application.

Legacy compatibility modules may remain at the backend root for older imports; the active application router registration uses the feature modules under `app/`.

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
