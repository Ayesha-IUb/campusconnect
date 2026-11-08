import type { Profile } from "../types"

interface PageHeaderProps {
  profile: Profile
  onSignOut: () => void
}

export default function PageHeader({ profile, onSignOut }: PageHeaderProps) {
  return (
    <>
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-logo">CC</div>
          <div>
            <h2>CampusConnect</h2>
            <span>University Services</span>
          </div>
        </div>

        <div className="nav-label">WORKSPACE</div>
        <div className="nav-item active">▣ Service Requests</div>

        <div className="sidebar-bottom">
          <div className="profile-avatar">
            {profile.full_name.slice(0, 1).toUpperCase() || "U"}
          </div>
          <div>
            <strong>{profile.full_name || profile.email}</strong>
            <span>{profile.role.toUpperCase()}</span>
          </div>
        </div>
      </aside>

      <header className="page-header">
        <div>
          <span className="eyebrow">{profile.role.toUpperCase()} WORKSPACE</span>
          <h1>Service Requests</h1>
          <p>Submit, review and manage university service requests.</p>
        </div>

        <div className="account-actions">
          <span className="header-badge">{profile.email} · {profile.role}</span>
          <button className="secondary-button" onClick={onSignOut}>
            Sign out
          </button>
        </div>
      </header>
    </>
  )
}
