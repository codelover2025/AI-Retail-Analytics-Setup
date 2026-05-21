"use client";

import { fetchRecognitions } from "@/services/analytics";
import { usePolling } from "./usePolling";

export function useRecognitions(limit = 100) {
  return usePolling(() => fetchRecognitions(limit));
}
