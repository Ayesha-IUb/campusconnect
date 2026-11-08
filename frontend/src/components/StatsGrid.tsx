import type { Profile, ServiceRequest } from "../types"

interface StatsGridProps {
  profile: Profile
  requests: ServiceRequest[]
}

export default function StatsGrid({ profile, requests }: StatsGridProps) {
  return (
    <section className="stats-grid">
      <div className="stat-card">
        <span>{profile.role === "student" ? "My requests" : "Total requests"}</span>
        <strong>{requests.length}</strong>
        <small>Visible requests</small>
      </div>
      <div className="stat-card">
        <span>Pending</span>
        <strong>{requests.filter((request) => request.status === "Pending").length}</strong>
        <small>Waiting for attention</small>
      </div>
      <div className="stat-card">
        <span>In progress</span>
        <strong>{requests.filter((request) => request.status === "In Progress").length}</strong>
        <small>Currently being handled</small>
      </div>
    </section>
  )
}
