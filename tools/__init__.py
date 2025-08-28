"""
MCOA Tools Package
Exports all tools and monitoring functionality for easy import
"""

# Import monitoring functionality
from .monitoring import set_tool_callback

# Import S-2 Intelligence tools
from .s2_intelligence import (
    get_weather_conditions,
    get_terrain_analysis,
    check_threat_assessment,
    # Models
    WeatherConditions,
    TerrainAnalysis,
    ThreatAssessment,
)

# Import S-3 Operations tools
from .s3_operations import (
    get_mission_status,
    check_unit_readiness,
    get_patrol_schedule,
    check_comms_status,
    compute_operation_feasibility,
    # Models
    MissionStatus,
    PersonnelStrength,
    UnitReadiness,
    Patrol,
    NetworkStatus,
    CommsStatus,
)

# Import S-4 Logistics tools
from .s4_logistics import (
    check_supply_inventory,
    check_vehicle_status,
    request_resupply,
    calculate_sustainment,
    # Models
    SupplyStatus,
    VehicleStatus,
    ResupplyRequest,
)

# Import Report Generation tools
from .report_generation import (
    generate_logstat_report,
    generate_perstat_report,
    generate_spot_report,
    generate_decision_package,
    submit_report,
    # Models
    LogstatReport,
    PerstatReport,
    SpotReport,
    DecisionPackage,
)

# Export all tools as a list for easy agent configuration
ALL_TOOLS = [
    # S-2 Intelligence
    get_weather_conditions,
    get_terrain_analysis,
    check_threat_assessment,
    # S-3 Operations
    get_mission_status,
    check_unit_readiness,
    get_patrol_schedule,
    check_comms_status,
    compute_operation_feasibility,
    # S-4 Logistics
    check_supply_inventory,
    check_vehicle_status,
    request_resupply,
    calculate_sustainment,
    # Report Generation
    generate_logstat_report,
    generate_perstat_report,
    generate_spot_report,
    generate_decision_package,
    submit_report,
]

__all__ = [
    # Monitoring
    'set_tool_callback',
    # S-2 Intelligence
    'get_weather_conditions',
    'get_terrain_analysis',
    'check_threat_assessment',
    'WeatherConditions',
    'TerrainAnalysis',
    'ThreatAssessment',
    # S-3 Operations
    'get_mission_status',
    'check_unit_readiness',
    'get_patrol_schedule',
    'check_comms_status',
    'compute_operation_feasibility',
    'MissionStatus',
    'PersonnelStrength',
    'UnitReadiness',
    'Patrol',
    'NetworkStatus',
    'CommsStatus',
    # S-4 Logistics
    'check_supply_inventory',
    'check_vehicle_status',
    'request_resupply',
    'calculate_sustainment',
    'SupplyStatus',
    'VehicleStatus',
    'ResupplyRequest',
    # Report Generation
    'generate_logstat_report',
    'generate_perstat_report',
    'generate_spot_report',
    'generate_decision_package',
    'submit_report',
    'LogstatReport',
    'PerstatReport',
    'SpotReport',
    'DecisionPackage',
    # Convenience
    'ALL_TOOLS',
]