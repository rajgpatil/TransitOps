import React from "react";
import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { AppShell } from "./components/AppShell";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Fleet from "./pages/Fleet";
import Drivers from "./pages/Drivers";
import Trips from "./pages/Trips";
import Maintenance from "./pages/Maintenance";
import Expenses from "./pages/Expenses";
import Analytics from "./pages/Analytics";
import Settings from "./pages/Settings";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function ProtectedLayout() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background text-sm text-muted-foreground font-medium">
        Loading session...
      </div>
    );
  }

  // if (!isAuthenticated) {
  //   return <Navigate to="/login" replace />;
  // }

  return (
    <AppShell>
      <Outlet />
    </AppShell>
  );
}

function RouteGuard({
  module,
  children,
}: {
  module: "fleet" | "drivers" | "trips" | "expenses" | "analytics";
  children: React.ReactElement;
}) {
  // const { canAccess } = useAuth();
  // if (!canAccess(module)) {
  //   return <Navigate to="/dashboard" replace />;
  // }
  return children;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />

            {/* Authenticated Application routes */}
            <Route element={<ProtectedLayout />}>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />

              <Route
                path="/fleet"
                element={
                  <RouteGuard module="fleet">
                    <Fleet />
                  </RouteGuard>
                }
              />
              <Route
                path="/drivers"
                element={
                  <RouteGuard module="drivers">
                    <Drivers />
                  </RouteGuard>
                }
              />
              <Route
                path="/trips"
                element={
                  <RouteGuard module="trips">
                    <Trips />
                  </RouteGuard>
                }
              />
              <Route
                path="/maintenance"
                element={
                  <RouteGuard module="fleet">
                    <Maintenance />
                  </RouteGuard>
                }
              />
              <Route
                path="/expenses"
                element={
                  <RouteGuard module="expenses">
                    <Expenses />
                  </RouteGuard>
                }
              />
              <Route
                path="/analytics"
                element={
                  <RouteGuard module="analytics">
                    <Analytics />
                  </RouteGuard>
                }
              />
              <Route path="/settings" element={<Settings />} />
            </Route>

            {/* Catch-all redirect */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
