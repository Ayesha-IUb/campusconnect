"""Admin reporting, moderation, audit logs and safe CSV export."""
import csv
import io
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException

from database import execute_query, get_database
from models import CurrentUser
from services.activity_service import record_activity


def overview() -> dict[str, int]:
    db = get_database()
    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    users = execute_query(db.table("profiles").select("id,is_banned,created_at")).data or []
    requests = execute_query(db.table("service_requests").select("id,created_at")).data or []
    groups = execute_query(db.table("groups").select("id,created_at")).data or []
    return {
        "users": len(users),
        "banned_users": sum(bool(row.get("is_banned")) for row in users),
        "requests": len(requests),
        "groups": len(groups),
        "new_users_7d": sum(row.get("created_at", "") >= since for row in users),
        "new_requests_7d": sum(row.get("created_at", "") >= since for row in requests),
    }


def list_users(search: str | None, role: str | None, banned: bool | None,
               page: int, page_size: int) -> dict[str, Any]:
    query = get_database().table("profiles").select(
        "id,email,full_name,role,is_banned,ban_reason,banned_at,created_at", count="exact"
    ).order("created_at", desc=True)
    if role:
        query = query.eq("role", role)
    if banned is not None:
        query = query.eq("is_banned", banned)
    if search:
        term = "".join(ch for ch in search if ch.isalnum() or ch in "@._- ")[:80].strip()
        if term:
            query = query.or_(f"email.ilike.%{term}%,full_name.ilike.%{term}%")
    result = execute_query(query.range((page - 1) * page_size, page * page_size - 1))
    return {"items": result.data or [], "total": result.count or 0, "page": page, "page_size": page_size}


def user_detail(user_id: str) -> dict[str, Any]:
    db = get_database()
    profile = execute_query(db.table("profiles").select(
        "id,email,full_name,role,is_banned,ban_reason,banned_at,created_at"
    ).eq("id", user_id).limit(1))
    if not profile.data:
        raise HTTPException(status_code=404, detail="User not found.")
    return {
        "profile": profile.data[0],
        "requests": execute_query(db.table("service_requests").select("*")
            .eq("user_id", user_id).order("created_at", desc=True)).data or [],
        "groups": execute_query(db.table("group_members").select("group_id,created_at")
            .eq("user_id", user_id)).data or [],
        "sessions": execute_query(db.table("app_sessions").select(
            "id,device_name,ip_address,created_at,last_seen_at,expires_at,revoked_at"
        ).eq("user_id", user_id).order("created_at", desc=True)).data or [],
        "activity": execute_query(db.table("activity_logs").select("*")
            .eq("actor_id", user_id).order("created_at", desc=True).limit(20)).data or [],
    }


