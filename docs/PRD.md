# Product Requirements Document (PRD)

## CampusConnect: University Service Request Management System

**Version:** 1.0\
**Status:** Course project draft\
**Technology:** React + TypeScript frontend; FastAPI + Python backend

## 1. Product Overview

CampusConnect is a web application for managing university service
requests. Students can submit and track requests for university
services. Staff can review requests assigned to them and update their
progress. Administrators can manage users, services, assignments, and
permissions.

## 2. Problem Statement

University service requests may be handled through scattered messages or
informal processes, making it difficult for students to track progress
and for staff to maintain a consistent record. CampusConnect provides
one place to submit, manage, and track requests.

## 3. Goals

-   Provide a central service-request workflow.
-   Let students create and track their own requests.
-   Let staff process assigned requests and record status updates.
-   Give administrators tools to manage services and user access.
-   Use a REST API between the frontend and backend.

## 4. Users and Roles

-   **Student:** browses available services and manages their own
    requests.
-   **Staff:** handles assigned requests and updates progress.
-   **Administrator:** manages users, services, assignments, and access
    permissions.

## 5. Scope and Priorities

### MVP (midterm)

-   View the available service list.
-   Create a service request.
-   View the current user's requests and request details.
-   Update or cancel an eligible request.
-   Staff can view requests and update their status.
-   Persist request and service data in a relational database.
-   Expose core operations through REST API endpoints.
-   Use a React + TypeScript frontend and FastAPI + Python backend.

### Beta (final)

-   User authentication.
-   Role-based access control (RBAC) for Student, Staff, and
    Administrator.
-   Permission/scope enforcement on protected endpoints.
-   User profile and role-specific dashboard.
-   Administrator tools for managing users, services, and staff
    assignments.
-   Input validation, secure error handling, and deployment.
-   Optional reporting and feedback features if time permits.

## 6. Core User Stories

-   As a Student, I want to submit a service request so the university
    can address my issue.
-   As a Student, I want to see the status of my own requests so I know
    what is happening.
-   As a Staff member, I want to view and update assigned requests so I
    can process them.
-   As an Administrator, I want to manage services and assign staff so
    requests reach the appropriate team.

## 7. Success Criteria

-   A student can create a request and later see its saved details and
    status.
-   Staff can update a request's status through the application.
-   The frontend communicates with the backend through documented REST
    endpoints.
-   In Beta, users can access only the actions allowed by their role and
    permissions.

## 8. Out of Scope

-   AI/ML features.
-   Payment processing.
-   Native mobile applications.
-   Integration with the university's official student information
    system.

## 9. Assumptions and Constraints

-   This is a course project and will be built incrementally.
-   The MVP prioritizes core CRUD operations and local development.
-   Authentication, RBAC, advanced permissions, and deployment are
    planned for Beta.
-   Only necessary student/request information should be stored.
