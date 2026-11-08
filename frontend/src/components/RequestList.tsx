import type { Role, ServiceRequest } from "../types"

interface RequestListProps {
  requests: ServiceRequest[]
  selectedId: number | null
  role: Role
  onSelect: (id: number) => void
}

export default function RequestList({ requests, selectedId, role, onSelect }: RequestListProps) {
  return (
    <section className="panel list-panel">
      <div className="panel-heading list-heading">
        <div><h2>{role === "student" ? "My requests" : "All requests"}</h2><p>{requests.length} request(s) found</p></div>
        <span className="count-badge">{requests.length}</span>
      </div>
      {requests.length === 0 ? <div className="empty-state">No requests yet.</div> : (
        <div className="request-list">
          {requests.map((request) => (
            <button type="button" key={request.id} className={`request-card ${selectedId === request.id ? "selected" : ""}`} onClick={() => onSelect(request.id)}>
              <div className="request-card-top">
                <span className="request-id">REQUEST #{request.id}</span>
                <span className={`status-pill status-${request.status.toLowerCase().replace(" ", "-")}`}>{request.status}</span>
              </div>
              <h3>{request.title}</h3>
              <p>{request.description}</p>
              <div className="request-card-bottom">
                <span>{request.category}</span>
                <span>{new Date(request.created_at).toLocaleString()}</span>
              </div>
            </button>
          ))}
        </div>
      )}
    </section>
  )
}
