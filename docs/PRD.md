# Product Requirements Document (PRD)
## CampusConnect: University Service Request Management System

**Version:** 1.1 | **Status:** MVP planning document

## 1. Product overview
CampusConnect is a web application for submitting, tracking, and managing university service requests. Students can report campus problems; staff can review requests and update their status.

## 2. Problem statement
Requests about classroom equipment, Wi-Fi, facilities, and other services may be scattered across messages, calls, or paper forms. This makes tracking progress difficult for students and organizing work difficult for staff. CampusConnect provides one organized workflow.

## 3. Goals and success criteria
- Students can submit a request with a title, description, and category.
- Students can view submitted requests and their statuses.
- Staff can review requests and update status.
- Request information is stored centrally.
- The design supports later authentication and role-based access control.

MVP success means a valid request can be created, saved, retrieved, displayed, and updated, while invalid input returns a clear error.

## 4. Target users
### Students
Students who need to report a campus service issue and track whether it has been received, is being handled, or has been resolved.

### Service staff
University employees, such as IT support or facilities staff, who review requests and update progress.

### Administrators
Authorized personnel who will manage users, service categories, and permissions in a later release.

## 5. User stories
- As a student, I want to submit a service request so the relevant team can address a problem.
- As a student, I want to view request status so I know whether action has been taken.
- As a staff member, I want to review requests and update their status so students can see progress.
- As an administrator, I want to manage categories and access so the system remains organized.

## 6. Scope
### MVP
- Create, list, and retrieve service requests.
- Update request status.
- Validate required fields.
- React + TypeScript frontend and FastAPI backend.
- Persistent storage suitable for local development.

### Later / Beta
- Authentication and role-based permissions.
- Separate student, staff, and administrator views.
- Request assignment, filtering, and search.
- Audit logging, security improvements, and deployment.

### Out of scope for MVP
- Native mobile apps.
- University single sign-on.
- Email/SMS notifications.
- Complex service-level analytics.

## 7. Milestones
| Milestone | Planned work | Completion evidence |
|---|---|---|
| M1: Foundation | Repository, frontend/backend setup, PRD/SRS/TDD, Git workflow | App runs locally and docs are reviewed |
| M2: MVP API | Request model and create/list/detail/status endpoints | API tests pass |
| M3: MVP frontend | Request form and request list/status view | Frontend calls API and displays saved data |
| M4: Integration | Validation, error handling, tests | Core flows pass documented tests |
| M5: Beta | Authentication, roles, staff/admin views | Role permissions are tested |
| M6: Deployment | Environment setup and hosting | Deployed app and configuration documented |

These milestones are plans, not claims that all features are already implemented.

## 8. Functional requirements
- FR-1: Accept a request title, description, and category.
- FR-2: Reject requests with missing required fields.
- FR-3: Assign a unique ID to each saved request.
- FR-4: Set new requests to `Submitted`.
- FR-5: Allow requests to be listed and retrieved.
- FR-6: Allow authorized staff to update status in Beta.
- FR-7: Enforce role-based access in Beta.

## 9. Non-functional requirements
- Usability: forms and status labels should be clear.
- Maintainability: separate frontend and backend modules.
- Reliability: return explicit API errors.
- Security: protect credentials and privileged operations.
- Testability: test core API behavior automatically.

## 10. Assumptions and risks
This is a course project and initially a local demonstration. Real staff accounts and university service rules may not be available. Minimize personal data and use non-sensitive test data.
