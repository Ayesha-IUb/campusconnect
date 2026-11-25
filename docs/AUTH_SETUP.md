# CampusConnect Authentication, Database and Deployment Setup

## 1. Apply database migrations

Use the Supabase SQL Editor in this order:

1. Run backend/migrations/001_auth_rbac.sql if it has not already been applied.
2. Run backend/migrations/002_final_features.sql after migration 001.

Migration 002 adds:
- is_banned and ban metadata to profiles.
- Groups, member permissions and group/assignee fields on service requests.
- Hashed refresh/access token records in app_sessions.
- Activity logs, security events and failed-login records.

The application uses the backend Supabase service client for protected data access. These new tables have RLS enabled and no browser-facing write policies.

## 2. Supabase Auth settings

In Supabase Authentication settings:
- Keep email/password authentication enabled.
- Use the deployed site URL https://campusconnect-two-ivory.vercel.app for the Site URL and allowed redirect URLs.
- Set the JWT/access-token lifetime to 900 seconds or less to satisfy the course requirement.
- Configure refresh/session lifetime consistently with the application's seven-day refresh-cookie/session lifetime.

Supabase Auth performs salted password hashing. CampusConnect adds a server-side HMAC pepper pre-hash before sending the password to Supabase Auth. The pepper must be stable and must never be exposed to the browser or repository.

## 3. Vercel environment variables

Set the following for the backend deployment:

| Variable | Purpose |
|---|---|
| SUPABASE_URL | Supabase project URL |
| SUPABASE_SECRET_KEY | Backend-only privileged key; never expose it to Vite |
| SUPABASE_ANON_KEY | Public/anon key for backend Supabase Auth REST calls |
| PASSWORD_PEPPER | Stable high-entropy secret used by the backend password pre-hash |
| REFRESH_TOKEN_DAYS | Optional; defaults to 7 |
| FRONTEND_ORIGINS | Comma-separated allowed frontend origins |

For the frontend, set only:
- VITE_SUPABASE_URL
- VITE_SUPABASE_ANON_KEY

The backend can fall back to the existing VITE_SUPABASE_ANON_KEY value if SUPABASE_ANON_KEY is not set, but a server-side SUPABASE_ANON_KEY is clearer. Never put the service-role/secret key in a VITE_ variable.

After changing Vercel variables, redeploy the application.

## 4. Existing account compatibility

Older accounts were originally registered before the server-side pepper was added. The login flow first verifies the peppered form; if that fails, it tries the old raw password once and upgrades the stored Supabase Auth password to the peppered form. This compatibility path is intended to avoid forcing all existing demo accounts to be recreated.

After deploying this authentication flow, users should sign in again because the application now requires an active app_sessions record for each access token.

## 5. Assign admin and staff roles

All new self-registrations receive the Student role. A public role selector is intentionally not provided.

After trusted test accounts register and confirm their email, promote selected accounts using the SQL Editor. Replace the example email with the actual demo email:

    update public.profiles set role = 'admin'
    where email = 'admin-one@example.edu';

    update public.profiles set role = 'admin'
    where email = 'admin-two@example.edu';

    update public.profiles set role = 'staff'
    where email = 'staff@example.edu';

Do not make a student account an admin merely for convenience. Use only test accounts.

## 6. Role and group permissions

| Action | Student | Staff | Admin |
|---|---|---|---|
| Sign in / sign out | Yes | Yes | Yes |
| Create request | Own | No | Any |
| View request list | Own requests | All requests | All requests |
| Edit request details | Own pending requests | No | All requests |
| Change request status | No | Yes | Yes |
| Delete request | Own pending requests | No | Any |
| Administer users/groups/logs | No | No | Yes |

For groups, the group owner controls membership and grants can_create_requests, can_edit_requests and can_assign_requests permissions. The owner alone can rename/delete the group, manage members and delete shared requests. Backend checks are authoritative; hiding a UI control is not a security boundary.

## 7. Security behavior

- Access JWT is verified on every protected API request.
- The backend also checks the current profile role, ban status and active-session token hash.
- Refresh tokens are placed in an HttpOnly cookie and only their SHA-256 hashes are stored in the database.
- Refresh rotates the Supabase token pair and updates the stored hashes.
- Logout/session revoke invalidates the server-side session record.
- A banned user is rejected on the next protected request; banning also revokes the user's active sessions.
- Five failed logins for an email/IP pair within 15 minutes trigger a lockout response.
- CORS is limited to configured frontend origins. Security response headers are applied by FastAPI.

## 8. Live verification checklist

Use only the deployed Vercel URL; localhost screenshots do not satisfy the course requirement.

1. Check /api/health and /api/docs.
2. Sign in, reload and confirm the session restores.
3. Wait for/force an access token expiry in a test account and confirm the refresh-cookie flow.
4. Sign out and confirm the refresh session is revoked.
5. Verify student ownership restrictions and staff status-only restrictions.
6. Create a group with different create/edit/assign permissions; verify each member's denied and allowed actions.
7. Verify admin user search, role changes, ban/unban, session revoke, activity, security and CSV exports.

Do not publish secrets, passwords, or real personal information in GitHub.
