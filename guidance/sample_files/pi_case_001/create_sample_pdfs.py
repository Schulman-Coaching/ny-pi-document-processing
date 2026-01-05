#!/usr/bin/env python3
"""Generate sample PI case PDFs for testing the IDP pipeline."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__)) + "/input"
os.makedirs(OUTPUT_DIR, exist_ok=True)

styles = getSampleStyleSheet()
title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=14, spaceAfter=12)
header_style = ParagraphStyle('Header', parent=styles['Heading2'], fontSize=12, spaceAfter=6)
body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, spaceAfter=6)

def create_medical_record():
    """Create a sample medical record PDF."""
    doc = SimpleDocTemplate(f"{OUTPUT_DIR}/medical_record_bellevue.pdf", pagesize=letter)
    story = []

    story.append(Paragraph("BELLEVUE HOSPITAL CENTER", title_style))
    story.append(Paragraph("462 First Avenue, New York, NY 10016", body_style))
    story.append(Paragraph("Emergency Department Medical Record", header_style))
    story.append(Spacer(1, 12))

    patient_info = [
        ["Patient Name:", "Maria Rodriguez", "DOB:", "03/15/1985"],
        ["MRN:", "BH-2024-789456", "Date of Service:", "01/15/2024"],
        ["Chief Complaint:", "Motor vehicle accident - neck and back pain", "", ""],
    ]
    t = Table(patient_info, colWidths=[1.5*inch, 2*inch, 1*inch, 2*inch])
    t.setStyle(TableStyle([('FONTSIZE', (0,0), (-1,-1), 9), ('BOTTOMPADDING', (0,0), (-1,-1), 6)]))
    story.append(t)
    story.append(Spacer(1, 12))

    story.append(Paragraph("HISTORY OF PRESENT ILLNESS:", header_style))
    story.append(Paragraph(
        "38-year-old female presents to ED via ambulance following a motor vehicle collision at the intersection "
        "of Broadway and 42nd Street, Manhattan. Patient was the restrained driver of a vehicle that was struck "
        "on the driver's side by another vehicle that ran a red light. Patient reports immediate onset of severe "
        "neck pain, lower back pain, and left shoulder pain. Denies loss of consciousness. GCS 15 at scene.",
        body_style
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("PHYSICAL EXAMINATION:", header_style))
    exam_text = """
    Vital Signs: BP 142/88, HR 96, RR 18, Temp 98.6F, SpO2 99% RA
    General: Alert, oriented x3, appears uncomfortable, in moderate distress
    HEENT: Normocephalic, atraumatic. PERRLA. No facial tenderness.
    Neck: Cervical spine tenderness at C5-C7. Decreased ROM - flexion limited to 30 degrees,
          extension limited to 15 degrees due to pain. Paraspinal muscle spasm noted.
    Back: Lumbar spine tenderness at L4-S1. Paraspinal muscle spasm. SLR positive bilaterally at 45 degrees.
    Extremities: Left shoulder tenderness over AC joint. ROM limited by pain.
    Neurological: Strength 5/5 bilateral upper and lower extremities. Sensation intact. DTRs 2+ symmetric.
    """
    story.append(Paragraph(exam_text.replace('\n', '<br/>'), body_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("DIAGNOSTIC IMAGING:", header_style))
    story.append(Paragraph(
        "CT Cervical Spine: No acute fracture or dislocation. Mild degenerative changes at C5-C6.<br/>"
        "CT Lumbar Spine: No acute fracture. L4-L5 and L5-S1 disc bulging.<br/>"
        "X-ray Left Shoulder: No acute fracture. AC joint widening suggestive of Grade I separation.",
        body_style
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("ASSESSMENT:", header_style))
    diagnoses = [
        ["1.", "Cervical strain/sprain", "ICD-10: S13.4XXA"],
        ["2.", "Lumbar strain/sprain with radiculopathy", "ICD-10: S33.5XXA, M54.16"],
        ["3.", "AC joint sprain, Grade I", "ICD-10: S43.50XA"],
        ["4.", "Post-traumatic headache", "ICD-10: G44.329"],
    ]
    t = Table(diagnoses, colWidths=[0.3*inch, 3*inch, 2*inch])
    t.setStyle(TableStyle([('FONTSIZE', (0,0), (-1,-1), 9)]))
    story.append(t)
    story.append(Spacer(1, 8))

    story.append(Paragraph("PLAN:", header_style))
    story.append(Paragraph(
        "1. Cervical collar for comfort<br/>"
        "2. Flexeril 10mg TID for muscle spasm<br/>"
        "3. Ibuprofen 800mg TID with food<br/>"
        "4. Follow up with orthopedics within 1 week<br/>"
        "5. MRI cervical and lumbar spine recommended if symptoms persist<br/>"
        "6. Patient advised no work x 2 weeks<br/>"
        "7. Return precautions given",
        body_style
    ))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Patient is unable to perform usual daily activities due to pain and limited mobility. "
                          "Prognosis for full recovery uncertain pending further evaluation.", body_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Attending Physician: James Chen, MD", body_style))
    story.append(Paragraph("Date/Time: 01/15/2024 22:45", body_style))

    doc.build(story)
    print(f"Created: {OUTPUT_DIR}/medical_record_bellevue.pdf")

def create_police_report():
    """Create a sample NYPD police report PDF."""
    doc = SimpleDocTemplate(f"{OUTPUT_DIR}/police_report_mv104.pdf", pagesize=letter)
    story = []

    story.append(Paragraph("NEW YORK CITY POLICE DEPARTMENT", title_style))
    story.append(Paragraph("MOTOR VEHICLE ACCIDENT REPORT (MV-104)", header_style))
    story.append(Spacer(1, 12))

    report_info = [
        ["Report Number:", "2024-MAN-0115-7892", "Precinct:", "Times Square (MTS)"],
        ["Date of Accident:", "01/15/2024", "Time:", "18:32"],
        ["Location:", "Broadway & W 42nd Street, Manhattan, NY", "", ""],
    ]
    t = Table(report_info, colWidths=[1.5*inch, 2.5*inch, 1*inch, 1.5*inch])
    t.setStyle(TableStyle([('FONTSIZE', (0,0), (-1,-1), 9), ('BOTTOMPADDING', (0,0), (-1,-1), 6)]))
    story.append(t)
    story.append(Spacer(1, 12))

    story.append(Paragraph("VEHICLE 1 (PLAINTIFF):", header_style))
    v1_info = [
        ["Driver:", "Maria Rodriguez", "DOB:", "03/15/1985"],
        ["Address:", "456 East 78th Street, Apt 4B, New York, NY 10075", "", ""],
        ["License:", "NY DL# 123-456-789", "State:", "NY"],
        ["Vehicle:", "2021 Honda Accord", "Plate:", "ABC-1234 (NY)"],
        ["Insurance:", "State Farm Policy #SF-2024-78901", "", ""],
        ["Damage:", "Heavy damage to driver side door and quarter panel", "", ""],
        ["Injury:", "Complaint of neck, back, and shoulder pain. Transported to Bellevue.", "", ""],
    ]
    t = Table(v1_info, colWidths=[1*inch, 3*inch, 0.8*inch, 1.7*inch])
    t.setStyle(TableStyle([('FONTSIZE', (0,0), (-1,-1), 9), ('BOTTOMPADDING', (0,0), (-1,-1), 4)]))
    story.append(t)
    story.append(Spacer(1, 10))

    story.append(Paragraph("VEHICLE 2 (AT-FAULT):", header_style))
    v2_info = [
        ["Driver:", "James Thompson", "DOB:", "07/22/1978"],
        ["Address:", "123 Main Street, Jersey City, NJ 07302", "", ""],
        ["License:", "NJ DL# T1234-56789-01234", "State:", "NJ"],
        ["Vehicle:", "2019 Ford F-150 (Commercial)", "Plate:", "XYZ-9876 (NJ)"],
        ["Insurance:", "Progressive Commercial Policy #PC-2024-45678", "", ""],
        ["Damage:", "Front bumper and hood damage", "", ""],
        ["Injury:", "None reported. Refused medical attention.", "", ""],
    ]
    t = Table(v2_info, colWidths=[1*inch, 3*inch, 0.8*inch, 1.7*inch])
    t.setStyle(TableStyle([('FONTSIZE', (0,0), (-1,-1), 9), ('BOTTOMPADDING', (0,0), (-1,-1), 4)]))
    story.append(t)
    story.append(Spacer(1, 12))

    story.append(Paragraph("NARRATIVE:", header_style))
    story.append(Paragraph(
        "On the above date and time, the undersigned officer responded to a motor vehicle collision at the "
        "intersection of Broadway and West 42nd Street. Upon arrival, observed Vehicle 1 (2021 Honda Accord) "
        "with significant driver-side damage and Vehicle 2 (2019 Ford F-150) with front-end damage.<br/><br/>"
        "Investigation revealed that Vehicle 1 was traveling westbound on 42nd Street with a green light. "
        "Vehicle 2 was traveling northbound on Broadway. Witness statements and traffic camera footage confirm "
        "that Vehicle 2 proceeded through a red traffic signal, striking Vehicle 1 in the intersection.<br/><br/>"
        "Driver of Vehicle 2 (Thompson) stated he 'thought the light was yellow' and 'didn't see the other car.' "
        "Driver appeared distracted and was observed holding a cell phone at the time of the collision.",
        body_style
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("VIOLATIONS ISSUED:", header_style))
    violations = [
        ["Vehicle 2 Driver (Thompson):", ""],
        ["", "VTL 1111(d)(1) - Failure to obey traffic control device (red light)"],
        ["", "VTL 1225-c - Use of mobile telephone while driving"],
    ]
    t = Table(violations, colWidths=[2*inch, 4.5*inch])
    t.setStyle(TableStyle([('FONTSIZE', (0,0), (-1,-1), 9)]))
    story.append(t)
    story.append(Spacer(1, 10))

    story.append(Paragraph("WITNESS INFORMATION:", header_style))
    story.append(Paragraph(
        "1. Robert Kim, pedestrian at corner, confirmed Vehicle 2 ran red light. Contact: 212-555-0147<br/>"
        "2. Sarah Johnson, driver of Vehicle 3 (stopped at light), confirmed same. Contact: 917-555-0298",
        body_style
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("FAULT DETERMINATION:", header_style))
    story.append(Paragraph(
        "Based on witness statements, physical evidence, and traffic camera footage, Vehicle 2 driver "
        "(James Thompson) is determined to be AT FAULT for this collision due to failure to obey traffic signal "
        "and distracted driving.",
        body_style
    ))
    story.append(Spacer(1, 20))

    story.append(Paragraph("Reporting Officer: P.O. Michael Davis, Shield #4521", body_style))
    story.append(Paragraph("Supervisor: Sgt. Patricia Williams, Shield #2187", body_style))
    story.append(Paragraph("Report Date: 01/15/2024", body_style))

    doc.build(story)
    print(f"Created: {OUTPUT_DIR}/police_report_mv104.pdf")

def create_insurance_policy():
    """Create a sample auto insurance policy PDF."""
    doc = SimpleDocTemplate(f"{OUTPUT_DIR}/insurance_policy_statefarm.pdf", pagesize=letter)
    story = []

    story.append(Paragraph("STATE FARM INSURANCE", title_style))
    story.append(Paragraph("Personal Auto Policy Declarations", header_style))
    story.append(Spacer(1, 12))

    policy_info = [
        ["Policy Number:", "SF-2024-78901-NY"],
        ["Policy Period:", "07/01/2023 to 07/01/2024"],
        ["Named Insured:", "Maria Rodriguez"],
        ["Address:", "456 East 78th Street, Apt 4B, New York, NY 10075"],
    ]
    t = Table(policy_info, colWidths=[1.5*inch, 5*inch])
    t.setStyle(TableStyle([('FONTSIZE', (0,0), (-1,-1), 10), ('BOTTOMPADDING', (0,0), (-1,-1), 6)]))
    story.append(t)
    story.append(Spacer(1, 12))

    story.append(Paragraph("COVERED VEHICLE:", header_style))
    vehicle_info = [
        ["Year/Make/Model:", "2021 Honda Accord EX-L"],
        ["VIN:", "1HGCV1F34MA123456"],
        ["Garaging Address:", "Same as above"],
    ]
    t = Table(vehicle_info, colWidths=[1.5*inch, 5*inch])
    t.setStyle(TableStyle([('FONTSIZE', (0,0), (-1,-1), 10)]))
    story.append(t)
    story.append(Spacer(1, 12))

    story.append(Paragraph("COVERAGE SUMMARY:", header_style))
    coverage_data = [
        ["Coverage", "Limits", "Premium"],
        ["Bodily Injury Liability", "$100,000 per person / $300,000 per accident", "$425.00"],
        ["Property Damage Liability", "$100,000 per accident", "$215.00"],
        ["Personal Injury Protection (No-Fault)", "$50,000 per person (Basic PIP)", "$385.00"],
        ["Additional PIP (Optional)", "$100,000 per person", "$125.00"],
        ["Uninsured Motorist BI", "$100,000 per person / $300,000 per accident", "$145.00"],
        ["Underinsured Motorist BI (SUM)", "$100,000 per person / $300,000 per accident", "$95.00"],
        ["Collision", "Actual Cash Value less $500 deductible", "$340.00"],
        ["Comprehensive", "Actual Cash Value less $250 deductible", "$185.00"],
        ["Medical Payments", "$10,000 per person", "$45.00"],
        ["Rental Reimbursement", "$50/day, $1,500 max", "$35.00"],
        ["", "TOTAL ANNUAL PREMIUM:", "$1,995.00"],
    ]
    t = Table(coverage_data, colWidths=[2.5*inch, 2.5*inch, 1.5*inch])
    t.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('FONTWEIGHT', (0,0), (-1,0), 'BOLD'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    story.append(Paragraph("NEW YORK MINIMUM REQUIREMENTS COMPLIANCE:", header_style))
    story.append(Paragraph(
        "This policy meets or exceeds New York State minimum requirements:<br/>"
        "✓ Bodily Injury: $25,000/$50,000 minimum - EXCEEDS<br/>"
        "✓ Property Damage: $10,000 minimum - EXCEEDS<br/>"
        "✓ Personal Injury Protection: $50,000 minimum - MEETS<br/>"
        "✓ Uninsured Motorist: $25,000/$50,000 minimum - EXCEEDS",
        body_style
    ))
    story.append(Spacer(1, 12))

    story.append(Paragraph("NO-FAULT (PIP) BENEFITS DETAIL:", header_style))
    story.append(Paragraph(
        "Basic Personal Injury Protection covers, regardless of fault:<br/>"
        "• Medical expenses up to $50,000<br/>"
        "• Lost wages (80% of gross income, up to $2,000/month for 3 years)<br/>"
        "• Other reasonable and necessary expenses up to $25/day<br/>"
        "• Death benefit of $2,000<br/><br/>"
        "Optional Additional PIP extends medical expense coverage to $100,000.",
        body_style
    ))
    story.append(Spacer(1, 20))

    story.append(Paragraph("Agent: John Smith, State Farm Agent", body_style))
    story.append(Paragraph("Agency: 789 Park Avenue, New York, NY 10021", body_style))
    story.append(Paragraph("Phone: (212) 555-0100", body_style))

    doc.build(story)
    print(f"Created: {OUTPUT_DIR}/insurance_policy_statefarm.pdf")

def create_medical_bill():
    """Create a sample medical bill PDF."""
    doc = SimpleDocTemplate(f"{OUTPUT_DIR}/medical_bill_bellevue.pdf", pagesize=letter)
    story = []

    story.append(Paragraph("BELLEVUE HOSPITAL CENTER", title_style))
    story.append(Paragraph("Patient Billing Statement", header_style))
    story.append(Spacer(1, 12))

    bill_info = [
        ["Account Number:", "BH-2024-789456-001"],
        ["Statement Date:", "02/01/2024"],
        ["Patient:", "Maria Rodriguez"],
        ["Date of Service:", "01/15/2024"],
        ["Billing Address:", "456 East 78th Street, Apt 4B, New York, NY 10075"],
    ]
    t = Table(bill_info, colWidths=[1.5*inch, 5*inch])
    t.setStyle(TableStyle([('FONTSIZE', (0,0), (-1,-1), 10), ('BOTTOMPADDING', (0,0), (-1,-1), 4)]))
    story.append(t)
    story.append(Spacer(1, 12))

    story.append(Paragraph("ITEMIZED CHARGES:", header_style))
    charges_data = [
        ["CPT Code", "Description", "Quantity", "Amount"],
        ["99285", "Emergency Dept Visit - Level 5 (High Severity)", "1", "$1,850.00"],
        ["72125", "CT Cervical Spine without Contrast", "1", "$1,200.00"],
        ["72131", "CT Lumbar Spine without Contrast", "1", "$1,200.00"],
        ["73030", "X-ray Shoulder, Complete", "1", "$285.00"],
        ["96372", "Therapeutic Injection", "2", "$180.00"],
        ["99070", "Cervical Collar Supply", "1", "$125.00"],
        ["A0427", "Ambulance Transport, Advanced Life Support", "1", "$1,450.00"],
        ["", "", "SUBTOTAL:", "$6,290.00"],
    ]
    t = Table(charges_data, colWidths=[1*inch, 3.5*inch, 0.8*inch, 1.2*inch])
    t.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('FONTWEIGHT', (0,0), (-1,0), 'BOLD'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    story.append(Paragraph("PAYMENT SUMMARY:", header_style))
    payment_data = [
        ["Total Charges:", "$6,290.00"],
        ["Insurance Payment (State Farm PIP):", "-$5,032.00"],
        ["Insurance Adjustment:", "-$628.00"],
        ["Patient Responsibility:", "$630.00"],
        ["Amount Due:", "$630.00"],
    ]
    t = Table(payment_data, colWidths=[4*inch, 1.5*inch])
    t.setStyle(TableStyle([
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('LINEABOVE', (0,-1), (-1,-1), 1, colors.black),
        ('FONTWEIGHT', (0,-1), (-1,-1), 'BOLD'),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    story.append(Paragraph("INSURANCE INFORMATION:", header_style))
    story.append(Paragraph(
        "Primary: State Farm - Policy #SF-2024-78901-NY (No-Fault/PIP)<br/>"
        "Claim Status: PAID - $5,032.00 received 01/28/2024<br/>"
        "Remaining PIP Benefits: $44,968.00",
        body_style
    ))
    story.append(Spacer(1, 12))

    story.append(Paragraph("MEDICAL LIEN NOTICE:", header_style))
    story.append(Paragraph(
        "A medical lien in the amount of $630.00 has been filed with respect to any third-party "
        "liability recovery. This lien attaches to any settlement or judgment obtained against "
        "the responsible party. Please notify our billing department of any legal representation.",
        body_style
    ))
    story.append(Spacer(1, 20))

    story.append(Paragraph("For billing inquiries: (212) 562-4141", body_style))
    story.append(Paragraph("Payment due within 30 days", body_style))

    doc.build(story)
    print(f"Created: {OUTPUT_DIR}/medical_bill_bellevue.pdf")

if __name__ == "__main__":
    print("Generating sample PI case PDFs...")
    create_medical_record()
    create_police_report()
    create_insurance_policy()
    create_medical_bill()
    print(f"\nAll PDFs created in: {OUTPUT_DIR}")
