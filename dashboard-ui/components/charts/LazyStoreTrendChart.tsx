"use client";

import dynamic from "next/dynamic";
import { Skeleton } from "@/components/ui/skeleton";

const StoreTrendChart = dynamic(
  () => import("./StoreTrendChart").then((m) => m.StoreTrendChart),
  {
    ssr: false,
    loading: () => <Skeleton className="h-[260px] w-full" />,
  }
);

export { StoreTrendChart };
