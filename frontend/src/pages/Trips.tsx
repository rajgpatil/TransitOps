import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Plus, X, Route as RouteIcon, Check } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { PageHeader } from "../components/AppShell";
import { StatusBadge } from "../components/StatusBadge";
import { Card, SectionHeader } from "../components/SectionHeader";
import { FormField, TextInput, Select } from "../components/FormField";
import { LifecycleStepper } from "../components/LifecycleStepper";
import { apiClient } from "../api/client";
import { useAuth } from "../contexts/AuthContext";
import { TripResponse, VehicleResponse, DriverResponse } from "../types";

// Validation schema for creating a trip
const tripCreateSchema = z.object({
  source: z.string().min(2, "Source is required"),
  destination: z.string().min(2, "Destination is required"),
  vehicle_id: z.coerce.number().positive("Select a vehicle"),
  driver_id: z.coerce.number().positive("Select a driver"),
  cargo_weight: z.coerce.number().positive("Weight must be positive"),
  planned_distance: z.coerce.number().positive("Distance must be positive"),
  revenue: z.coerce.number().nonnegative("Revenue must be non-negative").optional(),
});

type TripCreateValues = z.infer<typeof tripCreateSchema>;

// Validation schema for completing a trip
const tripCompleteSchema = (minOdo: number) =>
  z.object({
    actual_distance: z.coerce.number().positive("Actual distance must be positive"),
    fuel_consumed: z.coerce.number().positive("Fuel consumed must be positive"),
    final_odometer: z.coerce
      .number()
      .min(minOdo, `Final odometer must be at least ${minOdo.toLocaleString()} km`),
    revenue: z.coerce.number().nonnegative("Revenue must be non-negative").optional(),
  });

type TripCompleteValues = z.infer<ReturnType<typeof tripCompleteSchema>>;

