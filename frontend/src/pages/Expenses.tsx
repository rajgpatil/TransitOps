import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, X, AlertTriangle } from "lucide-react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { PageHeader } from "../components/AppShell";
import { Card } from "../components/SectionHeader";
import { FormField, TextInput, Select } from "../components/FormField";
import { apiClient } from "../api/client";
import { useAuth } from "../contexts/AuthContext";
import { FuelLogResponse, ExpenseResponse, VehicleResponse, TripResponse } from "../types";

// Validation schema for Fuel Log
const fuelLogFormSchema = z.object({
  vehicle_id: z.coerce.number().positive("Select a vehicle"),
  trip_id: z.string().optional(),
  liters: z.coerce.number().positive("Liters must be positive"),
  cost: z.coerce.number().positive("Cost must be positive"),
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Use YYYY-MM-DD format"),
  odometer_at_fill: z.string().optional(),
});

type FuelLogFormValues = z.infer<typeof fuelLogFormSchema>;

// Validation schema for Expense
const expenseFormSchema = z.object({
  vehicle_id: z.coerce.number().positive("Select a vehicle"),
  trip_id: z.string().optional(),
  expense_type: z.enum([
    "toll",
    "parking",
    "insurance",
    "registration_fee",
    "fine",
    "maintenance_related",
    "cleaning",
    "other",
  ] as const),
  description: z.string().max(500).optional(),
  cost: z.coerce.number().positive("Cost must be positive"),
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, "Use YYYY-MM-DD format"),
});

type ExpenseFormValues = z.infer<typeof expenseFormSchema>;

const expenseTypesList = [
  { value: "toll", label: "Toll Fee" },
  { value: "parking", label: "Parking Charge" },
  { value: "insurance", label: "Insurance Premium" },
  { value: "registration_fee", label: "Registration / License Fee" },
  { value: "fine", label: "Fine / Challan" },
  { value: "maintenance_related", label: "Maintenance Related" },
  { value: "cleaning", label: "Vehicle Washing / Cleaning" },
  { value: "other", label: "Miscellaneous / Other" },
];

