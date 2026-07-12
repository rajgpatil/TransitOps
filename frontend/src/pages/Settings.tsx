import React, { useState } from "react";
import { Check, Minus, Eye, CheckCircle } from "lucide-react";
import { PageHeader } from "../components/AppShell";
import { Card } from "../components/SectionHeader";
import { FormField, TextInput, Select } from "../components/FormField";
import { useAuth } from "../contexts/AuthContext";

type Cell = "check" | "view" | "dash";

interface MatrixRow {
  role: string;
  cells: Cell[];
}

const matrix: MatrixRow[] = [
  { role: "Fleet Manager", cells: ["check", "check", "check", "check", "check", "check"] },
  { role: "Dispatcher (Driver)", cells: ["view", "view", "check", "dash", "check", "dash"] },
  { role: "Safety Officer", cells: ["view", "check", "view", "view", "view", "dash"] },
  { role: "Financial Analyst", cells: ["view", "view", "view", "view", "check", "view"] },
];

const cols = ["Fleet", "Drivers", "Trips", "Maintenance", "Fuel/Exp.", "Analytics"];

function CellIcon({ v }: { v: Cell }) {
  if (v === "check") return <Check className="h-4 w-4 text-status-green" />;
  if (v === "view") return <Eye className="h-4 w-4 text-status-blue" />;
  return <Minus className="h-4 w-4 text-muted-foreground/60" />;
}

export default function Settings() {
  const { user, canWrite } = useAuth();
  const [depotName, setDepotName] = useState("Gandhinagar Depot GJ4");
  const [currency, setCurrency] = useState("INR");
  const [distanceUnit, setDistanceUnit] = useState("Kilometers");
  const [showSavedToast, setShowSavedToast] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setShowSavedToast(true);
    setTimeout(() => {
      setShowSavedToast(false);
    }, 3000);
  };

  return (
    <>
      <PageHeader title="Settings & RBAC" description="Depot defaults and who gets to see or change what." />

      {showSavedToast && (
        <div className="mb-4 flex items-center gap-2 rounded-lg bg-status-green/10 p-3 text-sm text-status-green animate-fade-in">
          <CheckCircle className="h-4 w-4 shrink-0" />
          <span>Depot settings successfully updated.</span>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.4fr)]">
        <Card className="p-6 h-fit">
          <h2 className="font-display text-lg text-ink">General Defaults</h2>
          <form onSubmit={handleSave} className="mt-4 space-y-4">
            <FormField label="Depot Name">
              <TextInput value={depotName} onChange={(e) => setDepotName(e.target.value)} />
            </FormField>
            <FormField label="Currency">
              <Select value={currency} onChange={(e) => setCurrency(e.target.value)}>
                <option value="INR">INR (₹)</option>
                <option value="USD">USD ($)</option>
                <option value="EUR">EUR (€)</option>
              </Select>
            </FormField>
            <FormField label="Distance Unit">
              <Select value={distanceUnit} onChange={(e) => setDistanceUnit(e.target.value)}>
                <option value="Kilometers">Kilometers</option>
                <option value="Miles">Miles</option>
              </Select>
            </FormField>
            {canWrite("fleet") && (
              <button
                type="submit"
                className="mt-6 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 cursor-pointer transition"
              >
                Save changes
              </button>
            )}
          </form>
        </Card>

        <Card className="p-6">
          <h2 className="font-display text-lg text-ink">Role-Based Access Control (RBAC)</h2>
          <p className="text-xs text-muted-foreground mt-1 mb-4">
            Current session is loaded under: <span className="font-semibold text-foreground capitalize">{user?.role.replace("_", " ")}</span>
          </p>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                  <th className="pb-3 pr-4">Role</th>
                  {cols.map((c) => (
                    <th key={c} className="pb-3 pr-4 text-center">
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {matrix.map((row) => (
                  <tr key={row.role}>
                    <td className="py-3 pr-4 font-medium">{row.role}</td>
                    {row.cells.map((c, i) => (
                      <td key={i} className="py-3 pr-4">
                        <div className="flex items-center justify-center">
                          {c === "view" ? (
                            <span className="inline-flex items-center gap-1 rounded-full bg-status-blue/10 px-2 py-0.5 text-[11px] font-medium text-status-blue">
                              view
                            </span>
                          ) : (
                            <CellIcon v={c} />
                          )}
                        </div>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-6 flex flex-wrap items-center gap-4 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-1.5 font-medium">
              <Check className="h-3.5 w-3.5 text-status-green" /> Full Access
            </span>
            <span className="inline-flex items-center gap-1.5 font-medium">
              <Eye className="h-3.5 w-3.5 text-status-blue" /> View Only
            </span>
            <span className="inline-flex items-center gap-1.5 font-medium">
              <Minus className="h-3.5 w-3.5" /> No Access
            </span>
          </div>
        </Card>
      </div>
    </>
  );
}
