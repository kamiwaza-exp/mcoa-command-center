#!/usr/bin/env python
"""
MCOA Flask Application with WebSocket Support
Real-time tool execution monitoring dashboard
"""

import asyncio
import json
import time
import random
import os
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, abort, make_response
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading
from queue import Queue
import uuid

# Import our MCOA components
from mcoa_service import MCOAService

# Check for PDF generation capability
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab not installed. PDF generation will be limited.")

# Discord webhook configuration (should be in env var for production)
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", 
    "https://discord.com/api/webhooks/1409985676354781324/7vt7Mf2fIjuaAeX_3Zl_7NyZponKPci9EvfSLWfIVJqHs-OIQxILoQ0Uks6cHC5kc96s")

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


# ============== DISCORD WEBHOOK ==============

def send_pdf_to_discord(pdf_path: str, report_type: str, confirmation: str):
    """Send PDF report to Discord webhook."""
    try:
        # Check if file exists
        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            return False
        
        # Prepare the message
        message = f"🎖️ **MCOA REPORT SUBMISSION**\n" \
                 f"**Type:** {report_type}\n" \
                 f"**Confirmation:** {confirmation}\n" \
                 f"**DTG:** {datetime.now().strftime('%d%H%MZ %b %y').upper()}\n" \
                 f"**Status:** TRANSMITTED TO HIGHER HQ"
        
        # Read the PDF file
        with open(pdf_path, 'rb') as f:
            files = {
                'file': (os.path.basename(pdf_path), f, 'application/pdf')
            }
            data = {
                'content': message,
                'username': 'MCOA Report Agent'
            }
            
            # Send to Discord
            response = requests.post(DISCORD_WEBHOOK_URL, data=data, files=files, timeout=30)
            response.raise_for_status()
            
        print(f"Successfully sent {report_type} to Discord")
        return True
        
    except Exception as e:
        print(f"Error sending to Discord: {e}")
        return False


# ============== FRAGO ENDPOINTS ==============

@app.route('/api/rf/data', methods=['GET'])
def get_rf_data():
    """Get RF sensor data for monitoring."""
    import os
    import json
    
    rf_data_file = os.path.join(app.root_path, 'testing-sensor', 'rf_sensor_data.jsonl')
    
    # Check if file exists, if not generate it
    if not os.path.exists(rf_data_file):
        # Generate RF data on the fly
        from testing_sensor.generate_rf_data import RFDataSimulator
        simulator = RFDataSimulator()
        messages = simulator.generate_dataset(duration_seconds=60, sample_rate=2)
        simulator.save_dataset(messages, rf_data_file)
    
    # Read and return the data
    try:
        with open(rf_data_file, 'r') as f:
            lines = f.readlines()
            data = [json.loads(line) for line in lines if json.loads(line).get('messageId') == 'SPECTRUM_DATA']
        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/rf/generate-drone-report-pdf', methods=['POST'])
