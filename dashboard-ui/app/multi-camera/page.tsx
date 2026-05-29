"use client";

import { ErrorBanner } from "@/components/ErrorBanner";
import { Header } from "@/components/layout/Header";
import { LoadingState } from "@/components/LoadingState";
import { StatCard } from "@/components/StatCard";
import {
  useMultiCameraAnalytics,
  type CameraFilter,
} from "@/hooks/useMultiCameraAnalytics";
import { formatNumber } from "@/utils/format";
import {
  Activity,
  Camera,
  Clock,
  MapPin,
  Repeat,
  Users,
} from "lucide-react";
import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

function formatSeconds(sec: number): string {
  if (sec < 60) return `${Math.round(sec)}s`;
  const m = Math.floor(sec / 60);
  const s = Math.round(sec % 60);
  return `${m}m ${s}s`;
}

export default function MultiCameraPage() {
  const [cameraId, setCameraId] = useState<CameraFilter>("ALL");
  const {
    cameras,
    storeFootfall,
    cameraFootfall,
    dwell,
    zones,
    repeat,
    interactions,
    loading,
    error,
    refresh,
  } = useMultiCameraAnalytics(cameraId);

  const footfallChart = useMemo(() => {
    const src =
      cameraId === "ALL"
        ? storeFootfall?.points
        : cameraFootfall?.points ?? storeFootfall?.points;
    if (!src?.length) return [];
    return [...src]
      .reverse()
      .map((p) => ({
        day: p.day,
        visitors: p.total_visitors,
        repeat: p.repeat_visitors,
      }));
  }, [cameraId, storeFootfall, cameraFootfall]);

  const zoneChart = useMemo(
    () =>
      (zones?.zones ?? []).map((z) => ({
        name: z.zone_name,
        time: Math.round(z.total_time_spent),
        visits: z.visit_count,
      })),
    [zones]
  );

  const summary = cameraId === "ALL" ? storeFootfall?.summary : cameraFootfall?.summary ?? storeFootfall?.summary;

  return (
    <>
      <Header
        title="Multi-camera analytics"
        subtitle="Per-camera and store-wide footfall, dwell, zones, and interactions"
        onRefresh={refresh}
        refreshing={loading && !!storeFootfall}
      />
      <main className="flex-1 space-y-6 p-4 md:p-6">
        <section className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <label className="flex flex-col gap-1 text-sm text-slate-600">
            <span className="font-medium text-slate-800">Camera</span>
            <select
              className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              value={cameraId}
              onChange={(e) => setCameraId(e.target.value as CameraFilter)}
            >
              <option value="ALL">Store summary (all cameras)</option>
              {cameras.map((c) => (
                <option key={c.camera_id} value={c.camera_id}>
                  {c.name ?? c.camera_id}
                </option>
              ))}
            </select>
          </label>
          <p className="text-xs text-slate-500">
            {cameras.length} cameras · identities are not merged across cameras
          </p>
        </section>

        {error && <ErrorBanner message={error} onRetry={refresh} />}
        {loading && !storeFootfall && <LoadingState />}

        {summary && (
          <>
            <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard
                title="Total visitors"
                value={formatNumber(summary.total_visitors)}
                subtitle={cameraId === "ALL" ? "All cameras" : cameraId}
                icon={Users}
                accent="blue"
              />
              <StatCard
                title="Repeat visitors"
                value={formatNumber(summary.repeat_visitors)}
                subtitle={`${(summary.repeat_ratio * 100).toFixed(1)}% repeat ratio`}
                icon={Repeat}
                accent="green"
              />
              <StatCard
                title="Avg dwell"
                value={dwell ? formatSeconds(dwell.avg_dwell_seconds) : "—"}
                subtitle={
                  dwell
                    ? `p50 ${formatSeconds(dwell.p50_dwell_seconds)} · ${dwell.session_count} sessions`
                    : undefined
                }
                icon={Clock}
                accent="amber"
              />
              <StatCard
                title="Interactions"
                value={formatNumber(interactions?.total ?? 0)}
                subtitle="Staff–customer events"
                icon={Activity}
                accent="rose"
              />
            </section>

            {footfallChart.length > 0 && (
              <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-800">
                  <Camera className="h-4 w-4" />
                  Footfall trend
                </h2>
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={footfallChart}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="visitors"
                      name="Visitors"
                      stroke="#2563eb"
                      strokeWidth={2}
                      dot={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="repeat"
                      name="Repeat"
                      stroke="#16a34a"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </section>
            )}

            <section className="grid gap-6 lg:grid-cols-2">
              {zoneChart.length > 0 && (
                <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                  <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-800">
                    <MapPin className="h-4 w-4" />
                    Zone analytics
                  </h2>
                  <ResponsiveContainer width="100%" height={240}>
                    <BarChart data={zoneChart} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis type="number" tick={{ fontSize: 11 }} />
                      <YAxis
                        type="category"
                        dataKey="name"
                        width={100}
                        tick={{ fontSize: 10 }}
                      />
                      <Tooltip />
                      <Bar dataKey="time" name="Time (s)" fill="#6366f1" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {repeat && (
                <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                  <h2 className="mb-3 text-sm font-semibold text-slate-800">
                    Repeat vs new
                  </h2>
                  <ul className="space-y-2 text-sm text-slate-700">
                    <li className="flex justify-between border-b border-slate-100 py-2">
                      <span>New visitors</span>
                      <span className="font-medium">{formatNumber(repeat.new_visitors)}</span>
                    </li>
                    <li className="flex justify-between border-b border-slate-100 py-2">
                      <span>Repeat visitors</span>
                      <span className="font-medium">
                        {formatNumber(repeat.repeat_visitors)}
                      </span>
                    </li>
                    <li className="flex justify-between py-2">
                      <span>Repeat ratio</span>
                      <span className="font-medium text-brand-700">
                        {(repeat.repeat_ratio * 100).toFixed(1)}%
                      </span>
                    </li>
                  </ul>
                </div>
              )}
            </section>

            <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h2 className="mb-3 text-sm font-semibold text-slate-800">
                Recent interactions
              </h2>
              {!interactions?.items.length ? (
                <p className="text-sm text-slate-500">No interactions recorded.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-slate-200 text-slate-500">
                        <th className="py-2 pr-4 font-medium">Time</th>
                        <th className="py-2 pr-4 font-medium">Camera</th>
                        <th className="py-2 pr-4 font-medium">Customer</th>
                        <th className="py-2 font-medium">Employee</th>
                      </tr>
                    </thead>
                    <tbody>
                      {interactions.items.map((row) => (
                        <tr key={row.id} className="border-b border-slate-50">
                          <td className="py-2 pr-4 text-slate-700">
                            {new Date(row.timestamp).toLocaleString()}
                          </td>
                          <td className="py-2 pr-4">{row.camera_id}</td>
                          <td className="py-2 pr-4 font-mono text-xs">
                            {row.customer_id}
                          </td>
                          <td className="py-2 font-mono text-xs">{row.employee_id}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </>
        )}
      </main>
    </>
  );
}
