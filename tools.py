"""
Marine Corps Operations Assistant (MCOA) - Mock Tools
These are simulated tools for demonstration purposes
"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pydantic import BaseModel
from agents import function_tool


# ============== S-4 LOGISTICS TOOLS ==============

class SupplyStatus(BaseModel):
    item: str
    quantity: int
    unit: str
    location: str
    days_remaining: int


@function_tool
def check_supply_inventory(unit: str, supply_type: str) -> SupplyStatus:
    """Check supply inventory levels for a specific unit and supply type."""
    
    supplies = {
        "MREs": {"quantity": random.randint(500, 2000), "unit": "meals", "days": 7},
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


@function_tool
def check_vehicle_status(vehicle_type: str, unit: str) -> Dict:
    """Check vehicle and equipment readiness status."""
    
    vehicles = {
        "LAV": {"operational": 8, "maintenance": 2, "total": 10},
        "HMMWV": {"operational": 15, "maintenance": 3, "total": 18},
        "MTVR": {"operational": 6, "maintenance": 1, "total": 7},
        "AAV": {"operational": 4, "maintenance": 2, "total": 6}
    }
    
    status = vehicles.get(vehicle_type, {"operational": 0, "maintenance": 0, "total": 0})
    readiness_rate = (status["operational"] / status["total"] * 100) if status["total"] > 0 else 0
    
    return {
        "vehicle_type": vehicle_type,
        "unit": unit,
        "operational": status["operational"],
        "in_maintenance": status["maintenance"],
        "total": status["total"],
        "readiness_rate": f"{readiness_rate:.1f}%",
        "next_maintenance": "72 hours"
    }


@function_tool
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


# ============== S-2 INTELLIGENCE TOOLS ==============

@function_tool
def get_weather_conditions(grid_reference: str, hours_ahead: int = 0) -> Dict:
    """Get current and forecast weather conditions for a grid reference."""
    
    base_temp = random.randint(65, 95)
    conditions = ["Clear", "Partly Cloudy", "Overcast", "Light Rain", "Fog"]
    
    if hours_ahead == 0:
        condition = "Clear"
        temp = base_temp
    else:
        condition = random.choice(conditions)
        temp = base_temp + random.randint(-10, 10)
    
    return {
        "grid_reference": grid_reference,
        "time": f"+{hours_ahead} hours" if hours_ahead > 0 else "Current",
        "temperature_f": temp,
        "condition": condition,
        "wind_speed_mph": random.randint(5, 25),
        "wind_direction": random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
        "visibility_meters": 1000 if condition == "Fog" else 10000,
        "precipitation_chance": 20 if "Rain" in condition else 5,
        "moon_illumination": "73%" if hours_ahead > 12 else "Waxing Gibbous"
    }


@function_tool
def get_terrain_analysis(grid_reference: str, radius_km: int = 5) -> Dict:
    """Get terrain analysis for area of operations."""
    
    terrain_types = ["Mountainous", "Desert", "Urban", "Forest", "Coastal"]
    terrain = random.choice(terrain_types)
    
    return {
        "grid_reference": grid_reference,
        "analysis_radius_km": radius_km,
        "primary_terrain": terrain,
        "elevation_range_m": f"{random.randint(50, 200)}-{random.randint(300, 800)}",
        "key_terrain": ["Hill 362", "MSR Tampa", "Bridge Point Alpha"],
        "obstacles": ["Wadi system", "Urban sprawl"] if terrain == "Desert" else ["Dense vegetation"],
        "cover_concealment": "Good" if terrain in ["Forest", "Urban"] else "Limited",
        "mobility_assessment": "Restricted" if terrain == "Mountainous" else "Good",
        "recommended_approach": "Northwest ridge line provides best cover"
    }


@function_tool
def check_threat_assessment(area: str) -> Dict:
    """Check current threat assessment for an area."""
    
    threat_levels = ["LOW", "MODERATE", "ELEVATED", "HIGH"]
    threat_level = random.choice(threat_levels)
    
    return {
        "area": area,
        "threat_level": threat_level,
        "last_contact": f"{random.randint(2, 48)} hours ago",
        "enemy_strength": "Squad-sized element" if threat_level == "MODERATE" else "Unknown",
        "enemy_activity": "Sporadic small arms fire" if threat_level != "LOW" else "No recent activity",
        "idf_threat": "Possible" if threat_level in ["ELEVATED", "HIGH"] else "Unlikely",
        "pattern_analysis": "Enemy typically active during dawn/dusk",
        "recommended_posture": "Heightened security" if threat_level != "LOW" else "Normal operations"
    }


# ============== S-3 OPERATIONS TOOLS ==============

@function_tool
def get_mission_status(mission_id: Optional[str] = None) -> Dict:
    """Get current mission status."""
    
    if not mission_id:
        mission_id = f"OP-{random.randint(100, 999)}"
    
    statuses = ["IN_PROGRESS", "PLANNING", "COMPLETE", "ON_HOLD"]
    status = random.choice(statuses)
    
    return {
        "mission_id": mission_id,
        "mission_name": f"Operation {random.choice(['STEEL', 'IRON', 'EAGLE', 'THUNDER'])} {random.choice(['STORM', 'HAWK', 'SHIELD', 'SPEAR'])}",
        "status": status,
        "phase": "Execution" if status == "IN_PROGRESS" else "Planning",
        "units_involved": ["2/5 Marines", "3rd LAR", "1st Recon Bn"],
        "start_time": "0600Z",
        "estimated_completion": "1800Z",
        "commander_intent": "Secure and hold objective ALPHA",
        "current_sitrep": "All units in position, proceeding as planned"
    }


@function_tool
def check_unit_readiness(unit: str) -> Dict:
    """Check personnel and equipment readiness for a unit."""
    
    personnel_ready = random.randint(85, 98)
    equipment_ready = random.randint(80, 95)
    
    return {
        "unit": unit,
        "personnel_strength": {
            "assigned": 145,
            "present": 138,
            "ready": int(145 * personnel_ready / 100),
            "readiness_percent": f"{personnel_ready}%"
        },
        "equipment_readiness": f"{equipment_ready}%",
        "limiting_factors": ["2 Marines on light duty", "1 vehicle in maintenance"] if equipment_ready < 90 else ["None"],
        "c_rating": "C-2" if personnel_ready > 90 and equipment_ready > 85 else "C-3",
        "last_updated": "2 hours ago",
        "next_readiness_check": "0600 tomorrow"
    }


@function_tool
def get_patrol_schedule(unit: str, timeframe: str = "today") -> List[Dict]:
    """Get patrol schedule for a unit."""
    
    patrols = []
    num_patrols = 3 if timeframe == "today" else 9
    
    for i in range(num_patrols):
        patrol = {
            "patrol_id": f"PTL-{random.randint(100, 999)}",
            "unit": f"{unit}/{random.choice(['1st', '2nd', '3rd'])} Squad",
            "type": random.choice(["Security", "Recon", "Presence"]),
            "departure": f"{6 + i*6:02d}00",
            "return": f"{10 + i*6:02d}00",
            "route": f"Route {random.choice(['RED', 'BLUE', 'GREEN'])}",
            "grid_points": [f"MC {random.randint(10000, 99999)} {random.randint(10000, 99999)}"],
            "status": "Scheduled" if i > 0 else "Active"
        }
        patrols.append(patrol)
    
    return patrols


@function_tool
def check_comms_status() -> Dict:
    """Check communication systems status."""
    
    return {
        "primary_net": {
            "type": "SINCGARS",
            "status": "OPERATIONAL",
            "signal_strength": "Strong",
            "crypto": "Loaded",
            "last_check": "30 minutes ago"
        },
        "alternate_net": {
            "type": "HF",
            "status": "OPERATIONAL",
            "signal_strength": "Moderate",
            "next_window": "1200Z"
        },
        "data_link": {
            "type": "BFT",
            "status": "OPERATIONAL",
            "satellites": 7,
            "latency_ms": 245
        },
        "emergency": {
            "type": "SATCOM",
            "status": "STANDBY",
            "channel": "GUARD"
        }
    }