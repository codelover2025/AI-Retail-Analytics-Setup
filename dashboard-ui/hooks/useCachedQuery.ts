"use client";

import { cacheKey, getCached, setCached } from "@/lib/query-cache";
import { useCallback, useEffect, useRef, useState } from "react";

interface UseCachedQueryOptions<T> {
  key: Record<string, string | number | undefined>;
  fetcher: () => Promise<T>;
  ttlMs?: number;
  enabled?: boolean;
}

export function useCachedQuery<T>({
  key,
  fetcher,
  ttlMs = 60_000,
  enabled = true,
}: UseCachedQueryOptions<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const keyStr = cacheKey(key);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const refresh = useCallback(
    async (skipCache = false) => {
      if (!enabled) return;
      setLoading(true);
      setError(null);
      try {
        if (!skipCache) {
          const hit = getCached<T>(keyStr);
          if (hit !== null) {
            setData(hit);
            setLoading(false);
            return;
          }
        }
        const result = await fetcherRef.current();
        setCached(keyStr, result, ttlMs);
        setData(result);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Request failed");
      } finally {
        setLoading(false);
      }
    },
    [enabled, keyStr, ttlMs]
  );

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { data, loading, error, refresh: () => refresh(true) };
}
