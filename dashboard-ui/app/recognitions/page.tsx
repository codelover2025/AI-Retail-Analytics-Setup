"use client";

import { DataTable } from "@/components/DataTable";
import { ErrorBanner } from "@/components/ErrorBanner";
import { Header } from "@/components/layout/Header";
import { LoadingState } from "@/components/LoadingState";
import { useIdentityRecognitions } from "@/hooks/useIdentity";
import type { IdentityRecognition } from "@/services/identity-types";
import { formatDateTime } from "@/utils/format";
import clsx from "clsx";

function typeBadge(type: string) {
  const styles: Record<string, string> = {
    employee: "bg-violet-100 text-violet-800",
    new_visitor: "bg-emerald-100 text-emerald-800",
    repeat_visitor: "bg-brand-100 text-brand-800",
    customer: "bg-sky-100 text-sky-800",
    vip: "bg-amber-100 text-amber-800",
  };
  return (
    <span
      className={clsx(
        "inline-flex rounded-full px-2 py-0.5 text-xs font-medium",
        styles[type] ?? "bg-slate-100 text-slate-700"
      )}
    >
      {type}
    </span>
  );
}

export default function RecognitionsPage() {
  const { data, error, loading, refresh } = useIdentityRecognitions(500);

  const columns = [
    {
      key: "timestamp",
      header: "Time",
      render: (r: IdentityRecognition) => formatDateTime(r.timestamp),
    },
    {
      key: "type",
      header: "Type",
      render: (r: IdentityRecognition) => typeBadge(r.type),
    },
    {
      key: "person_id",
      header: "Person ID",
      className: "font-mono text-xs max-w-[180px] truncate",
      render: (r: IdentityRecognition) => r.person_id,
    },
    {
      key: "camera_id",
      header: "Camera",
      render: (r: IdentityRecognition) => r.camera_id,
    },
  ];

  return (
    <>
      <Header
        title="Recognition logs"
        subtitle="Raw events from AI pipeline"
        onRefresh={refresh}
        refreshing={loading && !!data}
      />
      <main className="flex-1 space-y-4 p-4 md:p-6">
        {error && <ErrorBanner message={error} onRetry={refresh} />}
        {loading && !data && <LoadingState />}
        {data && (
          <>
            <p className="text-sm text-slate-500">
              {data.length} recognition{data.length === 1 ? "" : "s"}
            </p>
            <DataTable
              columns={columns}
              rows={data}
              keyExtractor={(r) => r.id}
              emptyMessage="No logs — POST to /api/ingest/recognition or run seed_identity_demo.py"
            />
          </>
        )}
      </main>
    </>
  );
}
