import { useEffect, useState, type FormEvent } from "react"
import type { Category, RequestStatus, Session, Profile, ServiceRequest } from "./types"
import AuthForm from "./components/AuthForm"
import PageHeader from "./components/PageHeader"
import RequestDetails from "./components/RequestDetails"
import RequestForm, { type RequestFormValues } from "./components/RequestForm"
import RequestList from "./components/RequestList"
import RequestStats from "./components/RequestStats"
import Sidebar from "./components/Sidebar"
import { apiRequest, authRequest, logoutRequest } from "./services/api"

const emptyForm: RequestFormValues = {
  title: "",
  description: "",
  category: "Other",
  status: "Pending",
}

export default function App() {
  const [session, setSession] = useState<Session | null>(() => {
    try {
      return JSON.parse(localStorage.getItem("campusconnect_session") || "null")
    } catch {
      return null
    }
  })
  const [profile, setProfile] = useState<Profile | null>(null)
  const [authMode, setAuthMode] = useState<"login" | "signup">("login")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [fullName, setFullName] = useState("")
  const [requests, setRequests] = useState<ServiceRequest[]>([])
  const [selected, setSelected] = useState<ServiceRequest | null>(null)
  const [form, setForm] = useState<RequestFormValues>(emptyForm)
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
    setProfile(await apiRequest<Profile>("/api/me", current))
  }

  async function handleAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError("")
    setNotice("")

    try {
      const result = authMode === "signup"
        ? await authRequest("signup", { email, password, data: { full_name: fullName } })
        : await authRequest("token?grant_type=password", { email, password })

      if (authMode === "signup" && !result.access_token) {
        setNotice("Account created. Check your email to confirm it, then sign in.")
        setAuthMode("login")
        return
      }

      const next = result as Session
      saveSession(next)
      await loadProfile(next)
    } catch (err) {
      saveSession(null)
      setProfile(null)
      setError(err instanceof Error ? err.message : "Could not sign in.")
    } finally {
      setBusy(false)
    }
  }

  async function handleResendConfirmation() {
    if (!email.trim()) {
      setError("Enter your email address first.")
      return
    }
    setBusy(true)
    setError("")
    setNotice("")
    try {
      await authRequest("resend", {
        type: "signup",
        email: email.trim(),
        options: { emailRedirectTo: "https://campusconnect-two-ivory.vercel.app" },
      })
      setNotice("A new confirmation email has been requested. Check your inbox and spam folder.")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not resend the confirmation email.")
    } finally {
      setBusy(false)
    }
  }

  function signOut() {
    if (session) logoutRequest(session)
    saveSession(null)
    setProfile(null)
    setRequests([])
    setSelected(null)
    setEditingId(null)
    setForm(emptyForm)
    setError("")
    setNotice("")
  }

  async function loadRequests(current: Session) {
    setRequests(await apiRequest<ServiceRequest[]>("/api/requests", current))
  }

  useEffect(() => {
    let active = true
    async function initialize() {
      if (!session) {
        setLoading(false)
        return
      }
      try {
        await loadProfile(session)
        await loadRequests(session)
      } catch (err) {
        if (active) {
          saveSession(null)
          setProfile(null)
          setError(err instanceof Error ? err.message : "Session expired. Please sign in again.")
        }
      } finally {
        if (active) setLoading(false)
      }
    }
    void initialize()
    return () => { active = false }
  }, [])

  async function selectRequest(id: number) {
    if (!session) return
    setError("")
    setNotice("")
    try {
      setSelected(await apiRequest<ServiceRequest>("/api/requests/" + id, session))
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load request.")
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!session || !profile) return
    setSaving(true)
    setError("")
    setNotice("")

    const payload = {
      title: form.title.trim(),
      description: form.description.trim(),
      category: form.category,
    }

    try {
      if (editingId !== null) {
        const updated = await apiRequest<ServiceRequest>(
          "/api/requests/" + editingId,
          session,
          { method: "PUT", body: JSON.stringify({ ...payload, status: form.status }) },
        )
        setRequests(current => current.map(item => item.id === updated.id ? updated : item))
        setSelected(updated)
        setNotice("Service request updated successfully.")
      } else {
        const created = await apiRequest<ServiceRequest>(
          "/api/requests",
          session,
          { method: "POST", body: JSON.stringify(payload) },
        )
        setRequests(current => [created, ...current])
        setSelected(created)
        setNotice("Service request submitted successfully.")
      }
      setEditingId(null)
      setForm(emptyForm)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save request.")
    } finally {
      setSaving(false)
    }
  }

  function startEditing(request: ServiceRequest) {
    setEditingId(request.id)
    setForm({
      title: request.title,
      description: request.description,
      category: request.category,
      status: request.status,
    })
  }

  async function handleDelete() {
    if (!session || !selected || !window.confirm("Delete \"" + selected.title + "\"?")) return
    setError("")
    setNotice("")
    try {
      await apiRequest("/api/requests/" + selected.id, session, { method: "DELETE" })
      setRequests(current => current.filter(item => item.id !== selected.id))
      setSelected(null)
      setEditingId(null)
      setForm(emptyForm)
      setNotice("Service request deleted successfully.")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete request.")
    }
  }

  const canCreate = profile?.role === "student" || profile?.role === "admin"
  const canEdit = !!profile && (
    profile.role === "admin" ||
    profile.role === "staff" ||
    (profile.role === "student" && selected?.user_id === profile.id && selected.status === "Pending")
  )
  const canDelete = !!profile && (
    profile.role === "admin" ||
    (profile.role === "student" && selected?.user_id === profile.id && selected.status === "Pending")
  )
  const canChangeStatus = profile?.role === "admin" || profile?.role === "staff"

  if (loading) {
    return <main className="auth-shell"><div className="auth-card">Loading CampusConnect...</div></main>
  }

  if (!session || !profile) {
    return (
      <AuthForm
        authMode={authMode}
        email={email}
        password={password}
        fullName={fullName}
        busy={busy}
        error={error}
        notice={notice}
        onModeChange={mode => { setAuthMode(mode); setError("") }}
        onEmailChange={setEmail}
        onPasswordChange={setPassword}
        onFullNameChange={setFullName}
        onSubmit={handleAuth}
        onResendConfirmation={() => void handleResendConfirmation()}
      />
    )
  }

  return (
    <div className="app-shell">
      <Sidebar profile={profile} />
      <main className="main-area">
        <PageHeader profile={profile} onSignOut={signOut} />
        <RequestStats requests={requests} isStudent={profile.role === "student"} />

        {error && <div className="alert alert-error" role="alert">{error}</div>}
        {notice && <div className="alert alert-success" role="status">{notice}</div>}

        <div className="workspace-grid">
          {(canCreate || (profile.role === "staff" && editingId !== null)) && (
            <RequestForm
              form={form}
              editingId={editingId}
              isStaff={profile.role === "staff"}
              canChangeStatus={!!canChangeStatus}
              saving={saving}
              onTitleChange={value => setForm(current => ({ ...current, title: value }))}
              onDescriptionChange={value => setForm(current => ({ ...current, description: value }))}
              onCategoryChange={(value: Category) => setForm(current => ({ ...current, category: value }))}
              onStatusChange={(value: RequestStatus) => setForm(current => ({ ...current, status: value }))}
              onSubmit={handleSubmit}
              onCancel={() => { setEditingId(null); setForm(emptyForm) }}
            />
          )}

          <RequestList
            requests={requests}
            selected={selected}
            isStudent={profile.role === "student"}
            onSelect={id => void selectRequest(id)}
          />
        </div>

        <RequestDetails
          selected={selected}
          canEdit={canEdit}
          canDelete={canDelete}
          isStaff={profile.role === "staff"}
          onEdit={startEditing}
          onDelete={() => void handleDelete()}
        />

        <footer className="page-footer">CampusConnect · University Service Request Management</footer>
      </main>
    </div>
  )
}
