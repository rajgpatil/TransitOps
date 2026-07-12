import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, X, AlertTriangle } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { PageHeader } from "../components/AppShell";
import { StatusBadge } from "../components/StatusBadge";
import { Card, SectionHeader } from "../components/SectionHeader";
import { Select, TextInput, FormField } from "../components/FormField";
import { apiClient } from "../api/client";
import { useAuth } from "../contexts/AuthContext";
import { VehicleResponse, VehicleType, VehicleStatus } from "../types";

// Validation schema matching schemas/vehicle.json
const vehicleFormSchema = z.object({
  registration_number: z
    .string()
    .min(1, "Registration number is required")
    .regex(/^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$/, "Invalid format (e.g. GJ01AB4521)"),
  name: z.string().min(2, "Name/Model is required"),
  type: z.enum(["truck", "van", "bus", "sedan", "pickup", "other"] as const),
  max_load_capacity: z.coerce.number().positive("Capacity must be positive"),
  odometer: z.coerce.number().min(0, "Odometer must be non-negative"),
  acquisition_cost: z.coerce.number().positive("Acquisition cost must be positive"),
  region: z.string().min(1, "Region is required"),
  status: z.enum(["available", "on_trip", "in_shop", "retired"] as const),
});

type VehicleFormValues = z.infer<typeof vehicleFormSchema>;

