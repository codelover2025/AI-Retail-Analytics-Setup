"use client";

import { useState } from "react";
import { PageShell } from "@/components/enterprise/PageShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  FileText,
  Layers,
  Cpu,
  Server,
  Terminal,
  Activity,
  CheckCircle,
  Database,
  Link,
  ChevronRight,
  Code,
} from "lucide-react";

interface ApiEndpoint {
  method: "GET" | "POST" | "PATCH" | "DELETE";
  path: string;
  description: string;
  requestBody?: string;
  responseBody: string;
}

const API_ENDPOINTS: ApiEndpoint[] = [
  {
    method: "POST",
    path: "/api/v1/ai/assistant/chat",
    description: "Submit query to the RAG-based AI assistant for conversational retail metrics.",
    requestBody: `{
  "query": "Compare store-001 vs store-002 footfall",
  "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}`,
    responseBody: `{
  "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "answer": "Mumbai store (store-001) had 120 visitors, which is 20% higher than store-002...",
  "summary": "Mumbai footfall leads Delhi by 20%.",
  "kpis": [{"kpi": "Visitors Ratio", "value": "1.2"}],
  "sources": [{"type": "database_aggregation", "detail": "..."}]
}`,
  },
  {
    method: "POST",
    path: "/api/v1/ai/voice/stt",
    description: "Transcribe WAV/MP3 speech recordings to text query commands.",
    requestBody: "Multipart/Form-Data containing 'file' (audio bin) and query param 'language' (en | hi).",
    responseBody: `{
  "transcription": "Show me daily visitor trends",
  "language": "en",
  "filename": "recording.wav"
}`,
  },
  {
    method: "POST",
    path: "/api/v1/ai/voice/tts",
    description: "Convert text output strings to audio speech stream files (MP3 format).",
    requestBody: `{
  "text": "Daily visitor count is increasing",
  "language": "en"
}`,
    responseBody: "Binary MP3 audio stream (Response Content-Type: audio/mpeg)",
  },
  {
    method: "GET",
    path: "/api/v1/ai/predictions",
    description: "Retrieve predictive daily footfall, staffing volumes, and peak operating hours.",
    responseBody: `{
  "store_id": "store-001",
  "days_ahead": 7,
  "predictions": {
    "footfall": [{"date": "2026-06-22", "predicted_visitors": 45, "confidence_score": 0.85}],
    "peak_hours": [{"hour": 18, "label": "06:00 PM", "weight": 0.18}],
    "staff_requirements": [{"date": "2026-06-22", "recommended_staff_count": 4}]
  }
}`,
  },
  {
    method: "GET",
    path: "/api/v1/ai/forecasts",
    description: "Compute statistical forecasts for revenue, retention, and growth with 95% confidence intervals.",
    responseBody: `{
  "store_id": "store-001",
  "horizon": "daily",
  "forecasts": {
    "revenue": [{"date": "2026-06-22", "forecast": 612.0, "lower_ci": 510.0, "upper_ci": 714.0}]
  }
}`,
  },
  {
    method: "GET",
    path: "/api/v1/ai/recommendations",
    description: "Get prioritized business recommendations with impact scores and actionable plans.",
    responseBody: `{
  "store_id": "store-001",
  "recommendations": [
    {
      "id": "uuid",
      "category": "staffing",
      "title": "Increase Floor Coverage during Peak Hours",
      "impact_level": "High",
      "confidence_score": 0.88,
      "actionable_steps": ["Deploy greeter", "Schedule additional cashiers"]
    }
  ]
}`,
  },
];

