import type { Profile } from "../types"

interface PageHeaderProps {
  profile: Profile
  onSignOut: () => void
}

export default function PageHeader({ profile, onSignOut }: PageHeaderProps) {
  return (
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
  )
}
