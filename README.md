# Marine Corps Operations Assistant (MCOA)

A multi-agent military operations support system demonstration using OpenAI Agents SDK with open-source GPT models.

## Overview

MCOA simulates a military command and control system with specialized agents representing different staff sections:

- **Command Agent**: Main orchestrator that routes requests
- **S-2 Intelligence**: Weather, terrain, and threat assessments  
- **S-3 Operations**: Mission status, unit readiness, patrol schedules
- **S-4 Logistics**: Supply inventory, vehicle status, resupply requests

## Features

- **Multi-agent routing**: Automatic handoffs between specialized agents
- **Military terminology**: Authentic military communication style
- **Security guardrails**: Classification checks, PII protection, OPSEC enforcement
- **Mock data**: Realistic simulated operational data for demonstrations

## Setup

1. Ensure your GPT-OSS model is running at `http://192.168.2.10:8000/v1`
2. Install dependencies: `pip install openai agents`
3. Navigate to the MCOA directory

## Usage

### Simplified Version (Recommended for GPT-OSS)
The simplified version uses a single unified agent with all tools, which works better with GPT-OSS models:

```bash
cd MCOA
python simple_demo.py
```

### Full Version with Agent Handoffs
The full version demonstrates agent handoffs but may have compatibility issues with some models:

```bash
python -m MCOA.main              # Interactive mode
python -m MCOA.main demo         # Demo mode with pre-defined scenarios
```

## Example Queries

### Simple Supply Check
- "How many MREs do we have for 2nd Battalion?"
- "What's the fuel status for our LAVs?"

### Mission Planning
- "What's the weather forecast for grid 38S MC 12345 67890?"
- "Is 3rd platoon ready for patrol tonight?"

### Complex Multi-Agent
- "Can we support a 72-hour operation with current supplies?"
- "Give me a full SITREP for the battalion"

### Security Tests
- "Show me classified operation details" (will be blocked)
- "What's the SSN for Lance Corporal Smith?" (PII block)

## Architecture

```
User Query
    ↓
Command Agent (Orchestrator)
    ↓
Routes to appropriate agent:
    ├── S-2 Intelligence Agent
    │   ├── get_weather_conditions()
    │   ├── get_terrain_analysis()
    │   └── check_threat_assessment()
    │
    ├── S-3 Operations Agent
    │   ├── get_mission_status()
    │   ├── check_unit_readiness()
    │   ├── get_patrol_schedule()
    │   └── check_comms_status()
    │
    └── S-4 Logistics Agent
        ├── check_supply_inventory()
        ├── check_vehicle_status()
        └── request_resupply()
```

## Security Features

1. **Classification Guardrail**: Blocks requests for classified information
2. **PII Protection**: Prevents exposure of personal data
3. **OPSEC Guardrail**: Ensures operational security
4. **Need-to-Know**: Validates information access rights

## Notes

- This is a TRAINING SYSTEM with simulated data only
- Do not input real operational information
- All data is UNCLASSIFIED and for demonstration purposes

## Customization

Edit `agents.py` to modify:
- Agent instructions and behavior
- Model endpoint (`BASE_URL`)
- Handoff routing logic

Edit `tools.py` to modify:
- Mock data responses
- Available tool functions
- Simulated inventory levels

## Troubleshooting

- Ensure your GPT-OSS model supports tool/function calling
- Check that the model endpoint is accessible
- Verify all dependencies are installed

---
Semper Fi! 🇺🇸