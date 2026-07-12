import React from "react";

const steps = [
  { key: "draft", label: "Draft", color: "bg-status-green" },
  { key: "dispatched", label: "Dispatched", color: "bg-status-blue" },
  { key: "completed", label: "Completed", color: "bg-status-slate/60" },
  { key: "cancelled", label: "Cancelled", color: "bg-status-slate/60" },
] as const;

export function LifecycleStepper({ current = "dispatched" }: { current?: typeof steps[number]["key"] }) {
  const idx = steps.findIndex(s => s.key === current);
  return (
    <div className="flex items-center">
      {steps.map((s, i) => (
        <div key={s.key} className="flex flex-1 items-center last:flex-none">
          <div className="flex flex-col items-center">
            <div className={`h-3 w-3 rounded-full ring-4 ring-background ${i <= idx ? s.color : "bg-muted-foreground/25"}`} />
            <span className={`mt-2 text-[11px] font-medium ${i === idx ? "text-foreground" : "text-muted-foreground"}`}>{s.label}</span>
          </div>
          {i < steps.length - 1 && (
            <div className={`mx-2 h-px flex-1 ${i < idx ? "bg-foreground/40" : "bg-border"}`} />
          )}
        </div>
      ))}
    </div>
  );
}
