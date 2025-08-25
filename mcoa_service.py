"""
MCOA Service Wrapper with Tool Monitoring
Integrates the MCOA agent with WebSocket event emissions
"""

import asyncio
import time
import json
from typing import Dict, Any, Callable, Optional
from functools import wraps
from datetime import datetime

from agents import Runner, set_tracing_disabled, InputGuardrailTripwireTriggered
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from guardrails import get_security_guardrails

# Import monitored tools from new structure
import tools

# Disable tracing for cleaner output
set_tracing_disabled(True)


class ToolMonitor:
    """Monitors and wraps tool execution for real-time updates."""
    
    def __init__(self, callback: Optional[Callable] = None):
        self.callback = callback
        self.active_tools = set()
        
    def wrap_tool(self, tool_func, tool_name: str, section: str):
        """Wrap a tool function to emit events."""
        
        @wraps(tool_func)
        def wrapper(*args, **kwargs):
            # Emit tool start event
            start_time = time.time()
            self.active_tools.add(tool_name)
            
            if self.callback:
                self.callback('tool_start', {
                    'tool_name': tool_name,
                    'section': section,
                    'parameters': {
                        'args': [str(arg)[:100] for arg in args],  # Truncate long args
                        'kwargs': {k: str(v)[:100] for k, v in kwargs.items()}
                    },
                    'timestamp': datetime.now().isoformat()
                })
            
            try:
                # Execute the actual tool
                result = tool_func(*args, **kwargs)
                
                # Process result for emission
                if hasattr(result, 'dict'):
                    result_data = result.dict()
                elif hasattr(result, '__dict__'):
                    result_data = result.__dict__
                elif isinstance(result, dict):
                    result_data = result
                elif isinstance(result, list):
                    result_data = {'items': result, 'count': len(result)}
                else:
                    result_data = {'value': str(result)[:500]}
                
                # Emit tool complete event
                duration = time.time() - start_time
                
                if self.callback:
                    self.callback('tool_complete', {
                        'tool_name': tool_name,
                        'section': section,
                        'duration': duration,
                        'result': result_data,
                        'success': True,
                        'timestamp': datetime.now().isoformat()
                    })
                
                return result
                
            except Exception as e:
                # Emit tool error event
                duration = time.time() - start_time
                
                if self.callback:
                    self.callback('tool_error', {
                        'tool_name': tool_name,
                        'section': section,
                        'duration': duration,
                        'error': str(e),
                        'success': False,
                        'timestamp': datetime.now().isoformat()
                    })
                
                raise
                
            finally:
                self.active_tools.discard(tool_name)
        
        # Preserve the original function attributes
        if hasattr(tool_func, '__name__'):
            wrapper.__name__ = tool_func.__name__
        elif hasattr(tool_func, 'name'):
            wrapper.__name__ = tool_func.name
        else:
            wrapper.__name__ = tool_name
            
        if hasattr(tool_func, '__doc__'):
            wrapper.__doc__ = tool_func.__doc__
            
        # Preserve function_tool decorator attributes
        if hasattr(tool_func, '_function_tool'):
            wrapper._function_tool = tool_func._function_tool
        
        # Copy over all attributes from the original function tool
        for attr in ['name', 'description', 'parameters']:
            if hasattr(tool_func, attr):
                setattr(wrapper, attr, getattr(tool_func, attr))
        
        return wrapper


