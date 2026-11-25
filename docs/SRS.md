# Software Requirements Specification (SRS)
## CampusConnect: University Service Request Management System

**Version:** 2.0 · **Status:** Final project specification

## 1. Purpose and scope
This document specifies the functional and security requirements for CampusConnect, a React/TypeScript and FastAPI service-request platform backed by Supabase PostgreSQL/Auth and deployed through Vercel.

## 2. User classes
- Student
- Staff
- Administrator

## 3. Functional requirements

### Authentication and sessions
- AUTH-01: The system shall support email/password signup and login.
- AUTH-02: The system shall issue a signed access JWT through Supabase Auth and verify it on protected API routes.
- AUTH-03: The backend shall set an HttpOnly refresh cookie and rotate refresh tokens.
- AUTH-04: Logout and explicit session revocation shall invalidate stored session records.
- AUTH-05: Users shall list and revoke their own sessions.
- AUTH-06: Users shall update their full name.
- AUTH-07: Users shall change their password only after the current password is verified.
- AUTH-08: Five failed attempts for an email/IP pair within the configured time window shall trigger a temporary lockout.

### Service requests
- REQ-01: Students and administrators shall create requests with title, description and category.
- REQ-02: Students shall list and retrieve only their own requests.
- REQ-03: Staff and administrators shall view all requests.
- REQ-04: Students shall edit/delete only their own Pending requests.
- REQ-05: Staff shall update status only.
- REQ-06: Administrators shall manage all requests.
- REQ-07: Invalid fields shall return validation errors; unknown records shall return not-found responses.

### RBAC and groups
- RBAC-01: Roles shall be read from the database and enforced on the backend.
- RBAC-02: Shared permission rules shall be implemented in a reusable RBAC module and group service.
- GROUP-01: A user shall create a group and become its owner.
- GROUP-02: The owner shall add/remove registered members.
- GROUP-03: The owner shall grant create, edit and assign permissions independently.
- GROUP-04: Members shall only perform shared-request actions allowed by their permissions.
- GROUP-05: Only the owner shall rename/delete a group, manage members and delete shared requests.
- GROUP-06: The owner/admin may view the member list; members may view groups they belong to.

### Administration and monitoring
- ADM-01: Administrators shall view overview statistics.
- ADM-02: Administrators shall search, filter, paginate and inspect users.
- ADM-03: Administrators shall change non-admin roles, ban/unban non-admin users and provide a ban reason.
- ADM-04: An administrator shall not change their own role, ban themselves or ban/change another admin.
- ADM-05: Banning shall revoke active sessions and cause subsequent protected requests to be rejected.
- ADM-06: Administrators shall moderate requests and groups, including bulk deletion.
- ADM-07: The system shall record activity/security events with timestamp, actor where known, IP and browser user agent where available.
- ADM-08: Administrators shall filter activity/security logs and export users, requests, groups and activity as CSV.
- ADM-09: Administrators shall purge old activity using an allowed retention period.

## 4. External interfaces

### REST API
Authentication: /api/auth/*; personal profile: /api/me; requests: /api/requests; groups: /api/groups; administration: /api/admin; API docs: /api/docs; health: /api/health.

### User interface
- Sign-in/sign-up form.
- Request management workspace.
- Profile and active sessions screen.
- Groups and shared requests workspace.
- Admin tabs for users, content, activity and security.

## 5. Data requirements
- Profile records use Supabase Auth user UUIDs and database role/ban metadata.
- Service requests store owner, optional group, optional assignee, category, status and timestamps.
- Groups store a single owner; group_members stores independent permission flags.
- app_sessions stores only hashed access/refresh tokens and device metadata.
- activity_logs and security_events store audit/security metadata; never store passwords or bearer tokens.

## 6. Security and non-functional requirements
- Protected requests require a valid JWT, active non-revoked session and unbanned user.
- Supabase privileged credentials and password pepper are backend-only.
- Refresh cookies shall be HttpOnly, SameSite=Lax and Secure on HTTPS.
- CORS shall permit only configured frontend origins.
- Input fields shall be validated by Pydantic.
- Database errors shall not return stack traces to clients.
- Application data shall persist in Supabase PostgreSQL, not ephemeral serverless disk.

## 7. Acceptance criteria
- Authentication succeeds for a valid account and rejects invalid/expired access tokens.
- Refresh rotates the refresh token and logout/session revoke blocks further protected requests after session validation.
- Students cannot read/update/delete another student's request.
- Staff cannot create or delete requests and can only change status.
- Group members with no create permission cannot create shared requests; edit/assign operations require the corresponding flag.
- Non-admin users cannot access admin endpoints; admin safety restrictions are enforced.
- Ban, activity, security and CSV functions return expected data on hosted Supabase.
- Frontend build, backend import checks and RBAC unit tests pass.
