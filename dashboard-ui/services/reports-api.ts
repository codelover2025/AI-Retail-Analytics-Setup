import { apiClient } from "./api";

export interface ReportJob {
  job_id: string;
  status: string;
  report_type: string;
  output_format: string;
  created_at: string;
  completed_at?: string | null;
  error_message?: string | null;
  download_url?: string | null;
}

export interface ReportSchedule {
  id: string;
  report_type: string;
  output_format: string;
  cron_expr: string;
  delivery_channels: string[];
  recipients: string[];
  is_active: boolean;
  created_at: string;
}

export async function generateReport(body: {
  report_type: string;
  output_format: string;
  store_ids?: string[];
  from_day?: string;
  to_day?: string;
}) {
  const { data } = await apiClient.post<{ job_id: string; status: string }>(
    "/api/reports/generate",
    body
  );
  return data;
}

export async function fetchReportJob(jobId: string): Promise<ReportJob> {
  const { data } = await apiClient.get<ReportJob>(`/api/reports/export/${jobId}`);
  return data;
}

export async function listReportSchedules(): Promise<ReportSchedule[]> {
  const { data } = await apiClient.get<ReportSchedule[]>("/api/reports/schedule");
  return data;
}

export async function createReportSchedule(body: {
  report_type: string;
  output_format: string;
  cron_expr: string;
  store_ids?: string[];
  delivery_channels?: string[];
  recipients?: string[];
}) {
  const { data } = await apiClient.post("/api/reports/schedule", body);
  return data;
}

export async function deleteReportSchedule(scheduleId: string) {
  await apiClient.delete(`/api/reports/schedule/${scheduleId}`);
}
