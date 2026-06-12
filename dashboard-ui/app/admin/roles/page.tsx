"use client";

import { Shield } from "lucide-react";
import { PageShell } from "@/components/enterprise/PageShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useCachedQuery } from "@/hooks/useCachedQuery";
import {
  fetchAuditLogs,
  fetchPlatformUsers,
  PERMISSIONS_MATRIX,
  ROLES,
} from "@/services/rbac-api";

export default function RolesPage() {
  const { data, loading, error, refresh } = useCachedQuery({
    key: { page: "rbac" },
    fetcher: async () => {
      const [users, audit] = await Promise.all([
        fetchPlatformUsers().catch(() => []),
        fetchAuditLogs(30).catch(() => []),
      ]);
      return { users, audit };
    },
  });

  return (
    <PageShell
      title="Role management"
      subtitle="RBAC permissions matrix and user audit trail"
      loading={loading && !data}
      error={error}
      onRefresh={refresh}
      refreshing={loading}
    >
      {data && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Shield className="h-4 w-4" />
                Permissions matrix
              </CardTitle>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left">
                    <th className="pb-2 pr-4">Role</th>
                    <th className="pb-2">Permissions</th>
                  </tr>
                </thead>
                <tbody>
                  {ROLES.map((role) => (
                    <tr key={role} className="border-b border-border/50">
                      <td className="py-2 pr-4 font-medium">{role}</td>
                      <td className="py-2">
                        <div className="flex flex-wrap gap-1">
                          {(PERMISSIONS_MATRIX[role] ?? []).map((p) => (
                            <Badge key={p} variant="secondary">{p}</Badge>
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Platform users</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {data.users.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No users returned — JWT auth may be required for RBAC endpoints.
                  </p>
                ) : (
                  data.users.map((u) => (
                    <div key={u.id} className="flex items-center justify-between rounded-lg border border-border px-3 py-2">
                      <div>
                        <p className="text-sm font-medium">{u.email}</p>
                        <p className="text-xs text-muted-foreground">{u.store_id ?? "brand-wide"}</p>
                      </div>
                      <Badge>{u.role}</Badge>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Audit log</CardTitle>
              </CardHeader>
              <CardContent className="max-h-80 space-y-2 overflow-y-auto">
                {data.audit.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No audit entries available.</p>
                ) : (
                  data.audit.map((entry) => (
                    <div key={entry.id} className="rounded-lg border border-border px-3 py-2 text-sm">
                      <p className="font-medium">{entry.action}</p>
                      <p className="text-xs text-muted-foreground">
                        {entry.actor} · {new Date(entry.created_at).toLocaleString()}
                      </p>
                    </div>
                  ))
                )}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </PageShell>
  );
}
