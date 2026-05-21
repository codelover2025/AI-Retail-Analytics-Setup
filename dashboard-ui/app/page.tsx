"use client";

import { AlertNotification } from "@/components/AlertNotification";
import { ErrorBanner } from "@/components/ErrorBanner";
import { Header } from "@/components/layout/Header";
import { LoadingState } from "@/components/LoadingState";
import { StatCard } from "@/components/StatCard";
import { HourlyFootfallChart } from "@/charts/HourlyFootfallChart";
import { RecognitionBreakdownChart } from "@/charts/RecognitionBreakdownChart";
import { useDashboard } from "@/hooks/useDashboard";
import { formatDateTime, formatNumber } from "@/utils/format";
import {
  Activity,
  Bell,
  Footprints,
  UserPlus,
  Users,
} from "lucide-react";

export default function DashboardPage() {
  const { data, error, loading, refresh } = useDashboard();

  return (
    <>
      <Header
        title="Dashboard"
        subtitle="Live store analytics"
        onRefresh={refresh}
        refreshing={loading && !!data}
      />
      <main className="flex-1 space-y-6 p-4 md:p-6">
        {error && <ErrorBanner message={error} onRetry={refresh} />}
        {loading && !data && !error && <LoadingState />}
        {!loading && !data && !error && (
          <p className="text-sm text-slate-500">Waiting for data…</p>
        )}
        {data && (
          <>
            <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard
                title="Live in store"
                value={formatNumber(data.kpis.liveCount)}
                subtitle={`Updated ${formatDateTime(data.kpis.liveUpdatedAt)}`}
                icon={Users}
                accent="blue"
              />
              <StatCard
                title="Today — unique"
                value={formatNumber(data.kpis.todayUniqueVisitors)}
                subtitle="Daily footfall"
                icon={Footprints}
                accent="green"
              />
              <StatCard
                title="Recognitions (24h)"
                value={formatNumber(data.kpis.recognitionCount24h)}
                subtitle={`${data.kpis.newVisitors24h} new · ${data.kpis.repeatVisitors24h} repeat`}
                icon={UserPlus}
                accent="amber"
              />
              <StatCard
                title="Alerts"
                value={formatNumber(data.kpis.alertCount)}
                subtitle={
                  data.kpis.vipCount24h > 0
                    ? `${data.kpis.vipCount24h} VIP (24h)`
                    : "From API"
                }
                icon={Bell}
                accent="rose"
              />
            </section>

            <section className="grid gap-6 lg:grid-cols-3">
              <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm lg:col-span-2">
                <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-800">
                  <Activity className="h-4 w-4 text-brand-600" />
                  Hourly activity
                </h2>
                <HourlyFootfallChart data={data.hourlyChart} />
              </div>
              <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <h2 className="mb-3 text-sm font-semibold text-slate-800">
                  Visitor mix (24h)
                </h2>
                <RecognitionBreakdownChart
                  data={data.recognitionBreakdown.map((r) => ({
                    label: r.label,
                    count: r.count,
                  }))}
                />
              </div>
            </section>

            <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h2 className="mb-3 text-sm font-semibold text-slate-800">
                Recent alerts
              </h2>
              <AlertNotification alerts={data.recentAlerts} />
            </section>
          </>
        )}
      </main>
    </>
  );
}
