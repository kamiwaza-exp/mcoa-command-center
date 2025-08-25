"""
Shared monitoring functionality for all tools
"""

import time
from datetime import datetime
from typing import Callable
from functools import wraps

# Global callback for monitoring
_tool_callback = None

def set_tool_callback(callback: Callable):
    """Set the callback function for tool monitoring."""
    global _tool_callback
    _tool_callback = callback

def monitor_tool(tool_name: str, section: str):
    """Decorator to monitor tool execution."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Emit tool start event
            start_time = time.time()
            
            if _tool_callback:
                _tool_callback('tool_start', {
                    'tool_name': tool_name,
                    'section': section,
                    'parameters': {
                        'args': [str(arg)[:100] for arg in args],
                        'kwargs': {k: str(v)[:100] for k, v in kwargs.items()}
                    },
                    'timestamp': datetime.now().isoformat()
                })
            
            try:
                # Execute the actual tool
                result = func(*args, **kwargs)
                
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
                
                if _tool_callback:
                    _tool_callback('tool_complete', {
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
                
                if _tool_callback:
                    _tool_callback('tool_error', {
                        'tool_name': tool_name,
                        'section': section,
                        'duration': duration,
                        'error': str(e),
                        'success': False,
                        'timestamp': datetime.now().isoformat()
                    })
                
                raise
        
        return wrapper
    return decorator