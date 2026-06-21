"use client";

import { useState, useEffect } from "react";
import { DollarSign, Store, TrendingUp, Users, AlertOctagon, Heart, Award, ArrowUpRight, ArrowDownRight, Sparkles } from "lucide-react";
import { PageShell } from "@/components/enterprise/PageShell";
import { FilterBar, FilterField, filterInputClass } from "@/components/enterprise/FilterBar";
import { KpiCard } from "@/components/enterprise/KpiCard";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { StoreTrendChart } from "@/components/charts/LazyStoreTrendChart";
import { fetchExecutiveSnapshot } from "@/services/executive-api";
import { fetchRecommendations, fetchForecasts, RecommendationItem, ForecastItem } from "@/services/ai-api";
import { defaultDateRange, formatPct } from "@/lib/utils";
import { formatNumber } from "@/utils/format";
import { ResponsiveContainer, RadialBarChart, RadialBar, Tooltip, Legend } from "recharts";

export default function ExecutivePage() {
  const initial = defaultDateRange(30);
  const [fromDay, setFromDay] = useState(initial.from);
  const [toDay, setToDay] = useState(initial.to);
  const [storeId, setStoreId] = useState("store-001");

  // State for AI-enriched CEO context
  const [snapshotData, setSnapshotData] = useState<any>(null);
  const [topRecs, setTopRecs] = useState<RecommendationItem[]>([]);
  const [growthForecast, setGrowthForecast] = useState<ForecastItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadCEOData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Fetch Phase 4 executive baseline snapshot
      const snapshot = await fetchExecutiveSnapshot({ from_day: fromDay, to_day: toDay });
      setSnapshotData(snapshot);

      // 2. Fetch Phase 5 predictive/prescriptive layers
      const [recs, forecasts] = await Promise.all([
        fetchRecommendations({ store_id: storeId }),
        fetchForecasts({ store_id: storeId, horizon: "daily" }),
      ]);
      setTopRecs(recs.recommendations.slice(0, 3));
      setGrowthForecast(forecasts.forecasts.revenue);
    } catch (err: any) {
      console.error(err);
      setError("Failed to compile CEO-level analytics report.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCEOData();
  }, [fromDay, toDay, storeId]);

  const overview = snapshotData?.overview.summary;
  const conversion = snapshotData?.conversion;
  
  // Calculate Business Health Score
  // Weighted: 40% conversion rate (scaled), 30% revenue target ($15k target), 30% repeat ratio
  const calculateHealthScore = () => {
    if (!conversion || !overview) return 75;
    const convWeight = Math.min(100, (conversion.conversion_rate / 0.25) * 100) * 0.4;
    const revWeight = Math.min(100, (conversion.total_revenue / 15000) * 100) * 0.3;
    const repeatWeight = (overview.repeat_ratio || 0.35) * 100 * 0.3;
    return Math.round(convWeight + revWeight + repeatWeight);
  };

  const healthScore = calculateHealthScore();

  // Custom visual health score gauge data
  const healthData = [
    {
      name: "Health Index",
      value: healthScore,
      fill: healthScore >= 80 ? "#10b981" : healthScore >= 60 ? "#f59e0b" : "#f43f5e",
    },
  ];

  // Risks compilation
  const getRiskIndicators = () => {
    const risks = [];
    if (conversion && conversion.conversion_rate < 0.12) {
      risks.push({
        title: "Critical Conversion Drop",
        description: `Overall conversion is low at ${formatPct(conversion.conversion_rate)}. Suggest checkout optimization.`,
      });
    }
    if (overview && (overview.repeat_ratio || 0.3) < 0.22) {
      risks.push({
        title: "Weak Repeat Visitor Base",
        description: "Customer retention index has dipped below 22% this week.",
      });
    }
    if (topRecs.some((r) => r.category === "staffing" && r.impact_level === "High")) {
      risks.push({
        title: "Peak Hour Staff Bottleneck",
        description: "Staff shortages predicted during upcoming high traffic windows.",
      });
    }
    return risks;
  };

  const activeRisks = getRiskIndicators();

  return (
    <PageShell
      title="Executive AI Dashboard"
      subtitle="CEO Portal — Real-time business health, forecast growth, and risk assessments"
      onRefresh={loadCEOData}
      refreshing={loading}
    >
      {snapshotData && overview && conversion && (
        <div className="space-y-6">
          
          <FilterBar>
            <FilterField label="From">
              <input type="date" className={filterInputClass()} value={fromDay} onChange={(e) => setFromDay(e.target.value)} />
            </FilterField>
            <FilterField label="To">
              <input type="date" className={filterInputClass()} value={toDay} onChange={(e) => setToDay(e.target.value)} />
            </FilterField>
            <FilterField label="Top Rec Store context">
              <select className={filterInputClass()} value={storeId} onChange={(e) => setStoreId(e.target.value)}>
                <option value="store-001">Mumbai Store</option>
                <option value="store-002">Delhi Store</option>
              </select>
            </FilterField>
          </FilterBar>

          {/* AI Generated Overview Summary */}
          <section className="rounded-xl border border-indigo-100 bg-indigo-50/40 p-4 dark:border-indigo-950/30 dark:bg-indigo-950/10">
            <h2 className="text-xs font-bold uppercase tracking-wider text-indigo-700 dark:text-indigo-400 flex items-center gap-1.5 mb-1.5">
              <Sparkles className="h-4 w-4" /> AI Executive Summary
            </h2>
            <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
              Your overall retail business health score stands at <strong className="text-indigo-700 dark:text-indigo-400">{healthScore}%</strong>.
              Mumbai main store continues to lead visitor traffic with {formatNumber(overview.total_visitors)} unique entries.
              {activeRisks.length > 0
                ? ` Warning: AI identified ${activeRisks.length} key operational risk factors requiring attention, primarily relating to conversion and floor staff.`
                : " Overall operations are running in optimal ranges with no urgent threats detected."}
            </p>
          </section>

          {/* CEO KPIs */}
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard title="Total Revenue" value={`₹${formatNumber(conversion.total_revenue ?? 0)}`} icon={DollarSign} />
            <KpiCard title="Unique Customers" value={formatNumber(overview.total_visitors)} icon={Users} />
            <KpiCard title="Checkout Conversion" value={formatPct(conversion.conversion_rate ?? 0)} icon={TrendingUp} />
            <KpiCard title="Average Ticket Size" value={`₹${(conversion.revenue_per_visitor ?? 0).toFixed(0)}`} icon={DollarSign} />
          </section>

          {/* Health Score & Risks Row */}
          <section className="grid gap-6 lg:grid-cols-3">
            
            {/* Business Health Score Radial */}
            <Card className="flex flex-col justify-between">
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-1.5">
                  <Heart className="h-4.5 w-4.5 text-rose-500 fill-current" />
                  Business Health Score
                </CardTitle>
                <CardDescription>Overall performance index calculated across store metrics.</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col items-center justify-center py-6">
                <div className="relative h-44 w-44 flex items-center justify-center">
                  <div className="absolute flex flex-col items-center justify-center">
                    <span className="text-4xl font-extrabold text-foreground">{healthScore}%</span>
                    <span className="text-[10px] uppercase font-bold text-muted-foreground">Index Rating</span>
                  </div>
                  <ResponsiveContainer width="100%" height="100%">
                    <RadialBarChart cx="50%" cy="50%" innerRadius="70%" outerRadius="100%" barSize={12} data={healthData} startAngle={180} endAngle={-180}>
                      <RadialBar background dataKey="value" />
                    </RadialBarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* AI Risk Warnings */}
            <Card className="flex flex-col justify-between">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-1.5">
                  <AlertOctagon className="h-4.5 w-4.5 text-amber-500" />
                  Critical Risk Indicators
                </CardTitle>
                <CardDescription>Active exceptions flagged by AI surveillance rules.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3.5 flex-1">
                {activeRisks.length === 0 ? (
                  <div className="text-center py-12 text-xs text-muted-foreground">
                    All operations green. No critical risks detected.
                  </div>
                ) : (
                  activeRisks.map((risk, idx) => (
                    <div key={idx} className="flex gap-2.5 p-3 rounded-lg border border-rose-100 bg-rose-50/40 text-xs dark:border-rose-950/20 dark:bg-rose-950/5">
                      <AlertOctagon className="h-4.5 w-4.5 text-rose-500 shrink-0" />
                      <div>
                        <h4 className="font-bold text-rose-800 dark:text-rose-400">{risk.title}</h4>
                        <p className="text-muted-foreground mt-0.5">{risk.description}</p>
                      </div>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            {/* Top AI Recommendations */}
            <Card className="flex flex-col justify-between">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-1.5">
                  <Award className="h-4.5 w-4.5 text-indigo-500" />
                  Top Actionable Recommendations
                </CardTitle>
                <CardDescription>Prioritized decisions to drive higher LTV and footfall.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3.5 flex-1">
                {topRecs.length === 0 ? (
                  <div className="text-center py-12 text-xs text-muted-foreground">
                    Deploy AI recommendations in the recommendation center to see items here.
                  </div>
                ) : (
                  topRecs.map((rec) => (
                    <div key={rec.id} className="flex items-start justify-between gap-2 p-2.5 rounded-lg border border-border bg-card">
                      <div className="min-w-0">
                        <h4 className="font-bold text-xs text-foreground truncate">{rec.title}</h4>
                        <p className="text-[11px] text-muted-foreground truncate mt-0.5">{rec.description}</p>
                      </div>
                      <Badge className="text-[9px] shrink-0 font-semibold uppercase">{rec.impact_level}</Badge>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

          </section>

          {/* Visitor Trends & Store Comparisons */}
          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Historical Visitor Trends</CardTitle>
              </CardHeader>
              <CardContent>
                <StoreTrendChart
                  data={snapshotData.overview.stores.map((s: any) => ({
                    day: s.store_id,
                    visitors: s.total_visitors,
                    repeat: s.repeat_visitors,
                  }))}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Store Ranking Performance</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {(snapshotData.comparison?.stores ?? snapshotData.overview.stores).map((s: any, idx: number) => (
                  <div key={s.store_id} className="flex items-center justify-between rounded-lg border border-border px-4 py-2.5 bg-card hover:bg-muted/10 transition-colors">
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-bold text-muted-foreground">#{idx + 1}</span>
                      <Store className="h-4 w-4 text-primary" />
                      <span className="text-sm font-semibold text-foreground">{s.store_id}</span>
                    </div>
                    <div className="flex items-center gap-4 text-right">
                      <div className="text-xs">
                        <p className="font-bold text-foreground">{formatNumber(s.total_visitors)} visitors</p>
                        <p className="text-muted-foreground">{formatPct(s.repeat_ratio)} repeat ratio</p>
                      </div>
                      {idx === 0 ? (
                        <div className="p-1 rounded-full bg-emerald-50 text-emerald-600"><ArrowUpRight className="h-4 w-4" /></div>
                      ) : (
                        <div className="p-1 rounded-full bg-slate-50 text-slate-500"><ArrowDownRight className="h-4 w-4" /></div>
                      )}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Revenue by Store Table */}
          {conversion.stores && conversion.stores.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Detailed POS Conversion Revenue by Store</CardTitle>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-muted-foreground font-semibold">
                      <th className="pb-2 pr-4">Store Location ID</th>
                      <th className="pb-2 pr-4">Customers Detected</th>
                      <th className="pb-2 pr-4">Transactions Checked</th>
                      <th className="pb-2 pr-4">Conversion Rate</th>
                      <th className="pb-2">Gross Revenue</th>
                    </tr>
                  </thead>
                  <tbody>
                    {conversion.stores.map((s: any) => (
                      <tr key={s.store_id} className="border-b border-border/50 hover:bg-muted/5 transition-colors">
                        <td className="py-2.5 pr-4 font-medium text-foreground">{s.store_id}</td>
                        <td className="py-2.5 pr-4">{formatNumber(s.visitors)}</td>
                        <td className="py-2.5 pr-4">{formatNumber(s.transactions)}</td>
                        <td className="py-2.5 pr-4 font-semibold text-primary">{formatPct(s.conversion_rate)}</td>
                        <td className="py-2.5 font-bold text-emerald-600 dark:text-emerald-400">₹{formatNumber(s.revenue)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </PageShell>
  );
}