export default function Fleet() {
  const { canWrite } = useAuth();
  const queryClient = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [filters, setFilters] = useState({
    type: "All",
    status: "All",
    search: "",
  });

  // Query vehicles registry
  const { data: pageData, isLoading } = useQuery({
    queryKey: ["vehicles", filters],
    queryFn: async () => {
      const res = await apiClient.get("/api/vehicles", { params: filters });
      return res.data;
    },
  });

  const vehicles: VehicleResponse[] = pageData?.items || [];

  // Mutation to create a vehicle
  const createVehicleMutation = useMutation({
    mutationFn: async (data: VehicleFormValues) => {
      const res = await apiClient.post("/api/vehicles", data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["vehicles"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-kpis"] });
      setShowModal(false);
      reset();
    },
    onError: (err: any) => {
      setErrorMsg(err.response?.data?.message || "Failed to add vehicle. Verify registration number uniqueness.");
    },
  });

  // Form setup
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<VehicleFormValues>({
    resolver: zodResolver(vehicleFormSchema),
    defaultValues: {
      registration_number: "",
      name: "",
      type: "van",
      max_load_capacity: 500,
      odometer: 0,
      acquisition_cost: 500000,
      region: "Gandhinagar",
      status: "available",
    },
  });

  const onSubmit = (data: VehicleFormValues) => {
    setErrorMsg(null);
    createVehicleMutation.mutate(data);
  };

  return (
    <>
      <PageHeader
        title="Vehicle Registry"
        description="Every truck, van and mini in your fleet — one source of truth."
        actions={
          canWrite("fleet") && (
            <button
              onClick={() => {
                setErrorMsg(null);
                setShowModal(true);
              }}
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 cursor-pointer"
            >
              <Plus className="h-4 w-4" /> Add Vehicle
            </button>
          )
        }
      />

      <Card className="mb-4 p-4">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div>
            <SectionHeader className="mb-1">Type</SectionHeader>
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
              <option value="retired">Retired</option>
            </Select>
          </div>
          <div>
            <SectionHeader className="mb-1">Registration / Name</SectionHeader>
            <TextInput
              placeholder="Search reg. no or name…"
              value={filters.search}
              onChange={(e) => setFilters((prev) => ({ ...prev, search: e.target.value }))}
            />
          </div>
        </div>
      </Card>

      <Card className="p-5">
        <div className="overflow-x-auto">
          {isLoading ? (
            <div className="space-y-3 py-6 animate-pulse">
              <div className="h-6 bg-muted rounded w-full" />
              <div className="h-6 bg-muted rounded w-full" />
              <div className="h-6 bg-muted rounded w-full" />
            </div>
          ) : vehicles.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">No vehicles match filters.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                  <th className="pb-3 pr-4">Reg. No. (Unique)</th>
                  <th className="pb-3 pr-4">Name / Model</th>
                  <th className="pb-3 pr-4">Type</th>
                  <th className="pb-3 pr-4">Capacity</th>
                  <th className="pb-3 pr-4">Odometer</th>
                  <th className="pb-3 pr-4">Acq. Cost</th>
                  <th className="pb-3 pr-4">Region</th>
                  <th className="pb-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {vehicles.map((v) => (
                  <tr key={v.id}>
                    <td className="py-3 pr-4 font-mono text-xs">{v.registration_number}</td>
                    <td className="py-3 pr-4 font-medium">{v.name}</td>
                    <td className="py-3 pr-4 text-muted-foreground capitalize">{v.type}</td>
                    <td className="py-3 pr-4 text-muted-foreground">
                      {v.max_load_capacity >= 1000
                        ? `${v.max_load_capacity / 1000} Ton`
                        : `${v.max_load_capacity} kg`}
                    </td>
                    <td className="py-3 pr-4 tabular-nums text-muted-foreground">
                      {v.odometer.toLocaleString()} km
                    </td>
                    <td className="py-3 pr-4 tabular-nums text-muted-foreground">
                      ₹ {v.acquisition_cost.toLocaleString()}
                    </td>
                    <td className="py-3 pr-4 text-muted-foreground">{v.region || "—"}</td>
                    <td className="py-3">
                      <StatusBadge variant={v.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </Card>

      {/* Add Vehicle Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <Card className="w-full max-w-lg bg-card p-6 shadow-2xl relative">
            <button
              onClick={() => setShowModal(false)}
              className="absolute right-4 top-4 text-muted-foreground hover:text-foreground cursor-pointer"
            >
              <X className="h-5 w-5" />
            </button>

            <h3 className="font-display text-xl text-ink mb-4">Add Vehicle to Registry</h3>

            {errorMsg && (
              <div className="mb-4 flex items-center gap-2 rounded-lg bg-status-red/10 p-3 text-sm text-status-red">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <FormField label="Registration No." error={errors.registration_number?.message}>
                  <TextInput placeholder="GJ01AB4521" {...register("registration_number")} />
                </FormField>
                <FormField label="Name / Model" error={errors.name?.message}>
                  <TextInput placeholder="VAN-05" {...register("name")} />
                </FormField>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <FormField label="Type" error={errors.type?.message}>
                  <Select {...register("type")}>
                    <option value="van">Van</option>
                    <option value="truck">Truck</option>
                    <option value="pickup">Mini / Pickup</option>
                    <option value="bus">Bus</option>
                    <option value="sedan">Sedan</option>
                    <option value="other">Other</option>
                  </Select>
                </FormField>
                <FormField label="Capacity (kg)" error={errors.max_load_capacity?.message}>
                  <TextInput type="number" {...register("max_load_capacity")} />
                </FormField>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <FormField label="Odometer (km)" error={errors.odometer?.message}>
                  <TextInput type="number" {...register("odometer")} />
                </FormField>
                <FormField label="Acq. Cost (₹)" error={errors.acquisition_cost?.message}>
                  <TextInput type="number" {...register("acquisition_cost")} />
                </FormField>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <FormField label="Region" error={errors.region?.message}>
                  <TextInput placeholder="Gandhinagar" {...register("region")} />
                </FormField>
                <FormField label="Initial Status" error={errors.status?.message}>
                  <Select {...register("status")}>
                    <option value="available">Available</option>
                    <option value="in_shop">In Shop</option>
                    <option value="retired">Retired</option>
                  </Select>
                </FormField>
              </div>

              <div className="mt-6 flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium text-foreground hover:bg-accent cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 disabled:opacity-50 cursor-pointer"
                >
                  {isSubmitting ? "Saving..." : "Save Vehicle"}
                </button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </>
  );
}
