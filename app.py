#!/usr/bin/env python
"""
MCOA Flask Application with WebSocket Support
Real-time tool execution monitoring dashboard
"""

import asyncio
import json
import time
from datetime import datetime
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading
from queue import Queue
import uuid

# Import our MCOA components
from mcoa_service import MCOAService

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mcoa-secret-key-2024'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global service instance
mcoa_service = None
message_queue = Queue()
run_histories: dict[str, dict] = {}
thread_local = threading.local()

# Initialize service on import
def init_service():
    global mcoa_service
    if mcoa_service is None:
        from mcoa_service import MCOAService
        mcoa_service = MCOAService(tool_callback=emit_tool_event)
    return mcoa_service

# Tool execution statistics
tool_stats = {
    'total_calls': 0,
    's2_calls': 0,
    's3_calls': 0,
    's4_calls': 0,
    'avg_response_time': 0,
    'total_response_time': 0,
    'session_start': None
}


@app.route('/')
def index():
    """Render the main dashboard."""
    return render_template('dashboard.html')


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print(f"Client connected: {request.sid}")
    
    # Send initial stats
    emit('stats_update', tool_stats)
    
    # Send available tools
    tools_info = {
        's2_tools': [
            {'name': 'get_weather_conditions', 'display': 'Weather', 'status': 'idle'},
            {'name': 'get_terrain_analysis', 'display': 'Terrain', 'status': 'idle'},
            {'name': 'check_threat_assessment', 'display': 'Threats', 'status': 'idle'}
        ],
        's3_tools': [
            {'name': 'get_mission_status', 'display': 'Mission', 'status': 'idle'},
            {'name': 'check_unit_readiness', 'display': 'Readiness', 'status': 'idle'},
            {'name': 'get_patrol_schedule', 'display': 'Patrols', 'status': 'idle'},
            {'name': 'check_comms_status', 'display': 'Comms', 'status': 'idle'}
        ],
        's4_tools': [
            {'name': 'check_supply_inventory', 'display': 'Supply', 'status': 'idle'},
            {'name': 'check_vehicle_status', 'display': 'Vehicle', 'status': 'idle'},
            {'name': 'request_resupply', 'display': 'Resupply', 'status': 'idle'}
        ]
    }
    emit('tools_info', tools_info)


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print(f"Client disconnected: {request.sid}")


@socketio.on('send_query')
def handle_query(data):
    """Handle incoming query from client."""
    query = data.get('query', '')
    print(f"Received query: {query}")
    
    # Start processing in background
    def process_query():
        global tool_stats, mcoa_service

        # Ensure service is initialized
        if mcoa_service is None:
            mcoa_service = init_service()
        
        # Update stats
        if tool_stats['session_start'] is None:
            tool_stats['session_start'] = datetime.now().isoformat()
        
        start_time = time.time()
        # Create a run id for this query to group tool events
        run_id = str(uuid.uuid4())
        thread_local.run_id = run_id
        run_histories[run_id] = {
            'run_id': run_id,
            'query': query,
            'start_time': datetime.now().isoformat(),
            'tools': [],  # list of {tool_name, section, start_ts, duration, parameters, result}
        }
        
        try:
            # Send processing status
            socketio.emit('query_status', {'status': 'processing', 'query': query})
            
            # Run the MCOA service
            response = asyncio.run(mcoa_service.process_query(query))
            
            # Calculate response time
            response_time = time.time() - start_time
            tool_stats['total_response_time'] += response_time
            tool_stats['total_calls'] += 1
            tool_stats['avg_response_time'] = tool_stats['total_response_time'] / tool_stats['total_calls']
            
            # Send response
            # Ensure we send a string response to the UI, not an object
            response_text = response.get('response') if isinstance(response, dict) else str(response)
            socketio.emit('query_response', {
                'query': query,
                'response': response_text,
                'response_time': response_time
            })

            # Update stats
            socketio.emit('stats_update', tool_stats)

            # Emit a run summary with the captured tool executions
            summary = run_histories.get(run_id, {})
            summary.update({
                'response_preview': (response_text or '')[:400],
                'response_time': response_time,
                'end_time': datetime.now().isoformat(),
            })
            socketio.emit('run_summary', summary)

        except Exception as e:
            print(f"Error processing query: {e}")
            socketio.emit('query_error', {'error': str(e), 'query': query})
        finally:
            # Clear thread-local run id to avoid leaking into subsequent tasks
            try:
                del thread_local.run_id
            except AttributeError:
                pass
    
    # Run in background thread
    thread = threading.Thread(target=process_query)
    thread.daemon = True
    thread.start()


