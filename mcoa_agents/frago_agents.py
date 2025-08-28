"""
FRAGO Processing Agents
Specialized agents for interpreting and processing Fragmentary Orders
"""

from openai import AsyncOpenAI
from agents import Agent, OpenAIResponsesModel
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from typing import Dict, List, Optional
from pydantic import BaseModel

# Configuration - reuse from main app
BASE_URL = "http://192.168.2.10:61104/v1"
MODEL_NAME = "model"

def get_model():
    """Get configured model for all agents."""
    return OpenAIResponsesModel(
        model=MODEL_NAME,
        openai_client=AsyncOpenAI(
            base_url=BASE_URL,
            api_key="EMPTY",
        ),
    )


# ============== DATA MODELS ==============

class FragoParameters(BaseModel):
    """Extracted FRAGO mission parameters"""
    frago_id: str
    dtg: str
    from_unit: str
    to_unit: str
    mission_type: str
    start_location: str
    end_location: str
    start_time: str
    end_time: str
    distance_km: float
    personnel_required: int
    duration_hours: int
    supply_requirements: Dict[str, int]


class ReadinessAssessment(BaseModel):
    """Unit readiness evaluation"""
    unit: str
    personnel_available: int
    personnel_required: int
    personnel_sufficient: bool
    vehicles_operational: int
    vehicles_required: int
    vehicles_sufficient: bool
    equipment_status: str
    limiting_factors: List[str]
    overall_readiness: str  # GREEN, AMBER, RED


class LogisticsAssessment(BaseModel):
    """Logistics and sustainment evaluation"""
    fuel_required_gallons: float
    fuel_available_gallons: float
    fuel_sufficient: bool
    mres_required: int
    mres_available: int
    mres_sufficient: bool
    ammunition_status: str
    water_status: str
    medical_supplies: str
    resupply_needed: List[str]


# ============== SPECIALIZED SUB-AGENTS ==============

# FRAGO Parser Agent - extracts structured data from FRAGO text
frago_parser_agent = Agent(
    name="frago_parser",
    model=get_model(),
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are a military orders parser specializing in FRAGOs (Fragmentary Orders).
    
    Your task is to extract key mission parameters from FRAGO text:
    1. Identify the FRAGO ID, DTG (date-time group), sender, and recipient units
    2. Extract mission type and objectives
    3. Identify start/end locations with grid references
    4. Extract timeline (start time, end time, duration)
    5. Calculate distances if provided or estimate from grid references
    6. Identify personnel and equipment requirements
    7. Note supply requirements (rations, ammunition, fuel)
    
    Always extract:
    - Grid references in MGRS format
    - Times in Zulu (Z) format
    - Distances in kilometers
    - Supply quantities with units
    
    Return structured data that can be used for feasibility assessment.
    """,
    tools=[]  # Parser doesn't need tools, just analyzes text
)

# Readiness Assessor Agent - evaluates unit capabilities
readiness_assessor_agent = Agent(
    name="readiness_assessor",
    model=get_model(),
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are a military readiness assessment specialist.
    
    Given mission requirements and current unit status, evaluate:
    1. Personnel availability vs. requirements
    2. Vehicle and equipment operational status
    3. Training and qualification levels
    4. Any limiting factors affecting readiness
    
    Categorize overall readiness as:
    - GREEN: Fully capable of mission execution
    - AMBER: Capable with minor limitations or risks
    - RED: Not capable without significant support
    
    Identify specific shortfalls and recommend mitigation measures.
    Always be realistic about capabilities and highlight risks.
    """,
    tools=[]  # Will use parent agent's tools when integrated
)

