"""Unit tests for the centralized request RBAC policies."""
import pytest
from fastapi import HTTPException

from rbac import (
    assert_can_create_request,
    assert_can_delete_request,
    assert_can_update_request,
)

STUDENT = {"id": "student-1", "role": "student"}
OTHER_STUDENT = {"id": "student-2", "role": "student"}
STAFF = {"id": "staff-1", "role": "staff"}
ADMIN = {"id": "admin-1", "role": "admin"}
PENDING = {"id": 12, "user_id": "student-1", "title": "WiFi",
           "description": "No internet", "category": "IT Support", "status": "Pending"}


def test_student_can_create_request():
    assert_can_create_request(STUDENT)


def test_staff_cannot_create_request():
    with pytest.raises(HTTPException) as exc:
        assert_can_create_request(STAFF)
    assert exc.value.status_code == 403


def test_student_cannot_read_update_another_owners_request():
    payload = {"title": "Changed", "description": "No internet", "category": "IT Support", "status": "Pending"}
    with pytest.raises(HTTPException) as exc:
        assert_can_update_request(OTHER_STUDENT, PENDING, payload)
    assert exc.value.status_code == 403


def test_student_cannot_change_status():
    payload = {"title": "WiFi", "description": "No internet", "category": "IT Support", "status": "Resolved"}
    with pytest.raises(HTTPException) as exc:
        assert_can_update_request(STUDENT, PENDING, payload)
    assert exc.value.status_code == 403


def test_staff_can_change_status_only():
    payload = {"title": "WiFi", "description": "No internet", "category": "IT Support", "status": "In Progress"}
    assert_can_update_request(STAFF, PENDING, payload)


def test_staff_cannot_edit_title():
    payload = {"title": "Changed", "description": "No internet", "category": "IT Support", "status": "In Progress"}
    with pytest.raises(HTTPException) as exc:
        assert_can_update_request(STAFF, PENDING, payload)
    assert exc.value.status_code == 403


def test_admin_can_update_any_request():
    payload = {"title": "Changed", "description": "Updated", "category": "Other", "status": "Resolved"}
    assert_can_update_request(ADMIN, PENDING, payload)


def test_student_can_delete_own_pending_request():
    assert_can_delete_request(STUDENT, PENDING)


def test_student_cannot_delete_other_users_request():
    with pytest.raises(HTTPException) as exc:
        assert_can_delete_request(OTHER_STUDENT, PENDING)
    assert exc.value.status_code == 403


def test_admin_can_delete_any_request():
    assert_can_delete_request(ADMIN, PENDING)
