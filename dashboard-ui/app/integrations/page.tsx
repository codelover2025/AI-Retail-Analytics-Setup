"use client";

import { useState } from "react";
import { MessageCircle, Monitor, RefreshCw, ShoppingCart, Users } from "lucide-react";
import { PageShell } from "@/components/enterprise/PageShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useCachedQuery } from "@/hooks/useCachedQuery";
import { fetchDetailedHealth, triggerPOSSync } from "@/services/integrations-api";
import { syncHRMSEmployees } from "@/services/staff-api";

const INTEGRATIONS = [
  { id: "whatsapp", label: "WhatsApp", icon: MessageCircle },
  { id: "pos", label: "POS", icon: ShoppingCart },
  { id: "crm", label: "CRM", icon: Users },
  { id: "hrms", label: "HRMS", icon: Monitor },
] as const;

function statusVariant(status: string): "success" | "warning" | "destructive" | "secondary" {
  if (status === "ok" || status === "configured") return "success";
  if (status === "not_configured") return "warning";
  if (status === "error") return "destructive";
  return "secondary";
}

export default function IntegrationsPage() {
  const [logs, setLogs] = useState<string[]>([]);
  const [syncing, setSyncing] = useState<string | null>(null);

  const { data, loading, error, refresh } = useCachedQuery({
    key: { page: "integrations" },
    fetcher: fetchDetailedHealth,
    ttlMs: 30_000,
  });

  async function runSync(id: string) {
    setSyncing(id);
    try {
      if (id === "pos") {
        const storeId = process.env.NEXT_PUBLIC_STORE_ID ?? "store-001";
        const res = await triggerPOSSync(storeId, new Date().toISOString().slice(0, 10));
        setLogs((p) => [`POS sync: ${JSON.stringify(res)}`, ...p].slice(0, 20));
      } else if (id === "hrms") {
        const res = await syncHRMSEmployees();
        setLogs((p) => [`HRMS sync: ${JSON.stringify(res)}`, ...p].slice(0, 20));
      } else {
        setLogs((p) => [`${id}: sync triggered (provider-dependent)`, ...p].slice(0, 20));
      }
      refresh();
    } catch (e) {
      setLogs((p) => [`${id} error: ${e instanceof Error ? e.message : "failed"}`, ...p]);
    } finally {
      setSyncing(null);
    }
  }

  return (
    <PageShell
      title="Integration center"
      subtitle="WhatsApp, POS, CRM, and HRMS connection status"
      loading={loading && !data}
      error={error}
      onRefresh={refresh}
      refreshing={loading}
    >
      {data && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {INTEGRATIONS.map(({ id, label, icon: Icon }) => {
              const sub = data.subsystems[id];
              return (
                <Card key={id}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <Icon className="h-5 w-5 text-primary" />
                        <span className="font-medium">{label}</span>
                      </div>
                      <Badge variant={statusVariant(sub?.status ?? "unknown")}>
                        {sub?.status ?? "unknown"}
                      </Badge>
                    </div>
                    <p className="mt-2 text-xs text-muted-foreground">
                      Provider: {sub?.provider ?? "—"}
                    </p>
                    <Button
                      size="sm"
                      variant="outline"
                      className="mt-3 w-full"
                      disabled={syncing === id}
                      onClick={() => runSync(id)}
                    >
                      <RefreshCw className={`h-3 w-3 ${syncing === id ? "animate-spin" : ""}`} />
                      Sync now
                    </Button>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Platform health</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-2 sm:grid-cols-2">
              {Object.entries(data.subsystems).map(([name, sub]) => (
                <div key={name} className="flex items-center justify-between rounded-lg border border-border px-3 py-2 text-sm">
                  <span className="capitalize">{name}</span>
                  <Badge variant={statusVariant(sub.status)}>{sub.status}</Badge>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Sync logs</CardTitle>
            </CardHeader>
            <CardContent className="max-h-64 overflow-y-auto font-mono text-xs">
              {logs.length === 0 ? (
                <p className="text-muted-foreground">No sync activity yet.</p>
              ) : (
                logs.map((log, i) => (
                  <p key={i} className="mb-1 rounded bg-muted px-2 py-1">{log}</p>
                ))
              )}
            </CardContent>
          </Card>
        </>
      )}
    </PageShell>
  );
}
