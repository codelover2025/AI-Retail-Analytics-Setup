"use client";

import { DailyFootfallChart } from "@/charts/DailyFootfallChart";
import { HourlyFootfallChart } from "@/charts/HourlyFootfallChart";
import { ErrorBanner } from "@/components/ErrorBanner";
import { Header } from "@/components/layout/Header";
import { LoadingState } from "@/components/LoadingState";
import { StatCard } from "@/components/StatCard";
import { useFootfallAnalytics } from "@/hooks/useFootfall";
import { buildStoreReport } from "@analytics/reports";
import { fetchLiveVisitors, fetchRecognitions, fetchAlerts } from "@/services/analytics";
import { formatNumber } from "@/utils/format";
import { estimateDwellDistribution } from "@analytics/dwell_time";
import { BarChart3, TrendingDown, TrendingUp, Minus } from "lucide-react";
import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export default function AnalyticsPage() {
  const { data, error, loading, refresh } = useFootfallAnalytics();
  const [dwell, setDwell] = useState<{ label: string; count: number }[]>([]);
  const [highlights, setHighlights] = useState<string[]>([]);

  useEffect(() => {
    if (!data) return;
    (async () => {
      try {
        const [live, recs, alerts] = await Promise.all([
          fetchLiveVisitors(),
          fetchRecognitions(100),
          fetchAlerts(20),
        ]);
        const report = buildStoreReport(live, recs, data.raw, alerts);
        setHighlights(report.highlights);
        setDwell(estimateDwellDistribution(recs));
      } catch {
        /* optional enrichment */
      }
    })();
  }, [data]);

  const trend = data?.trend;
  const TrendIcon =
    trend?.direction === "up"
      ? TrendingUp
      : trend?.direction === "down"
        ? TrendingDown
        : Minus;

  const latestKpi = data?.kpis[data.kpis.length - 1];

  return (
    <>
      <Header
        title="Analytics"
        subtitle="Footfall trends and visitor patterns"
        onRefresh={refresh}
        refreshing={loading && !!data}
      />
      <main className="flex-1 space-y-6 p-4 md:p-6">
        {error && <ErrorBanner message={error} onRetry={refresh} />}
        {loading && !data && <LoadingState />}
        {data && (
          <>
            <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <StatCard
                title="Latest day — unique"
                value={formatNumber(latestKpi?.uniqueVisitors ?? 0)}
                subtitle={latestKpi?.day}
                icon={BarChart3}
                accent="blue"
              />
              <StatCard
                title="Latest day — detections"
                value={formatNumber(latestKpi?.totalDetections ?? 0)}
                subtitle={
                  latestKpi
                    ? `Avg ${latestKpi.avgDetectionsPerVisitor}/visitor`
                    : undefined
                }
                accent="green"
              />
              <StatCard
                title="Footfall trend"
                value={
                  trend
                    ? `${trend.percentChange > 0 ? "+" : ""}${trend.percentChange}%`
                    : "—"
                }
                subtitle={trend ? `vs prior day (${trend.direction})` : "Need 2+ days"}
                icon={TrendIcon}
                accent="amber"
              />
            </section>

            {highlights.length > 0 && (
              <section className="rounded-xl border border-brand-100 bg-brand-50 p-4">
                <h2 className="text-sm font-semibold text-brand-900">Summary</h2>
                <ul className="mt-2 list-inside list-disc text-sm text-brand-800">
                  {highlights.map((h, i) => (
                    <li key={i}>{h}</li>
                  ))}
                </ul>
              </section>
            )}

            <section className="grid gap-6 lg:grid-cols-2">
              <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <h2 className="mb-3 text-sm font-semibold text-slate-800">
                  Daily footfall
                </h2>
                <DailyFootfallChart data={data.dailyChart} />
              </div>
              <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <h2 className="mb-3 text-sm font-semibold text-slate-800">
                  Hourly recognitions
                </h2>
                <HourlyFootfallChart data={data.hourlyChart} />
              </div>
            </section>

            {dwell.length > 0 && (
              <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <h2 className="mb-1 text-sm font-semibold text-slate-800">
                  Visit gap distribution (proxy)
                </h2>
                <p className="mb-3 text-xs text-slate-500">
                  Estimated from recognition timestamps until zone dwell (Phase 2)
                </p>
                <ResponsiveContainer width="100%" height={220}>
                  <BarChart data={dwell}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </section>
            )}
          </>
        )}
      </main>
    </>
  );
}
