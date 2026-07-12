import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { PageHeader } from "../components/AppShell";
import { StatCard } from "../components/StatCard";
import { StatusBadge } from "../components/StatusBadge";
import { HorizontalBar } from "../components/charts";
import { Card, SectionHeader } from "../components/SectionHeader";
import { Select } from "../components/FormField";
import { apiClient } from "../api/client";
import { TripResponse } from "../types";

export default function Dashboard() {
  const [filters, setFilters] = useState({
    type: "All",
    status: "All",
    region: "All",
  });

  // Query KPIs (passing filters to refetch dynamically)
  const { data: kpis, isLoading: isKpisLoading } = useQuery({
    queryKey: ["dashboard-kpis", filters],
    queryFn: async () => {
      const res = await apiClient.get("/api/dashboard/kpis", { params: filters });
      return res.data;
    },
  });

  // Query charts data
  const { data: charts, isLoading: isChartsLoading } = useQuery({
    queryKey: ["dashboard-charts"],
    queryFn: async () => {
      const res = await apiClient.get("/api/dashboard/charts");
      return res.data;
    },
  });

  // Query recent trips
  const { data: tripsPage, isLoading: isTripsLoading } = useQuery({
    queryKey: ["recent-trips"],
    queryFn: async () => {
      const res = await apiClient.get("/api/trips", { params: { page: 1, page_size: 4 } });
      return res.data;
    },
  });

  const recentTrips = tripsPage?.items || [];

  return (
    <>
      <PageHeader title="Dashboard" description="Live snapshot of your operations across depots." />

      <Card className="mb-6 p-4">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div>
            <SectionHeader className="mb-1">Vehicle Type</SectionHeader>
            <Select
              value={filters.type}
              onChange={(e) => setFilters((prev) => ({ ...prev, type: e.target.value }))}
            >
              <option value="All">All</option>
              <option value="van">Van</option>
              <option value="truck">Truck</option>
              <option value="pickup">Mini / Pickup</option>
            </Select>
          </div>
          <div>
            <SectionHeader className="mb-1">Status</SectionHeader>
            <Select
              value={filters.status}
              onChange={(e) => setFilters((prev) => ({ ...prev, status: e.target.value }))}
            >
              <option value="All">All</option>
              <option value="available">Available</option>
              <option value="on_trip">On Trip</option>
              <option value="in_shop">In Shop</option>
            </Select>
          </div>
          <div>
            <SectionHeader className="mb-1">Region</SectionHeader>
            <Select
              value={filters.region}
              onChange={(e) => setFilters((prev) => ({ ...prev, region: e.target.value }))}
            >
              <option value="All">All</option>
              <option value="Gandhinagar">Gandhinagar</option>
              <option value="Ahmedabad">Ahmedabad</option>
              <option value="Sanand">Sanand</option>
            </Select>
          </div>
        </div>
      </Card>

      {isKpisLoading ? (
        <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-7 animate-pulse">
          {[...Array(7)].map((_, i) => (
            <div key={i} className="h-24 rounded-2xl bg-card border border-border" />
          ))}
        </div>
      ) : (
        <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-7">
          <StatCard label="Active Vehicles" value={kpis?.activeVehicles ?? 0} accent="blue" />
          <StatCard label="Available" value={kpis?.availableVehicles ?? 0} accent="green" />
          <StatCard label="In Maintenance" value={kpis?.inShopVehicles ?? 0} accent="amber" />
          <StatCard label="Active Trips" value={kpis?.activeTrips ?? 0} accent="blue" />
          <StatCard label="Pending Trips" value={kpis?.pendingTrips ?? 0} accent="slate" />
          <StatCard label="Drivers On Duty" value={kpis?.driversOnDuty ?? 0} accent="primary" />
          <StatCard label="Fleet Utilization" value={kpis?.utilization ?? "0%"} accent="green" />
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1.5fr_1fr]">
        <Card className="p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-display text-lg text-ink">Recent Trips</h2>
            <Link to="/trips" className="text-xs font-medium text-primary hover:underline">
              View all
            </Link>
          </div>
          <div className="overflow-x-auto">
            {isTripsLoading ? (
              <div className="space-y-3 py-4 animate-pulse">
                <div className="h-6 bg-muted rounded w-3/4" />
                <div className="h-6 bg-muted rounded w-5/6" />
                <div className="h-6 bg-muted rounded w-2/3" />
              </div>
            ) : recentTrips.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">No recent trips logged.</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                    <th className="pb-3 pr-4">Trip</th>
                    <th className="pb-3 pr-4">Vehicle</th>
                    <th className="pb-3 pr-4">Driver</th>
                    <th className="pb-3 pr-4">Status</th>
                    <th className="pb-3">Details / ETA</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {recentTrips.map((t: TripResponse) => (
                    <tr key={t.id} className="text-foreground">
                      <td className="py-3 pr-4 font-medium">TR00{t.id}</td>
                      <td className="py-3 pr-4 text-muted-foreground">
                        {t.vehicle?.name || "—"}
                      </td>
                      <td className="py-3 pr-4 text-muted-foreground">
                        {t.driver?.name || "—"}
                      </td>
                      <td className="py-3 pr-4">
                        <StatusBadge variant={t.status} />
                      </td>
                      <td className="py-3 text-muted-foreground text-xs">
                        {t.status === "dispatched" && "In transit"}
                        {t.status === "completed" && `Completed (${t.actual_distance} km)`}
                        {t.status === "cancelled" && `Cancelled: ${t.cancel_reason}`}
                        {t.status === "draft" && "Awaiting dispatch"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </Card>

        <Card className="p-5">
          <h2 className="mb-4 font-display text-lg text-ink">Vehicle Status</h2>
          {isChartsLoading ? (
            <div className="space-y-3 py-4 animate-pulse">
              <div className="h-4 bg-muted rounded w-full" />
              <div className="h-4 bg-muted rounded w-full" />
              <div className="h-4 bg-muted rounded w-full" />
            </div>
          ) : (
            <div className="space-y-1">
              <HorizontalBar label="Available" value={kpis?.availableVehicles ?? 0} max={kpis?.totalVehicles ?? 10} color="green" />
              <HorizontalBar label="On Trip" value={kpis?.activeTrips ?? 0} max={kpis?.totalVehicles ?? 10} color="blue" />
              <HorizontalBar label="In Shop" value={kpis?.inShopVehicles ?? 0} max={kpis?.totalVehicles ?? 10} color="amber" />
              <HorizontalBar label="Retired" value={kpis?.retiredVehicles ?? 0} max={kpis?.totalVehicles ?? 10} color="red" />
            </div>
          )}
        </Card>
      </div>
    </>
  );
}
