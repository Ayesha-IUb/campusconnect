"""Admin reporting, moderation, audit logs and safe CSV export."""
import csv
import io
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException

from app.core.models import CurrentUser
from app.activity.service import record_activity
from app.admin import repository as admin_repo


def overview() -> dict[str, int]:
    data = admin_repo.get_overview_data()
    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    users = data["users"]
    requests = data["requests"]
    groups = data["groups"]

    return {
        "users": len(users),
        "banned_users": sum(bool(row.get("is_banned")) for row in users),
        "requests": len(requests),
        "groups": len(groups),
        "new_users_7d": sum(row.get("created_at", "") >= since for row in users),
        "new_requests_7d": sum(row.get("created_at", "") >= since for row in requests),
        "new_groups_7d": sum(row.get("created_at", "") >= since for row in groups),
    }


def list_users(search: str | None, role: str | None, banned: bool | None,
               page: int, page_size: int) -> dict[str, Any]:
    result = admin_repo.list_users(search, role, banned, page, page_size)

    return {
        "items": result["items"],
        "total": result["total"],
        "page": page,
        "page_size": page_size,
    }

def user_detail(user_id: str) -> dict[str, Any]:
    result = admin_repo.get_user_detail_data(user_id)

    if result is None:
        raise HTTPException(status_code=404, detail="User not found.")

    return result


