"""
Email Notification Module for Yacco EMR
Handles transactional emails for:
- Staff account creation with temporary passwords
- Appointment reminders
- Lab results notifications
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Optional, List
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, EmailStr
import uuid

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Resend if API key is available
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")

resend_client = None
if RESEND_API_KEY:
    try:
        import resend
        resend.api_key = RESEND_API_KEY
        resend_client = resend
        logger.info("✅ Resend email service initialized")
    except ImportError:
        logger.warning("⚠️ Resend package not installed. Email notifications disabled.")
else:
    logger.warning("⚠️ RESEND_API_KEY not configured. Email notifications disabled.")

router = APIRouter(prefix="/api/email", tags=["Email Notifications"])


# ============== Pydantic Models ==============

class EmailRequest(BaseModel):
    recipient_email: EmailStr
    subject: str
    html_content: str


class StaffAccountEmail(BaseModel):
    recipient_email: EmailStr
    recipient_name: str
    hospital_name: str
    role: str
    temp_password: str
    login_url: Optional[str] = None


class AppointmentReminderEmail(BaseModel):
    recipient_email: EmailStr
    patient_name: str
    provider_name: str
    appointment_date: str
    appointment_time: str
    location: str
    appointment_type: str
    notes: Optional[str] = None


class LabResultsEmail(BaseModel):
    recipient_email: EmailStr
    patient_name: str
    test_name: str
    result_date: str
    provider_name: str
    has_abnormal_results: bool = False
    portal_url: Optional[str] = None


class EmailResponse(BaseModel):
    status: str
    message: str
    email_id: Optional[str] = None


# ============== Email Templates ==============

def get_staff_account_template(data: StaffAccountEmail) -> str:
    """Generate HTML template for staff account creation email"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc;">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <tr>
                <td>
                    <!-- Header -->
                    <table width="100%" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%); border-radius: 12px 12px 0 0; padding: 30px;">
                        <tr>
                            <td style="text-align: center;">
                                <h1 style="color: white; margin: 0; font-size: 24px;">🏥 Yacco EMR</h1>
                                <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0; font-size: 14px;">Healthcare Platform</p>
                            </td>
                        </tr>
                    </table>
                    
                    <!-- Content -->
                    <table width="100%" cellpadding="0" cellspacing="0" style="background: white; padding: 40px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <tr>
                            <td>
                                <h2 style="color: #1e293b; margin: 0 0 16px 0; font-size: 20px;">Welcome to {data.hospital_name}!</h2>
                                <p style="color: #475569; line-height: 1.6; margin: 0 0 24px 0;">
                                    Dear {data.recipient_name},
                                </p>
                                <p style="color: #475569; line-height: 1.6; margin: 0 0 24px 0;">
                                    Your staff account has been created for <strong>{data.hospital_name}</strong>. 
                                    You have been assigned the role of <strong style="color: #0ea5e9;">{data.role}</strong>.
                                </p>
                                
                                <!-- Credentials Box -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="background: #f0f9ff; border-radius: 8px; padding: 20px; margin-bottom: 24px; border-left: 4px solid #0ea5e9;">
                                    <tr>
                                        <td>
                                            <p style="color: #0369a1; font-weight: 600; margin: 0 0 12px 0;">Your Login Credentials:</p>
                                            <p style="color: #475569; margin: 0 0 8px 0;"><strong>Email:</strong> {data.recipient_email}</p>
                                            <p style="color: #475569; margin: 0;"><strong>Temporary Password:</strong> <code style="background: #e0f2fe; padding: 4px 8px; border-radius: 4px; font-family: monospace;">{data.temp_password}</code></p>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Warning Box -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="background: #fef3c7; border-radius: 8px; padding: 16px; margin-bottom: 24px; border-left: 4px solid #f59e0b;">
                                    <tr>
                                        <td>
                                            <p style="color: #92400e; margin: 0; font-size: 14px;">
                                                ⚠️ <strong>Important:</strong> Please change your password immediately after your first login for security purposes.
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- CTA Button -->
                                {f'''<table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td style="text-align: center;">
                                            <a href="{data.login_url}" style="display: inline-block; background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%); color: white; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                                                Login to Your Account →
                                            </a>
                                        </td>
                                    </tr>
                                </table>''' if data.login_url else ''}
                                
                                <p style="color: #64748b; font-size: 14px; margin: 24px 0 0 0; line-height: 1.6;">
                                    If you have any questions, please contact your hospital administrator or IT support.
                                </p>
                            </td>
                        </tr>
                    </table>
                    
                    <!-- Footer -->
                    <table width="100%" cellpadding="0" cellspacing="0" style="padding: 20px;">
                        <tr>
                            <td style="text-align: center;">
                                <p style="color: #94a3b8; font-size: 12px; margin: 0;">
                                    © 2026 Yacco EMR. All rights reserved.<br>
                                    This is an automated message. Please do not reply to this email.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


