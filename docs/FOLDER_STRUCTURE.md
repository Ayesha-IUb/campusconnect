# CampusConnect Folder Structure

This refactor separates interface components, API communication, shared types,
HTTP route declarations, request validation, database access, and business rules.

## Frontend

```text
frontend/src/
├── components/
│   ├── AuthPage.tsx
│   ├── DashboardShell.tsx
│   ├── RequestDetails.tsx
│   ├── RequestForm.tsx
│   ├── RequestList.tsx
│   └── StatsGrid.tsx
├── constants/
│   └── requests.ts
├── services/
│   └── api.ts
├── types/
│   └── index.ts
├── App.tsx
├── index.css
└── main.tsx
```

- `components/`: reusable UI sections.
- `services/api.ts`: all Supabase Auth and FastAPI fetch calls.
- `types/`: shared TypeScript data types.
- `constants/`: request categories, statuses, and initial form values.
- `App.tsx`: application state and coordination between components.

## Backend

```text
backend/
├── routers/
│   ├── __init__.py
│   ├── auth.py
│   ├── health.py
│   └── requests.py
├── services/
│   ├── __init__.py
│   └── request_service.py
├── database.py
├── dependencies.py
├── main.py
├── models.py
└── schemas.py
```

- `routers/`: HTTP endpoint definitions.
- `schemas.py`: Pydantic validation and response schemas.
- `models.py`: typed descriptions of Supabase database records.
- `services/`: database operations and role-based business rules.
- `dependencies.py`: shared JWT authentication and role lookup.
- `database.py`: Supabase client setup and query execution.
- `main.py`: creates the FastAPI app and registers routers.

## Behaviour kept

The API endpoint paths and payloads stay the same. Student, staff, and admin
permissions continue to be checked on the backend. The Supabase migration,
environment variable names, and Vercel entrypoint are unchanged.
