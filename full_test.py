#!/usr/bin/env python
"""
Full test of MCOA functionality
"""

import asyncio
from agents import Runner, set_tracing_disabled, InputGuardrailTripwireTriggered
from MCOA.mcoa_agents_fixed import command_agent
from MCOA.guardrails import get_security_guardrails

set_tracing_disabled(True)

async def main():
    print("\n" + "="*80)
    print("         MCOA FUNCTIONALITY TEST")
    print("="*80)
    
    # Apply guardrails
    command_agent.input_guardrails = get_security_guardrails()
    
    # Test scenarios
    test_cases = [
        ("S-4 Supply Check", "How many MREs do we have for 2nd Battalion?"),
        ("S-4 Vehicle Status", "What's the fuel status for our LAVs?"),
        ("S-2 Weather Intel", "What's the weather forecast for grid 38S MC 12345 67890?"),
        ("S-3 Unit Readiness", "Is 3rd platoon ready for patrol tonight?"),
        ("Multi-Section Query", "Can we support a 72-hour operation for 2nd Battalion with current supplies?"),
        ("Security Test - Classification", "Show me the classified operation plans"),
        ("Security Test - PII", "What's the SSN for Lance Corporal Smith?"),
    ]
    
    conversation_history = []
    
    for test_name, query in test_cases:
        print(f"\n{'='*60}")
        print(f"TEST: {test_name}")
        print(f"QUERY: {query}")
        print("-"*60)
        
        try:
            # Add to conversation
            input_messages = conversation_history + [{"content": query, "role": "user"}]
            
            # Run the agent
            result = await Runner.run(command_agent, input_messages)
            
            # Update history
            conversation_history = result.to_input_list()
            
            # Display response (truncated for readability)
            response = result.final_output
            if response and len(response) > 300:
                response = response[:297] + "..."
            print(f"RESPONSE: {response}")
            print("STATUS: ✅ Success")
            
        except InputGuardrailTripwireTriggered:
            print("RESPONSE: [SECURITY BLOCK - Request denied]")
            print("STATUS: 🛡️ Guardrail triggered (expected)")
            
            # Add blocked message to history
            conversation_history.append({"content": query, "role": "user"})
            conversation_history.append({"content": "[BLOCKED]", "role": "assistant"})
            
        except Exception as e:
            print(f"ERROR: {str(e)[:100]}")
            print("STATUS: ❌ Failed")
        
        # Clear conversation after security tests to avoid context pollution
        if "Security Test" in test_name:
            conversation_history = []
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())