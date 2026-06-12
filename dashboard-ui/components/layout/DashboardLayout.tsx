import { ThemeProvider } from "@/components/providers/ThemeProvider";
import { EnterpriseSidebar } from "./EnterpriseSidebar";

export function DashboardLayout({ children }: { children: React.ReactNode }) {
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
