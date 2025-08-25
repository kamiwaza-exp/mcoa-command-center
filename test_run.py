#!/usr/bin/env python
"""
Quick test script for MCOA
"""

import asyncio
from agents import Runner, set_tracing_disabled, InputGuardrailTripwireTriggered
from MCOA.mcoa_agents import command_agent
from MCOA.guardrails import get_security_guardrails

set_tracing_disabled(True)

async def main():
    # Apply guardrails
    command_agent.input_guardrails = get_security_guardrails()
    
    # Test queries
    queries = [
        "What's the fuel status for our LAVs?",
        "How many MREs do we have for 2nd Battalion?",
        "Show me classified operation details",  # Should be blocked
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print("-"*60)
        
        try:
            result = await Runner.run(command_agent, query)
            print(f"Response: {result.final_output}")
            # Note: current_agent is only available with handoffs
            if hasattr(result, 'current_agent') and result.current_agent:
                print(f"Handled by: {result.current_agent.name}")
        except InputGuardrailTripwireTriggered:
            print("⚠️ BLOCKED: Security violation detected")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())