class MCOAService:
    """MCOA Service with integrated tool monitoring."""
    
    def __init__(self, tool_callback: Optional[Callable] = None):
        self.tool_callback = tool_callback
        self.conversation_history = []
        
        # Set the callback for monitored tools
        tools.set_tool_callback(tool_callback)
        
        # Import and configure the command agent with monitored tools
        from mcoa_agents_ui import command_agent
        
        # Update command agent with all monitored tools
        command_agent.tools = tools.ALL_TOOLS
        
        # Apply guardrails
        command_agent.input_guardrails = get_security_guardrails()
        
        # Store reference
        self.command_agent = command_agent
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Process a query and return response with metadata."""

        def _to_text(obj: Any) -> str:
            """Convert various output types to a readable string for the UI/chat.

            - str: returned as-is
            - Pydantic v2/v1 models: dump to dict (by_alias) and JSON stringify
            - dict/list: JSON stringify
            - other: use str()
            """
            if obj is None:
                return ""
            if isinstance(obj, str):
                return obj
            try:
                # Pydantic v2
                if hasattr(obj, "model_dump") and callable(getattr(obj, "model_dump")):
                    data = obj.model_dump(by_alias=True)
                    return json.dumps(data, ensure_ascii=False, indent=2)
                # Pydantic v1
                if hasattr(obj, "dict") and callable(getattr(obj, "dict")):
                    data = obj.dict(by_alias=True)
                    return json.dumps(data, ensure_ascii=False, indent=2)
            except Exception:
                pass

            if isinstance(obj, (dict, list)):
                try:
                    return json.dumps(obj, ensure_ascii=False, indent=2)
                except Exception:
                    return str(obj)

            return str(obj)

        try:
            # Emit processing start
            if self.tool_callback:
                self.tool_callback('processing_start', {'query': query})
            
            # Prepare input
            if self.conversation_history:
                # Clean history
                clean_hist = [
                    {"content": h.get("content", ""), "role": h.get("role", "user")}
                    for h in self.conversation_history if h.get("content")
                ]
                # Limit history
                if len(clean_hist) > 6:
                    clean_hist = clean_hist[-6:]
                input_data = clean_hist + [{"content": query, "role": "user"}]
            else:
                input_data = query
            
            # Run the agent
            # Allow more tool-thought turns for complex demos
            result = await Runner.run(self.command_agent, input_data, max_turns=20)
            # Prefer a narrative field from feasibility tool if present
            final = result.final_output
            if isinstance(final, dict) and "narrative" in final:
                response_text = _to_text(final.get("narrative"))
            else:
                response_text = _to_text(final)
            
            # Update conversation history
            if response_text:
                self.conversation_history.append({"content": query, "role": "user"})
                self.conversation_history.append({"content": response_text, "role": "assistant"})
            
            # Emit processing complete
            if self.tool_callback:
                self.tool_callback('processing_complete', {
                    'query': query,
                    'response': response_text
                })
            
            return {
                'success': True,
                'response': response_text,
                'query': query,
                'timestamp': datetime.now().isoformat()
            }
            
        except InputGuardrailTripwireTriggered as e:
            # Handle guardrail blocks
            violation_msg = self._get_violation_message(query)
            
            if self.tool_callback:
                self.tool_callback('guardrail_triggered', {
                    'query': query,
                    'violation': violation_msg
                })
            
            return {
                'success': False,
                'response': f"[SECURITY BLOCK] {violation_msg}",
                'query': query,
                'guardrail_triggered': True,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            # Handle other errors
            if self.tool_callback:
                self.tool_callback('processing_error', {
                    'query': query,
                    'error': str(e)
                })
            
            return {
                'success': False,
                'response': f"Error processing query: {str(e)}",
                'query': query,
                'error': True,
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_violation_message(self, query: str) -> str:
        """Determine which guardrail was triggered."""
        query_lower = query.lower()
        
        if "classified" in query_lower or "secret" in query_lower:
            return "CLASSIFICATION WARNING: Request for classified information blocked."
        elif "ssn" in query_lower or "social security" in query_lower:
            return "PII PROTECTION: Personal information request blocked."
        elif "real world" in query_lower or "actual operation" in query_lower:
            return "OPSEC VIOLATION: Real operational data request blocked."
        else:
            return "Security violation detected."
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        
        if self.tool_callback:
            self.tool_callback('history_cleared', {
                'timestamp': datetime.now().isoformat()
            })
