"""Admin-only dashboard, moderation, audit and security endpoints."""
from fastapi import APIRouter, Depends, Query, Request, Response

from models import CurrentUser
from rbac import require_admin
from schemas import BanInput, BulkUserAction, BulkRequestDeleteInput, BulkDeleteInput, RoleChange
from services import admin_service

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/overview")
def overview(_: CurrentUser = Depends(require_admin)):
    return admin_service.overview()


@router.get("/users")
def users(search: str | None = None, role: str | None = None,
          banned: bool | None = None, page: int = Query(1, ge=1),
          page_size: int = Query(20, ge=1, le=100),
          _: CurrentUser = Depends(require_admin)):
    return admin_service.list_users(search, role, banned, page, page_size)


@router.get("/users/{user_id}")
def user_detail(user_id: str, _: CurrentUser = Depends(require_admin)):
    return admin_service.user_detail(user_id)


@router.patch("/users/{user_id}/role")
def change_role(user_id: str, payload: RoleChange, request: Request,
                admin: CurrentUser = Depends(require_admin)):
    return admin_service.change_role(user_id, payload.role, admin, request)


@router.post("/users/{user_id}/ban")
def ban_user(user_id: str, payload: BanInput, request: Request,
             admin: CurrentUser = Depends(require_admin)):
    return admin_service.set_banned(user_id, True, payload.reason, admin, request)


@router.post("/users/{user_id}/unban")
def unban_user(user_id: str, request: Request,
               admin: CurrentUser = Depends(require_admin)):
    return admin_service.set_banned(user_id, False, None, admin, request)


@router.post("/users/bulk-ban")
def bulk_ban(payload: BulkUserAction, request: Request,
             admin: CurrentUser = Depends(require_admin)):
    return admin_service.bulk_ban(payload.user_ids, True, payload.reason, admin, request)


@router.post("/users/bulk-unban")
def bulk_unban(payload: BulkUserAction, request: Request,
               admin: CurrentUser = Depends(require_admin)):
    return admin_service.bulk_ban(payload.user_ids, False, "", admin, request)


@router.get("/requests")
def requests(search: str | None = None, status: str | None = None,
             page: int = Query(1, ge=1), page_size: int = Query(100, ge=1, le=100),
             _: CurrentUser = Depends(require_admin)):
    return admin_service.list_requests(search, status, page, page_size)["items"]


@router.get("/groups")
def groups(search: str | None = None, page: int = Query(1, ge=1),
           page_size: int = Query(100, ge=1, le=100),
           _: CurrentUser = Depends(require_admin)):
    return admin_service.list_groups(search, page, page_size)["items"]


@router.post("/requests/bulk-delete")
def bulk_delete_requests(payload: BulkRequestDeleteInput, request: Request,
                         admin: CurrentUser = Depends(require_admin)):
    return admin_service.bulk_delete_requests(payload.ids, admin, request)


@router.post("/groups/bulk-delete")
def bulk_delete_groups(payload: BulkDeleteInput, request: Request,
                       admin: CurrentUser = Depends(require_admin)):
    return admin_service.bulk_delete_groups(payload.ids, admin, request)


@router.get("/activity")
def activity(action: str | None = None, actor_id: str | None = None,
             search: str | None = None, page: int = Query(1, ge=1),
             page_size: int = Query(50, ge=1, le=100),
             _: CurrentUser = Depends(require_admin)):
    return admin_service.list_activity(action, actor_id, search, page, page_size)


@router.get("/security")
def security(event_type: str | None = None, ip_address: str | None = None,
             email: str | None = None, page: int = Query(1, ge=1),
             page_size: int = Query(50, ge=1, le=100),
             _: CurrentUser = Depends(require_admin)):
    return admin_service.list_security(event_type, ip_address, email, page, page_size)


@router.get("/export/{kind}")
def export(kind: str, search: str | None = None, role: str | None = None,
           banned: str | None = None, status: str | None = None, action: str | None = None,
           _: CurrentUser = Depends(require_admin)):
    csv_text = admin_service.export_csv(kind, {
        "search": search, "role": role, "banned": banned, "status": status, "action": action,
    })
    return Response(content=csv_text, media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="campusconnect-{kind}.csv"'})


@router.delete("/requests/{request_id}")
def delete_request(request_id: int, request: Request,
                   admin: CurrentUser = Depends(require_admin)):
    admin_service.delete_request(request_id, admin, request)
    return {"message": "Request deleted."}


@router.delete("/groups/{group_id}")
def delete_group(group_id: str, request: Request,
                 admin: CurrentUser = Depends(require_admin)):
    admin_service.delete_group(group_id, admin, request)
    return {"message": "Group deleted."}


@router.delete("/activity")
def purge_activity(request: Request, older_than_days: int = Query(90, ge=30, le=3650),
                   admin: CurrentUser = Depends(require_admin)):
    deleted = admin_service.purge_activity(older_than_days, admin, request)
    return {"deleted": deleted}
