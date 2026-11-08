import type { ServiceRequest } from "../types"

interface RequestStatsProps {
  requests: ServiceRequest[]
  isStudent: boolean
}

export default function RequestStats({ requests, isStudent }: RequestStatsProps) {
  const pendingCount = requests.filter(request => request.status === "Pending").length
  const inProgressCount = requests.filter(request => request.status === "In Progress").length

  return (
    <section className="stats-grid">
      <div className="stat-card">
        <span>{isStudent ? "My requests" : "Total requests"}</span>
        <strong>{requests.length}</strong>
        <small>Visible requests</small>
      </div>

      <div className="stat-card">
        <span>Pending</span>
        <strong>{pendingCount}</strong>
        <small>Waiting for attention</small>
      </div>

      <div className="stat-card">
        <span>In progress</span>
        <strong>{inProgressCount}</strong>
        <small>Currently being handled</small>
      </div>
    </section>
  )
}
