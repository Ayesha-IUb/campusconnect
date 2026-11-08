import type { FormEvent } from "react"
import type { AuthMode } from "../types"

interface AuthPageProps {
  authMode: AuthMode
  onAuthModeChange: (mode: AuthMode) => void
  email: string
  onEmailChange: (value: string) => void
  password: string
  onPasswordChange: (value: string) => void
  fullName: string
  onFullNameChange: (value: string) => void
  busy: boolean
  error: string
  notice: string
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
  onResendConfirmation: () => void
}

export default function AuthPage(props: AuthPageProps) {
  const {
    authMode, onAuthModeChange, email, onEmailChange, password,
    onPasswordChange, fullName, onFullNameChange, busy, error,
    notice, onSubmit, onResendConfirmation,
  } = props

  return (
    <main className="auth-shell">
      <section className="auth-card">
        <div className="brand-logo">CC</div>
        <h1>CampusConnect</h1>
        <p>University Service Request Management</p>
        <div className="auth-tabs">
          <button className={authMode === "login" ? "active" : ""} onClick={() => onAuthModeChange("login")}>Sign in</button>
          <button className={authMode === "signup" ? "active" : ""} onClick={() => onAuthModeChange("signup")}>Create account</button>
        </div>
        {error && <div className="alert alert-error">{error}</div>}
        {notice && <div className="alert alert-success">{notice}</div>}
        <form onSubmit={onSubmit}>
          {authMode === "signup" && <>
            <label htmlFor="fullName">Full name</label>
            <input id="fullName" value={fullName} onChange={(event) => onFullNameChange(event.target.value)} required maxLength={100} />
          </>}
          <label htmlFor="email">Email</label>
          <input id="email" type="email" value={email} onChange={(event) => onEmailChange(event.target.value)} required autoComplete="email" />
          <label htmlFor="password">Password</label>
          <input id="password" type="password" value={password} onChange={(event) => onPasswordChange(event.target.value)} required minLength={8} autoComplete={authMode === "login" ? "current-password" : "new-password"} />
          <button className="primary-button" type="submit" disabled={busy}>
            {busy ? "Please wait..." : authMode === "login" ? "Sign in" : "Create student account"}
          </button>
          {authMode === "login" && (
            <button className="secondary-button" type="button" onClick={onResendConfirmation} disabled={busy || !email.trim()}>
              Resend confirmation email
            </button>
          )}
        </form>
        <small>New accounts receive the Student role automatically. Staff and admin roles are assigned by an administrator.</small>
      </section>
    </main>
  )
}
