import type { Profile } from "../types"

interface SidebarProps {
  profile: Profile
}

export default function Sidebar({ profile }: SidebarProps) {
  return (
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
  )
}
