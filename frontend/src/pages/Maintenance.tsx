import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, Plus, X, AlertTriangle, Check } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { PageHeader } from "../components/AppShell";
import { StatusBadge } from "../components/StatusBadge";
import { Card, SectionHeader } from "../components/SectionHeader";
import { FormField, TextInput, Select } from "../components/FormField";
import { apiClient } from "../api/client";
import { useAuth } from "../contexts/AuthContext";
import { MaintenanceLogResponse, VehicleResponse, MaintenanceType } from "../types";

// Validation schema for creating a maintenance log
const maintenanceFormSchema = z.object({
  vehicle_id: z.coerce.number().positive("Select a vehicle"),
  maintenance_type: z.enum([
    "oil_change",
    "tire_replacement",
    "brake_service",
    "engine_repair",
    "body_work",
    "inspection",
    "electrical",
    "transmission",
    "other",
  ] as const),
  description: z.string().min(3, "Description is required"),
  cost: z.coerce.number().min(0, "Cost must be non-negative").optional(),
  started_at: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Use YYYY-MM-DD format"),
});

type MaintenanceFormValues = z.infer<typeof maintenanceFormSchema>;

// Validation schema for closing a maintenance log
const closeLogSchema = z.object({
  cost: z.coerce.number().min(0, "Cost must be non-negative"),
  notes: z.string().min(2, "Closing notes/resolution is required"),
});

type CloseLogValues = z.infer<typeof closeLogSchema>;

const serviceTypesList = [
  { value: "oil_change", label: "Oil Change" },
  { value: "tire_replacement", label: "Tire Replacement" },
  { value: "brake_service", label: "Brake Service" },
  { value: "engine_repair", label: "Engine Repair" },
  { value: "body_work", label: "Body Work" },
  { value: "inspection", label: "General Inspection" },
  { value: "electrical", label: "Electrical Work" },
  { value: "transmission", label: "Transmission Service" },
  { value: "other", label: "Other Wrench Work" },
];

