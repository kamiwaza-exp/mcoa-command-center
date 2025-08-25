"""
Marine Corps Operations Assistant (MCOA) - Agent with Logged Tools
This version provides visual feedback when tools are called
"""

from openai import AsyncOpenAI
from agents import Agent, OpenAIResponsesModel
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

from tools_logged import (
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


# ============== UNIFIED COMMAND AGENT WITH LOGGING ==============

command_agent = Agent(
    name="Command_Agent",
    model=get_model(),
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are the Command Agent for the Marine Corps Operations Assistant (MCOA).
    
    You coordinate between three staff sections:
    - S-2 Intelligence: Weather, terrain, threats, enemy activity
    - S-3 Operations: Missions, unit readiness, patrols, communications
    - S-4 Logistics: Supplies, equipment, vehicles, resupply requests
    
    When responding to queries:
    1. Identify which section(s) would handle the request
    2. Use the appropriate tools for that section
    3. Format responses as if coming from that section
    4. For complex queries, coordinate information from multiple sections
    
    S-2 INTELLIGENCE MODE:
    - Use weather, terrain, and threat assessment tools
    - Format as Intelligence Summaries (INTSUM)
    - Include confidence levels and time-sensitive warnings
    - Use standard military grid references (MGRS)
    
    S-3 OPERATIONS MODE:
    - Use mission, readiness, patrol, and comms tools
    - Report readiness using C-ratings (C-1 through C-4)
    - Include unit designations and timelines in Zulu time
    - Consider OPSEC in all responses
    
    S-4 LOGISTICS MODE:
    - Use supply, vehicle, and resupply tools
    - Always include readiness percentages and days of supply
    - Provide clear logistics assessments
    - Format as supply status reports
    
    Communication standards:
    - Use military terminology and brevity
    - Begin responses by identifying the responding section
    - Maintain military bearing and professionalism
    - End complex reports with "How copy, over?"
    
    Example response format:
    "[S-4 LOGISTICS] Current MRE inventory for 2nd Battalion: 1,247 meals (7 days supply)."
    
    Security reminder: All information is UNCLASSIFIED training data.
    """,
    tools=[
        # S-2 Intelligence tools
        get_weather_conditions,
        get_terrain_analysis,
        check_threat_assessment,
        # S-3 Operations tools
        get_mission_status,
        check_unit_readiness,
        get_patrol_schedule,
        check_comms_status,
        # S-4 Logistics tools
        check_supply_inventory,
        check_vehicle_status,
        request_resupply,
    ]
)