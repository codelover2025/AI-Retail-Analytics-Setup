import { apiClient } from "./api";

export interface PlatformUser {
  id: string;
  email: string;
  role: string;
  brand_id?: string | null;
  store_id?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface AuditLogEntry {
  id: string;
  actor: string;
  action: string;
  resource?: string | null;
  created_at: string;
}

export const ROLES = [
  "super_admin",
  "brand_admin",
  "store_manager",
  "staff_viewer",
] as const;

export const PERMISSIONS_MATRIX: Record<string, string[]> = {
  super_admin: ["*"],
  brand_admin: ["dashboard", "reports", "integrations", "admin", "rbac.read"],
  store_manager: ["dashboard", "reports", "staff", "realtime", "heatmap"],
  staff_viewer: ["dashboard.read", "realtime.read"],
};

export async function fetchPlatformUsers(): Promise<PlatformUser[]> {
  const { data } = await apiClient.get<PlatformUser[]>("/api/rbac/users");
  return data;
}

export async function fetchAuditLogs(limit = 50): Promise<AuditLogEntry[]> {
  const { data } = await apiClient.get<AuditLogEntry[]>("/api/rbac/audit-logs", {
    params: { limit },
  });
  return data;
}