def change_role(target_id: str, role: str, actor: CurrentUser, request) -> dict[str, Any]:
    if target_id == actor["id"]:
        raise HTTPException(status_code=403, detail="An administrator cannot change their own role.")
    if role not in {"student", "staff", "admin"}:
        raise HTTPException(status_code=422, detail="Invalid role.")
    target = admin_repo.get_user_role(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
    if target["role"] == "admin":
        raise HTTPException(status_code=403, detail="An administrator cannot change another administrator's role.")
    result = admin_repo.update_user_role(target_id, role, datetime.now(timezone.utc).isoformat())
    record_activity(actor["id"], "user_role_changed", "user", target_id, request, {"role": role})
    return result.data[0]




def set_banned(target_id: str, banned: bool, reason: str | None,
               actor: CurrentUser, request) -> dict[str, Any]:
    if target_id == actor["id"]:
        raise HTTPException(status_code=403, detail="An administrator cannot ban their own account.")
    target = admin_repo.get_user_role(target_id)
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
    if target["role"] == "admin":
        raise HTTPException(status_code=403, detail="An administrator cannot ban another administrator.")
    now = datetime.now(timezone.utc).isoformat()
    values = {
        "is_banned": banned,
        "ban_reason": (reason or "").strip() if banned else None,
        "banned_at": now if banned else None,
        "updated_at": now,
    }
    result = admin_repo.update_user_ban(target_id, values)
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found.")
    if banned:
        admin_repo.revoke_active_sessions(target_id, now)
    record_activity(actor["id"], "user_banned" if banned else "user_unbanned",
                    "user", target_id, request, {"reason": reason or ""})
    return result.data[0]




def bulk_ban(user_ids: list[str], banned: bool, reason: str,
             actor: CurrentUser, request) -> dict[str, int]:
    changed = 0
    for user_id in dict.fromkeys(user_ids):
        if user_id == actor["id"]:
            continue
        target = admin_repo.get_user_role(user_id)
        if not target or target["role"] == "admin":
            continue
        set_banned(user_id, banned, reason if banned else None, actor, request)
        changed += 1
    return {"updated": changed}




def list_requests(search: str | None, status: str | None, page: int, page_size: int) -> dict[str, Any]:
    result = admin_repo.list_requests(search, status, page, page_size)
    return {
        "items": result["items"],
        "total": result["total"],
        "page": page,
        "page_size": page_size,
    }


def list_groups(search: str | None, page: int, page_size: int) -> dict[str, Any]:
    result = admin_repo.list_groups(search, page, page_size)
    return {
        "items": result["items"],
        "total": result["total"],
        "page": page,
        "page_size": page_size,
    }


def bulk_delete_requests(ids: list[int], actor: CurrentUser, request) -> dict[str, int]:
    result = admin_repo.bulk_delete_requests(ids)
    count = len(result.data or [])
    record_activity(actor["id"], "admin_bulk_requests_deleted", "request", request=request,
                    details={"deleted": count})
    return {"deleted": count}




def bulk_delete_groups(ids: list[str], actor: CurrentUser, request) -> dict[str, int]:
    result = admin_repo.bulk_delete_groups(ids)
    count = len(result.data or [])
    record_activity(actor["id"], "admin_bulk_groups_deleted", "group", request=request,
                    details={"deleted": count})
    return {"deleted": count}




def list_activity(action: str | None, actor_id: str | None, search: str | None,
                  page: int, page_size: int) -> dict[str, Any]:
    result = admin_repo.list_activity(action, actor_id, search, page, page_size)

    return {
        "items": result.data or [],
        "total": result.count or 0,
        "page": page,
        "page_size": page_size,
    }


def list_security(event_type: str | None, ip_address: str | None, email: str | None,
                  page: int, page_size: int) -> dict[str, Any]:
    result = admin_repo.list_security(
        event_type, ip_address, email, page, page_size
    )

    items = result.data or []
    by_ip: dict[str, int] = {}
    by_email: dict[str, int] = {}

    for item in items:
        if item.get("ip_address"):
            by_ip[item["ip_address"]] = by_ip.get(item["ip_address"], 0) + 1

        if item.get("email"):
            by_email[item["email"]] = by_email.get(item["email"], 0) + 1

    return {
        "items": items,
        "total": result.count or 0,
        "by_ip": by_ip,
        "by_email": by_email,
        "page": page,
        "page_size": page_size,
    }


def delete_request(request_id: int, actor: CurrentUser, request) -> None:
    result = admin_repo.delete_request(request_id)
    if not result.data:
        raise HTTPException(status_code=404, detail="Request not found.")
    record_activity(actor["id"], "admin_request_deleted", "request", request_id, request)


def delete_group(group_id: str, actor: CurrentUser, request) -> None:
    result = admin_repo.delete_group(group_id)
    if not result.data:
        raise HTTPException(status_code=404, detail="Group not found.")
    record_activity(actor["id"], "admin_group_deleted", "group", group_id, request)


def _escape_csv_cell(value: Any) -> str:
    cell = "" if value is None else str(value)
    if cell.startswith(("=", "+", "-", "@")):
        return "'" + cell
    return cell


def export_csv(kind: str, filters: dict[str, str | None] | None = None) -> str:
    filters = filters or {}
    allowed = {
        "users": ("profiles", "id,email,full_name,role,is_banned,ban_reason,created_at"),
        "requests": ("service_requests", "*"),
        "groups": ("groups", "*"),
        "activity": ("activity_logs", "*"),
    }
    if kind not in allowed:
        raise HTTPException(status_code=404, detail="Unknown export type.")
    table, columns = allowed[kind]
    result = admin_repo.export_rows(kind, table, columns, filters)
    rows = result.data or []
    fields = list(rows[0].keys()) if rows else (columns.split(",") if columns != "*" else ["id"])
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: _escape_csv_cell(value) for key, value in row.items()})
    return "\ufeff" + buffer.getvalue()




def purge_activity(older_than_days: int, actor: CurrentUser, request) -> int:
    if older_than_days < 30 or older_than_days > 3650:
        raise HTTPException(status_code=422, detail="Retention must be between 30 and 3650 days.")
    cutoff = (datetime.now(timezone.utc) - timedelta(days=older_than_days)).isoformat()
    result = admin_repo.purge_activity(cutoff)
    deleted = len(result.data or [])
    record_activity(actor["id"], "activity_purged", "activity", request=request,
                    details={"deleted": deleted, "older_than_days": older_than_days})
    return deleted





def revoke_user_session(user_id: str, session_id: str, actor: CurrentUser, request) -> None:
    result = admin_repo.revoke_user_session(
        user_id, session_id, datetime.now(timezone.utc).isoformat()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Active session not found.")
    record_activity(actor["id"], "admin_session_revoked", "session", session_id, request,
                    {"target_user_id": user_id})
