"""
S-4 Logistics Section Tools and Models
Supply inventory, vehicle status, and resupply management
"""

import random
from typing import Dict
from pydantic import BaseModel
from agents import function_tool
from .monitoring import monitor_tool


# ============== S-4 MODELS ==============

class SupplyStatus(BaseModel):
    item: str
    quantity: int
    unit: str
    location: str
    days_remaining: int


class VehicleStatus(BaseModel):
    vehicle_type: str
    unit: str
    operational: int
    in_maintenance: int
    total: int
    readiness_rate: str
    next_maintenance: str


class ResupplyRequest(BaseModel):
    request_id: str
    unit: str
    supply_type: str
    quantity_requested: int
    priority: str
    status: str
    estimated_delivery: str
    delivery_method: str


# ============== S-4 TOOLS ==============

@function_tool(strict_mode=False)
@monitor_tool('check_supply_inventory', 'S-4')
def check_supply_inventory(unit: str, supply_type: str) -> SupplyStatus:
    """Check supply inventory levels for a specific unit and supply type."""
    
    supplies = {
        "MREs": {"quantity": random.randint(500, 2000), "unit": "meals", "days": 7},
        "MRE": {"quantity": random.randint(500, 2000), "unit": "meals", "days": 7},
        "5.56mm": {"quantity": random.randint(10000, 50000), "unit": "rounds", "days": 14},
        "7.62mm": {"quantity": random.randint(5000, 20000), "unit": "rounds", "days": 10},
        "fuel": {"quantity": random.randint(1000, 5000), "unit": "gallons", "days": 5},
        "water": {"quantity": random.randint(500, 2000), "unit": "gallons", "days": 3},
        "medical": {"quantity": random.randint(50, 200), "unit": "kits", "days": 30}
    }
    
    supply_data = supplies.get(supply_type, {"quantity": 0, "unit": "unknown", "days": 0})
    
    return SupplyStatus(
        item=supply_type,
        quantity=supply_data["quantity"],
        unit=supply_data["unit"],
        location=f"{unit} Supply Point",
        days_remaining=supply_data["days"]
    )


@function_tool(strict_mode=False)
@monitor_tool('check_vehicle_status', 'S-4')
def check_vehicle_status(vehicle_type: str, unit: str) -> VehicleStatus:
    """Check vehicle and equipment readiness status."""
    
    vehicles = {
        "LAV": {"operational": 8, "maintenance": 2, "total": 10},
        "HMMWV": {"operational": 15, "maintenance": 3, "total": 18},
        "MTVR": {"operational": 6, "maintenance": 1, "total": 7},
        "AAV": {"operational": 4, "maintenance": 2, "total": 6}
    }
    
    status = vehicles.get(vehicle_type, {"operational": 0, "maintenance": 0, "total": 0})
    readiness_rate = (status["operational"] / status["total"] * 100) if status["total"] > 0 else 0
    
    return VehicleStatus(
        vehicle_type=vehicle_type,
        unit=unit,
        operational=status["operational"],
        in_maintenance=status["maintenance"],
        total=status["total"],
        readiness_rate=f"{readiness_rate:.1f}%",
        next_maintenance="72 hours"
    )


@function_tool(strict_mode=False)
@monitor_tool('request_resupply', 'S-4')
def request_resupply(unit: str, supply_type: str, quantity: int, priority: str) -> Dict:
    """Initiate a resupply request for a unit."""
    
    request_id = f"RSP-{random.randint(1000, 9999)}"
    eta_hours = {"urgent": 6, "priority": 12, "routine": 24}.get(priority.lower(), 24)
    
    return {
        "request_id": request_id,
        "unit": unit,
        "supply_type": supply_type,
        "quantity_requested": quantity,
        "priority": priority.upper(),
        "status": "APPROVED",
        "estimated_delivery": f"{eta_hours} hours",
        "delivery_method": "Convoy" if eta_hours > 12 else "Air"
    }


@function_tool(strict_mode=False)
@monitor_tool('calculate_sustainment', 'S-4')
def calculate_sustainment(
    unit: str,
    personnel_count: int,
    duration_hours: int,
    mres_per_day_per_person: float = 3.0,
    fuel_gallons_per_hour: float = 50.0,
) -> Dict:
    """Compute rough sustainment requirements (MREs and fuel) for the given duration.

    Returns required quantities and planning notes. Combine with current inventory via
    check_supply_inventory to decide if resupply is needed.
    """
    days = max(1, int(round(duration_hours / 24)))
    mres_required = int(personnel_count * days * mres_per_day_per_person)
    fuel_required = int(duration_hours * fuel_gallons_per_hour)
    return {
        "unit": unit,
        "duration_hours": duration_hours,
        "assumptions": {
            "mres_per_day_per_person": mres_per_day_per_person,
            "fuel_gallons_per_hour": fuel_gallons_per_hour,
        },
        "requirements": {
            "mres_required": mres_required,
            "fuel_required_gallons": fuel_required,
        },
        "notes": "Compare requirements vs. current inventory; if shortfall, request resupply."
    }