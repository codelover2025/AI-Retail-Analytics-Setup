import { apiClient } from "./api";

export interface DashboardSummary {
  total_visitors: number;
  repeat_visitors: number;
  new_visitors: number;
  avg_dwell_seconds: number;
  staff_interactions: number;
  repeat_ratio: number;
  store_count: number;
}

export interface StoreMetric {
  store_id: string;
  total_visitors: number;
  repeat_visitors: number;
  new_visitors: number;
  repeat_ratio: number;
  avg_dwell_seconds: number;
  staff_interactions: number;
  top_zone?: string | null;
  zone_count?: number;
  rank?: number;
  vs_best_pct?: number;
}

export interface DashboardOverview {
  brand_id: string;
  from_day: string;
  to_day: string;
  summary: DashboardSummary;
  stores: StoreMetric[];
  generated_at: string;
}

export interface CameraMetric {
  camera_id: string;
  name?: string | null;
  enabled: boolean;
  total_visitors: number;
  repeat_visitors: number;
  avg_dwell_seconds: number;
  top_zone?: string | null;
}

export interface PaginatedStores {
  items: StoreMetric[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export async function fetchDashboardOverview(params: {
  from_day?: string;
  to_day?: string;
  store_ids?: string;
}): Promise<DashboardOverview> {
  const { data } = await apiClient.get<DashboardOverview>("/api/dashboard/overview", { params });
  return data;
}

export async function fetchDashboardStores(params: {
  from_day?: string;
  to_day?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
}): Promise<PaginatedStores> {
  const { data } = await apiClient.get<PaginatedStores>("/api/dashboard/stores", { params });
  return data;
}

export async function fetchStoreComparison(
  storeIds: string[],
  params?: { from_day?: string; to_day?: string }
) {
  const { data } = await apiClient.get("/api/dashboard/comparison", {
    params: { store_ids: storeIds.join(","), ...params },
  });
  return data as { stores: StoreMetric[]; from_day: string; to_day: string };
}

export async function fetchCameraBreakdown(params: {
  store_id?: string;
  from_day?: string;
  to_day?: string;
  days?: number;
}) {
  const { data } = await apiClient.get<{ cameras: CameraMetric[]; store_id: string }>(
    "/api/dashboard/cameras",
    { params }
  );
  return data;
}

export async function fetchLiveVisitors() {
  const { data } = await apiClient.get<{ count: number; timestamp: string }>("/api/live-visitors");
  return data;
}
