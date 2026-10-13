# Software Requirements Specification (SRS)

## CampusConnect: University Service Request Management System

**Version:** 1.0\
**Status:** Course project draft

## 1. Purpose

This document defines the functional and non-functional requirements for
CampusConnect.

## 2. System Overview

CampusConnect consists of a React + TypeScript frontend and a FastAPI +
Python backend. The frontend calls backend REST APIs. A relational
database will persist users, services, and requests.

## 3. User Classes

-   **Student:** accesses services and manages their own requests.
-   **Staff:** views and processes assigned requests.
-   **Administrator:** manages users, services, assignments, and
    permissions.

## 4. Functional Requirements

  -----------------------------------------------------------------------
  ID                      Requirement             Priority
  ----------------------- ----------------------- -----------------------
  FR-01                   The system shall        MVP
                          display the available   
                          university services.    

  FR-02                   A student shall be able MVP
                          to create a service     
                          request with a service, 
                          title, and description. 

  FR-03                   A student shall be able MVP
                          to view their own       
                          requests and each       
                          request's status.       

  FR-04                   A student shall be able MVP
                          to update or cancel an  
                          eligible request.       

  FR-05                   Staff shall be able to  MVP
                          view requests available 
                          or assigned to them.    

  FR-06                   Staff shall be able to  MVP
                          update a request status 
                          and add a processing    
                          remark.                 

  FR-07                   The backend shall       MVP
                          provide REST endpoints  
                          for service and request 
                          CRUD operations.        

  FR-08                   The system shall store  MVP
                          services and requests   
                          in a relational         
                          database.               

  FR-09                   Users shall be able to  Beta
                          register and log in.    

  FR-10                   The system shall        Beta
                          enforce Student, Staff, 
                          and Administrator role  
                          access.                 

  FR-11                   Protected API           Beta
                          operations shall        
                          enforce explicit        
                          permissions/scopes.     

  FR-12                   Administrators shall    Beta
                          manage users, services, 
                          and staff assignments.  

  FR-13                   The system shall        Beta
                          provide                 
                          role-appropriate        
                          profile/dashboard       
                          views.                  

  FR-14                   The system shall        Beta
                          support deployment with 
                          environment-specific    
                          configuration.          
  -----------------------------------------------------------------------

## 5. Main Use Cases

### UC-01: Create a service request (MVP)

1.  Student opens the service list.
2.  Student selects a service and enters request details.
3.  Frontend validates required fields and sends a request to the API.
4.  Backend validates and stores the request.
5.  System returns the created request and its initial status.

### UC-02: Track a request (MVP)

1.  Student opens their request list.
2.  Frontend requests the student's requests from the API.
3.  Backend returns only requests belonging to that student.
4.  Student views details and status.

### UC-03: Process a request (MVP)

1.  Staff opens the request queue.
2.  Staff selects a request.
3.  Staff updates its status and adds a remark.
4.  Backend validates and saves the update.
5.  The updated status is shown to the user.

### UC-04: Manage access (Beta)

1.  Administrator assigns a role or permission.
2.  Backend validates the administrator's authorization.
3.  The system saves the change and applies it to protected API
    operations.

## 6. Data Requirements

-   **User:** id, name, email, role; authentication data will be added
    for Beta.
-   **Service:** id, name, description, active status.
-   **ServiceRequest:** id, student id, service id, title, description,
    status, assigned staff id (optional), remarks (optional),
    created/updated timestamps.

## 7. Interface Requirements

-   Frontend: React and TypeScript in a browser.
-   Backend: FastAPI REST API using JSON request/response bodies.
-   API documentation: OpenAPI/Swagger UI provided by FastAPI.
-   Database: relational database; exact engine may be selected during
    implementation.

## 8. Non-Functional Requirements

-   **Usability:** forms and status labels should be understandable to
    university users.
-   **Reliability:** invalid input should return clear validation errors
    rather than crash the application.
-   **Security (Beta):** protected operations must verify identity,
    role, and required permissions.
-   **Privacy:** students must not be able to access other students'
    private requests.
-   **Maintainability:** frontend, API routes, business logic, and data
    access should be organized clearly.
-   **Performance:** common list and detail requests should return
    promptly for a course-project-sized dataset.

## 9. Validation and Error Handling

-   Required fields must not be empty.
-   Invalid IDs or unknown services should return an appropriate client
    error.
-   Unauthorized operations should return an appropriate authorization
    error in Beta.
-   API responses should use consistent JSON structures.

## 10. Acceptance Criteria

-   MVP service and request operations work through the UI and REST API.
-   Created requests remain available after refresh/restart when
    database persistence is implemented.
-   Students can only view and change their own requests.
-   Staff can update request status according to the defined workflow.
-   Beta role and permission checks are tested for allowed and denied
    operations.
