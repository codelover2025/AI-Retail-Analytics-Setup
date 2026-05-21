import type {
  AlertItem,
  FootfallResponse,
  RecognitionItem,
  RecognitionType,
} from "@/services/types";

export interface DashboardKpis {
  liveCount: number;
  liveUpdatedAt: string;
  todayUniqueVisitors: number;
  todayTotalDetections: number;
  recognitionCount24h: number;
  newVisitors24h: number;
  repeatVisitors24h: number;
  vipCount24h: number;
  alertCount: number;
}

export interface RecognitionBreakdown {
  type: RecognitionType | string;
  label: string;
  count: number;
}

export interface HourlyChartPoint {
  label: string;
  count: number;
  bucket_start: string;
}

export interface DailyChartPoint {
  label: string;
  unique_visitors: number;
  total_detections: number;
  day: string;
}

export interface DashboardSummary {
  kpis: DashboardKpis;
  recognitionBreakdown: RecognitionBreakdown[];
  hourlyChart: HourlyChartPoint[];
  dailyChart: DailyChartPoint[];
  recentAlerts: AlertItem[];
}

const MS_24H = 24 * 60 * 60 * 1000;

function isWithin24h(iso: string): boolean {
  return Date.now() - new Date(iso).getTime() <= MS_24H;
}

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10);
}

export function processFootfallCharts(footfall: FootfallResponse): {
  hourlyChart: HourlyChartPoint[];
  dailyChart: DailyChartPoint[];
} {
  const hourlyChart = footfall.hourly.map((h) => ({
    bucket_start: h.bucket_start,
    label: new Intl.DateTimeFormat(undefined, {
      month: "short",
      day: "numeric",
      hour: "numeric",
    }).format(new Date(h.bucket_start)),
    count: h.count,
  }));

  const dailyChart = footfall.daily.map((d) => ({
    day: d.day,
    label: new Intl.DateTimeFormat(undefined, {
      month: "short",
      day: "numeric",
    }).format(new Date(d.day + "T12:00:00")),
    unique_visitors: d.unique_visitors,
    total_detections: d.total_detections,
  }));

  return { hourlyChart, dailyChart };
}

export function processRecognitionBreakdown(
  recognitions: RecognitionItem[]
): RecognitionBreakdown[] {
  const counts = new Map<string, number>();
  for (const r of recognitions) {
    counts.set(r.type, (counts.get(r.type) ?? 0) + 1);
  }
  const order: RecognitionType[] = [
    "vip",
    "new_visitor",
    "repeat_visitor",
    "visitor",
  ];
  const labels: Record<string, string> = {
    vip: "VIP",
    new_visitor: "New",
    repeat_visitor: "Repeat",
    visitor: "Other",
  };
  return order
    .filter((t) => counts.has(t))
    .map((type) => ({
      type,
      label: labels[type] ?? type,
      count: counts.get(type) ?? 0,
    }));
}

export function buildDashboardSummary(
  live: { count: number; timestamp: string },
  recognitions: RecognitionItem[],
  footfall: FootfallResponse,
  alerts: AlertItem[]
): DashboardSummary {
  const today = todayIsoDate();
  const todayRow = footfall.daily.find((d) => d.day === today);
  const rec24 = recognitions.filter((r) => isWithin24h(r.time));

  const kpis: DashboardKpis = {
    liveCount: live.count,
    liveUpdatedAt: live.timestamp,
    todayUniqueVisitors: todayRow?.unique_visitors ?? 0,
    todayTotalDetections: todayRow?.total_detections ?? 0,
    recognitionCount24h: rec24.length,
    newVisitors24h: rec24.filter((r) => r.type === "new_visitor").length,
    repeatVisitors24h: rec24.filter((r) => r.type === "repeat_visitor").length,
    vipCount24h: rec24.filter((r) => r.type === "vip").length,
    alertCount: alerts.length,
  };

  const { hourlyChart, dailyChart } = processFootfallCharts(footfall);

  return {
    kpis,
    recognitionBreakdown: processRecognitionBreakdown(rec24),
    hourlyChart,
    dailyChart,
    recentAlerts: alerts.slice(0, 5),
  };
}
