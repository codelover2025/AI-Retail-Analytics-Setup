import { apiClient } from "./api";

export interface ChatMessageOut {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: any[] | null;
  created_at: string;
}

export interface ChatSessionOut {
  id: string;
  title: string;
  created_at: string;
}

export interface ChatResponse {
  session_id: string;
  answer: string;
  summary: string;
  kpis: any[];
  sources: any[];
  messages: ChatMessageOut[];
}

export interface ChatRequest {
  query: string;
  session_id?: string | null;
}

export interface FootfallPrediction {
  date: string;
  predicted_visitors: number;
  confidence_score: number;
}

export interface PeakHourPrediction {
  hour: number;
  label: string;
  weight: number;
}

export interface RepeatVisitorPrediction {
  date: string;
  predicted_repeat_ratio: number;
  confidence_score: number;
}

export interface ConversionProbabilityPrediction {
  date: string;
  conversion_probability: number;
  confidence_score: number;
}

export interface StaffRequirementPrediction {
  date: string;
  predicted_footfall: number;
  recommended_staff_count: number;
  confidence_score: number;
}

export interface StorePerformancePrediction {
  score: number;
  rating: string;
  metrics: {
    footfall_index: number;
    conversion_index: number;
    average_daily_footfall: number;
    conversion_rate: number;
  };
}

export interface PredictionsResponse {
  store_id: string;
  days_ahead: number;
  predictions: {
    footfall: FootfallPrediction[];
    peak_hours: PeakHourPrediction[];
    repeat_visitors: RepeatVisitorPrediction[];
    conversion_probability: ConversionProbabilityPrediction[];
    staff_requirements: StaffRequirementPrediction[];
    store_performance: StorePerformancePrediction;
  };
}

export interface ForecastItem {
  date: string;
  forecast: number;
  lower_ci: number;
  upper_ci: number;
  confidence_level: number;
}

export interface ForecastGrowthItem {
  date: string;
  forecast_growth_pct: number;
  lower_ci: number;
  upper_ci: number;
  confidence_level: number;
}

export interface ForecastRetentionItem {
  date: string;
  forecast_repeat_visitors: number;
  lower_ci: number;
  upper_ci: number;
  confidence_level: number;
}

export interface ForecastsResponse {
  store_id: string;
  horizon: "daily" | "weekly" | "monthly";
  forecasts: {
    revenue: ForecastItem[];
    growth: ForecastGrowthItem[];
    retention: ForecastRetentionItem[];
  };
}

export interface RecommendationItem {
  id: string;
  category: "staffing" | "marketing" | "layout" | "placement" | "business";
  title: string;
  description: string;
  confidence_score: number;
  impact_level: "High" | "Medium" | "Low";
  actionable_steps: string[];
}

export interface RecommendationsResponse {
  store_id: string;
  recommendations: RecommendationItem[];
}

export interface SubsystemHealth {
  status: "ok" | "degraded" | "error" | "not_configured" | "configured";
  type?: string;
  error?: string;
  provider?: string;
  pool?: any;
}

export interface HealthDetailedResponse {
  status: "ok" | "degraded" | "error";
  version: string;
  phase: number;
  env: string;
  uptime_seconds: number;
  timestamp: string;
  subsystems: Record<string, SubsystemHealth>;
}

// API methods
export async function sendChatMessage(payload: ChatRequest): Promise<ChatResponse> {
  const { data } = await apiClient.post<ChatResponse>("/api/v1/ai/assistant/chat", payload);
  return data;
}

export async function fetchChatSessions(): Promise<ChatSessionOut[]> {
  const { data } = await apiClient.get<ChatSessionOut[]>("/api/v1/ai/assistant/sessions");
  return data;
}

export async function fetchChatSessionDetails(sessionId: string): Promise<ChatMessageOut[]> {
  const { data } = await apiClient.get<ChatMessageOut[]>(`/api/v1/ai/assistant/sessions/${sessionId}`);
  return data;
}

export async function uploadSpeechToText(audioBlob: Blob, language = "en"): Promise<{
  transcription: string;
  language: string;
  filename: string;
}> {
  const formData = new FormData();
  formData.append("file", audioBlob, "recording.wav");
  const { data } = await apiClient.post("/api/v1/ai/voice/stt", formData, {
    params: { language },
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return data;
}

export async function generateTextToSpeech(text: string, language = "en"): Promise<Blob> {
  const { data } = await apiClient.post("/api/v1/ai/voice/tts", { text, language }, {
    responseType: "blob",
  });
  return data;
}

export async function fetchPredictions(params?: {
  store_id?: string;
  days_ahead?: number;
}): Promise<PredictionsResponse> {
  const { data } = await apiClient.get<PredictionsResponse>("/api/v1/ai/predictions", { params });
  return data;
}

export async function fetchForecasts(params?: {
  store_id?: string;
  horizon?: "daily" | "weekly" | "monthly";
}): Promise<ForecastsResponse> {
  const { data } = await apiClient.get<ForecastsResponse>("/api/v1/ai/forecasts", { params });
  return data;
}

export async function fetchRecommendations(params?: {
  store_id?: string;
}): Promise<RecommendationsResponse> {
  const { data } = await apiClient.get<RecommendationsResponse>("/api/v1/ai/recommendations", { params });
  return data;
}

export async function fetchDetailedHealth(): Promise<HealthDetailedResponse> {
  const { data } = await apiClient.get<HealthDetailedResponse>("/api/v1/health/detailed");
  return data;
}
