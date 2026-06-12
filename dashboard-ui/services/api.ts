import axios, { type AxiosInstance } from "axios";
import { getToken } from "@/lib/auth";

/** Browser uses Next rewrite proxy; server-side uses direct URL */
function resolveBaseUrl(): string {
  if (typeof window !== "undefined") {
    return "/backend-api";
  }
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
}

function buildClient(): AxiosInstance {
  const baseURL = resolveBaseUrl();
  const apiKey = process.env.NEXT_PUBLIC_API_KEY;
  const brandSlug = process.env.NEXT_PUBLIC_BRAND_SLUG;
  const storeId = process.env.NEXT_PUBLIC_STORE_ID;

  const headers: Record<string, string> = {};
  // Static headers for tenant context (used as fallback when no JWT)
  if (brandSlug) headers["X-Brand-Slug"] = brandSlug;
  if (storeId) headers["X-Store-Id"] = storeId;

  const client = axios.create({
    baseURL,
    headers,
    timeout: 15000,
  });

  // Request interceptor — inject JWT if available, otherwise fall back to API key
  client.interceptors.request.use((config) => {
    const token = getToken();
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
      // Remove API key header when JWT is present
      delete config.headers["X-API-Key"];
    } else if (apiKey) {
      config.headers["X-API-Key"] = apiKey;
    }
    return config;
  });

  // Response interceptor — on 401, clear session and redirect to login
  client.interceptors.response.use(
    (response) => response,
    (error) => {
      if (
        error.response?.status === 401 &&
        typeof window !== "undefined" &&
        !window.location.pathname.startsWith("/login")
      ) {
        // Clear stale token
        import("@/lib/auth").then(({ clearToken }) => {
          clearToken();
          // Clear cookie
          document.cookie = "orzen_auth=; path=/; max-age=0";
          window.location.href = "/login";
        });
      }
      return Promise.reject(error);
    }
  );

  return client;
}

export const apiClient = buildClient();

