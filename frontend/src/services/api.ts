import type { Session } from "../types";

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL;
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY;

async function readResponse(response: Response): Promise<any> {
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const message = data?.detail || data?.msg || data?.message || data?.error_description || `Request failed (${response.status})`;
    throw new Error(String(message));
  }
  return data;
}

// Signup/login now go through FastAPI; refresh tokens stay in an HttpOnly cookie.
export async function authRequest(path: string, body: object): Promise<any> {
  if (path === "resend") {
    if (!SUPABASE_URL || !SUPABASE_ANON_KEY) throw new Error("Email confirmation is not configured.");
    const response = await fetch(`${SUPABASE_URL}/auth/v1/resend`, {
      method: "POST",
      headers: { "Content-Type": "application/json", apikey: SUPABASE_ANON_KEY },
      body: JSON.stringify(body),
    });
    return readResponse(response);
  }

  const endpoint = path === "signup" ? "/api/auth/signup" : "/api/auth/login";
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  });
  return readResponse(response);
}

function storeSession(session: Session): void {
  try {
    localStorage.setItem("campusconnect_session", JSON.stringify(session));
  } catch {
    // The current request can still complete if browser storage is unavailable.
  }
}

export async function apiRequest<T>(
  endpoint: string,
  session: Session,
  options: RequestInit = {},
): Promise<T> {
  const send = (token: string) => fetch(endpoint, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
      Authorization: `Bearer ${token}`,
    },
  });

  let response = await send(session.access_token);

  if (response.status === 401 && !endpoint.startsWith("/api/auth/refresh")) {
    const refreshResponse = await fetch("/api/auth/refresh", {
      method: "POST",
      credentials: "include",
    });
    if (!refreshResponse.ok) {
      try { localStorage.removeItem("campusconnect_session"); } catch { /* ignore */ }
      throw new Error("Your session expired. Please sign in again.");
    }
    const refreshed = await readResponse(refreshResponse);
    session.access_token = refreshed.access_token;
    session.session_id = refreshed.session_id;
    storeSession(session);
    response = await send(session.access_token);
  }

  return readResponse(response) as Promise<T>;
}

export async function logoutRequest(_session?: Session): Promise<void> {
  try {
    await fetch("/api/auth/logout", { method: "POST", credentials: "include" });
  } finally {
    try { localStorage.removeItem("campusconnect_session"); } catch { /* ignore */ }
  }
}

export async function downloadCsv(session: Session, kind: string, filters: Record<string, string> = {}): Promise<void> {
  const query = new URLSearchParams(Object.entries(filters).filter(([, value]) => Boolean(value)));
  const suffix = query.toString() ? `?${query.toString()}` : "";
  const response = await fetch(`/api/admin/export/${encodeURIComponent(kind)}${suffix}`, {
    credentials: "include",
    headers: { Authorization: `Bearer ${session.access_token}` },
  });
  const blob = await response.blob();
  if (!response.ok) {
    const text = await blob.text().catch(() => "");
    throw new Error(text || `Export failed (${response.status})`);
  }
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `campusconnect-${kind}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}
