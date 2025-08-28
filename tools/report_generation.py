"""
Military Report Generation Tools
Generates LOGSTAT, PERSTAT, SPOT reports and creates PDFs
"""

import random
import os
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel
from agents import function_tool
from .monitoring import monitor_tool

# Import PDF generation library
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab not installed. PDF generation will be limited.")


# ============== REPORT DATA MODELS ==============

class LogstatReport(BaseModel):
    """Logistics Status Report Structure"""
    report_type: str = "LOGSTAT"
    unit: str
    dtg: str
    classification: str = "UNCLASSIFIED//FOUO"
    reporting_period: str
    supply_classes: Dict[str, Dict]  # Class I-IX status
    combat_effectiveness: str  # FO/SO/MO/NO
    days_of_supply: Dict[str, int]
    shortfalls: List[str]
    projections_24h: Dict[str, str]
    projections_48h: Dict[str, str]
    projections_72h: Dict[str, str]
    narrative: str
    recommendations: List[str]
    prepared_by: str
    
    
class PerstatReport(BaseModel):
    """Personnel Status Report Structure"""
    report_type: str = "PERSTAT"
    unit: str
    dtg: str
    classification: str = "UNCLASSIFIED//FOUO"
    reporting_period: str
    authorized: int
    assigned: int
    present_for_duty: int
    on_leave: int
    sick_call: int
    awol: int
    casualties: int
    gains: int
    losses: int
    readiness_percent: float
    limiting_factors: List[str]
    narrative: str
    prepared_by: str


class SpotReport(BaseModel):
    """SPOT Report (SALUTE Format)"""
    report_type: str = "SPOT"
    unit: str
    dtg: str
    classification: str = "UNCLASSIFIED//FOUO"
    size: str  # Enemy size
    activity: str  # What they're doing
    location: str  # Grid reference
    unit_identification: str  # Enemy unit
    time_observed: str  # When seen
    equipment: str  # What they have
    narrative: str
    threat_assessment: str
    recommended_actions: List[str]
    prepared_by: str


class DecisionPackage(BaseModel):
    """Comprehensive FRAGO Decision Package"""
    frago_id: str
    dtg: str
    mission_summary: str
    go_no_go: str  # GO, NO-GO, GO WITH CAVEATS
    score: int  # 0-10 feasibility score
    constraints: List[Dict]
    required_reports: List[str]
    recommendations: List[str]
    risk_assessment: str


# ============== REPORT GENERATION TOOLS ==============

@function_tool(strict_mode=False)
@monitor_tool('generate_logstat_report', 'S-4')
def generate_logstat_report(
    unit: str,
    issue_description: str,
    supply_data: Optional[Dict] = None,
    generate_pdf: bool = False
) -> Dict:
    """
    Generate a LOGSTAT (Logistics Status) report.
    
    Args:
        unit: Unit designation
        issue_description: Description of logistics issues
        supply_data: Current supply status data
        generate_pdf: Whether to create PDF file
    
    Returns:
        Report data and optional PDF filepath
    """
    
    # Build report data
    report = LogstatReport(
        unit=unit,
        dtg=get_current_dtg(),
        reporting_period="Past 24 hours",
        supply_classes={
            "Class I (Subsistence)": {
                "on_hand": supply_data.get("mres", {}).get("quantity", 0) if supply_data else 1200,
                "required": 1500,
                "status": "AMBER"
            },
            "Class III (POL)": {
                "on_hand": supply_data.get("fuel", {}).get("quantity", 0) if supply_data else 2500,
                "required": 3000,
                "status": "RED" if "fuel" in issue_description.lower() else "GREEN"
            },
            "Class V (Ammunition)": {
                "on_hand": 15000,
                "required": 10000,
                "status": "GREEN"
            },
            "Class IX (Repair Parts)": {
                "on_hand": 85,
                "required": 100,
                "status": "AMBER"
            }
        },
        combat_effectiveness="MO" if "fuel" in issue_description.lower() else "FO",
        days_of_supply={
            "MREs": 5,
            "Fuel": 2 if "fuel" in issue_description.lower() else 7,
            "Water": 3,
            "Ammunition": 14
        },
        shortfalls=[issue_description] if issue_description else [],
        projections_24h={"status": "AMBER", "notes": "Resupply required"},
        projections_48h={"status": "RED", "notes": "Critical shortfalls expected"},
        projections_72h={"status": "BLACK", "notes": "Mission capability compromised"},
        narrative=f"[S-4 LOGISTICS] {issue_description}. Current supply posture indicates {unit} "
                 f"has LIMITED operational capability. Immediate resupply required to maintain mission readiness.",
        recommendations=[
            "Submit PRIORITY resupply request for Class III (POL)",
            "Reduce non-essential vehicle movements",
            "Implement fuel conservation measures",
            "Coordinate with adjacent units for emergency supply transfer"
        ],
        prepared_by="S-4 OPS/2nd Lt Smith"
    )
    
    result = {
        "report_type": "LOGSTAT",
        "report_data": report.dict(),
        "dtg": report.dtg,
        "unit": unit
    }
    
    # Generate PDF if requested
    if generate_pdf and REPORTLAB_AVAILABLE:
        pdf_path = create_logstat_pdf(report)
        result["pdf_path"] = pdf_path
        result["pdf_generated"] = True
    
    return result


