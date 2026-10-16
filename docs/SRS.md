# Software Requirements Specification (SRS)
## CampusConnect: University Service Request Management System

**Version:** 1.1 | **Status:** MVP planning document

## 1. Purpose
This document defines CampusConnect's functional and non-functional requirements and provides a basis for implementation and testing.

## 2. Scope
CampusConnect is a web application for students to submit and track university service requests and for staff to process them. The MVP covers creating, listing, retrieving, and updating request status. Authentication, role-based access, and administrator management are planned for Beta.

**Included in MVP**
- React + TypeScript user interface.
- Python + FastAPI REST API.
- Persistent storage for requests.
- Input validation and clear API responses.
- Tests for the main request workflow.

**Not included in MVP**
- University single sign-on.
- Email/SMS notifications.
- Native mobile apps.
- Production analytics or university-system integrations.

## 3. User classes
- **Student:** submits requests and views them. Ownership checks are required once authentication is implemented.
- **Staff:** reviews and processes requests; staff permissions are Beta scope.
- **Administrator:** manages users, service categories, and permissions in Beta.

## 4. Operating environment
- OS: Windows, macOS, or Linux for development.
- Frontend: modern browser, React + TypeScript, Vite.
- Backend: Python 3.11+ and FastAPI, served by Uvicorn.
- Storage: SQLite is suitable for local MVP development; production choice is TBD.
- API: JSON over HTTP using REST-style endpoints.

## 5. Functional requirements
- SRS-FR-01: Create a service request from valid input.
- SRS-FR-02: Require title, description, and category.
- SRS-FR-03: Generate a unique ID for each saved request.
- SRS-FR-04: Set initial status to `Submitted`.
- SRS-FR-05: Return a list of requests.
- SRS-FR-06: Return request details by ID.
- SRS-FR-07: Update request status when the requested status is valid.
- SRS-FR-08: Return not-found for an unknown request ID.
- SRS-FR-09: Return a clear client error for invalid data.
- SRS-FR-10: Beta protected operations require authentication.
- SRS-FR-11: Beta staff/admin operations enforce role permissions.

## 6. External interface requirements
### User interface
- Request form with title, description, and category.
- Clear validation messages.
- Request list showing ID, title, category, creation time, and status.
- Status labels such as `Submitted`, `In Progress`, and `Resolved`.

### Planned API
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Check backend availability |
| POST | `/api/requests` | Create a request |
| GET | `/api/requests` | List requests |
| GET | `/api/requests/{request_id}` | Retrieve a request |
| PATCH | `/api/requests/{request_id}/status` | Update status |

The request endpoints are planned until implemented and tested. The health endpoint is a separate backend check.

### Data requirements
A request record should include `id`, `title`, `description`, `category`, `status`, `created_at`, and optionally `updated_at`.

## 7. Non-functional requirements
- Performance: common local API requests should respond promptly.
- Reliability: return meaningful HTTP status codes and errors.
- Security: never commit secrets; protect privileged routes when auth is added.
- Usability: the main workflow should be understandable without training.
- Maintainability: organize routes, models, and components.
- Testability: test successful and failed API requests.

## 8. Use cases
### UC-1: Submit request
1. Student opens the form and enters details.
2. Frontend sends data to `POST /api/requests`.
3. Backend validates and stores the request.
4. System returns the saved request or a validation error.

### UC-2: View requests
1. User opens the request list.
2. Frontend calls `GET /api/requests`.
3. Backend returns available records.
4. Frontend displays requests and statuses.

### UC-3: Update status
1. Staff selects a request and a new status.
2. Frontend sends the update.
3. Backend validates status and authorization.
4. Backend saves the change and returns the updated request.
5. Frontend displays the new status.

Proper identity and role checks are required before real-world deployment.

## 9. Acceptance criteria
- Valid input creates a saved record with a unique ID and initial status.
- Missing required fields return a validation error.
- Listing returns saved records.
- Unknown IDs return not-found.
- A valid status update persists.
- Automated tests cover success and failure cases.
- Beta protected routes reject unauthorized operations.
