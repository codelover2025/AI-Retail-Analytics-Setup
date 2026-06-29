import { apiClient } from "./api";

export interface CameraListItem {
  camera_id: string; // maps to external_id
  id?: string; // UUID
  name?: string | null;
  enabled: boolean;
  rtsp_url?: string;
  frame_skip?: number | null;
}

export interface CameraCreateIn {
  external_id: string;
  name?: string | null;
  rtsp_url: string;
  enabled: boolean;
  frame_skip?: number | null;
  store_id?: string;
}

export interface CameraUpdateIn {
  name?: string | null;
  rtsp_url?: string;
  enabled?: boolean;
  frame_skip?: number | null;
}

export interface FootfallCameraPoint {
  day: string;
  camera_id?: string | null;
  total_visitors: number;
  repeat_visitors: number;
  repeat_ratio: number;
}

export interface FootfallCameraResponse {
  store_id: string;
  camera_id?: string | null;
  aggregated: boolean;
  points: FootfallCameraPoint[];
  summary: FootfallCameraPoint;
}

export interface DwellTimeStats {
  camera_id?: string | null;
  session_count: number;
  avg_dwell_seconds: number;
  min_dwell_seconds: number;
  max_dwell_seconds: number;
  p50_dwell_seconds: number;
}

export interface ZoneAnalyticsItem {
  zone_name: string;
  total_time_spent: number;
  visit_count: number;
  avg_time_spent: number;
}

export interface ZoneAnalyticsResponse {
  camera_id?: string | null;
  zones: ZoneAnalyticsItem[];
}

export interface RepeatAnalyticsResponse {
  camera_id?: string | null;
  total_visitors: number;
  repeat_visitors: number;
  new_visitors: number;
  repeat_ratio: number;
}

export interface InteractionItem {
  id: string;
  customer_id: string;
  employee_id: string;
  camera_id: string;
  timestamp: string;
}

export interface InteractionsResponse {
  camera_id?: string | null;
  total: number;
  items: InteractionItem[];
}

export async function fetchCameras(): Promise<CameraListItem[]> {
  const { data } = await apiClient.get<CameraListItem[]>("/api/cameras");
  return data;
}

export async function createCamera(payload: CameraCreateIn): Promise<CameraListItem> {
  const { data } = await apiClient.post<CameraListItem>("/api/cameras", payload);
  return data;
}

export async function updateCamera(id: string, payload: CameraUpdateIn): Promise<CameraListItem> {
  const { data } = await apiClient.patch<CameraListItem>(`/api/cameras/${id}`, payload);
  return data;
}

export async function deleteCamera(id: string): Promise<void> {
  await apiClient.delete(`/api/cameras/${id}`);
}


export async function fetchCameraFootfall(
  cameraId?: string,
  storeId?: string,
  days = 30
): Promise<FootfallCameraResponse> {
  const { data } = await apiClient.get<FootfallCameraResponse>("/api/footfall", {
    params: {
      camera_id: cameraId,
      store_id: storeId,
      days,
    },
  });
  return data;
}

export async function fetchStoreFootfallAll(days = 30): Promise<FootfallCameraResponse> {
  const { data } = await apiClient.get<FootfallCameraResponse>("/api/footfall", {
    params: { store_id: "ALL", days },
  });
  return data;
}

export async function fetchDwellTime(
  cameraId?: string,
  days = 7
): Promise<DwellTimeStats> {
  const { data } = await apiClient.get<DwellTimeStats>("/api/dwell-time", {
    params: { camera_id: cameraId, days },
  });
  return data;
}

export async function fetchZones(
  cameraId?: string,
  days = 7
): Promise<ZoneAnalyticsResponse> {
  const { data } = await apiClient.get<ZoneAnalyticsResponse>("/api/zones", {
    params: { camera_id: cameraId, days },
  });
  return data;
}

export async function fetchRepeatAnalytics(
  cameraId?: string,
  days = 30
): Promise<RepeatAnalyticsResponse> {
  const { data } = await apiClient.get<RepeatAnalyticsResponse>(
    "/api/repeat-analytics",
    { params: { camera_id: cameraId, days } }
  );
  return data;
}

export async function fetchInteractions(
  cameraId?: string,
  limit = 50
): Promise<InteractionsResponse> {
  const { data } = await apiClient.get<InteractionsResponse>("/api/interactions", {
    params: { camera_id: cameraId, limit },
  });
  return data;
}

export interface HeatmapCell {
  zone_name: string;
  intensity: number;
  total_time_spent: number;
  visit_count: number;
}

export interface HeatmapResponse {
  camera_id?: string | null;
  cells: HeatmapCell[];
}

export async function fetchHeatmap(
  cameraId?: string,
  days = 7
): Promise<HeatmapResponse> {
  const { data } = await apiClient.get<HeatmapResponse>("/api/heatmap", {
    params: { camera_id: cameraId, days },
  });
  return data;
}

export interface JourneyStep {
  camera_id: string;
  entry_time: string;
  exit_time?: string | null;
  dwell_time: number;
  journey_path: string[];
}

export interface JourneyResponse {
  person_id: string;
  cross_camera: boolean;
  steps: JourneyStep[];
}

export async function fetchJourney(
  personId: string,
  days = 30
): Promise<JourneyResponse> {
  const { data } = await apiClient.get<JourneyResponse>(
    `/api/journey/${personId}`,
    { params: { days } }
  );
  return data;
}


export interface MultiCameraSummaryResponse {
  cameras: CameraListItem[];
  store_footfall: FootfallCameraResponse;
  camera_footfall?: FootfallCameraResponse | null;
  dwell?: DwellTimeStats | null;
  zones?: ZoneAnalyticsResponse | null;
  repeat?: RepeatAnalyticsResponse | null;
  interactions?: InteractionsResponse | null;
  heatmap?: HeatmapResponse | null;
}

export async function fetchMultiCameraSummary(cameraId?: string): Promise<MultiCameraSummaryResponse> {
  const { data } = await apiClient.get<MultiCameraSummaryResponse>("/api/v1/analytics/multi-camera/summary", {
    params: cameraId && cameraId !== "ALL" ? { camera_id: cameraId } : undefined
  });
  return data;
}