@function_tool(strict_mode=False)
@monitor_tool('generate_perstat_report', 'S-1')
def generate_perstat_report(
    unit: str,
    personnel_issue: Optional[str] = None,
    personnel_data: Optional[Dict] = None,
    generate_pdf: bool = False
) -> Dict:
    """
    Generate a PERSTAT (Personnel Status) report.
    
    Args:
        unit: Unit designation
        personnel_issue: Description of personnel issues
        personnel_data: Current personnel status
        generate_pdf: Whether to create PDF file
    
    Returns:
        Report data and optional PDF filepath
    """
    
    # Default or provided data
    authorized = personnel_data.get("authorized", 145) if personnel_data else 145
    assigned = personnel_data.get("assigned", 138) if personnel_data else 138
    present = personnel_data.get("present", 132) if personnel_data else 132
    
    report = PerstatReport(
        unit=unit,
        dtg=get_current_dtg(),
        reporting_period="0001Z-2359Z",
        authorized=authorized,
        assigned=assigned,
        present_for_duty=present,
        on_leave=3,
        sick_call=2,
        awol=1,
        casualties=0,
        gains=0,
        losses=2 if personnel_issue else 0,
        readiness_percent=(present / authorized * 100),
        limiting_factors=[personnel_issue] if personnel_issue else ["None"],
        narrative=f"[S-1 PERSONNEL] {unit} currently at {present}/{authorized} strength. "
                 f"{personnel_issue if personnel_issue else 'Unit maintains acceptable readiness level.'}",
        prepared_by="S-1 CHIEF/SSgt Johnson"
    )
    
    result = {
        "report_type": "PERSTAT",
        "report_data": report.dict(),
        "dtg": report.dtg,
        "unit": unit,
        "readiness_percent": report.readiness_percent
    }
    
    if generate_pdf and REPORTLAB_AVAILABLE:
        pdf_path = create_perstat_pdf(report)
        result["pdf_path"] = pdf_path
        result["pdf_generated"] = True
    
    return result


@function_tool(strict_mode=False)
@monitor_tool('generate_spot_report', 'S-2')
def generate_spot_report(
    reporting_unit: str,
    size: str,
    activity: str,
    location: str,
    enemy_unit: str,
    time_observed: str,
    equipment: str,
    generate_pdf: bool = False
) -> Dict:
    """
    Generate a SPOT report using SALUTE format.
    
    Args:
        reporting_unit: Unit making the report
        size: Enemy force size
        activity: What enemy was doing
        location: Grid reference
        enemy_unit: Enemy unit identification
        time_observed: When observed
        equipment: Equipment observed
        generate_pdf: Whether to create PDF file
    
    Returns:
        Report data and optional PDF filepath
    """
    
    report = SpotReport(
        unit=reporting_unit,
        dtg=get_current_dtg(),
        size=size,
        activity=activity,
        location=location,
        unit_identification=enemy_unit,
        time_observed=time_observed,
        equipment=equipment,
        narrative=f"[S-2 INTELLIGENCE] ENEMY CONTACT. {size} observed conducting {activity} "
                 f"at grid {location} at {time_observed}. Unit assessed as {enemy_unit}. "
                 f"Equipment observed: {equipment}.",
        threat_assessment="MODERATE - Enemy presence confirmed in AO. Likely reconnaissance element.",
        recommended_actions=[
            "Increase force protection posture",
            "Deploy QRF to grid vicinity",
            "Request ISR coverage of area",
            "Alert adjacent units"
        ],
        prepared_by="S-2 WATCH/Cpl Davis"
    )
    
    result = {
        "report_type": "SPOT",
        "report_data": report.dict(),
        "dtg": report.dtg,
        "reporting_unit": reporting_unit
    }
    
    if generate_pdf and REPORTLAB_AVAILABLE:
        pdf_path = create_spot_report_pdf(report)
        result["pdf_path"] = pdf_path
        result["pdf_generated"] = True
    
    return result


