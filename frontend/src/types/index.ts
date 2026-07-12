export interface AuditFields {
  id: number;
  created_at: string;
  updated_at: string;
}

// User / Auth Schemas
export type Role = "fleet_manager" | "driver" | "safety_officer" | "financial_analyst";

export interface UserCreate {
  email: string;
  full_name: string;
  role: Role;
}

export interface UserUpdate {
  email?: string;
  full_name?: string;
  role?: Role;
  is_active?: boolean;
}

export interface UserResponse extends AuditFields {
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
}

// Vehicle Schemas
export type VehicleStatus = "available" | "on_trip" | "in_shop" | "retired";
export type VehicleType = "truck" | "van" | "bus" | "sedan" | "pickup" | "other";

export interface VehicleCreate {
  registration_number: string;
  name: string;
  type: VehicleType;
  max_load_capacity: number;
  odometer: number;
  acquisition_cost: number;
  region?: string;
  status?: VehicleStatus;
}

export interface VehicleUpdate {
  name?: string;
  type?: VehicleType;
  max_load_capacity?: number;
  odometer?: number;
  acquisition_cost?: number;
  region?: string;
  status?: VehicleStatus;
}

export interface VehicleResponse extends AuditFields {
  registration_number: string;
  name: string;
  type: VehicleType;
  max_load_capacity: number;
  odometer: number;
  acquisition_cost: number;
  region: string | null;
  status: VehicleStatus;
  active_maintenance_count: number;
}

// Driver Schemas
export type DriverStatus = "available" | "on_trip" | "off_duty" | "suspended";
export type LicenseCategory = "A" | "B" | "C" | "D" | "E" | "CE" | "DE";

export interface DriverCreate {
  name: string;
  license_number: string;
  license_category: LicenseCategory;
  license_expiry: string; // YYYY-MM-DD
  contact_number: string;
  safety_score?: number;
  status?: DriverStatus;
}

export interface DriverUpdate {
  name?: string;
  license_category?: LicenseCategory;
  license_expiry?: string;
  contact_number?: string;
  safety_score?: number;
  status?: DriverStatus;
}

export interface DriverResponse extends AuditFields {
  name: string;
  license_number: string;
  license_category: LicenseCategory;
  license_expiry: string;
  contact_number: string;
  safety_score: number;
  status: DriverStatus;
  is_license_expired: boolean;
  is_assignable: boolean;
}

// Trip Schemas
export type TripStatus = "draft" | "dispatched" | "completed" | "cancelled";

export interface TripCreate {
  source: string;
  destination: string;
  vehicle_id: number;
  driver_id: number;
  cargo_weight: number;
  planned_distance: number;
  revenue?: number | null;
}

export interface TripUpdate {
  source?: string;
  destination?: string;
  vehicle_id?: number;
  driver_id?: number;
  cargo_weight?: number;
  planned_distance?: number;
  revenue?: number | null;
}

export interface TripCompleteRequest {
  actual_distance: number;
  fuel_consumed: number;
  final_odometer: number;
  revenue?: number | null;
}

export interface TripCancelRequest {
  reason?: string;
}

export interface TripResponse extends AuditFields {
  source: string;
  destination: string;
  vehicle_id: number;
  driver_id: number;
  cargo_weight: number;
  planned_distance: number;
  actual_distance: number | null;
  fuel_consumed: number | null;
  final_odometer: number | null;
  revenue: number | null;
  status: TripStatus;
  dispatched_at: string | null;
  completed_at: string | null;
  cancelled_at: string | null;
  cancel_reason: string | null;
  vehicle?: Partial<VehicleResponse>;
  driver?: Partial<DriverResponse>;
}

// Maintenance Log Schemas
export type MaintenanceStatus = "active" | "closed";
export type MaintenanceType =
  | "oil_change"
  | "tire_replacement"
  | "brake_service"
  | "engine_repair"
  | "body_work"
  | "inspection"
  | "electrical"
  | "transmission"
  | "other";

export interface MaintenanceLogCreate {
  vehicle_id: number;
  maintenance_type: MaintenanceType;
  description: string;
  cost?: number;
  started_at?: string;
}

export interface MaintenanceLogUpdate {
  maintenance_type?: MaintenanceType;
  description?: string;
  cost?: number;
}

export interface MaintenanceLogCloseRequest {
  cost?: number;
  notes?: string;
}

export interface MaintenanceLogResponse extends AuditFields {
  vehicle_id: number;
  maintenance_type: MaintenanceType;
  description: string;
  cost: number | null;
  status: MaintenanceStatus;
  started_at: string;
  closed_at: string | null;
  notes: string | null;
  vehicle?: Partial<VehicleResponse>;
}

// Fuel Log Schemas
export interface FuelLogCreate {
  vehicle_id: number;
  trip_id?: number | null;
  liters: number;
  cost: number;
  date: string; // YYYY-MM-DD
  odometer_at_fill?: number | null;
}

export interface FuelLogUpdate {
  liters?: number;
  cost?: number;
  date?: string;
  odometer_at_fill?: number | null;
}

export interface FuelLogResponse extends AuditFields {
  vehicle_id: number;
  trip_id: number | null;
  liters: number;
  cost: number;
  date: string;
  odometer_at_fill: number | null;
  created_by: number;
  vehicle?: Partial<VehicleResponse>;
}

// Expense Schemas
export type ExpenseType =
  | "toll"
  | "parking"
  | "insurance"
  | "registration_fee"
  | "fine"
  | "maintenance_related"
  | "cleaning"
  | "other";

export interface ExpenseCreate {
  vehicle_id: number;
  trip_id?: number | null;
  expense_type: ExpenseType;
  description?: string;
  cost: number;
  date: string; // YYYY-MM-DD
}

export interface ExpenseUpdate {
  expense_type?: ExpenseType;
  description?: string;
  cost?: number;
  date?: string;
}

export interface ExpenseResponse extends AuditFields {
  vehicle_id: number;
  trip_id: number | null;
  expense_type: ExpenseType;
  description: string | null;
  cost: number;
  date: string;
  created_by: number;
  vehicle?: Partial<VehicleResponse>;
}

// Common pagination and responses
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
