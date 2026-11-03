
import { useEffect, useState, type FormEvent } from "react"

type Role = "student" | "staff" | "admin"
type Category = "IT Support" | "Classroom" | "Facilities" | "Library" | "Other"
type RequestStatus = "Pending" | "In Progress" | "Resolved" | "Rejected"

interface Session {
  access_token: string
  refresh_token: string
  user: { id: string; email: string }
}
interface Profile {
  id: string
  email: string
  full_name: string
  role: Role
}
interface ServiceRequest {
  id: number
  user_id: string | null
  title: string
  description: string
  category: Category
  status: RequestStatus
  created_at: string
  updated_at: string
}

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY
const categories: Category[] = ["IT Support", "Classroom", "Facilities", "Library", "Other"]
const statuses: RequestStatus[] = ["Pending", "In Progress", "Resolved", "Rejected"]
const emptyForm = { title: "", description: "", category: "Other" as Category, status: "Pending" as RequestStatus }

async function authRequest(path: string, body: object): Promise<any> {
  if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
    throw new Error("Authentication is not configured. Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to Vercel.")
  }
  const response = await fetch(`${SUPABASE_URL}/auth/v1/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", apikey: SUPABASE_ANON_KEY },
    body: JSON.stringify(body),
  })
  const data = await response.json()
  if (!response.ok) throw new Error(data.msg || data.message || data.error_description || data.error || "Authentication failed.")
  return data
}

async function apiRequest<T>(endpoint: string, session: Session, options: RequestInit = {}): Promise<T> {
  const response = await fetch(endpoint, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${session.access_token}`,
      ...options.headers,
    },
  })
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const message = typeof data === "object" && data && "detail" in data ? String(data.detail) : `Request failed (${response.status})`
    throw new Error(message)
  }
  return data as T
}

