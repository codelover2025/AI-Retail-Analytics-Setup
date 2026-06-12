/**
 * Auth utilities — token storage, login/logout, JWT decode.
 * Uses localStorage for token persistence (httpOnly cookie approach
 * requires SSR changes; localStorage is sufficient for this SPA pattern).
 */

const TOKEN_KEY = "orzen_access_token";
const USER_KEY = "orzen_user";

export interface AuthUser {
  user_id: string | null;
  email: string | null;
  role: string;
  brand_id: string | null;
  store_id: string | null;
}

// ---------------------------------------------------------------------------
// Token storage
// ---------------------------------------------------------------------------

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

// ---------------------------------------------------------------------------
// JWT decode (no validation — server validates on every request)
// ---------------------------------------------------------------------------

function base64UrlDecode(str: string): string {
  const padded = str.replace(/-/g, "+").replace(/_/g, "/");
  const pad = padded.length % 4;
  const padded2 = pad ? padded + "=".repeat(4 - pad) : padded;
  try {
    return decodeURIComponent(
      atob(padded2)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
  } catch {
    return atob(padded2);
  }
}

export function decodeToken(token: string): AuthUser | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const payload = JSON.parse(base64UrlDecode(parts[1]));
    return {
      user_id: payload.user_id ?? null,
      email: payload.email ?? payload.sub ?? null,
      role: payload.role ?? "staff_viewer",
      brand_id: payload.brand_id ?? null,
      store_id: payload.store_id ?? null,
    };
  } catch {
    return null;
  }
}

export function isTokenExpired(token: string): boolean {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return true;
    const payload = JSON.parse(base64UrlDecode(parts[1]));
    if (!payload.exp) return false;
    return Date.now() / 1000 > payload.exp;
  } catch {
    return true;
  }
}

// ---------------------------------------------------------------------------
// Session helpers
// ---------------------------------------------------------------------------

export function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

export function storeUser(user: AuthUser): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getCurrentUser(): AuthUser | null {
  const token = getToken();
  if (!token || isTokenExpired(token)) {
    clearToken();
    return null;
  }
  return getStoredUser() ?? decodeToken(token);
}

// ---------------------------------------------------------------------------
// API login call
// ---------------------------------------------------------------------------

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginResult {
  access_token: string;
  token_type: string;
  role: string;
}

export async function loginWithCredentials(
  credentials: LoginCredentials
): Promise<AuthUser> {
  const baseUrl =
    typeof window !== "undefined" ? "/backend-api" : (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000");

  const response = await fetch(`${baseUrl}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? "Invalid credentials");
  }

  const result: LoginResult = await response.json();
  const user = decodeToken(result.access_token) ?? {
    user_id: null,
    email: credentials.email,
    role: result.role,
    brand_id: null,
    store_id: null,
  };

  setToken(result.access_token);
  storeUser(user);
  return user;
}

export function logout(): void {
  clearToken();
  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
}

// ---------------------------------------------------------------------------
// Role helpers
// ---------------------------------------------------------------------------

const ROLE_HIERARCHY = ["staff_viewer", "store_manager", "brand_admin", "super_admin"];

export function hasRole(userRole: string, requiredRole: string): boolean {
  return ROLE_HIERARCHY.indexOf(userRole) >= ROLE_HIERARCHY.indexOf(requiredRole);
}
