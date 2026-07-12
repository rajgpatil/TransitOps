import React from "react";

export function BarChart({ data, height = 180 }: { data: { label: string; value: number }[]; height?: number }) {
  const max = Math.max(...data.map(d => d.value), 1);
  return (
    <div className="flex items-end gap-3" style={{ height }}>
      {data.map(d => (
        <div key={d.label} className="flex flex-1 flex-col items-center gap-2">
          <div
            className="w-full rounded-t-md bg-orange-700 transition-all hover:bg-[oklch(0.58_0.14_40)] animate-fade-in"
            style={{ height: `${(d.value / max) * (height - 24)}px` }}
            title={`${d.label}: ${d.value.toLocaleString()}`}
          />
          <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">{d.label}</span>
        </div>
      ))}
    </div>
  );
}

export function HorizontalBar({
  label,
  value,
  max,
  color = "blue",
}: {
  label: string;
  value: number;
  max: number;
  color?: "blue" | "green" | "amber" | "red" | "slate";
}) {
  const colors: Record<string, string> = {
    blue: "bg-status-blue",
    green: "bg-status-green",
    amber: "bg-status-amber",
    red: "bg-status-red",
    slate: "bg-status-slate",
  };
  const pct = Math.min(100, (value / Math.max(max, 1)) * 100);
  return (
    <div className="grid grid-cols-[80px_1fr_auto] items-center gap-3 py-1.5">
      <span className="truncate text-xs font-medium text-foreground">{label}</span>
      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <div className={`h-full rounded-full ${colors[color]}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-10 text-right text-[11px] tabular-nums text-muted-foreground">{value}</span>
    </div>
  );
}