export default function DocumentationPage() {
  const [selectedEndpoint, setSelectedEndpoint] = useState<ApiEndpoint | null>(API_ENDPOINTS[0]);

  const getMethodBadge = (method: string) => {
    switch (method) {
      case "GET":
        return <Badge className="bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">GET</Badge>;
      case "POST":
        return <Badge className="bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300">POST</Badge>;
      case "PATCH":
        return <Badge className="bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300">PATCH</Badge>;
      default:
        return <Badge className="bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300">DELETE</Badge>;
    }
  };

  return (
    <PageShell
      title="Platform Documentation & API Registry"
      subtitle="Deployment manifests, running AI deep learning models, and developer reference specifications"
    >
      <div className="space-y-6">
        
        {/* Core Release Metadata & Deployment */}
        <section className="grid gap-6 md:grid-cols-3">
          
          {/* Deployment Status */}
          <Card className="border border-border shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-bold flex items-center gap-1.5">
                <Server className="h-4.5 w-4.5 text-indigo-500" />
                Deployment Kubernetes Status
              </CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-muted-foreground space-y-2">
              <div className="flex justify-between items-center border-b border-border pb-1.5">
                <span>Cluster Node:</span>
                <span className="font-bold text-foreground">gke-orzen-prod-01</span>
              </div>
              <div className="flex justify-between items-center border-b border-border pb-1.5">
                <span>Containers:</span>
                <span className="font-bold text-foreground">12 Pods Running</span>
              </div>
              <div className="flex justify-between items-center border-b border-border pb-1.5">
                <span>Docker registry:</span>
                <Badge className="bg-indigo-50 text-indigo-700">docker.io/orzen/core:v5</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span>SSL Certificate:</span>
                <Badge className="bg-green-150 text-green-700 font-semibold">Active ({"Let's Encrypt"})</Badge>
              </div>
            </CardContent>
          </Card>

          {/* Software Versions */}
          <Card className="border border-border shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-bold flex items-center gap-1.5">
                <Layers className="h-4.5 w-4.5 text-emerald-500" />
                Software Architecture
              </CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-muted-foreground space-y-2">
              <div className="flex justify-between items-center border-b border-border pb-1.5">
                <span>Platform Core:</span>
                <span className="font-bold text-foreground">v5.0.0 (Phase 5 Release)</span>
              </div>
              <div className="flex justify-between items-center border-b border-border pb-1.5">
                <span>UI Client Engine:</span>
                <span className="font-bold text-foreground">Next.js 15.1.3 + TS</span>
              </div>
              <div className="flex justify-between items-center border-b border-border pb-1.5">
                <span>Backend Framework:</span>
                <span className="font-bold text-foreground">FastAPI v0.110.0</span>
              </div>
              <div className="flex justify-between items-center">
                <span>Relational Schema:</span>
                <span className="font-bold text-foreground">Alembic Migration 05_phase5</span>
              </div>
            </CardContent>
          </Card>

          {/* Machine Learning Models */}
          <Card className="border border-border shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-bold flex items-center gap-1.5">
                <Cpu className="h-4.5 w-4.5 text-purple-500" />
                Deep Learning Model Registry
              </CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-muted-foreground space-y-2">
              <div className="flex justify-between items-center border-b border-border pb-1.5">
                <span>YOLOv8x (Footfall):</span>
                <Badge variant="outline" className="text-[10px] font-semibold text-purple-700 bg-purple-50">v1.2.4-active</Badge>
              </div>
              <div className="flex justify-between items-center border-b border-border pb-1.5">
                <span>ResNet-50 (Repeat Vis):</span>
                <Badge variant="outline" className="text-[10px] font-semibold text-indigo-700 bg-indigo-50">v3.1.0-active</Badge>
              </div>
              <div className="flex justify-between items-center border-b border-border pb-1.5">
                <span>DeepFace (Engagement):</span>
                <Badge variant="outline" className="text-[10px] font-semibold text-rose-700 bg-rose-50">v2.0.2-fallback</Badge>
              </div>
              <div className="flex justify-between items-center">
                <span>BERT (Intent Parsing):</span>
                <Badge variant="outline" className="text-[10px] font-semibold text-amber-700 bg-amber-50">v1.5.0-active</Badge>
              </div>
            </CardContent>
          </Card>

        </section>

        {/* API documentation Split Explorer */}
        <section className="grid gap-6 md:grid-cols-3">
          
          {/* List panel */}
          <div className="md:col-span-1 space-y-2">
            <h3 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <Code className="h-4.5 w-4.5" /> API Endpoint Catalog
            </h3>
            <div className="space-y-1.5">
              {API_ENDPOINTS.map((endpoint, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedEndpoint(endpoint)}
                  className={`w-full text-left p-3 rounded-lg border transition-all flex items-start gap-2.5 ${
                    selectedEndpoint?.path === endpoint.path
                      ? "bg-primary/10 text-primary border-primary"
                      : "bg-card text-foreground border-border hover:bg-muted/50"
                  }`}
                >
                  <div className="mt-0.5">{getMethodBadge(endpoint.method)}</div>
                  <div className="min-w-0">
                    <p className="font-mono text-xs truncate font-bold">{endpoint.path}</p>
                    <p className="text-[11px] text-muted-foreground truncate mt-0.5">{endpoint.description}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Details Spec panel */}
          <div className="md:col-span-2">
            {selectedEndpoint ? (
              <Card className="border border-border shadow-sm h-full flex flex-col justify-between">
                <CardHeader className="pb-3 border-b border-border">
                  <div className="flex items-center gap-2 mb-1.5">
                    {getMethodBadge(selectedEndpoint.method)}
                    <span className="font-mono text-xs font-bold text-foreground bg-muted px-2 py-0.5 rounded">
                      {selectedEndpoint.path}
                    </span>
                  </div>
                  <CardTitle className="text-base">{selectedEndpoint.description}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4 pt-4 flex-1">
                  
                  {/* Request Body */}
                  {selectedEndpoint.requestBody && (
                    <div className="space-y-1.5">
                      <h4 className="text-xs font-bold text-muted-foreground flex items-center gap-1">
                        <Terminal className="h-3.5 w-3.5" /> Expected Request Payload
                      </h4>
                      <pre className="p-3 bg-slate-950 text-slate-100 rounded-lg text-[11px] font-mono overflow-x-auto leading-relaxed border border-slate-800">
                        {selectedEndpoint.requestBody}
                      </pre>
                    </div>
                  )}

                  {/* Response Body */}
                  <div className="space-y-1.5">
                    <h4 className="text-xs font-bold text-muted-foreground flex items-center gap-1">
                      <Database className="h-3.5 w-3.5" /> Expected Response Output
                    </h4>
                    <pre className="p-3 bg-slate-950 text-slate-100 rounded-lg text-[11px] font-mono overflow-x-auto leading-relaxed border border-slate-800">
                      {selectedEndpoint.responseBody}
                    </pre>
                  </div>

                </CardContent>
              </Card>
            ) : (
              <div className="h-full flex items-center justify-center border border-dashed border-border rounded-xl">
                <p className="text-sm text-muted-foreground">Select an endpoint from the catalog to inspect detailed specifications.</p>
              </div>
            )}
          </div>

        </section>

      </div>
    </PageShell>
  );
}
