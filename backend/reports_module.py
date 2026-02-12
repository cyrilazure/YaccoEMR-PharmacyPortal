"""
Reports Module for Yacco EMR
Handles patient visit reports, AI-assisted generation, and PDF export
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
from enum import Enum
import uuid
import os

router = APIRouter(prefix="/api/reports", tags=["Reports"])

# ============ MODELS ============
class ReportType(str, Enum):
    VISIT_SUMMARY = "visit_summary"
    DISCHARGE_SUMMARY = "discharge_summary"
    REFERRAL_LETTER = "referral_letter"
    LAB_SUMMARY = "lab_summary"
    PROGRESS_NOTE = "progress_note"

class ReportCreate(BaseModel):
    patient_id: str
    report_type: ReportType
    encounter_id: Optional[str] = None
    title: Optional[str] = None
    include_vitals: bool = True
    include_problems: bool = True
    include_medications: bool = True
    include_allergies: bool = True
    include_notes: bool = True
    include_orders: bool = True
    include_labs: bool = True
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    additional_notes: Optional[str] = None

class AIReportRequest(BaseModel):
    patient_id: str
    report_type: ReportType
    encounter_id: Optional[str] = None
    focus_areas: Optional[List[str]] = None
    additional_instructions: Optional[str] = None

class ReportResponse(BaseModel):
    id: str
    patient_id: str
    patient_name: str
    report_type: str
    title: str
    content: str
    generated_by: str
    generated_by_name: str
    ai_assisted: bool
    created_at: str
    organization_id: Optional[str] = None


def setup_routes(db, get_current_user):
    """Setup report routes with database and auth dependency"""
    
    EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')
    
    async def get_patient_data(patient_id: str, org_id: str = None):
        """Gather all patient data for report generation"""
        query = {"id": patient_id}
        if org_id:
            query["organization_id"] = org_id
        
        patient = await db.patients.find_one(query, {"_id": 0})
        if not patient:
            return None
        
        # Get related data
        vitals = await db.vitals.find({"patient_id": patient_id}, {"_id": 0}).sort("recorded_at", -1).to_list(10)
        problems = await db.problems.find({"patient_id": patient_id}, {"_id": 0}).to_list(50)
        medications = await db.medications.find({"patient_id": patient_id}, {"_id": 0}).to_list(50)
        allergies = await db.allergies.find({"patient_id": patient_id}, {"_id": 0}).to_list(50)
        notes = await db.notes.find({"patient_id": patient_id}, {"_id": 0}).sort("created_at", -1).to_list(10)
        orders = await db.orders.find({"patient_id": patient_id}, {"_id": 0}).sort("created_at", -1).to_list(20)
        lab_results = await db.lab_results.find({"patient_id": patient_id}, {"_id": 0}).sort("resulted_at", -1).to_list(10)
        
        return {
            "patient": patient,
            "vitals": vitals,
            "problems": problems,
            "medications": medications,
            "allergies": allergies,
            "notes": notes,
            "orders": orders,
            "lab_results": lab_results
        }
    
    def format_patient_data_for_report(data: dict, config: ReportCreate) -> str:
        """Format patient data into structured text for report"""
        patient = data["patient"]
        sections = []
        
        # Header
        sections.append(f"# Patient Visit Report")
        sections.append(f"**Patient:** {patient['first_name']} {patient['last_name']}")
        sections.append(f"**MRN:** {patient.get('mrn', 'N/A')}")
        sections.append(f"**DOB:** {patient.get('date_of_birth', 'N/A')}")
        sections.append(f"**Gender:** {patient.get('gender', 'N/A')}")
        sections.append(f"**Report Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}")
        sections.append("")
        
        # Vitals
        if config.include_vitals and data.get("vitals"):
            sections.append("## Vital Signs")
            latest = data["vitals"][0]
            sections.append(f"- Blood Pressure: {latest.get('blood_pressure_systolic', '--')}/{latest.get('blood_pressure_diastolic', '--')} mmHg")
            sections.append(f"- Heart Rate: {latest.get('heart_rate', '--')} bpm")
            sections.append(f"- Temperature: {latest.get('temperature', '--')}°F")
            sections.append(f"- Respiratory Rate: {latest.get('respiratory_rate', '--')} /min")
            sections.append(f"- O2 Saturation: {latest.get('oxygen_saturation', '--')}%")
            sections.append(f"- Weight: {latest.get('weight', '--')} kg")
            sections.append(f"- Height: {latest.get('height', '--')} cm")
            sections.append("")
        
        # Problems
        if config.include_problems and data.get("problems"):
            sections.append("## Active Problems/Diagnoses")
            for problem in data["problems"]:
                if problem.get("status") == "active":
                    sections.append(f"- {problem.get('name', 'Unknown')} ({problem.get('icd10_code', '')})")
            sections.append("")
        
        # Medications
        if config.include_medications and data.get("medications"):
            sections.append("## Current Medications")
            for med in data["medications"]:
                if med.get("status") == "active":
                    sections.append(f"- {med.get('name', 'Unknown')} {med.get('dosage', '')} {med.get('frequency', '')}")
            sections.append("")
        
        # Allergies
        if config.include_allergies and data.get("allergies"):
            sections.append("## Allergies")
            for allergy in data["allergies"]:
                sections.append(f"- {allergy.get('allergen', 'Unknown')} ({allergy.get('reaction', 'Unknown reaction')})")
            sections.append("")
        
        # Recent Notes
        if config.include_notes and data.get("notes"):
            sections.append("## Clinical Notes")
            for note in data["notes"][:3]:  # Last 3 notes
                sections.append(f"### {note.get('note_type', 'Note')} - {note.get('created_at', '')[:10]}")
                if note.get("subjective"):
                    sections.append(f"**Subjective:** {note['subjective']}")
                if note.get("objective"):
                    sections.append(f"**Objective:** {note['objective']}")
                if note.get("assessment"):
                    sections.append(f"**Assessment:** {note['assessment']}")
                if note.get("plan"):
                    sections.append(f"**Plan:** {note['plan']}")
                sections.append("")
        
        # Orders
        if config.include_orders and data.get("orders"):
            sections.append("## Recent Orders")
            for order in data["orders"][:10]:
                sections.append(f"- [{order.get('type', 'Order')}] {order.get('description', '')} - {order.get('status', '')}")
            sections.append("")
        
        # Lab Results
        if config.include_labs and data.get("lab_results"):
            sections.append("## Lab Results")
            for result in data["lab_results"][:5]:
                sections.append(f"### {result.get('panel_name', 'Lab')} - {result.get('resulted_at', '')[:10]}")
                for item in result.get("results", [])[:5]:
                    flag = " *" if item.get("abnormal_flag") else ""
                    sections.append(f"- {item.get('test_name', '')}: {item.get('value', '')} {item.get('unit', '')}{flag}")
                sections.append("")
        
        # Additional notes
        if config.additional_notes:
            sections.append("## Additional Notes")
            sections.append(config.additional_notes)
            sections.append("")
        
        return "\n".join(sections)
    
    # ============ REPORT GENERATION ============
    @router.post("/generate")
    async def generate_report(
        report_config: ReportCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Generate a structured patient report"""
        org_id = current_user.get("organization_id")
        
        # Get patient data
        data = await get_patient_data(report_config.patient_id, org_id if current_user.get("role") != "super_admin" else None)
        
        if not data:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Format report content
        content = format_patient_data_for_report(data, report_config)
        
        # Determine title
        title = report_config.title or f"{report_config.report_type.replace('_', ' ').title()} - {data['patient']['first_name']} {data['patient']['last_name']}"
        
        # Save report
        report_id = str(uuid.uuid4())
        report_doc = {
            "id": report_id,
            "patient_id": report_config.patient_id,
            "patient_name": f"{data['patient']['first_name']} {data['patient']['last_name']}",
            "report_type": report_config.report_type,
            "title": title,
            "content": content,
            "generated_by": current_user["id"],
            "generated_by_name": f"{current_user['first_name']} {current_user['last_name']}",
            "ai_assisted": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "organization_id": org_id
        }
        
        await db.reports.insert_one(report_doc)
        
        return {
            "message": "Report generated",
            "report_id": report_id,
            "title": title,
            "content": content
        }
    
    @router.post("/generate/ai")
    async def generate_ai_report(
        request: AIReportRequest,
        current_user: dict = Depends(get_current_user)
    ):
        """Generate AI-assisted patient report"""
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        org_id = current_user.get("organization_id")
        
        # Get patient data
        data = await get_patient_data(request.patient_id, org_id if current_user.get("role") != "super_admin" else None)
        
        if not data:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        patient = data["patient"]
        
        # Build context for AI
        context_parts = []
        context_parts.append(f"Patient: {patient['first_name']} {patient['last_name']}, DOB: {patient.get('date_of_birth', 'Unknown')}, Gender: {patient.get('gender', 'Unknown')}")
        
        if data.get("vitals"):
            latest_vitals = data["vitals"][0]
            context_parts.append(f"Latest Vitals: BP {latest_vitals.get('blood_pressure_systolic', '--')}/{latest_vitals.get('blood_pressure_diastolic', '--')}, HR {latest_vitals.get('heart_rate', '--')}, Temp {latest_vitals.get('temperature', '--')}°F, SpO2 {latest_vitals.get('oxygen_saturation', '--')}%")
        
        if data.get("problems"):
            active_problems = [p["name"] for p in data["problems"] if p.get("status") == "active"]
            if active_problems:
                context_parts.append(f"Active Problems: {', '.join(active_problems[:10])}")
        
        if data.get("medications"):
            active_meds = [f"{m['name']} {m.get('dosage', '')}" for m in data["medications"] if m.get("status") == "active"]
            if active_meds:
                context_parts.append(f"Current Medications: {', '.join(active_meds[:10])}")
        
        if data.get("allergies"):
            allergies = [a["allergen"] for a in data["allergies"]]
            if allergies:
                context_parts.append(f"Allergies: {', '.join(allergies)}")
        
        if data.get("notes"):
            recent_note = data["notes"][0]
            if recent_note.get("assessment"):
                context_parts.append(f"Recent Assessment: {recent_note['assessment'][:500]}")
            if recent_note.get("plan"):
                context_parts.append(f"Recent Plan: {recent_note['plan'][:500]}")
        
        patient_context = "\n".join(context_parts)
        
        # Build prompt based on report type
        report_prompts = {
            ReportType.VISIT_SUMMARY: "Generate a comprehensive visit summary for this patient. Include chief complaint interpretation, assessment, and follow-up recommendations.",
            ReportType.DISCHARGE_SUMMARY: "Generate a discharge summary including discharge diagnosis, hospital course summary, medications at discharge, and follow-up instructions.",
            ReportType.REFERRAL_LETTER: "Generate a professional referral letter summarizing the patient's condition and reason for referral.",
            ReportType.LAB_SUMMARY: "Generate a summary of recent laboratory findings with clinical interpretation.",
            ReportType.PROGRESS_NOTE: "Generate a progress note documenting the patient's current status and treatment progress."
        }
        
        prompt = f"""You are a medical documentation assistant helping physicians create professional clinical reports.

Patient Information:
{patient_context}

Task: {report_prompts.get(request.report_type, "Generate a clinical report for this patient.")}

{f"Focus on: {', '.join(request.focus_areas)}" if request.focus_areas else ""}
{f"Additional instructions: {request.additional_instructions}" if request.additional_instructions else ""}

Please generate a professional, HIPAA-compliant clinical report in markdown format. Include appropriate sections, be thorough but concise, and maintain clinical accuracy. Do not fabricate any information not provided in the patient data."""

        try:
            # Use emergentintegrations for AI
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"report-{request.patient_id}-{datetime.now().timestamp()}",
                system_message="You are a medical documentation AI assistant. Generate professional, accurate clinical reports based on provided patient data. Never fabricate information."
            ).with_model("openai", "gpt-5.2")
            
            user_message = UserMessage(text=prompt)
            ai_content = await chat.send_message(user_message)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")
        
        # Determine title
        title = f"AI-Assisted {request.report_type.replace('_', ' ').title()} - {patient['first_name']} {patient['last_name']}"
        
        # Save report
        report_id = str(uuid.uuid4())
        report_doc = {
            "id": report_id,
            "patient_id": request.patient_id,
            "patient_name": f"{patient['first_name']} {patient['last_name']}",
            "report_type": request.report_type,
            "title": title,
            "content": ai_content,
            "generated_by": current_user["id"],
            "generated_by_name": f"{current_user['first_name']} {current_user['last_name']}",
            "ai_assisted": True,
            "ai_model": "gpt-5.2",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "organization_id": org_id
        }
        
        await db.reports.insert_one(report_doc)
        
        return {
            "message": "AI report generated",
            "report_id": report_id,
            "title": title,
            "content": ai_content,
            "ai_assisted": True
        }
    
    # ============ REPORT CRUD ============
    @router.get("/patient/{patient_id}")
    async def get_patient_reports(
        patient_id: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Get all reports for a patient"""
        query = {"patient_id": patient_id}
        org_id = current_user.get("organization_id")
        
        if org_id and current_user.get("role") != "super_admin":
            query["organization_id"] = org_id
        
        reports = await db.reports.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
        
        return {"reports": reports, "count": len(reports)}
    
    @router.get("/{report_id}")
    async def get_report(report_id: str, current_user: dict = Depends(get_current_user)):
        """Get a specific report"""
        report = await db.reports.find_one({"id": report_id}, {"_id": 0})
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return report
    
    @router.put("/{report_id}")
    async def update_report(
        report_id: str,
        content: str,
        title: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Update report content"""
        update_data = {
            "content": content,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": current_user["id"]
        }
        
        if title:
            update_data["title"] = title
        
        result = await db.reports.update_one(
            {"id": report_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return {"message": "Report updated"}
    
    @router.delete("/{report_id}")
    async def delete_report(report_id: str, current_user: dict = Depends(get_current_user)):
        """Delete a report"""
        result = await db.reports.delete_one({"id": report_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Report not found")
        
        return {"message": "Report deleted"}
    
    # ============ PDF EXPORT ============
    @router.get("/{report_id}/pdf")
    async def export_report_pdf(report_id: str, current_user: dict = Depends(get_current_user)):
        """Export report as PDF (returns HTML for client-side PDF generation)"""
        report = await db.reports.find_one({"id": report_id}, {"_id": 0})
        
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Convert markdown to HTML
        import re
        
        content = report["content"]
        
        # Simple markdown to HTML conversion
        html_content = content
        # Headers
        html_content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)
        # Bold
        html_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_content)
        # List items
        html_content = re.sub(r'^- (.+)$', r'<li>\1</li>', html_content, flags=re.MULTILINE)
        # Paragraphs
        html_content = re.sub(r'\n\n', '</p><p>', html_content)
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{report['title']}</title>
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px;
            color: #333;
        }}
        h1 {{ color: #0ea5e9; border-bottom: 2px solid #0ea5e9; padding-bottom: 10px; }}
        h2 {{ color: #1e40af; margin-top: 30px; }}
        h3 {{ color: #374151; }}
        li {{ margin: 5px 0; }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 1px solid #e5e7eb;
            padding-bottom: 20px;
        }}
        .logo {{ font-size: 24px; font-weight: bold; color: #0ea5e9; }}
        .meta {{ color: #6b7280; font-size: 14px; }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            font-size: 12px;
            color: #6b7280;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">Yacco EMR</div>
        <div class="meta">
            Report Generated: {report['created_at'][:10]}<br>
            By: {report['generated_by_name']}
            {' (AI-Assisted)' if report.get('ai_assisted') else ''}
        </div>
    </div>
    
    <div class="content">
        <p>{html_content}</p>
    </div>
    
    <div class="footer">
        <p>This document was generated by Yacco EMR System.</p>
        <p>Report ID: {report['id']}</p>
    </div>
</body>
</html>
"""
        
        return {
            "html": html,
            "title": report["title"],
            "filename": f"report-{report['id'][:8]}.pdf"
        }
    
    # ============ REPORT TYPES ============
    @router.get("/types/list")
    async def get_report_types():
        """Get available report types"""
        return {
            "report_types": [
                {"value": "visit_summary", "label": "Visit Summary", "description": "Comprehensive summary of a patient visit"},
                {"value": "discharge_summary", "label": "Discharge Summary", "description": "Summary for patient discharge"},
                {"value": "referral_letter", "label": "Referral Letter", "description": "Professional referral to specialist"},
                {"value": "lab_summary", "label": "Lab Summary", "description": "Summary of laboratory findings"},
                {"value": "progress_note", "label": "Progress Note", "description": "Documentation of patient progress"}
            ]
        }
    
    return router
