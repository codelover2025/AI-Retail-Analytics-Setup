import type { FootfallResponse } from "../footfall";
import type { RecognitionItem } from "../dwell_time";

export interface LiveVisitorsResponse {
  count: number;
  timestamp: string;
}

export interface AlertItem {
  type: string;
  message: string;
  time: string;
}
import { computeFootfallKpis, computeFootfallTrend } from "../footfall";
import { estimateDwellDistribution } from "../dwell_time";

export interface StoreReport {
  generatedAt: string;
  live: LiveVisitorsResponse;
  footfallKpis: ReturnType<typeof computeFootfallKpis>;
  footfallTrend: ReturnType<typeof computeFootfallTrend>;
  recognitionTotal: number;
  alertTotal: number;
  dwellBuckets: ReturnType<typeof estimateDwellDistribution>;
  highlights: string[];
}

/** Build a text-friendly store summary from API payloads */
export function buildStoreReport(
  live: LiveVisitorsResponse,
  recognitions: RecognitionItem[],
  footfall: FootfallResponse,
  alerts: AlertItem[]
): StoreReport {
  const footfallKpis = computeFootfallKpis(footfall);
  const footfallTrend = computeFootfallTrend(footfall);
  const dwellBuckets = estimateDwellDistribution(recognitions);

  const highlights: string[] = [];
  highlights.push(`${live.count} visitors in store right now`);
  const latest = footfallKpis[footfallKpis.length - 1];
  if (latest) {
    highlights.push(
      `${latest.uniqueVisitors} unique visitors on ${latest.day}`
    );
  }
  if (footfallTrend) {
    highlights.push(
      `Footfall trend: ${footfallTrend.direction} (${footfallTrend.percentChange}% vs prior day)`
    );
  }
  if (alerts.length > 0) {
    highlights.push(`${alerts.length} active alert(s)`);
  }

  return {
    generatedAt: new Date().toISOString(),
    live,
    footfallKpis,
    footfallTrend,
    recognitionTotal: recognitions.length,
    alertTotal: alerts.length,
    dwellBuckets,
    highlights,
  };
}
