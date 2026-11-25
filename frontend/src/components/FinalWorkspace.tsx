import { useEffect, useState, type FormEvent } from "react";
import type { AppPage, AppSession, CampusGroup, Category, GroupMember, Profile, RequestStatus, ServiceRequest, Session } from "../types";
import { apiRequest, downloadCsv } from "../services/api";

interface FinalWorkspaceProps {
  page: AppPage;
  profile: Profile;
  session: Session;
  onSignOut: () => void;
}
type AdminUser = { id: string; email: string; full_name: string; role: string; is_banned: boolean; ban_reason?: string | null };
type AuditEntry = { id: number; actor_id: string | null; action: string; entity_type: string; entity_id: string | null; ip_address: string | null; user_agent: string | null; created_at: string };
type SecurityEntry = { id: number; event_type: string; email: string | null; ip_address: string | null; user_agent: string | null; created_at: string };

const categories: Category[] = ["IT Support", "Classroom", "Facilities", "Library", "Other"];
const statuses: RequestStatus[] = ["Pending", "In Progress", "Resolved", "Rejected"];

export default function FinalWorkspace({ page, profile, session, onSignOut }: FinalWorkspaceProps) {
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  // Profile and sessions
  const [fullName, setFullName] = useState(profile.full_name || "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [sessions, setSessions] = useState<AppSession[]>([]);

  // Groups
  const [groups, setGroups] = useState<CampusGroup[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<CampusGroup | null>(null);
  const [members, setMembers] = useState<GroupMember[]>([]);
  const [groupRequests, setGroupRequests] = useState<ServiceRequest[]>([]);
  const [groupName, setGroupName] = useState("");
  const [groupDescription, setGroupDescription] = useState("");
  const [memberEmail, setMemberEmail] = useState("");
  const [permissions, setPermissions] = useState({ can_create_requests: false, can_edit_requests: false, can_assign_requests: false });
  const [requestTitle, setRequestTitle] = useState("");
  const [requestDescription, setRequestDescription] = useState("");
  const [requestCategory, setRequestCategory] = useState<Category>("Other");

  // Admin
  const [adminTab, setAdminTab] = useState<"users" | "content" | "activity" | "security">("users");
  const [overview, setOverview] = useState<Record<string, number>>({});
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [userSearch, setUserSearch] = useState("");
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([]);
  const [userDetail, setUserDetail] = useState<any>(null);
  const [activity, setActivity] = useState<AuditEntry[]>([]);
  const [securityEvents, setSecurityEvents] = useState<SecurityEntry[]>([]);
  const [allRequests, setAllRequests] = useState<ServiceRequest[]>([]);
  const [allGroups, setAllGroups] = useState<CampusGroup[]>([]);
  const [moderationSearch, setModerationSearch] = useState("");

  async function loadGroups() {
    const rows = await apiRequest<CampusGroup[]>("/api/groups", session);
    setGroups(rows);
    if (selectedGroup && !rows.some(row => row.id === selectedGroup.id)) setSelectedGroup(null);
  }

  async function selectGroup(group: CampusGroup) {
    setSelectedGroup(group);
    setError("");
    try {
      const [memberRows, requestRows] = await Promise.all([
        apiRequest<GroupMember[]>(`/api/groups/${group.id}`, session),
        apiRequest<ServiceRequest[]>(`/api/groups/${group.id}/requests`, session),
      ]);
      setMembers(memberRows);
      setGroupRequests(requestRows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load group.");
    }
  }

  async function loadAdmin() {
    const [stats, userPage, activityPage, securityPage, requestRows, groupRows] = await Promise.all([
      apiRequest<Record<string, number>>("/api/admin/overview", session),
      apiRequest<{ items: AdminUser[] }>("/api/admin/users?page=1&page_size=100", session),
      apiRequest<{ items: AuditEntry[] }>("/api/admin/activity?page=1&page_size=50", session),
      apiRequest<{ items: SecurityEntry[] }>("/api/admin/security?page=1&page_size=50", session),
      apiRequest<ServiceRequest[]>("/api/admin/requests?page=1&page_size=100", session),
      apiRequest<CampusGroup[]>("/api/admin/groups?page=1&page_size=100", session),
    ]);
    setOverview(stats);
    setUsers(userPage.items || []);
    setActivity(activityPage.items || []);
    setSecurityEvents(securityPage.items || []);
    setAllRequests(requestRows);
    setAllGroups(groupRows);
  }

  useEffect(() => {
    setError("");
    setNotice("");
    if (page === "profile") {
      apiRequest<AppSession[]>("/api/auth/sessions", session).then(setSessions)
        .catch(err => setError(err instanceof Error ? err.message : "Could not load sessions."));
    }
    if (page === "groups") {
      loadGroups().catch(err => setError(err instanceof Error ? err.message : "Could not load groups."));
    }
    if (page === "admin" && profile.role === "admin") {
      loadAdmin().catch(err => setError(err instanceof Error ? err.message : "Could not load admin dashboard."));
    }
    // Data loads when the user navigates to a workspace section.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(""); setNotice("");
    try {
      await apiRequest("/api/me", session, { method: "PATCH", body: JSON.stringify({ full_name: fullName }) });
      setNotice("Profile updated successfully.");
    } catch (err) { setError(err instanceof Error ? err.message : "Profile update failed."); }
  }

  async function savePassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(""); setNotice("");
    try {
      await apiRequest("/api/me/password", session, { method: "POST", body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }) });
      setNotice("Password changed. Please sign in again.");
      setCurrentPassword(""); setNewPassword("");
      onSignOut();
    } catch (err) { setError(err instanceof Error ? err.message : "Password update failed."); }
  }

  async function revokeSession(id: string) {
    setError("");
    try {
      await apiRequest(`/api/auth/sessions/${id}`, session, { method: "DELETE" });
      setSessions(current => current.map(item => item.id === id ? { ...item, revoked_at: new Date().toISOString() } : item));
      if (id === session.session_id) onSignOut();
      setNotice("Session revoked.");
    } catch (err) { setError(err instanceof Error ? err.message : "Could not revoke session."); }
  }

  async function revokeOthers() {
    setError("");
    try {
      const result = await apiRequest<{ revoked: number }>("/api/auth/sessions/revoke-others", session, { method: "POST" });
      setNotice(`${result.revoked} other session(s) revoked.`);
      const rows = await apiRequest<AppSession[]>("/api/auth/sessions", session);
      setSessions(rows);
    } catch (err) { setError(err instanceof Error ? err.message : "Could not revoke sessions."); }
  }

  async function createGroup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setNotice("");
    try {
      await apiRequest("/api/groups", session, { method: "POST", body: JSON.stringify({ name: groupName, description: groupDescription }) });
      setGroupName(""); setGroupDescription("");
      await loadGroups();
      setNotice("Group created successfully.");
    } catch (err) { setError(err instanceof Error ? err.message : "Group creation failed."); }
  }

  async function addMember(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedGroup) return;
    setError(""); setNotice("");
    try {
      await apiRequest(`/api/groups/${selectedGroup.id}/members`, session, {
        method: "POST", body: JSON.stringify({ email: memberEmail, ...permissions }),
      });
      setMemberEmail("");
      await selectGroup(selectedGroup);
      setNotice("Member permissions saved.");
    } catch (err) { setError(err instanceof Error ? err.message : "Could not add group member."); }
  }

  async function createGroupRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedGroup) return;
    setError(""); setNotice("");
    try {
      await apiRequest(`/api/groups/${selectedGroup.id}/requests`, session, {
        method: "POST", body: JSON.stringify({ title: requestTitle, description: requestDescription, category: requestCategory }),
      });
      setRequestTitle(""); setRequestDescription("");
      await selectGroup(selectedGroup);
      setNotice("Shared request created.");
    } catch (err) { setError(err instanceof Error ? err.message : "Could not create shared request."); }
  }

  async function adminRefresh() {
    try { await loadAdmin(); } catch (err) { setError(err instanceof Error ? err.message : "Refresh failed."); }
  }

  async function changeUserRole(userId: string, role: string) {
    setError(""); setNotice("");
    try {
      await apiRequest(`/api/admin/users/${userId}/role`, session, { method: "PATCH", body: JSON.stringify({ role }) });
      await adminRefresh(); setNotice("User role updated.");
    } catch (err) { setError(err instanceof Error ? err.message : "Role update failed."); }
  }

  async function toggleBan(user: AdminUser) {
    const reason = user.is_banned ? "" : window.prompt("Reason for banning this user:");
    if (!user.is_banned && !reason) return;
    setError(""); setNotice("");
    try {
      await apiRequest(`/api/admin/users/${user.id}/${user.is_banned ? "unban" : "ban"}`, session, {
        method: "POST", ...(user.is_banned ? {} : { body: JSON.stringify({ reason }) }),
      });
      await adminRefresh(); setNotice(user.is_banned ? "User unbanned." : "User banned and sessions revoked.");
    } catch (err) { setError(err instanceof Error ? err.message : "User action failed."); }
  }

  async function bulkUsers(action: "ban" | "unban") {
    if (!selectedUserIds.length) return;
    const reason = action === "ban" ? window.prompt("Reason for bulk ban:") : "";
    if (action === "ban" && !reason) return;
    try {
      const path = action === "ban" ? "bulk-ban" : "bulk-unban";
      await apiRequest(`/api/admin/users/${path}`, session, {
        method: "POST", body: JSON.stringify({ user_ids: selectedUserIds, reason: reason || "Bulk unban" }),
      });
      setSelectedUserIds([]); await adminRefresh(); setNotice("Bulk action completed.");
    } catch (err) { setError(err instanceof Error ? err.message : "Bulk action failed."); }
  }

  async function showUser(userId: string) {
    try { setUserDetail(await apiRequest(`/api/admin/users/${userId}`, session)); }
    catch (err) { setError(err instanceof Error ? err.message : "Could not load user details."); }
  }

  async function exportData(kind: string) {
    try { await downloadCsv(session, kind); }
    catch (err) { setError(err instanceof Error ? err.message : "CSV export failed."); }
  }

  async function moderateDelete(kind: "requests" | "groups", id: string | number) {
    if (!window.confirm(`Permanently delete this ${kind === "requests" ? "request" : "group"}?`)) return;
    try {
      const path = kind === "requests" ? `/api/admin/requests/${id}` : `/api/admin/groups/${id}`;
      await apiRequest(path, session, { method: "DELETE" });
      await adminRefresh(); setNotice("Content deleted.");
    } catch (err) { setError(err instanceof Error ? err.message : "Delete failed."); }
  }

  const filteredUsers = users.filter(user => `${user.email} ${user.full_name}`.toLowerCase().includes(userSearch.toLowerCase()));
  const filteredRequests = allRequests.filter(item => `${item.title} ${item.category} ${item.status}`.toLowerCase().includes(moderationSearch.toLowerCase()));
  const filteredGroups = allGroups.filter(item => `${item.name} ${item.description}`.toLowerCase().includes(moderationSearch.toLowerCase()));

  return (
    <section className="panel final-workspace">
      <div className="panel-heading">
        <div>
          <h2>{page === "profile" ? "Profile & Sessions" : page === "groups" ? "Groups & Shared Requests" : "Administrator Dashboard"}</h2>
          <p>{page === "profile" ? "Manage your account and active devices." : page === "groups" ? "Create groups and manage shared request permissions." : "Manage users, content, activity and security."}</p>
        </div>
      </div>
      {error && <div className="alert alert-error" role="alert">{error}</div>}
      {notice && <div className="alert alert-success" role="status">{notice}</div>}

      {page === "profile" && (
        <div className="final-grid">
          <form className="final-card" onSubmit={saveProfile}>
            <h3>Update profile</h3>
            <label htmlFor="profile-name">Full name</label>
            <input id="profile-name" value={fullName} onChange={e => setFullName(e.target.value)} minLength={2} maxLength={100} required />
            <label>Email</label><input value={profile.email} disabled />
            <button className="primary-button" type="submit">Save profile</button>
          </form>
          <form className="final-card" onSubmit={savePassword}>
            <h3>Change password</h3>
            <label htmlFor="current-password">Current password</label>
            <input id="current-password" type="password" value={currentPassword} onChange={e => setCurrentPassword(e.target.value)} required />
            <label htmlFor="new-password">New password</label>
            <input id="new-password" type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} minLength={10} required />
            <small>Use at least 10 characters with uppercase, lowercase and a number.</small>
            <button className="primary-button" type="submit">Change password</button>
          </form>
          <div className="final-card final-wide">
            <div className="panel-heading"><div><h3>Signed-in devices</h3><p>Revoke this device or other sessions.</p></div><button className="secondary-button" type="button" onClick={() => void revokeOthers()}>Sign out other devices</button></div>
            {sessions.length === 0 ? <p>No session records found.</p> : sessions.map(item => (
              <div className="final-row" key={item.id}>
                <div><strong>{item.device_name || "Browser"}</strong><small>{item.ip_address || "IP unavailable"} · Last active {new Date(item.last_seen_at).toLocaleString()}</small><small>{item.revoked_at ? "Revoked" : item.id === session.session_id ? "Current device" : "Active"}</small></div>
                {!item.revoked_at && <button className="danger-button" type="button" onClick={() => void revokeSession(item.id)}>Revoke</button>}
              </div>
            ))}
          </div>
        </div>
      )}

      {page === "groups" && (
        <div className="final-grid">
          <form className="final-card" onSubmit={createGroup}>
            <h3>Create a group</h3>
            <label htmlFor="group-name">Group name</label>
            <input id="group-name" value={groupName} onChange={e => setGroupName(e.target.value)} minLength={2} maxLength={100} required />
            <label htmlFor="group-description">Description</label>
            <textarea id="group-description" value={groupDescription} onChange={e => setGroupDescription(e.target.value)} maxLength={1000} rows={3} />
            <button className="primary-button" type="submit">Create group</button>
          </form>
          <div className="final-card">
            <h3>Your groups</h3>
            {groups.length === 0 ? <p>No groups yet. Create one to share requests.</p> : groups.map(group => (
              <button className={`group-choice ${selectedGroup?.id === group.id ? "active" : ""}`} key={group.id} type="button" onClick={() => void selectGroup(group)}>
                <strong>{group.name}</strong><small>{group.description}</small>
              </button>
            ))}
          </div>
          {selectedGroup && (
            <div className="final-card final-wide">
              <h3>{selectedGroup.name}</h3>
              <p>{selectedGroup.description}</p>
              <h4>Members and permissions</h4>
              {members.map(member => (
                <div className="final-row" key={member.id}>
                  <div><strong>{member.user_id}</strong><small>{[
                    member.can_create_requests && "Create",
                    member.can_edit_requests && "Edit",
                    member.can_assign_requests && "Assign",
                  ].filter(Boolean).join(" · ") || "Read only"}</small></div>
                </div>
              ))}
              {selectedGroup.owner_id === profile.id && (
                <form className="final-card inner-card" onSubmit={addMember}>
                  <h4>Add member or update permissions</h4>
                  <label htmlFor="member-email">Registered member email</label>
                  <input id="member-email" type="email" value={memberEmail} onChange={e => setMemberEmail(e.target.value)} required />
                  <label className="check-line"><input type="checkbox" checked={permissions.can_create_requests} onChange={e => setPermissions(p => ({...p, can_create_requests:e.target.checked}))}/> Can create requests</label>
                  <label className="check-line"><input type="checkbox" checked={permissions.can_edit_requests} onChange={e => setPermissions(p => ({...p, can_edit_requests:e.target.checked}))}/> Can edit requests</label>
                  <label className="check-line"><input type="checkbox" checked={permissions.can_assign_requests} onChange={e => setPermissions(p => ({...p, can_assign_requests:e.target.checked}))}/> Can assign requests</label>
                  <button className="primary-button" type="submit">Save member permissions</button>
                </form>
              )}
              <h4>Shared requests</h4>
              {groupRequests.map(item => <div className="final-row" key={item.id}><div><strong>#{item.id} {item.title}</strong><small>{item.category} · {item.status}</small><small>{item.description}</small></div></div>)}
              <form className="final-card inner-card" onSubmit={createGroupRequest}>
                <h4>Create shared request</h4>
                <label htmlFor="shared-title">Title</label><input id="shared-title" value={requestTitle} onChange={e => setRequestTitle(e.target.value)} minLength={3} required />
                <label htmlFor="shared-description">Description</label><textarea id="shared-description" value={requestDescription} onChange={e => setRequestDescription(e.target.value)} minLength={5} required />
                <label htmlFor="shared-category">Category</label><select id="shared-category" value={requestCategory} onChange={e => setRequestCategory(e.target.value as Category)}>{categories.map(x => <option key={x}>{x}</option>)}</select>
                <button className="primary-button" type="submit">Submit shared request</button>
              </form>
            </div>
          )}
        </div>
      )}

      {page === "admin" && profile.role === "admin" && (
        <>
          <div className="admin-stats">
            {Object.entries(overview).map(([key,value]) => <div className="stat-card" key={key}><small>{key.replaceAll("_"," ")}</small><strong>{value}</strong></div>)}
          </div>
          <div className="admin-tabs">
            {(["users","content","activity","security"] as const).map(tab => <button key={tab} type="button" className={adminTab===tab?"active":""} onClick={()=>setAdminTab(tab)}>{tab}</button>)}
          </div>
          <div className="final-toolbar">
            <button className="secondary-button" type="button" onClick={() => void adminRefresh()}>Refresh data</button>
            {(["users","requests","groups","activity"] as const).map(kind => <button className="secondary-button" type="button" key={kind} onClick={() => void exportData(kind)}>Export {kind} CSV</button>)}
          </div>
          {adminTab === "users" && (
            <div className="final-card">
              <div className="final-toolbar"><input aria-label="Search users" placeholder="Search users by name or email" value={userSearch} onChange={e=>setUserSearch(e.target.value)}/><button className="secondary-button" type="button" onClick={()=>void bulkUsers("ban")} disabled={!selectedUserIds.length}>Bulk ban</button><button className="secondary-button" type="button" onClick={()=>void bulkUsers("unban")} disabled={!selectedUserIds.length}>Bulk unban</button></div>
              <div className="table-scroll"><table className="final-table"><thead><tr><th>Select</th><th>User</th><th>Role</th><th>Status</th><th>Actions</th></tr></thead><tbody>
                {filteredUsers.map(user=><tr key={user.id}>
                  <td><input type="checkbox" checked={selectedUserIds.includes(user.id)} onChange={e=>setSelectedUserIds(ids=>e.target.checked?[...ids,user.id]:ids.filter(id=>id!==user.id))}/></td>
                  <td><button className="text-button" type="button" onClick={()=>void showUser(user.id)}>{user.full_name || user.email}</button><small>{user.email}</small></td>
                  <td><select value={user.role} onChange={e=>void changeUserRole(user.id,e.target.value)} disabled={user.role==="admin" || user.id===profile.id}><option value="student">Student</option><option value="staff">Staff</option><option value="admin">Admin</option></select></td>
                  <td>{user.is_banned?"Banned":"Active"}</td>
                  <td><button className={user.is_banned?"secondary-button":"danger-button"} type="button" disabled={user.role==="admin" || user.id===profile.id} onClick={()=>void toggleBan(user)}>{user.is_banned?"Unban":"Ban"}</button></td>
                </tr>)}
              </tbody></table></div>
              {userDetail && <div className="final-card inner-card"><div className="panel-heading"><h3>User detail</h3><button type="button" className="secondary-button" onClick={()=>setUserDetail(null)}>Close</button></div><pre>{JSON.stringify(userDetail,null,2)}</pre></div>}
            </div>
          )}
          {adminTab === "content" && (
            <div className="final-card">
              <input aria-label="Search content" placeholder="Search requests and groups" value={moderationSearch} onChange={e=>setModerationSearch(e.target.value)}/>
              <h3>Service requests</h3>
              {filteredRequests.map(item=><div className="final-row" key={item.id}><div><strong>#{item.id} {item.title}</strong><small>{item.category} · {item.status}</small></div><button className="danger-button" type="button" onClick={()=>void moderateDelete("requests",item.id)}>Delete</button></div>)}
              <h3>Groups</h3>
              {filteredGroups.map(group=><div className="final-row" key={group.id}><div><strong>{group.name}</strong><small>{group.description}</small></div><button className="danger-button" type="button" onClick={()=>void moderateDelete("groups",group.id)}>Delete</button></div>)}
            </div>
          )}
          {adminTab === "activity" && <div className="final-card"><h3>Audit activity</h3>{activity.map(item=><div className="final-row" key={item.id}><div><strong>{item.action}</strong><small>{item.entity_type} {item.entity_id || ""} · {item.actor_id || "System"}</small><small>{item.ip_address || "IP unavailable"} · {item.user_agent || "Browser unavailable"}</small><small>{new Date(item.created_at).toLocaleString()}</small></div></div>)}</div>}
          {adminTab === "security" && <div className="final-card"><h3>Security events</h3>{securityEvents.map(item=><div className="final-row" key={item.id}><div><strong>{item.event_type}</strong><small>{item.email || "Unknown account"} · {item.ip_address || "IP unavailable"}</small><small>{item.user_agent || "Browser unavailable"} · {new Date(item.created_at).toLocaleString()}</small></div></div>)}</div>}
        </>
      )}
    </section>
  );
}
