"use client";

import { useState } from "react";
import { DollarSign, Store, TrendingUp, Users } from "lucide-react";
import { PageShell } from "@/components/enterprise/PageShell";
import { FilterBar, FilterField, filterInputClass } from "@/components/enterprise/FilterBar";
import { KpiCard } from "@/components/enterprise/KpiCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StoreTrendChart } from "@/components/charts/LazyStoreTrendChart";
import { useCachedQuery } from "@/hooks/useCachedQuery";
import { fetchExecutiveSnapshot } from "@/services/executive-api";
import { defaultDateRange, formatPct } from "@/lib/utils";
import { formatNumber } from "@/utils/format";

export default function ExecutivePage() {
  const initial = defaultDateRange(30);
  const [fromDay, setFromDay] = useState(initial.from);
  const [toDay, setToDay] = useState(initial.to);

  const { data, loading, error, refresh } = useCachedQuery({
    key: { page: "executive", fromDay, toDay },
    fetcher: () => fetchExecutiveSnapshot({ from_day: fromDay, to_day: toDay }),
  });

  const overview = data?.overview.summary;
  const conversion = data?.conversion;

  return (
    <PageShell
      title="Executive dashboard"
      subtitle="CEO view — revenue, visitors, and store comparisons"
      loading={loading && !data}
      error={error}
      onRefresh={refresh}
      refreshing={loading}
    >
      {data && overview && conversion && (
        <>
          <FilterBar>
            <FilterField label="From">
              <input type="date" className={filterInputClass()} value={fromDay} onChange={(e) => setFromDay(e.target.value)} />
            </FilterField>
            <FilterField label="To">
              <input type="date" className={filterInputClass()} value={toDay} onChange={(e) => setToDay(e.target.value)} />
            </FilterField>
          </FilterBar>

          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard title="Total revenue" value={`₹${formatNumber(conversion.total_revenue ?? 0)}`} icon={DollarSign} />
            <KpiCard title="Total visitors" value={formatNumber(overview.total_visitors)} icon={Users} />
            <KpiCard title="Conversion rate" value={formatPct(conversion.conversion_rate ?? 0)} icon={TrendingUp} />
            <KpiCard title="Revenue / visitor" value={`₹${(conversion.revenue_per_visitor ?? 0).toFixed(0)}`} icon={DollarSign} />
          </section>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Visitor trends</CardTitle>
              </CardHeader>
              <CardContent>
                <StoreTrendChart
                  data={data.overview.stores.map((s) => ({
                    day: s.store_id,
                    visitors: s.total_visitors,
                    repeat: s.repeat_visitors,
                  }))}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Store comparison</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {(data.comparison?.stores ?? data.overview.stores).map((s) => (
                  <div key={s.store_id} className="flex items-center justify-between rounded-lg border border-border px-3 py-2">
                    <div className="flex items-center gap-2">
                      <Store className="h-4 w-4 text-primary" />
                      <span className="text-sm font-medium">{s.store_id}</span>
                      {"rank" in s && s.rank != null && (
                        <span className="text-xs text-muted-foreground">#{s.rank}</span>
                      )}
                    </div>
                    <div className="text-right text-sm">
                      <p className="font-medium">{formatNumber(s.total_visitors)} visitors</p>
                      {"vs_best_pct" in s && s.vs_best_pct != null && (
                        <p className="text-xs text-muted-foreground">{s.vs_best_pct}% vs best</p>
                      )}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {conversion.stores && conversion.stores.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Revenue by store</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-muted-foreground">
                      <th className="pb-2 pr-4">Store</th>
                      <th className="pb-2 pr-4">Visitors</th>
                      <th className="pb-2 pr-4">Transactions</th>
                      <th className="pb-2 pr-4">Conversion</th>
                      <th className="pb-2">Revenue</th>
                    </tr>
                  </thead>
                  <tbody>
                    {conversion.stores.map((s) => (
                      <tr key={s.store_id} className="border-b border-border/50">
                        <td className="py-2 pr-4">{s.store_id}</td>
                        <td className="py-2 pr-4">{formatNumber(s.visitors)}</td>
                        <td className="py-2 pr-4">{formatNumber(s.transactions)}</td>
                        <td className="py-2 pr-4">{formatPct(s.conversion_rate)}</td>
                        <td className="py-2">₹{formatNumber(s.revenue)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </PageShell>
  );
}
