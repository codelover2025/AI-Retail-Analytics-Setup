import { apiClient } from "./api";
import type {
  AlertItem,
  FootfallResponse,
  LiveVisitorsResponse,
  RecognitionItem,
} from "./types";

export async function fetchLiveVisitors(): Promise<LiveVisitorsResponse> {
  const { data } = await apiClient.get<LiveVisitorsResponse>(
    "/api/live-visitors"
  );
  return data;
}

export async function fetchRecognitions(
  limit = 100
): Promise<RecognitionItem[]> {
  const { data } = await apiClient.get<RecognitionItem[]>(
    "/api/recognitions",
    { params: { limit } }
  );
  return data;
}

export async function fetchFootfall(
  fromDay?: string
): Promise<FootfallResponse> {
  const { data } = await apiClient.get<FootfallResponse>("/api/footfall", {
    params: fromDay ? { from_day: fromDay } : undefined,
  });
  return data;
}

export async function fetchAlerts(
  limit = 50,
  unacknowledgedOnly = false
): Promise<AlertItem[]> {
  const { data } = await apiClient.get<AlertItem[]>("/api/alerts", {
    params: { limit, unacknowledged_only: unacknowledgedOnly },
  });
  return data;
}

export async function fetchDashboardSnapshot() {
  const [live, recognitions, footfall, alerts] = await Promise.all([
    fetchLiveVisitors(),
    fetchRecognitions(50),
    fetchFootfall(),
    fetchAlerts(20),
  ]);
  return { live, recognitions, footfall, alerts };
}
