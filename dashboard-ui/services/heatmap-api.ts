import { apiClient } from "./api";

export interface HeatmapCell {
  zone_name?: string;
  hour?: number;
  store_id?: string;
  intensity: number;
  value?: number;
  label?: string;
}

export interface HeatmapResponse {
  store_id: string;
  camera_id?: string | null;
  heatmap_type: string;
  cells: HeatmapCell[];
  max_intensity: number;
}

export async function fetchZoneHeatmap(params?: {
  store_id?: string;
  camera_id?: string;
  days?: number;
}): Promise<HeatmapResponse> {
  const { data } = await apiClient.get<HeatmapResponse>("/api/heatmap/zone", { params });
  return data;
}

export async function fetchOccupancyHeatmap(params?: {
  store_id?: string;
  camera_id?: string;
  days?: number;
}): Promise<HeatmapResponse> {
  const { data } = await apiClient.get<HeatmapResponse>("/api/heatmap/occupancy", { params });
  return data;
}

export async function fetchDwellHeatmap(params?: {
  store_id?: string;
  camera_id?: string;
  days?: number;
}): Promise<HeatmapResponse> {
  const { data } = await apiClient.get<HeatmapResponse>("/api/heatmap/dwell", { params });
  return data;
}

export async function fetchHourlyHeatmap(params?: {
  store_id?: string;
  camera_id?: string;
  zone_name?: string;
  days?: number;
}): Promise<HeatmapResponse> {
  const { data } = await apiClient.get<HeatmapResponse>("/api/heatmap/hourly", { params });
  return data;
}
