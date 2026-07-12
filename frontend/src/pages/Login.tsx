import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Check, AlertCircle } from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { Role } from "../types";

const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(1, "Password is required"),
  role: z.enum(["fleet_manager", "driver", "safety_officer", "financial_analyst"] as const),
});

type LoginFormValues = z.infer<typeof loginSchema>;

const rolesList = [
  { value: "fleet_manager", label: "Fleet Manager" },
  { value: "driver", label: "Dispatcher" },
  { value: "safety_officer", label: "Safety Officer" },
  { value: "financial_analyst", label: "Financial Analyst" },
];

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
      role: "fleet_manager",
    },
  });

  const selectedRole = watch("role");

  // Sync email default values based on role just for usability
  const handleRoleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const role = e.target.value as Role;
    setValue("role", role);
    if (role === "fleet_manager") {
      setValue("email", "raven.k@transitops.in");
    } else if (role === "driver") {
      setValue("email", "driver.alex@transitops.in");
    } else if (role === "safety_officer") {
      setValue("email", "safety.officer@transitops.in");
    } else if (role === "financial_analyst") {
      setValue("email", "financial.analyst@transitops.in");
    }
  };

  const onSubmit = async (data: LoginFormValues) => {
    setError(null);
    try {
      await login(data.email, data.password, data.role);
      navigate("/dashboard");
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Invalid credentials or login failed.";
      setError(errorMessage);
    }
  };

  return (
    <div className="grid min-h-screen grid-cols-1 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
      {/* Left: dark brand panel */}
      <div className="relative hidden flex-col justify-between bg-[oklch(0.19_0.015_260)] p-10 text-white lg:flex">
        <div>
          <div className="flex items-center gap-3">
            {/* <div className="grid h-10 w-10 place-items-center rounded-md bg-primary text-primary-foreground shadow-sm">
              <span className="font-display text-base font-semibold">T</span>
            </div> */}
            <div>
              <div className="font-display text-2xl">TransitOps</div>
              <div className="text-xs text-white/60">Smart Transport Operations Platform</div>
            </div>
          </div>
          <div className="mt-16">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-white/50">One login, four roles</p>
            <ul className="mt-4 space-y-2.5">
              {rolesList.map(r => (
                <li key={r.value} className="flex items-center gap-2.5 text-sm text-white/85">
                  <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                  {r.label}
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div className="text-[11px] uppercase tracking-[0.18em] text-white/40">
          TransitOps © 2026 · RBAC enabled
        </div>
      </div>

      {/* Right: form */}
      <div className="flex items-center justify-center px-6 py-12 sm:px-10">
        <div className="w-full max-w-md">
          <h1 className="font-display text-3xl text-ink">Sign in to your account</h1>
          <p className="mt-2 text-sm text-muted-foreground">Enter your credentials to continue</p>

          {error && (
            <div className="mt-4 flex items-center gap-2 rounded-lg bg-status-red/10 p-3 text-sm text-status-red">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form className="mt-8 space-y-4" onSubmit={handleSubmit(onSubmit)}>
            <div>
              <label className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Email</label>
              <input
                type="email"
                {...register("email")}
                className="w-full rounded-lg border border-border bg-card px-3.5 py-2.5 text-sm focus:border-primary/60 focus:outline-none focus:ring-2 focus:ring-primary/20 transition"
              />
              {errors.email && (
                <span className="mt-1 block text-xs text-status-red font-medium">{errors.email.message}</span>
              )}
            </div>
            <div>
              <label className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Password</label>
              <input
                type="password"
                {...register("password")}
                className="w-full rounded-lg border border-border bg-card px-3.5 py-2.5 text-sm focus:border-primary/60 focus:outline-none focus:ring-2 focus:ring-primary/20 transition"
              />
              {errors.password && (
                <span className="mt-1 block text-xs text-status-red font-medium">{errors.password.message}</span>
              )}
            </div>
            <div>
              <label className="mb-1.5 block text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">Role (RBAC)</label>
              <select
                value={selectedRole}
                onChange={handleRoleChange}
                className="w-full rounded-lg border border-border bg-card px-3.5 py-2.5 text-sm focus:border-primary/60 focus:outline-none focus:ring-2 focus:ring-primary/20 transition"
              >
                {rolesList.map(r => (
                  <option key={r.value} value={r.value}>
                    {r.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center gap-2 text-sm text-foreground">
                <span className="grid h-4 w-4 place-items-center rounded border border-primary bg-primary text-primary-foreground">
                  <Check className="h-3 w-3" />
                </span>
                Remember me
              </label>
              <a href="#" className="text-sm font-medium text-primary hover:underline">Forgot password?</a>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="mt-2 flex w-full items-center justify-center rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground shadow-sm transition hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? "Signing In..." : "Sign In"}
            </button>
          </form>

          <div className="mt-8 rounded-xl border border-border bg-paper p-4 text-xs text-muted-foreground">
            <p className="mb-2 font-semibold text-foreground">Access is scoped by role after login</p>
            <ul className="space-y-1">
              <li>• Fleet Manager → Fleet, Maintenance, Trips, Expenses, Analytics</li>
              <li>• Dispatcher → Dashboard, Trips, Fleet (view)</li>
              <li>• Safety Officer → Drivers, Compliance, Trips (view)</li>
              <li>• Financial Analyst → Fuel &amp; Expenses, Analytics, Fleet (view)</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
