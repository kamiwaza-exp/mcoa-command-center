#!/usr/bin/env python
"""
MCOA Demo with Visual Tool Call Logging
Shows exactly which tools are being called during agent execution
"""

import asyncio
from datetime import datetime
from agents import Runner, set_tracing_disabled, InputGuardrailTripwireTriggered
from mcoa_agents_logged import command_agent
from guardrails import get_security_guardrails

# Disable tracing for cleaner output
set_tracing_disabled(True)


class LoggedMCOADemo:
    """MCOA Demo with tool call visualization."""
    
    def __init__(self):
        self.conversation_history = []
        
    def print_header(self):
        """Print system header."""
        print("\n" + "="*80)
        print("    MARINE CORPS OPERATIONS ASSISTANT - TOOL CALL VISUALIZATION")
        print("                     UNCLASSIFIED // TRAINING")
        print("="*80)
        print(f"DTG: {datetime.now().strftime('%d%H%MZ %b %y').upper()}")
        print("Tool calls will be logged with visual indicators")
        print("="*80 + "\n")
    
    def print_legend(self):
        """Print color legend."""
        print("\n📍 TOOL CALL LEGEND:")
        print("-" * 40)
        print("🔧 \033[94mBLUE\033[0m    = S-4 Logistics Tools")
        print("🔧 \033[95mMAGENTA\033[0m = S-2 Intelligence Tools")
        print("🔧 \033[93mYELLOW\033[0m  = S-3 Operations Tools")
        print("-" * 40)
        print()
    
    async def process_query(self, query: str):
        """Process a query and show tool calls."""
        print(f"\n{'='*80}")
        print(f"🎯 USER QUERY: {query}")
        print(f"{'='*80}")
        
        try:
            # Apply guardrails
            command_agent.input_guardrails = get_security_guardrails()
            
            # Prepare input
            if self.conversation_history:
                # Clean history - only keep content and role
                clean_hist = [{"content": h.get("content", ""), "role": h.get("role", "user")} 
                             for h in self.conversation_history if h.get("content")]
                # Limit to last 4 messages
                if len(clean_hist) > 4:
                    clean_hist = clean_hist[-4:]
                input_data = clean_hist + [{"content": query, "role": "user"}]
            else:
                input_data = query
            
            print("\n⏳ Processing request...\n")
            
            # Run the agent - tool calls will be logged automatically
            result = await Runner.run(command_agent, input_data)
            
            # Update history
            if result.final_output:
                self.conversation_history.append({"content": query, "role": "user"})
                self.conversation_history.append({"content": result.final_output, "role": "assistant"})
            
            # Display response
            print(f"\n{'='*80}")
            print("📡 MCOA RESPONSE:")
            print("-" * 60)
            if result.final_output:
                # Truncate long responses for readability
                if len(result.final_output) > 500:
                    print(result.final_output[:497] + "...")
                else:
                    print(result.final_output)
            print(f"{'='*80}\n")
            
        except InputGuardrailTripwireTriggered:
            print("\n⚠️ SECURITY BLOCK: Request denied by guardrails")
            print(f"{'='*80}\n")
            
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)[:100]}")
            print(f"{'='*80}\n")
    
    async def run_demo(self):
        """Run demonstration scenarios."""
        self.print_header()
        self.print_legend()
        
        # Demo scenarios that will trigger different tools
        scenarios = [
            ("S-4 Tool Demo", "How many MREs do we have for 2nd Battalion?"),
            ("S-3 Tool Demo", "Check unit readiness for 3rd platoon"),
            ("S-2 Tool Demo", "What's the weather at grid 38S MC 12345 67890?"),
            ("Multiple Tools", "Can we support a 72-hour operation for 2nd Battalion?"),
            ("Vehicle Status", "Check LAV readiness for our unit"),
        ]
        
        print("Running demonstration scenarios...\n")
        print("Watch for the colored tool call indicators!\n")
        
        for title, query in scenarios:
            print(f"\n{'='*80}")
            print(f"📌 SCENARIO: {title}")
            print(f"{'='*80}")
            
            await self.process_query(query)
            
            # Clear history between scenarios for cleaner demo
            self.conversation_history = []
            
            print("\n[Press Enter for next scenario...]")
            input()
        
        print("\n" + "="*80)
        print("DEMO COMPLETE - Tool logging visualization successful!")
        print("="*80)
    
    async def interactive_mode(self):
        """Run in interactive mode."""
        self.print_header()
        self.print_legend()
        
        print("💡 Enter queries to see which tools are called")
        print("Commands: 'clear' to reset, 'exit' to quit\n")
        
        while True:
            try:
                query = input("\n🎖️ MCOA> ").strip()
                
                if query.lower() == 'exit':
                    print("\nSemper Fi! 🇺🇸")
                    break
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
    import sys
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "demo"
    
    demo = LoggedMCOADemo()
    
    if mode == "interactive":
        await demo.interactive_mode()
    else:
        await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())