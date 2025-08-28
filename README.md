# MCOA (Military Command Operations Assistant)

A demonstration system for military command and control operations featuring real-time data monitoring, AI-powered decision support, and automated report generation.

## Overview

MCOA simulates a military operations center by integrating multiple staff sections (S-2 Intelligence, S-3 Operations, S-4 Logistics) into a unified command dashboard. The system uses AI agents to process FRAGOs (Fragmentary Orders), assess operational feasibility, and generate standard military reports.

## Architecture

```
MCOA/
├── Core Services
│   ├── mcoa_service.py         # Main service wrapper with tool monitoring
│   ├── app.py                  # Flask web application with WebSocket support
│   └── mcoa_agents_ui.py       # AI agent configuration
│
├── Tools (Data Sources)
│   ├── tools/
│   │   ├── s2_intelligence.py  # Weather, terrain, threat assessment
│   │   ├── s3_operations.py    # Mission status, readiness, patrols
│   │   ├── s4_logistics.py     # Supply, vehicles, resupply management
│   │   ├── report_generation.py # PERSTAT, LOGSTAT, SPOT reports
│   │   └── monitoring.py       # Tool execution monitoring
│   │
│   └── testing-sensor/         # RF spectrum analysis simulation
│       ├── generate_rf_data.py # Simulated drone RF signatures
│       └── sensor/             # SpectrumGuard data files
│
├── Web Interface
│   ├── templates/
│   │   └── dashboard.html      # Real-time operations dashboard
│   └── static/
│       ├── css/dashboard.css
│       └── js/dashboard.js     # WebSocket client, real-time updates
│
└── FRAGO Processing
    └── mcoa_agents/
        └── frago_agents.py     # FRAGO interpretation and planning

```

## Current Data Sources (Simulated)

### S-2 Intelligence Section
- **Weather Data**: Temperature, wind speed/direction, visibility, precipitation
- **Terrain Analysis**: Elevation profiles, mobility assessments, key terrain features
- **Threat Assessment**: Enemy activity levels, IDF threats, pattern analysis

### S-3 Operations Section  
- **Mission Tracking**: Active operations, phase status, unit assignments
- **Unit Readiness**: Personnel strength (assigned/present/ready), equipment status
- **Patrol Management**: Routes, schedules, grid coordinates
- **Communications**: Network status (SINCGARS, HF, SATCOM, BFT)

### S-4 Logistics Section
- **Supply Inventory**: MREs, ammunition, fuel, water, medical supplies
- **Vehicle Status**: Operational rates for LAVs, HMMWVs, MTVRs
- **Resupply Pipeline**: Request tracking, priority levels, delivery ETAs

### RF Sensor Network
- **Spectrum Monitoring**: 433MHz-5.8GHz frequency bands
- **Drone Detection**: DJI Phantom, FPV racer signature profiles
- **Background RF**: WiFi, cellular, ISM band activity

## Installation

```bash
# Clone the repository
git clone [repository-url]
cd MCOA

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Access the dashboard at `http://localhost:5000`

## How It Works

1. **Data Ingestion**: Tools in the `tools/` directory simulate data from various military systems
2. **AI Processing**: The `mcoa_service.py` coordinates AI agents that analyze incoming data
3. **Real-time Monitoring**: WebSocket connections push tool executions to the dashboard
4. **Decision Support**: The system aggregates data to compute operational feasibility scores
5. **Report Generation**: Automated creation of standard military reports (PERSTAT, LOGSTAT, SPOT)

## Building Upon MCOA

### Adding New Data Sources

1. **Create a new tool module** in `tools/`:
```python
# tools/s6_communications.py
from agents import function_tool
from .monitoring import monitor_tool

@function_tool(strict_mode=False)
@monitor_tool('check_network_topology', 'S-6')
def check_network_topology(network_id: str) -> Dict:
    """Check network topology and connectivity."""
    # Your data source logic here
    return {
        "network_id": network_id,
        "nodes_online": 42,
        "bandwidth_utilization": "67%"
    }
```

2. **Register the tool** in `tools/__init__.py`:
```python
from .s6_communications import check_network_topology

ALL_TOOLS = [
    # ... existing tools ...
    check_network_topology,
]
```

### Integrating Real Data Sources

Replace simulated data with actual feeds:

```python
# Example: Integrating real weather API
import requests

@function_tool(strict_mode=False)
@monitor_tool('get_weather_conditions', 'S-2')
def get_weather_conditions(grid_reference: str) -> Dict:
    # Convert military grid to lat/lon
    lat, lon = convert_mgrs_to_latlon(grid_reference)
    
    # Call real weather API
    response = requests.get(f"https://api.weather.mil/data?lat={lat}&lon={lon}")
    data = response.json()
    
    return {
        "grid_reference": grid_reference,
        "temperature_f": data["temp"],
        "wind_speed_mph": data["wind"]["speed"],
        # ... map real data fields
    }
```

### Adding New Report Types

1. **Define the report structure** in `tools/report_generation.py`:
```python
@function_tool(strict_mode=False)
@monitor_tool('generate_medevac_report', 'Reports')
def generate_medevac_report(casualty_data: Dict) -> Dict:
    """Generate 9-Line MEDEVAC request."""
    return {
        "line_1_location": casualty_data["grid"],
        "line_2_frequency": casualty_data["freq"],
        "line_3_patients": casualty_data["priority"],
        # ... additional lines
    }
```

### Extending the Dashboard

Add new visualization components in `static/js/dashboard.js`:
```javascript
// Add new data visualization
socket.on('sensor_data', function(data) {
    updateSensorDisplay(data);
    plotSpectrumWaterfall(data.spectrum);
});

function updateSensorDisplay(data) {
    // Update UI with sensor readings
    document.getElementById('sensor-panel').innerHTML = 
        renderSensorData(data);
}
```

### Customizing AI Agents

Modify agent behavior in `mcoa_agents_ui.py`:
```python
# Add specialized agent for medical operations
medical_agent = Agent(
    instructions="""You are a medical operations specialist.
    Analyze casualty data and coordinate MEDEVAC operations.""",
    tools=[generate_medevac_report, check_landing_zones]
)
```

## API Endpoints

- `POST /api/query` - Submit operational queries
- `POST /api/frago` - Process FRAGO documents
- `GET /api/reports/generate` - Generate military reports
- `WebSocket /socket.io` - Real-time tool execution updates

## Security Considerations

- The system includes guardrails against classified information requests
- PII protection is enforced
- OPSEC violations are blocked
- All data is currently simulated - no real operational data

## Future Enhancements

- [ ] Integration with real military data systems (BFT, GCCS)
- [ ] Machine learning for pattern recognition in sensor data
- [ ] Predictive analytics for supply consumption
- [ ] Multi-domain operations (cyber, space, information)
- [ ] Coalition/joint operations support
- [ ] Offline capability for disconnected operations
- [ ] Enhanced report templates (OPORD, WARNO, CONOP)

## Contributing

To contribute new capabilities:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-capability`)
3. Add your data source or tool
4. Update tests if applicable
5. Submit a pull request

## License

[Specify your license]

## Contact

[Your contact information]

---

**Note**: This is a demonstration system using simulated data. Not for actual military operations.