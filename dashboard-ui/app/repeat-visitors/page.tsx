"use client";

import { DataTable } from "@/components/DataTable";
import { ErrorBanner } from "@/components/ErrorBanner";
import { Header } from "@/components/layout/Header";
import { LoadingState } from "@/components/LoadingState";
import { StatCard } from "@/components/StatCard";
import {
  useCustomers,
  useIdentityStats,
  useRepeatVisitors,
} from "@/hooks/useIdentity";
import type { RepeatVisitor } from "@/services/identity-types";
import { formatDateTime, formatNumber } from "@/utils/format";
import { UserCheck, UserPlus } from "lucide-react";

export default function RepeatVisitorsPage() {
  const { data: repeat, error, loading, refresh } = useRepeatVisitors();
  const { data: customers } = useCustomers();
  const { data: stats } = useIdentityStats();

  const newCount =
    customers?.filter((c) => c.visit_count <= 1).length ?? stats?.new_visitors_today ?? 0;

  const columns = [
    {
      key: "person_id",
      header: "Person ID",
      className: "font-mono text-xs max-w-[220px] truncate",
      render: (r: RepeatVisitor) => r.person_id,
    },
    {
      key: "visit_count",
      header: "Visits",
      render: (r: RepeatVisitor) => formatNumber(r.visit_count),
    },
    {
      key: "first_seen",
      header: "First seen",
      render: (r: RepeatVisitor) => formatDateTime(r.first_seen),
    },
    {
      key: "last_seen",
      header: "Last seen",
      render: (r: RepeatVisitor) => formatDateTime(r.last_seen),
    },
  ];

  return (
    <>
      <Header
        title="Repeat vs new"
        subtitle="Visitor frequency insights"
        onRefresh={refresh}
        refreshing={loading && !!repeat}
      />
      <main className="flex-1 space-y-6 p-4 md:p-6">
        {error && <ErrorBanner message={error} onRetry={refresh} />}
        {loading && !repeat && <LoadingState />}
        {repeat && (
          <>
            <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <StatCard
                title="Repeat visitors"
                value={formatNumber(repeat.length)}
                icon={UserCheck}
                accent="blue"
              />
              <StatCard
                title="New / single visit"
                value={formatNumber(newCount)}
                icon={UserPlus}
                accent="green"
              />
              <StatCard
                title="Total customers"
                value={formatNumber(stats?.total_customers ?? customers?.length ?? 0)}
                accent="amber"
              />
            </section>
            <DataTable
              columns={columns}
              rows={repeat}
              keyExtractor={(r) => r.person_id}
              emptyMessage="No repeat visitors yet (need 2+ visits)"
            />
          </>
        )}
      </main>
    </>
  );
}
