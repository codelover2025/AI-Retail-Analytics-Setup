import axios, { type AxiosInstance } from "axios";

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
  if (apiKey) headers["X-API-Key"] = apiKey;
  if (brandSlug) headers["X-Brand-Slug"] = brandSlug;
  if (storeId) headers["X-Store-Id"] = storeId;

  return axios.create({
    baseURL,
    headers,
    timeout: 15000,
  });
}

export const apiClient = buildClient();
