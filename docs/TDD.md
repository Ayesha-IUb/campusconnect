# Technical Design Document (TDD)
## CampusConnect: University Service Request Management System

**Version:** 1.1 | **Status:** Proposed implementation design

## 1. Architecture
CampusConnect uses a frontend/backend architecture. React + TypeScript presents forms and request lists. FastAPI exposes JSON REST endpoints, validates input, and applies application rules. A database stores requests and, in Beta, user and role information.

## 2. Tech stack
| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React | Reusable UI components |
| Frontend language | TypeScript | Static types for frontend code |
| Frontend tooling | Vite | Development server and build tooling |
| Backend language | Python 3.11+ | Backend logic |
| Backend framework | FastAPI | REST endpoints and input validation |
| ASGI server | Uvicorn | Runs FastAPI |
| Database | SQLite for local MVP; production choice TBD | Persistent request storage |
| API documentation | OpenAPI / Swagger UI via FastAPI | Inspect and test endpoints |
| Version control | Git and GitHub | History, issues, branches, pull requests |
| Testing | pytest and FastAPI TestClient (planned) | Automated backend tests |
| Deployment | Vercel may host frontend; backend host TBD | Publish after local MVP works |

The repository has a Vite-based React/TypeScript frontend and FastAPI backend. Database integration, tests, and deployment must be verified separately before being described as complete.

## 3. Project structure
Proposed structure as features are implemented:

```text
campusconnect/
├── docs/
│   ├── PRD.md
│   ├── SRS.md
│   └── TDD.md
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── types/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── models/
│   │   ├── services/
│   │   └── database.py
│   ├── main.py
│   ├── requirements.txt
│   └── tests/
├── .gitignore
└── README.md
```

This is a proposed future structure; some folders may not exist yet. Create them as needed. Never commit `backend/venv/`, `node_modules/`, build output, local databases, or secrets.

## 4. Data design
### ServiceRequest
- `id`: unique integer or UUID.
- `title`: required short text.
- `description`: required text.
- `category`: required category name or ID.
- `status`: initially `Submitted`.
- `created_at`: creation timestamp.
- `updated_at`: timestamp updated when relevant fields change.

### User (Beta)
- `id`: unique identifier.
- `name`: display name.
- `email`: unique login identifier.
- `password_hash`: password hash only, never plaintext.
- `role`: `student`, `staff`, or `admin`.

In Beta, a request should reference its submitting user and optionally an assigned staff user. Students should access only their own requests; staff should only perform permitted actions.

## 5. Planned API design
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Existing basic health check |
| GET | `/api/hello` | Existing sample endpoint |
| POST | `/api/requests` | Create a request |
| GET | `/api/requests` | List requests |
| GET | `/api/requests/{request_id}` | Retrieve one request |
| PATCH | `/api/requests/{request_id}/status` | Update status |

Request endpoints are planned until implemented. Suggested statuses are `Submitted`, `In Progress`, and `Resolved`. Use appropriate HTTP status codes such as 201 for creation and 404 for missing records.

## 6. Configuration
- Keep environment-specific settings outside source code.
- Use environment variables for API URLs, database locations, and secret keys.
- Provide `.env.example` with placeholders only; never commit real credentials.
- Add `.env`, Python virtual environments, `node_modules/`, build output, and local database files to `.gitignore`.
- Configure CORS to allow the local frontend origin during development and restrict origins in production.
- Use a strong secret from the hosting environment when authentication is implemented.

Example placeholder settings:
```env
DATABASE_URL=sqlite:///./campusconnect.db
FRONTEND_ORIGIN=http://localhost:5173
SECRET_KEY=replace-with-a-long-random-secret-before-use
```

## 7. Deployment / configuration
### Local development
1. Install Node.js and Python.
2. In `frontend/`, run `npm install`, then `npm run dev`.
3. In `backend/`, create and activate a Python virtual environment and install `requirements.txt`.
4. Start FastAPI using the configured development command.
5. Open the frontend in a browser and use the backend Swagger UI to inspect API behavior.

### Deployment plan
- **Frontend:** Vercel is an optional target. Configure the API base URL to point to the deployed backend.
- **Backend:** select a Python-compatible hosting provider; configure start command, environment variables, CORS, and database connection.
- **Database:** use persistent storage; do not rely on an ephemeral filesystem for production data.
- **Secrets:** configure them in the hosting provider, never in committed files.
- **Verification:** test health checks, request create/list/update flows, and browser-to-API connectivity after deployment.

Documenting deployment does not mean deployment is complete. Verify the live environment before claiming it is running.

## 8. Security considerations
- Validate client input on the backend.
- Never store plaintext passwords.
- Enforce authentication and role authorization before enabling protected Beta operations.
- Avoid exposing sensitive data in responses or logs.
- Use HTTPS in production.
- Never commit `.env` files, credentials, or virtual environments.

## 9. Testing strategy
- Unit tests for validation and application logic.
- API tests for request create/list/detail/status operations.
- Negative tests for missing fields, invalid status, and unknown IDs.
- Frontend tests for form validation and loading/error states.
- Integration tests for frontend/backend communication.
- Beta security tests for role-based access.

## 10. Technical risks
Database and hosting choices may change. Authentication must be designed before real student data is used. CORS and API URLs differ between local and deployed environments. Adjust the proposed structure to match implemented code.
