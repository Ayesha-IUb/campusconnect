import type { Dispatch, FormEvent, SetStateAction } from "react"
import { categories, statuses } from "../constants/requests"
import type { Profile, RequestFormValues } from "../types"

interface RequestFormProps {
  profile: Profile
  editingId: number | null
  form: RequestFormValues
  setForm: Dispatch<SetStateAction<RequestFormValues>>
  canChangeStatus: boolean
  saving: boolean
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
  onCancel: () => void
}

export default function RequestForm({
  profile, editingId, form, setForm, canChangeStatus, saving, onSubmit, onCancel,
}: RequestFormProps) {
  const isStaff = profile.role === "staff"

  return (
    <section className="panel form-panel">
      <div className="panel-heading">
        <div>
          <h2>{editingId !== null ? "Edit request" : "Create a request"}</h2>
          <p>{editingId !== null ? `Updating request #${editingId}` : "Tell us what support you need."}</p>
        </div>
      </div>
      <form onSubmit={onSubmit}>
        <label htmlFor="title">Request title</label>
        <input id="title" disabled={isStaff} value={form.title} onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))} minLength={3} maxLength={120} required />
        <label htmlFor="description">Description</label>
        <textarea id="description" disabled={isStaff} value={form.description} onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} minLength={5} maxLength={2000} rows={5} required />
        <label htmlFor="category">Category</label>
        <select id="category" disabled={isStaff} value={form.category} onChange={(event) => setForm((current) => ({ ...current, category: event.target.value as RequestFormValues["category"] }))}>
          {categories.map((category) => <option key={category}>{category}</option>)}
        </select>
        {editingId !== null && canChangeStatus && <>
          <label htmlFor="status">Request status</label>
          <select id="status" value={form.status} onChange={(event) => setForm((current) => ({ ...current, status: event.target.value as RequestFormValues["status"] }))}>
            {statuses.map((status) => <option key={status}>{status}</option>)}
          </select>
        </>}
        <button className="primary-button" type="submit" disabled={saving}>
          {saving ? "Saving..." : editingId !== null ? "Save changes" : "Submit request"}
        </button>
        {editingId !== null && <button className="secondary-button" type="button" onClick={onCancel}>Cancel editing</button>}
      </form>
    </section>
  )
}
