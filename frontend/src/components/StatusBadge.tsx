import React, { ReactNode } from "react";

type Variant =
  | "available" | "on_trip" | "on-trip" | "in_shop" | "in-shop" | "retired" | "suspended"
  | "off_duty" | "off-duty" | "draft" | "completed" | "dispatched" | "cancelled" | "pending"
  | "active" | "closed";

const styles: Record<string, string> = {
  available:  "bg-status-green/12 text-status-green ring-status-green/25",
  completed:  "bg-status-green/12 text-status-green ring-status-green/25",
  active:     "bg-status-green/12 text-status-green ring-status-green/25",
  "on-trip":  "bg-status-blue/12 text-status-blue ring-status-blue/25",
  on_trip:    "bg-status-blue/12 text-status-blue ring-status-blue/25",
  dispatched: "bg-status-blue/12 text-status-blue ring-status-blue/25",
  pending:    "bg-status-amber/15 text-status-amber ring-status-amber/30",
  "in-shop":  "bg-status-amber/15 text-status-amber ring-status-amber/30",
  in_shop:    "bg-status-amber/15 text-status-amber ring-status-amber/30",
  retired:    "bg-status-red/12 text-status-red ring-status-red/25",
  suspended:  "bg-status-red/12 text-status-red ring-status-red/25",
  cancelled:  "bg-status-red/12 text-status-red ring-status-red/25",
  closed:     "bg-status-slate/12 text-status-slate ring-status-slate/25",
  "off-duty": "bg-status-slate/12 text-status-slate ring-status-slate/25",
  off_duty:   "bg-status-slate/12 text-status-slate ring-status-slate/25",
  draft:      "bg-status-slate/12 text-status-slate ring-status-slate/25",
};

const labels: Record<string, string> = {
  available: "Available", "on-trip": "On Trip", on_trip: "On Trip", "in-shop": "In Shop", in_shop: "In Shop",
  retired: "Retired", suspended: "Suspended", "off-duty": "Off Duty", off_duty: "Off Duty",
  draft: "Draft", completed: "Completed", dispatched: "Dispatched",
  cancelled: "Cancelled", pending: "Pending", active: "Active", closed: "Closed",
};

export function StatusBadge({ variant, children }: { variant: Variant; children?: ReactNode }) {
  const normVariant = (variant || "").toLowerCase();
  const styleClass = styles[normVariant] || "bg-status-slate/12 text-status-slate ring-status-slate/25";
  const labelText = labels[normVariant] || variant;

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${styleClass}`}>
      {children ?? labelText}
    </span>
  );
}
