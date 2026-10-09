# Technical Design Document (TDD)

## CampusConnect: University Service Request Management System

**Version:** 1.0\
**Status:** Course project draft

## 1. Architecture

CampusConnect uses a client-server architecture: - **Frontend:** React +
TypeScript + Vite. - **Backend:** FastAPI + Python. - **API style:**
REST with JSON. - **Persistence:** relational database. - **API
exploration:** FastAPI Swagger UI at `/docs` during local development.

## 2. High-Level Request Flow

1.  User interacts with a React page.
2.  Frontend validates basic form input.
3.  Frontend sends an HTTP request to the FastAPI endpoint.
4.  FastAPI validates input using request schemas.
5.  Application logic checks business rules and accesses the database.
6.  Backend returns a JSON response and HTTP status code.
7.  Frontend displays the result or a useful error message.

## 3. Proposed Backend Structure

The exact files may evolve as implementation grows.

-   `main.py`: create the FastAPI app and register routers.
-   `routers/`: API endpoints grouped by resource.
-   `schemas/`: Pydantic request/response models.
-   `models/`: database models.
-   `services/`: business rules and workflow logic.
-   `database/`: database connection and session configuration.
-   `tests/`: API and business-logic tests.

For the first increment, keep the structure simple and avoid creating
empty layers that are not yet needed.

## 4. Proposed Frontend Structure

-   `src/`: application source.
-   `components/`: reusable UI elements.
-   `pages/`: service list, request list, request form, request detail.
-   `api/`: functions for calling backend endpoints.
-   `types/`: shared TypeScript types.
-   `App.tsx`: application shell and routing entry point, depending on
    the template.

## 5. Proposed Data Model

### User

-   `id` (primary key)
-   `name`
-   `email` (unique)
-   `role` (Student, Staff, Administrator; Beta authorization)

### Service

-   `id` (primary key)
-   `name`
-   `description`
-   `is_active`

### ServiceRequest

-   `id` (primary key)
-   `student_id` (foreign key to User)
-   `service_id` (foreign key to Service)
-   `title`
-   `description`
-   `status` (e.g. Submitted, In Progress, Completed, Rejected,
    Cancelled)
-   `assigned_staff_id` (nullable foreign key to User)
-   `staff_remark` (optional)
-   `created_at`
-   `updated_at`

## 6. Proposed REST API

These are planned endpoints, not a claim that they have already been
implemented.

  --------------------------------------------------------------------------------------------
  Method            Path                                  Purpose            Priority
  ----------------- ------------------------------------- ------------------ -----------------
  GET               `/api/health`                         Health check       Existing template

  GET               `/api/hello`                          Template/example   Existing template
                                                          endpoint           

  GET               `/api/services`                       List active        MVP
                                                          services           

  POST              `/api/requests`                       Create a request   MVP

  GET               `/api/requests`                       List requests      MVP
                                                          allowed for        
                                                          current            
                                                          user/context       

  GET               `/api/requests/{request_id}`          Get request        MVP
                                                          details            

  PATCH             `/api/requests/{request_id}`          Update eligible    MVP
                                                          request fields     

  DELETE            `/api/requests/{request_id}`          Cancel/delete an   MVP
                                                          eligible request   

  PATCH             `/api/requests/{request_id}/status`   Staff updates      MVP
                                                          status/remark      

  POST              `/api/auth/register`                  Register a user    Beta

  POST              `/api/auth/login`                     Authenticate a     Beta
                                                          user               

  GET               `/api/admin/users`                    Administrator user Beta
                                                          management         

  POST              `/api/admin/services`                 Create/manage      Beta
                                                          services           
  --------------------------------------------------------------------------------------------

## 7. Authorization Design

-   **MVP:** implement core CRUD and ownership rules suitable for local
    development; do not represent the application as production-secure
    without authentication.
-   **Beta:** authenticate users, derive identity from the authenticated
    session/token, and enforce roles and permissions on the backend.
-   Proposed permissions include `services:read`, `services:manage`,
    `requests:create`, `requests:read`, `requests:update`,
    `requests:cancel`, `requests:manage`, and `users:manage`.
-   The frontend may hide unavailable actions for usability, but backend
    authorization remains the source of truth.

## 8. Error Handling and Validation

-   Use Pydantic schemas to validate API payloads.
-   Return suitable HTTP status codes for success, invalid input,
    missing resources, and denied access.
-   Avoid exposing secrets or stack traces to end users.
-   Keep configuration and secrets out of source control.

## 9. Testing Strategy

-   Test health endpoint and each implemented API route.
-   Test valid and invalid request payloads.
-   Test request ownership and status-transition rules.
-   For Beta, test allowed and denied access for each role and
    permission.
-   Perform a manual end-to-end check from the React UI to the FastAPI
    API.

## 10. Development and Delivery

-   Run frontend and backend locally during development.
-   Use feature branches for work.
-   Make focused commits with descriptive messages.
-   Open a Pull Request for review and link it to the related Issue.
-   MVP focuses on local core REST/CRUD functionality; Beta adds
    authentication, RBAC, permission scopes, profiles/dashboard,
    security hardening, and deployment.
