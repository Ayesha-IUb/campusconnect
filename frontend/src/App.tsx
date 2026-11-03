
import { useEffect, useState, type FormEvent } from "react"

type Category =
  | "IT Support"
  | "Classroom"
  | "Facilities"
  | "Library"
  | "Other"

type RequestStatus =
  | "Pending"
  | "In Progress"
  | "Resolved"
  | "Rejected"

interface ServiceRequest {
  id: number
  title: string
  description: string
  category: Category
  status: RequestStatus
  created_at: string
  updated_at: string
}

interface FormValues {
  title: string
  description: string
  category: Category
  status: RequestStatus
}

const categories: Category[] = [
  "IT Support",
  "Classroom",
  "Facilities",
  "Library",
  "Other",
]

const statuses: RequestStatus[] = [
  "Pending",
  "In Progress",
  "Resolved",
  "Rejected",
]

const emptyForm: FormValues = {
  title: "",
  description: "",
  category: "Other",
  status: "Pending",
}

// Common function for communicating with FastAPI
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(endpoint, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  })

  let data: unknown = null

  try {
    data = await response.json()
  } catch {
    data = null
  }

  if (!response.ok) {
    const message =
      typeof data === "object" &&
      data !== null &&
      "detail" in data
        ? String(data.detail)
        : `Request failed (${response.status})`

    throw new Error(message)
  }

  return data as T
}

function formatDate(date: string) {
  return new Date(date).toLocaleString()
}

