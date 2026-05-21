export interface FootfallDailyPoint {
  day: string;
  unique_visitors: number;
  total_detections: number;
}

export interface FootfallHourlyPoint {
  bucket_start: string;
  count: number;
}

export interface FootfallResponse {
  daily: FootfallDailyPoint[];
  hourly: FootfallHourlyPoint[];
}

export interface FootfallKpi {
  day: string;
  uniqueVisitors: number;
  totalDetections: number;
  avgDetectionsPerVisitor: number;
}

export interface FootfallTrend {
  direction: "up" | "down" | "flat";
  percentChange: number;
}

/** Aggregate footfall API data into store KPIs */
export function computeFootfallKpis(footfall: FootfallResponse): FootfallKpi[] {
  return footfall.daily.map((d) => ({
    day: d.day,
    uniqueVisitors: d.unique_visitors,
    totalDetections: d.total_detections,
    avgDetectionsPerVisitor:
      d.unique_visitors > 0
        ? Math.round((d.total_detections / d.unique_visitors) * 10) / 10
        : 0,
  }));
}

export function computeFootfallTrend(
  footfall: FootfallResponse
): FootfallTrend | null {
  const sorted = [...footfall.daily].sort((a, b) =>
    a.day.localeCompare(b.day)
  );
  if (sorted.length < 2) return null;

  const prev = sorted[sorted.length - 2].unique_visitors;
  const curr = sorted[sorted.length - 1].unique_visitors;
  if (prev === 0) {
    return { direction: curr > 0 ? "up" : "flat", percentChange: 0 };
  }
  const pct = Math.round(((curr - prev) / prev) * 100);
  return {
    direction: pct > 0 ? "up" : pct < 0 ? "down" : "flat",
    percentChange: pct,
  };
}

export function sumHourlyFootfall(footfall: FootfallResponse): number {
  return footfall.hourly.reduce((sum, h) => sum + h.count, 0);
}
