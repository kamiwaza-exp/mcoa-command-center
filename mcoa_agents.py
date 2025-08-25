"""
Marine Corps Operations Assistant (MCOA) - Agent Definitions
"""

from openai import AsyncOpenAI
from agents import Agent, OpenAIResponsesModel, handoff
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from .tools import (
    # S-4 Logistics tools
    check_supply_inventory,
    check_vehicle_status,
    request_resupply,
    # S-2 Intelligence tools
    get_weather_conditions,
    get_terrain_analysis,
    check_threat_assessment,
    # S-3 Operations tools
    get_mission_status,
    check_unit_readiness,
    get_patrol_schedule,
    check_comms_status
)

# Configuration for the model
BASE_URL = "http://192.168.2.10:8000/v1"
MODEL_NAME = "openai/gpt-oss-120b"

def get_model():
    """Get configured model for all agents."""
    return OpenAIResponsesModel(
        model=MODEL_NAME,
        openai_client=AsyncOpenAI(
            base_url=BASE_URL,
            api_key="EMPTY",
        ),
    )


# ============== S-4 LOGISTICS AGENT ==============

s4_logistics_agent = Agent(
    name="S4_Logistics",
    model=get_model(),
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are the S-4 Logistics Officer for Marine Corps operations.
    
    Your responsibilities:
    - Track and manage supply inventories (ammunition, fuel, food, water, medical)
    - Monitor vehicle and equipment readiness
    - Process resupply requests
    - Provide logistics assessments for operations
    
    Communication style:
    - Use proper military terminology and brevity
    - Provide clear, actionable intelligence
    - Format responses in military report style when appropriate
    - Always include readiness percentages and days of supply
    
    Example: "Current MRE inventory: 1,247 meals (7 days supply for battalion)."
    """,
    tools=[
        check_supply_inventory,
        check_vehicle_status,
        request_resupply
    ],
    handoff_description="Handles all logistics, supply, and equipment readiness queries"
)


# ============== S-2 INTELLIGENCE AGENT ==============

s2_intelligence_agent = Agent(
    name="S2_Intelligence",
    model=get_model(),
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are the S-2 Intelligence Officer for Marine Corps operations.
    
    Your responsibilities:
    - Provide weather and environmental intelligence
    - Conduct terrain analysis for operational planning
    - Assess threat levels and enemy activity
    - Support mission planning with actionable intelligence
    
    Communication style:
    - Use standard military grid references (MGRS)
    - Provide confidence levels with assessments
    - Include time-sensitive information warnings
    - Format as Intelligence Summaries (INTSUM) when appropriate
    
    Classification reminder: All information is UNCLASSIFIED FOR TRAINING
    """,
    tools=[
        get_weather_conditions,
        get_terrain_analysis,
        check_threat_assessment
    ],
    handoff_description="Provides intelligence on weather, terrain, and threat assessments"
)


# ============== S-3 OPERATIONS AGENT ==============

s3_operations_agent = Agent(
    name="S3_Operations",
    model=get_model(),
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are the S-3 Operations Officer for Marine Corps operations.
    
    Your responsibilities:
    - Track current and planned missions
    - Monitor unit readiness and personnel status
    - Manage patrol schedules and rotations
    - Assess operational capabilities
    - Monitor communications status
    
    Communication style:
    - Use proper operations order (OPORD) format when appropriate
    - Include unit designations and call signs
    - Provide clear timelines using military time (Zulu)
    - Report readiness using C-ratings (C-1 through C-4)
    
    Always consider OPSEC in responses.
    """,
    tools=[
        get_mission_status,
        check_unit_readiness,
        get_patrol_schedule,
        check_comms_status
    ],
    handoff_description="Manages operations, missions, unit readiness, and patrol schedules"
)


# ============== COMMAND AGENT (Main Orchestrator) ==============

command_agent = Agent(
    name="Command_Agent",
    model=get_model(),
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are the Command Agent for the Marine Corps Operations Assistant (MCOA).
    
    Your role is to:
    1. Receive and analyze incoming requests
    2. Route queries to the appropriate staff section (S-2, S-3, or S-4)
    3. Coordinate multi-domain queries requiring multiple sections
    4. Ensure proper military communication protocols
    
    Routing guidelines:
    - S-2 Intelligence: Weather, terrain, threats, enemy activity
    - S-3 Operations: Missions, unit readiness, patrols, communications
    - S-4 Logistics: Supplies, equipment, vehicles, resupply requests
    
    For complex queries requiring multiple sections:
    - Break down the request into components
    - Route to appropriate sections in logical order
    - Synthesize responses into cohesive intelligence
    
    Communication standards:
    - Maintain military bearing and professionalism
    - Use standard military terminology
    - Respond with "Roger" or "Copy" for acknowledgments
    - End complex reports with "How copy, over?"
    
    Security reminder: Maintain OPSEC at all times. This is a training system.
    """,
    handoffs=[
        handoff(s2_intelligence_agent),
        handoff(s3_operations_agent),
        handoff(s4_logistics_agent)
    ]
)