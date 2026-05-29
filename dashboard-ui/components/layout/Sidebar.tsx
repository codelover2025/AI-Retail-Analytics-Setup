"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  Bell,
  Cctv,
  ClipboardList,
  LayoutDashboard,
  Repeat,
  UserCircle,
  Users,
  BadgeCheck,
} from "lucide-react";
import clsx from "clsx";
import { OrzenLogo } from "@/components/OrzenLogo";

const nav = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/customers", label: "Customers", icon: UserCircle },
  { href: "/recognitions", label: "Logs", icon: ClipboardList },
  { href: "/repeat-visitors", label: "Repeat / New", icon: Repeat },
  { href: "/employees", label: "Employees", icon: BadgeCheck },
  { href: "/visitors", label: "Store visitors", icon: Users },
  { href: "/alerts", label: "Alerts", icon: Bell },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/multi-camera", label: "Multi-camera", icon: Cctv },
];

export function Sidebar() {
  const pathname = usePathname() ?? "/";

  return (
    <>
      <aside className="hidden w-60 shrink-0 flex-col border-r border-slate-200 bg-white md:flex">
        <div className="flex min-h-[4.5rem] items-center border-b border-slate-200 px-4 py-3">
          <OrzenLogo variant="primary" priority />
        </div>
        <nav className="flex flex-1 flex-col gap-1 p-3" aria-label="Main">
          {nav.map(({ href, label, icon: Icon }) => {
            const active =
              href === "/" ? pathname === "/" : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={clsx(
                  "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  active
                    ? "bg-brand-50 text-brand-700"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                )}
              >
                <Icon className="h-4 w-4 shrink-0" aria-hidden />
                {label}
              </Link>
            );
          })}
        </nav>
        <p className="border-t border-slate-100 px-4 py-3 text-xs text-slate-400">
          Orzen Vision · Store analytics
        </p>
      </aside>

      <header className="fixed left-0 right-0 top-0 z-40 flex h-14 items-center justify-center border-b border-slate-200 bg-white px-4 md:hidden">
        <OrzenLogo variant="primary" className="max-h-8" priority />
      </header>

      <nav
        className="fixed bottom-0 left-0 right-0 z-40 flex border-t border-slate-200 bg-white md:hidden"
        aria-label="Mobile"
        style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      >
        {nav.map(({ href, label, icon: Icon }) => {
          const active =
            href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                "flex flex-1 flex-col items-center gap-0.5 py-2 text-xs",
                active ? "text-brand-600" : "text-slate-500"
              )}
            >
              <Icon className="h-5 w-5" />
              {label}
            </Link>
          );
        })}
      </nav>
    </>
  );
}
