export function formatDateTime(iso: string): string {
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function formatTime(iso: string): string {
  try {
    return new Intl.DateTimeFormat(undefined, {
      timeStyle: "short",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function formatDay(day: string): string {
  try {
    return new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(
      new Date(day + "T12:00:00")
    );
  } catch {
    return day;
  }
}

export function formatNumber(n: number): string {
  return new Intl.NumberFormat().format(n);
}

export function recognitionLabel(type: string): string {
  const labels: Record<string, string> = {
    vip: "VIP",
    new_visitor: "New visitor",
    repeat_visitor: "Repeat visitor",
    visitor: "Visitor",
  };
  return labels[type] ?? type;
}
