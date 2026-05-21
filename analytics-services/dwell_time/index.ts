export interface RecognitionItem {
  id: string;
  type: string;
  time: string;
}

export interface DwellBucket {
  label: string;
  count: number;
}

/**
 * Proxy dwell distribution from recognition inter-arrival gaps (Phase 1).
 * Full dwell requires zone analytics (Phase 2).
 */
export function estimateDwellDistribution(
  recognitions: RecognitionItem[]
): DwellBucket[] {
  if (recognitions.length < 2) {
    return [
      { label: "< 5 min", count: recognitions.length },
      { label: "5–15 min", count: 0 },
      { label: "15–30 min", count: 0 },
      { label: "30+ min", count: 0 },
    ];
  }

  const sorted = [...recognitions].sort(
    (a, b) => new Date(a.time).getTime() - new Date(b.time).getTime()
  );

  const buckets = { short: 0, medium: 0, long: 0, extended: 0 };
  for (let i = 1; i < sorted.length; i++) {
    const gapMin =
      (new Date(sorted[i].time).getTime() -
        new Date(sorted[i - 1].time).getTime()) /
      60000;
    if (gapMin < 5) buckets.short++;
    else if (gapMin < 15) buckets.medium++;
    else if (gapMin < 30) buckets.long++;
    else buckets.extended++;
  }

  return [
    { label: "< 5 min", count: buckets.short },
    { label: "5–15 min", count: buckets.medium },
    { label: "15–30 min", count: buckets.long },
    { label: "30+ min", count: buckets.extended },
  ];
}
