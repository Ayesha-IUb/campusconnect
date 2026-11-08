import type { ReactNode } from "react"
import type { Profile } from "../types"

interface DashboardShellProps {
  profile: Profile
  onSignOut: () => void
  children: ReactNode
}

export default function DashboardShell({ profile, onSignOut, children }: DashboardShellProps) {
  const displayName = profile.full_name || profile.email

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-logo">CC</div>
          <div><h2>CampusConnect</h2><span>University Services</span></div>
        </div>
        <div className="nav-label">WORKSPACE</div>
        <div className="nav-item active">▣ Service Requests</div>
        <div className="sidebar-bottom">
          <div className="profile-avatar">{displayName.slice(0, 1).toUpperCase() || "U"}</div>
          <div><strong>{displayName}</strong><span>{profile.role.toUpperCase()}</span></div>
        </div>
      </aside>

      <main className="main-area">
        <header className="page-header">
          <div>
            <span className="eyebrow">{profile.role.toUpperCase()} WORKSPACE</span>
            <h1>Service Requests</h1>
            <p>Submit, review and manage university service requests.</p>
          </div>
          <div className="account-actions">
            <span className="header-badge">{profile.email} · {profile.role}</span>
            <button className="secondary-button" onClick={onSignOut}>Sign out</button>
          </div>
        </header>
        {children}
        <footer className="page-footer">CampusConnect · University Service Request Management</footer>
      </main>
    </div>
  )
}
