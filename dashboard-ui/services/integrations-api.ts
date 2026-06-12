import { apiClient } from "./api";

export interface SubsystemHealth {
  status: string;
  provider?: string;
  type?: string;
  error?: string;
}

export interface DetailedHealth {
  status: string;
  version: string;
  uptime_seconds: number;
  subsystems: Record<string, SubsystemHealth>;
}

export async function fetchDetailedHealth(): Promise<DetailedHealth> {
  const { data } = await apiClient.get<DetailedHealth>("/api/v1/health/detailed");
  return data;
}

export async function triggerPOSSync(storeId: string, fromDate: string) {
  const { data } = await apiClient.post("/api/pos/sync", null, {
    params: { store_id: storeId, from_date: fromDate },
  });
  return data;
}

export async function triggerCRMLookup(visitorId: string) {
  const { data } = await apiClient.get(`/api/crm/customers/${visitorId}`);
  return data;
}
