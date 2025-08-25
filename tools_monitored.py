"""
Marine Corps Operations Assistant (MCOA) - Monitored Tools
These are the original tools wrapped with monitoring for the UI
"""

import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from functools import wraps
from pydantic import BaseModel, ConfigDict
from agents import function_tool

# Import all the proper models
from tool_models import (
    SupplyStatus, VehicleStatus, ResupplyRequest,
    WeatherConditions, TerrainAnalysis, ThreatAssessment,
    MissionStatus, UnitReadiness, Patrol, CommsStatus,
    PersonnelStrength, NetworkStatus
)

# Global callback for monitoring
_tool_callback = None

def set_tool_callback(callback: Callable):
    """Set the callback function for tool monitoring."""
    global _tool_callback
    _tool_callback = callback

def monitor_tool(tool_name: str, section: str):
    """Decorator to monitor tool execution."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Emit tool start event
            start_time = time.time()
            
            if _tool_callback:
                _tool_callback('tool_start', {
                    'tool_name': tool_name,
                    'section': section,
                    'parameters': {
                        'args': [str(arg)[:100] for arg in args],
                        'kwargs': {k: str(v)[:100] for k, v in kwargs.items()}
                    },
                    'timestamp': datetime.now().isoformat()
                })
            
            try:
                # Execute the actual tool
                result = func(*args, **kwargs)
                
                # Process result for emission
                if hasattr(result, 'dict'):
                    result_data = result.dict()
                elif hasattr(result, '__dict__'):
                    result_data = result.__dict__
                elif isinstance(result, dict):
                    result_data = result
                elif isinstance(result, list):
                    result_data = {'items': result, 'count': len(result)}
                else:
                    result_data = {'value': str(result)[:500]}
                
                # Emit tool complete event
                duration = time.time() - start_time
                
                if _tool_callback:
                    _tool_callback('tool_complete', {
                        'tool_name': tool_name,
                        'section': section,
                        'duration': duration,
                        'result': result_data,
                        'success': True,
                        'timestamp': datetime.now().isoformat()
                    })
                
                return result
                
            except Exception as e:
                # Emit tool error event
                duration = time.time() - start_time
                
                if _tool_callback:
                    _tool_callback('tool_error', {
                        'tool_name': tool_name,
                        'section': section,
                        'duration': duration,
                        'error': str(e),
                        'success': False,
                        'timestamp': datetime.now().isoformat()
                    })
                
                raise
        
        return wrapper
    return decorator


# ============== S-4 LOGISTICS TOOLS ==============


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


# ============== S-2 INTELLIGENCE TOOLS ==============

@function_tool(strict_mode=False)
@monitor_tool('get_weather_conditions', 'S-2')
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


@function_tool(strict_mode=False)
@monitor_tool('get_terrain_analysis', 'S-2')
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


@function_tool(strict_mode=False)
@monitor_tool('check_threat_assessment', 'S-2')
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

@function_tool(strict_mode=False)
@monitor_tool('get_mission_status', 'S-3')
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


@function_tool(strict_mode=False)
@monitor_tool('check_unit_readiness', 'S-3')
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


@function_tool(strict_mode=False)
@monitor_tool('get_patrol_schedule', 'S-3')
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


@function_tool(strict_mode=False)
@monitor_tool('check_comms_status', 'S-3')
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


# ============== PLANNING / ASSESSMENT TOOLS (S-3 ORCHESTRATION) ==============


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


@function_tool(strict_mode=False)
@monitor_tool('compute_operation_feasibility', 'S-3')
def compute_operation_feasibility(
    operation_name: str,
    grid_reference: str,
    start_time_zulu: str,
    duration_hours: int,
    weather: Dict,
    terrain: Dict,
    threat: Dict,
    readiness: Dict,
    vehicle_status: Dict,
    supply_mres: Dict,
    supply_fuel: Dict,
    comms: Dict,
    sustainment: Optional[Dict] = None,
    ) -> Dict:
    """Aggregate multi-domain inputs into a single feasibility assessment.

    The LLM should first call S-2/S-3/S-4 tools to populate these fields, then call this tool.
    Returns a summarized feasibility decision with key caveats and recommendations.
    """
    # Simple heuristic feasibility scoring
    score = 0
    try:
        wind = weather.get("wind_speed_mph", 10)
        vis = weather.get("visibility_meters", 10000)
        score += 1 if wind <= 20 else 0
        score += 1 if vis >= 5000 else 0
    except Exception:
        pass

    try:
        mobility = terrain.get("mobility_assessment", "Good")
        score += 1 if mobility.lower() == "good" else 0
    except Exception:
        pass

    try:
        level = threat.get("threat_level", "MODERATE")
        score += {"LOW": 2, "MODERATE": 1}.get(level, 0)
    except Exception:
        pass

    try:
        pr = readiness.get("personnel_strength", {}).get("readiness_percent", "90%")
        er = readiness.get("equipment_readiness", "90%")
        pr_val = int(str(pr).replace("%", "") or 0)
        er_val = int(str(er).replace("%", "") or 0)
        score += 1 if pr_val >= 90 else 0
        score += 1 if er_val >= 85 else 0
    except Exception:
        pass

    try:
        op = vehicle_status.get("operational", 0)
        total = vehicle_status.get("total", 1)
        rate = (op / total) * 100 if total else 0
        score += 1 if rate >= 70 else 0
    except Exception:
        pass

    try:
        primary_ok = comms.get("primary_net", {}).get("status", "OPERATIONAL") == "OPERATIONAL"
        alt_ok = comms.get("alternate_net", {}).get("status", "OPERATIONAL") == "OPERATIONAL"
        score += 1 if primary_ok else 0
        score += 1 if alt_ok else 0
    except Exception:
        pass

    sustainment_ok = True
    if sustainment and isinstance(sustainment, dict):
        try:
            mres_req = sustainment.get("requirements", {}).get("mres_required", 0)
            fuel_req = sustainment.get("requirements", {}).get("fuel_required_gallons", 0)
            mres_have = supply_mres.get("quantity", 0)
            fuel_have = supply_fuel.get("quantity", 0)
            if mres_have >= mres_req and fuel_have >= fuel_req:
                score += 2
            else:
                sustainment_ok = False
        except Exception:
            pass

    decision = (
        "GO" if score >= 7 and sustainment_ok else ("GO WITH CAVEATS" if score >= 5 else "NO-GO")
    )
    # Compose a concise operations-style feasibility report for human consumption
    lines = []
    lines.append(f"[S-3 OPERATIONS] FEASIBILITY – {operation_name}")
    lines.append(f"AO: {grid_reference} | SP: {start_time_zulu} | DUR: {duration_hours} hrs")
    lines.append("")
    lines.append("S-2 SUMMARY:")
    try:
        lines.append(
            f"  Weather: {weather.get('condition','N/A')}, {weather.get('temperature_f','?')}F, "
            f"wind {weather.get('wind_speed_mph','?')} mph, vis {weather.get('visibility_meters','?')} m"
        )
    except Exception:
        pass
    try:
        lines.append(
            f"  Terrain: {terrain.get('primary_terrain','N/A')}, mobility {terrain.get('mobility_assessment','N/A')}"
        )
    except Exception:
        pass
    try:
        lines.append(f"  Threat: {threat.get('threat_level','N/A')} – {threat.get('recommended_posture','')}")
    except Exception:
        pass

    lines.append("")
    lines.append("S-3 SUMMARY:")
    try:
        pr = readiness.get('personnel_strength', {}).get('readiness_percent', 'N/A')
        er = readiness.get('equipment_readiness', 'N/A')
        lines.append(f"  Readiness: personnel {pr}, equipment {er}")
    except Exception:
        pass
    try:
        op = vehicle_status.get('operational', '?')
        tot = vehicle_status.get('total', '?')
        lines.append(f"  Vehicles: operational {op}/{tot}")
    except Exception:
        pass
    try:
        lines.append(f"  Comms: PRI {comms.get('primary_net',{}).get('status','?')}, ALT {comms.get('alternate_net',{}).get('status','?')}")
    except Exception:
        pass

    lines.append("")
    lines.append("S-4 SUMMARY:")
    try:
        lines.append(
            f"  MREs: {supply_mres.get('quantity','?')} {supply_mres.get('unit','')} @ {supply_mres.get('location','')}"
        )
        lines.append(
            f"  Fuel: {supply_fuel.get('quantity','?')} {supply_fuel.get('unit','')} @ {supply_fuel.get('location','')}"
        )
    except Exception:
        pass
    if sustainment and isinstance(sustainment, dict):
        req = sustainment.get('requirements', {})
        lines.append(
            f"  Requirements (est.): {req.get('mres_required','?')} MREs, {req.get('fuel_required_gallons','?')} gal fuel"
        )

    lines.append("")
    lines.append(f"DECISION: {decision} (score {score}/10) | Sustainment OK: {'YES' if sustainment_ok else 'NO'}")
    lines.append("RECOMMENDATIONS:")
    lines.append("  - If shortfall, submit PRIORITY resupply and align delivery with L-H hour")
    lines.append("  - Align movements with best weather/visibility windows")
    lines.append("  - Verify ALT comms checks prior to SP; rehearse PACE")

    # Also return a machine-readable block alongside the narrative for UI debugging if needed
    return {
        "narrative": "\n".join(lines),
        "decision": decision,
        "score": score,
        "sustainment_ok": sustainment_ok,
    }
