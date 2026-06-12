"use client";

import dynamic from "next/dynamic";
import { Skeleton } from "@/components/ui/skeleton";

export const LazyHeatmapGrid = dynamic(
  () => import("./HeatmapGrid").then((m) => m.HeatmapGrid),
  { ssr: false, loading: () => <Skeleton className="h-[320px] w-full" /> }
);
