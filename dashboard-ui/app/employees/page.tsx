"use client";

import { DataTable } from "@/components/DataTable";
import { ErrorBanner } from "@/components/ErrorBanner";
import { Header } from "@/components/layout/Header";
import { LoadingState } from "@/components/LoadingState";
import { useEmployees, useIdentityRecognitions } from "@/hooks/useIdentity";
import type { Employee } from "@/services/identity-types";
import { formatDateTime } from "@/utils/format";
import { BadgeCheck } from "lucide-react";

export default function EmployeesPage() {
  const { data: employees, error, loading, refresh } = useEmployees();
  const { data: logs } = useIdentityRecognitions(200);

  const employeeIds = new Set(
    logs?.filter((r) => r.type === "employee").map((r) => r.person_id) ?? []
  );

  const columns = [
    {
      key: "name",
      header: "Name",
      render: (e: Employee) => (
        <span className="font-medium text-slate-800">{e.name}</span>
      ),
    },
    {
      key: "id",
      header: "Employee ID",
      className: "font-mono text-xs",
      render: (e: Employee) => e.id,
    },
    {
      key: "created_at",
      header: "Tagged",
      render: (e: Employee) => formatDateTime(e.created_at),
    },
    {
      key: "seen",
      header: "Recent sighting",
      render: (e: Employee) =>
        employeeIds.has(e.id) ? (
          <span className="text-emerald-600 text-xs font-medium">Active</span>
        ) : (
          <span className="text-slate-400 text-xs">—</span>
        ),
    },
  ];

  return (
    <>
      <Header
        title="Employees"
        subtitle="Staff tagging from recognition type"
        onRefresh={refresh}
        refreshing={loading && !!employees}
      />
      <main className="flex-1 space-y-6 p-4 md:p-6">
        {error && <ErrorBanner message={error} onRetry={refresh} />}
        {loading && !employees && <LoadingState />}
        {employees && (
          <>
            <div className="flex items-center gap-2 rounded-lg border border-violet-100 bg-violet-50 px-4 py-3 text-sm text-violet-900">
              <BadgeCheck className="h-4 w-4 shrink-0" />
              Recognitions with type <strong>employee</strong> are shown in logs and
              linked here.
            </div>
            <DataTable
              columns={columns}
              rows={employees}
              keyExtractor={(e) => e.id}
              emptyMessage="No employees tagged yet"
            />
          </>
        )}
      </main>
    </>
  );
}
