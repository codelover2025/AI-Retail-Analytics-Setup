import { apiClient } from "./api";
import { fetchInteractions, type InteractionsResponse } from "./multi-camera-analytics";

export interface HRMSEmployee {
  id: string;
  name: string;
  active: boolean;
  created_at: string;
}

export interface StaffPerformanceRow {
  employee_id: string;
  interaction_count: number;
  last_seen?: string;
}

export async function fetchHRMSEmployees(): Promise<HRMSEmployee[]> {
  const { data } = await apiClient.get<HRMSEmployee[]>("/api/hrms/employees");
  return data;
}

export async function syncHRMSEmployees() {
  const { data } = await apiClient.post("/api/hrms/sync/employees");
  return data as { synced: number; total_from_hrms: number };
}

export async function syncHRMSAttendance(syncDate?: string) {
  const { data } = await apiClient.post("/api/hrms/sync/attendance", null, {
    params: syncDate ? { sync_date: syncDate } : undefined,
  });
  return data as { date: string; records_from_hrms: number; saved: number };
}

export async function fetchStaffInteractions(cameraId?: string): Promise<InteractionsResponse> {
  return fetchInteractions(cameraId, 200);
}

export async function buildStaffPerformance(): Promise<StaffPerformanceRow[]> {
  const interactions = await fetchStaffInteractions();
  const counts = new Map<string, { count: number; last: string }>();
  for (const ix of interactions.items) {
    const cur = counts.get(ix.employee_id) ?? { count: 0, last: ix.timestamp };
    counts.set(ix.employee_id, {
      count: cur.count + 1,
      last: ix.timestamp > cur.last ? ix.timestamp : cur.last,
    });
  }
  return [...counts.entries()]
    .map(([employee_id, v]) => ({
      employee_id,
      interaction_count: v.count,
      last_seen: v.last,
    }))
    .sort((a, b) => b.interaction_count - a.interaction_count);
}
