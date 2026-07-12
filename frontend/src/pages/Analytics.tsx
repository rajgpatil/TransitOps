import React from "react";
import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "../components/AppShell";
import { StatCard } from "../components/StatCard";
import { BarChart, HorizontalBar } from "../components/charts";
import { Card } from "../components/SectionHeader";
import { apiClient } from "../api/client";

export default function Analytics() {
  // Query KPIs
  const { data: kpis, isLoading: isKpisLoading } = useQuery({
    queryKey: ["dashboard-kpis"],
    queryFn: async () => {
      const res = await apiClient.get("/api/dashboard/kpis");
      return res.data;
    },
  });

  // Query Charts
  const { data: charts, isLoading: isChartsLoading } = useQuery({
    queryKey: ["dashboard-charts"],
    queryFn: async () => {
      const res = await apiClient.get("/api/dashboard/charts");
      return res.data;
    },
  });

  const revenueData = charts?.revenue || [
    { label: "Jan", value: 42 },
    { label: "Feb", value: 55 },
    { label: "Mar", value: 38 },
    { label: "Apr", value: 71 },
    { label: "May", value: 62 },
    { label: "Jun", value: 84 },
    { label: "Jul", value: 76 },
  ];

  // Map values to thousands for charting clean display if they are full numbers
  const formattedRevenue = revenueData.map((d: any) => ({
    label: d.label,
    value: d.value > 1000 ? Math.round(d.value / 1000) : d.value,
  }));

  const costliestVehicles = charts?.costliestVehicles || [];

  return (
    <>
      <PageHeader
        title="Reports & Analytics"
        description="How the fleet performed — money in, money out, and where it went."
      />

      {isKpisLoading ? (
        <div className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4 animate-pulse">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-24 rounded-2xl bg-card border border-border" />
          ))}
        </div>
      ) : (
        <div className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
          <StatCard label="Fuel Efficiency" value={kpis?.fuelEfficiency || "8.4 km/L"} accent="blue" />
          <StatCard label="Fleet Utilization" value={kpis?.utilization || "81%"} accent="green" />
          <StatCard
            label="Operational Cost"
            value={kpis?.operationalCost ? `₹ ${kpis.operationalCost.toLocaleString()}` : "₹ 34,070"}
            accent="amber"
          />
          <StatCard label="Vehicle ROI" value={kpis?.vehicleRoi || "14.2%"} accent="primary" />
        </div>
      )}

      <p className="mb-6 text-xs text-muted-foreground">
        <span className="font-semibold text-foreground">ROI</span> = (Revenue − (Maintenance + Fuel)) / Acquisition Cost
      </p>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1.4fr_1fr]">
        <Card className="p-5">
          <h2 className="mb-6 font-display text-lg text-ink">Monthly Revenue (₹ '000)</h2>
          {isChartsLoading ? (
            <div className="h-[220px] bg-muted animate-pulse rounded" />
          ) : (
            <BarChart data={formattedRevenue} height={220} />
          )}
        </Card>

        <Card className="p-5">
          <h2 className="mb-4 font-display text-lg text-ink">Top Costliest Vehicles (₹)</h2>
          {isChartsLoading ? (
            <div className="space-y-2 animate-pulse">
              <div className="h-6 bg-muted rounded w-full" />
              <div className="h-6 bg-muted rounded w-full" />
            </div>
          ) : costliestVehicles.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">No maintenance or fuel costs registered.</p>
          ) : (
            <div className="space-y-2">
              {costliestVehicles.map((v: any, i: number) => {
                const maxVal = Math.max(...costliestVehicles.map((x: any) => x.value), 1);
                const colors = ["red", "amber", "blue", "slate", "green"];
                const color = colors[i % colors.length] as any;
                return (
                  <HorizontalBar
                    key={v.label}
                    label={v.label}
                    value={v.value}
                    max={maxVal}
                    color={color}
                  />
                );
              })}
            </div>
          )}
        </Card>
      </div>
    </>
  );
}