def generate_drone_report_pdf():
    """Generate a PDF version of the drone detection report."""
    import io
    from datetime import datetime
    
    data = request.json
    report_text = data.get('report', '')
    drone_type = data.get('drone_type', 'Unknown UAV')
    threat_level = data.get('threat_level', 'MODERATE')
    
    if not REPORTLAB_AVAILABLE:
        # Fallback to text file download if reportlab not available
        response = make_response(report_text)
        response.headers['Content-Type'] = 'text/plain'
        response.headers['Content-Disposition'] = f'attachment; filename=drone_detection_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        return response
    
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from reportlab.platypus.tableofcontents import TableOfContents
        import re
        
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                              rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceAfter=30,
            fontName='Helvetica-Bold'
        )
        
        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.black,
            fontName='Helvetica-Bold',
            spaceAfter=6,
            spaceBefore=12
        )
        
        normal_style = ParagraphStyle(
            'NormalText',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            alignment=TA_LEFT
        )
        
        # Build PDF content
        story = []
        
        # Add classification header
        class_style = ParagraphStyle(
            'Classification',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.red,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        story.append(Paragraph("UNCLASSIFIED // TRAINING", class_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Add title
        story.append(Paragraph("DRONE DETECTION REPORT", title_style))
        
        # Add report metadata table
        threat_color = colors.red if threat_level == "HIGH" else colors.orange if threat_level == "MODERATE" else colors.green
        metadata = [
            ['Report Type:', 'RF SPECTRUM ANALYSIS'],
            ['Detection Time:', datetime.now().strftime('%d%H%MZ %b %Y').upper()],
            ['Sensor ID:', 'P11A-11210037 (CTL26)'],
            ['Threat Level:', threat_level],
            ['Drone Type:', drone_type]
        ]
        
        metadata_table = Table(metadata, colWidths=[2*inch, 3.5*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.lightgrey),
            ('TEXTCOLOR', (0,0), (0,-1), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('BACKGROUND', (1,3), (1,3), threat_color),
            ('TEXTCOLOR', (1,3), (1,3), colors.white if threat_level == "HIGH" else colors.black),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        story.append(metadata_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Function to parse markdown table
        def parse_markdown_table(lines_list):
            table_data = []
            
            for line in lines_list:
                # Skip separator lines
                if re.match(r'^[\s\|:\-]+$', line):
                    continue
                    
                # Parse table row
                if '|' in line:
                    # Split by | and clean up cells
                    cells = line.split('|')
                    # Remove empty cells at start and end
                    cleaned_cells = []
                    for cell in cells:
                        cell = cell.strip()
                        if cell:  # Only add non-empty cells
                            # Remove markdown bold markers
                            cell = cell.replace('**', '')
                            cleaned_cells.append(cell)
                    
                    if cleaned_cells:
                        table_data.append(cleaned_cells)
            
            return table_data if table_data else None
        
        # Parse the report text - handle markdown formatting
        sections = []
        current_section = {'title': '', 'content': [], 'type': 'text'}
        
        lines = report_text.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for markdown headers (## or **)
            if line.startswith('**') and line.endswith('**'):
                # Save previous section
                if current_section['title'] or current_section['content']:
                    sections.append(current_section)
                # Start new section
                title = line.strip('*').strip()
                current_section = {'title': title, 'content': [], 'type': 'text'}
            
            # Check for numbered sections
            elif re.match(r'^(\d+\.|\w+\.)\s+\*\*.*\*\*', line):
                # Save previous section
                if current_section['title'] or current_section['content']:
                    sections.append(current_section)
                # Start new section
                current_section = {'title': line.strip(), 'content': [], 'type': 'text'}
            
            # Check for table start
            elif '|' in line and i + 1 < len(lines) and '---' in lines[i + 1]:
                # This is a table
                table_lines = []
                while i < len(lines) and '|' in lines[i]:
                    table_lines.append(lines[i])
                    i += 1
                i -= 1  # Back up one since we'll increment at the end
                
                table_data = parse_markdown_table(table_lines)
                if table_data:
                    current_section['content'].append({'type': 'table', 'data': table_data})
            
            # Regular content
            elif line.strip():
                current_section['content'].append({'type': 'text', 'data': line})
            
            i += 1
        
        # Add the last section
        if current_section['title'] or current_section['content']:
            sections.append(current_section)
        
        # Create formatted sections
        for section in sections:
            # Skip empty sections
            if not section['title'] and not section['content']:
                continue
                
            # Add section header if it exists
            if section['title']:
                # Clean up section title - remove markdown formatting
                title = section['title']
                title = re.sub(r'^\d+\.\s*', '', title)  # Remove numbering
                title = title.replace('**', '')  # Remove bold markers
                story.append(Paragraph(title, section_style))
            
            # Process content items
            for item in section['content']:
                if item['type'] == 'table':
                    # Render markdown table
                    table_data = item['data']
                    if table_data:
                        # Create ReportLab table
                        pdf_table = Table(table_data, colWidths=[2.75*inch, 2.75*inch])
                        
                        # Style the table
                        table_style = [
                            ('BACKGROUND', (0,0), (-1,0), colors.grey),  # Header row
                            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),  # Header bold
                            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),  # Body normal
                            ('FONTSIZE', (0,0), (-1,-1), 10),
                            ('GRID', (0,0), (-1,-1), 1, colors.black),
                            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                            ('TOPPADDING', (0,0), (-1,-1), 6),
                        ]
                        
                        # Add alternating row colors for readability
                        for i in range(1, len(table_data)):
                            if i % 2 == 0:
                                table_style.append(('BACKGROUND', (0,i), (-1,i), colors.lightgrey))
                        
                        pdf_table.setStyle(TableStyle(table_style))
                        story.append(pdf_table)
                        story.append(Spacer(1, 0.1*inch))
                        
                elif item['type'] == 'text':
                    text = item['data']
                    
                    # Clean up text - remove markdown bold markers
                    text = text.replace('**', '')
                    
                    # Check if it's a bullet point or numbered item
                    if text.strip().startswith('-') or text.strip().startswith('•'):
                        # Create bullet point
                        bullet_text = text.strip().lstrip('-•').strip()
                        bullet_para = Paragraph(f"• {bullet_text}", normal_style)
                        story.append(bullet_para)
                    elif re.match(r'^\d+\.', text.strip()):
                        # Numbered item
                        story.append(Paragraph(text.strip(), normal_style))
                    else:
                        # Regular paragraph
                        if text.strip():
                            story.append(Paragraph(text.strip(), normal_style))
            
            story.append(Spacer(1, 0.1*inch))
        
        # Add authentication footer
        story.append(Spacer(1, 0.3*inch))
        auth_data = [
            ['Prepared By:', 'RF MONITOR SYSTEM'],
            ['Reviewed By:', 'S-2 INTELLIGENCE'],
            ['Classification:', 'UNCLASSIFIED // TRAINING'],
            ['DTG:', datetime.now().strftime('%d%H%MZ %b %Y').upper()]
        ]
        
        auth_table = Table(auth_data, colWidths=[1.5*inch, 4*inch])
        auth_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (0,-1), colors.grey),
            ('TEXTCOLOR', (0,0), (0,-1), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        story.append(auth_table)
        
        # Add classification footer
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("UNCLASSIFIED // TRAINING", class_style))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Return PDF as download
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=drone_detection_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        
        return response
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/rf/generate-drone-report', methods=['POST'])
def generate_drone_report():
    """Generate a drone detection report using LLM based on RF signature."""
    from datetime import datetime
    
    global mcoa_service
    
    # Ensure service is initialized
    if mcoa_service is None:
        mcoa_service = init_service()
    
    data = request.json
    detection = data.get('detection', {})
    spectrum = data.get('spectrum', [])
    timestamp = data.get('timestamp', datetime.now().isoformat())
    
    # Extract frequency data for analysis
    detected_frequencies = []
    for point in spectrum:
        freq = point.get('freq_mhz', 0)
        power = point.get('power_dbm', -150)
        
        # Only include significant signals
        if power > -80:
            detected_frequencies.append({
                'frequency_mhz': freq,
                'power_dbm': power
            })
    
    # Create prompt for LLM
    prompt = f"""You are a military intelligence analyst specializing in RF signal analysis and drone detection.
    
An RF sensor (P11A-11210037, CTL26 type) has detected a potential drone with the following signature:

Detection Data:
- Drone Type Identified: {detection.get('drone_type', 'Unknown')}
- Confidence Level: {detection.get('confidence', 0) * 100:.1f}%
- Detection Time: {timestamp}

RF Spectrum Analysis:
{chr(10).join([f"- {f['frequency_mhz']:.1f} MHz at {f['power_dbm']:.1f} dBm" for f in detected_frequencies])}

Key frequency bands to consider:
- 433 MHz: Long-range telemetry
- 915 MHz: Telemetry/control
- 1575 MHz: GPS L1
- 2400-2483 MHz: ISM band (WiFi/Bluetooth/drone control)
- 5725-5850 MHz: ISM band (video transmission)

Based on this RF signature data, generate a detailed DRONE DETECTION REPORT in military format that includes:

1. DETECTION SUMMARY - Type of drone, confidence, method
2. RF SIGNATURE ANALYSIS - Analyze the detected frequencies and what they indicate
3. THREAT ASSESSMENT - Estimate range based on signal strength, assess threat level
4. TECHNICAL ANALYSIS - Identify drone capabilities, vulnerabilities
5. RECOMMENDED ACTIONS - Tactical recommendations based on threat
6. COUNTERMEASURES - Specific jamming frequencies if applicable

Consider:
- Signal strength indicates range (-40 to -50 dBm is very close, -60 to -70 dBm is medium range, below -80 dBm is far)
- Presence of both 2.4GHz and 5.8GHz likely indicates consumer drone with video
- Military drones may use different frequency patterns
- FPV racers often use analog video on 5.8GHz

Format as a proper military report with DTG, classification markings, and authentication block."""

    try:
        # Get LLM response (async function needs to be awaited)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(mcoa_service.process_query(prompt))
        
        # Extract the response text
        response = result.get('response', '') if isinstance(result, dict) else str(result)
        
        # Extract threat level from response
        threat_level = "MODERATE"  # Default
        if "HIGH THREAT" in response.upper() or "HIGH RISK" in response.upper():
            threat_level = "HIGH"
        elif "LOW THREAT" in response.upper() or "LOW RISK" in response.upper():
            threat_level = "LOW"
        
        # Extract estimated range
        est_range = "Unknown"
        if "< 500" in response or "less than 500" in response.lower():
            est_range = "< 500m"
        elif "500-1000" in response or "500m-1000m" in response:
            est_range = "500-1000m"
        elif "1000-2000" in response or "1km-2km" in response:
            est_range = "1000-2000m"
        elif "> 2000" in response or "greater than 2" in response.lower():
            est_range = "> 2000m"
        
        return jsonify({
            'status': 'success',
            'report': response,
            'threat_level': threat_level,
            'estimated_range': est_range,
            'drone_type': detection.get('drone_type', 'Unknown UAV'),
            'llm_generated': True
        })
        
    except Exception as e:
        print(f"Error generating LLM report: {e}")
        # Fallback to basic report if LLM fails
        fallback_report = f"""DRONE DETECTION REPORT
DTG: {datetime.now().strftime('%d%H%MZ %b %y').upper()}
SENSOR: P11A-11210037

DETECTION ALERT:
- Type: {detection.get('drone_type', 'Unknown UAV')}
- Confidence: {detection.get('confidence', 0) * 100:.1f}%
- Time: {timestamp}

RF SIGNATURES DETECTED:
{chr(10).join([f"- {f['frequency_mhz']:.1f} MHz at {f['power_dbm']:.1f} dBm" for f in detected_frequencies])}

ASSESSMENT: Automated analysis unavailable. Manual review required.

RECOMMENDED: Maintain observation, prepare countermeasures if hostile intent confirmed.
"""
        
        return jsonify({
            'status': 'success',
            'report': fallback_report,
            'threat_level': 'MODERATE',
            'estimated_range': 'Unknown',
            'drone_type': detection.get('drone_type', 'Unknown UAV'),
            'llm_generated': False
        })


@app.route('/api/frago/fetch', methods=['GET'])
def fetch_frago():
    """Dummy endpoint that returns a static FRAGO for testing."""
    dummy_frago = {
        "frago_id": "024-2024",
        "dtg": "261200Z DEC 24",
        "from": "CO 2/5",
        "to": "3rd PLT",
        "text": """FRAGO 024-2024
DTG: 261200Z DEC 24
FROM: CO 2/5
TO: 3rd PLT

1. SITUATION: Enemy activity reported vicinity grid 38S MC 45678 12345.

2. MISSION: 3rd PLT conduct reconnaissance patrol NLT 271800Z DEC 24 
   from CP ALPHA (38S MC 12345 67890) to CP BRAVO (38S MC 45678 12345) 
   via Route GOLD to assess enemy presence and report.

3. EXECUTION: 
   a. Depart CP ALPHA 270600Z
   b. Return NLT 271800Z  
   c. Min force: 2 squads (est. 24 personnel)
   d. Report at checkpoints every 2 hours
   e. Total distance: 45km round trip

4. SERVICE SUPPORT: Draw 72hrs rations and ammo basic load.

5. COMMAND/SIGNAL: TAC 1 primary, TAC 2 alternate."""
    }
    return jsonify(dummy_frago)


@socketio.on('process_frago')
def handle_frago_processing(data):
    """Process FRAGO through interpreter agent."""
    frago_text = data.get('frago', '')
    print(f"Processing FRAGO: {frago_text[:100]}...")
    
    def process_frago_async():
        global mcoa_service
        
        # Ensure service is initialized
        if mcoa_service is None:
            mcoa_service = init_service()
        
        try:
            # Send processing status
            socketio.emit('frago_status', {
                'status': 'parsing',
                'message': 'Parsing FRAGO document...'
            })
            
            # Process through FRAGO interpreter agent
            response = asyncio.run(mcoa_service.process_frago(frago_text))
            
            # Parse response to determine required reports
            response_text = response.get('response', '')
            
            # Determine which reports are needed based on issues found
            required_reports = []
            if 'fuel' in response_text.lower() or 'supply' in response_text.lower():
                required_reports.append('LOGSTAT')
            if 'personnel' in response_text.lower() or 'casualty' in response_text.lower():
                required_reports.append('PERSTAT')
            if 'enemy' in response_text.lower() or 'threat' in response_text.lower():
                required_reports.append('SPOT')
            
            # Determine decision
            decision = 'NO-GO' if 'no-go' in response_text.lower() else 'GO'
            
            # Add decision summary to conversation context
            decision_summary = f"[FRAGO 024-2024 DECISION: {decision}]\nRequired Reports: {', '.join(required_reports) if required_reports else 'None'}"
            mcoa_service.add_context_to_history(decision_summary, "system")
            
            # Emit decision package
            socketio.emit('frago_decision_package', {
                'frago_id': '024-2024',
                'decision': decision,
                'analysis': response_text,
                'required_reports': required_reports,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"Error processing FRAGO: {e}")
            socketio.emit('frago_error', {
                'error': str(e),
                'message': 'Failed to process FRAGO'
            })
    
    # Run in background thread
    thread = threading.Thread(target=process_frago_async)
    thread.daemon = True
    thread.start()


@app.route('/api/reports/submit', methods=['POST'])
def submit_report_endpoint():
    """Dummy endpoint for report submission simulation."""
    report_data = request.json
    
    # Simulate processing delay
    time.sleep(1)
    
    # Return mock confirmation
    confirmation_number = f"RPT-{random.randint(1000, 9999)}"
    
    return jsonify({
        "status": "success",
        "confirmation": confirmation_number,
        "message": f"{report_data.get('report_type', 'Report')} submitted to {report_data.get('destination', 'HQ')}",
        "timestamp": datetime.now().strftime("%d%H%MZ %b %y").upper()
    })


@app.route('/api/reports/download/<path:filename>', methods=['GET'])
def download_report(filename):
    """Download a generated PDF report."""
    try:
        # Construct safe path to PDF file
        safe_filename = os.path.basename(filename)  # Prevent directory traversal
        file_path = os.path.join('reports', 'generated', safe_filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            abort(404, description="Report not found")
        
        # Send file with appropriate headers
        return send_file(
            file_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=safe_filename
        )
    except Exception as e:
        print(f"Error downloading report: {e}")
        abort(500, description="Error downloading report")


@socketio.on('generate_report')
def handle_report_generation(data):
    """Generate military report based on type and data."""
    report_type = data.get('report_type', '')
    report_data = data.get('data', {})
    
    print(f"Generating {report_type} report...")
    
    def generate_report_async():
        try:
            # Generate report through service WITH PDF
            if report_type == 'LOGSTAT':
                query = f"Generate LOGSTAT report for {report_data.get('unit', '3rd PLT')} with issue: {report_data.get('issue', 'fuel shortfall')} based on FRAGO 024-2024. Set generate_pdf=True to create PDF file."
            elif report_type == 'PERSTAT':
                query = f"Generate PERSTAT report for {report_data.get('unit', '3rd PLT')} based on FRAGO 024-2024. Set generate_pdf=True to create PDF file."
            elif report_type == 'SPOT':
                query = f"Generate SPOT report for enemy contact at {report_data.get('location', 'grid 38S MC 45678 12345')} related to FRAGO 024-2024. Set generate_pdf=True to create PDF file."
            else:
                query = f"Generate {report_type} report based on FRAGO 024-2024. Set generate_pdf=True to create PDF file."
            
            # Add report generation note to history
            mcoa_service.add_context_to_history(f"[GENERATING {report_type} REPORT for FRAGO 024-2024]", "system")
            
            response = asyncio.run(mcoa_service.process_query(query))
            
            # Try to extract PDF path from response
            response_text = response.get('response', '')
            pdf_path = None
            
            # Look for PDF path in the response (usually mentioned as "PDF saved to...")
            import re
            pdf_match = re.search(r'reports/generated/([A-Z]+_.*?\.pdf)', response_text)
            if pdf_match:
                pdf_path = pdf_match.group(0)
            
            # Emit report ready
            socketio.emit('report_generated', {
                'report_type': report_type,
                'content': response_text,
                'pdf_path': pdf_path,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"Error generating report: {e}")
            socketio.emit('report_error', {
                'error': str(e),
                'report_type': report_type
            })
    
    thread = threading.Thread(target=generate_report_async)
    thread.daemon = True
    thread.start()


@socketio.on('submit_report')
def handle_report_submission(data):
    """Handle report submission via WebSocket."""
    report_type = data.get('report_type', '')
    pdf_path = data.get('pdf_path', '')
    destination = data.get('destination', 'Battalion S-4')
    
    print(f"Submitting {report_type} to {destination}...")
    
    # Generate confirmation number
    confirmation = f"RPT-{random.randint(1000, 9999)}"
    
    # Send PDF to Discord if path exists
    discord_success = False
    if pdf_path:
        # Construct full path
        full_pdf_path = os.path.join('reports', 'generated', os.path.basename(pdf_path.split('/')[-1]))
        discord_success = send_pdf_to_discord(full_pdf_path, report_type, confirmation)
    
    # Add submission to conversation history
    submission_note = f"[REPORT SUBMITTED] {report_type} transmitted to {destination}. Confirmation: {confirmation}"
    if discord_success:
        submission_note += " (Discord: ✓)"
    mcoa_service.add_context_to_history(submission_note, "system")
    
    # Emit confirmation
    socketio.emit('report_submitted', {
        'report_type': report_type,
        'confirmation': confirmation,
        'destination': destination,
        'discord_sent': discord_success,
        'message': f"{report_type} successfully transmitted to {destination}. Confirmation: {confirmation}",
        'timestamp': datetime.now().strftime("%d%H%MZ %b %y").upper()
    })


if __name__ == '__main__':
    # Initialize MCOA service with event callback
    mcoa_service = init_service()
    
    print("\n" + "="*60)
    print("🎖️  MCOA COMMAND CENTER - WEB UI")
    print("="*60)
    print("Starting server at http://localhost:5001")
    print("Open your browser to view the dashboard")
    print("="*60 + "\n")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5001, allow_unsafe_werkzeug=True)