export default function App() {
  const [requests, setRequests] = useState<ServiceRequest[]>([])
  const [selected, setSelected] = useState<ServiceRequest | null>(null)

  const [form, setForm] = useState<FormValues>(emptyForm)
  const [editingId, setEditingId] = useState<number | null>(null)

  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  const [error, setError] = useState("")
  const [notice, setNotice] = useState("")

  // READ LIST: Load all service requests
  useEffect(() => {
    let active = true

    async function loadRequests() {
      try {
        const data = await apiRequest<ServiceRequest[]>(
          "/api/requests",
        )

        if (active) {
          setRequests(data)
        }
      } catch (err) {
        if (active) {
          setError(
            err instanceof Error
              ? err.message
              : "Could not load requests.",
          )
        }
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    void loadRequests()

    return () => {
      active = false
    }
  }, [])

  // READ SINGLE: Load one request by its ID
  async function selectRequest(id: number) {
    setDetailLoading(true)
    setError("")
    setNotice("")

    try {
      const data = await apiRequest<ServiceRequest>(
        `/api/requests/${id}`,
      )

      setSelected(data)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not load request details.",
      )
    } finally {
      setDetailLoading(false)
    }
  }

  function handleInputChange(
    field: keyof FormValues,
    value: string,
  ) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }))
  }

  // CREATE and UPDATE
  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    setSaving(true)
    setError("")
    setNotice("")

    const payload = {
      title: form.title.trim(),
      description: form.description.trim(),
      category: form.category,
    }

    try {
      if (editingId !== null) {
        // UPDATE
        const updated = await apiRequest<ServiceRequest>(
          `/api/requests/${editingId}`,
          {
            method: "PUT",
            body: JSON.stringify({
              ...payload,
              status: form.status,
            }),
          },
        )

        setRequests((current) =>
          current.map((item) =>
            item.id === updated.id ? updated : item,
          ),
        )

        setSelected(updated)
        setNotice("Service request updated successfully.")
      } else {
        // CREATE
        const created = await apiRequest<ServiceRequest>(
          "/api/requests",
          {
            method: "POST",
            body: JSON.stringify(payload),
          },
        )

        setRequests((current) => [created, ...current])
        setSelected(created)
        setNotice("Service request submitted successfully.")
      }

      setEditingId(null)
      setForm(emptyForm)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not save your request.",
      )
    } finally {
      setSaving(false)
    }
  }

  // Start editing a selected request
  function startEditing(request: ServiceRequest) {
    setEditingId(request.id)

    setForm({
      title: request.title,
      description: request.description,
      category: request.category,
      status: request.status,
    })

    setError("")
    setNotice("")
  }

  function cancelEditing() {
    setEditingId(null)
    setForm(emptyForm)
    setError("")
    setNotice("")
  }

  // DELETE
  async function handleDelete() {
    if (!selected) return

    const confirmed = window.confirm(
      `Are you sure you want to delete "${selected.title}"?`,
    )

    if (!confirmed) return

    setError("")
    setNotice("")

    try {
      await apiRequest<{ message: string; id: number }>(
        `/api/requests/${selected.id}`,
        { method: "DELETE" },
      )

      setRequests((current) =>
        current.filter((item) => item.id !== selected.id),
      )

      setSelected(null)

      if (editingId === selected.id) {
        cancelEditing()
      }

      setNotice("Service request deleted successfully.")
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not delete request.",
      )
    }
  }

  const editing = editingId !== null

  const pendingCount = requests.filter(
    (request) => request.status === "Pending",
  ).length

  const activeCount = requests.filter(
    (request) => request.status === "In Progress",
  ).length

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-logo">CC</div>
          <div>
            <h2>CampusConnect</h2>
            <span>University Services</span>
          </div>
        </div>

        <div className="nav-label">WORKSPACE</div>

        <div className="nav-item active">
          <span className="nav-icon">▣</span>
          Service Requests
        </div>

        <div className="sidebar-bottom">
          <div className="profile-avatar">S</div>
          <div>
            <strong>Student Portal</strong>
            <span>CampusConnect MVP</span>
          </div>
        </div>
      </aside>

      <main className="main-area">
        <header className="page-header">
          <div>
            <span className="eyebrow">STUDENT WORKSPACE</span>
            <h1>Service Requests</h1>
            <p>
              Submit and manage your university service requests.
            </p>
          </div>

          <div className="header-badge">
            <span className="online-dot" />
            System online
          </div>
        </header>

        <section className="stats-grid">
          <div className="stat-card">
            <span>Total requests</span>
            <strong>{requests.length}</strong>
            <small>All submitted requests</small>
          </div>

          <div className="stat-card">
            <span>Pending</span>
            <strong>{pendingCount}</strong>
            <small>Waiting for attention</small>
          </div>

          <div className="stat-card">
            <span>In progress</span>
            <strong>{activeCount}</strong>
            <small>Currently being handled</small>
          </div>
        </section>

        {error && (
          <div className="alert alert-error" role="alert">
            {error}
          </div>
        )}

        {notice && (
          <div className="alert alert-success" role="status">
            {notice}
          </div>
        )}

        <div className="workspace-grid">
          <section className="panel form-panel">
            <div className="panel-heading">
              <div className="section-icon">＋</div>
              <div>
                <h2>
                  {editing ? "Edit request" : "Create a request"}
                </h2>
                <p>
                  {editing
                    ? `Updating request #${editingId}`
                    : "Tell us what support you need."}
                </p>
              </div>
            </div>

            <form onSubmit={handleSubmit}>
              <label htmlFor="title">Request title</label>
              <input
                id="title"
                type="text"
                placeholder="e.g. Projector not working"
                value={form.title}
                onChange={(e) =>
                  handleInputChange("title", e.target.value)
                }
                minLength={3}
                maxLength={120}
                required
              />

              <label htmlFor="description">Description</label>
              <textarea
                id="description"
                placeholder="Describe the problem in detail..."
                value={form.description}
                onChange={(e) =>
                  handleInputChange("description", e.target.value)
                }
                minLength={5}
                maxLength={2000}
                rows={5}
                required
              />

              <label htmlFor="category">Category</label>
              <select
                id="category"
                value={form.category}
                onChange={(e) =>
                  handleInputChange("category", e.target.value)
                }
              >
                {categories.map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>

              {editing && (
                <>
                  <label htmlFor="status">Request status</label>
                  <select
                    id="status"
                    value={form.status}
                    onChange={(e) =>
                      handleInputChange("status", e.target.value)
                    }
                  >
                    {statuses.map((status) => (
                      <option key={status} value={status}>
                        {status}
                      </option>
                    ))}
                  </select>
                </>
              )}

              <button
                className="primary-button"
                type="submit"
                disabled={saving}
              >
                {saving
                  ? "Saving..."
                  : editing
                    ? "Save changes"
                    : "Submit request"}
              </button>

              {editing && (
                <button
                  className="secondary-button"
                  type="button"
                  onClick={cancelEditing}
                  disabled={saving}
                >
                  Cancel editing
                </button>
              )}
            </form>

            <div className="form-tip">
              <strong>Before submitting</strong>
              <p>
                Provide a clear title and enough details to help
                university staff understand your request.
              </p>
            </div>
          </section>

          <section className="panel list-panel">
            <div className="panel-heading list-heading">
              <div>
                <h2>All requests</h2>
                <p>
                  {requests.length} request
                  {requests.length === 1 ? "" : "s"} found
                </p>
              </div>

              <span className="count-badge">{requests.length}</span>
            </div>

            {loading ? (
              <div className="empty-state">
                Loading service requests...
              </div>
            ) : requests.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">▤</div>
                <h3>No requests yet</h3>
                <p>
                  Your submitted service requests will appear here.
                </p>
              </div>
            ) : (
              <div className="request-list">
                {requests.map((request) => (
                  <button
                    type="button"
                    key={request.id}
                    className={`request-card ${
                      selected?.id === request.id ? "selected" : ""
                    }`}
                    onClick={() => void selectRequest(request.id)}
                  >
                    <div className="request-card-top">
                      <span className="request-id">
                        REQUEST #{request.id}
                      </span>

                      <span
                        className={`status-pill status-${request.status
                          .toLowerCase()
                          .replace(" ", "-")}`}
                      >
                        {request.status}
                      </span>
                    </div>

                    <h3>{request.title}</h3>

                    <p>{request.description}</p>

                    <div className="request-card-bottom">
                      <span>{request.category}</span>
                      <span>{formatDate(request.created_at)}</span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </section>
        </div>

        <section className="panel details-panel">
          <div className="panel-heading">
            <div>
              <h2>Request details</h2>
              <p>View the complete information of a request.</p>
            </div>
          </div>

          {detailLoading ? (
            <div className="empty-state">Loading request details...</div>
          ) : selected ? (
            <div className="details-content">
              <div className="details-main">
                <span className="request-id">
                  REQUEST #{selected.id}
                </span>
                <h2>{selected.title}</h2>
                <p>{selected.description}</p>
              </div>

              <div className="details-meta">
                <div>
                  <span>Category</span>
                  <strong>{selected.category}</strong>
                </div>

                <div>
                  <span>Status</span>
                  <strong>{selected.status}</strong>
                </div>

                <div>
                  <span>Created</span>
                  <strong>{formatDate(selected.created_at)}</strong>
                </div>

                <div>
                  <span>Last updated</span>
                  <strong>{formatDate(selected.updated_at)}</strong>
                </div>
              </div>

              <div className="details-actions">
                <button
                  className="secondary-button"
                  type="button"
                  onClick={() => startEditing(selected)}
                >
                  Edit request
                </button>

                <button
                  className="danger-button"
                  type="button"
                  onClick={() => void handleDelete()}
                >
                  Delete request
                </button>
              </div>
            </div>
          ) : (
            <div className="empty-state">
              Select a request from the list to see its details.
            </div>
          )}
        </section>

        <footer className="page-footer">
          CampusConnect · University Service Request Management
        </footer>
      </main>
    </div>
  )
}