def get_appointment_reminder_template(data: AppointmentReminderEmail) -> str:
    """Generate HTML template for appointment reminder email"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc;">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <tr>
                <td>
                    <!-- Header -->
                    <table width="100%" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); border-radius: 12px 12px 0 0; padding: 30px;">
                        <tr>
                            <td style="text-align: center;">
                                <h1 style="color: white; margin: 0; font-size: 24px;">📅 Appointment Reminder</h1>
                                <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0; font-size: 14px;">Yacco EMR</p>
                            </td>
                        </tr>
                    </table>
                    
                    <!-- Content -->
                    <table width="100%" cellpadding="0" cellspacing="0" style="background: white; padding: 40px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <tr>
                            <td>
                                <h2 style="color: #1e293b; margin: 0 0 16px 0; font-size: 20px;">Hello {data.patient_name},</h2>
                                <p style="color: #475569; line-height: 1.6; margin: 0 0 24px 0;">
                                    This is a friendly reminder about your upcoming appointment.
                                </p>
                                
                                <!-- Appointment Details Box -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="background: #f0fdf4; border-radius: 8px; padding: 20px; margin-bottom: 24px; border-left: 4px solid #10b981;">
                                    <tr>
                                        <td>
                                            <p style="color: #166534; font-weight: 600; margin: 0 0 16px 0; font-size: 16px;">Appointment Details:</p>
                                            <table cellpadding="0" cellspacing="0">
                                                <tr>
                                                    <td style="padding: 4px 0; color: #64748b; width: 120px;">📆 Date:</td>
                                                    <td style="padding: 4px 0; color: #1e293b; font-weight: 500;">{data.appointment_date}</td>
                                                </tr>
                                                <tr>
                                                    <td style="padding: 4px 0; color: #64748b;">🕐 Time:</td>
                                                    <td style="padding: 4px 0; color: #1e293b; font-weight: 500;">{data.appointment_time}</td>
                                                </tr>
                                                <tr>
                                                    <td style="padding: 4px 0; color: #64748b;">👨‍⚕️ Provider:</td>
                                                    <td style="padding: 4px 0; color: #1e293b; font-weight: 500;">{data.provider_name}</td>
                                                </tr>
                                                <tr>
                                                    <td style="padding: 4px 0; color: #64748b;">📍 Location:</td>
                                                    <td style="padding: 4px 0; color: #1e293b; font-weight: 500;">{data.location}</td>
                                                </tr>
                                                <tr>
                                                    <td style="padding: 4px 0; color: #64748b;">📋 Type:</td>
                                                    <td style="padding: 4px 0; color: #1e293b; font-weight: 500;">{data.appointment_type}</td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                                
                                {f'''<table width="100%" cellpadding="0" cellspacing="0" style="background: #f8fafc; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
                                    <tr>
                                        <td>
                                            <p style="color: #64748b; margin: 0; font-size: 14px;">
                                                <strong>Notes:</strong> {data.notes}
                                            </p>
                                        </td>
                                    </tr>
                                </table>''' if data.notes else ''}
                                
                                <!-- Tips Box -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="background: #eff6ff; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
                                    <tr>
                                        <td>
                                            <p style="color: #1e40af; font-weight: 600; margin: 0 0 8px 0;">💡 Helpful Tips:</p>
                                            <ul style="color: #3b82f6; margin: 0; padding-left: 20px; line-height: 1.8;">
                                                <li>Please arrive 15 minutes early</li>
                                                <li>Bring your insurance card and ID</li>
                                                <li>Bring a list of current medications</li>
                                            </ul>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="color: #64748b; font-size: 14px; margin: 24px 0 0 0; line-height: 1.6;">
                                    Need to reschedule? Please contact us at least 24 hours in advance.
                                </p>
                            </td>
                        </tr>
                    </table>
                    
                    <!-- Footer -->
                    <table width="100%" cellpadding="0" cellspacing="0" style="padding: 20px;">
                        <tr>
                            <td style="text-align: center;">
                                <p style="color: #94a3b8; font-size: 12px; margin: 0;">
                                    © 2026 Yacco EMR. All rights reserved.<br>
                                    This is an automated reminder. Please do not reply to this email.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


def get_lab_results_template(data: LabResultsEmail) -> str:
    """Generate HTML template for lab results notification email"""
    alert_style = "background: #fef2f2; border-left: 4px solid #ef4444;" if data.has_abnormal_results else "background: #f0fdf4; border-left: 4px solid #10b981;"
    alert_text = "Some results may require attention. Please review with your healthcare provider." if data.has_abnormal_results else "Your results are within normal ranges."
    alert_icon = "⚠️" if data.has_abnormal_results else "✅"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc;">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <tr>
                <td>
                    <!-- Header -->
                    <table width="100%" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); border-radius: 12px 12px 0 0; padding: 30px;">
                        <tr>
                            <td style="text-align: center;">
                                <h1 style="color: white; margin: 0; font-size: 24px;">🔬 Lab Results Available</h1>
                                <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0 0; font-size: 14px;">Yacco EMR</p>
                            </td>
                        </tr>
                    </table>
                    
                    <!-- Content -->
                    <table width="100%" cellpadding="0" cellspacing="0" style="background: white; padding: 40px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <tr>
                            <td>
                                <h2 style="color: #1e293b; margin: 0 0 16px 0; font-size: 20px;">Hello {data.patient_name},</h2>
                                <p style="color: #475569; line-height: 1.6; margin: 0 0 24px 0;">
                                    Your lab results are now available for review.
                                </p>
                                
                                <!-- Results Info Box -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="background: #faf5ff; border-radius: 8px; padding: 20px; margin-bottom: 24px; border-left: 4px solid #8b5cf6;">
                                    <tr>
                                        <td>
                                            <p style="color: #6b21a8; font-weight: 600; margin: 0 0 12px 0;">Lab Test Information:</p>
                                            <table cellpadding="0" cellspacing="0">
                                                <tr>
                                                    <td style="padding: 4px 0; color: #64748b; width: 120px;">Test Name:</td>
                                                    <td style="padding: 4px 0; color: #1e293b; font-weight: 500;">{data.test_name}</td>
                                                </tr>
                                                <tr>
                                                    <td style="padding: 4px 0; color: #64748b;">Result Date:</td>
                                                    <td style="padding: 4px 0; color: #1e293b; font-weight: 500;">{data.result_date}</td>
                                                </tr>
                                                <tr>
                                                    <td style="padding: 4px 0; color: #64748b;">Ordered By:</td>
                                                    <td style="padding: 4px 0; color: #1e293b; font-weight: 500;">{data.provider_name}</td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Status Box -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="{alert_style} border-radius: 8px; padding: 16px; margin-bottom: 24px;">
                                    <tr>
                                        <td>
                                            <p style="color: {'#991b1b' if data.has_abnormal_results else '#166534'}; margin: 0; font-size: 14px;">
                                                {alert_icon} {alert_text}
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- CTA Button -->
                                {f'''<table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td style="text-align: center;">
                                            <a href="{data.portal_url}" style="display: inline-block; background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%); color: white; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                                                View Full Results →
                                            </a>
                                        </td>
                                    </tr>
                                </table>''' if data.portal_url else ''}
                                
                                <p style="color: #64748b; font-size: 14px; margin: 24px 0 0 0; line-height: 1.6;">
                                    If you have questions about your results, please contact your healthcare provider.
                                </p>
                            </td>
                        </tr>
                    </table>
                    
                    <!-- Footer -->
                    <table width="100%" cellpadding="0" cellspacing="0" style="padding: 20px;">
                        <tr>
                            <td style="text-align: center;">
                                <p style="color: #94a3b8; font-size: 12px; margin: 0;">
                                    © 2026 Yacco EMR. All rights reserved.<br>
                                    This is an automated notification. Please do not reply to this email.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


# ============== Email Sending Functions ==============

async def send_email_async(to_email: str, subject: str, html_content: str) -> Optional[str]:
    """
    Send email asynchronously using Resend API
    Returns email ID on success, None on failure
    """
    if not resend_client:
        logger.warning("Email service not available. Skipping email send.")
        return None
    
    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        
        # Run sync SDK in thread to keep FastAPI non-blocking
        email = await asyncio.to_thread(resend_client.Emails.send, params)
        email_id = email.get("id") if isinstance(email, dict) else None
        logger.info(f"✅ Email sent successfully to {to_email} (ID: {email_id})")
        return email_id
    except Exception as e:
        logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
        return None


# ============== Public API Functions ==============

async def send_staff_account_email(data: StaffAccountEmail) -> bool:
    """Send staff account creation email with temporary password"""
    html_content = get_staff_account_template(data)
    subject = f"🏥 Welcome to {data.hospital_name} - Your Account Has Been Created"
    
    email_id = await send_email_async(data.recipient_email, subject, html_content)
    return email_id is not None


async def send_appointment_reminder(data: AppointmentReminderEmail) -> bool:
    """Send appointment reminder email to patient"""
    html_content = get_appointment_reminder_template(data)
    subject = f"📅 Appointment Reminder - {data.appointment_date} at {data.appointment_time}"
    
    email_id = await send_email_async(data.recipient_email, subject, html_content)
    return email_id is not None


async def send_lab_results_notification(data: LabResultsEmail) -> bool:
    """Send lab results notification email to patient"""
    html_content = get_lab_results_template(data)
    subject = f"🔬 Lab Results Available - {data.test_name}"
    
    email_id = await send_email_async(data.recipient_email, subject, html_content)
    return email_id is not None


# ============== API Endpoints ==============

@router.get("/status")
async def get_email_service_status():
    """Check email service status"""
    return {
        "service": "email",
        "status": "active" if resend_client else "inactive",
        "provider": "Resend" if resend_client else None,
        "sender_email": SENDER_EMAIL if resend_client else None,
        "message": "Email service is ready" if resend_client else "Email service not configured. Set RESEND_API_KEY in environment."
    }


@router.post("/send", response_model=EmailResponse)
async def send_generic_email(request: EmailRequest):
    """Send a generic email (admin use only)"""
    if not resend_client:
        raise HTTPException(status_code=503, detail="Email service not configured")
    
    email_id = await send_email_async(
        request.recipient_email,
        request.subject,
        request.html_content
    )
    
    if email_id:
        return EmailResponse(
            status="success",
            message=f"Email sent to {request.recipient_email}",
            email_id=email_id
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to send email")


@router.post("/staff-account", response_model=EmailResponse)
async def send_staff_account_notification(data: StaffAccountEmail):
    """Send staff account creation email"""
    if not resend_client:
        raise HTTPException(status_code=503, detail="Email service not configured")
    
    success = await send_staff_account_email(data)
    
    if success:
        return EmailResponse(
            status="success",
            message=f"Staff account email sent to {data.recipient_email}"
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to send staff account email")


@router.post("/appointment-reminder", response_model=EmailResponse)
async def send_appointment_reminder_endpoint(data: AppointmentReminderEmail):
    """Send appointment reminder email"""
    if not resend_client:
        raise HTTPException(status_code=503, detail="Email service not configured")
    
    success = await send_appointment_reminder(data)
    
    if success:
        return EmailResponse(
            status="success",
            message=f"Appointment reminder sent to {data.recipient_email}"
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to send appointment reminder")


@router.post("/lab-results", response_model=EmailResponse)
async def send_lab_results_endpoint(data: LabResultsEmail):
    """Send lab results notification email"""
    if not resend_client:
        raise HTTPException(status_code=503, detail="Email service not configured")
    
    success = await send_lab_results_notification(data)
    
    if success:
        return EmailResponse(
            status="success",
            message=f"Lab results notification sent to {data.recipient_email}"
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to send lab results notification")
