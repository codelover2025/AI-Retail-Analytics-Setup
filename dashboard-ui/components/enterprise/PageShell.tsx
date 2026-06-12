"use client";

import { ErrorBanner } from "@/components/ErrorBanner";
import { LoadingState } from "@/components/LoadingState";
import { Button } from "@/components/ui/button";
import { RefreshCw } from "lucide-react";

interface PageShellProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
  loading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
  refreshing?: boolean;
  children: React.ReactNode;
}

export function PageShell({
  title,
  subtitle,
  actions,
  loading,
  error,
  onRefresh,
  refreshing,
  children,
}: PageShellProps) {
  return (
    <>
      <header className="sticky top-0 z-30 flex flex-wrap items-center justify-between gap-3 border-b border-border bg-background/95 px-4 py-3 backdrop-blur md:px-6 md:py-4">
        <div>
          <h1 className="text-lg font-semibold tracking-tight md:text-xl">{title}</h1>
          {subtitle && <p className="text-sm text-muted-foreground">{subtitle}</p>}
        </div>
        <div className="flex items-center gap-2">
          {actions}
          {onRefresh && (
            <Button variant="outline" size="sm" onClick={onRefresh} disabled={refreshing}>
              <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          )}
        </div>
      </header>
      <main className="flex-1 space-y-6 p-4 md:p-6">
        {error && onRefresh && <ErrorBanner message={error} onRetry={onRefresh} />}
        {error && !onRefresh && <ErrorBanner message={error} />}
        {loading ? <LoadingState /> : children}
      </main>
    </>
  );
}
