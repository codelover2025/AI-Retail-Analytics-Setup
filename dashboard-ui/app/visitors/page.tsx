"use client";

import { DataTable } from "@/components/DataTable";
import { ErrorBanner } from "@/components/ErrorBanner";
import { Header } from "@/components/layout/Header";
import { LoadingState } from "@/components/LoadingState";
import { useRecognitions } from "@/hooks/useRecognitions";
import type { RecognitionItem } from "@/services/types";
import { formatDateTime, recognitionLabel } from "@/utils/format";
import clsx from "clsx";

function typeBadge(type: string) {
  const styles: Record<string, string> = {
    vip: "bg-amber-100 text-amber-800",
    new_visitor: "bg-emerald-100 text-emerald-800",
    repeat_visitor: "bg-brand-100 text-brand-800",
    visitor: "bg-slate-100 text-slate-700",
  };
  return (
    <span
      className={clsx(
        "inline-flex rounded-full px-2 py-0.5 text-xs font-medium",
        styles[type] ?? "bg-slate-100 text-slate-700"
      )}
    >
      {recognitionLabel(type)}
    </span>
  );
}

export default function VisitorsPage() {
  const { data, error, loading, refresh } = useRecognitions(200);

  const columns = [
    {
      key: "time",
      header: "Time",
      render: (r: RecognitionItem) => formatDateTime(r.time),
    },
    {
      key: "type",
      header: "Type",
      render: (r: RecognitionItem) => typeBadge(r.type),
    },
    {
      key: "id",
      header: "Recognition ID",
      className: "font-mono text-xs max-w-[200px] truncate",
      render: (r: RecognitionItem) => r.id,
    },
  ];

  return (
    <>
      <Header
        title="Visitors"
        subtitle="Recognition logs from edge pipeline"
        onRefresh={refresh}
        refreshing={loading && !!data}
      />
      <main className="flex-1 space-y-4 p-4 md:p-6">
        {error && <ErrorBanner message={error} onRetry={refresh} />}
        {loading && !data && <LoadingState />}
        {data && (
          <>
            <p className="text-sm text-slate-500">
              {data.length} recognition{data.length === 1 ? "" : "s"} loaded
            </p>
            <DataTable
              columns={columns}
              rows={data}
              keyExtractor={(r) => r.id}
              emptyMessage="No recognitions yet — run the edge pipeline"
            />
          </>
        )}
      </main>
    </>
  );
}
