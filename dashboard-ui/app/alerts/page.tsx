"use client";

import { useState, useEffect } from "react";
import { PageShell } from "@/components/enterprise/PageShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import {
  Bell,
  AlertTriangle,
  Users,
  Clock,
  Check,
  CheckCircle,
  WifiOff,
  TrendingDown,
  Activity,
  Play,
  Sliders,
  Settings,
  Plus,
} from "lucide-react";
import { apiClient } from "@/services/api";

interface AlertItem {
  id: string;
  alert_type: string;
  store_id: string;
  message: string;
  acknowledged: boolean;
  created_at: string;
  payload?: any;
}

interface AlertRule {
  id: string;
  alert_type: string;
  store_id: string;
  threshold?: number;
  channels: string[];
  recipients: string[];
  enabled: boolean;
  config: any;
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [activeTab, setActiveTab] = useState<"feed" | "rules" | "diagnose">("feed");
  const [filterType, setFilterType] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Diagnostic form state
  const [diagStore, setDiagStore] = useState("store-001");
  const [diagFootfall, setDiagFootfall] = useState(25);
  const [diagTransactions, setDiagTransactions] = useState(2);
  const [diagQueue, setDiagQueue] = useState(6);
  const [diagDuration, setDiagDuration] = useState(30);
  const [diagTriggered, setDiagTriggered] = useState<any[]>([]);
  const [diagLoading, setDiagLoading] = useState(false);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch alerts
      const alertsRes = await apiClient.get<{ items: AlertItem[] }>("/api/alerts", {
        params: { page_size: 50 },
      });
      setAlerts(alertsRes.data.items || []);