def change_role(target_id: str, role: str, actor: CurrentUser, request) -> dict[str, Any]:
    if target_id == actor["id"]:
        raise HTTPException(status_code=403, detail="An administrator cannot change their own role.")
    if role not in {"student", "staff", "admin"}:
        raise HTTPException(status_code=422, detail="Invalid role.")
    db = get_database()
    target = execute_query(db.table("profiles").select("id,role").eq("id", target_id).limit(1))
    if not target.data:
        raise HTTPException(status_code=404, detail="User not found.")
    if target.data[0]["role"] == "admin":
        raise HTTPException(status_code=403, detail="An administrator cannot change another administrator's role.")
    result = execute_query(db.table("profiles").update({
        "role": role, "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", target_id).select("id,email,full_name,role,is_banned"))
    record_activity(actor["id"], "user_role_changed", "user", target_id, request, {"role": role})
    return result.data[0]


def set_banned(target_id: str, banned: bool, reason: str | None,
               actor: CurrentUser, request) -> dict[str, Any]:
    if target_id == actor["id"]:
        raise HTTPException(status_code=403, detail="An administrator cannot ban their own account.")
    db = get_database()
    target = execute_query(db.table("profiles").select("id,role").eq("id", target_id).limit(1))
    if not target.data:
        raise HTTPException(status_code=404, detail="User not found.")
    if target.data[0]["role"] == "admin":
        raise HTTPException(status_code=403, detail="An administrator cannot ban another administrator.")
    values = {
        "is_banned": banned,
        "ban_reason": (reason or "").strip() if banned else None,
        "banned_at": datetime.now(timezone.utc).isoformat() if banned else None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    result = execute_query(db.table("profiles").update(values).eq("id", target_id)
        .select("id,email,full_name,role,is_banned,ban_reason,banned_at"))
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found.")
    if banned:
        execute_query(db.table("app_sessions").update({
            "revoked_at": datetime.now(timezone.utc).isoformat(),
        }).eq("user_id", target_id).is_("revoked_at", "null"))
    record_activity(actor["id"], "user_banned" if banned else "user_unbanned",
                    "user", target_id, request, {"reason": reason or ""})
    return result.data[0]


def bulk_ban(user_ids: list[str], banned: bool, reason: str,
             actor: CurrentUser, request) -> dict[str, int]:
    changed = 0
    for user_id in dict.fromkeys(user_ids):
        if user_id == actor["id"]:
            continue
        target = execute_query(get_database().table("profiles").select("role")
            .eq("id", user_id).limit(1))
        if not target.data or target.data[0]["role"] == "admin":
            continue
        set_banned(user_id, banned, reason if banned else None, actor, request)
        changed += 1
    return {"updated": changed}


def list_requests(search: str | None, status: str | None, page: int, page_size: int) -> dict[str, Any]:
    query = get_database().table("service_requests").select("*", count="exact").order("created_at", desc=True)
    if status:
        query = query.eq("status", status)
    if search:
        term = "".join(ch for ch in search if ch.isalnum() or ch in " -_")[:80].strip()
        if term:
            query = query.ilike("title", f"%{term}%")
    result = execute_query(query.range((page - 1) * page_size, page * page_size - 1))
    return {"items": result.data or [], "total": result.count or 0}


def list_groups(search: str | None, page: int, page_size: int) -> dict[str, Any]:
    query = get_database().table("groups").select("*", count="exact").order("created_at", desc=True)
    if search:
        term = "".join(ch for ch in search if ch.isalnum() or ch in " -_")[:80].strip()
        if term:
            query = query.ilike("name", f"%{term}%")
    result = execute_query(query.range((page - 1) * page_size, page * page_size - 1))
    return {"items": result.data or [], "total": result.count or 0}


def bulk_delete_requests(ids: list[int], actor: CurrentUser, request) -> dict[str, int]:
    result = execute_query(get_database().table("service_requests").delete().in_("id", list(set(ids))).select("id"))
    count = len(result.data or [])
    record_activity(actor["id"], "admin_bulk_requests_deleted", "request", request=request,
                    details={"deleted": count})
    return {"deleted": count}


def bulk_delete_groups(ids: list[str], actor: CurrentUser, request) -> dict[str, int]:
    result = execute_query(get_database().table("groups").delete().in_("id", list(set(ids))).select("id"))
    count = len(result.data or [])
    record_activity(actor["id"], "admin_bulk_groups_deleted", "group", request=request,
                    details={"deleted": count})
    return {"deleted": count}


def list_activity(action: str | None, actor_id: str | None, search: str | None,
                  page: int, page_size: int) -> dict[str, Any]:
    query = get_database().table("activity_logs").select("*", count="exact").order("created_at", desc=True)
    if action:
        query = query.eq("action", action)
    if actor_id:
        query = query.eq("actor_id", actor_id)
    if search:
        term = "".join(ch for ch in search if ch.isalnum() or ch in " -_")[:80].strip()
        if term:
            query = query.ilike("action", f"%{term}%")
    result = execute_query(query.range((page - 1) * page_size, page * page_size - 1))
    return {"items": result.data or [], "total": result.count or 0, "page": page, "page_size": page_size}


def list_security(event_type: str | None, ip_address: str | None, email: str | None,
                  page: int, page_size: int) -> dict[str, Any]:
    query = get_database().table("security_events").select("*", count="exact").order("created_at", desc=True)
    if event_type:
        query = query.eq("event_type", event_type)
    if ip_address:
        query = query.eq("ip_address", ip_address)
    if email:
        query = query.eq("email", email.strip().lower())
    result = execute_query(query.range((page - 1) * page_size, page * page_size - 1))
    items = result.data or []
    by_ip: dict[str, int] = {}
    by_email: dict[str, int] = {}
    for item in items:
        if item.get("ip_address"):
            by_ip[item["ip_address"]] = by_ip.get(item["ip_address"], 0) + 1
        if item.get("email"):
            by_email[item["email"]] = by_email.get(item["email"], 0) + 1
    return {"items": items, "total": result.count or 0, "by_ip": by_ip, "by_email": by_email,
            "page": page, "page_size": page_size}


def delete_request(request_id: int, actor: CurrentUser, request) -> None:
    result = execute_query(get_database().table("service_requests").delete()
        .eq("id", request_id).select("id"))
    if not result.data:
        raise HTTPException(status_code=404, detail="Request not found.")
    record_activity(actor["id"], "admin_request_deleted", "request", request_id, request)


def delete_group(group_id: str, actor: CurrentUser, request) -> None:
    result = execute_query(get_database().table("groups").delete().eq("id", group_id).select("id"))
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
    query = get_database().table(table).select(columns).limit(10000)
    if kind == "users":
        if filters.get("role"):
            query = query.eq("role", filters["role"])
        if filters.get("banned") in {"true", "false"}:
            query = query.eq("is_banned", filters["banned"] == "true")
        if filters.get("search"):
            term = "".join(ch for ch in filters["search"] if ch.isalnum() or ch in "@._- ")[:80].strip()
            if term:
                query = query.or_(f"email.ilike.%{term}%,full_name.ilike.%{term}%")
    elif kind == "requests":
        if filters.get("status"):
            query = query.eq("status", filters["status"])
        if filters.get("search"):
            query = query.ilike("title", f"%{filters['search'][:80]}%")
    elif kind == "activity" and filters.get("action"):
        query = query.eq("action", filters["action"])
    result = execute_query(query)
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
    result = execute_query(get_database().table("activity_logs").delete()
        .lt("created_at", cutoff).select("id"))
    deleted = len(result.data or [])
    record_activity(actor["id"], "activity_purged", "activity", request=request,
                    details={"deleted": deleted, "older_than_days": older_than_days})
    return deleted
