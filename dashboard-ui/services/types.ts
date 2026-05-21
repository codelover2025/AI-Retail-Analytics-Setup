/** Strict API contract — mirrors backend_core/schemas/contract.py */

export type RecognitionType =
  | "vip"
  | "new_visitor"
  | "repeat_visitor"
  | "visitor";

export interface LiveVisitorsResponse {
  count: number;
  timestamp: string;
}

export interface RecognitionItem {
  id: string;
  type: RecognitionType;
  time: string;
}

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

export interface AlertItem {
  type: string;
  message: string;
  time: string;
}
