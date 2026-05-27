"use client";

import { DataTable } from "@/components/DataTable";
import { ErrorBanner } from "@/components/ErrorBanner";
import { Header } from "@/components/layout/Header";
import { LoadingState } from "@/components/LoadingState";
import { StatCard } from "@/components/StatCard";
import { useCustomers } from "@/hooks/useIdentity";
import type { Customer } from "@/services/identity-types";
import { formatDateTime, formatNumber } from "@/utils/format";
import { Users } from "lucide-react";

export default function CustomersPage() {
  const { data, error, loading, refresh } = useCustomers();

  const columns = [
    {
      key: "id",
      header: "Customer ID",
      className: "font-mono text-xs max-w-[220px] truncate",
      render: (c: Customer) => c.id,
    },
    {
      key: "first_seen",
      header: "First seen",
      render: (c: Customer) => formatDateTime(c.first_seen),
    },
    {
      key: "last_seen",
      header: "Last seen",
      render: (c: Customer) => formatDateTime(c.last_seen),
    },
    {
      key: "visit_count",
      header: "Visits",
      render: (c: Customer) => formatNumber(c.visit_count),
    },
  ];

  const totalVisits = data?.reduce((s, c) => s + c.visit_count, 0) ?? 0;

  return (
    <>
      <Header
        title="Customers"
        subtitle="Identity insights from recognition logs"
        onRefresh={refresh}
        refreshing={loading && !!data}
      />
      <main className="flex-1 space-y-6 p-4 md:p-6">
        {error && <ErrorBanner message={error} onRetry={refresh} />}
        {loading && !data && <LoadingState />}
        {data && (
          <>
            <section className="grid gap-4 sm:grid-cols-2">
              <StatCard
                title="Total customers"
                value={formatNumber(data.length)}
                icon={Users}
                accent="blue"
              />
              <StatCard
                title="Total visits"
                value={formatNumber(totalVisits)}
                accent="green"
              />
            </section>
            <DataTable
              columns={columns}
              rows={data}
              keyExtractor={(c) => c.id}
              emptyMessage="No customers yet — run seed or ingest AI events"
            />
          </>
        )}
      </main>
    </>
  );
}
