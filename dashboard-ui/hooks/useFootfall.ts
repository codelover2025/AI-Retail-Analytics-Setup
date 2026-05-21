"use client";

import { fetchFootfall } from "@/services/analytics";
import { processFootfallCharts } from "@/utils/analytics-processors";
import {
  computeFootfallKpis,
  computeFootfallTrend,
} from "@analytics/footfall";
import { usePolling } from "./usePolling";

export function useFootfallAnalytics() {
  return usePolling(async () => {
    const footfall = await fetchFootfall();
    const charts = processFootfallCharts(footfall);
    return {
      raw: footfall,
      kpis: computeFootfallKpis(footfall),
      trend: computeFootfallTrend(footfall),
      ...charts,
    };
  });
}
