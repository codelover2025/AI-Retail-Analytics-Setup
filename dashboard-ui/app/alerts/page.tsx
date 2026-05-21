"use client";

import { AlertNotification } from "@/components/AlertNotification";
import { DataTable } from "@/components/DataTable";
import { ErrorBanner } from "@/components/ErrorBanner";
import { Header } from "@/components/layout/Header";
import { LoadingState } from "@/components/LoadingState";
import { StatCard } from "@/components/StatCard";
import { useAlerts } from "@/hooks/useAlerts";
import type { AlertItem } from "@/services/types";
import { formatDateTime, formatNumber } from "@/utils/format";
import { AlertTriangle, Bell } from "lucide-react";

export default function AlertsPage() {
  const { data, error, loading, refresh } = useAlerts(100);

  const vipAlerts = data?.filter((a) => a.type.includes("vip")).length ?? 0;

  const columns = [
    {
      key: "time",
      header: "Time",
      render: (a: AlertItem) => formatDateTime(a.time),
    },
    {
      key: "type",
      header: "Type",
      render: (a: AlertItem) => (
        <span className="font-medium text-slate-800">{a.type}</span>
      ),
    },
    {
      key: "message",
      header: "Message",
      className: "max-w-md",
      render: (a: AlertItem) => (
        <span className="text-slate-600">{a.message}</span>
      ),
    },
  ];

  return (
    <>
      <Header
        title="Alerts"
        subtitle="VIP, watchlist, and system notifications"
        onRefresh={refresh}
        refreshing={loading && !!data}
      />
      <main className="flex-1 space-y-6 p-4 md:p-6">
        {error && <ErrorBanner message={error} onRetry={refresh} />}
        {loading && !data && <LoadingState />}
        {data && (
          <>
            <section className="grid gap-4 sm:grid-cols-2">
              <StatCard
                title="Total alerts"
                value={formatNumber(data.length)}
                icon={Bell}
                accent="blue"
              />
              <StatCard
                title="VIP-related"
                value={formatNumber(vipAlerts)}
                icon={AlertTriangle}
                accent="amber"
              />
            </section>

            <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h2 className="mb-3 text-sm font-semibold text-slate-800">
                Latest notifications
              </h2>
              <AlertNotification alerts={data} max={10} />
            </section>

            <section>
              <h2 className="mb-3 text-sm font-semibold text-slate-800">
                All alerts
              </h2>
              <DataTable
                columns={columns}
                rows={data}
                keyExtractor={(a) => `${a.type}-${a.time}`}
                emptyMessage="No alerts — VIP events appear when configured"
              />
            </section>
          </>
        )}
      </main>
    </>
  );
}
