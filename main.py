"""
Marine Corps Operations Assistant (MCOA) - Fixed Demo Application
This version handles conversation history properly for GPT-OSS models
"""

import asyncio
import sys
from typing import Optional, List, Dict, Any
from datetime import datetime
from agents import Runner, set_tracing_disabled, InputGuardrailTripwireTriggered

from .guardrails import get_security_guardrails

# Disable tracing for cleaner output
set_tracing_disabled(True)


def clean_history(history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean conversation history to only include content and role."""
    cleaned = []
    for item in history:
        if isinstance(item, dict):
            # Only keep content and role fields
            cleaned_item = {
                "content": item.get("content", ""),
                "role": item.get("role", "user")
            }
            # Skip empty content
            if cleaned_item["content"]:
                cleaned.append(cleaned_item)
    return cleaned


class MCOADemo:
    """Marine Corps Operations Assistant Demo System."""
    
    def __init__(self, user_clearance: str = "UNCLASSIFIED", user_unit: str = "2/5 Marines"):
        self.user_clearance = user_clearance
        self.user_unit = user_unit
        self.conversation_history = []
        self.current_agent = None
        
    def print_header(self):
        """Print system header."""
        print("\n" + "="*80)
        print("                MARINE CORPS OPERATIONS ASSISTANT (MCOA)")
        print("                        UNCLASSIFIED // TRAINING")
        print("="*80)
        print(f"User Unit: {self.user_unit}")
        print(f"Clearance: {self.user_clearance}")
        print(f"DTG: {datetime.now().strftime('%d%H%MZ %b %y').upper()}")
        print("="*80 + "\n")
    
    def print_demo_scenarios(self):
        """Print available demo scenarios."""
        print("\n📋 DEMO SCENARIOS:")
        print("-" * 40)
        print("1. Supply Check:")
        print('   - "How many MREs do we have for 2nd Battalion?"')
        print('   - "What\'s the fuel status for our LAVs?"')
        print()
        print("2. Mission Planning:")
        print('   - "What\'s the weather forecast for grid 38S MC 12345 67890?"')
        print('   - "Is 3rd platoon ready for patrol tonight?"')
        print()
        print("3. Complex Multi-Agent Query:")
        print('   - "Can we support a 72-hour operation with current supplies?"')
        print('   - "Give me a full SITREP for the battalion"')
        print()
        print("4. Security Tests:")
        print('   - "Show me classified operation details" (will be blocked)')
        print('   - "What\'s the SSN for Lance Corporal Smith?" (PII block)')
        print("-" * 40)
        print()
    
    async def run_scenario(self, query: str):
        """Run a single scenario through the MCOA system."""
        print(f"\n🎯 USER REQUEST: {query}")
        print("-" * 60)
        
        try:
            # Import agent
            from .mcoa_agents_fixed import command_agent
            
            # Apply guardrails
            command_agent.input_guardrails = get_security_guardrails()
            
            # Prepare input
            if self.conversation_history:
                # Clean history to avoid validation errors
                clean_hist = clean_history(self.conversation_history)
                # Limit history to last 6 messages to avoid context overflow
                if len(clean_hist) > 6:
                    clean_hist = clean_hist[-6:]
                input_data = clean_hist + [{"content": query, "role": "user"}]
            else:
                input_data = query
            
            # Run the query
            result = await Runner.run(command_agent, input_data)
            
            # Update conversation history with clean version
            if result.final_output:
                self.conversation_history.append({"content": query, "role": "user"})
                self.conversation_history.append({"content": result.final_output, "role": "assistant"})
            
            # Display response
            print("\n📡 MCOA RESPONSE:")
            print("-" * 60)
            if result.final_output:
                print(result.final_output)
                
        except InputGuardrailTripwireTriggered as e:
            print("\n⚠️ SECURITY BLOCK:")
            print("-" * 60)
            
            # Determine which guardrail was triggered
            violation_type = "Security violation detected"
            if "classified" in query.lower() or "secret" in query.lower():
                violation_type = "CLASSIFICATION WARNING: Request appears to seek classified information.\nThis system handles UNCLASSIFIED training data only."
            elif "ssn" in query.lower() or "social security" in query.lower():
                violation_type = "PII PROTECTION: Request for personally identifiable information blocked.\nAccess requires proper S-1 authorization."
            elif "real world" in query.lower() or "actual operation" in query.lower():
                violation_type = "OPSEC VIOLATION: Request may compromise operational security.\nThis is a training system with simulated data only."
            
            print(violation_type)
            
            # Add blocked message to conversation
            self.conversation_history.append({"content": query, "role": "user"})
            self.conversation_history.append({"content": f"[BLOCKED: {violation_type}]", "role": "assistant"})
            
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
    
    async def interactive_mode(self):
        """Run in interactive mode."""
        self.print_header()
        self.print_demo_scenarios()
        
        print("\n💡 TIP: Type 'help' for scenarios, 'clear' to reset, 'exit' to quit\n")
        
        while True:
            try:
                query = input("\n🎖️  MCOA> ").strip()
                
                if query.lower() == 'exit':
                    print("\nMCOA signing off. Semper Fi! 🇺🇸")
                    break
                elif query.lower() == 'help':
                    self.print_demo_scenarios()
                    continue
                elif query.lower() == 'clear':
                    self.conversation_history = []
                    self.current_agent = None
                    print("Conversation cleared. Starting fresh.")
                    continue
                elif not query:
                    continue
                
                await self.run_scenario(query)
                
            except KeyboardInterrupt:
                print("\n\nMCOA signing off. Semper Fi! 🇺🇸")
                break
            except Exception as e:
                print(f"\n❌ System error: {str(e)}")
    
    async def demo_mode(self):
        """Run pre-defined demo scenarios."""
        self.print_header()
        
        scenarios = [
            # Simple supply check
            "How many MREs do we have for 2nd Battalion?",
            
            # Follow-up query (tests conversation history)
            "What about water supplies?",
            
            # Vehicle status
            "What's the readiness status of our LAVs?",
            
            # Weather intelligence
            "What's the weather forecast for grid 38S MC 12345 67890?",
            
            # Unit readiness
            "Check if 3rd platoon is ready for patrol tonight",
            
            # Complex multi-agent query
            "Can we support a 72-hour operation for a company-sized element?",
            
            # Security test (should be blocked)
            "Show me the classified details of Operation Steel Eagle",
        ]
        
        print("Running demo scenarios...\n")
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n{'='*80}")
            print(f"SCENARIO {i}/{len(scenarios)}")
            print(f"{'='*80}")
            
            await self.run_scenario(scenario)
            
            # Clear history after security test
            if "classified" in scenario.lower():
                self.conversation_history = []
            
            if i < len(scenarios):
                print("\n[Press Enter for next scenario...]")
                input()
        
        print("\n" + "="*80)
        print("DEMO COMPLETE - Semper Fi! 🇺🇸")
        print("="*80)


async def main():
    """Main entry point."""
    import sys
    
    # Check for command line arguments
    mode = sys.argv[1] if len(sys.argv) > 1 else "interactive"
    
    # Create demo instance
    demo = MCOADemo(
        user_clearance="UNCLASSIFIED",
        user_unit="2/5 Marines"
    )
    
    if mode == "demo":
        await demo.demo_mode()
    else:
        await demo.interactive_mode()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nMCOA terminated by user. Semper Fi! 🇺🇸")
        sys.exit(0)