"""
S-2 Intelligence Section Tools and Models
Weather, terrain, and threat assessment capabilities
"""

import random
from typing import Dict, List
from pydantic import BaseModel
from agents import function_tool
from .monitoring import monitor_tool


# ============== S-2 MODELS ==============

class WeatherConditions(BaseModel):
    grid_reference: str
    time: str
    temperature_f: int
    condition: str
    wind_speed_mph: int
    wind_direction: str
    visibility_meters: int
    precipitation_chance: int
    moon_illumination: str


class TerrainAnalysis(BaseModel):
    grid_reference: str
    analysis_radius_km: int
    primary_terrain: str
    elevation_range_m: str
    key_terrain: List[str]
    obstacles: List[str]
    cover_concealment: str
    mobility_assessment: str
    recommended_approach: str


class ThreatAssessment(BaseModel):
    area: str
    threat_level: str
    last_contact: str
    enemy_strength: str
    enemy_activity: str
    idf_threat: str
    pattern_analysis: str
    recommended_posture: str


# ============== S-2 TOOLS ==============

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