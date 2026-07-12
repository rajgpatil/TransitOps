import enum
from typing import Set, Dict, Tuple
from app.models.user import RoleEnum


class ModuleEnum(str, enum.Enum):
    vehicles = "vehicles"
    drivers = "drivers"
    trips = "trips"
    maintenance = "maintenance"
    expenses = "expenses"
    dashboard = "dashboard"
    reports = "reports"


class ActionEnum(str, enum.Enum):
    create = "create"
    read = "read"
    update = "update"
    delete = "delete"


# Define the permission mapping: (Module, Action) -> set[RoleEnum]
PERMISSION_MATRIX: Dict[Tuple[ModuleEnum, ActionEnum], Set[RoleEnum]] = {
    # Vehicle Registry (CRUD)
    (ModuleEnum.vehicles, ActionEnum.create): {RoleEnum.fleet_manager},
    (ModuleEnum.vehicles, ActionEnum.read): {RoleEnum.fleet_manager, RoleEnum.driver, RoleEnum.safety_officer, RoleEnum.financial_analyst},
    (ModuleEnum.vehicles, ActionEnum.update): {RoleEnum.fleet_manager},
    (ModuleEnum.vehicles, ActionEnum.delete): {RoleEnum.fleet_manager},

    # Driver Management (CRUD)
    (ModuleEnum.drivers, ActionEnum.create): {RoleEnum.safety_officer},
    (ModuleEnum.drivers, ActionEnum.read): {RoleEnum.fleet_manager, RoleEnum.driver, RoleEnum.safety_officer, RoleEnum.financial_analyst},
    (ModuleEnum.drivers, ActionEnum.update): {RoleEnum.safety_officer, RoleEnum.fleet_manager},
    (ModuleEnum.drivers, ActionEnum.delete): {RoleEnum.safety_officer},

    # Trip Management (CRUD)
    (ModuleEnum.trips, ActionEnum.create): {RoleEnum.driver},
    (ModuleEnum.trips, ActionEnum.read): {RoleEnum.fleet_manager, RoleEnum.driver, RoleEnum.safety_officer, RoleEnum.financial_analyst},
    (ModuleEnum.trips, ActionEnum.update): {RoleEnum.driver},
    (ModuleEnum.trips, ActionEnum.delete): {RoleEnum.driver},

    # Maintenance Logs
    (ModuleEnum.maintenance, ActionEnum.create): {RoleEnum.fleet_manager},
    (ModuleEnum.maintenance, ActionEnum.read): {RoleEnum.fleet_manager, RoleEnum.safety_officer, RoleEnum.financial_analyst},
    (ModuleEnum.maintenance, ActionEnum.update): {RoleEnum.fleet_manager},
    (ModuleEnum.maintenance, ActionEnum.delete): {RoleEnum.fleet_manager},

    # Fuel & Expense Logs (CRUD)
    (ModuleEnum.expenses, ActionEnum.create): {RoleEnum.financial_analyst, RoleEnum.driver, RoleEnum.fleet_manager},
    (ModuleEnum.expenses, ActionEnum.read): {RoleEnum.financial_analyst, RoleEnum.fleet_manager, RoleEnum.safety_officer, RoleEnum.driver},
    (ModuleEnum.expenses, ActionEnum.update): {RoleEnum.financial_analyst, RoleEnum.fleet_manager},
    (ModuleEnum.expenses, ActionEnum.delete): {RoleEnum.financial_analyst},

    # Dashboard/KPIs
    (ModuleEnum.dashboard, ActionEnum.read): {RoleEnum.fleet_manager, RoleEnum.driver, RoleEnum.safety_officer, RoleEnum.financial_analyst},

    # Reports & Analytics
    (ModuleEnum.reports, ActionEnum.read): {RoleEnum.fleet_manager, RoleEnum.financial_analyst},
}


def has_permission(role: RoleEnum, module: ModuleEnum, action: ActionEnum) -> bool:
    """Check if a role has permission to perform an action on a module."""
    allowed_roles = PERMISSION_MATRIX.get((module, action), set())
    return role in allowed_roles
