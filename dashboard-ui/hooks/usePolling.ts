"use client";

import axios from "axios";
import { useCallback, useEffect, useRef, useState } from "react";

const DEFAULT_INTERVAL = Number(
  process.env.NEXT_PUBLIC_POLL_INTERVAL_MS ?? 10000
);

export function usePolling<T>(
  fetcher: () => Promise<T>,
  intervalMs = DEFAULT_INTERVAL,
  enabled = true
) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const refresh = useCallback(async () => {
    try {
      const result = await fetcherRef.current();
      setData(result);
      setError(null);
    } catch (e: unknown) {
      let msg = "Failed to load data";
      if (axios.isAxiosError(e)) {
        if (e.code === "ECONNABORTED") msg = "API timeout — is the backend running on port 8000?";
        else if (e.code === "ERR_NETWORK" || !e.response)
          msg = "Cannot reach API — start: uvicorn backend_core.main:app --reload --port 8000";
        else msg = e.response?.data?.detail ?? e.message;
      } else if (e instanceof Error) {
        msg = e.message;
      }
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!enabled) return;
    refresh();
    const id = setInterval(refresh, intervalMs);
    return () => clearInterval(id);
  }, [refresh, intervalMs, enabled]);

  return { data, error, loading, refresh };
}
