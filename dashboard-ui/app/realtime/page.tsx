"use client";

import { useMemo } from "react";
import { Activity, Bell, Camera, Radio, Users } from "lucide-react";
import { PageShell } from "@/components/enterprise/PageShell";
import { KpiCard } from "@/components/enterprise/KpiCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useCachedQuery } from "@/hooks/useCachedQuery";
import { useSSE } from "@/hooks/useSSE";
import { useWebSocket } from "@/hooks/useWebSocket";
import { fetchAlerts, fetchLiveVisitors, fetchRecognitions } from "@/services/analytics";
import { fetchCameraBreakdown } from "@/services/dashboard-api";
import { formatNumber } from "@/utils/format";

export default function RealtimePage() {
  const storeId = process.env.NEXT_PUBLIC_STORE_ID ?? "store-001";

  const { data, loading, error, refresh } = useCachedQuery({
    key: { page: "realtime" },
    fetcher: async () => {
      const [live, recognitions, alerts, cameras] = await Promise.all([
        fetchLiveVisitors(),
        fetchRecognitions(30),
        fetchAlerts(20),
        fetchCameraBreakdown({ store_id: storeId }),
      ]);
      return { live, recognitions, alerts, cameras };
    },
    ttlMs: 15_000,
  });

  const sseLive = useSSE(`/stream/live-visitors?store_id=${storeId}`);
  const sseEvents = useSSE(`/stream/events?store_id=${storeId}`);
  const sseHealth = useSSE(`/stream/camera-health?store_id=${storeId}`);
  const ws = useWebSocket("/ws/live");

  const liveCount = useMemo(() => {
    const sseMsg = sseLive.messages.find((m) => m.event === "live_visitors");
    if (sseMsg && typeof sseMsg.data === "object" && sseMsg.data && "count" in (sseMsg.data as object)) {
      return (sseMsg.data as { count: number }).count;
    }
    return data?.live.count ?? 0;
  }, [sseLive.messages, data]);

  const streamEvents = [...sseEvents.messages, ...ws.messages].slice(0, 20);

  return (
    <PageShell
      title="Realtime monitoring"
      subtitle="Live visitors, recognition events, alerts, and camera status"
      loading={loading && !data}
      error={error}
      onRefresh={refresh}
      refreshing={loading}
    >
      {data && (
        <>
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <KpiCard title="Active visitors" value={formatNumber(liveCount)} subtitle="SSE + API" icon={Users} />
            <KpiCard title="Recognitions" value={data.recognitions.length} icon={Activity} />
            <KpiCard title="Alerts" value={data.alerts.length} icon={Bell} />
            <KpiCard
              title="Streams"
              value={[sseLive.connected, sseEvents.connected, ws.connected].filter(Boolean).length}
              subtitle="of 3 connected"
              icon={Radio}
            />
          </section>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-base">Recognition events</CardTitle>
                <Badge variant={sseEvents.connected ? "success" : "warning"}>
                  {sseEvents.connected ? "SSE live" : "Polling"}
                </Badge>
              </CardHeader>
              <CardContent className="max-h-80 space-y-2 overflow-y-auto">
                {data.recognitions.slice(0, 15).map((r) => (
                  <div key={r.id} className="rounded-lg border border-border px-3 py-2 text-sm">
                    <span className="font-medium">{r.type}</span>
                    <span className="ml-2 text-xs text-muted-foreground">
                      {new Date(r.time).toLocaleTimeString()}
                    </span>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Alerts</CardTitle>
              </CardHeader>
              <CardContent className="max-h-80 space-y-2 overflow-y-auto">
                {data.alerts.map((a, i) => (
                  <div key={i} className="rounded-lg border border-border px-3 py-2 text-sm">
                    <p className="font-medium">{a.type}</p>
                    <p className="text-xs text-muted-foreground">{a.message}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-base">Camera status</CardTitle>
              <Badge variant={sseHealth.connected ? "success" : "outline"}>
                Health stream {sseHealth.connected ? "on" : "off"}
              </Badge>
            </CardHeader>
            <CardContent className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {data.cameras.cameras.map((cam) => (
                <div key={cam.camera_id} className="flex items-center gap-2 rounded-lg border border-border px-3 py-2">
                  <Camera className="h-4 w-4 text-primary" />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{cam.name ?? cam.camera_id}</p>
                  </div>
                  <Badge variant={cam.enabled ? "success" : "destructive"}>
                    {cam.enabled ? "OK" : "Off"}
                  </Badge>
                </div>
              ))}
            </CardContent>
          </Card>

          {streamEvents.length > 0 && (
            <Card>
              <CardHeader><CardTitle className="text-base">Live stream feed</CardTitle></CardHeader>
              <CardContent className="max-h-48 overflow-y-auto font-mono text-xs">
                {streamEvents.map((ev, i) => (
                  <pre key={i} className="mb-2 rounded bg-muted p-2">
                    {JSON.stringify(ev, null, 2)}
                  </pre>
                ))}
              </CardContent>
            </Card>
          )}
        </>
      )}
    </PageShell>
  );
}