@function_tool(strict_mode=False)
@monitor_tool('generate_decision_package', 'S-3')
def generate_decision_package(
    frago_id: str,
    mission_summary: str,
    assessments: Dict,
    issues: List[str],
    recommendations: List[str]
) -> Dict:
    """
    Generate comprehensive FRAGO decision package.
    
    Args:
        frago_id: FRAGO identifier
        mission_summary: Brief mission description
        assessments: Dict of various assessments
        issues: List of identified issues
        recommendations: List of recommendations
    
    Returns:
        Complete decision package
    """
    
    # Calculate feasibility score
    score = 10
    for issue in issues:
        if "fuel" in issue.lower():
            score -= 3
        if "vehicle" in issue.lower():
            score -= 2
        if "personnel" in issue.lower():
            score -= 2
    
    # Determine GO/NO-GO
    if score >= 8:
        decision = "GO"
    elif score >= 6:
        decision = "GO WITH CAVEATS"
    else:
        decision = "NO-GO"
    
    # Determine required reports based on issues
    required_reports = []
    for issue in issues:
        if "fuel" in issue.lower() or "supply" in issue.lower():
            required_reports.append("LOGSTAT")
        if "personnel" in issue.lower() or "casualty" in issue.lower():
            required_reports.append("PERSTAT")
        if "enemy" in issue.lower() or "contact" in issue.lower():
            required_reports.append("SPOT")
    
    package = DecisionPackage(
        frago_id=frago_id,
        dtg=get_current_dtg(),
        mission_summary=mission_summary,
        go_no_go=decision,
        score=score,
        constraints=[{"type": "logistics", "issue": issue} for issue in issues],
        required_reports=list(set(required_reports)),  # Remove duplicates
        recommendations=recommendations,
        risk_assessment="MODERATE" if score >= 6 else "HIGH"
    )
    
    return {
        "decision": decision,
        "package": package.dict(),
        "requires_immediate_action": decision == "NO-GO"
    }


# ============== PDF GENERATION FUNCTIONS ==============

