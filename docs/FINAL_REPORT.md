# CampusConnect Final Project Report

**Course:** CSE309 · Autumn 2026  
**Project:** CampusConnect — University Service Request Management System  
**Stack:** React + TypeScript, FastAPI, Supabase PostgreSQL/Auth, Vercel

> **Evidence status:** The final branch contains the features and test code described here. Hosted database migration, final deployment and live verification must be completed before claiming every feature is verified in production. Replace the evidence placeholders with genuine screenshots/video from the deployed application.

## 1. Product overview

CampusConnect provides one place for students to report campus service problems such as Wi-Fi, classroom equipment, library and facility issues. Students can track their own requests. Staff can review requests and update status. Administrators can manage accounts and campus-service content. Shared groups support collaboration for team-level service work.

## 2. Problem statement and objectives

University service issues can be reported through scattered messages, calls or paper forms. This makes ownership and progress hard to track. CampusConnect organizes requests, ownership, status changes and group collaboration in one web application.

Objectives:
- Provide a validated REST API and responsive React interface.
- Authenticate users and verify signed access tokens on protected routes.
- Enforce Student, Staff and Admin permissions on the backend.
- Support groups with fine-grained create/edit/assign permissions.
- Provide administrator tools, audit history, security monitoring and CSV exports.
- Deploy the frontend and backend together through Vercel with Supabase as persistent storage.

## 3. Implemented functionality

### 3.1 Service request workflow
- Create, list, retrieve, update and delete requests.
- Students see their own requests and may edit/delete their own Pending requests.
- Staff can view all requests and change status only.
- Admins may manage all service requests.
- Pydantic validates request fields and category/status values.

### 3.2 Authentication and sessions
- Signup and password login are proxied through the FastAPI backend to Supabase Auth.
- Supabase issues a signed access JWT; the backend verifies the token claims for protected operations.
- The frontend keeps the short-lived access token in local storage. The refresh token is stored server-side in an HttpOnly cookie.
- Refresh calls rotate the token pair; only token hashes are stored in app_sessions.
- Logout and session revocation mark server-side sessions revoked.
- Profile name update and password change are provided. Password change requires the current password.
- Five failed attempts for an email/IP pair within 15 minutes trigger a login lockout.
- A server-side HMAC pepper pre-hash is applied before Supabase Auth's salted password hash. Keep the pepper secret and stable.

### 3.3 Authorization
The backend verifies identity, current database role, ban status and the active access-token session hash. Role checks are centralized in backend/rbac.py and group-specific checks are in group_service.py.

| Action | Student | Staff | Admin |
|---|---|---|---|
| Create personal request | Yes | No | Yes |
| View requests | Own | All | All |
| Edit request details | Own Pending | No | All |
| Change request status | No | Yes | Yes |
| Delete personal request | Own Pending | No | All |
| Admin dashboard | No | No | Yes |

### 3.4 Groups
- Users can create groups and list groups they own or belong to.
- Owners can add registered users and choose create, edit and assign permissions.
- Members see shared requests and can perform actions allowed by their permissions.
- Only owners may rename/delete their group or manage members.
- Shared request deletion is restricted to the group owner; admin moderation is separate.

### 3.5 Administration and monitoring
- Dashboard overview: users, banned users, requests, groups and recent activity counts.
- User listing with search, role/status filters and pagination; user detail includes related requests, groups, sessions and recent activity.
- Role changes, ban/unban with a reason, bulk ban/unban and session revocation.
- Request/group content moderation and bulk-delete endpoints.
- Activity and security-event lists with filters, IP/account summaries and CSV exports.
- CSV formula-like cell values are escaped and exports are capped at 10,000 rows.
- Activity retention purge is available with a minimum and maximum retention window.

## 4. System architecture

### Frontend

    React UI
      ├── components/      reusable form, list, details, sidebar and workspace UI
      ├── services/api.ts  HTTP, auth proxy calls, refresh retry and CSV downloads
      ├── types/           TypeScript domain types
      └── App.tsx          application state and navigation

### Backend

    HTTP request
      → routers/         request parsing, dependencies and HTTP responses
      → services/        application rules, business logic and authorization
      → repositories/    Supabase persistence for request and group resources
      → database.py     configured Supabase client
      → Supabase PostgreSQL

Authentication dependencies verify each signed JWT and then verify that its access-token hash is associated with a non-revoked session. The current role and ban status are read from the profiles table rather than trusted from frontend state.

## 5. Database design

| Table | Purpose |
|---|---|
| profiles | Supabase user profile, role and ban state |
| service_requests | Personal and group requests, ownership, status, assignee |
| groups | Group name, description and owner |
| group_members | Per-user create/edit/assign permission flags |
| app_sessions | Hashed access/refresh tokens, device metadata, expiry and revocation |
| activity_logs | User and admin audit activity |
| security_events | Rejected tokens, failed login and security events |
| login_attempts | Failed/successful login attempt records used by lockout |

Schema changes are managed by SQL migrations in backend/migrations. Apply migration 001 first and migration 002 second.

## 6. Main API surface

