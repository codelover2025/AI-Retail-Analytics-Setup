"use client";

import { useState } from "react";
import { PageShell } from "@/components/enterprise/PageShell";
import { FilterBar, FilterField, filterInputClass } from "@/components/enterprise/FilterBar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LazyHeatmapGrid } from "@/components/charts/LazyHeatmapGrid";
import { useCachedQuery } from "@/hooks/useCachedQuery";
import {
  fetchDwellHeatmap,
  fetchHourlyHeatmap,
  fetchOccupancyHeatmap,
  fetchZoneHeatmap,
} from "@/services/heatmap-api";
import { fetchCameras } from "@/services/multi-camera-analytics";

type HeatmapMode = "zone" | "occupancy" | "dwell" | "hourly";

export default function HeatmapPage() {
  const [mode, setMode] = useState<HeatmapMode>("zone");
  const [cameraId, setCameraId] = useState("");
  const [days, setDays] = useState(7);

  const { data, loading, error, refresh } = useCachedQuery({
    key: { page: "heatmap", mode, cameraId, days },
    fetcher: async () => {
      const params = { camera_id: cameraId || undefined, days };
      const [heatmap, cameras] = await Promise.all([
        mode === "zone"
          ? fetchZoneHeatmap(params)
          : mode === "occupancy"
            ? fetchOccupancyHeatmap(params)
            : mode === "dwell"
              ? fetchDwellHeatmap(params)
              : fetchHourlyHeatmap(params),
        fetchCameras(),
      ]);
      return { heatmap, cameras };
    },
  });

  return (
    <PageShell
      title="Heatmap visualization"
      subtitle="Zone occupancy, dwell density, and hourly patterns"
      loading={loading && !data}
      error={error}
      onRefresh={refresh}
      refreshing={loading}
    >
      {data && (
        <>
          <FilterBar>
            <FilterField label="View">
              <div className="flex flex-wrap gap-2">
                {(
                  [
                    ["zone", "Zone dwell"],
                    ["occupancy", "Occupancy"],
                    ["dwell", "Dwell"],
                    ["hourly", "Hourly"],
                  ] as const
                ).map(([id, label]) => (
                  <Button
                    key={id}
                    size="sm"
                    variant={mode === id ? "default" : "outline"}
                    onClick={() => setMode(id)}
                  >
                    {label}
                  </Button>
                ))}
              </div>
            </FilterField>
            <FilterField label="Camera">
              <select
                className={filterInputClass()}
                value={cameraId}
                onChange={(e) => setCameraId(e.target.value)}
              >
                <option value="">All cameras</option>
                {data.cameras.map((c) => (
                  <option key={c.camera_id} value={c.camera_id}>
                    {c.name ?? c.camera_id}
                  </option>
                ))}
              </select>
            </FilterField>
            <FilterField label="Days">
              <input
                type="number"
                min={1}
                max={90}
                className={filterInputClass()}
                value={days}
                onChange={(e) => setDays(Number(e.target.value))}
              />
            </FilterField>
          </FilterBar>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">
                {mode === "zone" && "Store floor — zone dwell density"}
                {mode === "occupancy" && "Zone occupancy frequency"}
                {mode === "dwell" && "Average dwell heatmap"}
                {mode === "hourly" && "Hourly visitor distribution"}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <LazyHeatmapGrid
                cells={data.heatmap.cells}
                maxIntensity={data.heatmap.max_intensity}
              />
            </CardContent>
          </Card>

          <p className="text-xs text-muted-foreground">
            Store: {data.heatmap.store_id}
            {data.heatmap.camera_id ? ` · Camera: ${data.heatmap.camera_id}` : ""}
            · Intensity normalized 0–1
          </p>
        </>
      )}
    </PageShell>
  );
}
