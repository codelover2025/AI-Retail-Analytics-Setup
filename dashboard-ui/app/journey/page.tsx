"use client";

import { useState } from "react";
import { GitFork, MapPin, Route, Users } from "lucide-react";
import { PageShell } from "@/components/enterprise/PageShell";
import { KpiCard } from "@/components/enterprise/KpiCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FilterBar, FilterField, filterInputClass } from "@/components/enterprise/FilterBar";
import { useCachedQuery } from "@/hooks/useCachedQuery";
import { apiClient } from "@/services/api";
import { defaultDateRange } from "@/lib/utils";
import { formatNumber, formatDuration } from "@/utils/format";

interface JourneyStore {
  store_id: string;
  total_visitors: number;
  repeat_visitors: number;
  avg_dwell_seconds: number;
  top_zone: string | null;
  zone_count: number;
}

interface JourneyOverview {
  brand_id: string;
  from_day: string;
  to_day: string;
  summary: {
    total_visitors: number;
    repeat_visitors: number;
    new_visitors: number;
    avg_dwell_seconds: number;
    repeat_ratio: number;
    store_count: number;
  };
  stores: JourneyStore[];
}

async function fetchJourneyData(days: number): Promise<JourneyOverview> {
  const to = new Date();
  const from = new Date(to);
  from.setDate(to.getDate() - days + 1);
  const fmt = (d: Date) => d.toISOString().split("T")[0];

  const { data } = await apiClient.get<JourneyOverview>("/api/dashboard/overview", {
    params: { from_day: fmt(from), to_day: fmt(to) },
  });
  return data;
}

// Simple Sankey-style path visualizer using pure CSS
function JourneyFlowBar({
  label,
  value,
  max,
  color,
}: {
  label: string;
  value: number;
  max: number;
  color: string;
}) {
  const pct = max > 0 ? Math.max(4, Math.round((value / max) * 100)) : 4;
  return (
    <div className="flex items-center gap-3">
      <div className="w-28 shrink-0 text-right text-xs text-muted-foreground">{label}</div>
      <div className="flex-1 rounded-full bg-muted/40">
        <div
          className="h-5 rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <div className="w-14 text-xs font-mono text-foreground">{formatNumber(value)}</div>
    </div>
  );
}

export default function JourneyMappingPage() {
  const initial = defaultDateRange(7);
  const [days, setDays] = useState("7");

  const { data, loading, error, refresh } = useCachedQuery<JourneyOverview>({
    key: { page: "journey", days },
    fetcher: () => fetchJourneyData(Number(days)),
  });

  const stores = data?.stores ?? [];
  const summary = data?.summary;
  const maxVisitors = Math.max(...stores.map((s) => s.total_visitors), 1);

  const ZONE_COLORS = [
    "#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444",
    "#06b6d4", "#ec4899", "#84cc16",
  ];

  return (
    <PageShell
      title="Journey mapping"
      subtitle="Customer flow, dwell patterns, and zone-to-zone transitions across stores"
      loading={loading && !data}
      error={error}
      onRefresh={refresh}
      refreshing={loading}
    >
      <FilterBar>
        <FilterField label="Period">
          <select
            className={filterInputClass()}
            value={days}
            onChange={(e) => setDays(e.target.value)}
          >
            <option value="1">Today</option>
            <option value="7">Last 7 days</option>
            <option value="14">Last 14 days</option>
            <option value="30">Last 30 days</option>
          </select>
        </FilterField>
      </FilterBar>

      {summary && (
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KpiCard
            title="Total journeys"
            value={formatNumber(summary.total_visitors)}
            subtitle={`${data?.from_day} → ${data?.to_day}`}
            icon={Route}
          />
          <KpiCard
            title="Repeat visitors"
            value={formatNumber(summary.repeat_visitors)}
            subtitle={`${(summary.repeat_ratio * 100).toFixed(1)}% of total`}
            icon={Users}
          />
          <KpiCard
            title="New visitors"
            value={formatNumber(summary.new_visitors)}
            icon={MapPin}
          />
          <KpiCard
            title="Avg. dwell time"
            value={formatDuration(summary.avg_dwell_seconds)}
            icon={GitFork}
          />
        </section>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Store Journey Volume */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Journey volume by store</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {stores.length === 0 ? (
              <p className="text-sm text-muted-foreground">No journey data for this period.</p>
            ) : (
              stores.map((s, i) => (
                <JourneyFlowBar
                  key={s.store_id}
                  label={s.store_id}
                  value={s.total_visitors}
                  max={maxVisitors}
                  color={ZONE_COLORS[i % ZONE_COLORS.length]}
                />
              ))
            )}
          </CardContent>
        </Card>

        {/* Dwell + Zone breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Dwell & zone highlights</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {stores.length === 0 ? (
              <p className="text-sm text-muted-foreground">No zone data available.</p>
            ) : (
              stores.map((s) => (
                <div
                  key={s.store_id}
                  className="flex items-center justify-between rounded-xl border border-border/60 px-4 py-3"
                >
                  <div>
                    <p className="text-sm font-semibold">{s.store_id}</p>
                    <p className="text-xs text-muted-foreground">
                      {s.zone_count} zone{s.zone_count !== 1 ? "s" : ""} tracked
                    </p>
                    {s.top_zone && (
                      <p className="text-xs text-muted-foreground">
                        Top zone: <span className="font-medium text-foreground">{s.top_zone}</span>
                      </p>
                    )}
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-bold">{formatDuration(s.avg_dwell_seconds)}</p>
                    <p className="text-[10px] text-muted-foreground">avg. dwell</p>
                    <Badge variant="secondary" className="mt-1 text-[10px]">
                      {formatNumber(s.repeat_visitors)} repeat
                    </Badge>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      {/* Cross-store journey patterns */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Repeat vs. new visitor flow</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {stores.map((s, i) => {
              const total = s.total_visitors || 1;
              const repeatPct = Math.round((s.repeat_visitors / total) * 100);
              const newPct = 100 - repeatPct;
              return (
                <div key={s.store_id} className="space-y-1">
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>{s.store_id}</span>
                    <span>{repeatPct}% repeat · {newPct}% new</span>
                  </div>
                  <div className="flex h-4 overflow-hidden rounded-full">
                    <div
                      className="h-full transition-all duration-700"
                      style={{
                        width: `${repeatPct}%`,
                        background: ZONE_COLORS[i % ZONE_COLORS.length],
                      }}
                    />
                    <div
                      className="h-full flex-1"
                      style={{ background: `${ZONE_COLORS[i % ZONE_COLORS.length]}33` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </PageShell>
  );
}
