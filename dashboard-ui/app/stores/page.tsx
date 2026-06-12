"use client";

import { useMemo, useState } from "react";
import { Camera, Clock, Repeat, TrendingUp, Users } from "lucide-react";
import { PageShell } from "@/components/enterprise/PageShell";
import { FilterBar, FilterField, filterInputClass } from "@/components/enterprise/FilterBar";
import { KpiCard } from "@/components/enterprise/KpiCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { StoreTrendChart } from "@/components/charts/LazyStoreTrendChart";
import { useCachedQuery } from "@/hooks/useCachedQuery";
import {
  fetchCameraBreakdown,
  fetchDashboardOverview,
  fetchLiveVisitors,
} from "@/services/dashboard-api";
import { fetchCameras } from "@/services/multi-camera-analytics";
import { fetchConversionAnalytics } from "@/services/executive-api";
import { defaultDateRange, formatPct, formatSeconds } from "@/lib/utils";
import { formatNumber } from "@/utils/format";

export default function MultiStorePage() {
  const initial = defaultDateRange(30);
  const [fromDay, setFromDay] = useState(initial.from);
  const [toDay, setToDay] = useState(initial.to);
  const [storeId, setStoreId] = useState<string>("");
  const [cameraId, setCameraId] = useState<string>("");

  const { data, loading, error, refresh } = useCachedQuery({
    key: { page: "stores", fromDay, toDay, storeId, cameraId },
    fetcher: async () => {
      const [overview, live, conversion, cameras, cameraHealth] = await Promise.all([
        fetchDashboardOverview({
          from_day: fromDay,
          to_day: toDay,
          store_ids: storeId || undefined,
        }),
        fetchLiveVisitors(),
        fetchConversionAnalytics({ from_day: fromDay, to_day: toDay }),
        fetchCameras(),
        fetchCameraBreakdown({ store_id: storeId || undefined, days: 30 }),
      ]);
      return { overview, live, conversion, cameras, cameraHealth };
    },
  });

  const rankedStores = useMemo(
    () =>
      [...(data?.overview.stores ?? [])].sort(
        (a, b) => b.total_visitors - a.total_visitors
      ),
    [data]
  );

  const filteredCameras = useMemo(() => {
    const cams = data?.cameraHealth.cameras ?? [];
    return cameraId ? cams.filter((c) => c.camera_id === cameraId) : cams;
  }, [data, cameraId]);

  const summary = data?.overview.summary;

  return (
    <PageShell
      title="Multi-store dashboard"
      subtitle="Brand-wide analytics with store, camera, and date filters"
      loading={loading && !data}
      error={error}
      onRefresh={refresh}
      refreshing={loading}
    >
      {data && summary && (
        <>
          <FilterBar>
            <FilterField label="From">
              <input
                type="date"
                className={filterInputClass()}
                value={fromDay}
                onChange={(e) => setFromDay(e.target.value)}
              />
            </FilterField>
            <FilterField label="To">
              <input
                type="date"
                className={filterInputClass()}
                value={toDay}
                onChange={(e) => setToDay(e.target.value)}
              />
            </FilterField>
            <FilterField label="Store">
              <select
                className={filterInputClass()}
                value={storeId}
                onChange={(e) => setStoreId(e.target.value)}
              >
                <option value="">All stores</option>
                {data.overview.stores.map((s) => (
                  <option key={s.store_id} value={s.store_id}>
                    {s.store_id}
                  </option>
                ))}
              </select>
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
          </FilterBar>

          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
            <KpiCard title="Total visitors" value={formatNumber(summary.total_visitors)} icon={Users} />
            <KpiCard title="Repeat visitors" value={formatNumber(summary.repeat_visitors)} subtitle={formatPct(summary.repeat_ratio)} icon={Repeat} />
            <KpiCard title="Active now" value={formatNumber(data.live.count)} subtitle="Live in store" icon={TrendingUp} />
            <KpiCard title="Avg dwell" value={formatSeconds(summary.avg_dwell_seconds)} icon={Clock} />
            <KpiCard title="Conversion rate" value={formatPct(data.conversion.conversion_rate ?? 0)} subtitle="Visitor → purchase" icon={TrendingUp} />
            <KpiCard title="Stores" value={summary.store_count} subtitle={`${filteredCameras.length} cameras`} icon={Camera} />
          </section>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Store rankings</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-muted-foreground">
                      <th className="pb-2 pr-3">#</th>
                      <th className="pb-2 pr-3">Store</th>
                      <th className="pb-2 pr-3">Visitors</th>
                      <th className="pb-2 pr-3">Repeat %</th>
                      <th className="pb-2">Dwell</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rankedStores.map((s, i) => (
                      <tr key={s.store_id} className="border-b border-border/50">
                        <td className="py-2 pr-3 font-medium">{i + 1}</td>
                        <td className="py-2 pr-3">{s.store_id}</td>
                        <td className="py-2 pr-3">{formatNumber(s.total_visitors)}</td>
                        <td className="py-2 pr-3">{formatPct(s.repeat_ratio)}</td>
                        <td className="py-2">{formatSeconds(s.avg_dwell_seconds)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Camera health</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {filteredCameras.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No camera data for selection.</p>
                ) : (
                  filteredCameras.map((cam) => (
                    <div
                      key={cam.camera_id}
                      className="flex items-center justify-between rounded-lg border border-border px-3 py-2"
                    >
                      <div>
                        <p className="text-sm font-medium">{cam.name ?? cam.camera_id}</p>
                        <p className="text-xs text-muted-foreground">
                          {formatNumber(cam.total_visitors)} visitors · {formatSeconds(cam.avg_dwell_seconds)}
                        </p>
                      </div>
                      <Badge variant={cam.enabled ? "success" : "warning"}>
                        {cam.enabled ? "Online" : "Disabled"}
                      </Badge>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Visitor trend by store</CardTitle>
            </CardHeader>
            <CardContent>
              <StoreTrendChart
                data={rankedStores.map((s) => ({
                  day: s.store_id,
                  visitors: s.total_visitors,
                  repeat: s.repeat_visitors,
                }))}
              />
            </CardContent>
          </Card>
        </>
      )}
    </PageShell>
  );
}
