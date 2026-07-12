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
import { DriverResponse, LicenseCategory, DriverStatus } from "../types";

// Driver validation matching schemas/driver.json
const driverFormSchema = z.object({
  name: z.string().min(2, "Driver name is required"),
  license_number: z.string().min(5, "License number must be at least 5 characters"),
  license_category: z.enum(["A", "B", "C", "D", "E", "CE", "DE"] as const),
  license_expiry: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Use YYYY-MM-DD date format"),
  contact_number: z
    .string()
    .min(7, "Contact number must be at least 7 characters")
    .max(20, "Contact number must be 20 characters or less")
    .regex(/^[+]?[0-9\s\-()]+$/, "Invalid phone format (e.g. +91 99999 99999 or 09999999999)"),
  safety_score: z.coerce.number().min(0, "Cannot be less than 0").max(100, "Cannot exceed 100"),
  status: z.enum(["available", "on_trip", "off_duty", "suspended"] as const),
});

type DriverFormValues = z.infer<typeof driverFormSchema>;

export default function Drivers() {
  const { canWrite } = useAuth();
  const queryClient = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [filters, setFilters] = useState({
    status: "All",
    search: "",
  });

  // Query drivers registry
  const { data: pageData, isLoading } = useQuery({
    queryKey: ["drivers", filters.status],
    queryFn: async () => {
      const params: any = {};
      if (filters.status !== "All") {
        params.status_filter = filters.status;
      }
      const res = await apiClient.get("/api/drivers", { params });
      return res.data;
    },
  });

  const rawDrivers: DriverResponse[] = Array.isArray(pageData) ? pageData : pageData?.items || [];

  const drivers = rawDrivers.filter((d) => {
    const matchSearch =
      !filters.search ||
      d.name.toLowerCase().includes(filters.search.toLowerCase()) ||
      d.license_number.toLowerCase().includes(filters.search.toLowerCase());
    return matchSearch;
  });

  // Mutation to create driver
  const createDriverMutation = useMutation({
    mutationFn: async (data: DriverFormValues) => {
      const res = await apiClient.post("/api/drivers", data);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["drivers"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-kpis"] });
      setShowModal(false);
      reset();
    },
    onError: (err: any) => {
      setErrorMsg(err.response?.data?.message || err.response?.data?.detail || "Failed to add driver. Ensure license number is unique.");
    },
  });

  // Form setup
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<DriverFormValues>({
    resolver: zodResolver(driverFormSchema),
    defaultValues: {
      name: "",
      license_number: "",
      license_category: "B",
      license_expiry: new Date(Date.now() + 365 * 24 * 3600000).toISOString().split("T")[0],
      contact_number: "",
      safety_score: 100,
      status: "available",
    },
  });

  const onSubmit = (data: DriverFormValues) => {
    setErrorMsg(null);
    createDriverMutation.mutate(data);
  };

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
  };

  return (
    <>
      <PageHeader
        title="Drivers & Safety"
        description="Roster, license validity and duty state across your teams."
        actions={
          canWrite("drivers") && (
            <button
              onClick={() => {
                setErrorMsg(null);
                setShowModal(true);
              }}
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 cursor-pointer"
            >
              <Plus className="h-4 w-4" /> Add Driver
            </button>
          )
        }
      />

      <Card className="mb-4 p-4">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <SectionHeader className="mb-1">Status</SectionHeader>
            <Select
              value={filters.status}
              onChange={(e) => setFilters((prev) => ({ ...prev, status: e.target.value }))}
            >
              <option value="All">All</option>
              <option value="available">Available</option>
              <option value="on_trip">On Trip</option>
              <option value="off_duty">Off Duty</option>
              <option value="suspended">Suspended</option>
            </Select>
          </div>
          <div>
            <SectionHeader className="mb-1">Driver Search</SectionHeader>
            <TextInput
              placeholder="Search driver name or license…"
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
          ) : drivers.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">No drivers match search filters.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                  <th className="pb-3 pr-4">Driver</th>
                  <th className="pb-3 pr-4">License No.</th>
                  <th className="pb-3 pr-4">Category</th>
                  <th className="pb-3 pr-4">Expiry</th>
                  <th className="pb-3 pr-4">Contact</th>
                  <th className="pb-3 pr-4">Safety Score</th>
                  <th className="pb-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {drivers.map((d) => (
                  <tr key={d.id}>
                    <td className="py-3 pr-4 font-medium">{d.name}</td>
                    <td className="py-3 pr-4 font-mono text-xs">{d.license_number}</td>
                    <td className="py-3 pr-4 text-muted-foreground">{d.license_category}</td>
                    <td
                      className={`py-3 pr-4 ${
                        d.is_license_expired ? "text-status-red font-medium" : "text-muted-foreground"
                      }`}
                    >
                      {formatDate(d.license_expiry)} {d.is_license_expired && "(EXPIRED)"}
                    </td>
                    <td className="py-3 pr-4 font-mono text-xs text-muted-foreground">
                      {d.contact_number}
                    </td>
                    <td className="py-3 pr-4 tabular-nums text-muted-foreground font-medium">
                      {d.safety_score}%
                    </td>
                    <td className="py-3">
                      <StatusBadge variant={d.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </Card>

      <div className="mt-6">
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Duty States Reference</p>
        <div className="flex flex-wrap gap-2">
          <StatusBadge variant="available" />
          <StatusBadge variant="on_trip" />
          <StatusBadge variant="off_duty" />
          <StatusBadge variant="suspended" />
        </div>
      </div>

      {/* Add Driver Modal */}
      {canWrite("drivers") && showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <Card className="w-full max-w-lg bg-card p-6 shadow-2xl relative">
            <button
              onClick={() => setShowModal(false)}
              className="absolute right-4 top-4 text-muted-foreground hover:text-foreground cursor-pointer"
            >
              <X className="h-5 w-5" />
            </button>

            <h3 className="font-display text-xl text-ink mb-4">Register New Driver</h3>

            {errorMsg && (
              <div className="mb-4 flex items-center gap-2 rounded-lg bg-status-red/10 p-3 text-sm text-status-red">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <FormField label="Full Name" error={errors.name?.message}>
                <TextInput placeholder="Alex" {...register("name")} />
              </FormField>

              <div className="grid grid-cols-2 gap-4">
                <FormField label="License Number" error={errors.license_number?.message}>
                  <TextInput placeholder="DL-88213" {...register("license_number")} />
                </FormField>
                <FormField label="License Category" error={errors.license_category?.message}>
                  <Select {...register("license_category")}>
                    <option value="B">LMV (B)</option>
                    <option value="CE">HMV (CE)</option>
                    <option value="C">Transport (C)</option>
                    <option value="A">Motorcycle (A)</option>
                    <option value="D">Bus (D)</option>
                  </Select>
                </FormField>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <FormField label="License Expiry" error={errors.license_expiry?.message}>
                  <TextInput type="date" {...register("license_expiry")} />
                </FormField>
                <FormField label="Contact Number" error={errors.contact_number?.message}>
                  <TextInput placeholder="9876543210" {...register("contact_number")} />
                </FormField>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <FormField label="Safety Score (%)" error={errors.safety_score?.message}>
                  <TextInput type="number" {...register("safety_score")} />
                </FormField>
                <FormField label="Status" error={errors.status?.message}>
                  <Select {...register("status")}>
                    <option value="available">Available</option>
                    <option value="off_duty">Off Duty</option>
                    <option value="suspended">Suspended</option>
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
                  {isSubmitting ? "Registering..." : "Register Driver"}
                </button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </>
  );
}
