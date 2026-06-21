"use client";

import { useState, useEffect } from "react";
import { PageShell } from "@/components/enterprise/PageShell";
import { FilterBar, FilterField, filterInputClass } from "@/components/enterprise/FilterBar";
import { KpiCard } from "@/components/enterprise/KpiCard";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  TrendingUp,
  Users,
  DollarSign,
  Clock,
  UserCheck,
  Percent,
  Activity,
  Calendar,
  Sparkles,
} from "lucide-react";
import {
  fetchPredictions,
  fetchForecasts,
  PredictionsResponse,
  ForecastsResponse,
} from "@/services/ai-api";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";

export default function PredictiveAnalyticsPage() {
  const [storeId, setStoreId] = useState("store-001");
  const [daysAhead, setDaysAhead] = useState(7);
  const [horizon, setHorizon] = useState<"daily" | "weekly" | "monthly">("daily");

  const [predictionsData, setPredictionsData] = useState<PredictionsResponse | null>(null);
  const [forecastsData, setForecastsData] = useState<ForecastsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [preds, fcsts] = await Promise.all([
        fetchPredictions({ store_id: storeId, days_ahead: daysAhead }),
        fetchForecasts({ store_id: storeId, horizon }),
      ]);
      setPredictionsData(preds);
      setForecastsData(fcsts);
    } catch (err: any) {
      console.error(err);
      setError("Failed to load predictive analytics. Verify the backend AI services are online.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [storeId, daysAhead, horizon]);

  const preds = predictionsData?.predictions;
  const fcsts = forecastsData?.forecasts;

  return (
    <PageShell
      title="Predictive AI Analytics"
      subtitle="AI-generated projections for footfall, revenue trends, and staff optimization"
      onRefresh={loadData}
      refreshing={loading}
    >
      <FilterBar>
        <FilterField label="Target Store">
          <select
            className={filterInputClass()}
            value={storeId}
            onChange={(e) => setStoreId(e.target.value)}
          >
            <option value="store-001">Store 001 (Mumbai Main)</option>
            <option value="store-002">Store 002 (Delhi South)</option>
            <option value="store-003">Store 003 (Bangalore Tech)</option>
          </select>
        </FilterField>
        
        <FilterField label="Forecast Horizon">
          <select
            className={filterInputClass()}
            value={horizon}
            onChange={(e) => setHorizon(e.target.value as any)}
          >
            <option value="daily">Daily Horizon (7 Days)</option>
            <option value="weekly">Weekly Horizon (4 Weeks)</option>
            <option value="monthly">Monthly Horizon (3 Months)</option>
          </select>
        </FilterField>

        <FilterField label="Staffing Window (Days)">
          <select
            className={filterInputClass()}
            value={daysAhead}
            onChange={(e) => setDaysAhead(Number(e.target.value))}
          >
            <option value={7}>7 Days Ahead</option>
            <option value={14}>14 Days Ahead</option>
            <option value={30}>30 Days Ahead</option>
          </select>
        </FilterField>
      </FilterBar>

      {error && (
        <Card className="border-rose-200 bg-rose-50 text-rose-800">
          <CardContent className="pt-6">
            <p className="text-sm font-semibold">{error}</p>
          </CardContent>
        </Card>
      )}

      {predictionsData && forecastsData && preds && fcsts && (
        <div className="space-y-6">
          
          {/* Performance Health Index & Quick Stats */}
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="relative overflow-hidden">
              <CardHeader className="pb-2">
                <CardDescription className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  AI Performance Index
                </CardDescription>
                <CardTitle className="text-3xl font-extrabold text-indigo-600 dark:text-indigo-400">
                  {preds.store_performance.score}/100
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground">Rating:</span>
                  <Badge className={
                    preds.store_performance.rating === "Excellent"
                      ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                      : "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                  }>
                    {preds.store_performance.rating}
                  </Badge>
                </div>
              </CardContent>
            </Card>

            <KpiCard
              title="Daily Footfall (Avg)"
              value={preds.store_performance.metrics.average_daily_footfall.toString()}
              icon={Users}
            />

            <KpiCard
              title="Conversion Rate (Index)"
              value={`${(preds.store_performance.metrics.conversion_rate * 100).toFixed(1)}%`}
              icon={Percent}
            />

            <Card>
              <CardHeader className="pb-2">
                <CardDescription className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Revenue Confidence
                </CardDescription>
                <CardTitle className="text-3xl font-extrabold text-emerald-600 dark:text-emerald-400">
                  95% Interval
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <span className="text-xs text-muted-foreground flex items-center gap-1">
                  <Sparkles className="h-3 w-3 text-emerald-500" /> Statistical forecasting active
                </span>
              </CardContent>
            </Card>
          </section>

          {/* Revenue Forecasts with 95% Confidence Band */}
          <section className="grid gap-6 lg:grid-cols-3">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <DollarSign className="h-4.5 w-4.5 text-emerald-500" />
                  Revenue Forecast with 95% Confidence Band
                </CardTitle>
                <CardDescription>
                  Solid line denotes expected revenue; shaded region marks standard statistical variance.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={fcsts.revenue}>
                      <defs>
                        <linearGradient id="colorConfidence" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#10b981" stopOpacity={0.15}/>
                          <stop offset="95%" stopColor="#10b981" stopOpacity={0.01}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                      <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                      <YAxis tick={{ fontSize: 10 }} tickFormatter={(val) => `₹${val}`} />
                      <Tooltip formatter={(value: any) => [`₹${Number(value).toFixed(2)}`]} />
                      <Legend />
                      <Area
                        name="Confidence Interval (95%)"
                        type="monotone"
                        dataKey="upper_ci"
                        stroke="none"
                        fill="url(#colorConfidence)"
                        activeDot={false}
                      />
                      <Area
                        name="Lower Boundary"
                        type="monotone"
                        dataKey="lower_ci"
                        stroke="none"
                        fill="#f8fafc"
                        fillOpacity={0}
                        activeDot={false}
                      />
                      <Line
                        name="Expected Revenue (Forecast)"
                        type="monotone"
                        dataKey="forecast"
                        stroke="#10b981"
                        strokeWidth={2.5}
                        dot={{ r: 4 }}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Peak Operating Hours Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Clock className="h-4.5 w-4.5 text-indigo-500" />
                  Busiest Peak Operating Hours
                </CardTitle>
                <CardDescription>
                  Predicted busiest store intervals based on entry flow weights.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={preds.peak_hours} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                      <XAxis type="number" tick={{ fontSize: 9 }} />
                      <YAxis dataKey="label" type="category" tick={{ fontSize: 9 }} width={70} />
                      <Tooltip formatter={(value: any) => [`${(Number(value) * 100).toFixed(1)}% weight`]} />
                      <Bar dataKey="weight" fill="#6366f1" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </section>

          {/* Footfall & Staffing Scheduler */}
          <section className="grid gap-6 lg:grid-cols-2">
            
            {/* Staff Optimization Scheduler */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <UserCheck className="h-4.5 w-4.5 text-blue-500" />
                  Staff Capacity Optimization Planner
                </CardTitle>
                <CardDescription>
                  Recommended floor staff count based on predicted customer volumes.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={preds.staff_requirements}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                      <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                      <YAxis yAxisId="left" orientation="left" stroke="#6366f1" tick={{ fontSize: 10 }} label={{ value: 'Customers', angle: -90, position: 'insideLeft', style: {fontSize: 10} }} />
                      <YAxis yAxisId="right" orientation="right" stroke="#f59e0b" tick={{ fontSize: 10 }} label={{ value: 'Staff Count', angle: 90, position: 'insideRight', style: {fontSize: 10} }} />
                      <Tooltip />
                      <Legend />
                      <Bar yAxisId="left" name="Predicted Footfall" dataKey="predicted_footfall" fill="#6366f1" opacity={0.7} radius={[4, 4, 0, 0]} />
                      <Line yAxisId="right" name="Recommended Staff" type="monotone" dataKey="recommended_staff_count" stroke="#f59e0b" strokeWidth={3} dot={{ r: 4 }} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Retention Forecast */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Activity className="h-4.5 w-4.5 text-indigo-500" />
                  Customer Loyalty & Growth Forecast
                </CardTitle>
                <CardDescription>
                  Forecasted count of repeat visitors with 95% upper and lower boundaries.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={fcsts.retention}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                      <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                      <YAxis tick={{ fontSize: 10 }} />
                      <Tooltip />
                      <Legend />
                      <Area
                        name="Variance Zone"
                        type="monotone"
                        dataKey="upper_ci"
                        stroke="none"
                        fill="#6366f1"
                        fillOpacity={0.1}
                      />
                      <Line
                        name="Loyal Customers (Forecast)"
                        type="monotone"
                        dataKey="forecast_repeat_visitors"
                        stroke="#6366f1"
                        strokeWidth={2}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

          </section>

        </div>
      )}
    </PageShell>
  );
}
