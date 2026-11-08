import type { FormEventHandler } from "react"

interface AuthFormProps {
  authMode: "login" | "signup"
  email: string
  password: string
  fullName: string
  busy: boolean
  error: string
  notice: string
  onModeChange: (mode: "login" | "signup") => void
  onEmailChange: (value: string) => void
  onPasswordChange: (value: string) => void
  onFullNameChange: (value: string) => void
  onSubmit: FormEventHandler<HTMLFormElement>
  onResendConfirmation: () => void
}

export default function AuthForm({
  authMode,
  email,
  password,
  fullName,
  busy,
  error,
  notice,
  onModeChange,
  onEmailChange,
  onPasswordChange,
  onFullNameChange,
  onSubmit,
  onResendConfirmation,
}: AuthFormProps) {
  return (
    <main className="auth-shell">
      <section className="auth-card">
        <div className="brand-logo">CC</div>
        <h1>CampusConnect</h1>
        <p>University Service Request Management</p>

        <div className="auth-tabs">
          <button
            className={authMode === "login" ? "active" : ""}
            onClick={() => onModeChange("login")}
          >
            Sign in
          </button>
          <button
            className={authMode === "signup" ? "active" : ""}
            onClick={() => onModeChange("signup")}
          >
            Create account
          </button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {notice && <div className="alert alert-success">{notice}</div>}

        <form onSubmit={onSubmit}>
          {authMode === "signup" && (
            <>
              <label htmlFor="fullName">Full name</label>
              <input
                id="fullName"
                value={fullName}
                onChange={event => onFullNameChange(event.target.value)}
                required
                maxLength={100}
              />
            </>
          )}

          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={event => onEmailChange(event.target.value)}
            required
            autoComplete="email"
          />

          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={event => onPasswordChange(event.target.value)}
            required
            minLength={8}
            autoComplete={authMode === "login" ? "current-password" : "new-password"}
          />

          <button className="primary-button" type="submit" disabled={busy}>
            {busy
              ? "Please wait..."
              : authMode === "login"
                ? "Sign in"
                : "Create student account"}
          </button>

          {authMode === "login" && (
            <button
              className="secondary-button"
              type="button"
              onClick={onResendConfirmation}
              disabled={busy || !email.trim()}
            >
              Resend confirmation email
            </button>
          )}
        </form>

        <small>
          New accounts receive the Student role automatically. Staff and admin roles are assigned by an administrator.
        </small>
      </section>
    </main>
  )
}
