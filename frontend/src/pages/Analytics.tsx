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

  // Query Charts (Operating Cost Trend)
  const { data: charts, isLoading: isChartsLoading } = useQuery({
    queryKey: ["dashboard-charts"],
    queryFn: async () => {
      const res = await apiClient.get("/api/dashboard/charts");
      return res.data;
    },
  });

  // Query Operational Cost Report (to find costliest vehicles)
  const { data: operationalCosts, isLoading: isCostsLoading } = useQuery({
    queryKey: ["reports-operational-cost"],
    queryFn: async () => {
      const res = await apiClient.get("/api/reports/operational-cost");
      return res.data;
    },
  });

  const costTrendData = charts?.cost_trend || [];
  const formattedCostTrend = costTrendData.map((d: any) => {
    const [year, monthStr] = d.month.split("-");
    const dateObj = new Date(Number(year), Number(monthStr) - 1, 1);
    const label = dateObj.toLocaleDateString("en-US", { month: "short" });
    const totalCost = Number(d.fuel_cost) + Number(d.maintenance_cost) + Number(d.other_expense_cost);
    return {
      label,
      value: totalCost > 1000 ? Math.round(totalCost / 1000) : totalCost,
    };
  });

  const rawCosts: any[] = Array.isArray(operationalCosts) ? operationalCosts : [];
  const costliestVehicles = [...rawCosts]
    .sort((a, b) => Number(b.total_cost) - Number(a.total_cost))
    .slice(0, 5)
    .map((item) => ({
      label: item.registration_number,
      value: Number(item.total_cost),
    }));

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
          <StatCard label="Fuel Efficiency" value={kpis?.fuel_efficiency !== undefined ? `${Number(kpis.fuel_efficiency).toFixed(1)} km/L` : "0.0 km/L"} accent="blue" />
          <StatCard label="Fleet Utilization" value={kpis?.fleet_utilization_pct !== undefined ? `${Number(kpis.fleet_utilization_pct).toFixed(1)}%` : "0.0%"} accent="green" />
          <StatCard
            label="Operational Cost"
            value={kpis?.operational_cost ? `₹ ${Number(kpis.operational_cost).toLocaleString("en-IN")}` : "₹ 0"}
            accent="amber"
          />
          <StatCard label="Vehicle ROI" value={kpis?.roi !== undefined && kpis.roi !== "N/A" ? `${Number(kpis.roi).toFixed(1)}%` : "N/A"} accent="primary" />
        </div>
      )}

      <p className="mb-6 text-xs text-muted-foreground">
        <span className="font-semibold text-foreground">ROI</span> = (Revenue − (Maintenance + Fuel)) / Acquisition Cost
      </p>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1.4fr_1fr]">
        <Card className="p-5">
          <h2 className="mb-6 font-display text-lg text-ink">Monthly Operating Cost (₹ '000)</h2>
          {isChartsLoading ? (
            <div className="h-[220px] bg-muted animate-pulse rounded" />
          ) : formattedCostTrend.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">No monthly operating cost logged.</p>
          ) : (
            <BarChart data={formattedCostTrend} height={220} />
          )}
        </Card>

        <Card className="p-5">
          <h2 className="mb-4 font-display text-lg text-ink">Top Costliest Vehicles (₹)</h2>
          {isCostsLoading || isChartsLoading ? (
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