export default function Expenses() {
  const { canWrite } = useAuth();
  const queryClient = useQueryClient();
  const [showFuelModal, setShowFuelModal] = useState(false);
  const [showExpenseModal, setShowExpenseModal] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Queries
  const { data: fuelPage, isLoading: isFuelLoading } = useQuery({
    queryKey: ["fuel-logs"],
    queryFn: async () => {
      const res = await apiClient.get("/api/fuel-logs");
      return res.data;
    },
  });

  const { data: expensesPage, isLoading: isExpensesLoading } = useQuery({
    queryKey: ["expenses"],
    queryFn: async () => {
      const res = await apiClient.get("/api/expenses");
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

  const { data: tripsPage } = useQuery({
    queryKey: ["trips"],
    queryFn: async () => {
      const res = await apiClient.get("/api/trips");
      return res.data;
    },
  });

  const fuelLogs: FuelLogResponse[] = Array.isArray(fuelPage) ? fuelPage : fuelPage?.items || [];
  const expenses: ExpenseResponse[] = Array.isArray(expensesPage) ? expensesPage : expensesPage?.items || [];
  const vehicles: VehicleResponse[] = Array.isArray(vehiclesPage) ? vehiclesPage : vehiclesPage?.items || [];
  const trips: TripResponse[] = Array.isArray(tripsPage) ? tripsPage : tripsPage?.items || [];

  // Form setups
  const {
    register: registerFuel,
    handleSubmit: handleSubmitFuel,
    reset: resetFuel,
    formState: { errors: errorsFuel, isSubmitting: isSubmittingFuel },
  } = useForm<FuelLogFormValues>({
    resolver: zodResolver(fuelLogFormSchema),
    defaultValues: {
      liters: 0,
      cost: 0,
      date: new Date().toISOString().split("T")[0],
    },
  });

  const {
    register: registerExpense,
    handleSubmit: handleSubmitExpense,
    reset: resetExpense,
    formState: { errors: errorsExpense, isSubmitting: isSubmittingExpense },
  } = useForm<ExpenseFormValues>({
    resolver: zodResolver(expenseFormSchema),
    defaultValues: {
      expense_type: "toll",
      cost: 0,
      date: new Date().toISOString().split("T")[0],
      description: "",
    },
  });

  // Mutations
  const addFuelMutation = useMutation({
    mutationFn: async (data: FuelLogFormValues) => {
      const payload = {
        ...data,
        trip_id: data.trip_id ? Number(data.trip_id) : null,
        odometer_at_fill: data.odometer_at_fill ? Number(data.odometer_at_fill) : null,
      };
      const res = await apiClient.post("/api/fuel-logs", payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["fuel-logs"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-kpis"] });
      setShowFuelModal(false);
      resetFuel();
    },
    onError: (err: any) => {
      setErrorMsg(err.response?.data?.message || "Failed to log fuel refill.");
    },
  });

  const addExpenseMutation = useMutation({
    mutationFn: async (data: ExpenseFormValues) => {
      const payload = {
        ...data,
        trip_id: data.trip_id ? Number(data.trip_id) : null,
      };
      const res = await apiClient.post("/api/expenses", payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-kpis"] });
      setShowExpenseModal(false);
      resetExpense();
    },
    onError: (err: any) => {
      setErrorMsg(err.response?.data?.message || "Failed to add expense.");
    },
  });

  const onSubmitFuel = (data: FuelLogFormValues) => {
    setErrorMsg(null);
    addFuelMutation.mutate(data);
  };

  const onSubmitExpense = (data: ExpenseFormValues) => {
    setErrorMsg(null);
    addExpenseMutation.mutate(data);
  };

  // Operational cost roll-up math: Sum of fuel cost + Sum of expenses
  const fuelTotal = fuelLogs.reduce((sum, f) => sum + f.cost, 0);
  const expenseTotal = expenses.reduce((sum, e) => sum + e.cost, 0);
  const totalOperationalCost = fuelTotal + expenseTotal;

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
  };

  return (
    <>
      <PageHeader
        title="Fuel & Expenses"
        description="Everything that adds up — fuel, tolls, and linked maintenance — in one ledger."
        actions={
          canWrite("expenses") && (
            <div className="flex gap-2">
              <button
                onClick={() => {
                  setErrorMsg(null);
                  setShowFuelModal(true);
                }}
                className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 cursor-pointer"
              >
                <Plus className="h-4 w-4" /> Log Fuel
              </button>
              <button
                onClick={() => {
                  setErrorMsg(null);
                  setShowExpenseModal(true);
                }}
                className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 cursor-pointer"
              >
                <Plus className="h-4 w-4" /> Add Expense
              </button>
            </div>
          )
        }
      />

      <Card className="mb-6 p-5">
        <h2 className="mb-4 font-display text-lg text-ink">Fuel Logs</h2>
        <div className="overflow-x-auto">
          {isFuelLoading ? (
            <div className="space-y-2 py-4 animate-pulse">
              <div className="h-6 bg-muted rounded w-full" />
              <div className="h-6 bg-muted rounded w-full" />
            </div>
          ) : fuelLogs.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">No fuel logs registered yet.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                  <th className="pb-3 pr-4">Vehicle</th>
                  <th className="pb-3 pr-4">Date</th>
                  <th className="pb-3 pr-4">Liters</th>
                  <th className="pb-3 pr-4">Odometer at Fill</th>
                  <th className="pb-3 pr-4">Refill Cost</th>
                  <th className="pb-3">Trip Link</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {fuelLogs.map((f) => (
                  <tr key={f.id}>
                    <td className="py-3 pr-4 font-medium">{f.vehicle?.name || `Vehicle ID ${f.vehicle_id}`}</td>
                    <td className="py-3 pr-4 text-muted-foreground">{formatDate(f.date)}</td>
                    <td className="py-3 pr-4 tabular-nums text-muted-foreground">{f.liters} L</td>
                    <td className="py-3 pr-4 tabular-nums text-muted-foreground">
                      {f.odometer_at_fill ? `${f.odometer_at_fill.toLocaleString()} km` : "—"}
                    </td>
                    <td className="py-3 pr-4 tabular-nums font-medium">₹ {f.cost.toLocaleString()}</td>
                    <td className="py-3 text-muted-foreground text-xs font-mono">
                      {f.trip_id ? `TR00${f.trip_id}` : "Direct refill"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </Card>

      <Card className="p-5">
        <h2 className="mb-4 font-display text-lg text-ink">
          Other Expenses <span className="text-sm font-normal text-muted-foreground">· Toll / Misc</span>
        </h2>
        <div className="overflow-x-auto">
          {isExpensesLoading ? (
            <div className="space-y-2 py-4 animate-pulse">
              <div className="h-6 bg-muted rounded w-full" />
              <div className="h-6 bg-muted rounded w-full" />
            </div>
          ) : expenses.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">No other expenses logged yet.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                  <th className="pb-3 pr-4">Trip</th>
                  <th className="pb-3 pr-4">Vehicle</th>
                  <th className="pb-3 pr-4">Expense Type</th>
                  <th className="pb-3 pr-4">Description</th>
                  <th className="pb-3 pr-4">Date</th>
                  <th className="pb-3">Cost</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {expenses.map((e) => (
                  <tr key={e.id}>
                    <td className="py-3 pr-4 font-medium font-mono text-xs">
                      {e.trip_id ? `TR00${e.trip_id}` : "General"}
                    </td>
                    <td className="py-3 pr-4 text-muted-foreground">{e.vehicle?.name || `Vehicle ID ${e.vehicle_id}`}</td>
                    <td className="py-3 pr-4 capitalize text-muted-foreground">
                      {e.expense_type.replace("_", " ")}
                    </td>
                    <td className="py-3 pr-4 text-muted-foreground text-xs truncate max-w-[200px]" title={e.description || ""}>
                      {e.description || "—"}
                    </td>
                    <td className="py-3 pr-4 text-muted-foreground text-xs">{formatDate(e.date)}</td>
                    <td className="py-3 tabular-nums font-semibold">₹ {e.cost.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-primary/25 bg-primary/5 px-4 py-3">
          <span className="text-sm font-medium text-foreground">
            Total operational cost <span className="text-muted-foreground">(auto = fuel logs + other expenses)</span>
          </span>
          <span className="font-display text-2xl text-primary">₹ {totalOperationalCost.toLocaleString()}</span>
        </div>
      </Card>

      {/* Log Fuel Modal */}
      {canWrite("expenses") && showFuelModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <Card className="w-full max-w-md bg-card p-6 shadow-2xl relative">
            <button
              onClick={() => setShowFuelModal(false)}
              className="absolute right-4 top-4 text-muted-foreground hover:text-foreground cursor-pointer"
            >
              <X className="h-5 w-5" />
            </button>

            <h3 className="font-display text-xl text-ink mb-4">Log Fuel Refill</h3>

            {errorMsg && (
              <div className="mb-4 flex items-center gap-2 rounded-lg bg-status-red/10 p-3 text-sm text-status-red">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            <form onSubmit={handleSubmitFuel(onSubmitFuel)} className="space-y-4">
              <FormField label="Vehicle" error={errorsFuel.vehicle_id?.message}>
                <Select {...registerFuel("vehicle_id")}>
                  <option value="">Select vehicle</option>
                  {vehicles.filter(v => v.status !== "retired").map(v => (
                    <option key={v.id} value={v.id}>
                      {v.name} ({v.registration_number})
                    </option>
                  ))}
                </Select>
              </FormField>

              <FormField label="Link to Trip (Optional)">
                <Select {...registerFuel("trip_id")}>
                  <option value="">Direct fueling (No trip link)</option>
                  {trips.filter(t => t.status === "dispatched" || t.status === "completed").map(t => (
                    <option key={t.id} value={t.id}>
                      TR00{t.id} ({t.source} → {t.destination})
                    </option>
                  ))}
                </Select>
              </FormField>

              <div className="grid grid-cols-2 gap-4">
                <FormField label="Fuel liters" error={errorsFuel.liters?.message}>
                  <TextInput type="number" step="any" {...registerFuel("liters")} />
                </FormField>
                <FormField label="Total Cost (₹)" error={errorsFuel.cost?.message}>
                  <TextInput type="number" {...registerFuel("cost")} />
                </FormField>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <FormField label="Date" error={errorsFuel.date?.message}>
                  <TextInput type="date" {...registerFuel("date")} />
                </FormField>
                <FormField label="Odometer (Optional)">
                  <TextInput type="number" {...registerFuel("odometer_at_fill")} />
                </FormField>
              </div>

              <div className="mt-6 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowFuelModal(false)}
                  className="rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium text-foreground hover:bg-accent cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingFuel}
                  className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 disabled:opacity-50 cursor-pointer"
                >
                  {isSubmittingFuel ? "Saving..." : "Log Fuel"}
                </button>
              </div>
            </form>
          </Card>
        </div>
      )}

      {/* Add Expense Modal */}
      {canWrite("expenses") && showExpenseModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <Card className="w-full max-w-md bg-card p-6 shadow-2xl relative">
            <button
              onClick={() => setShowExpenseModal(false)}
              className="absolute right-4 top-4 text-muted-foreground hover:text-foreground cursor-pointer"
            >
              <X className="h-5 w-5" />
            </button>

            <h3 className="font-display text-xl text-ink mb-4">Add Operational Expense</h3>

            {errorMsg && (
              <div className="mb-4 flex items-center gap-2 rounded-lg bg-status-red/10 p-3 text-sm text-status-red">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                <span>{errorMsg}</span>
              </div>
            )}

            <form onSubmit={handleSubmitExpense(onSubmitExpense)} className="space-y-4">
              <FormField label="Vehicle" error={errorsExpense.vehicle_id?.message}>
                <Select {...registerExpense("vehicle_id")}>
                  <option value="">Select vehicle</option>
                  {vehicles.filter(v => v.status !== "retired").map(v => (
                    <option key={v.id} value={v.id}>
                      {v.name} ({v.registration_number})
                    </option>
                  ))}
                </Select>
              </FormField>

              <div className="grid grid-cols-2 gap-4">
                <FormField label="Expense Category" error={errorsExpense.expense_type?.message}>
                  <Select {...registerExpense("expense_type")}>
                    {expenseTypesList.map(t => (
                      <option key={t.value} value={t.value}>
                        {t.label}
                      </option>
                    ))}
                  </Select>
                </FormField>
                <FormField label="Link to Trip (Optional)">
                  <Select {...registerExpense("trip_id")}>
                    <option value="">General Expense (No trip link)</option>
                    {trips.map(t => (
                      <option key={t.id} value={t.id}>
                        TR00{t.id} ({t.source} → {t.destination})
                      </option>
                    ))}
                  </Select>
                </FormField>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <FormField label="Cost (₹)" error={errorsExpense.cost?.message}>
                  <TextInput type="number" {...registerExpense("cost")} />
                </FormField>
                <FormField label="Date" error={errorsExpense.date?.message}>
                  <TextInput type="date" {...registerExpense("date")} />
                </FormField>
              </div>

              <FormField label="Description" error={errorsExpense.description?.message}>
                <TextInput placeholder="e.g. NH-48 Toll charges, parking fee, insurance pay" {...registerExpense("description")} />
              </FormField>

              <div className="mt-6 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowExpenseModal(false)}
                  className="rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium text-foreground hover:bg-accent cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingExpense}
                  className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 disabled:opacity-50 cursor-pointer"
                >
                  {isSubmittingExpense ? "Adding..." : "Add Expense"}
                </button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </>
  );
}
