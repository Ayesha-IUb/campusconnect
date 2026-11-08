import type {
  Profile,
  RequestFormValues,
  ServiceRequest,
  Session,
  SignupResult,
} from "../types"

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY

function getErrorMessage(data: unknown, fallback: string): string {
  if (data && typeof data === "object") {
    const payload = data as Record<string, unknown>
    for (const key of ["detail", "msg", "message", "error_description", "error"]) {
      if (typeof payload[key] === "string") return payload[key] as string
    }
  }
  return fallback
}

async function authRequest<T>(path: string, body: object): Promise<T> {
  if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
    throw new Error(
      "Authentication is not configured. Add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to Vercel.",
    )
  }

  const response = await fetch(`${SUPABASE_URL}/auth/v1/${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      apikey: SUPABASE_ANON_KEY,
    },
    body: JSON.stringify(body),
  })

  const data: unknown = await response.json().catch(() => null)
  if (!response.ok) throw new Error(getErrorMessage(data, "Authentication failed."))
  return data as T
}

async function apiRequest<T>(
  endpoint: string,
  session: Session,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(endpoint, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${session.access_token}`,
      ...options.headers,
    },
  })

  const data: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(getErrorMessage(data, `Request failed (${response.status})`))
  }
  return data as T
}

export function signUp(email: string, password: string, fullName: string): Promise<SignupResult> {
  return authRequest<SignupResult>("signup", {
    email,
    password,
    data: { full_name: fullName },
  })
}

export function signIn(email: string, password: string): Promise<Session> {
  return authRequest<Session>("token?grant_type=password", { email, password })
}

export function resendConfirmation(email: string): Promise<unknown> {
  return authRequest<unknown>("resend", {
    type: "signup",
    email: email.trim(),
    options: { emailRedirectTo: "https://campusconnect-two-ivory.vercel.app" },
  })
}

export async function signOut(session: Session): Promise<void> {
  if (!SUPABASE_URL || !SUPABASE_ANON_KEY) return
  await fetch(`${SUPABASE_URL}/auth/v1/logout`, {
    method: "POST",
    headers: {
      apikey: SUPABASE_ANON_KEY,
      Authorization: `Bearer ${session.access_token}`,
    },
  })
}

export function getProfile(session: Session): Promise<Profile> {
  return apiRequest<Profile>("/api/me", session)
}

export function getRequests(session: Session): Promise<ServiceRequest[]> {
  return apiRequest<ServiceRequest[]>("/api/requests", session)
}

export function getRequest(id: number, session: Session): Promise<ServiceRequest> {
  return apiRequest<ServiceRequest>(`/api/requests/${id}`, session)
}

export function createRequest(
  payload: Pick<RequestFormValues, "title" | "description" | "category">,
  session: Session,
): Promise<ServiceRequest> {
  return apiRequest<ServiceRequest>("/api/requests", session, {
    method: "POST",
    body: JSON.stringify(payload),
  })
}

export function updateRequest(
  id: number,
  payload: RequestFormValues,
  session: Session,
): Promise<ServiceRequest> {
  return apiRequest<ServiceRequest>(`/api/requests/${id}`, session, {
    method: "PUT",
    body: JSON.stringify(payload),
  })
}

export async function deleteRequest(id: number, session: Session): Promise<void> {
  await apiRequest<{ message: string; id: number }>(
    `/api/requests/${id}`,
    session,
    { method: "DELETE" },
  )
}