export default function Trips() {
  const { canWrite } = useAuth();
  const queryClient = useQueryClient();
  const [completeTripId, setCompleteTripId] = useState<number | null>(null);
  const [cancelTripId, setCancelTripId] = useState<number | null>(null);
  const [cancelReason, setCancelReason] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Queries
  const { data: tripsPage, isLoading: isTripsLoading } = useQuery({
    queryKey: ["trips"],
    queryFn: async () => {
      const res = await apiClient.get("/api/trips");
      return res.data;
    },
  });

  const { data: vehiclesPage } = useQuery({
    queryKey: ["vehicles"],
    queryFn: async () => {
      const res = await apiClient.get("/api/vehicles");
      return res.data;
    },
  });

  const { data: driversPage } = useQuery({
    queryKey: ["drivers", "available"],
    queryFn: async () => {
      const res = await apiClient.get("/api/drivers/available");
      return res.data;
    },
  });

  const trips: TripResponse[] = Array.isArray(tripsPage) ? tripsPage : tripsPage?.items || [];
  
  const rawVehicles: VehicleResponse[] = Array.isArray(vehiclesPage) ? vehiclesPage : vehiclesPage?.items || [];
  const availableVehicles = rawVehicles.filter((v) => v.status === "available");
  
  const availableDrivers: DriverResponse[] = Array.isArray(driversPage) ? driversPage : driversPage?.items || [];

  // Form hooks
  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<TripCreateValues>({
    resolver: zodResolver(tripCreateSchema),
    defaultValues: {
      source: "",
      destination: "",
      cargo_weight: 0,
      planned_distance: 0,
      revenue: 0,
    },
  });

  const selectedVehicleId = watch("vehicle_id");
  const typedCargoWeight = watch("cargo_weight") || 0;

  // Find selected vehicle details for real-time capacity validation
  const selectedVehicle = availableVehicles.find((v) => v.id === Number(selectedVehicleId));
  const isOverCapacity =
    selectedVehicle && typedCargoWeight > selectedVehicle.max_load_capacity;
  const capacityExcess = selectedVehicle ? typedCargoWeight - selectedVehicle.max_load_capacity : 0;

  // Complete Trip Form
  const currentVehicleOdo =
    trips.find((t) => t.id === completeTripId)?.vehicle?.odometer || 0;

  const {
    register: registerComplete,
    handleSubmit: handleSubmitComplete,
    reset: resetComplete,
    formState: { errors: errorsComplete, isSubmitting: isCompleting },
  } = useForm<TripCompleteValues>({
    resolver: zodResolver(tripCompleteSchema(currentVehicleOdo)),
    values: {
      actual_distance: trips.find((t) => t.id === completeTripId)?.planned_distance || 0,
      fuel_consumed: 0,
      final_odometer: currentVehicleOdo,
      revenue: trips.find((t) => t.id === completeTripId)?.revenue || 0,
    },
  });

  // Mutations
  const createTripMutation = useMutation({
    mutationFn: async (data: TripCreateValues) => {
      const res = await apiClient.post("/api/trips", data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trips"] });
      reset();
    },
    onError: (err: any) => {
      setErrorMsg(err.response?.data?.message || "Failed to create trip.");
    },
  });

  const dispatchMutation = useMutation({
    mutationFn: async (id: number) => {
      const res = await apiClient.post(`/api/trips/${id}/dispatch`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trips"] });
      queryClient.invalidateQueries({ queryKey: ["vehicles"] });
      queryClient.invalidateQueries({ queryKey: ["drivers"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-kpis"] });
    },
  });

  const completeMutation = useMutation({
    mutationFn: async ({ id, data }: { id: number; data: TripCompleteValues }) => {
      const res = await apiClient.post(`/api/trips/${id}/complete`, data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trips"] });
      queryClient.invalidateQueries({ queryKey: ["vehicles"] });
      queryClient.invalidateQueries({ queryKey: ["drivers"] });
      queryClient.invalidateQueries({ queryKey: ["fuel-logs"] });
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-kpis"] });
      setCompleteTripId(null);
      resetComplete();
    },
  });

  const cancelMutation = useMutation({
    mutationFn: async ({ id, reason }: { id: number; reason: string }) => {
      const res = await apiClient.post(`/api/trips/${id}/cancel`, { reason });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["trips"] });
      queryClient.invalidateQueries({ queryKey: ["vehicles"] });
      queryClient.invalidateQueries({ queryKey: ["drivers"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-kpis"] });
      setCancelTripId(null);
      setCancelReason("");
    },
  });

  const handleCreateTrip = (data: TripCreateValues) => {
    if (isOverCapacity) return;
    setErrorMsg(null);
    createTripMutation.mutate(data);
  };

  const handleCompleteTrip = (data: TripCompleteValues) => {
    if (completeTripId) {
      completeMutation.mutate({ id: completeTripId, data });
    }
  };

  const handleCancelTrip = () => {
    if (cancelTripId) {
      cancelMutation.mutate({ id: cancelTripId, reason: cancelReason });
    }
  };

  return (
    <>
      <PageHeader
        title="Trip Dispatcher"
        description="Plan, validate and dispatch trips with live capacity and driver checks."
      />

      <div className={
        canWrite("trips")
          ? "grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]"
          : "grid grid-cols-1 gap-6"
      }>
        {/* Left: Create Form */}
        {canWrite("trips") && (
          <Card className="p-6 h-fit">
            <SectionHeader className="mb-3">Trip Lifecycle</SectionHeader>
            <LifecycleStepper current={trips.some(t => t.status === "dispatched") ? "dispatched" : "draft"} />

            <h2 className="mt-8 font-display text-lg text-ink">Create Trip</h2>
            {errorMsg && (
              <div className="mt-3 flex items-center gap-2 rounded-lg bg-status-red/10 p-3 text-sm text-status-red">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            <form onSubmit={handleSubmit(handleCreateTrip)} className="mt-4 space-y-4">
              <FormField label="Source" error={errors.source?.message}>
                <TextInput placeholder="Gandhinagar Depot" {...register("source")} />
              </FormField>
              <FormField label="Destination" error={errors.destination?.message}>
                <TextInput placeholder="Ahmedabad Hub" {...register("destination")} />
              </FormField>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FormField label="Vehicle (Available Only)" error={errors.vehicle_id?.message}>
                  <Select {...register("vehicle_id")}>
                    <option value="">Select vehicle</option>
                    {availableVehicles.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.name} ({v.registration_number}) · {v.max_load_capacity} kg cap
                      </option>
                    ))}
                  </Select>
                </FormField>

                <FormField label="Driver (Available Only)" error={errors.driver_id?.message}>
                  <Select {...register("driver_id")}>
                    <option value="">Select driver</option>
                    {availableDrivers.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name} (DL: {d.license_number}) · Score: {d.safety_score}%
                      </option>
                    ))}
                  </Select>
                </FormField>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <FormField label="Cargo Weight (kg)" error={errors.cargo_weight?.message}>
                  <TextInput type="number" {...register("cargo_weight")} />
                </FormField>
                <FormField label="Planned Distance (km)" error={errors.planned_distance?.message}>
                  <TextInput type="number" {...register("planned_distance")} />
                </FormField>
              </div>

              <FormField label="Est. Revenue (₹) - Optional" error={errors.revenue?.message}>
                <TextInput type="number" {...register("revenue")} />
              </FormField>

              {isOverCapacity && selectedVehicle && (
                <div className="mt-5 rounded-xl border border-status-red/30 bg-status-red/5 p-4 text-sm">
                  <div className="flex items-start gap-2.5">
                    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-status-red" />
                    <div className="space-y-1">
                      <div className="text-foreground">
                        <span className="font-medium">Vehicle capacity:</span>{" "}
                        {selectedVehicle.max_load_capacity} kg
                      </div>
                      <div className="text-foreground">
                        <span className="font-medium">Cargo weight:</span> {typedCargoWeight} kg
                      </div>
                      <div className="font-medium text-status-red">
                        Capacity exceeded by {capacityExcess} kg — dispatch blocked
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div className="mt-5 flex flex-wrap items-center gap-3">
                <button
                  type="submit"
                  disabled={isSubmitting || isOverCapacity || !canWrite("trips")}
                  className="rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 disabled:bg-muted disabled:text-muted-foreground disabled:cursor-not-allowed cursor-pointer"
                >
                  Create Draft Trip
                </button>
                <button
                  type="button"
                  onClick={() => reset()}
                  className="rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium text-foreground hover:bg-accent cursor-pointer"
                >
                  Cancel
                </button>
              </div>
            </form>
          </Card>
        )}

        {/* Right: Live Board */}
        <div>
          <h2 className="mb-3 font-display text-lg text-ink">Live Board</h2>
          {isTripsLoading ? (
            <div className="space-y-3 animate-pulse">
              <div className="h-28 bg-card border rounded-2xl" />
              <div className="h-28 bg-card border rounded-2xl" />
            </div>
          ) : trips.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground bg-card border rounded-2xl">
              No trips logged.
            </p>
          ) : (
            <div className="space-y-3">
              {trips.map((t) => (
                <Card key={t.id} className="p-4 relative">
                  <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-foreground">TR00{t.id}</span>
                        <StatusBadge variant={t.status} />
                      </div>
                      <p className="mt-1 truncate text-sm text-foreground font-medium">
                        {t.source} → {t.destination}
                      </p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        Weight: {t.cargo_weight} kg · Distance: {t.planned_distance} km
                        {t.revenue ? ` · Rev: ₹${t.revenue.toLocaleString()}` : ""}
                      </p>
                    </div>
                    <div className="shrink-0 text-right">
                      <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                        {t.vehicle?.name || "Unassigned"} / {t.driver?.name || "Unassigned"}
                      </div>
                      <div className="mt-1 text-xs text-foreground">
                        {t.status === "draft" && "Awaiting Dispatch"}
                        {t.status === "dispatched" && "In Transit"}
                        {t.status === "completed" && `Completed at ${new Date(t.completed_at || "").toLocaleDateString()}`}
                        {t.status === "cancelled" && "Cancelled"}
                      </div>
                    </div>
                  </div>

                  {/* Actions for draft and dispatched states */}
                  {canWrite("trips") && (
                    <div className="mt-4 flex gap-2 border-t border-border/60 pt-3">
                      {t.status === "draft" && (
                        <button
                          onClick={() => dispatchMutation.mutate(t.id)}
                          className="inline-flex items-center gap-1 rounded bg-status-blue/10 px-2.5 py-1 text-xs font-semibold text-status-blue hover:bg-status-blue/20 cursor-pointer"
                        >
                          Dispatch Trip
                        </button>
                      )}
                      {t.status === "dispatched" && (
                        <>
                          <button
                            onClick={() => setCompleteTripId(t.id)}
                            className="inline-flex items-center gap-1 rounded bg-status-green/10 px-2.5 py-1 text-xs font-semibold text-status-green hover:bg-status-green/20 cursor-pointer"
                          >
                            <Check className="h-3 w-3" /> Log Complete
                          </button>
                          <button
                            onClick={() => setCancelTripId(t.id)}
                            className="inline-flex items-center gap-1 rounded bg-status-red/10 px-2.5 py-1 text-xs font-semibold text-status-red hover:bg-status-red/20 cursor-pointer"
                          >
                            Cancel
                          </button>
                        </>
                      )}
                    </div>
                  )}
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Complete Trip Modal */}
      {completeTripId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <Card className="w-full max-w-md bg-card p-6 shadow-2xl relative">
            <button
              onClick={() => setCompleteTripId(null)}
              className="absolute right-4 top-4 text-muted-foreground hover:text-foreground cursor-pointer"
            >
              <X className="h-5 w-5" />
            </button>

            <h3 className="font-display text-xl text-ink mb-4">Complete Trip TR00{completeTripId}</h3>
            <p className="text-xs text-muted-foreground mb-4">
              Current vehicle odometer reading: <span className="font-semibold text-foreground">{currentVehicleOdo.toLocaleString()} km</span>
            </p>

            <form onSubmit={handleSubmitComplete(handleCompleteTrip)} className="space-y-4">
              <FormField label="Actual Distance (km)" error={errorsComplete.actual_distance?.message}>
                <TextInput type="number" {...registerComplete("actual_distance")} />
              </FormField>

              <FormField label="Fuel Consumed (liters)" error={errorsComplete.fuel_consumed?.message}>
                <TextInput type="number" {...registerComplete("fuel_consumed")} />
              </FormField>

              <FormField label="Final Odometer Reading (km)" error={errorsComplete.final_odometer?.message}>
                <TextInput type="number" {...registerComplete("final_odometer")} />
              </FormField>

              <FormField label="Final Revenue (₹)" error={errorsComplete.revenue?.message}>
                <TextInput type="number" {...registerComplete("revenue")} />
              </FormField>

              <div className="mt-6 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setCompleteTripId(null)}
                  className="rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium text-foreground hover:bg-accent cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isCompleting}
                  className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 disabled:opacity-50 cursor-pointer"
                >
                  {isCompleting ? "Saving..." : "Complete Trip"}
                </button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* Cancel Trip Modal */}
      {cancelTripId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <Card className="w-full max-w-md bg-card p-6 shadow-2xl relative">
            <button
              onClick={() => setCancelTripId(null)}
              className="absolute right-4 top-4 text-muted-foreground hover:text-foreground cursor-pointer"
            >
              <X className="h-5 w-5" />
            </button>

            <h3 className="font-display text-xl text-ink mb-4">Cancel Trip TR00{cancelTripId}</h3>

            <div className="space-y-4">
              <FormField label="Cancellation Reason">
                <TextInput
                  placeholder="e.g. Vehicle went to shop, driver called in sick..."
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                />
              </FormField>

              <div className="mt-6 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setCancelTripId(null)}
                  className="rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium text-foreground hover:bg-accent cursor-pointer"
                >
                  Discard
                </button>
                <button
                  onClick={handleCancelTrip}
                  className="rounded-lg bg-status-red px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-status-red/90 cursor-pointer"
                >
                  Cancel Trip
                </button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </>
  );
}
