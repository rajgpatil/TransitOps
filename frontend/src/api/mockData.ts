import {
  VehicleResponse,
  DriverResponse,
  TripResponse,
  MaintenanceLogResponse,
  FuelLogResponse,
  ExpenseResponse,
  UserResponse,
} from "../types";

// In-memory mock database state
export const mockUsers: UserResponse[] = [
  {
    id: 1,
    email: "raven.k@transitops.in",
    full_name: "Raven K.",
    role: "fleet_manager",
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 2,
    email: "driver.alex@transitops.in",
    full_name: "Alex",
    role: "driver",
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 3,
    email: "safety.officer@transitops.in",
    full_name: "Officer Suresh",
    role: "safety_officer",
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 4,
    email: "financial.analyst@transitops.in",
    full_name: "Analyst Priya",
    role: "financial_analyst",
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

export const mockVehicles: VehicleResponse[] = [
  {
    id: 1,
    registration_number: "GJ01AB4521",
    name: "VAN-05",
    type: "van",
    max_load_capacity: 500,
    odometer: 74000,
    acquisition_cost: 620000,
    region: "Gandhinagar",
    status: "available",
    active_maintenance_count: 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 2,
    registration_number: "GJ01AB9981",
    name: "TRUCK-11",
    type: "truck",
    max_load_capacity: 5000,
    odometer: 182000,
    acquisition_cost: 2450000,
    region: "Ahmedabad",
    status: "on_trip",
    active_maintenance_count: 0,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 3,
    registration_number: "GJ01AB1120",
    name: "MINI-03",
    type: "pickup",
    max_load_capacity: 1000,
    odometer: 66000,
    acquisition_cost: 410000,
    region: "Sanand",
    status: "in_shop",
    active_maintenance_count: 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 4,
    registration_number: "GJ01AB0087",
    name: "VAN-09",
    type: "van",
    max_load_capacity: 750,
    odometer: 241900,
    acquisition_cost: 590000,
    region: "Gandhinagar",
    status: "retired",
    active_maintenance_count: 0,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

export const mockDrivers: DriverResponse[] = [
  {
    id: 1,
    name: "Alex",
    license_number: "DL-88213",
    license_category: "B",
    license_expiry: "2028-12-31",
    contact_number: "9876543210",
    safety_score: 96,
    status: "available",
    is_license_expired: false,
    is_assignable: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 2,
    name: "John",
    license_number: "DL-44120",
    license_category: "C",
    license_expiry: "2025-03-15", // Expired
    contact_number: "9822011220",
    safety_score: 81,
    status: "suspended",
    is_license_expired: true,
    is_assignable: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 3,
    name: "Priya",
    license_number: "DL-77031",
    license_category: "B",
    license_expiry: "2027-08-15",
    contact_number: "9911022330",
    safety_score: 99,
    status: "on_trip",
    is_license_expired: false,
    is_assignable: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 4,
    name: "Suresh",
    license_number: "DL-90045",
    license_category: "CE",
    license_expiry: "2027-01-15",
    contact_number: "9744099880",
    safety_score: 88,
    status: "off_duty",
    is_license_expired: false,
    is_assignable: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

export const mockTrips: TripResponse[] = [
  {
    id: 1,
    source: "Gandhinagar Depot",
    destination: "Ahmedabad Hub",
    vehicle_id: 1,
    driver_id: 1,
    cargo_weight: 400,
    planned_distance: 38,
    actual_distance: null,
    fuel_consumed: null,
    final_odometer: null,
    revenue: 5000,
    status: "dispatched",
    dispatched_at: new Date(Date.now() - 30 * 60000).toISOString(),
    completed_at: null,
    cancelled_at: null,
    cancel_reason: null,
    created_at: new Date(Date.now() - 60 * 60000).toISOString(),
    updated_at: new Date(Date.now() - 30 * 60000).toISOString(),
  },
  {
    id: 2,
    source: "Vatva Industrial Area",
    destination: "Sanand Warehouse",
    vehicle_id: 2,
    driver_id: 3,
    cargo_weight: 4800,
    planned_distance: 52,
    actual_distance: 52,
    fuel_consumed: 15,
    final_odometer: 182000,
    revenue: 12000,
    status: "completed",
    dispatched_at: new Date(Date.now() - 4 * 3600000).toISOString(),
    completed_at: new Date(Date.now() - 2 * 3600000).toISOString(),
    cancelled_at: null,
    cancel_reason: null,
    created_at: new Date(Date.now() - 5 * 3600000).toISOString(),
    updated_at: new Date(Date.now() - 2 * 3600000).toISOString(),
  },
  {
    id: 3,
    source: "Mansa",
    destination: "Kalol Depot",
    vehicle_id: 3,
    driver_id: 4,
    cargo_weight: 800,
    planned_distance: 25,
    actual_distance: null,
    fuel_consumed: null,
    final_odometer: null,
    revenue: 3500,
    status: "cancelled",
    dispatched_at: null,
    completed_at: null,
    cancelled_at: new Date().toISOString(),
    cancel_reason: "Vehicle went to shop",
    created_at: new Date(Date.now() - 12 * 3600000).toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 4,
    source: "Ahmedabad Depot",
    destination: "Baroda Hub",
    vehicle_id: 1,
    driver_id: 1,
    cargo_weight: 450,
    planned_distance: 120,
    actual_distance: null,
    fuel_consumed: null,
    final_odometer: null,
    revenue: 9000,
    status: "draft",
    dispatched_at: null,
    completed_at: null,
    cancelled_at: null,
    cancel_reason: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

export const mockMaintenanceLogs: MaintenanceLogResponse[] = [
  {
    id: 1,
    vehicle_id: 1,
    maintenance_type: "oil_change",
    description: "Oil Change — 10W-40",
    cost: 2500,
    status: "active",
    started_at: new Date(Date.now() - 24 * 3600000).toISOString(),
    closed_at: null,
    notes: null,
    created_at: new Date(Date.now() - 24 * 3600000).toISOString(),
    updated_at: new Date(Date.now() - 24 * 3600000).toISOString(),
  },
  {
    id: 2,
    vehicle_id: 2,
    maintenance_type: "engine_repair",
    description: "Engine overheating check and radiator repair",
    cost: 18000,
    status: "closed",
    started_at: new Date(Date.now() - 10 * 24 * 3600000).toISOString(),
    closed_at: new Date(Date.now() - 9 * 24 * 3600000).toISOString(),
    notes: "Radiator replaced. Test run OK.",
    created_at: new Date(Date.now() - 10 * 24 * 3600000).toISOString(),
    updated_at: new Date(Date.now() - 9 * 24 * 3600000).toISOString(),
  },
  {
    id: 3,
    vehicle_id: 3,
    maintenance_type: "tire_replacement",
    description: "Tyre Replace — Front two tires",
    cost: 6200,
    status: "active",
    started_at: new Date(Date.now() - 12 * 3600000).toISOString(),
    closed_at: null,
    notes: null,
    created_at: new Date(Date.now() - 12 * 3600000).toISOString(),
    updated_at: new Date(Date.now() - 12 * 3600000).toISOString(),
  },
];

export const mockFuelLogs: FuelLogResponse[] = [
  {
    id: 1,
    vehicle_id: 1,
    trip_id: 1,
    liters: 42,
    cost: 3150,
    date: "2026-07-05",
    odometer_at_fill: 73950,
    created_by: 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 2,
    vehicle_id: 2,
    trip_id: 2,
    liters: 110,
    cost: 8400,
    date: "2026-07-06",
    odometer_at_fill: 181900,
    created_by: 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 3,
    vehicle_id: 3,
    trip_id: null,
    liters: 28,
    cost: 2050,
    date: "2026-07-06",
    odometer_at_fill: 65900,
    created_by: 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

export const mockExpenses: ExpenseResponse[] = [
  {
    id: 1,
    vehicle_id: 1,
    trip_id: 1,
    expense_type: "toll",
    description: "NH-48 Toll plaza toll",
    cost: 120,
    date: "2026-07-05",
    created_by: 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 2,
    vehicle_id: 2,
    trip_id: 2,
    expense_type: "toll",
    description: "Sardar Patel Ring Road Toll",
    cost: 340,
    date: "2026-07-06",
    created_by: 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 3,
    vehicle_id: 2,
    trip_id: 2,
    expense_type: "other",
    description: "Driver meals allowance",
    cost: 150,
    date: "2026-07-06",
    created_by: 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 4,
    vehicle_id: 2,
    trip_id: 2,
    expense_type: "maintenance_related",
    description: "Engine heat inspection charge",
    cost: 18000,
    date: "2026-07-06",
    created_by: 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

// Memory DB CRUD functions
class LocalDB {
  vehicles = [...mockVehicles];
  drivers = [...mockDrivers];
  trips = [...mockTrips];
  maintenanceLogs = [...mockMaintenanceLogs];
  fuelLogs = [...mockFuelLogs];
  expenses = [...mockExpenses];
  users = [...mockUsers];

  // Helper to paginate
  paginate<T>(items: T[], page = 1, pageSize = 20) {
    const total = items.length;
    const totalPages = Math.ceil(total / pageSize);
    const start = (page - 1) * pageSize;
    const end = start + pageSize;
    return {
      items: items.slice(start, end),
      total,
      page,
      page_size: pageSize,
      total_pages: totalPages,
    };
  }

  // Vehicles
  getVehicles(filters: { type?: string; status?: string; search?: string }) {
    let list = this.vehicles;
    if (filters.type && filters.type !== "All") {
      list = list.filter(v => v.type.toLowerCase() === filters.type?.toLowerCase());
    }
    if (filters.status && filters.status !== "All") {
      list = list.filter(v => v.status === filters.status);
    }
    if (filters.search) {
      const q = filters.search.toLowerCase();
      list = list.filter(
        v =>
          v.registration_number.toLowerCase().includes(q) ||
          v.name.toLowerCase().includes(q) ||
          (v.region && v.region.toLowerCase().includes(q))
      );
    }
    return list;
  }

  createVehicle(data: any) {
    const id = this.vehicles.length > 0 ? Math.max(...this.vehicles.map(v => v.id)) + 1 : 1;
    const item: VehicleResponse = {
      id,
      ...data,
      active_maintenance_count: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    this.vehicles.push(item);
    return item;
  }

  updateVehicle(id: number, data: any) {
    const idx = this.vehicles.findIndex(v => v.id === id);
    if (idx !== -1) {
      this.vehicles[idx] = {
        ...this.vehicles[idx],
        ...data,
        updated_at: new Date().toISOString(),
      };
      return this.vehicles[idx];
    }
    return null;
  }

  deleteVehicle(id: number) {
    // Soft delete / retire vehicle
    const vehicle = this.vehicles.find(v => v.id === id);
    if (vehicle) {
      vehicle.status = "retired";
      vehicle.updated_at = new Date().toISOString();
      return vehicle;
    }
    return null;
  }

  // Drivers
  getDrivers(filters: { status?: string; search?: string }) {
    let list = this.drivers;
    if (filters.status && filters.status !== "All") {
      list = list.filter(d => d.status === filters.status);
    }
    if (filters.search) {
      const q = filters.search.toLowerCase();
      list = list.filter(
        d =>
          d.name.toLowerCase().includes(q) ||
          d.license_number.toLowerCase().includes(q)
      );
    }
    return list;
  }

  createDriver(data: any) {
    const id = this.drivers.length > 0 ? Math.max(...this.drivers.map(d => d.id)) + 1 : 1;
    const is_license_expired = new Date(data.license_expiry) < new Date();
    const status = data.status || "available";
    const item: DriverResponse = {
      id,
      ...data,
      is_license_expired,
      is_assignable: status === "available" && !is_license_expired,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    this.drivers.push(item);
    return item;
  }

  updateDriver(id: number, data: any) {
    const idx = this.drivers.findIndex(d => d.id === id);
    if (idx !== -1) {
      const updated = {
        ...this.drivers[idx],
        ...data,
        updated_at: new Date().toISOString(),
      };
      updated.is_license_expired = new Date(updated.license_expiry) < new Date();
      updated.is_assignable = updated.status === "available" && !updated.is_license_expired;
      this.drivers[idx] = updated;
      return updated;
    }
    return null;
  }

  deleteDriver(id: number) {
    const driver = this.drivers.find(d => d.id === id);
    if (driver) {
      driver.status = "suspended";
      driver.is_assignable = false;
      driver.updated_at = new Date().toISOString();
      return driver;
    }
    return null;
  }

  // Trips
  getTrips(filters: { status?: string }) {
    let list = this.trips;
    if (filters.status && filters.status !== "All") {
      list = list.filter(t => t.status === filters.status);
    }
    // Populate nested vehicles/drivers
    return list.map(t => ({
      ...t,
      vehicle: this.vehicles.find(v => v.id === t.vehicle_id),
      driver: this.drivers.find(d => d.id === t.driver_id),
    }));
  }

  createTrip(data: any) {
    const id = this.trips.length > 0 ? Math.max(...this.trips.map(t => t.id)) + 1 : 1;
    const item: TripResponse = {
      id,
      ...data,
      status: "draft",
      actual_distance: null,
      fuel_consumed: null,
      final_odometer: null,
      dispatched_at: null,
      completed_at: null,
      cancelled_at: null,
      cancel_reason: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    this.trips.push(item);
    return item;
  }

  dispatchTrip(id: number) {
    const trip = this.trips.find(t => t.id === id);
    if (!trip) return null;
    
    // Update trip
    trip.status = "dispatched";
    trip.dispatched_at = new Date().toISOString();
    trip.updated_at = new Date().toISOString();

    // Update vehicle status -> on_trip
    const vehicle = this.vehicles.find(v => v.id === trip.vehicle_id);
    if (vehicle) {
      vehicle.status = "on_trip";
      vehicle.updated_at = new Date().toISOString();
    }

    // Update driver status -> on_trip
    const driver = this.drivers.find(d => d.id === trip.driver_id);
    if (driver) {
      driver.status = "on_trip";
      driver.is_assignable = false;
      driver.updated_at = new Date().toISOString();
    }

    return trip;
  }

  completeTrip(id: number, data: { actual_distance: number; fuel_consumed: number; final_odometer: number; revenue?: number }) {
    const trip = this.trips.find(t => t.id === id);
    if (!trip) return null;

    trip.status = "completed";
    trip.actual_distance = data.actual_distance;
    trip.fuel_consumed = data.fuel_consumed;
    trip.final_odometer = data.final_odometer;
    if (data.revenue !== undefined) {
      trip.revenue = data.revenue;
    }
    trip.completed_at = new Date().toISOString();
    trip.updated_at = new Date().toISOString();

    // Update vehicle status -> available, update odometer
    const vehicle = this.vehicles.find(v => v.id === trip.vehicle_id);
    if (vehicle) {
      vehicle.status = "available";
      vehicle.odometer = data.final_odometer;
      vehicle.updated_at = new Date().toISOString();
    }

    // Update driver status -> available
    const driver = this.drivers.find(d => d.id === trip.driver_id);
    if (driver) {
      driver.status = "available";
      driver.is_assignable = !driver.is_license_expired;
      driver.updated_at = new Date().toISOString();
    }

    // Automatically log fuel
    const fuelId = this.fuelLogs.length > 0 ? Math.max(...this.fuelLogs.map(f => f.id)) + 1 : 1;
    // Estimate cost based on average price or liters
    const estimatedFuelCost = data.fuel_consumed * 95; 
    this.fuelLogs.push({
      id: fuelId,
      vehicle_id: trip.vehicle_id,
      trip_id: trip.id,
      liters: data.fuel_consumed,
      cost: estimatedFuelCost,
      date: new Date().toISOString().split("T")[0],
      odometer_at_fill: data.final_odometer,
      created_by: 1,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });

    return trip;
  }

  cancelTrip(id: number, data?: { reason?: string }) {
    const trip = this.trips.find(t => t.id === id);
    if (!trip) return null;

    const wasDispatched = trip.status === "dispatched";
    trip.status = "cancelled";
    trip.cancelled_at = new Date().toISOString();
    trip.cancel_reason = data?.reason || "Cancelled by user";
    trip.updated_at = new Date().toISOString();

    if (wasDispatched) {
      // Revert vehicle and driver
      const vehicle = this.vehicles.find(v => v.id === trip.vehicle_id);
      if (vehicle) {
        // Check if vehicle has active maintenance logs. If so, put In Shop, else Available.
        const activeMaint = this.maintenanceLogs.filter(m => m.vehicle_id === vehicle.id && m.status === "active").length;
        vehicle.status = activeMaint > 0 ? "in_shop" : "available";
        vehicle.updated_at = new Date().toISOString();
      }

      const driver = this.drivers.find(d => d.id === trip.driver_id);
      if (driver) {
        driver.status = "available";
        driver.is_assignable = !driver.is_license_expired;
        driver.updated_at = new Date().toISOString();
      }
    }

    return trip;
  }

  // Maintenance
  getMaintenanceLogs() {
    return this.maintenanceLogs.map(m => ({
      ...m,
      vehicle: this.vehicles.find(v => v.id === m.vehicle_id),
    }));
  }

  createMaintenanceLog(data: any) {
    const id = this.maintenanceLogs.length > 0 ? Math.max(...this.maintenanceLogs.map(m => m.id)) + 1 : 1;
    const item: MaintenanceLogResponse = {
      id,
      vehicle_id: Number(data.vehicle_id),
      maintenance_type: data.maintenance_type,
      description: data.description,
      cost: data.cost ? Number(data.cost) : null,
      status: "active",
      started_at: data.started_at || new Date().toISOString(),
      closed_at: null,
      notes: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    this.maintenanceLogs.push(item);

    // Update vehicle -> in_shop
    const vehicle = this.vehicles.find(v => v.id === item.vehicle_id);
    if (vehicle) {
      vehicle.status = "in_shop";
      vehicle.active_maintenance_count = (vehicle.active_maintenance_count || 0) + 1;
      vehicle.updated_at = new Date().toISOString();
    }

    return item;
  }

  closeMaintenanceLog(id: number, data?: { cost?: number; notes?: string }) {
    const log = this.maintenanceLogs.find(m => m.id === id);
    if (!log) return null;

    log.status = "closed";
    log.closed_at = new Date().toISOString();
    if (data?.cost !== undefined) {
      log.cost = data.cost;
    }
    if (data?.notes !== undefined) {
      log.notes = data.notes;
    }
    log.updated_at = new Date().toISOString();

    // Update vehicle
    const vehicle = this.vehicles.find(v => v.id === log.vehicle_id);
    if (vehicle) {
      vehicle.active_maintenance_count = Math.max(0, (vehicle.active_maintenance_count || 1) - 1);
      
      // If no other active logs AND vehicle is not retired, set back to available
      const activeLogs = this.maintenanceLogs.filter(m => m.vehicle_id === vehicle.id && m.status === "active").length;
      if (activeLogs === 0 && vehicle.status !== "retired") {
        vehicle.status = "available";
      }
      vehicle.updated_at = new Date().toISOString();
    }

    // Automatically log expense
    const expenseId = this.expenses.length > 0 ? Math.max(...this.expenses.map(e => e.id)) + 1 : 1;
    this.expenses.push({
      id: expenseId,
      vehicle_id: log.vehicle_id,
      trip_id: null,
      expense_type: "maintenance_related",
      description: `Closed maintenance: ${log.description}`,
      cost: log.cost || 0,
      date: new Date().toISOString().split("T")[0],
      created_by: 1,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });

    return log;
  }

  // Fuel Logs
  getFuelLogs() {
    return this.fuelLogs.map(f => ({
      ...f,
      vehicle: this.vehicles.find(v => v.id === f.vehicle_id),
    }));
  }

  createFuelLog(data: any) {
    const id = this.fuelLogs.length > 0 ? Math.max(...this.fuelLogs.map(f => f.id)) + 1 : 1;
    const item: FuelLogResponse = {
      id,
      vehicle_id: Number(data.vehicle_id),
      trip_id: data.trip_id ? Number(data.trip_id) : null,
      liters: Number(data.liters),
      cost: Number(data.cost),
      date: data.date,
      odometer_at_fill: data.odometer_at_fill ? Number(data.odometer_at_fill) : null,
      created_by: 1,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    this.fuelLogs.push(item);

    // Update vehicle odometer if higher
    if (item.odometer_at_fill) {
      const vehicle = this.vehicles.find(v => v.id === item.vehicle_id);
      if (vehicle && item.odometer_at_fill > vehicle.odometer) {
        vehicle.odometer = item.odometer_at_fill;
        vehicle.updated_at = new Date().toISOString();
      }
    }

    return item;
  }

  // Expenses
  getExpenses() {
    return this.expenses.map(e => ({
      ...e,
      vehicle: this.vehicles.find(v => v.id === e.vehicle_id),
    }));
  }

  createExpense(data: any) {
    const id = this.expenses.length > 0 ? Math.max(...this.expenses.map(e => e.id)) + 1 : 1;
    const item: ExpenseResponse = {
      id,
      vehicle_id: Number(data.vehicle_id),
      trip_id: data.trip_id ? Number(data.trip_id) : null,
      expense_type: data.expense_type,
      description: data.description || null,
      cost: Number(data.cost),
      date: data.date,
      created_by: 1,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    this.expenses.push(item);
    return item;
  }

  // Dashboard KPIs
  getDashboardKPIs() {
    const totalVehicles = this.vehicles.length;
    const activeVehicles = this.vehicles.filter(v => v.status === "available" || v.status === "on_trip").length;
    const availableVehicles = this.vehicles.filter(v => v.status === "available").length;
    const inShopVehicles = this.vehicles.filter(v => v.status === "in_shop").length;
    const retiredVehicles = this.vehicles.filter(v => v.status === "retired").length;

    const totalNonRetired = this.vehicles.filter(v => v.status !== "retired").length;
    const onTripCount = this.vehicles.filter(v => v.status === "on_trip").length;
    const utilization = totalNonRetired > 0 ? Math.round((onTripCount / totalNonRetired) * 100) : 0;

    const activeTrips = this.trips.filter(t => t.status === "dispatched").length;
    const pendingTrips = this.trips.filter(t => t.status === "draft").length;

    const driversOnDuty = this.drivers.filter(d => d.status === "available" || d.status === "on_trip").length;

    // Fuel efficiency: Sum of trip actual_distance / Sum of trip fuel_consumed
    const completedTrips = this.trips.filter(t => t.status === "completed" && t.actual_distance && t.fuel_consumed);
    const totalDist = completedTrips.reduce((sum, t) => sum + (t.actual_distance || 0), 0);
    const totalFuel = completedTrips.reduce((sum, t) => sum + (t.fuel_consumed || 0), 0);
    const fuelEfficiency = totalFuel > 0 ? (totalDist / totalFuel).toFixed(1) : "8.4";

    // Operational cost: fuel + maintenance
    const fuelCostTotal = this.fuelLogs.reduce((sum, f) => sum + f.cost, 0);
    const maintCostTotal = this.maintenanceLogs.reduce((sum, m) => sum + (m.cost || 0), 0);
    const totalOperationalCost = fuelCostTotal + maintCostTotal;

    // Vehicle ROI: ROI = (sum(trip.revenue) − (maintenance_cost + fuel_cost)) / acquisition_cost
    const totalRevenue = this.trips.filter(t => t.status === "completed").reduce((sum, t) => sum + (t.revenue || 0), 0);
    const totalAcq = this.vehicles.reduce((sum, v) => sum + v.acquisition_cost, 0);
    const roi = totalAcq > 0 ? (((totalRevenue - totalOperationalCost) / totalAcq) * 100).toFixed(1) : "14.2";

    return {
      activeVehicles,
      availableVehicles,
      inShopVehicles,
      activeTrips,
      pendingTrips,
      driversOnDuty,
      utilization: `${utilization}%`,
      fuelEfficiency: `${fuelEfficiency} km/L`,
      operationalCost: totalOperationalCost,
      vehicleRoi: `${roi}%`,
      totalVehicles,
      retiredVehicles,
    };
  }

  // Dashboard Charts
  getDashboardCharts() {
    return {
      revenue: [
        { label: "Jan", value: 42000 },
        { label: "Feb", value: 55000 },
        { label: "Mar", value: 38000 },
        { label: "Apr", value: 71000 },
        { label: "May", value: 62000 },
        { label: "Jun", value: 84000 },
        { label: "Jul", value: 76000 },
      ],
      costliestVehicles: this.vehicles
        .map(v => {
          const vFuel = this.fuelLogs.filter(f => f.vehicle_id === v.id).reduce((sum, f) => sum + f.cost, 0);
          const vMaint = this.maintenanceLogs.filter(m => m.vehicle_id === v.id).reduce((sum, m) => sum + (m.cost || 0), 0);
          return {
            label: v.name,
            value: vFuel + vMaint,
          };
        })
        .filter(x => x.value > 0)
        .sort((a, b) => b.value - a.value)
        .slice(0, 5),
    };
  }
}

export const db = new LocalDB();
