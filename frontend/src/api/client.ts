import axios from "axios";
import { db } from "./mockData";

export const apiClient = axios.create({
  baseURL: "",
  headers: {
    "Content-Type": "application/json",
  },
});

// Attach auth token if exists
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Intercept 404s and fallback to mock data
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Check if error is indeed a 404 response
    if (error.response && error.response.status === 404) {
      const url = new URL(originalRequest.url, window.location.origin);
      const pathname = url.pathname;
      const method = originalRequest.method?.toUpperCase();
      const params = Object.fromEntries(url.searchParams.entries());
      const body = originalRequest.data ? JSON.parse(originalRequest.data) : undefined;

      console.warn(`[API Client] Endpoint ${method} ${pathname} returned 404. Falling back to local mock data.`, { params, body });

      try {
        const mockResponse = handleMockRequest(method || "GET", pathname, params, body);
        if (mockResponse !== undefined) {
          return {
            data: mockResponse,
            status: 200,
            statusText: "OK",
            headers: originalRequest.headers,
            config: originalRequest,
          };
        }
      } catch (err) {
        console.error("[API Client] Error handling mock fallback:", err);
      }
    }

    return Promise.reject(error);
  }
);

function handleMockRequest(method: string, pathname: string, params: Record<string, string>, body: any): any {
  // 1. Auth endpoints
  if (pathname.includes("/api/auth/me")) {
    const role = localStorage.getItem("userRole") || "fleet_manager";
    const user = db.users.find(u => u.role === role) || db.users[0];
    return user;
  }
  
  if (pathname.includes("/api/auth/login")) {
    const role = body?.role || "fleet_manager";
    const email = body?.email || `${role}@transitops.in`;
    const user = db.users.find(u => u.role === role) || db.users[0];
    localStorage.setItem("userRole", role);
    localStorage.setItem("token", "mock-jwt-token");
    return {
      access_token: "mock-jwt-token",
      refresh_token: "mock-refresh-token",
      token_type: "bearer",
      expires_in: 3600,
      user,
    };
  }

  // 2. Dashboard KPI and Charts
  if (pathname.includes("/api/dashboard/kpis")) {
    return db.getDashboardKPIs();
  }

  if (pathname.includes("/api/dashboard/charts")) {
    return db.getDashboardCharts();
  }

  // 3. Vehicles
  if (pathname.match(/\/api\/vehicles\/\d+$/)) {
    const id = Number(pathname.split("/").pop());
    if (method === "PUT" || method === "PATCH") {
      return db.updateVehicle(id, body) || { error: "Not found" };
    }
    if (method === "DELETE") {
      return db.deleteVehicle(id) || { error: "Not found" };
    }
    return db.vehicles.find(v => v.id === id) || { error: "Not found" };
  }

  if (pathname.includes("/api/vehicles")) {
    if (method === "POST") {
      return db.createVehicle(body);
    }
    const type = params.type || "All";
    const status = params.status || "All";
    const search = params.search || "";
    const list = db.getVehicles({ type, status, search });
    
    // Check if pagination is explicitly requested
    const page = params.page ? Number(params.page) : 1;
    const pageSize = params.page_size ? Number(params.page_size) : 20;
    return db.paginate(list, page, pageSize);
  }

  // 4. Drivers
  if (pathname.match(/\/api\/drivers\/\d+$/)) {
    const id = Number(pathname.split("/").pop());
    if (method === "PUT" || method === "PATCH") {
      return db.updateDriver(id, body) || { error: "Not found" };
    }
    if (method === "DELETE") {
      return db.deleteDriver(id) || { error: "Not found" };
    }
    return db.drivers.find(d => d.id === id) || { error: "Not found" };
  }

  if (pathname.includes("/api/drivers")) {
    if (method === "POST") {
      return db.createDriver(body);
    }
    const status = params.status || "All";
    const search = params.search || "";
    const list = db.getDrivers({ status, search });
    
    const page = params.page ? Number(params.page) : 1;
    const pageSize = params.page_size ? Number(params.page_size) : 20;
    return db.paginate(list, page, pageSize);
  }

  // 5. Trips
  if (pathname.match(/\/api\/trips\/\d+\/complete$/)) {
    const id = Number(pathname.split("/")[3]);
    return db.completeTrip(id, body) || { error: "Not found" };
  }

  if (pathname.match(/\/api\/trips\/\d+\/cancel$/)) {
    const id = Number(pathname.split("/")[3]);
    return db.cancelTrip(id, body) || { error: "Not found" };
  }

  if (pathname.match(/\/api\/trips\/\d+\/dispatch$/)) {
    const id = Number(pathname.split("/")[3]);
    return db.dispatchTrip(id) || { error: "Not found" };
  }

  if (pathname.match(/\/api\/trips\/\d+$/)) {
    const id = Number(pathname.split("/").pop());
    if (method === "PUT" || method === "PATCH") {
      return db.trips.find(t => t.id === id) || { error: "Not found" }; // simple fallback
    }
    return db.trips.map(t => ({
      ...t,
      vehicle: db.vehicles.find(v => v.id === t.vehicle_id),
      driver: db.drivers.find(d => d.id === t.driver_id),
    })).find(t => t.id === id) || { error: "Not found" };
  }

  if (pathname.includes("/api/trips")) {
    if (method === "POST") {
      return db.createTrip(body);
    }
    const status = params.status || "All";
    const list = db.getTrips({ status });

    const page = params.page ? Number(params.page) : 1;
    const pageSize = params.page_size ? Number(params.page_size) : 20;
    return db.paginate(list, page, pageSize);
  }

  // 6. Maintenance Logs
  if (pathname.match(/\/api\/maintenance\/\d+\/close$/)) {
    const id = Number(pathname.split("/")[3]);
    return db.closeMaintenanceLog(id, body) || { error: "Not found" };
  }

  if (pathname.match(/\/api\/maintenance\/\d+$/)) {
    const id = Number(pathname.split("/").pop());
    return db.maintenanceLogs.find(m => m.id === id) || { error: "Not found" };
  }

  if (pathname.includes("/api/maintenance")) {
    if (method === "POST") {
      return db.createMaintenanceLog(body);
    }
    const list = db.getMaintenanceLogs();

    const page = params.page ? Number(params.page) : 1;
    const pageSize = params.page_size ? Number(params.page_size) : 20;
    return db.paginate(list, page, pageSize);
  }

  // 7. Fuel Logs
  if (pathname.includes("/api/fuel-logs")) {
    if (method === "POST") {
      return db.createFuelLog(body);
    }
    const list = db.getFuelLogs();
    
    const page = params.page ? Number(params.page) : 1;
    const pageSize = params.page_size ? Number(params.page_size) : 20;
    return db.paginate(list, page, pageSize);
  }

  // 8. Expenses
  if (pathname.includes("/api/expenses")) {
    if (method === "POST") {
      return db.createExpense(body);
    }
    const list = db.getExpenses();
    
    const page = params.page ? Number(params.page) : 1;
    const pageSize = params.page_size ? Number(params.page_size) : 20;
    return db.paginate(list, page, pageSize);
  }

  // Generic fallback if not matched
  return null;
}
