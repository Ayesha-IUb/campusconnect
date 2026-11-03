# CampusConnect Authentication and RBAC Setup

## 1. Apply the database migration

1. Open the Supabase project used by CampusConnect.
2. Open **SQL Editor** and create a new query.
3. Copy and run the complete contents of `backend/migrations/001_auth_rbac.sql`.
4. Confirm that the `profiles` table exists and that `service_requests` now has a `user_id` column.

The migration creates a profile with the `student` role automatically for every new Supabase Auth user. Existing service requests keep a NULL `user_id`; they are not automatically assigned to a student.

## 2. Configure Supabase Auth

In Supabase **Authentication → URL Configuration**, set the Site URL to:

`https://campusconnect-two-ivory.vercel.app`

Add the deployed site URL to the allowed redirect URLs if email confirmation is enabled.

For a simple course MVP, email/password sign-in is used. If email confirmation is enabled, users must confirm their email before they can sign in.

## 3. Configure Vercel environment variables

Keep the existing backend variables:
- `SUPABASE_URL`
- `SUPABASE_SECRET_KEY` (backend only; never expose this in frontend code)

Add these frontend variables to the Vercel project for Production and Preview:
- `VITE_SUPABASE_URL` = the same Supabase project URL
- `VITE_SUPABASE_ANON_KEY` = the Supabase publishable/anon key

The publishable/anon key is intended for browser use. Never put the secret/service-role key in a `VITE_` variable.

Redeploy the Vercel project after changing environment variables.

## 4. Assign trusted staff and admin roles

All self-registered users become students. A user cannot choose their role during signup.

After a trusted staff/admin user registers, use Supabase SQL Editor to promote that account by email. Replace the example email:

```sql
update public.profiles
set role = 'admin'
where email = 'admin@example.edu';

update public.profiles
set role = 'staff'
where email = 'staff@example.edu';
```

Only a trusted project/database administrator should run these statements. Never add a public role-selection dropdown to signup.

## 5. Role permissions

| Action | Student | Staff | Admin |
|---|---|---|---|
| Sign in / sign out | Yes | Yes | Yes |
| Create request | Yes | No | Yes |
| View request list | Own requests | All requests | All requests |
| View one request | Own requests | All requests | All requests |
| Edit request details | Own pending requests | No | All requests |
| Change request status | No | Yes | Yes |
| Delete request | Own pending requests | No | Any request |

The backend verifies Supabase access tokens and checks the role in the database. Frontend button visibility is only a usability feature; backend checks are the actual permission enforcement.

## 6. Test checklist

1. Register a new account. It should receive the Student role.
2. Sign in and create a request.
3. Sign out, register/sign in as a second student, and confirm the first student's request is not visible.
4. Promote a test account to Staff using the SQL above. Sign in as Staff and verify that all requests are visible and status can be changed.
5. Promote a trusted test account to Admin. Verify admin CRUD.
6. Call `GET /api/requests` in Swagger without a bearer token. It should return 401.
7. Try a forbidden action. The API should return 403.

## Security notes

- Never commit Supabase secrets or place them in frontend variables.
- The backend uses the privileged Supabase secret key, so the API's JWT and role checks are critical. Do not expose this backend to real student data without a fuller security review.
- Existing requests with NULL `user_id` are legacy records. Students cannot see or claim them; staff/admin can still review them.
- Access tokens are held in browser localStorage in this MVP. For a production system, prefer a hardened session strategy (for example, secure HttpOnly cookies), add rate limiting and audit logging, and review token refresh/expiry handling.
