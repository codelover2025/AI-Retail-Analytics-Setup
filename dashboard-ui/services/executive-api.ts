import { apiClient } from "./api";
import { fetchDashboardOverview, fetchStoreComparison } from "./dashboard-api";

export interface ConversionAnalytics {
  total_visitors: number;
  total_transactions: number;
  conversion_rate: number;
  total_revenue: number;
  revenue_per_visitor: number;
  stores?: Array<{
    store_id: string;
    visitors: number;
    transactions: number;
    conversion_rate: number;
    revenue: number;
  }>;
}

export async function fetchConversionAnalytics(params?: {
  store_id?: string;
  from_day?: string;
  to_day?: string;
  days?: number;
}): Promise<ConversionAnalytics> {
  const { data } = await apiClient.get<ConversionAnalytics>("/api/pos/analytics", { params });
  return data;
}

export async function fetchExecutiveSnapshot(params: {
  from_day?: string;
  to_day?: string;
}) {
  const [overview, conversion] = await Promise.all([
    fetchDashboardOverview(params),
    fetchConversionAnalytics({ ...params, days: 30 }),
  ]);
  const topStores = [...overview.stores]
    .sort((a, b) => b.total_visitors - a.total_visitors)
    .slice(0, 5);
  const comparison =
    topStores.length >= 2
      ? await fetchStoreComparison(
          topStores.map((s) => s.store_id),
          params
        )
      : null;
  return { overview, conversion, comparison };
}
