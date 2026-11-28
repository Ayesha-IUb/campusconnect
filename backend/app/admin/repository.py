"""Database operations for the Admin feature."""

from app.core.database import execute_query, get_database


def get_overview_data() -> dict:
    db = get_database()

    users = execute_query(
        db.table("profiles").select("id,is_banned,created_at")
    ).data or []

    requests = execute_query(
        db.table("service_requests").select("id,created_at")
    ).data or []

    groups = execute_query(
        db.table("groups").select("id,created_at")
    ).data or []

    return {
        "users": users,
        "requests": requests,
        "groups": groups,
    }


def list_users(search, role, banned, page, page_size):
    query = get_database().table("profiles").select(
        "id,email,full_name,role,is_banned,ban_reason,banned_at,created_at",
        count="exact",
    ).order("created_at", desc=True)

    if role:
        query = query.eq("role", role)

    if banned is not None:
        query = query.eq("is_banned", banned)

    if search:
        term = "".join(
            ch for ch in search if ch.isalnum() or ch in "@._- "
        )[:80].strip()

        if term:
            query = query.or_(
                f"email.ilike.%{term}%,full_name.ilike.%{term}%"
            )

    result = execute_query(
        query.range((page - 1) * page_size, page * page_size - 1)
    )

    return {
        "items": result.data or [],
        "total": result.count or 0,
    }


def get_user_detail_data(user_id):
    db = get_database()

    profile = execute_query(
        db.table("profiles").select(
            "id,email,full_name,role,is_banned,ban_reason,banned_at,created_at"
        ).eq("id", user_id).limit(1)
    )

    if not profile.data:
        return None

    return {
        "profile": profile.data[0],
        "requests": execute_query(
            db.table("service_requests").select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
        ).data or [],
        "groups": {
            "owned": execute_query(
                db.table("groups").select(
                    "id,name,description,created_at"
                ).eq("owner_id", user_id)
            ).data or [],
            "member_of": execute_query(
                db.table("group_members").select(
                    "group_id,created_at,can_create_requests,"
                    "can_edit_requests,can_assign_requests"
                ).eq("user_id", user_id)
            ).data or [],
        },
        "sessions": execute_query(
            db.table("app_sessions").select(
                "id,device_name,ip_address,created_at,last_seen_at,"
                "expires_at,revoked_at"
            ).eq("user_id", user_id)
            .order("created_at", desc=True)
        ).data or [],
        "activity": execute_query(
            db.table("activity_logs").select("*")
            .eq("actor_id", user_id)
            .order("created_at", desc=True)
            .limit(20)
        ).data or [],
    }


def list_requests(search, status, page, page_size):
    query = get_database().table("service_requests").select(
        "*", count="exact"
    ).order("created_at", desc=True)

    if status:
        query = query.eq("status", status)

    if search:
        term = "".join(
            ch for ch in search if ch.isalnum() or ch in " -_"
        )[:80].strip()

        if term:
            query = query.ilike("title", f"%{term}%")

    result = execute_query(
        query.range((page - 1) * page_size, page * page_size - 1)
    )

    return {"items": result.data or [], "total": result.count or 0}


def list_groups(search, page, page_size):
    query = get_database().table("groups").select(
        "*", count="exact"
    ).order("created_at", desc=True)

    if search:
        term = "".join(
            ch for ch in search if ch.isalnum() or ch in " -_"
        )[:80].strip()

        if term:
            query = query.ilike("name", f"%{term}%")

    result = execute_query(
        query.range((page - 1) * page_size, page * page_size - 1)
    )

    return {"items": result.data or [], "total": result.count or 0}


def list_activity(action, actor_id, search, page, page_size):
    query = get_database().table("activity_logs").select(
        "*", count="exact"
    ).order("created_at", desc=True)

    if action:
        query = query.eq("action", action)

    if actor_id:
        query = query.eq("actor_id", actor_id)

    if search:
        term = "".join(
            ch for ch in search if ch.isalnum() or ch in " -_"
        )[:80].strip()

        if term:
            query = query.ilike("action", f"%{term}%")

    return execute_query(
        query.range((page - 1) * page_size, page * page_size - 1)
    )


def list_security(event_type, ip_address, email, page, page_size):
    query = get_database().table("security_events").select(
        "*", count="exact"
    ).order("created_at", desc=True)

    if event_type:
        query = query.eq("event_type", event_type)

    if ip_address:
        query = query.eq("ip_address", ip_address)

    if email:
        query = query.eq("email", email.strip().lower())

    return execute_query(
        query.range((page - 1) * page_size, page * page_size - 1)
    )


def delete_request(request_id):
    return execute_query(
        get_database().table("service_requests").delete()
        .eq("id", request_id).select("id")
    )


def delete_group(group_id):
    return execute_query(
        get_database().table("groups").delete()
        .eq("id", group_id).select("id")
    )

def get_user_role(user_id):
    result = execute_query(
        get_database().table("profiles").select("id,role")
        .eq("id", user_id).limit(1)
    )
    return result.data[0] if result.data else None


def update_user_role(user_id, role, updated_at):
    return execute_query(
        get_database().table("profiles").update({
            "role": role, "updated_at": updated_at,
        }).eq("id", user_id)
        .select("id,email,full_name,role,is_banned")
    )


def update_user_ban(user_id, values):
    return execute_query(
        get_database().table("profiles").update(values)
        .eq("id", user_id)
        .select("id,email,full_name,role,is_banned,ban_reason,banned_at")
    )


def revoke_active_sessions(user_id, revoked_at):
    return execute_query(
        get_database().table("app_sessions").update({
            "revoked_at": revoked_at,
        }).eq("user_id", user_id).is_("revoked_at", "null")
    )


def bulk_delete_requests(ids):
    return execute_query(
        get_database().table("service_requests").delete()
        .in_("id", list(set(ids))).select("id")
    )


def bulk_delete_groups(ids):
    return execute_query(
        get_database().table("groups").delete()
        .in_("id", list(set(ids))).select("id")
    )


def export_rows(kind, table, columns, filters):
    query = get_database().table(table).select(columns).limit(10000)

    if kind == "users":
        if filters.get("role"):
            query = query.eq("role", filters["role"])
        if filters.get("banned") in {"true", "false"}:
            query = query.eq("is_banned", filters["banned"] == "true")
        if filters.get("search"):
            term = "".join(
                ch for ch in filters["search"]
                if ch.isalnum() or ch in "@._- "
            )[:80].strip()
            if term:
                query = query.or_(
                    f"email.ilike.%{term}%,full_name.ilike.%{term}%"
                )
    elif kind == "requests":
        if filters.get("status"):
            query = query.eq("status", filters["status"])
        if filters.get("search"):
            query = query.ilike("title", f"%{filters['search'][:80]}%")
    elif kind == "activity" and filters.get("action"):
        query = query.eq("action", filters["action"])

    return execute_query(query)


def purge_activity(cutoff):
    return execute_query(
        get_database().table("activity_logs").delete()
        .lt("created_at", cutoff).select("id")
    )


def revoke_user_session(user_id, session_id, revoked_at):
    return execute_query(
        get_database().table("app_sessions").update({
            "revoked_at": revoked_at,
        }).eq("id", session_id).eq("user_id", user_id)
        .is_("revoked_at", "null").select("id")
    )
