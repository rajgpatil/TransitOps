import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  Search,
  LayoutDashboard,
  Truck,
  Users,
  Route as RouteIcon,
  Wrench,
  Fuel,
  BarChart3,
  Settings,
  LogOut,
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, module: null },
  { to: "/fleet", label: "Fleet", icon: Truck, module: "fleet" },
  { to: "/drivers", label: "Drivers", icon: Users, module: "drivers" },
  { to: "/trips", label: "Trips", icon: RouteIcon, module: "trips" },
  { to: "/maintenance", label: "Maintenance", icon: Wrench, module: "fleet" }, // Maintenance checks fleet access
  { to: "/expenses", label: "Fuel & Expenses", icon: Fuel, module: "expenses" },
  { to: "/analytics", label: "Analytics", icon: BarChart3, module: "analytics" },
  { to: "/settings", label: "Settings", icon: Settings, module: null },
] as const;

function Brand() {
  return (
    <div className="flex items-center gap-2.5 px-2">
      {/* <div className="grid h-8 w-8 place-items-center rounded-md bg-primary text-primary-foreground shadow-sm">
        <span className="font-display text-sm font-semibold">T</span> */}
      {/* </div> */}
      <span className="font-display text-2xl text-ink">TransitOps</span>
    </div>
  );
}

function Sidebar() {
  const location = useLocation();
  const { canAccess } = useAuth();
  
  return (
    <aside className="hidden w-60 shrink-0 flex-col border-r border-border bg-paper md:flex">
      <div className="flex h-16 items-center border-b border-border px-4">
        <Brand />
      </div>
      <nav className="flex-1 space-y-0.5 p-3">
        {navItems.map(item => {
          // If RBAC blocks access, don't show the link (except for settings and dashboard)
          // if (item.module && !canAccess(item.module as any)) {
          //   return null;
          // }
          const Icon = item.icon;
          const active = location.pathname.startsWith(item.to);
          return (
            <Link
              key={item.to}
              to={item.to}
              className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                active
                  ? "bg-primary/10 text-primary ring-1 ring-primary/20"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground"
              }`}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span className="truncate">{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-border p-4 text-[11px] text-muted-foreground">
        TransitOps · 2026
      </div>
    </aside>
  );
}

const roleLabels: Record<string, string> = {
  fleet_manager: "Fleet Manager",
  driver: "Driver / Dispatcher",
  safety_officer: "Safety Officer",
  financial_analyst: "Financial Analyst",
};

function Topbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [showDropdown, setShowDropdown] = useState(false);

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map(p => p[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-4 border-b border-border bg-background/80 px-4 py-3 backdrop-blur sm:px-6 relative z-10">
      <div className="relative min-w-0 max-w-md">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search vehicles, trips, drivers…"
          className="w-full rounded-lg border border-border bg-card py-2 pl-9 pr-3 text-sm placeholder:text-muted-foreground/70 focus:border-primary/60 focus:outline-none focus:ring-2 focus:ring-primary/20"
        />
      </div>
      <div className="flex shrink-0 items-center gap-3 relative">
        <div className="text-right hidden sm:block">
          <div className="text-sm font-medium text-foreground">{user?.full_name || "Guest User"}</div>
          <div className="text-xs text-muted-foreground">{roleLabels[user?.role || ""] || "User"}</div>
        </div>
        <button
          onClick={() => setShowDropdown(!showDropdown)}
          className="grid h-9 w-9 place-items-center rounded-full bg-[oklch(0.58_0.14_40)] text-xs font-semibold text-white cursor-pointer hover:opacity-90"
        >
          {user ? getInitials(user.full_name) : "GU"}
        </button>

        {showDropdown && (
          <div className="absolute right-0 top-11 w-48 rounded-lg border border-border bg-card p-1 shadow-lg ring-1 ring-black/5">
            <div className="px-3 py-2 border-b border-border sm:hidden">
              <div className="text-sm font-medium text-foreground">{user?.full_name}</div>
              <div className="text-xs text-muted-foreground">{roleLabels[user?.role || ""]}</div>
            </div>
            <button
              onClick={handleLogout}
              className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm text-status-red hover:bg-status-red/10 cursor-pointer"
            >
              <LogOut className="h-4 w-4" />
              <span>Sign out</span>
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

function MobileNav() {
  const location = useLocation();
  const { canAccess } = useAuth();
  
  return (
    <div className="border-b border-border bg-paper md:hidden">
      <div className="flex h-14 items-center justify-between px-4">
        <Brand />
      </div>
      <div className="flex gap-1 overflow-x-auto px-3 pb-2">
        {navItems.map(item => {
          // if (item.module && !canAccess(item.module as any)) {
          //   return null;
          // }
          const active = location.pathname.startsWith(item.to);
          return (
            <Link
              key={item.to}
              to={item.to}
              className={`shrink-0 rounded-full px-3 py-1.5 text-xs font-medium ${
                active ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-accent"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </div>
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen w-full bg-background">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <MobileNav />
        <Topbar />
        <main className="flex-1 px-4 py-6 sm:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
}) {
  return (
    <div className="mb-6 grid grid-cols-[minmax(0,1fr)_auto] items-end gap-4">
      <div className="min-w-0">
        <h1 className="font-display text-2xl text-ink sm:text-3xl">{title}</h1>
        {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
      </div>
      {actions && <div className="shrink-0">{actions}</div>}
    </div>
  );
}
