"""
Pydantic models for MCOA tool responses
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


# S-4 Logistics Models
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


# S-2 Intelligence Models
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


# S-3 Operations Models
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