"use client";

import type { HeatmapCell } from "@/services/heatmap-api";
import { cn } from "@/lib/utils";

export function HeatmapGrid({ cells, maxIntensity }: { cells: HeatmapCell[]; maxIntensity: number }) {
  const max = maxIntensity || 1;

  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
      {cells.map((cell, i) => {
        const label = cell.zone_name ?? cell.label ?? `Hour ${cell.hour ?? i}`;
        const intensity = cell.intensity / max;
        return (
          <div
            key={`${label}-${i}`}
            className={cn(
              "rounded-lg border border-border p-3 transition-transform hover:scale-[1.02]",
              "bg-primary/[var(--opacity)]"
            )}
            style={
              {
                "--opacity": Math.max(0.08, intensity * 0.85),
              } as React.CSSProperties
            }
            title={`${label}: ${(intensity * 100).toFixed(0)}% intensity`}
          >
            <p className="truncate text-sm font-medium">{label}</p>
            <p className="text-xs text-muted-foreground">
              {cell.value != null ? cell.value.toFixed(1) : `${(intensity * 100).toFixed(0)}%`}
            </p>
          </div>
        );
      })}
    </div>
  );
}
