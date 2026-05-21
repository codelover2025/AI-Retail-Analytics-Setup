"use client";

import { fetchAlerts } from "@/services/analytics";
import { usePolling } from "./usePolling";

export function useAlerts(limit = 50) {
  return usePolling(() => fetchAlerts(limit));
}
