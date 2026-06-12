"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { ThemeProvider } from "@/components/providers/ThemeProvider";
import { EnterpriseSidebar } from "./EnterpriseSidebar";
import { useAuth } from "@/components/providers/AuthProvider";

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const isLoginPage = pathname === "/login";

  useEffect(() => {
    if (!isLoginPage && !isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isLoading, isAuthenticated, router, isLoginPage]);

  // While auth is being resolved from localStorage, show a neutral loading screen (except on login page)
  if (isLoading && !isLoginPage) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p className="text-sm text-muted-foreground">Loading…</p>
        </div>
      </div>
    );
  }

  // If not authenticated and not on login page, render nothing (redirect is in flight)
  if (!isAuthenticated && !isLoginPage) return null;

  if (isLoginPage) {
    return (
      <ThemeProvider>
        {children}
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider>
      <div className="flex min-h-screen bg-background">
        <EnterpriseSidebar />
        <div className="flex min-h-screen min-w-0 flex-1 flex-col pb-16 pt-14 md:pb-0 md:pt-0">
          {children}
        </div>
      </div>
    </ThemeProvider>
  );
}
