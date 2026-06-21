"use client";

import { useState, useEffect } from "react";
import { PageShell } from "@/components/enterprise/PageShell";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Sparkles,
  Users,
  Layout,
  TrendingUp,
  Award,
  CheckCircle,
  Clock,
  ArrowRight,
  Filter,
  Play,
  Check,
} from "lucide-react";
import { fetchRecommendations, RecommendationItem } from "@/services/ai-api";

const CATEGORY_MAP = {
  all: { label: "All Categories", icon: Filter },
  marketing: { label: "Marketing Campaigns", icon: Sparkles, color: "text-amber-500 bg-amber-50 dark:bg-amber-950/30" },
  staffing: { label: "Staff Scheduling", icon: Users, color: "text-blue-500 bg-blue-50 dark:bg-blue-950/30" },
  layout: { label: "Store Layout", icon: Layout, color: "text-indigo-500 bg-indigo-50 dark:bg-indigo-950/30" },
  placement: { label: "Product Placement", icon: Award, color: "text-purple-500 bg-purple-50 dark:bg-purple-950/30" },
  business: { label: "Business Operations", icon: TrendingUp, color: "text-emerald-500 bg-emerald-50 dark:bg-emerald-950/30" },
};

export default function RecommendationsPage() {
  const [storeId, setStoreId] = useState("store-001");
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [filteredRecs, setFilteredRecs] = useState<RecommendationItem[]>([]);
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Track applied status locally for button state changes
  const [appliedRecs, setAppliedRecs] = useState<Record<string, boolean>>({});

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRecommendations({ store_id: storeId });
      setRecommendations(data.recommendations);
      setFilteredRecs(data.recommendations);
    } catch (err: any) {
      console.error(err);
      setError("Failed to fetch AI recommendations.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [storeId]);

  // Filter logic
  useEffect(() => {
    if (activeCategory === "all") {
      setFilteredRecs(recommendations);
    } else {
      setFilteredRecs(recommendations.filter((r) => r.category === activeCategory));
    }
  }, [activeCategory, recommendations]);

  const handleApply = (id: string) => {
    setAppliedRecs((prev) => ({ ...prev, [id]: true }));
    // In a real app, this would dispatch a call to apply / configure the rule
    setTimeout(() => {
      alert("AI recommendation implementation request triggered and queued successfully.");
    }, 100);
  };

  const getImpactBadge = (impact: string) => {
    switch (impact.toLowerCase()) {
      case "high":
        return <Badge className="bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-200">High Impact</Badge>;
      case "medium":
        return <Badge className="bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-200">Medium Impact</Badge>;
      default:
        return <Badge className="bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-200">Low Impact</Badge>;
    }
  };

  return (
    <PageShell
      title="AI Recommendation Center"
      subtitle="Data-driven optimizations, staff allocation tweaks, and product placement insights"
      onRefresh={loadData}
      refreshing={loading}
    >
      <div className="space-y-6">
        
        {/* Store Selector & Filters */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-4">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-muted-foreground uppercase">Store:</span>
            <select
              className="px-3 py-1.5 rounded-lg border border-input text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-primary/20"
              value={storeId}
              onChange={(e) => setStoreId(e.target.value)}
            >
              <option value="store-001">Store-001 (Mumbai)</option>
              <option value="store-002">Store-002 (Delhi)</option>
              <option value="store-003">Store-003 (Bangalore)</option>
            </select>
          </div>

          <div className="flex flex-wrap gap-1">
            {Object.entries(CATEGORY_MAP).map(([key, value]) => (
              <Button
                key={key}
                size="sm"
                variant={activeCategory === key ? "default" : "outline"}
                className="h-8 text-xs flex items-center gap-1.5"
                onClick={() => setActiveCategory(key)}
              >
                <value.icon className="h-3.5 w-3.5" />
                <span>{value.label}</span>
              </Button>
            ))}
          </div>
        </div>

        {error && (
          <Card className="border-rose-200 bg-rose-50 text-rose-800">
            <CardContent className="pt-6">
              <p className="text-sm font-semibold">{error}</p>
            </CardContent>
          </Card>
        )}

        {/* Recommendations list */}
        {filteredRecs.length === 0 && !loading && (
          <div className="text-center py-12 border border-dashed border-border rounded-xl">
            <p className="text-sm text-muted-foreground">No active recommendations in this category.</p>
          </div>
        )}

        <div className="grid gap-6 md:grid-cols-2">
          {filteredRecs.map((rec) => {
            const catInfo = CATEGORY_MAP[rec.category] || CATEGORY_MAP.business;
            const Icon = catInfo.icon;
            const isApplied = appliedRecs[rec.id];

            return (
              <Card key={rec.id} className="flex flex-col h-full border border-border shadow-sm hover:shadow-md transition-shadow relative overflow-hidden">
                {/* Visual Accent bar depending on category */}
                <div className={`h-1.5 w-full bg-gradient-to-r ${rec.category === "marketing" ? "from-amber-400 to-orange-500" : rec.category === "staffing" ? "from-blue-400 to-indigo-500" : "from-emerald-400 to-teal-500"}`} />
                
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <div className={`p-2 rounded-lg ${catInfo.color}`}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="flex items-center gap-1.5">
                      {getImpactBadge(rec.impact_level)}
                      <Badge variant="outline" className="text-[10px] font-semibold border-indigo-200 bg-indigo-50/50 text-indigo-700">
                        {Math.round(rec.confidence_score * 100)}% Confidence
                      </Badge>
                    </div>
                  </div>
                  <CardTitle className="text-base font-bold text-foreground">
                    {rec.title}
                  </CardTitle>
                  <CardDescription className="text-xs mt-1 leading-relaxed">
                    {rec.description}
                  </CardDescription>
                </CardHeader>

                <CardContent className="flex-1 space-y-4 pb-6">
                  {/* Action Steps */}
                  <div className="space-y-2">
                    <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5" /> Action Plan
                    </h4>
                    <div className="space-y-1.5">
                      {rec.actionable_steps.map((step, idx) => (
                        <div key={idx} className="flex gap-2 text-xs">
                          <CheckCircle className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                          <span className="text-muted-foreground">{step}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Implementation Button */}
                  <div className="pt-4 border-t border-border flex items-center justify-between mt-auto">
                    <div className="w-2/3">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] text-muted-foreground">Confidence level:</span>
                        <span className="text-[10px] font-bold text-primary">{Math.round(rec.confidence_score * 100)}%</span>
                      </div>
                      <div className="w-full bg-muted rounded-full h-1.5 overflow-hidden">
                        <div
                          className="bg-primary h-1.5 rounded-full transition-all duration-500"
                          style={{ width: `${rec.confidence_score * 100}%` }}
                        />
                      </div>
                    </div>
                    
                    <Button
                      size="sm"
                      variant={isApplied ? "outline" : "default"}
                      onClick={() => handleApply(rec.id)}
                      disabled={isApplied}
                      className="h-8 text-xs shrink-0 flex items-center gap-1"
                    >
                      {isApplied ? (
                        <>
                          <Check className="h-3.5 w-3.5 text-emerald-500" />
                          <span>Applied</span>
                        </>
                      ) : (
                        <>
                          <Play className="h-3 w-3 fill-current" />
                          <span>Deploy</span>
                        </>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

      </div>
    </PageShell>
  );
}
