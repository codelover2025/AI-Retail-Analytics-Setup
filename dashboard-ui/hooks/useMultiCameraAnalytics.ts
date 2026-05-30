"use client";

import { useCallback, useEffect, useState } from "react";
import {
  fetchCameras,
  fetchCameraFootfall,
  fetchDwellTime,
  fetchInteractions,
  fetchRepeatAnalytics,
  fetchStoreFootfallAll,
  fetchHeatmap,
  fetchZones,
  type CameraListItem,
  type DwellTimeStats,
  type FootfallCameraResponse,
  type HeatmapResponse,
  type InteractionsResponse,
  type RepeatAnalyticsResponse,
  type ZoneAnalyticsResponse,
} from "@/services/multi-camera-analytics";

export type CameraFilter = "ALL" | string;

export function useMultiCameraAnalytics(cameraId: CameraFilter) {
  const [cameras, setCameras] = useState<CameraListItem[]>([]);
  const [storeFootfall, setStoreFootfall] = useState<FootfallCameraResponse | null>(
    null
  );
  const [cameraFootfall, setCameraFootfall] =
    useState<FootfallCameraResponse | null>(null);
  const [dwell, setDwell] = useState<DwellTimeStats | null>(null);
  const [zones, setZones] = useState<ZoneAnalyticsResponse | null>(null);
  const [repeat, setRepeat] = useState<RepeatAnalyticsResponse | null>(null);
  const [interactions, setInteractions] = useState<InteractionsResponse | null>(
    null
  );
  const [heatmap, setHeatmap] = useState<HeatmapResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const camList = await fetchCameras();
      setCameras(camList);

      const camParam = cameraId === "ALL" ? undefined : cameraId;
      const [storeFf, camFf, dwellStats, zoneStats, repeatStats, ix, hm] =
        await Promise.all([
          fetchStoreFootfallAll(),
          camParam ? fetchCameraFootfall(camParam) : Promise.resolve(null),
          fetchDwellTime(camParam),
          fetchZones(camParam),
          fetchRepeatAnalytics(camParam),
          fetchInteractions(camParam, 30),
          fetchHeatmap(camParam),
        ]);

      setStoreFootfall(storeFf);
      setCameraFootfall(camFf);
      setDwell(dwellStats);
      setZones(zoneStats);
      setRepeat(repeatStats);
      setInteractions(ix);
      setHeatmap(hm);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load analytics");
    } finally {
      setLoading(false);
    }
  }, [cameraId]);

  useEffect(() => {
    load();
  }, [load]);

  return {
    cameras,
    storeFootfall,
    cameraFootfall,
    dwell,
    zones,
    repeat,
    interactions,
    heatmap,
    loading,
    error,
    refresh: load,
  };
}
