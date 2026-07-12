import React, { createContext, useContext, useState, useEffect } from "react";
import { UserResponse, Role } from "../types";
import { apiClient } from "../api/client";

interface AuthContextType {
  user: UserResponse | null;
  role: Role | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (role: Role) => Promise<void>;
  logout: () => void;
  canAccess: (module: "fleet" | "drivers" | "trips" | "expenses" | "analytics") => boolean;
  canWrite: (module: "fleet" | "drivers" | "trips" | "expenses" | "analytics") => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const role = user?.role || null;
  const isAuthenticated = !!user;

  const fetchCurrentUser = async () => {
    try {
      const response = await apiClient.get<UserResponse>("/api/auth/me");
      setUser(response.data);
    } catch (err) {
      console.error("Failed to load user:", err);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      fetchCurrentUser();
    } else {
      setIsLoading(false);
    }
  }, []);

  const login = async (selectedRole: Role) => {
    setIsLoading(true);
    try {
      const response = await apiClient.post<{ user: UserResponse }>("/api/auth/login", { role: selectedRole });
      setUser(response.data.user);
    } catch (err) {
      console.error("Login failed:", err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("userRole");
    setUser(null);
  };

  // RBAC checks based on the Settings & RBAC matrix
  const canAccess = (module: "fleet" | "drivers" | "trips" | "expenses" | "analytics"): boolean => {
    if (!role) return false;
    if (role === "fleet_manager") return true;

    switch (module) {
      case "fleet":
        return role === "financial_analyst" || role === "driver"; // view only
      case "drivers":
        return role === "safety_officer"; // full check
      case "trips":
        return role === "driver" || role === "safety_officer"; // driver has full, safety has view
      case "expenses":
        return role === "financial_analyst"; // full check
      case "analytics":
        return role === "financial_analyst"; // full check
      default:
        return false;
    }
  };

  const canWrite = (module: "fleet" | "drivers" | "trips" | "expenses" | "analytics"): boolean => {
    if (!role) return false;
    if (role === "fleet_manager") return true;

    switch (module) {
      case "drivers":
        return role === "safety_officer";
      case "trips":
        return role === "driver";
      case "expenses":
        return role === "financial_analyst";
      case "fleet":
      case "analytics":
        return false; // only fleet manager can write fleet / analytics
      default:
        return false;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        role,
        isAuthenticated,
        isLoading,
        login,
        logout,
        canAccess,
        canWrite,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
