"use client";

import { useState } from "react";
import { Activity, Calendar, Clock, Users } from "lucide-react";
import { PageShell } from "@/components/enterprise/PageShell";
import { KpiCard } from "@/components/enterprise/KpiCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useCachedQuery } from "@/hooks/useCachedQuery";
import {
  buildStaffPerformance,
  fetchHRMSEmployees,
  fetchStaffInteractions,
  syncHRMSAttendance,
  syncHRMSEmployees,
} from "@/services/staff-api";
import { formatNumber } from "@/utils/format";

type Tab = "performance" | "interactions" | "attendance" | "shifts";

export default function StaffAnalyticsPage() {
  const [tab, setTab] = useState<Tab>("performance");
  const [syncing, setSyncing] = useState(false);

  const { data, loading, error, refresh } = useCachedQuery({
    key: { page: "staff", tab },
    fetcher: async () => {
      const [employees, performance, interactions] = await Promise.all([
        fetchHRMSEmployees(),
        buildStaffPerformance(),
        fetchStaffInteractions(),
      ]);
      return { employees, performance, interactions };
    },
  });

  async function handleSync(type: "employees" | "attendance") {
    setSyncing(true);
    try {
      if (type === "employees") await syncHRMSEmployees();
      else await syncHRMSAttendance();
      refresh();
    } finally {
      setSyncing(false);
    }
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "performance", label: "Performance" },
    { id: "interactions", label: "Interactions" },
    { id: "attendance", label: "Attendance" },
    { id: "shifts", label: "Shifts" },
  ];

  return (
    <PageShell
      title="Staff analytics"
      subtitle="Performance, interactions, attendance, and shift patterns"
      loading={loading && !data}
      error={error}
      onRefresh={refresh}
      refreshing={loading}
      actions={
        <div className="flex gap-2">
          <Button size="sm" variant="outline" disabled={syncing} onClick={() => handleSync("employees")}>
            Sync HRMS
          </Button>
          <Button size="sm" variant="outline" disabled={syncing} onClick={() => handleSync("attendance")}>
            Sync attendance
          </Button>
        </div>
      }
    >
      {data && (
        <>
          <div className="flex flex-wrap gap-2">
            {tabs.map((t) => (
              <Button
                key={t.id}
                size="sm"
                variant={tab === t.id ? "default" : "outline"}
                onClick={() => setTab(t.id)}
              >
                {t.label}
              </Button>
            ))}
          </div>

          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard title="Staff count" value={data.employees.length} icon={Users} />
            <KpiCard title="Interactions" value={data.interactions.total} icon={Activity} />
            <KpiCard title="Top performer" value={data.performance[0]?.employee_id ?? "—"} subtitle={`${data.performance[0]?.interaction_count ?? 0} events`} icon={Users} />
            <KpiCard title="Active staff" value={data.employees.filter((e) => e.active).length} icon={Calendar} />
          </section>

          {tab === "performance" && (
            <Card>
              <CardHeader><CardTitle className="text-base">Staff performance ranking</CardTitle></CardHeader>
              <CardContent className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-muted-foreground">
                      <th className="pb-2 pr-4">#</th>
                      <th className="pb-2 pr-4">Employee</th>
                      <th className="pb-2 pr-4">Interactions</th>
                      <th className="pb-2">Last seen</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.performance.map((row, i) => (
                      <tr key={row.employee_id} className="border-b border-border/50">
                        <td className="py-2 pr-4">{i + 1}</td>
                        <td className="py-2 pr-4 font-mono text-xs">{row.employee_id}</td>
                        <td className="py-2 pr-4">{formatNumber(row.interaction_count)}</td>
                        <td className="py-2 text-xs">{row.last_seen ? new Date(row.last_seen).toLocaleString() : "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          )}

          {tab === "interactions" && (
            <Card>
              <CardHeader><CardTitle className="text-base">Recent interactions</CardTitle></CardHeader>
              <CardContent className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-muted-foreground">
                      <th className="pb-2 pr-4">Time</th>
                      <th className="pb-2 pr-4">Camera</th>
                      <th className="pb-2 pr-4">Customer</th>
                      <th className="pb-2">Employee</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.interactions.items.map((ix) => (
                      <tr key={ix.id} className="border-b border-border/50">
                        <td className="py-2 pr-4">{new Date(ix.timestamp).toLocaleString()}</td>
                        <td className="py-2 pr-4">{ix.camera_id}</td>
                        <td className="py-2 pr-4 font-mono text-xs">{ix.customer_id}</td>
                        <td className="py-2 font-mono text-xs">{ix.employee_id}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          )}

          {tab === "attendance" && (
            <Card>
              <CardHeader><CardTitle className="text-base">HRMS employees</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                {data.employees.map((emp) => (
                  <div key={emp.id} className="flex items-center justify-between rounded-lg border border-border px-3 py-2">
                    <span className="text-sm font-medium">{emp.name}</span>
                    <Badge variant={emp.active ? "success" : "warning"}>{emp.active ? "Active" : "Inactive"}</Badge>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {tab === "shifts" && (
            <Card>
              <CardHeader><CardTitle className="text-base">Shift analytics (by hour)</CardTitle></CardHeader>
              <CardContent>
                <p className="mb-4 text-sm text-muted-foreground">
                  Interaction density by hour-of-day from recent staff events.
                </p>
                <div className="grid grid-cols-6 gap-2 sm:grid-cols-8 lg:grid-cols-12">
                  {Array.from({ length: 12 }, (_, h) => {
                    const hour = h + 9;
                    const count = data.interactions.items.filter(
                      (ix) => new Date(ix.timestamp).getHours() === hour
                    ).length;
                    return (
                      <div key={hour} className="rounded-md border border-border p-2 text-center">
                        <Clock className="mx-auto h-3 w-3 text-muted-foreground" />
                        <p className="text-xs font-medium">{hour}:00</p>
                        <p className="text-lg font-bold">{count}</p>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </PageShell>
  );
}
