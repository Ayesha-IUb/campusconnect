# Product Requirements Document (PRD)
## CampusConnect: University Service Request Management System

**Version:** 2.0 · **Status:** Final project scope

## 1. Product overview
CampusConnect is a web application for submitting, tracking and managing university service requests. Students report campus problems; staff review and process them; administrators manage users, content and security.

## 2. Problem statement
Requests about classroom equipment, Wi-Fi, facilities and library services can be scattered across messages or paper forms. CampusConnect centralizes request ownership, status and group collaboration, so students can track progress and staff can manage work.

## 3. Product goals
- Provide signup/login and secure JWT-protected API access.
- Restrict personal records to their owners and enforce Student/Staff/Admin roles on the server.
- Allow groups to share service requests with fine-grained create/edit/assign permissions.
- Give administrators tools to manage users, content, activity and security events.
- Keep records in hosted Supabase PostgreSQL and deploy the app through Vercel.

## 4. User classes
- **Student:** submit requests, view their own requests, collaborate in groups where invited.
- **Staff:** review all service requests and update status; no permission to create/delete personal requests.
- **Admin:** manage users and service content, review monitoring data and export records.

## 5. Functional scope

### Authentication and profile
- Sign up and sign in using email/password.
- Verify signed access JWTs on protected requests.
- Refresh tokens using an HttpOnly cookie, rotate tokens and revoke sessions on logout.
- List/revoke active sessions.
- Update profile name and change password after verifying current password.

### Service requests
- Create, list, view, update and delete requests.
- Enforce request ownership and role permissions.
- Validate title, description, category and status.

### Groups
- Create and list groups.
- Add/remove members and configure create/edit/assign permissions.
- Create and list shared requests; update only when permitted.
- Restrict rename, delete and member management to the group owner.

### Administration
- Overview counts, user search/filter/pagination and user detail.
- Role changes, ban/unban with reason, session revocation and bulk user actions.
- Request and group moderation.
- Activity and security logs, IP/account summaries, CSV export and activity purge.

## 6. Non-functional requirements
- Security: never commit secrets, validate inputs, enforce authorization server-side, limit CORS and use secure cookies over HTTPS.
- Reliability: return meaningful HTTP errors and keep data in hosted PostgreSQL.
- Maintainability: separate routers, services, repositories, schemas, models, frontend components, services and types.
- Testability: automate RBAC policy checks and production builds.
- Usability: provide loading, error and empty states and responsive workspace layouts.

## 7. Success criteria
The final project is considered ready for submission after:
- Frontend and backend build checks pass.
- Supabase migrations are applied to the hosted project.
- Demo accounts and a mixed-permission group are configured.
- Key authentication, ownership, role and group permission rules are verified on the live Vercel URL.
- Admin moderation, activity/security views and exports are verified.
- Genuine screenshots and a 5–8 minute demo video are prepared.

## 8. Out of scope
University single sign-on, payment services, native mobile apps and production integrations with university HR/student systems.