export default function App() {
  const [session, setSession] = useState<Session | null>(() => {
    try { return JSON.parse(localStorage.getItem("campusconnect_session") || "null") } catch { return null }
  })
  const [profile, setProfile] = useState<Profile | null>(null)
  const [authMode, setAuthMode] = useState<"login" | "signup">("login")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [fullName, setFullName] = useState("")
  const [requests, setRequests] = useState<ServiceRequest[]>([])
  const [selected, setSelected] = useState<ServiceRequest | null>(null)
  const [form, setForm] = useState(emptyForm)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState("")
  const [notice, setNotice] = useState("")

  function saveSession(next: Session | null) {
    setSession(next)
    if (next) localStorage.setItem("campusconnect_session", JSON.stringify(next))
    else localStorage.removeItem("campusconnect_session")
  }

  async function loadProfile(current: Session) {
    const me = await apiRequest<Profile>("/api/me", current)
    setProfile(me)
  }

  async function handleAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true); setError(""); setNotice("")
    try {
      if (authMode === "signup") {
        const result = await authRequest("signup", { email, password, data: { full_name: fullName } })
        if (!result.access_token) {
          setNotice("Account created. Check your email to confirm it, then sign in.")
          setAuthMode("login")
          return
        }
        const next: Session = result
        saveSession(next)
        await loadProfile(next)
      } else {
        const result = await authRequest("token?grant_type=password", { email, password })
        const next: Session = result
        saveSession(next)
        await loadProfile(next)
      }
    } catch (err) {
      saveSession(null); setProfile(null)
      setError(err instanceof Error ? err.message : "Could not sign in.")
    } finally { setBusy(false) }
  }

  function signOut() {
    if (session && SUPABASE_URL && SUPABASE_ANON_KEY) {
      void fetch(`${SUPABASE_URL}/auth/v1/logout`, {
        method: "POST",
        headers: { apikey: SUPABASE_ANON_KEY, Authorization: `Bearer ${session.access_token}` },
      })
    }
    saveSession(null); setProfile(null); setRequests([]); setSelected(null)
    setEditingId(null); setForm(emptyForm); setError(""); setNotice("")
  }

  async function loadRequests(current: Session) {
    const data = await apiRequest<ServiceRequest[]>("/api/requests", current)
    setRequests(data)
  }

  useEffect(() => {
    let active = true
    async function initialize() {
      if (!session) { setLoading(false); return }
      try {
        await loadProfile(session)
        await loadRequests(session)
      } catch (err) {
        if (active) {
          saveSession(null); setProfile(null)
          setError(err instanceof Error ? err.message : "Session expired. Please sign in again.")
        }
      } finally { if (active) setLoading(false) }
    }
    void initialize()
    return () => { active = false }
  }, [])

  async function selectRequest(id: number) {
    if (!session) return
    setError(""); setNotice("")
    try { setSelected(await apiRequest<ServiceRequest>(`/api/requests/${id}`, session)) }
    catch (err) { setError(err instanceof Error ? err.message : "Could not load request.") }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!session || !profile) return
    setSaving(true); setError(""); setNotice("")
    const payload = { title: form.title.trim(), description: form.description.trim(), category: form.category }
    try {
      if (editingId !== null) {
        const updated = await apiRequest<ServiceRequest>(`/api/requests/${editingId}`, session, {
          method: "PUT", body: JSON.stringify({ ...payload, status: form.status }),
        })
        setRequests(current => current.map(item => item.id === updated.id ? updated : item))
        setSelected(updated); setNotice("Service request updated successfully.")
      } else {
        const created = await apiRequest<ServiceRequest>("/api/requests", session, {
          method: "POST", body: JSON.stringify(payload),
        })
        setRequests(current => [created, ...current]); setSelected(created)
        setNotice("Service request submitted successfully.")
      }
      setEditingId(null); setForm(emptyForm)
    } catch (err) { setError(err instanceof Error ? err.message : "Could not save request.") }
    finally { setSaving(false) }
  }

  function startEditing(request: ServiceRequest) {
    setEditingId(request.id)
    setForm({ title: request.title, description: request.description, category: request.category, status: request.status })
  }

  async function handleDelete() {
    if (!session || !selected || !window.confirm(`Delete "${selected.title}"?`)) return
    setError(""); setNotice("")
    try {
      await apiRequest(`/api/requests/${selected.id}`, session, { method: "DELETE" })
      setRequests(current => current.filter(item => item.id !== selected.id))
      setSelected(null); setEditingId(null); setForm(emptyForm)
      setNotice("Service request deleted successfully.")
    } catch (err) { setError(err instanceof Error ? err.message : "Could not delete request.") }
  }

  const canCreate = profile?.role === "student" || profile?.role === "admin"
  const canEdit = !!profile && (profile.role === "admin" || profile.role === "staff" || (profile.role === "student" && selected?.user_id === profile.id && selected.status === "Pending"))
  const canDelete = !!profile && (profile.role === "admin" || (profile.role === "student" && selected?.user_id === profile.id && selected.status === "Pending"))
  const canChangeStatus = profile?.role === "admin" || profile?.role === "staff"

  if (loading) return <main className="auth-shell"><div className="auth-card">Loading CampusConnect...</div></main>

  if (!session || !profile) return (
    <main className="auth-shell">
      <section className="auth-card">
        <div className="brand-logo">CC</div>
        <h1>CampusConnect</h1>
        <p>University Service Request Management</p>
        <div className="auth-tabs">
          <button className={authMode === "login" ? "active" : ""} onClick={() => { setAuthMode("login"); setError(""); }}>Sign in</button>
          <button className={authMode === "signup" ? "active" : ""} onClick={() => { setAuthMode("signup"); setError(""); }}>Create account</button>
        </div>
        {error && <div className="alert alert-error">{error}</div>}
        {notice && <div className="alert alert-success">{notice}</div>}
        <form onSubmit={handleAuth}>
          {authMode === "signup" && <>
            <label htmlFor="fullName">Full name</label>
            <input id="fullName" value={fullName} onChange={e => setFullName(e.target.value)} required maxLength={100} />
          </>}
          <label htmlFor="email">Email</label>
          <input id="email" type="email" value={email} onChange={e => setEmail(e.target.value)} required autoComplete="email" />
          <label htmlFor="password">Password</label>
          <input id="password" type="password" value={password} onChange={e => setPassword(e.target.value)} required minLength={8} autoComplete={authMode === "login" ? "current-password" : "new-password"} />
          <button className="primary-button" type="submit" disabled={busy}>{busy ? "Please wait..." : authMode === "login" ? "Sign in" : "Create student account"}</button>
        </form>
        <small>New accounts receive the Student role automatically. Staff and admin roles are assigned by an administrator.</small>
      </section>
    </main>
  )

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-logo">CC</div><div><h2>CampusConnect</h2><span>University Services</span></div></div>
        <div className="nav-label">WORKSPACE</div>
        <div className="nav-item active">▣ Service Requests</div>
        <div className="sidebar-bottom"><div className="profile-avatar">{profile.full_name.slice(0,1).toUpperCase() || "U"}</div><div><strong>{profile.full_name || profile.email}</strong><span>{profile.role.toUpperCase()}</span></div></div>
      </aside>
      <main className="main-area">
        <header className="page-header">
          <div><span className="eyebrow">{profile.role.toUpperCase()} WORKSPACE</span><h1>Service Requests</h1><p>Submit, review and manage university service requests.</p></div>
          <div className="account-actions"><span className="header-badge">{profile.email} · {profile.role}</span><button className="secondary-button" onClick={signOut}>Sign out</button></div>
        </header>
        <section className="stats-grid">
          <div className="stat-card"><span>{profile.role === "student" ? "My requests" : "Total requests"}</span><strong>{requests.length}</strong><small>Visible requests</small></div>
          <div className="stat-card"><span>Pending</span><strong>{requests.filter(r => r.status === "Pending").length}</strong><small>Waiting for attention</small></div>
          <div className="stat-card"><span>In progress</span><strong>{requests.filter(r => r.status === "In Progress").length}</strong><small>Currently being handled</small></div>
        </section>
        {error && <div className="alert alert-error" role="alert">{error}</div>}
        {notice && <div className="alert alert-success" role="status">{notice}</div>}
        <div className="workspace-grid">
          {canCreate && <section className="panel form-panel">
            <div className="panel-heading"><div><h2>{editingId !== null ? "Edit request" : "Create a request"}</h2><p>{editingId !== null ? `Updating request #${editingId}` : "Tell us what support you need."}</p></div></div>
            <form onSubmit={handleSubmit}>
              <label htmlFor="title">Request title</label>
              <input id="title" disabled={profile.role === "staff"} value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} minLength={3} maxLength={120} required />
              <label htmlFor="description">Description</label>
              <textarea id="description" disabled={profile.role === "staff"} value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} minLength={5} maxLength={2000} rows={5} required />
              <label htmlFor="category">Category</label>
              <select id="category" disabled={profile.role === "staff"} value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value as Category }))}>{categories.map(c => <option key={c}>{c}</option>)}</select>
              {editingId !== null && canChangeStatus && <>
                <label htmlFor="status">Request status</label>
                <select id="status" value={form.status} onChange={e => setForm(f => ({ ...f, status: e.target.value as RequestStatus }))}>{statuses.map(s => <option key={s}>{s}</option>)}</select>
              </>}
              <button className="primary-button" type="submit" disabled={saving}>{saving ? "Saving..." : editingId !== null ? "Save changes" : "Submit request"}</button>
              {editingId !== null && <button className="secondary-button" type="button" onClick={() => { setEditingId(null); setForm(emptyForm); }}>Cancel editing</button>}
            </form>
          </section>}
          <section className="panel list-panel">
            <div className="panel-heading list-heading"><div><h2>{profile.role === "student" ? "My requests" : "All requests"}</h2><p>{requests.length} request(s) found</p></div><span className="count-badge">{requests.length}</span></div>
            {requests.length === 0 ? <div className="empty-state">No requests yet.</div> : <div className="request-list">
              {requests.map(request => <button type="button" key={request.id} className={`request-card ${selected?.id === request.id ? "selected" : ""}`} onClick={() => void selectRequest(request.id)}>
                <div className="request-card-top"><span className="request-id">REQUEST #{request.id}</span><span className={`status-pill status-${request.status.toLowerCase().replace(" ", "-")}`}>{request.status}</span></div>
                <h3>{request.title}</h3><p>{request.description}</p><div className="request-card-bottom"><span>{request.category}</span><span>{new Date(request.created_at).toLocaleString()}</span></div>
              </button>)}
            </div>}
          </section>
        </div>
        <section className="panel details-panel"><div className="panel-heading"><div><h2>Request details</h2><p>View the complete information of a request.</p></div></div>
          {!selected ? <div className="empty-state">Select a request to see its details.</div> : <div className="details-content">
            <div className="details-main"><span className="request-id">REQUEST #{selected.id}</span><h2>{selected.title}</h2><p>{selected.description}</p></div>
            <div className="details-meta"><div><span>Category</span><strong>{selected.category}</strong></div><div><span>Status</span><strong>{selected.status}</strong></div><div><span>Created</span><strong>{new Date(selected.created_at).toLocaleString()}</strong></div><div><span>Updated</span><strong>{new Date(selected.updated_at).toLocaleString()}</strong></div></div>
            <div className="details-actions">
              {canEdit && <button className="secondary-button" onClick={() => startEditing(selected)}>Edit request</button>}
              {canDelete && <button className="danger-button" onClick={() => void handleDelete()}>Delete request</button>}
              {profile.role === "staff" && <small>Staff can update status using the request status control when available to their workflow.</small>}
            </div>
          </div>}
        </section>
        <footer className="page-footer">CampusConnect · University Service Request Management</footer>
      </main>
    </div>
  )
}
