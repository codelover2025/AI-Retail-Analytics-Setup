"use client";

import Link from "next/link";
import { Building2, Camera, Shield, Users } from "lucide-react";
import { PageShell } from "@/components/enterprise/PageShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useCachedQuery } from "@/hooks/useCachedQuery";
import { fetchCameras } from "@/services/multi-camera-analytics";
import { fetchEmployees } from "@/services/identity-api";
import { fetchDashboardOverview } from "@/services/dashboard-api";
import { fetchPlatformUsers } from "@/services/rbac-api";

export default function AdminPage() {
  const { data, loading, error, refresh } = useCachedQuery({
    key: { page: "admin" },
    fetcher: async () => {
      const [overview, cameras, employees, users] = await Promise.all([
        fetchDashboardOverview({}),
        fetchCameras(),
        fetchEmployees(),
        fetchPlatformUsers().catch(() => []),
      ]);
      return { overview, cameras, employees, users };
    },
  });

  return (
    <PageShell
      title="Admin panel"
      subtitle="Manage stores, cameras, employees, and users"
      loading={loading && !data}
      error={error}
      onRefresh={refresh}
      refreshing={loading}
    >
      {data && (
        <>
          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Building2 className="h-4 w-4" />
                  Stores
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{data.overview.summary.store_count}</p>
                <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
                  {data.overview.stores.map((s) => (
                    <li key={s.store_id}>{s.store_id}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Camera className="h-4 w-4" />
                  Cameras
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{data.cameras.length}</p>
                <ul className="mt-2 max-h-24 space-y-1 overflow-y-auto text-sm text-muted-foreground">
                  {data.cameras.map((c) => (
                    <li key={c.camera_id}>{c.name ?? c.camera_id}</li>
                  ))}
                </ul>
                <Button size="sm" variant="outline" className="mt-2" asChild>
                  <Link href="/admin/cameras">Manage cameras</Link>
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Users className="h-4 w-4" />
                  Employees
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{data.employees.length}</p>
                <Button size="sm" variant="outline" className="mt-2" asChild>
                  <Link href="/employees">Manage employees</Link>
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Shield className="h-4 w-4" />
                  Users
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{data.users.length}</p>
                <Button size="sm" variant="outline" className="mt-2" asChild>
                  <Link href="/admin/roles">Roles & RBAC</Link>
                </Button>
              </CardContent>
            </Card>
          </section>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Provisioning</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              <p>
                Store and camera provisioning uses{" "}
                <code className="rounded bg-muted px-1">POST /api/v1/admin/*</code> with API key auth.
                Use your deployment scripts or API client for create operations.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <Button variant="outline" size="sm" asChild>
                  <Link href="/employees">Employees</Link>
                </Button>
                <Button variant="outline" size="sm" asChild>
                  <Link href="/customers">Customers</Link>
                </Button>
                <Button variant="outline" size="sm" asChild>
                  <Link href="/admin/roles">RBAC</Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </PageShell>
  );
}