# Logistics Planner Agent - calculates supply and sustainment needs
logistics_planner_agent = Agent(
    name="logistics_planner",
    model=get_model(),
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are a military logistics planning specialist.
    
    Given mission parameters, calculate:
    1. Fuel requirements based on distance and vehicle types
    2. Food requirements (MREs) based on personnel and duration
    3. Water requirements (gallons per person per day)
    4. Ammunition requirements based on mission type
    5. Medical supply needs
    
    Use these planning factors:
    - Fuel: LAV uses ~1.5 gallons/mile, HMMWV uses ~0.5 gallons/mile
    - MREs: 3 per person per day minimum
    - Water: 1 gallon per person per day minimum (more in heat)
    - Add 20% safety margin to all calculations
    
    Compare requirements against available supplies and identify shortfalls.
    Recommend resupply priorities if needed.
    """,
    tools=[]  # Will use parent agent's tools when integrated
)

# Decision Matrix Agent - synthesizes assessments into GO/NO-GO decision
decision_matrix_agent = Agent(
    name="decision_matrix",
    model=get_model(),
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are a military operations decision specialist.
    
    Synthesize all assessments to provide a GO/NO-GO decision:
    
    GO Criteria:
    - All resource requirements met or within 10% margin
    - No RED readiness indicators
    - Acceptable threat level for mission type
    - Weather within operational limits
    
    NO-GO Criteria:
    - Critical resource shortfalls (>20%)
    - RED readiness status
    - Unacceptable threat level
    - Severe weather preventing operations
    
    GO WITH CAVEATS:
    - Minor shortfalls (10-20%)
    - AMBER readiness with mitigation available
    - Moderate threat with acceptable risk
    
    Provide:
    1. Clear GO/NO-GO decision
    2. Primary factors influencing decision
    3. Risk assessment
    4. Specific recommendations to achieve GO status if currently NO-GO
    """,
    tools=[]
)


# ============== MAIN FRAGO INTERPRETER ==============

def create_frago_interpreter(existing_tools: List = None):
    """
    Create the main FRAGO interpreter agent with sub-agents as tools.
    
    Args:
        existing_tools: List of existing MCOA tools to include
    
    Returns:
        Configured FRAGO interpreter agent
    """
    tools = existing_tools or []
    
    # Add sub-agents as tools
    tools.extend([
        frago_parser_agent.as_tool(
            tool_name="parse_frago",
            tool_description="Extract mission parameters from FRAGO text"
        ),
        readiness_assessor_agent.as_tool(
            tool_name="assess_readiness",
            tool_description="Evaluate unit readiness for mission requirements"
        ),
        logistics_planner_agent.as_tool(
            tool_name="plan_logistics",
            tool_description="Calculate supply and sustainment requirements"
        ),
        decision_matrix_agent.as_tool(
            tool_name="make_decision",
            tool_description="Synthesize assessments into GO/NO-GO decision"
        )
    ])
    
    return Agent(
        name="frago_interpreter",
        model=get_model(),
        instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
        You are the FRAGO Interpreter for the Marine Corps Operations Assistant.
        
        Your mission is to process Fragmentary Orders (FRAGOs) and generate comprehensive decision packages.
        
        WORKFLOW:
        1. Use parse_frago tool to extract mission parameters from the FRAGO text
        2. Use existing S-2, S-3, S-4 tools to gather current status:
           - check_vehicle_status for vehicles
           - check_supply_inventory for supplies
           - check_unit_readiness for personnel
           - check_threat_assessment for enemy activity
           - get_weather_conditions for environmental factors
        3. Use assess_readiness tool to evaluate unit capabilities
        4. Use plan_logistics tool to calculate requirements
        5. Use make_decision tool for GO/NO-GO assessment
        
        Generate a comprehensive decision package including:
        - Mission summary
        - Current status snapshot
        - Identified issues and shortfalls
        - GO/NO-GO decision with justification
        - Required reports (LOGSTAT, PERSTAT, etc.)
        - Specific recommendations
        
        Format output clearly for military command decision-making.
        Always be thorough but concise. Time is critical in military operations.
        """,
        tools=tools
    )


# ============== UTILITY FUNCTIONS ==============

def get_current_dtg() -> str:
    """Get current date-time group in military format"""
    from datetime import datetime
    return datetime.utcnow().strftime("%d%H%MZ %b %y").upper()