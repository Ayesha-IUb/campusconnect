import type { FormEventHandler } from "react"
import type { Category, RequestStatus } from "../types"

export interface RequestFormValues {
  title: string
  description: string
  category: Category
  status: RequestStatus
}

interface RequestFormProps {
  form: RequestFormValues
  editingId: number | null
  isStaff: boolean
  canChangeStatus: boolean
  saving: boolean
  onTitleChange: (value: string) => void
  onDescriptionChange: (value: string) => void
  onCategoryChange: (value: Category) => void
  onStatusChange: (value: RequestStatus) => void
  onSubmit: FormEventHandler<HTMLFormElement>
  onCancel: () => void
}

const categories: Category[] = ["IT Support", "Classroom", "Facilities", "Library", "Other"]
const statuses: RequestStatus[] = ["Pending", "In Progress", "Resolved", "Rejected"]

export default function RequestForm({
  form,
  editingId,
  isStaff,
  canChangeStatus,
  saving,
  onTitleChange,
  onDescriptionChange,
  onCategoryChange,
  onStatusChange,
  onSubmit,
  onCancel,
}: RequestFormProps) {
  return (
    <section className="panel form-panel">
      <div className="panel-heading">
        <div>
          <h2>{editingId !== null ? "Edit request" : "Create a request"}</h2>
          <p>{editingId !== null ? "Updating request #" + editingId : "Tell us what support you need."}</p>
        </div>
      </div>

      <form onSubmit={onSubmit}>
        <label htmlFor="title">Request title</label>
        <input id="title" disabled={isStaff} value={form.title} onChange={event => onTitleChange(event.target.value)} minLength={3} maxLength={120} required />

        <label htmlFor="description">Description</label>
        <textarea id="description" disabled={isStaff} value={form.description} onChange={event => onDescriptionChange(event.target.value)} minLength={5} maxLength={2000} rows={5} required />

        <label htmlFor="category">Category</label>
        <select id="category" disabled={isStaff} value={form.category} onChange={event => onCategoryChange(event.target.value as Category)}>
          {categories.map(category => <option key={category}>{category}</option>)}
        </select>

        {editingId !== null && canChangeStatus && (
          <>
            <label htmlFor="status">Request status</label>
            <select id="status" value={form.status} onChange={event => onStatusChange(event.target.value as RequestStatus)}>
              {statuses.map(status => <option key={status}>{status}</option>)}
            </select>
          </>
        )}

        <button className="primary-button" type="submit" disabled={saving}>
          {saving ? "Saving..." : editingId !== null ? "Save changes" : "Submit request"}
        </button>

        {editingId !== null && (
          <button className="secondary-button" type="button" onClick={onCancel}>
            Cancel editing
          </button>
        )}
      </form>
    </section>
  )
}
