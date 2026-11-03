-- CampusConnect authentication and RBAC migration
-- Run this entire script once in Supabase SQL Editor.

-- Every newly registered Supabase Auth user gets a student profile.
create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    email text unique,
    full_name text not null default '',
    role text not null default 'student'
        check (role in ('student', 'staff', 'admin')),
    created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

-- Users can read their own profile. Role changes are deliberately not allowed
-- through client-side profile updates.
drop policy if exists "Users can read own profile" on public.profiles;
create policy "Users can read own profile"
on public.profiles for select
to authenticated
using (auth.uid() = id);

-- Create profiles automatically when Supabase Auth creates a user.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
    insert into public.profiles (id, email, full_name, role)
    values (
        new.id,
        new.email,
        coalesce(new.raw_user_meta_data ->> 'full_name', ''),
        'student'
    )
    on conflict (id) do nothing;
    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute procedure public.handle_new_user();

-- Link existing service requests to their owner.
alter table public.service_requests
add column if not exists user_id uuid references auth.users(id) on delete set null;

create index if not exists service_requests_user_id_idx
on public.service_requests(user_id);

-- The backend uses the Supabase secret/service-role key and performs explicit
-- authorization checks in FastAPI. Do not expose that key to the browser.
-- RLS is enabled as defence in depth for any future direct client access.
alter table public.service_requests enable row level security;

-- No anon/authenticated policies are intentionally added for service_requests.
-- All CRUD goes through the backend after JWT and role verification.

-- IMPORTANT: promote trusted staff/admin accounts manually after registration.
-- Replace the email below, then run a separate statement, e.g.:
-- update public.profiles set role = 'admin' where email = 'your-admin@example.com';
