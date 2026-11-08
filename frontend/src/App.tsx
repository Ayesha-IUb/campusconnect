import { useEffect, useState, type FormEvent } from "react"
import AuthPage from "./components/AuthPage"
import DashboardShell from "./components/DashboardShell"
import RequestDetails from "./components/RequestDetails"
import RequestForm from "./components/RequestForm"
import RequestList from "./components/RequestList"
import StatsGrid from "./components/StatsGrid"
import { emptyForm } from "./constants/requests"
import {
  createRequest,
  deleteRequest,
  getProfile,
  getRequest,
  getRequests,
  resendConfirmation,
  signIn,
  signOut,
  signUp,
  updateRequest,
} from "./services/api"
import type {
  AuthMode,
  Profile,
  RequestFormValues,
  ServiceRequest,
  Session,
} from "./types"

function readStoredSession(): Session | null {
  try {
    return JSON.parse(localStorage.getItem("campusconnect_session") || "null")
  } catch {
    return null
  }
}

export default function App() {
  const [session, setSession] = useState<Session | null>(readStoredSession)
  const [profile, setProfile] = useState<Profile | null>(null)
  const [authMode, setAuthMode] = useState<AuthMode>("login")
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
    if (next) {
      localStorage.setItem("campusconnect_session", JSON.stringify(next))
    } else {
      localStorage.removeItem("campusconnect_session")
    }
  }

  async function handleAuth(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError("")
    setNotice("")

    try {
      if (authMode === "signup") {
        const result = await signUp(email, password, fullName)

        if (!result.access_token || !result.refresh_token || !result.user) {
          setNotice("Account created. Check your email to confirm it, then sign in.")
          setAuthMode("login")
          return
        }

        const next: Session = result as Session
        saveSession(next)
        const [userProfile, data] = await Promise.all([
          getProfile(next),
          getRequests(next),
        ])
        setProfile(userProfile)
        setRequests(data)
      } else {
        const next = await signIn(email, password)
        saveSession(next)
        const [userProfile, data] = await Promise.all([
          getProfile(next),
          getRequests(next),
        ])
        setProfile(userProfile)
        setRequests(data)
      }
    } catch (err) {
      saveSession(null)
      setProfile(null)
      setRequests([])
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
      await resendConfirmation(email)
      setNotice(
        "A new confirmation email has been requested. Check your inbox and spam folder.",
      )
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not resend the confirmation email.",
      )
    } finally {
      setBusy(false)
    }
  }

  function handleSignOut() {
    if (session) {
      void signOut(session).catch(() => {
        // Clear the local session even if the remote logout request fails.
      })
    }

    saveSession(null)
    setProfile(null)
    setRequests([])
    setSelected(null)
    setEditingId(null)
    setForm(emptyForm)
    setError("")
    setNotice("")
  }

  useEffect(() => {
    let active = true

    async function initialize() {
      if (!session) {
        setLoading(false)
        return
      }

      try {
        const [userProfile, data] = await Promise.all([
          getProfile(session),
          getRequests(session),
        ])

        if (active) {
          setProfile(userProfile)
          setRequests(data)
        }
      } catch (err) {
        if (active) {
          saveSession(null)
          setProfile(null)
          setRequests([])
          setError(
            err instanceof Error
              ? err.message
              : "Session expired. Please sign in again.",
          )
        }
      } finally {
        if (active) setLoading(false)
      }
    }

    void initialize()
    return () => {
      active = false
    }
  }, [])

  async function selectRequest(id: number) {
    if (!session) return

    setError("")
    setNotice("")
    try {
      setSelected(await getRequest(id, session))
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
        const updated = await updateRequest(
          editingId,
          { ...payload, status: form.status },
          session,
        )
        setRequests((current) =>
          current.map((item) => (item.id === updated.id ? updated : item)),
        )
        setSelected(updated)
        setNotice("Service request updated successfully.")
      } else {
        const created = await createRequest(payload, session)
        setRequests((current) => [created, ...current])
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
    if (!session || !selected || !window.confirm(`Delete "${selected.title}"?`)) {
      return
    }

    setError("")
    setNotice("")
    try {
      await deleteRequest(selected.id, session)
      setRequests((current) =>
        current.filter((item) => item.id !== selected.id),
      )
      setSelected(null)
      setEditingId(null)
      setForm(emptyForm)
      setNotice("Service request deleted successfully.")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete request.")
    }
  }

  const canCreate = profile?.role === "student" || profile?.role === "admin"
  const canEdit =
    !!profile &&
    (profile.role === "admin" ||
      profile.role === "staff" ||
      (profile.role === "student" &&
        selected?.user_id === profile.id &&
        selected.status === "Pending"))
  const canDelete =
    !!profile &&
    (profile.role === "admin" ||
      (profile.role === "student" &&
        selected?.user_id === profile.id &&
        selected.status === "Pending"))
  const canChangeStatus = profile?.role === "admin" || profile?.role === "staff"
  const showRequestForm =
    !!profile &&
    (canCreate || (profile.role === "staff" && editingId !== null))

  if (loading) {
    return (
      <main className="auth-shell">
        <div className="auth-card">Loading CampusConnect...</div>
      </main>
    )
  }

  if (!session || !profile) {
    return (
      <AuthPage
        authMode={authMode}
        onAuthModeChange={(mode) => {
          setAuthMode(mode)
          setError("")
          setNotice("")
        }}
        email={email}
        onEmailChange={setEmail}
        password={password}
        onPasswordChange={setPassword}
        fullName={fullName}
        onFullNameChange={setFullName}
        busy={busy}
        error={error}
        notice={notice}
        onSubmit={handleAuth}
        onResendConfirmation={handleResendConfirmation}
      />
    )
  }

  return (
    <DashboardShell profile={profile} onSignOut={handleSignOut}>
      <StatsGrid profile={profile} requests={requests} />

      {error && (
        <div className="alert alert-error" role="alert">
          {error}
        </div>
      )}
      {notice && (
        <div className="alert alert-success" role="status">
          {notice}
        </div>
      )}

      <div className="workspace-grid">
        {showRequestForm && (
          <RequestForm
            profile={profile}
            editingId={editingId}
            form={form}
            setForm={setForm}
            canChangeStatus={canChangeStatus}
            saving={saving}
            onSubmit={handleSubmit}
            onCancel={() => {
              setEditingId(null)
              setForm(emptyForm)
            }}
          />
        )}

        <RequestList
          requests={requests}
          selectedId={selected?.id ?? null}
          role={profile.role}
          onSelect={(id) => void selectRequest(id)}
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
    </DashboardShell>
  )
}
