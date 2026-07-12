import React, { createContext, useContext, useState, useEffect } from "react";
import { UserResponse, Role } from "../types";
import { apiClient } from "../api/client";

interface AuthContextType {
  user: UserResponse | null;
  role: Role | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string, role: Role) => Promise<void>;
  logout: () => void;
  canAccess: (module: "fleet" | "drivers" | "trips" | "expenses" | "analytics" | "maintenance") => boolean;
  canWrite: (module: "fleet" | "drivers" | "trips" | "expenses" | "analytics" | "maintenance") => boolean;
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
    const handleLogoutEvent = () => {
      logout();
    };

    window.addEventListener("auth-logout", handleLogoutEvent);

    const token = localStorage.getItem("token");
    if (token) {
      fetchCurrentUser();
    } else {
      setIsLoading(false);
    }

    return () => {
      window.removeEventListener("auth-logout", handleLogoutEvent);
    };
  }, []);

  const login = async (email: string, password: string, selectedRole: Role) => {
    setIsLoading(true);
    try {
      const response = await apiClient.post<any>("/api/auth/login", {
        email,
        password,
      });

      const token = response.data.access_token;
      const refreshToken = response.data.refresh_token;

      if (token) {
        localStorage.setItem("token", token);
        localStorage.setItem("userRole", selectedRole);
      }
      if (refreshToken) {
        localStorage.setItem("refresh_token", refreshToken);
      }

      let userResponse = null;
      if (token) {
        const meResponse = await apiClient.get<UserResponse>("/api/auth/me");
        userResponse = meResponse.data;
      }

      if (!userResponse) {
        throw new Error("Could not retrieve user details.");
      }

      if (userResponse.role !== selectedRole) {
        localStorage.removeItem("token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("userRole");
        throw new Error(
          `Access denied: Your account is registered as a ${userResponse.role.replace(
            "_",
            " "
          )}, not a ${selectedRole.replace("_", " ")}.`
        );
      }

      setUser(userResponse);
    } catch (err) {
      console.error("Login failed:", err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("userRole");
    setUser(null);
  };

  // RBAC checks based on the Settings & RBAC matrix (aligned with backend PERMISSION_MATRIX)
  const canAccess = (module: "fleet" | "drivers" | "trips" | "expenses" | "analytics" | "maintenance"): boolean => {
    if (!role) return false;
    if (role === "fleet_manager") return true;

    switch (module) {
      case "fleet":
        // vehicles read: all roles
        return true;
      case "drivers":
        // drivers read: all roles
        return true;
      case "trips":
        // trips read: all roles
        return true;
      case "maintenance":
        // maintenance read: fleet_manager, safety_officer, financial_analyst
        return role === "safety_officer" || role === "financial_analyst";
      case "expenses":
        // expenses/fuel logs read: all roles
        return true;
      case "analytics":
        // reports read: fleet_manager, financial_analyst
        return role === "financial_analyst";
      default:
        return false;
    }
  };

  const canWrite = (module: "fleet" | "drivers" | "trips" | "expenses" | "analytics" | "maintenance"): boolean => {
    if (!role) return false;

    switch (module) {
      case "fleet":
        // vehicles write: fleet_manager
        return role === "fleet_manager";
      case "drivers":
        // drivers write: safety_officer, fleet_manager
        return role === "safety_officer" || role === "fleet_manager";
      case "trips":
        // trips write: driver (only driver is assigned write permission on trips in backend)
        return role === "driver";
      case "maintenance":
        // maintenance write: fleet_manager
        return role === "fleet_manager";
      case "expenses":
        // expenses/fuel logs write: financial_analyst, driver, fleet_manager
        return role === "financial_analyst" || role === "driver" || role === "fleet_manager";
      case "analytics":
        return false;
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

