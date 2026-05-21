import type { AlertItem } from "@/services/types";
import { formatDateTime } from "@/utils/format";
import { AlertTriangle, Bell } from "lucide-react";
import clsx from "clsx";

interface AlertNotificationProps {
  alerts: AlertItem[];
  max?: number;
}

function alertStyle(type: string) {
  if (type.includes("vip")) return "border-amber-200 bg-amber-50";
  if (type.includes("watchlist")) return "border-rose-200 bg-rose-50";
  return "border-slate-200 bg-slate-50";
}

export function AlertNotification({ alerts, max = 5 }: AlertNotificationProps) {
  const visible = alerts.slice(0, max);

  if (visible.length === 0) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-dashed border-slate-200 px-4 py-6 text-sm text-slate-500">
        <Bell className="h-4 w-4 shrink-0" />
        No alerts in the last fetch
      </div>
    );
  }

  return (
    <ul className="space-y-2" role="list">
      {visible.map((alert, i) => (
        <li
          key={`${alert.type}-${alert.time}-${i}`}
          className={clsx(
            "flex gap-3 rounded-lg border px-3 py-2.5 text-sm",
            alertStyle(alert.type)
          )}
        >
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
          <div className="min-w-0 flex-1">
            <p className="font-medium text-slate-800">{alert.type}</p>
            <p className="truncate text-slate-600">{alert.message}</p>
            <p className="mt-0.5 text-xs text-slate-500">
              {formatDateTime(alert.time)}
            </p>
          </div>
        </li>
      ))}
    </ul>
  );
}
