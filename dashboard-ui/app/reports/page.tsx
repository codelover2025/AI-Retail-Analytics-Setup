"use client";

import { useEffect, useState } from "react";
import { Download, FileText, History, Timer } from "lucide-react";
import { PageShell } from "@/components/enterprise/PageShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { FilterBar, FilterField, filterInputClass } from "@/components/enterprise/FilterBar";
import { useCachedQuery } from "@/hooks/useCachedQuery";
import {
  buildDownloadUrl,
  createReportSchedule,
  fetchReportJob,
  generateReport,
  listReportJobs,
  listReportSchedules,
  type ReportJob,
} from "@/services/reports-api";
import { defaultDateRange } from "@/lib/utils";

export default function ReportsPage() {
  const initial = defaultDateRange(7);
  const [reportType, setReportType] = useState("weekly");
  const [format, setFormat] = useState("pdf");
  const [fromDay, setFromDay] = useState(initial.from);
  const [toDay, setToDay] = useState(initial.to);
  const [generating, setGenerating] = useState(false);

  // Persistent job history from DB
  const {
    data: jobHistory,
    loading: historyLoading,
    error: historyError,
    refresh: refreshHistory,
  } = useCachedQuery<ReportJob[]>({
    key: { page: "report-jobs" },
    fetcher: () => listReportJobs(50),
    ttlMs: 10_000,
  });

  const { data: schedules, loading, error, refresh } = useCachedQuery({
    key: { page: "reports" },
    fetcher: () => listReportSchedules(),
  });

  async function handleGenerate() {
    setGenerating(true);
    try {
      const { job_id } = await generateReport({
        report_type: reportType,
        output_format: format,
        from_day: fromDay,
        to_day: toDay,
      });

      // Poll until complete, then refresh history
      const poll = async () => {
        const job = await fetchReportJob(job_id);
        if (job.status === "pending" || job.status === "running") {
          setTimeout(poll, 2000);
        } else {
          refreshHistory();
        }
      };
      await poll();
    } finally {
      setGenerating(false);
    }
  }

  async function handleSchedule() {
    await createReportSchedule({
      report_type: reportType,
      output_format: format,
      cron_expr: "0 8 * * 1",
      delivery_channels: ["email"],
      recipients: [],
    });
    refresh();
  }

  return (
    <PageShell
      title="Report center"
      subtitle="Generate, schedule, and download analytics reports"
      loading={loading && !schedules}
      error={error}
      onRefresh={refresh}
      refreshing={loading}
    >
      <FilterBar>
        <FilterField label="Type">
          <select className={filterInputClass()} value={reportType} onChange={(e) => setReportType(e.target.value)}>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
            <option value="custom">Custom</option>
          </select>
        </FilterField>
        <FilterField label="Format">
          <select className={filterInputClass()} value={format} onChange={(e) => setFormat(e.target.value)}>
            <option value="pdf">PDF</option>
            <option value="excel">Excel</option>
            <option value="csv">CSV</option>
          </select>
        </FilterField>
        <FilterField label="From">
          <input type="date" className={filterInputClass()} value={fromDay} onChange={(e) => setFromDay(e.target.value)} />
        </FilterField>
        <FilterField label="To">
          <input type="date" className={filterInputClass()} value={toDay} onChange={(e) => setToDay(e.target.value)} />
        </FilterField>
        <div className="flex gap-2 self-end">
          <Button onClick={handleGenerate} disabled={generating}>
            <FileText className="h-4 w-4" />
            {generating ? "Generating…" : "Generate"}
          </Button>
          <Button variant="outline" onClick={handleSchedule}>
            <Timer className="h-4 w-4" />
            Schedule
          </Button>
        </div>
      </FilterBar>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Persistent Report History */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <History className="h-4 w-4" />
              Report history
              {historyLoading && (
                <span className="ml-auto text-xs font-normal text-muted-foreground">Loading…</span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="max-h-80 space-y-2 overflow-y-auto">
            {!jobHistory?.length ? (
              <p className="text-sm text-muted-foreground">No reports generated yet.</p>
            ) : (
              jobHistory.map((job) => (
                <div
                  key={job.job_id}
                  className="flex items-center justify-between rounded-lg border border-border px-3 py-2"
                >
                  <div>
                    <p className="text-sm font-medium">{job.report_type} · {job.output_format.toUpperCase()}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(job.created_at).toLocaleString()}
                      {job.requested_by ? ` · ${job.requested_by}` : ""}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={job.status === "completed" ? "success" : job.status === "failed" ? "destructive" : "secondary"}>
                      {job.status}
                    </Badge>
                    {job.download_url && (
                      <Button size="sm" variant="outline" asChild>
                        <a href={buildDownloadUrl(job.download_url)} target="_blank" rel="noreferrer">
                          <Download className="h-3 w-3" />
                        </a>
                      </Button>
                    )}
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Scheduled Reports */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Timer className="h-4 w-4" />
              Scheduled reports
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {!schedules?.length ? (
              <p className="text-sm text-muted-foreground">No schedules configured.</p>
            ) : (
              schedules.map((s) => (
                <div key={s.id} className="rounded-lg border border-border px-3 py-2">
                  <p className="text-sm font-medium">{s.report_type} · {s.output_format.toUpperCase()}</p>
                  <p className="text-xs text-muted-foreground">Cron: {s.cron_expr}</p>
                  <p className="text-xs text-muted-foreground">
                    Channels: {s.delivery_channels?.join(", ") || "none"}
                  </p>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </PageShell>
  );
}
