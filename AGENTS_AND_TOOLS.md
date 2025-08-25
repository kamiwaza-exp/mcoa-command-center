# MCOA Agents and Tools

This document describes the sub‑agents that make up the Marine Corps Operations Assistant (MCOA) and the dummy tools wired into the app for demos and testing.

The repo has two variants of the agent wiring:
- Orchestrated sub‑agents (S‑2/S‑3/S‑4) plus a Command agent: `MCOA/mcoa_agents.py`
- UI variant with a single Command agent that directly exposes tools: `MCOA/mcoa_agents_ui.py` (tools injected by `MCOA/mcoa_service.py`)

All tools in the UI are instrumented via `MCOA/tools_monitored.py` so the dashboard can show real‑time events.

---

## Sub‑agents

### Command_Agent
- Role: Front‑door orchestrator. Receives user requests, decides which section(s) are relevant, and coordinates multi‑section queries.
- Typical actions:
  - Route weather/terrain/threat to S‑2
  - Route missions/readiness/patrols/comms to S‑3
  - Route supplies/vehicles/resupply to S‑4
  - For complex queries, call multiple tools and synthesize a single report
- Defined in:
  - `MCOA/mcoa_agents.py` (handoffs to S‑2/S‑3/S‑4)
  - `MCOA/mcoa_agents_ui.py` (single agent; tools are attached by service)

### S2_Intelligence
- Responsibilities:
  - Weather and environmental intelligence
  - Terrain analysis for planning
  - Threat assessment and enemy activity
- Communication:
  - Uses MGRS where appropriate; INTSUM style summaries; include confidence/time factors
- Tools: see S‑2 tools below
- Defined in: `MCOA/mcoa_agents.py`

### S3_Operations
- Responsibilities:
  - Track current/planned missions
  - Unit readiness and personnel status
  - Patrol schedules and rotations
  - Communications status
- Communication:
  - OPORD/operations style, use Zulu time, readiness C‑ratings (C‑1 … C‑4)
- Tools: see S‑3 tools below
- Defined in: `MCOA/mcoa_agents.py`

### S4_Logistics
- Responsibilities:
  - Supply inventories (ammo, fuel, food, water, medical)
  - Vehicle/equipment readiness
  - Resupply requests
- Communication:
  - Logistics report style; include readiness percentages and days of supply
- Tools: see S‑4 tools below
- Defined in: `MCOA/mcoa_agents.py`

---

## Dummy tools (demo/simulated)

In the UI, tools come from `MCOA/tools_monitored.py`. They simulate data with simple logic/randomness and emit real‑time events to the dashboard. Signatures and typical outputs:

### S‑4 Logistics tools
- `check_supply_inventory(unit: str, supply_type: str) -> SupplyStatus`
  - Returns quantity, unit, location, and days_remaining for the requested supply
  - Example supply types: "MREs", "fuel", "water"
- `check_vehicle_status(vehicle_type: str, unit: str) -> VehicleStatus`
  - Returns operational/in_maintenance/total counts and readiness rate
  - Example vehicle types: "LAV", "HMMWV", "MTVR", "AAV"
- `request_resupply(unit: str, supply_type: str, quantity: int, priority: str) -> dict`
  - Simulates a resupply request; returns request_id, status, ETA, delivery method

### S‑2 Intelligence tools
- `get_weather_conditions(grid_reference: str, hours_ahead: int = 0) -> dict`
  - Returns temperature, condition, wind, visibility, precip chance, moon illumination
- `get_terrain_analysis(grid_reference: str, radius_km: int = 5) -> dict`
  - Returns primary terrain, elevation range, key terrain, obstacles, mobility, recommended approach
- `check_threat_assessment(area: str) -> dict`
  - Returns threat level (LOW/MODERATE/ELEVATED/HIGH) with posture recommendations

### S‑3 Operations tools
- `get_mission_status(mission_id: str | None = None) -> dict`
  - Returns mission status (IN_PROGRESS/PLANNING/COMPLETE/ON_HOLD), units involved, SITREP
- `check_unit_readiness(unit: str) -> dict`
  - Returns personnel strength (assigned/present/ready) and equipment readiness, C‑rating
- `get_patrol_schedule(unit: str, timeframe: str = "today") -> list[dict]`
  - Returns a list of patrol windows/routes for the specified unit/timeframe
- `check_comms_status() -> dict`
  - Returns status for primary/alternate/data/emergency comms

### Planning/assessment helpers (for wow‑factor demos)
- `calculate_sustainment(unit: str, personnel_count: int, duration_hours: int, mres_per_day_per_person: float = 3.0, fuel_gallons_per_hour: float = 50.0) -> dict`
  - Computes rough MRE and fuel requirements for a duration; intended to be compared with `check_supply_inventory` results
- `compute_operation_feasibility(operation_name: str, grid_reference: str, start_time_zulu: str, duration_hours: int, weather: dict, terrain: dict, threat: dict, readiness: dict, vehicle_status: dict, supply_mres: dict, supply_fuel: dict, comms: dict, sustainment: dict | None = None) -> dict`
  - Aggregates S‑2/S‑3/S‑4 outputs into a single feasibility assessment; returns a human‑readable narrative, decision (GO/GO WITH CAVEATS/NO‑GO), and simple score

> Note: All tools are dummy/simulated for demo purposes. They are decorated with the Agents SDK’s `@function_tool` and a monitoring wrapper to emit `tool_start`, `tool_complete`, and `tool_error` events to the UI.

---

## Where things live
- Sub‑agents (multi‑agent orchestration example): `MCOA/mcoa_agents.py`
- UI command agent (single agent; tools injected): `MCOA/mcoa_agents_ui.py`
- Monitored tools for UI: `MCOA/tools_monitored.py`
- Pydantic models (tool output typing): `MCOA/tool_models.py`
- Security guardrails (classification/PII/OPSEC): `MCOA/guardrails.py`

---

## Example multi‑step demo queries
- 72‑hour operation feasibility (full S‑2/S‑3/S‑4 sweep):
  - Assess weather/terrain/threat → readiness/vehicles/comms → MRE/fuel inventory → sustainment calc → feasibility aggregation
- Convoy resupply plan with risk considerations:
  - Assess route weather/terrain/threat → comms/vehicles → issue `request_resupply` with PRIORITY if feasible

These scenarios are designed to make the agent call multiple tools with visible, real‑time execution in the dashboard before synthesizing a single report.

