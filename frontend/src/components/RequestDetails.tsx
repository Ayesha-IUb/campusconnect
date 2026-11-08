import type { ServiceRequest } from "../types"

interface RequestDetailsProps {
  selected: ServiceRequest | null
  canEdit: boolean
  canDelete: boolean
  isStaff: boolean
  onEdit: (request: ServiceRequest) => void
  onDelete: () => void
}

export default function RequestDetails({
  selected, canEdit, canDelete, isStaff, onEdit, onDelete,
}: RequestDetailsProps) {
  return (
    <section className="panel details-panel">
      <div className="panel-heading">
        <div><h2>Request details</h2><p>View the complete information of a request.</p></div>
      </div>
      {!selected ? <div className="empty-state">Select a request to see its details.</div> : (
        <div className="details-content">
          <div className="details-main">
            <span className="request-id">REQUEST #{selected.id}</span>
            <h2>{selected.title}</h2>
            <p>{selected.description}</p>
          </div>
          <div className="details-meta">
            <div><span>Category</span><strong>{selected.category}</strong></div>
            <div><span>Status</span><strong>{selected.status}</strong></div>
            <div><span>Created</span><strong>{new Date(selected.created_at).toLocaleString()}</strong></div>
            <div><span>Updated</span><strong>{new Date(selected.updated_at).toLocaleString()}</strong></div>
          </div>
          <div className="details-actions">
            {canEdit && <button className="secondary-button" onClick={() => onEdit(selected)}>Edit request</button>}
            {canDelete && <button className="danger-button" onClick={onDelete}>Delete request</button>}
            {isStaff && <small>Staff can change request status only. Click Edit request to open the status control.</small>}
          </div>
        </div>
      )}
    </section>
  )
}
