import React from "react";

type Accent = "green" | "blue" | "amber" | "red" | "slate" | "primary";

const bar: Record<Accent, string> = {
  green: "bg-status-green",
  blue: "bg-status-blue",
  amber: "bg-status-amber",
  red: "bg-status-red",
  slate: "bg-status-slate",
  primary: "bg-primary",
};

export function StatCard({
  label,
  value,
  accent = "slate",
  hint,
}: {
  label: string;
  value: string | number;
  accent?: Accent;
  hint?: string;
}) {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-border bg-card p-5 transition-shadow hover:shadow-sm">
      <span className={`absolute inset-x-0 top-0 h-1 ${bar[accent]}`} />
      <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">{label}</div>
      <div className="mt-3 font-display text-3xl text-ink">{value}</div>
      {hint && <div className="mt-1 text-xs text-muted-foreground">{hint}</div>}
    </div>
  );
}
