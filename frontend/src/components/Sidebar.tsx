import type { AppPage, Profile } from "../types";

interface SidebarProps {
  profile: Profile;
  activePage: AppPage;
  onNavigate: (page: AppPage) => void;
}

export default function Sidebar({ profile, activePage, onNavigate }: SidebarProps) {
  const items: { id: AppPage; label: string }[] = [
    { id: "requests", label: "Service Requests" },
    { id: "groups", label: "Groups" },
    { id: "profile", label: "Profile & Sessions" },
  ];
  if (profile.role === "admin") items.push({ id: "admin", label: "Admin Dashboard" });

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-logo">CC</div>
        <div><h2>CampusConnect</h2><span>University Services</span></div>
      </div>
      <div className="nav-label">WORKSPACE</div>
      {items.map(item => (
        <button
          type="button"
          key={item.id}
          className={`nav-item ${activePage === item.id ? "active" : ""}`}
          onClick={() => onNavigate(item.id)}
        >
          {item.label}
        </button>
      ))}
      <div className="sidebar-bottom">
        <div className="profile-avatar">{profile.full_name.slice(0, 1).toUpperCase() || "U"}</div>
        <div><strong>{profile.full_name || profile.email}</strong><span>{profile.role.toUpperCase()}</span></div>
      </div>
    </aside>
  );
}
