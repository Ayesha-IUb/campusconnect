# CampusConnect Final Project Report

**Course:** CSE309 · Autumn 2026  
**Project:** CampusConnect — University Service Request Management System  
**Stack:** React + TypeScript, FastAPI, Supabase PostgreSQL/Auth, Vercel  
**Verification snapshot:** 28 November 2026

> **Evidence and verification status:** The final authentication, group and administration features were merged to \`main\` in PR #12 and a READY production deployment was created from commit \`92701f5690e73b20b4743a5ef1c5d84bf4a0de57\`. The production health endpoint returns \`{"status":"ok","database_configured":true}\`. Hosted database tables and columns for the final features are present. Automated checks passed. A live Student smoke test succeeded on the current preview deployment. Admin workflows, full live RBAC acceptance tests, the 21 genuine screenshots and the 5–8 minute video are **not yet evidenced here**. Do not treat planned screenshot labels below as captured evidence.

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

## 3. Requirements documents

The project specification is maintained in:
- [Product Requirements Document](PRD.md)
- [Software Requirements Specification](SRS.md)
- [Technical Design Document](TDD.md)

The SRS defines requirement identifiers such as AUTH-01–AUTH-08, REQ-01–REQ-07, RBAC-01–RBAC-02, GROUP-01–GROUP-06 and ADM-01–ADM-09. The traceability matrix in Section 11 links these requirements to test cases and planned screenshot IDs.

## 4. Implemented functionality

### 4.1 Service request workflow
- Create, list, retrieve, update and delete requests.
- Students see their own requests and may edit/delete their own Pending requests.
- Staff can view requests and change status only.
- Admins may manage all service requests.
- Pydantic validates request fields and category/status values.

### 4.2 Authentication and sessions
- Signup and password login are proxied through the FastAPI backend to Supabase Auth.
- Supabase issues a signed access JWT; the backend verifies token claims for protected operations.
- The frontend keeps the short-lived access token in local storage. The refresh token is stored in an HttpOnly cookie.
- Refresh calls rotate the token pair; only token hashes are stored in \`app_sessions\`.
- Logout and session revocation mark server-side sessions revoked.
- Profile name update and password change are provided. Password change requires the current password.
- Five failed attempts for an email/IP pair within 15 minutes trigger a login lockout.
- A server-side HMAC pepper pre-hash is applied before Supabase Auth's salted password hash. Keep the pepper secret and stable.

### 4.3 Role-based access control

The backend verifies identity, current database role, ban status and the active access-token session hash. Role checks are enforced server-side; frontend navigation is not treated as a security boundary.

| Action | Student | Staff | Admin |
|---|---|---|---|
| Create personal request | Yes | No | Yes |
| View requests | Own | All | All |
| Edit request details | Own Pending | No | All |
| Change request status | No | Yes | Yes |
| Delete personal request | Own Pending | No | All |
| Admin dashboard | No | No | Yes |

### 4.4 Groups
- Users can create groups and list groups they own or belong to.
- Owners can add registered users and choose create, edit and assign permissions.
- Members see shared requests and can perform actions allowed by their permissions.
- Only owners may rename/delete their group or manage members.
- Shared request deletion is restricted to the group owner; admin moderation is separate.

### 4.5 Administration and monitoring
- Dashboard overview: users, banned users, requests, groups and recent activity counts.
- User listing with search, role/status filters and pagination; user detail includes related requests, groups, sessions and recent activity.
- Role changes, ban/unban with a reason, bulk ban/unban and session revocation.
- Request/group content moderation and bulk-delete endpoints.
- Activity and security-event lists with filters, IP/account summaries and CSV exports.
- CSV formula-like cell values are escaped and exports are capped at 10,000 rows.
- Activity retention purge is available with a bounded retention period.

## 5. System architecture

### Frontend
\`\`\`text
frontend/src/
├── components/       Reusable UI and workspace components
├── services/api.ts   HTTP calls, token refresh retry and CSV download
├── types/            Shared TypeScript types
├── App.tsx           Main application state and navigation
└── index.css         Application styles
\`\`\`

### Backend
\`\`\`text
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
\`\`\`

Main data flow: **HTTP request → Router → Service → Repository → Supabase PostgreSQL**. Authentication and administrative workflows use dedicated service modules and the shared database helper for their specialized workflows.

## 6. Authentication and authorization flow

1. The frontend sends email/password to \`POST /api/auth/login\`.
2. The backend applies the server-side pepper pre-hash and calls Supabase Auth.
3. Supabase returns a signed access JWT and refresh token.
4. The backend stores hashes of both tokens in \`app_sessions\` and sets the refresh token in an HttpOnly cookie.
5. The frontend stores the short-lived access token and sends it as a Bearer token.
6. The backend verifies the JWT signature/claims, loads the current profile, checks ban status and verifies the active access-token hash.
7. If an API request returns 401, the frontend calls \`/api/auth/refresh\`; the backend validates the stored refresh hash, asks Supabase to rotate the pair and updates stored hashes.
8. Logout revokes the session and clears the cookie.

RBAC decisions use the current database profile role, request ownership and group-member permission flags. A Student cannot access admin endpoints merely by changing frontend state.

## 7. Database design and hosted schema verification

| Table | Purpose |
|---|---|
| profiles | Supabase user profile, role and ban state |
| service_requests | Personal and group requests, ownership, status and assignee |
| groups | Group name, description and owner |
| group_members | Per-user create/edit/assign permission flags |
| app_sessions | Hashed access/refresh tokens, device metadata, expiry and revocation |
| activity_logs | User and admin audit activity |
| security_events | Rejected tokens, failed login and security events |
| login_attempts | Failed/successful login attempt records used for lockout |

A read-only inspection of the hosted Supabase project on 28 November confirmed that all eight tables above exist and have Row Level Security enabled. The final-feature columns, including ban metadata, group IDs, assignee IDs and access-token hashes, are present. The database contained 2 Admin profiles and 4 Student profiles at the time of inspection (the four include the project owner's normal Student account and the three demo Student accounts).

The migration-list endpoint returned no migration-history rows. Therefore, this report records the **live schema inspection** as evidence; it does not claim that the migration ledger independently confirms the SQL migration execution history.

### 7.1 Configured demo group

The hosted database contains the group **CampusConnect Instructor Demo Group**:
- Owner: Demo Student 1.
- Demo Student 2: create and edit permissions enabled; assign permission disabled.
- Demo Student 3: assign permission enabled; create and edit permissions disabled.

The current project-owner Student account is not a member of this group, which is why the group list appears empty in that account's workspace. The database configuration itself was verified read-only.

## 8. Main API surface

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

## 9. Testing and verification results

| Check | Result | Evidence / scope |
|---|---|---|
| Frontend TypeScript check and Vite production build | Passed | GitHub Actions Project checks |
| Backend Python compile/import and route registration | Passed | GitHub Actions CampusConnect CI |
| Backend RBAC unit tests | 13 passed | CI and local pytest |
| Latest PR #13 workflow runs | Passed | CampusConnect CI run #32 and Project checks run #4 |
| Vercel production deployment | READY | Production deployment from main commit \`92701f5\` |
| Production API health | Passed | \`{"status":"ok","database_configured":true}\` |
| Hosted final-feature schema | Present | Read-only Supabase table/column inspection |
| Student live smoke test | Passed on preview | Authenticated Student workspace, Groups and Profile & Sessions loaded without page errors |
| Live admin workflows | Not yet verified | Requires an Admin browser session |
| Full live JWT refresh/revoke and role/group negative tests | Not yet verified | Unit tests are not a substitute for live acceptance tests |
| Genuine screenshots S1–S21 | Pending | Must be captured from the running app |
| 5–8 minute demo video | Pending | Must be recorded from the running app |

### 9.1 Student preview smoke test

The current preview URL was opened with an authenticated Student session. The browser showed:
- Service Requests: 2 total requests, both Pending.
- Groups: no groups visible to this Student account.
- Profile & Sessions: 7 session entries, including 4 active and 3 revoked.
- No page errors were observed.
- The Admin navigation item was not visible to the Student account, as expected.

This test does not establish that Admin pages or every API permission case has been tested live.

## 10. Project management and deployment

### 10.1 GitHub workflow
- PR #11 (frontend/backend folder structure) was merged to \`main\`.
- PR #12 (final authentication, groups and admin features) was merged to \`main\`.
- PR #13 (dedicated frontend page structure and signup payload correction) remains an open draft PR. It is not part of the production deployment and has not been merged.
- GitHub Actions checks for the latest PR #13 head commit completed successfully.
- The final production deployment is based on \`main\`, commit \`92701f5690e73b20b4743a5ef1c5d84bf4a0de57\`.

### 10.2 Deployment links
- Production frontend: https://campusconnect-two-ivory.vercel.app/
- Production API docs: https://campusconnect-two-ivory.vercel.app/api/docs
- Production health: https://campusconnect-two-ivory.vercel.app/api/health
- Current preview frontend: https://campusconnect-elaj4c1k7-sdceg.vercel.app/
- GitHub repository: https://github.com/Ayesha-IUb/campusconnect
- Draft PR #13: https://github.com/Ayesha-IUb/campusconnect/pull/13

The production health response confirms the backend is reachable and database configuration is present. A health response does not prove every authenticated feature is operational.

## 11. Requirement-to-test-to-screenshot traceability

The following is the planned evidence map for the required screenshot labels S1–S21. **Every screenshot is still pending capture**; these rows define what must be captured and must not be represented as completed evidence until the genuine screenshot is inserted.

| Requirement(s) | Test case | Planned screenshot | Evidence to capture |
|---|---|---|---|
| AUTH-01 | TC-AUTH-01 | S1 | Signup form and successful account confirmation/login state |
| AUTH-01, AUTH-02 | TC-AUTH-02 | S2 | Successful login and authenticated Student workspace |
| AUTH-02, RBAC-01 | TC-AUTH-03 | S3 | Protected API request with valid bearer token; redact token value |
| AUTH-03 | TC-AUTH-04 | S4 | HttpOnly refresh cookie attributes in browser DevTools; redact cookie value |
| AUTH-03, AUTH-04 | TC-AUTH-05 | S5 | Refresh rotation followed by logout/revocation evidence |
| AUTH-05 | TC-AUTH-06 | S6 | Profile & Sessions list and a revoked session |
| AUTH-06, AUTH-07 | TC-AUTH-07 | S7 | Profile name update and password-change validation (never show password) |
| AUTH-08 | TC-AUTH-08 | S8 | Login lockout after configured failed attempts |
| REQ-01, REQ-02 | TC-REQ-01 | S9 | Student creates a request and sees it in their own list |
| REQ-03 | TC-REQ-02 | S10 | Staff request list showing requests across users |
| REQ-04 | TC-REQ-03 | S11 | Student edits/deletes own Pending request |
| REQ-05 | TC-REQ-04 | S12 | Staff changes status while request content remains read-only |
| REQ-06, RBAC-01 | TC-REQ-05 | S13 | Admin manages a request |
| RBAC-01, REQ-07 | TC-RBAC-01 | S14 | Student is denied a forbidden request/admin operation (show status/message, no secrets) |
| GROUP-01, GROUP-02 | TC-GROUP-01 | S15 | Group owner and member list |
| GROUP-03 | TC-GROUP-02 | S16 | Create/edit/assign permission settings for different members |
| GROUP-04, GROUP-05 | TC-GROUP-03 | S17 | Member shared-request action allowed/denied according to permission |
| ADM-01, ADM-02 | TC-ADM-01 | S18 | Admin overview and user search/filter |
| ADM-03, ADM-04, ADM-05 | TC-ADM-02 | S19 | Admin role/ban controls and resulting session revocation |
| ADM-06, ADM-07, ADM-09 | TC-ADM-03 | S20 | Moderation, activity/security records and retention controls |
| ADM-08 | TC-ADM-04 | S21 | CSV export result and downloaded file |

Screenshots must be genuine, unedited captures from the deployed app. Redact bearer tokens, refresh cookies, passwords and other secrets before submission. Keep the original captures and label the final images S1–S21 consistently in the report PDF.

## 12. Demo account appendix

The following five demo profiles were found in the hosted database. Passwords are deliberately excluded from this public repository and must be supplied only through the instructor's private submission channel.

| Demo account | User UUID | Role |
|---|---|---|
| Demo Admin 1 | 0e7bf5c4-e417-4dc1-ab56-8c0f1a80a4f1 | admin |
| Demo Admin 2 | 97952dc6-58f8-4a4a-b4fa-8959374221ba | admin |
| Demo Student 1 | 1b2e7100-6447-4480-a683-c8663309a924 | student |
| Demo Student 2 | 1b054778-5d4d-45b7-bfd6-00a36c80553f | student |
| Demo Student 3 | 6430f469-13cf-498d-a057-0c8978120b1f | student |

Configured mixed-permission group: **CampusConnect Instructor Demo Group**.
- Owner: Demo Student 1.
- Member with Create + Edit: Demo Student 2.
- Member with Assign: Demo Student 3.

No passwords or API secrets are included in this repository.

## 13. Video demonstration plan

Record a 5–8 minute screen recording with voice on the deployed production URL. Use the real demo accounts and show:
1. Student login and request creation/list.
2. Student denied access to an admin-only operation.
3. Group owner and members with different create/edit/assign permissions.
4. Profile and active-session list; show refresh/revocation behavior in DevTools without exposing token values.
5. Admin dashboard, user management and ban/unban.
6. Activity/security logs and CSV export.

The video must show the actual deployed application and actual demo accounts. The recording is not yet included in this repository.

## 14. Remaining submission checklist

- [x] PRD, SRS and TDD are present in \`docs/\`.
- [x] Final auth/groups/admin implementation merged to \`main\`.
- [x] Production deployment is READY.
- [x] Production health endpoint reports database configured.
- [x] Five demo accounts (2 Admin + 3 Student) exist in Supabase.
- [x] Mixed-permission demo group exists in Supabase.
- [x] Frontend build, backend compile/import and 13 RBAC unit tests passed.
- [ ] Capture and insert genuine screenshots S1–S21.
- [ ] Complete live Admin login and admin workflow tests.
- [ ] Complete live JWT refresh/revoke, negative RBAC and group permission acceptance tests.
- [ ] Generate the final report PDF with all 21 actual screenshots.
- [ ] Record and upload the 5–8 minute demo video.
- [ ] Submit/confirm final PDF, video and deployment links through the course Google Form.
- [ ] Provide demo passwords only through the instructor's private channel.

## 15. Conclusion

CampusConnect has its final authentication, RBAC, group and administration implementation merged into the production main branch. The hosted schema, demo-account roles, mixed-permission group, CI checks and production health endpoint have been inspected. The Student preview smoke test also succeeded. The submission is **not evidence-complete** until the live Admin and full acceptance tests, genuine S1–S21 screenshots, final PDF and 5–8 minute video are completed.
