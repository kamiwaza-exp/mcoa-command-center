# MCOA Web UI Dashboard

A real-time web dashboard for visualizing MCOA tool executions and agent interactions.

## Features

- **Real-time Tool Monitoring**: See which tools are being called with live updates
- **Visual Tool Status**: Color-coded indicators show active, completed, and idle tools
- **Execution Timeline**: Track the sequence and duration of tool calls
- **Interactive Chat Interface**: Send queries and see responses in real-time
- **Statistics Dashboard**: Monitor session metrics and tool usage
- **Security Guardrails**: Visual indicators for security blocks
- **Military Theme**: Dark tactical interface with section-specific colors

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure your GPT-OSS model is running at `http://192.168.2.10:8000/v1`

## Running the Dashboard

### Quick Start:
```bash
cd MCOA
python run_ui.py
```

This will:
- Start the Flask server on port 5001
- Automatically open your browser to http://localhost:5001
- Begin monitoring tool executions

### Manual Start:
```bash
cd MCOA
python app.py
```
Then open http://localhost:5001 in your browser.

## Dashboard Layout

### Left Panel - Tools Monitor
- **S-2 Intelligence** (Purple): Weather, Terrain, Threats
- **S-3 Operations** (Gold): Mission, Readiness, Patrols, Comms
- **S-4 Logistics** (Blue): Supply, Vehicle, Resupply

Tool indicators:
- 🟢 Green pulse = Currently executing
- 🔴 Red flash = Just completed
- ⚫ Gray = Idle
- Badge shows call count

### Center Panel
- **Active Tool Execution**: Real-time display of current tool calls with parameters
- **Execution Timeline**: History of recent tool calls with timestamps
- **Command Interface**: Chat-style query input with response display

### Right Panel - Statistics
- Session metrics (queries, response times)
- Tool usage by section
- Guardrail status indicators
- Last tool execution details

## Quick Actions

The dashboard includes quick action buttons for common queries:
- 📦 **Check MREs**: Inventory status for 2nd Battalion
- 🌤️ **Weather**: Current conditions at grid reference
- 📊 **Readiness**: Unit readiness check for 3rd platoon
- ⏱️ **72hr Op**: Operational sustainment assessment
- 🔧 **Test All**: Run all tools sequentially
- 🗑️ **Clear**: Reset conversation history

## WebSocket Events

The dashboard uses WebSocket for real-time updates:

### Emitted Events:
- `send_query`: Send user query to agent
- `clear_conversation`: Reset history
- `test_all_tools`: Run test suite

### Received Events:
- `tool_start`: Tool execution began
- `tool_complete`: Tool finished with results
- `query_response`: Agent response ready
- `guardrail_triggered`: Security block occurred
- `stats_update`: Session statistics updated

## Color Scheme

- Background: Dark military theme (olive/gray)
- S-2 Intelligence: Purple (#9b59b6)
- S-3 Operations: Gold (#f39c12)
- S-4 Logistics: Blue (#3498db)
- Success: Green (#27ae60)
- Warning: Orange (#f39c12)
- Error: Red (#e74c3c)

## Troubleshooting

### Connection Issues
- Ensure Flask server is running
- Check that port 5000 is not in use
- Verify WebSocket connection in browser console

### Tool Monitoring Not Working
- Check that mcoa_service.py is properly wrapping tools
- Verify WebSocket events in browser developer tools
- Ensure GPT-OSS model is accessible

### Browser Compatibility
- Works best in Chrome, Firefox, Safari
- Requires JavaScript enabled
- WebSocket support required

## Development

To modify the UI:
- HTML template: `templates/dashboard.html`
- CSS styling: `static/css/dashboard.css`
- JavaScript: `static/js/dashboard.js`
- Flask backend: `app.py`
- Tool monitoring: `mcoa_service.py`

## Security Note

This is a training/demo system. Do not expose to public networks without proper authentication and security measures.

---
Semper Fi! 🇺🇸