// Single source of truth for talking to the FastAPI backend: token storage,
// a typed fetch wrapper, and the request/response shapes mirroring the
// backend's Pydantic schemas. Page components should import from here
// rather than calling fetch() directly, so auth handling and error shape
// stay consistent across the app.

const TOKEN_KEY = "pesquei_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export function isLoggedIn(): boolean {
  return !!getToken();
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

/**
 * Fetch wrapper used for every backend call. Attaches the bearer token if
 * one is present, redirects to /login on a 401, and throws ApiError (with
 * the backend's `detail` message when available) on any other non-2xx
 * response. Returns `undefined` for a 204 No Content response.
 */
export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(path, { ...options, headers });

  if (response.status === 401) {
    clearToken();
    window.location.href = "/login";
    throw new ApiError(401, "Unauthorized");
  }

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") {
        detail = body.detail;
      }
    } catch {
      // response wasn't JSON — fall back to statusText
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

// ---- Types mirroring backend Pydantic schemas (schemas/*.py) ----

export interface User {
  id: number;
  username: string;
  email: string;
  created_at: string;
}

export interface Lure {
  id: number;
  user_id: number;
  name: string | null;
  weight: number | null;
  type: string | null;
  color: string | null;
  brand: string | null;
  model: string | null;
  size: number | null;
}

export interface LureCreate {
  name?: string;
  weight?: number;
  type?: string;
  color?: string;
  brand?: string;
  model?: string;
  size?: number;
}

export interface Catch {
  id: number;
  user_id: number;
  date_caught: string;
  species: string | null;
  weight: number | null;
  length: number | null;
  latitude: number | null;
  longitude: number | null;
  lure_id: number | null;
  depth: number | null;
  notes: string | null;
}

export interface CatchCreate {
  date_caught: string;
  species?: string;
  weight?: number;
  length?: number;
  latitude?: number;
  longitude?: number;
  lure_id?: number;
  depth?: number;
  notes?: string;
}

// ---- Auth ----

export function register(username: string, email: string, password: string): Promise<User> {
  return apiFetch<User>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, email, password }),
  });
}

export async function login(username: string, password: string): Promise<void> {
  const body = new URLSearchParams({ username, password });
  const data = await apiFetch<{ access_token: string; token_type: string }>("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  setToken(data.access_token);
}

// ---- Lures ----

export function listLures(): Promise<Lure[]> {
  return apiFetch<Lure[]>("/lure/");
}

export function createLure(data: LureCreate): Promise<Lure> {
  return apiFetch<Lure>("/lure/", { method: "POST", body: JSON.stringify(data) });
}

// ---- Catches ----

export function listCatches(): Promise<Catch[]> {
  return apiFetch<Catch[]>("/catch/");
}

export function createCatch(data: CatchCreate): Promise<Catch> {
  return apiFetch<Catch>("/catch/", { method: "POST", body: JSON.stringify(data) });
}
