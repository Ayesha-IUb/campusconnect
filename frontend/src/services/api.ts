import type { Session } from "../types"

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY

// Authentication API
export async function authRequest(
  path: string,
  body: object
): Promise<any> {
  if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
    throw new Error("Authentication is not configured.")
  }

  const response = await fetch(`${SUPABASE_URL}/auth/v1/${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      apikey: SUPABASE_ANON_KEY,
    },
    body: JSON.stringify(body),
  })

  const data = await response.json()

  if (!response.ok) {
    throw new Error(
      data.msg ||
      data.message ||
      data.error_description ||
      data.error ||
      "Authentication failed."
    )
  }

  return data
}

// Main backend API
export async function apiRequest<T>(
  endpoint: string,
  session: Session,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(endpoint, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${session.access_token}`,
      ...options.headers,
    },
  })

  const data = await response.json().catch(() => null)

  if (!response.ok) {
    const message =
      typeof data === "object" && data && "detail" in data
        ? String(data.detail)
        : `Request failed (${response.status})`

    throw new Error(message)
  }

  return data as T
}

// Logout API
export function logoutRequest(session: Session): void {
  if (!SUPABASE_URL || !SUPABASE_ANON_KEY) return

  void fetch(`${SUPABASE_URL}/auth/v1/logout`, {
    method: "POST",
    headers: {
      apikey: SUPABASE_ANON_KEY,
      Authorization: `Bearer ${session.access_token}`,
    },
  })
}