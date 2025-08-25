"""
S-3 Operations Section Tools and Models
Mission status, unit readiness, patrols, and communications
"""

import random
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from agents import function_tool
from .monitoring import monitor_tool


# ============== S-3 MODELS ==============

class MissionStatus(BaseModel):
    mission_id: str
    mission_name: str
    status: str
    phase: str
    units_involved: List[str]
    start_time: str
    estimated_completion: str
    commander_intent: str
    current_sitrep: str


class PersonnelStrength(BaseModel):
    assigned: int
    present: int
    ready: int
    readiness_percent: str


class UnitReadiness(BaseModel):
    unit: str
    personnel_strength: PersonnelStrength
    equipment_readiness: str
    limiting_factors: List[str]
    c_rating: str
    last_updated: str
    next_readiness_check: str


class Patrol(BaseModel):
    patrol_id: str
    unit: str
    type: str
    departure: str
    return_time: str = Field(alias="return")  # 'return' is a Python keyword
    route: str
    grid_points: List[str]
    status: str
    
    class Config:
        populate_by_name = True  # Allow both 'return' and 'return_time'


class NetworkStatus(BaseModel):
    type: str
    status: str
    signal_strength: str
    crypto: Optional[str] = None
    last_check: Optional[str] = None
    next_window: Optional[str] = None
    satellites: Optional[int] = None
    latency_ms: Optional[int] = None
    channel: Optional[str] = None


class CommsStatus(BaseModel):
    primary_net: NetworkStatus
    alternate_net: NetworkStatus
    data_link: NetworkStatus
    emergency: NetworkStatus


# ============== S-3 TOOLS ==============

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