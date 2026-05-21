import { Sidebar } from "./Sidebar";

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <div className="flex min-h-screen flex-1 flex-col pb-16 pt-14 md:pb-0 md:pt-0">
        {children}
      </div>
    </div>
  );
}