@socketio.on('clear_conversation')
def handle_clear():
    """Clear conversation history."""
    global tool_stats, mcoa_service
    
    # Ensure service is initialized
    if mcoa_service is None:
        mcoa_service = init_service()
    
    if mcoa_service:
        mcoa_service.clear_history()
    
    # Reset stats
    tool_stats = {
        'total_calls': 0,
        's2_calls': 0,
        's3_calls': 0,
        's4_calls': 0,
        'avg_response_time': 0,
        'total_response_time': 0,
        'session_start': datetime.now().isoformat()
    }
    
    emit('conversation_cleared', {})
    emit('stats_update', tool_stats)


@socketio.on('test_all_tools')
def handle_test_all():
    """Test all tools with sample queries."""
    test_queries = [
        "What's the weather at grid 38S MC 12345 67890?",
        "Check unit readiness for 3rd platoon",
        "How many MREs do we have for 2nd Battalion?",
        "What's our LAV status?",
        "Check current mission status",
        "What's the threat level in sector alpha?"
    ]
    
    def run_tests():
        for i, query in enumerate(test_queries):
            time.sleep(1)  # Space out the queries
            socketio.emit('test_query', {'query': query, 'index': i})
            handle_query({'query': query})
    
    thread = threading.Thread(target=run_tests)
    thread.daemon = True
    thread.start()


def emit_tool_event(event_type, data):
    """Emit tool-related events to all connected clients."""
    global tool_stats
    
    # Update section-specific stats
    if event_type == 'tool_start':
        tool_name = data.get('tool_name', '')
        if any(tool in tool_name for tool in ['weather', 'terrain', 'threat']):
            tool_stats['s2_calls'] += 1
        elif any(tool in tool_name for tool in ['mission', 'readiness', 'patrol', 'comms']):
            tool_stats['s3_calls'] += 1
        elif any(tool in tool_name for tool in ['supply', 'vehicle', 'resupply']):
            tool_stats['s4_calls'] += 1

    # Record into current run history if present
    run_id = getattr(thread_local, 'run_id', None)
    if run_id and run_id in run_histories:
        hist = run_histories[run_id]
        tools = hist.get('tools', [])
        if event_type == 'tool_start':
            tools.append({
                'tool_name': data.get('tool_name'),
                'section': data.get('section'),
                'parameters': data.get('parameters'),
                'start_ts': datetime.now().isoformat(),
            })
        elif event_type == 'tool_complete':
            # Find last started tool with same name that has no duration yet
            for t in reversed(tools):
                if t.get('tool_name') == data.get('tool_name') and 'duration' not in t:
                    t['duration'] = data.get('duration')
                    t['result'] = data.get('result')
                    t['end_ts'] = datetime.now().isoformat()
                    break
        elif event_type == 'tool_error':
            tools.append({
                'tool_name': data.get('tool_name'),
                'section': data.get('section'),
                'error': data.get('error'),
                'start_ts': datetime.now().isoformat(),
                'duration': data.get('duration'),
                'end_ts': datetime.now().isoformat(),
            })
        hist['tools'] = tools

    # Emit the event
    socketio.emit(event_type, data)


if __name__ == '__main__':
    # Initialize MCOA service with event callback
    mcoa_service = init_service()
    
    print("\n" + "="*60)
    print("🎖️  MCOA COMMAND CENTER - WEB UI")
    print("="*60)
    print("Starting server at http://localhost:5001")
    print("Open your browser to view the dashboard")
    print("="*60 + "\n")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)
