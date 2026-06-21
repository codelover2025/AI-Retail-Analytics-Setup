"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import {
  Activity,
  BarChart3,
  Bell,
  Building2,
  Cctv,
  ClipboardList,
  FileText,
  Flame,
  GitFork,
  LayoutDashboard,
  Link2,
  LogOut,
  Radio,
  Repeat,
  Settings2,
  Shield,
  Store,
  UserCircle,
  Users,
  BadgeCheck,
  Bot,
  Sparkles,
  Cpu,
  BookOpen,
  MessageSquare,
  LineChart,
} from "lucide-react";
import { OrzenLogo } from "@/components/OrzenLogo";
import { ThemeToggle } from "@/components/enterprise/ThemeToggle";
import { useAuth } from "@/components/providers/AuthProvider";

type NavItem = { href: string; label: string; icon: React.ComponentType<{ className?: string }> };
type NavSection = { title: string; items: NavItem[] };

const sections: NavSection[] = [
  {
    title: "Overview",
    items: [
      { href: "/stores", label: "Multi-store", icon: Store },
      { href: "/executive", label: "Executive", icon: BarChart3 },
      { href: "/", label: "Store live", icon: LayoutDashboard },
      { href: "/assistant", label: "AI Assistant", icon: Bot },
    ],
  },
  {
    title: "Operations",
    items: [
      { href: "/realtime", label: "Realtime", icon: Radio },
      { href: "/multi-camera", label: "Multi-camera", icon: Cctv },
      { href: "/heatmap", label: "Heatmap", icon: Flame },
      { href: "/journey", label: "Journey mapping", icon: GitFork },
      { href: "/predictive", label: "Predictive AI", icon: LineChart },
      { href: "/recommendations", label: "AI Recommendations", icon: Sparkles },
    ],
  },
  {
    title: "People",
    items: [
      { href: "/staff", label: "Staff analytics", icon: Activity },
      { href: "/employees", label: "Employees", icon: BadgeCheck },
      { href: "/customers", label: "Customers", icon: UserCircle },
      { href: "/recognitions", label: "Logs", icon: ClipboardList },
      { href: "/repeat-visitors", label: "Repeat / New", icon: Repeat },
      { href: "/visitors", label: "Store visitors", icon: Users },
      { href: "/alerts", label: "Alerts", icon: Bell },
    ],
  },
  {
    title: "Platform",
    items: [
      { href: "/reports", label: "Reports", icon: FileText },
      { href: "/integrations", label: "Integrations", icon: Link2 },
      { href: "/admin", label: "Admin", icon: Building2 },
      { href: "/admin/roles", label: "Roles & RBAC", icon: Shield },
      { href: "/settings", label: "Settings", icon: Settings2 },
      { href: "/performance", label: "System health", icon: Cpu },
      { href: "/docs", label: "Documentation", icon: BookOpen },
    ],
  },
  {
    title: "Legacy",
    items: [{ href: "/analytics", label: "Analytics", icon: BarChart3 }],
  },
];

function NavLink({ href, label, icon: Icon }: NavItem) {
  const pathname = usePathname() ?? "/";
  const active =
    href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);

  return (
    <Link
      href={href}
      className={clsx(
        "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
        active
          ? "bg-primary/10 text-primary"
          : "text-muted-foreground hover:bg-accent hover:text-foreground"
      )}
    >
      <Icon className="h-4 w-4 shrink-0" aria-hidden />
      <span className="truncate">{label}</span>
    </Link>
  );
}

function MobileNav() {
  const pathname = usePathname() ?? "/";
  const items = sections[0].items
    .concat(sections[1].items[0], sections[3].items[0]);

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-40 flex overflow-x-auto border-t border-border bg-card md:hidden"
      aria-label="Mobile"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
    >
      {items.map((item) => {
        const active =
          item.href === "/"
            ? pathname === "/"
            : pathname === item.href || pathname.startsWith(`${item.href}/`);
        const Icon = item.icon;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={clsx(
              "flex min-w-[4.5rem] flex-1 flex-col items-center gap-0.5 py-2 text-[10px]",
              active ? "text-primary" : "text-muted-foreground"
            )}
          >
            <Icon className="h-5 w-5" />
            {item.label.split(" ")[0]}
          </Link>
        );
      })}
    </nav>
  );
}

export function EnterpriseSidebar() {
  const { user, logout } = useAuth();

  return (
    <>
      <aside className="hidden w-64 shrink-0 flex-col border-r border-border bg-card md:flex">
        <div className="flex min-h-[4.5rem] items-center justify-between border-b border-border px-4 py-3">
          <OrzenLogo variant="primary" priority />
          <ThemeToggle />
        </div>
        <nav className="flex flex-1 flex-col gap-4 overflow-y-auto p-3" aria-label="Main">
          {sections.map((section) => (
            <div key={section.title}>
              <p className="mb-1 px-3 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                {section.title}
              </p>
              <div className="flex flex-col gap-0.5">
                {section.items.map((item) => (
                  <NavLink key={item.href} {...item} />
                ))}
              </div>
            </div>
          ))}
        </nav>
        {/* User + logout */}
        <div className="border-t border-border px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="min-w-0">
              <p className="truncate text-xs font-medium text-foreground">
                {user?.email ?? "—"}
              </p>
              <p className="text-[10px] capitalize text-muted-foreground">
                {user?.role?.replace("_", " ") ?? ""}
              </p>
            </div>
            <button
              onClick={logout}
              aria-label="Sign out"
              className="ml-2 rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive focus:outline-none focus:ring-2 focus:ring-destructive/40"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      <header className="fixed left-0 right-0 top-0 z-40 flex h-14 items-center justify-between border-b border-border bg-card px-4 md:hidden">
        <OrzenLogo variant="primary" className="max-h-8" priority />
        <ThemeToggle />
      </header>

      <MobileNav />
    </>
  );
}