| Method | Endpoint | Purpose |
|---|---|---|
| POST | /api/auth/signup | Create account |
| POST | /api/auth/login | Authenticate and set refresh cookie |
| POST | /api/auth/refresh | Rotate refresh token and issue access token |
| POST | /api/auth/logout | Revoke refresh session |
| GET/PATCH | /api/me | Read/update profile |
| POST | /api/me/password | Change password |
| GET/DELETE | /api/auth/sessions | List and revoke sessions |
| GET/POST | /api/requests | List/create service requests |
| GET/PUT/DELETE | /api/requests/{request_id} | Read/update/delete request |
| GET/POST | /api/groups | List/create groups |
| GET/PATCH/DELETE | /api/groups/{group_id} | Read members/rename/delete group |
| POST/DELETE | /api/groups/{group_id}/members | Add/remove members |
| GET/POST | /api/groups/{group_id}/requests | List/create shared requests |
| PATCH/DELETE | /api/groups/{group_id}/requests/{request_id} | Update/delete shared request |
| GET | /api/admin/overview | Admin overview statistics |
| GET/PATCH/POST | /api/admin/users... | User management, role and ban actions |
| GET | /api/admin/activity | Audit activity |
| GET | /api/admin/security | Security events and summaries |
| GET | /api/admin/export/{kind} | CSV export |
| GET | /api/health | Backend health |
| GET | /api/docs | Interactive OpenAPI documentation |

All admin endpoints require the reusable admin dependency. Protected routes require a valid bearer access token and active session.

## 7. Security controls and limitations

Controls implemented in code:
- Server-side JWT verification and active-session verification.
- Role/ownership checks on protected operations.
- HttpOnly refresh cookie, hashed token storage, refresh rotation and revocation.
- Ban state checked on each protected request; ban revokes active sessions.
- Login lockout and security-event records.
- Backend-only Supabase privileged key, CORS origin allow-list and security response headers.
- Pydantic input validation and generic database error responses.
- CSV formula injection mitigation.

Supabase Auth manages password storage and salted password hashing; CampusConnect applies a server-side pepper before submitting passwords to Auth. The pepper must never be committed or exposed in frontend variables.

Limitations/verification still required:
- Apply the final Supabase migration before deploying the branch.
- Confirm the deployed Supabase JWT lifetime is configured to 900 seconds or less.
- Validate the refresh-cookie flow, all RBAC cases and group permissions against hosted Supabase/Vercel.
- Confirm the required two admin accounts, three student accounts and one group with mixed permissions using actual demo accounts.
- Automated RBAC unit tests do not substitute for end-to-end live testing.

## 8. Automated testing

The repository includes pytest policy tests for:
- Student allowed/denied creation.
- Student ownership and Pending-only update/delete restrictions.
- Staff status-only updates and denial of content changes.
- Admin request management.

The GitHub Actions workflow runs:
- Frontend TypeScript and Vite production build.
- Backend Python compile/import and FastAPI route verification.
- pytest authorization tests.

Record the final successful CI run and local/live verification results before submission.

## 9. Deployment information

- Frontend: https://campusconnect-two-ivory.vercel.app/
- API docs: https://campusconnect-two-ivory.vercel.app/api/docs
- Health endpoint: https://campusconnect-two-ivory.vercel.app/api/health
- GitHub: https://github.com/Ayesha-IUb/campusconnect

The final features are in the final-viva-2026 pull request and are not part of production main until merged. Apply migration 002 and configure Vercel variables before merging/deployment.

## 10. Demo accounts and evidence

Fill in actual user UUIDs after creating test accounts. Passwords must not be stored in this GitHub repository.

| Account | User UUID | Role |
|---|---|---|
| Demo admin 1 | [add actual UUID] | admin |
| Demo admin 2 | [add actual UUID] | admin |
| Demo student 1 | [add actual UUID] | student |
| Demo student 2 | [add actual UUID] | student |
| Demo student 3 | [add actual UUID] | student |

Shared group:
- Name: [actual group name]
- Owner UUID: [actual owner UUID]
- Member with create permission: [actual UUID]
- Member with edit permission: [actual UUID]
- Member with assign permission: [actual UUID]

### Report screenshots to add

Replace these placeholders with genuine, unedited screenshots from the deployed Vercel app:
1. Student request workspace.
2. Profile update and active sessions.
3. Group with members and distinct permissions.
4. An RBAC-denied action/API response.
5. Admin user dashboard and ban/unban.
6. Activity log and Security view.
7. CSV export in action or downloaded output.

### Video demonstration

Record a 5–8 minute screen recording with voice on the deployed URL. Show login, student experience, a denied RBAC operation, a group with mixed permissions, token refresh/expiry evidence in browser DevTools and the Admin dashboard, including ban/unban, activity and export. The recording must show the actual deployed application and actual demo accounts.

## 11. Conclusion

CampusConnect evolves the original service-request MVP into a multi-user application with authentication, ownership-based access control, staff/admin workflows, shared groups, session management, moderation and audit/security capabilities. The final submission should be made only after the hosted schema migration, environment configuration, live verification, actual screenshots and demo video are complete.