def create_logstat_pdf(report: LogstatReport) -> str:
    """Create PDF for LOGSTAT report"""
    if not REPORTLAB_AVAILABLE:
        return None
    
    filename = f"LOGSTAT_{report.unit}_{report.dtg.replace(' ', '_').replace(':', '')}.pdf"
    filepath = f"/Users/tylerhouchin/code/demos/gpt-oss/MCOA/reports/generated/{filename}"
    
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Header
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=16,
        textColor=colors.HexColor('#000080')
    )
    
    story.append(Paragraph(f"LOGISTICS STATUS REPORT (LOGSTAT)", header_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Classification and metadata
    story.append(Paragraph(f"<b>CLASSIFICATION:</b> {report.classification}", styles['Normal']))
    story.append(Paragraph(f"<b>UNIT:</b> {report.unit}", styles['Normal']))
    story.append(Paragraph(f"<b>DTG:</b> {report.dtg}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Supply status table
    supply_data = []
    supply_data.append(['Supply Class', 'On Hand', 'Required', 'Status'])
    for class_name, data in report.supply_classes.items():
        supply_data.append([
            class_name,
            str(data.get('on_hand', 0)),
            str(data.get('required', 0)),
            data.get('status', 'UNK')
        ])
    
    supply_table = Table(supply_data, colWidths=[3*inch, 1.5*inch, 1.5*inch, 1*inch])
    supply_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(Paragraph("<b>SUPPLY STATUS:</b>", styles['Heading2']))
    story.append(supply_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Narrative and recommendations
    story.append(Paragraph("<b>ASSESSMENT:</b>", styles['Heading2']))
    story.append(Paragraph(report.narrative, styles['Normal']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("<b>RECOMMENDATIONS:</b>", styles['Heading2']))
    for rec in report.recommendations:
        story.append(Paragraph(f"• {rec}", styles['Normal']))
    
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f"<b>PREPARED BY:</b> {report.prepared_by}", styles['Normal']))
    
    # Build PDF
    doc.build(story)
    return filepath


def create_perstat_pdf(report: PerstatReport) -> str:
    """Create PDF for PERSTAT report"""
    if not REPORTLAB_AVAILABLE:
        return None
    
    filename = f"PERSTAT_{report.unit}_{report.dtg.replace(' ', '_').replace(':', '')}.pdf"
    filepath = f"/Users/tylerhouchin/code/demos/gpt-oss/MCOA/reports/generated/{filename}"
    
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Header
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=16,
        textColor=colors.HexColor('#000080')
    )
    
    story.append(Paragraph(f"PERSONNEL STATUS REPORT (PERSTAT)", header_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Metadata
    story.append(Paragraph(f"<b>CLASSIFICATION:</b> {report.classification}", styles['Normal']))
    story.append(Paragraph(f"<b>UNIT:</b> {report.unit}", styles['Normal']))
    story.append(Paragraph(f"<b>DTG:</b> {report.dtg}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Personnel table
    personnel_data = [
        ['Category', 'Count'],
        ['Authorized', str(report.authorized)],
        ['Assigned', str(report.assigned)],
        ['Present for Duty', str(report.present_for_duty)],
        ['On Leave', str(report.on_leave)],
        ['Sick Call', str(report.sick_call)],
        ['AWOL', str(report.awol)],
        ['Casualties', str(report.casualties)],
        ['Gains (24hr)', str(report.gains)],
        ['Losses (24hr)', str(report.losses)]
    ]
    
    personnel_table = Table(personnel_data, colWidths=[3*inch, 2*inch])
    personnel_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(Paragraph("<b>PERSONNEL ACCOUNTABILITY:</b>", styles['Heading2']))
    story.append(personnel_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Readiness
    story.append(Paragraph(f"<b>READINESS:</b> {report.readiness_percent:.1f}%", styles['Heading2']))
    story.append(Paragraph(report.narrative, styles['Normal']))
    
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f"<b>PREPARED BY:</b> {report.prepared_by}", styles['Normal']))
    
    doc.build(story)
    return filepath


def create_spot_report_pdf(report: SpotReport) -> str:
    """Create PDF for SPOT report"""
    if not REPORTLAB_AVAILABLE:
        return None
    
    filename = f"SPOT_{report.unit}_{report.dtg.replace(' ', '_').replace(':', '')}.pdf"
    filepath = f"/Users/tylerhouchin/code/demos/gpt-oss/MCOA/reports/generated/{filename}"
    
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Header
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading1'],
        alignment=TA_CENTER,
        fontSize=16,
        textColor=colors.HexColor('#FF0000')
    )
    
    story.append(Paragraph(f"SPOT REPORT - ENEMY CONTACT", header_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Metadata
    story.append(Paragraph(f"<b>CLASSIFICATION:</b> {report.classification}", styles['Normal']))
    story.append(Paragraph(f"<b>REPORTING UNIT:</b> {report.unit}", styles['Normal']))
    story.append(Paragraph(f"<b>DTG:</b> {report.dtg}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # SALUTE format
    salute_data = [
        ['SALUTE', 'Information'],
        ['SIZE', report.size],
        ['ACTIVITY', report.activity],
        ['LOCATION', report.location],
        ['UNIT', report.unit_identification],
        ['TIME', report.time_observed],
        ['EQUIPMENT', report.equipment]
    ]
    
    salute_table = Table(salute_data, colWidths=[1.5*inch, 5*inch])
    salute_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.red),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(salute_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Assessment and recommendations
    story.append(Paragraph("<b>THREAT ASSESSMENT:</b>", styles['Heading2']))
    story.append(Paragraph(report.threat_assessment, styles['Normal']))
    story.append(Spacer(1, 0.1*inch))
    
    story.append(Paragraph("<b>RECOMMENDED ACTIONS:</b>", styles['Heading2']))
    for action in report.recommended_actions:
        story.append(Paragraph(f"• {action}", styles['Normal']))
    
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f"<b>PREPARED BY:</b> {report.prepared_by}", styles['Normal']))
    
    doc.build(story)
    return filepath


# ============== SUBMISSION SIMULATION ==============

@function_tool(strict_mode=False)
@monitor_tool('submit_report', 'S-3')
def submit_report(
    report_type: str,
    filepath: str,
    destination: str,
    priority: str = "ROUTINE"
) -> Dict:
    """
    Simulate report submission to higher headquarters.
    
    Args:
        report_type: Type of report (LOGSTAT, PERSTAT, SPOT)
        filepath: Path to report PDF
        destination: Where to send (e.g., "Battalion S-4")
        priority: ROUTINE, PRIORITY, IMMEDIATE
    
    Returns:
        Submission confirmation
    """
    
    # In production, this would upload to a server or send via email
    # For now, simulate with confirmation
    
    confirmation_number = f"RPT-{random.randint(1000, 9999)}"
    
    return {
        "status": "SUBMITTED",
        "confirmation_number": confirmation_number,
        "report_type": report_type,
        "destination": destination,
        "priority": priority,
        "timestamp": get_current_dtg(),
        "message": f"{report_type} successfully transmitted to {destination}. "
                  f"Confirmation: {confirmation_number}. "
                  f"Receipt acknowledged by {destination} WATCHSTANDER.",
        "estimated_processing": "30 minutes" if priority == "IMMEDIATE" else "2-4 hours"
    }


# ============== UTILITY FUNCTIONS ==============

def get_current_dtg() -> str:
    """Get current date-time group in military format"""
    return datetime.utcnow().strftime("%d%H%MZ %b %y").upper()