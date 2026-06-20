"use client";

import { useEffect, useState } from "react";

export interface DashboardPermissions {
  role: string;
  email: string | null;
  brand_id: string | null;
  store_id: string | null;
  permissions: {
    system_admin_panel: boolean;
    brand_dashboard: boolean;
    store_analytics: boolean;
    live_footfall: boolean;
    pos_transactions: boolean;
    crm_profiles: boolean;
    voice_queries: boolean;
    predictive_forecasts: boolean;
    alerts_engine: boolean;
    system_audit_logs: boolean;
    role_management: boolean;
    [key: string]: boolean; // Allow dynamic expansion
  };
}

export function useDashboardPermissions() {
  const [permissions, setPermissions] = useState<DashboardPermissions | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchPermissions() {
      try {
        setLoading(true);
        // Retrieve access token from localStorage (standard for this UI client setup)
        const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
        const headers: Record<string, string> = {
          "Content-Type": "application/json",
        };
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }

        const backendUrl = process.env.NEXT_PUBLIC_API_URL || "";
        const response = await fetch(`${backendUrl}/api/rbac/me`, {
          method: "GET",
          headers,
        });

        if (!response.ok) {
          if (response.status === 401) {
            throw new Error("Unauthorized: Bearer token is invalid or missing");
          }
          throw new Error(`Failed to fetch permissions: ${response.statusText}`);
        }

        const data: DashboardPermissions = await response.json();
        setPermissions(data);
      } catch (err: any) {
        setError(err.message || "An unknown error occurred");
      } finally {
        setLoading(false);
      }
    }

    fetchPermissions();
  }, []);

  const hasPermission = (permissionKey: keyof DashboardPermissions["permissions"]): boolean => {
    if (!permissions) return false;
    return !!permissions.permissions[permissionKey];
  };

  return {
    permissions,
    loading,
    error,
    hasPermission,
    isSuperAdmin: permissions?.role === "super_admin",
    isBrandAdmin: permissions?.role === "brand_admin",
    isStoreManager: permissions?.role === "store_manager",
    isStaffViewer: permissions?.role === "staff_viewer",
  };
}
