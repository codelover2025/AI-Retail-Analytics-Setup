"use client";

import { fetchDashboardSnapshot } from "@/services/analytics";
import { buildDashboardSummary } from "@/utils/analytics-processors";
import { usePolling } from "./usePolling";

export function useDashboard() {
  return usePolling(async () => {
    const snapshot = await fetchDashboardSnapshot();
    return buildDashboardSummary(
      snapshot.live,
      snapshot.recognitions,
      snapshot.footfall,
      snapshot.alerts
    );
  });
}