export default function Maintenance() {
  const { canWrite } = useAuth();
  const queryClient = useQueryClient();
  const [closeLogId, setCloseLogId] = useState<number | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Queries
  const { data: logsPage, isLoading } = useQuery({
    queryKey: ["maintenance-logs"],
    queryFn: async () => {
      const res = await apiClient.get("/api/maintenance");
      return res.data;
    },
  });

  const { data: vehiclesPage } = useQuery({
    queryKey: ["vehicles", { status: "all" }],
    queryFn: async () => {
      const res = await apiClient.get("/api/vehicles");
      return res.data;
    },
  });

  const logs: MaintenanceLogResponse[] = Array.isArray(logsPage) ? logsPage : logsPage?.items || [];
  const allVehicles: VehicleResponse[] = Array.isArray(vehiclesPage) ? vehiclesPage : vehiclesPage?.items || [];
  // Filter out retired vehicles for dropdown
  const activeVehicles = allVehicles.filter(v => v.status !== "retired");

  // Form setups
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<MaintenanceFormValues>({
    resolver: zodResolver(maintenanceFormSchema),
    defaultValues: {
      maintenance_type: "oil_change",
      description: "",
      cost: 0,
      started_at: new Date().toISOString().split("T")[0],
    },
  });

  const {
    register: registerClose,
    handleSubmit: handleSubmitClose,
    reset: resetClose,
    formState: { errors: errorsClose, isSubmitting: isClosing },
  } = useForm<CloseLogValues>({
    resolver: zodResolver(closeLogSchema),
    values: {
      cost: logs.find(l => l.id === closeLogId)?.cost || 0,
      notes: "",
    },
  });

  // Mutations
  const logMutation = useMutation({
    mutationFn: async (data: MaintenanceFormValues) => {
      const res = await apiClient.post("/api/maintenance", data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["maintenance-logs"] });
      queryClient.invalidateQueries({ queryKey: ["vehicles"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-kpis"] });
      reset();
    },
    onError: (err: any) => {
      setErrorMsg(err.response?.data?.message || "Failed to log service record.");
    },
  });

  const closeMutation = useMutation({
    mutationFn: async ({ id, data }: { id: number; data: CloseLogValues }) => {
      const res = await apiClient.post(`/api/maintenance/${id}/close`, data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["maintenance-logs"] });
      queryClient.invalidateQueries({ queryKey: ["vehicles"] });
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-kpis"] });
      setCloseLogId(null);
      resetClose();
    },
  });

  const onSubmit = (data: MaintenanceFormValues) => {
    setErrorMsg(null);
    logMutation.mutate(data);
  };

  const handleCloseLog = (data: CloseLogValues) => {
    if (closeLogId) {
      closeMutation.mutate({ id: closeLogId, data });
    }
  };

  return (
    <>
      <PageHeader
        title="Maintenance"
        description="Every wrench turn logged — with the right vehicle taken off dispatch automatically."
      />

      <div className={
        canWrite("maintenance")
          ? "grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]"
          : "grid grid-cols-1 gap-6"
      }>
        {/* Left: Log service record */}
        {canWrite("maintenance") && (
          <Card className="p-6 h-fit">
            <h2 className="font-display text-lg text-ink">Log Service Record</h2>
            {errorMsg && (
              <div className="mt-3 flex items-center gap-2 rounded-lg bg-status-red/10 p-3 text-sm text-status-red">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="mt-4 space-y-4">
              <FormField label="Vehicle" error={errors.vehicle_id?.message}>
                <Select {...register("vehicle_id")}>
                  <option value="">Select vehicle</option>
                  {activeVehicles.map(v => (
                    <option key={v.id} value={v.id}>
                      {v.name} ({v.registration_number}) · {v.status}
                    </option>
                  ))}
                </Select>
              </FormField>

              <FormField label="Service Type" error={errors.maintenance_type?.message}>
                <Select {...register("maintenance_type")}>
                  {serviceTypesList.map(s => (
                    <option key={s.value} value={s.value}>
                      {s.label}
                    </option>
                  ))}
                </Select>
              </FormField>

              <FormField label="Description" error={errors.description?.message}>
                <TextInput placeholder=" radiator leak repair or oil swap..." {...register("description")} />
              </FormField>

              <div className="grid grid-cols-2 gap-4">
                <FormField label="Est. Cost (₹)" error={errors.cost?.message}>
                  <TextInput type="number" {...register("cost")} />
                </FormField>
                <FormField label="Date" error={errors.started_at?.message}>
                  <TextInput type="date" {...register("started_at")} />
                </FormField>
              </div>

              <button
                type="submit"
                disabled={isSubmitting || !canWrite("maintenance")}
                className="mt-6 w-full rounded-lg bg-primary py-2.5 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 disabled:bg-muted disabled:text-muted-foreground disabled:cursor-not-allowed cursor-pointer"
              >
                {isSubmitting ? "Saving..." : "Save Record"}
              </button>
            </form>

            {/* Stepper info */}
            <div className="mt-6 space-y-3 rounded-xl border border-border bg-paper p-4 text-xs">
              <div className="flex items-center gap-2">
                <StatusBadge variant="available" />
                <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-muted-foreground">creating active record</span>
                <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
                <StatusBadge variant="in_shop" />
              </div>
              <div className="flex items-center gap-2">
                <StatusBadge variant="in_shop" />
                <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-muted-foreground">closing record (not retired)</span>
                <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
                <StatusBadge variant="available" />
              </div>
            </div>
          </Card>
        )}

        {/* Right: Service Log */}
        <Card className="p-5">
          <h2 className="mb-4 font-display text-lg text-ink">Service Log</h2>
          <div className="overflow-x-auto">
            {isLoading ? (
              <div className="space-y-3 py-6 animate-pulse">
                <div className="h-6 bg-muted rounded w-full" />
                <div className="h-6 bg-muted rounded w-full" />
              </div>
            ) : logs.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">No service records logged yet.</p>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                    <th className="pb-3 pr-4">Vehicle</th>
                    <th className="pb-3 pr-4">Service</th>
                    <th className="pb-3 pr-4">Cost</th>
                    <th className="pb-3 pr-4">Status</th>
                    {canWrite("maintenance") && <th className="pb-3 text-right">Action</th>}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {logs.map((l) => (
                    <tr key={l.id}>
                      <td className="py-3 pr-4 font-medium">{l.vehicle?.name || "—"}</td>
                      <td className="py-3 pr-4 text-muted-foreground">
                        <span className="font-medium text-foreground block capitalize">
                          {l.maintenance_type.replace("_", " ")}
                        </span>
                        <span className="text-xs text-muted-foreground/90 block truncate max-w-xs">
                          {l.description}
                        </span>
                      </td>
                      <td className="py-3 pr-4 tabular-nums text-muted-foreground">
                        {l.cost ? `₹ ${l.cost.toLocaleString()}` : "—"}
                      </td>
                      <td className="py-3 pr-4">
                        <StatusBadge variant={l.status} />
                      </td>
                      {canWrite("maintenance") && (
                        <td className="py-3 text-right">
                          {l.status === "active" ? (
                            <button
                              onClick={() => setCloseLogId(l.id)}
                              className="inline-flex items-center gap-1 rounded bg-status-green/10 px-2 py-0.5 text-xs font-semibold text-status-green hover:bg-status-green/20 cursor-pointer"
                            >
                              <Check className="h-3 w-3" /> Close
                            </button>
                          ) : (
                            <span className="text-xs text-muted-foreground italic">Closed</span>
                          )}
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </Card>
      </div>

      {/* Close Maintenance Modal */}
      {closeLogId !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <Card className="w-full max-w-md bg-card p-6 shadow-2xl relative">
            <button
              onClick={() => setCloseLogId(null)}
              className="absolute right-4 top-4 text-muted-foreground hover:text-foreground cursor-pointer"
            >
              <X className="h-5 w-5" />
            </button>

            <h3 className="font-display text-xl text-ink mb-4">Close Service Record</h3>
            <p className="text-xs text-muted-foreground mb-4">
              Log final repairs, costs, and resolution. This will automatically release the vehicle back to Available status and log an operational expense.
            </p>

            <form onSubmit={handleSubmitClose(handleCloseLog)} className="space-y-4">
              <FormField label="Final Cost (₹)" error={errorsClose.cost?.message}>
                <TextInput type="number" {...registerClose("cost")} />
              </FormField>

              <FormField label="Resolution Notes" error={errorsClose.notes?.message}>
                <TextInput placeholder="e.g. Replaced oil filter, radiator hose replaced." {...registerClose("notes")} />
              </FormField>

              <div className="mt-6 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setCloseLogId(null)}
                  className="rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium text-foreground hover:bg-accent cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isClosing}
                  className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 disabled:opacity-50 cursor-pointer"
                >
                  {isClosing ? "Closing..." : "Close & Release"}
                </button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </>
  );
}
