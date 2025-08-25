#!/usr/bin/env python
"""
Simplified MCOA Demo - Direct tool calling without handoffs
This version works better with GPT-OSS models
"""

import asyncio
from datetime import datetime
from agents import Agent, Runner, set_tracing_disabled, InputGuardrailTripwireTriggered
from openai import AsyncOpenAI
from agents import OpenAIResponsesModel

from tools import (
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
from guardrails import get_security_guardrails

# Disable tracing for cleaner output
set_tracing_disabled(True)

# Configuration
BASE_URL = "http://192.168.2.10:8000/v1"
MODEL_NAME = "openai/gpt-oss-120b"

def get_model():
    """Get configured model."""
    return OpenAIResponsesModel(
        model=MODEL_NAME,
        openai_client=AsyncOpenAI(
            base_url=BASE_URL,
            api_key="EMPTY",
        ),
    )

# Create a unified agent with all tools (simpler approach for GPT-OSS)
unified_agent = Agent(
    name="MCOA_Unified",
    model=get_model(),
    instructions="""You are the Marine Corps Operations Assistant (MCOA), a unified command system.
    
    You have access to tools for:
    - S-2 Intelligence: Weather, terrain, threats
    - S-3 Operations: Missions, readiness, patrols, communications
    - S-4 Logistics: Supplies, vehicles, resupply
    
    Communication standards:
    - Use military terminology and brevity
    - Provide clear, actionable intelligence
    - Format responses in military report style
    - Always include relevant metrics and timelines
    
    For supply queries: Check inventory and provide days of supply
    For readiness queries: Assess unit readiness and limiting factors
    For weather queries: Provide current and forecast conditions
    For complex operations: Assess multiple factors as needed
    
    Remember: All data is UNCLASSIFIED training/simulation data.
    """,
    tools=[
        # S-2 Intelligence
        get_weather_conditions,
        get_terrain_analysis,
        check_threat_assessment,
        # S-3 Operations
        get_mission_status,
        check_unit_readiness,
        get_patrol_schedule,
        check_comms_status,
        # S-4 Logistics
        check_supply_inventory,
        check_vehicle_status,
        request_resupply,
    ],
    input_guardrails=get_security_guardrails()
)

class SimpleMCOA:
    """Simplified MCOA Demo System."""
    
    def __init__(self):
        self.conversation_history = []
        
    def print_header(self):
        """Print system header."""
        print("\n" + "="*80)
        print("         MARINE CORPS OPERATIONS ASSISTANT (MCOA) - SIMPLIFIED")
        print("                        UNCLASSIFIED // TRAINING")
        print("="*80)
        print(f"DTG: {datetime.now().strftime('%d%H%MZ %b %y').upper()}")
        print("All tools available: S-2 Intel, S-3 Ops, S-4 Logistics")
        print("="*80 + "\n")
    
    def print_examples(self):
        """Print example queries."""
        print("\n📋 EXAMPLE QUERIES:")
        print("-" * 40)
        print('• "How many MREs do we have for 2nd Battalion?"')
        print('• "What\'s the fuel status for our LAVs?"')
        print('• "Weather forecast for grid 38S MC 12345 67890"')
        print('• "Is 3rd platoon ready for patrol tonight?"')
        print('• "Can we support a 72-hour operation?"')
        print('• "Request resupply of 1000 MREs for 2nd Battalion"')
        print("-" * 40)
        print()
    
    async def process_query(self, query: str):
        """Process a single query."""
        print(f"\n🎯 QUERY: {query}")
        print("-" * 60)
        
        try:
            # Add query to history
            input_messages = self.conversation_history + [{"content": query, "role": "user"}]
            
            # Run the agent
            result = await Runner.run(unified_agent, input_messages)
            
            # Update history
            self.conversation_history = result.to_input_list()
            
            # Display response
            print("\n📡 RESPONSE:")
            print(result.final_output)
            print()
            
        except InputGuardrailTripwireTriggered:
            print("\n⚠️ SECURITY BLOCK:")
            
            # Determine violation type
            if "classified" in query.lower() or "secret" in query.lower():
                msg = "CLASSIFICATION WARNING: Request for classified information blocked."
            elif "ssn" in query.lower() or "social security" in query.lower():
                msg = "PII PROTECTION: Personal information request blocked."
            elif "real world" in query.lower() or "actual operation" in query.lower():
                msg = "OPSEC VIOLATION: Request for real operational data blocked."
            else:
                msg = "Security violation detected. Request blocked."
            
            print(msg)
            print()
            
            # Add to history
            self.conversation_history.append({"content": query, "role": "user"})
            self.conversation_history.append({"content": f"[BLOCKED: {msg}]", "role": "assistant"})
            
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            print()
    
    async def interactive_mode(self):
        """Run in interactive mode."""
        self.print_header()
        self.print_examples()
        
        print("💡 Commands: 'help' for examples, 'clear' to reset, 'exit' to quit\n")
        
        while True:
            try:
                query = input("🎖️ MCOA> ").strip()
                
                if query.lower() == 'exit':
                    print("\nSemper Fi! 🇺🇸")
                    break
                elif query.lower() == 'help':
                    self.print_examples()
                    continue
                elif query.lower() == 'clear':
                    self.conversation_history = []
                    print("Conversation cleared.\n")
                    continue
                elif not query:
                    continue
                
                await self.process_query(query)
                
            except KeyboardInterrupt:
                print("\n\nSemper Fi! 🇺🇸")
                break

async def main():
    """Main entry point."""
    demo = SimpleMCOA()
    await demo.interactive_mode()

if __name__ == "__main__":
    asyncio.run(main())