      // Fetch alert rules
      const rulesRes = await apiClient.get<AlertRule[]>("/api/alerts/rules");
      setRules(rulesRes.data || []);
    } catch (err: any) {
      console.error(err);
      setError("Failed to sync alerts database. Ensure backend APIs are running.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const acknowledgeAlert = async (id: string) => {
    try {
      await apiClient.post(`/api/alerts/${id}/acknowledge`);
      // Update state locally
      setAlerts((prev) =>
        prev.map((a) => (a.id === id ? { ...a, acknowledged: true } : a))
      );
    } catch (err) {
      alert("Acknowledge request failed.");
    }
  };

  const runDiagnostic = async () => {
    setDiagLoading(true);
    setDiagTriggered([]);
    try {
      const res = await apiClient.post("/api/v1/ai/alerts/evaluate", null, {
        params: {
          store_id: diagStore,
          footfall: diagFootfall,
          transactions: diagTransactions,
          queue_count: diagQueue,
          duration_minutes: diagDuration,
        },
      });
      setDiagTriggered(res.data.alerts_triggered || []);
      // Reload alerts to see new additions
      loadData();
    } catch (err) {
      alert("Diagnostic run failed. Check admin RBAC privileges.");
    } finally {
      setDiagLoading(false);
    }
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case "vip_detected":
        return <Users className="h-4 w-4 text-purple-600 dark:text-purple-400" />;
      case "watchlist_detected":
        return <AlertTriangle className="h-4 w-4 text-rose-600 dark:text-rose-400" />;
      case "camera_offline":
        return <WifiOff className="h-4 w-4 text-slate-600 dark:text-slate-400" />;
      case "low_traffic":
      case "low_conversion":
        return <TrendingDown className="h-4 w-4 text-amber-600 dark:text-amber-400" />;
      case "high_crowd":
      case "long_queue":
        return <Users className="h-4 w-4 text-orange-600 dark:text-orange-400" />;
      default:
        return <Bell className="h-4 w-4 text-primary" />;
    }
  };

  const getAlertBadge = (type: string) => {
    let style = "bg-slate-100 text-slate-800 dark:bg-slate-900 dark:text-slate-300";
    if (type === "vip_detected") style = "bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-300";
    else if (type === "watchlist_detected") style = "bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300";
    else if (type === "camera_offline") style = "bg-slate-100 text-slate-800 dark:bg-slate-900 dark:text-slate-300";
    else if (type.includes("low")) style = "bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300";
    else if (type.includes("queue") || type.includes("crowd")) style = "bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-300";

    return <Badge className={`${style} text-[10px] capitalize`}>{type.replace("_", " ")}</Badge>;
  };

  const filteredAlerts = filterType === "all"
    ? alerts
    : alerts.filter((a) => a.alert_type === filterType);

  return (
    <PageShell
      title="AI Alert Center"
      subtitle="Manage real-time alerts, VIP detections, queue limits, and diagnostic evaluation triggers"
      onRefresh={loadData}
      refreshing={loading}
    >
      <div className="space-y-6">
        
        {/* Alerts Control Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-4">
          <div className="flex gap-1.5">
            <Button
              size="sm"
              variant={activeTab === "feed" ? "default" : "outline"}
              className="h-8 text-xs flex items-center gap-1.5"
              onClick={() => setActiveTab("feed")}
            >
              <Bell className="h-3.5 w-3.5" />
              <span>Real-time Alert Feed</span>
            </Button>
            <Button
              size="sm"
              variant={activeTab === "rules" ? "default" : "outline"}
              className="h-8 text-xs flex items-center gap-1.5"
              onClick={() => setActiveTab("rules")}
            >
              <Sliders className="h-3.5 w-3.5" />
              <span>Active Threshold Rules</span>
            </Button>
            <Button
              size="sm"
              variant={activeTab === "diagnose" ? "default" : "outline"}
              className="h-8 text-xs flex items-center gap-1.5"
              onClick={() => setActiveTab("diagnose")}
            >
              <Activity className="h-3.5 w-3.5" />
              <span>Diagnostic Evaluator</span>
            </Button>
          </div>

          {activeTab === "feed" && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Type:</span>
              <select
                className="px-2.5 py-1.5 rounded-md border border-input text-xs bg-background focus:outline-none focus:ring-1 focus:ring-primary"
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
              >
                <option value="all">All Alerts</option>
                <option value="vip_detected">VIP Detected</option>
                <option value="watchlist_detected">Watchlist Detected</option>
                <option value="camera_offline">Camera Offline</option>
                <option value="low_traffic">Low Traffic</option>
                <option value="long_queue">Queue Alerts</option>
                <option value="high_crowd">Crowd Alerts</option>
              </select>
            </div>
          )}
        </div>

        {error && (
          <Card className="border-rose-200 bg-rose-50 text-rose-800">
            <CardContent className="pt-6">
              <p className="text-sm font-semibold">{error}</p>
            </CardContent>
          </Card>
        )}

        {/* FEED TAB */}
        {activeTab === "feed" && (
          <div className="space-y-4">
            {filteredAlerts.length === 0 && !loading && (
              <div className="text-center py-12 border border-dashed border-border rounded-xl">
                <p className="text-sm text-muted-foreground">No recent alerts found.</p>
              </div>
            )}

            <div className="grid gap-3">
              {filteredAlerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`flex items-center justify-between p-4 rounded-xl border bg-card transition-all ${
                    alert.acknowledged
                      ? "opacity-60 border-border"
                      : "border-l-4 border-l-rose-500 border-border shadow-sm"
                  }`}
                >
                  <div className="flex items-center gap-3.5 min-w-0">
                    <div className={`p-2.5 rounded-lg bg-muted/60`}>
                      {getAlertIcon(alert.alert_type)}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap mb-1">
                        <span className="text-xs font-semibold text-foreground">{alert.store_id}</span>
                        {getAlertBadge(alert.alert_type)}
                        <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {new Date(alert.created_at).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground truncate max-w-xl">
                        {alert.message}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {alert.acknowledged ? (
                      <span className="text-xs text-muted-foreground font-semibold flex items-center gap-1">
                        <CheckCircle className="h-3.5 w-3.5 text-emerald-500" />
                        <span>Acknowledged</span>
                      </span>
                    ) : (
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-8 text-xs flex items-center gap-1 border-rose-200 hover:bg-rose-50 text-rose-700 hover:text-rose-800"
                        onClick={() => acknowledgeAlert(alert.id)}
                      >
                        <Check className="h-3.5 w-3.5" />
                        <span>Acknowledge</span>
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* RULES TAB */}
        {activeTab === "rules" && (
          <div className="grid gap-6 md:grid-cols-2">
            {rules.length === 0 && !loading && (
              <div className="col-span-2 text-center py-12 border border-dashed border-border rounded-xl">
                <p className="text-sm text-muted-foreground">No custom threshold rules set up.</p>
              </div>
            )}

            {rules.map((rule) => (
              <Card key={rule.id} className="border border-border shadow-sm">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    {getAlertBadge(rule.alert_type)}
                    <span className="text-xs text-muted-foreground">Store: {rule.store_id || "All Stores"}</span>
                  </div>
                  <CardTitle className="text-sm font-bold mt-2">
                    {rule.alert_type.replace("_", " ").toUpperCase()} threshold
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="text-xs text-muted-foreground space-y-1.5">
                    {rule.threshold !== undefined && (
                      <div className="flex justify-between">
                        <span>Trigger Threshold:</span>
                        <span className="font-bold text-foreground">{rule.threshold}</span>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span>Delivery Channels:</span>
                      <span className="font-semibold text-foreground uppercase">{rule.channels.join(", ")}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Enabled Status:</span>
                      <Badge className={rule.enabled ? "bg-green-100 text-green-800" : "bg-slate-100 text-slate-800"}>
                        {rule.enabled ? "Active" : "Disabled"}
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* DIAGNOSTIC EVALUATOR TAB */}
        {activeTab === "diagnose" && (
          <div className="grid gap-6 md:grid-cols-3">
            
            {/* Control Form */}
            <Card className="md:col-span-1 border border-border shadow-sm">
              <CardHeader>
                <CardTitle className="text-sm font-bold flex items-center gap-1.5">
                  <Settings className="h-4.5 w-4.5 text-indigo-500" />
                  Diagnostic Inputs
                </CardTitle>
                <CardDescription>
                  Manually adjust metrics to check if AI rules trigger notifications.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-muted-foreground">Store ID</label>
                  <select
                    className="w-full px-3 py-2 rounded-lg border border-input text-xs bg-background focus:outline-none"
                    value={diagStore}
                    onChange={(e) => setDiagStore(e.target.value)}
                  >
                    <option value="store-001">store-001</option>
                    <option value="store-002">store-002</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-muted-foreground flex justify-between">
                    <span>Footfall Volume</span>
                    <span className="font-bold text-primary">{diagFootfall} customers</span>
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="100"
                    value={diagFootfall}
                    onChange={(e) => setDiagFootfall(Number(e.target.value))}
                    className="w-full h-1 bg-muted rounded-lg appearance-none cursor-pointer"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-muted-foreground flex justify-between">
                    <span>Transactions Completed</span>
                    <span className="font-bold text-primary">{diagTransactions} tx</span>
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="50"
                    value={diagTransactions}
                    onChange={(e) => setDiagTransactions(Number(e.target.value))}
                    className="w-full h-1 bg-muted rounded-lg appearance-none cursor-pointer"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-muted-foreground flex justify-between">
                    <span>Queue Count (Counter 1)</span>
                    <span className="font-bold text-primary">{diagQueue} people</span>
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="15"
                    value={diagQueue}
                    onChange={(e) => setDiagQueue(Number(e.target.value))}
                    className="w-full h-1 bg-muted rounded-lg appearance-none cursor-pointer"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-muted-foreground flex justify-between">
                    <span>Employee Inactivity Time</span>
                    <span className="font-bold text-primary">{diagDuration} mins</span>
                  </label>
                  <input
                    type="range"
                    min="5"
                    max="60"
                    value={diagDuration}
                    onChange={(e) => setDiagDuration(Number(e.target.value))}
                    className="w-full h-1 bg-muted rounded-lg appearance-none cursor-pointer"
                  />
                </div>

                <Button
                  className="w-full text-xs font-semibold flex items-center justify-center gap-1.5 mt-2"
                  onClick={runDiagnostic}
                  disabled={diagLoading}
                >
                  <Play className="h-3.5 w-3.5 fill-current" />
                  <span>{diagLoading ? "Evaluating Rules..." : "Trigger AI Evaluation"}</span>
                </Button>
              </CardContent>
            </Card>

            {/* Results Console */}
            <Card className="md:col-span-2 border border-border shadow-sm">
              <CardHeader>
                <CardTitle className="text-sm font-bold flex items-center gap-1.5">
                  <Activity className="h-4.5 w-4.5 text-rose-500" />
                  Evaluation Results Console
                </CardTitle>
                <CardDescription>
                  Results from running input parameters against the active rule engine.
                </CardDescription>
              </CardHeader>
              <CardContent className="h-80 overflow-y-auto border border-border rounded-lg p-4 bg-muted/5 font-mono text-xs text-slate-800">
                {diagTriggered.length === 0 ? (
                  <div className="text-center text-muted-foreground py-16">
                    Adjust variables and click &quot;Trigger AI Evaluation&quot; to run diagnostics.
                  </div>
                ) : (
                  <div className="space-y-3">
                    <p className="text-emerald-600 font-semibold">{"// EVALUATION COMPLETED SUCCESSFULLY"}</p>
                    <p className="text-slate-500">{"// Store Evaluated: "}{diagStore}</p>
                    <p className="text-slate-500">{"// Date Checked: "}{new Date().toISOString()}</p>
                    <p className="text-slate-500">{"-------------------------------------------"}</p>
                    {diagTriggered.map((alert, idx) => (
                      <div key={idx} className="p-2 border border-indigo-150 rounded bg-indigo-50/20 text-indigo-800">
                        <span className="font-bold text-indigo-600">ALERT TRIGGERED: </span>
                        <span>{alert.type.toUpperCase()} (ID: {alert.id})</span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

          </div>
        )}

      </div>
    </PageShell>
  );
}
