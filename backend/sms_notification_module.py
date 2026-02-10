"""
Yacco Health SMS/WhatsApp Notification Module
Using Arkesel SMS API for Ghana
"""
import httpx
import os
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
from datetime import datetime, timezone
from enum import Enum
import urllib.parse
import asyncio

# Arkesel SMS API Configuration
ARKESEL_API_URL = "https://sms.arkesel.com/sms/api"
ARKESEL_API_KEY = os.environ.get("ARKESEL_API_KEY", "bkV2eXRmb2tXTmJMa3VDYWh6RUo")
SENDER_ID = os.environ.get("SMS_SENDER_ID", "Yaccohealth")


class NotificationType(str, Enum):
    # EMR Notifications
    APPOINTMENT_REMINDER = "appointment_reminder"
    APPOINTMENT_CONFIRMATION = "appointment_confirmation"
    APPOINTMENT_CANCELLED = "appointment_cancelled"
    LAB_RESULTS_READY = "lab_results_ready"
    PRESCRIPTION_SENT = "prescription_sent"
    DISCHARGE_SUMMARY = "discharge_summary"
    PAYMENT_CONFIRMATION = "payment_confirmation"
    
    # Pharmacy Notifications
    PRESCRIPTION_RECEIVED = "prescription_received"
    PRESCRIPTION_READY = "prescription_ready"
    PRESCRIPTION_DISPENSED = "prescription_dispensed"
    ORDER_CONFIRMATION = "order_confirmation"
    DELIVERY_UPDATE = "delivery_update"
    LOW_STOCK_ALERT = "low_stock_alert"
    SUPPLY_REQUEST_RECEIVED = "supply_request_received"
    SUPPLY_REQUEST_FULFILLED = "supply_request_fulfilled"
    
    # General
    OTP_VERIFICATION = "otp_verification"
    PASSWORD_RESET = "password_reset"
    ACCOUNT_CREATED = "account_created"
    CUSTOM = "custom"


class SMSRequest(BaseModel):
    phone_number: str
    message: str
    notification_type: Optional[NotificationType] = NotificationType.CUSTOM


class BulkSMSRequest(BaseModel):
    phone_numbers: List[str]
    message: str
    notification_type: Optional[NotificationType] = NotificationType.CUSTOM


class SMSResponse(BaseModel):
    success: bool
    message: str
    phone_number: str
    sms_id: Optional[str] = None
    error: Optional[str] = None


def format_phone_number(phone: str) -> str:
    """Format phone number for Ghana (remove spaces, ensure country code)"""
    # Remove all non-digit characters
    phone = ''.join(filter(str.isdigit, phone))
    
    # Add Ghana country code if not present
    if phone.startswith('0'):
        phone = '233' + phone[1:]
    elif not phone.startswith('233'):
        phone = '233' + phone
    
    return phone


async def send_sms(phone_number: str, message: str) -> dict:
    """
    Send SMS using Arkesel API
    Returns dict with success status and details
    """
    try:
        formatted_phone = format_phone_number(phone_number)
        
        # URL encode the message
        encoded_message = urllib.parse.quote(message)
        
        # Build the API URL
        url = f"{ARKESEL_API_URL}?action=send-sms&api_key={ARKESEL_API_KEY}&to={formatted_phone}&from={SENDER_ID}&sms={encoded_message}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            
            # Arkesel returns different response formats
            response_text = response.text
            
            # Check if successful (Arkesel typically returns "OK" or JSON)
            if response.status_code == 200:
                if "OK" in response_text.upper() or "success" in response_text.lower():
                    return {
                        "success": True,
                        "message": "SMS sent successfully",
                        "phone_number": formatted_phone,
                        "response": response_text
                    }
                else:
                    return {
                        "success": False,
                        "message": "SMS sending failed",
                        "phone_number": formatted_phone,
                        "error": response_text
                    }
            else:
                return {
                    "success": False,
                    "message": f"API returned status {response.status_code}",
                    "phone_number": formatted_phone,
                    "error": response_text
                }
                
    except httpx.TimeoutException:
        return {
            "success": False,
            "message": "SMS API timeout",
            "phone_number": phone_number,
            "error": "Request timed out"
        }
    except Exception as e:
        return {
            "success": False,
            "message": "SMS sending failed",
            "phone_number": phone_number,
            "error": str(e)
        }


async def send_bulk_sms(phone_numbers: List[str], message: str) -> List[dict]:
    """Send SMS to multiple recipients"""
    results = []
    
    # Send in parallel with a semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests
    
    async def send_with_semaphore(phone):
        async with semaphore:
            return await send_sms(phone, message)
    
    tasks = [send_with_semaphore(phone) for phone in phone_numbers]
    results = await asyncio.gather(*tasks)
    
    return results


# ============== MESSAGE TEMPLATES ==============

class SMSTemplates:
    """Pre-defined SMS templates for various notifications"""
    
    # EMR Templates
    @staticmethod
    def appointment_reminder(patient_name: str, doctor_name: str, date: str, time: str, hospital: str) -> str:
        return f"Dear {patient_name}, this is a reminder for your appointment with {doctor_name} on {date} at {time} at {hospital}. Please arrive 15 minutes early. - Yacco Health"
    
    @staticmethod
    def appointment_confirmation(patient_name: str, doctor_name: str, date: str, time: str) -> str:
        return f"Dear {patient_name}, your appointment with {doctor_name} has been confirmed for {date} at {time}. - Yacco Health"
    
    @staticmethod
    def appointment_cancelled(patient_name: str, date: str) -> str:
        return f"Dear {patient_name}, your appointment scheduled for {date} has been cancelled. Please contact us to reschedule. - Yacco Health"
    
    @staticmethod
    def lab_results_ready(patient_name: str, test_type: str) -> str:
        return f"Dear {patient_name}, your {test_type} results are now ready. Please visit the hospital or check your patient portal. - Yacco Health"
    
    @staticmethod
    def prescription_sent_to_pharmacy(patient_name: str, pharmacy_name: str) -> str:
        return f"Dear {patient_name}, your prescription has been sent to {pharmacy_name}. You will be notified when it's ready for pickup. - Yacco Health"
    
    @staticmethod
    def payment_confirmation(patient_name: str, amount: str, reference: str) -> str:
        return f"Dear {patient_name}, payment of GHS {amount} received. Ref: {reference}. Thank you for choosing Yacco Health."
    
    # Pharmacy Templates
    @staticmethod
    def prescription_received(patient_name: str, pharmacy_name: str) -> str:
        return f"Dear {patient_name}, {pharmacy_name} has received your prescription. We are preparing your medications. - Yacco Pharm"
    
    @staticmethod
    def prescription_ready(patient_name: str, pharmacy_name: str, tracking_code: str) -> str:
        return f"Dear {patient_name}, your prescription is ready for pickup at {pharmacy_name}. Tracking code: {tracking_code}. - Yacco Pharm"
    
    @staticmethod
    def prescription_dispensed(patient_name: str, pharmacy_name: str) -> str:
        return f"Dear {patient_name}, your prescription has been dispensed at {pharmacy_name}. Take medications as directed. Get well soon! - Yacco Pharm"
    
    @staticmethod
    def delivery_update(patient_name: str, status: str, tracking_code: str) -> str:
        return f"Dear {patient_name}, delivery update for order {tracking_code}: {status}. Track at yacco.health/track/{tracking_code} - Yacco Pharm"
    
    @staticmethod
    def low_stock_alert(pharmacy_name: str, drug_name: str, current_stock: int) -> str:
        return f"ALERT: {pharmacy_name} - Low stock for {drug_name}. Current: {current_stock} units. Please reorder soon. - Yacco Pharm"
    
    @staticmethod
    def supply_request_received(pharmacy_name: str, requesting_pharmacy: str, drug_name: str) -> str:
        return f"{pharmacy_name}: Supply request from {requesting_pharmacy} for {drug_name}. Please respond in your dashboard. - Yacco Pharm"
    
    @staticmethod
    def supply_request_fulfilled(pharmacy_name: str, fulfilling_pharmacy: str, drug_name: str) -> str:
        return f"{pharmacy_name}: Your supply request for {drug_name} has been fulfilled by {fulfilling_pharmacy}. - Yacco Pharm"
    
    # General Templates
    @staticmethod
    def otp_verification(otp_code: str) -> str:
        return f"Your Yacco Health verification code is: {otp_code}. Valid for 10 minutes. Do not share this code."
    
    @staticmethod
    def password_reset(reset_code: str) -> str:
        return f"Your Yacco Health password reset code is: {reset_code}. Valid for 15 minutes. If you didn't request this, ignore this message."
    
    @staticmethod
    def account_created(name: str, platform: str) -> str:
        return f"Welcome to {platform}, {name}! Your account has been created successfully. Login at yacco.health to get started."


def create_sms_router(db):
    """Create SMS notification router with database access"""
    
    router = APIRouter(prefix="/sms", tags=["SMS Notifications"])
    
    @router.post("/send", response_model=SMSResponse)
    async def send_single_sms(request: SMSRequest):
        """Send a single SMS message"""
        result = await send_sms(request.phone_number, request.message)
        
        # Log the SMS
        await db["sms_logs"].insert_one({
            "phone_number": request.phone_number,
            "message": request.message,
            "notification_type": request.notification_type,
            "success": result["success"],
            "error": result.get("error"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return SMSResponse(
            success=result["success"],
            message=result["message"],
            phone_number=result["phone_number"],
            error=result.get("error")
        )
    
    @router.post("/send-bulk")
    async def send_bulk_sms_endpoint(request: BulkSMSRequest):
        """Send SMS to multiple recipients"""
        results = await send_bulk_sms(request.phone_numbers, request.message)
        
        # Log all SMS
        for result in results:
            await db["sms_logs"].insert_one({
                "phone_number": result["phone_number"],
                "message": request.message,
                "notification_type": request.notification_type,
                "success": result["success"],
                "error": result.get("error"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        
        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful
        
        return {
            "total": len(results),
            "successful": successful,
            "failed": failed,
            "results": results
        }
    
    @router.post("/notify/appointment-reminder")
    async def send_appointment_reminder(
        phone_number: str = Body(...),
        patient_name: str = Body(...),
        doctor_name: str = Body(...),
        date: str = Body(...),
        time: str = Body(...),
        hospital: str = Body(...)
    ):
        """Send appointment reminder SMS"""
        message = SMSTemplates.appointment_reminder(patient_name, doctor_name, date, time, hospital)
        result = await send_sms(phone_number, message)
        
        await db["sms_logs"].insert_one({
            "phone_number": phone_number,
            "message": message,
            "notification_type": NotificationType.APPOINTMENT_REMINDER,
            "success": result["success"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return result
    
    @router.post("/notify/prescription-ready")
    async def send_prescription_ready(
        phone_number: str = Body(...),
        patient_name: str = Body(...),
        pharmacy_name: str = Body(...),
        tracking_code: str = Body(...)
    ):
        """Send prescription ready notification"""
        message = SMSTemplates.prescription_ready(patient_name, pharmacy_name, tracking_code)
        result = await send_sms(phone_number, message)
        
        await db["sms_logs"].insert_one({
            "phone_number": phone_number,
            "message": message,
            "notification_type": NotificationType.PRESCRIPTION_READY,
            "success": result["success"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return result
    
    @router.post("/notify/delivery-update")
    async def send_delivery_update(
        phone_number: str = Body(...),
        patient_name: str = Body(...),
        status: str = Body(...),
        tracking_code: str = Body(...)
    ):
        """Send delivery status update"""
        message = SMSTemplates.delivery_update(patient_name, status, tracking_code)
        result = await send_sms(phone_number, message)
        
        await db["sms_logs"].insert_one({
            "phone_number": phone_number,
            "message": message,
            "notification_type": NotificationType.DELIVERY_UPDATE,
            "success": result["success"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return result
    
    @router.post("/notify/low-stock")
    async def send_low_stock_alert(
        phone_number: str = Body(...),
        pharmacy_name: str = Body(...),
        drug_name: str = Body(...),
        current_stock: int = Body(...)
    ):
        """Send low stock alert to pharmacy admin"""
        message = SMSTemplates.low_stock_alert(pharmacy_name, drug_name, current_stock)
        result = await send_sms(phone_number, message)
        
        await db["sms_logs"].insert_one({
            "phone_number": phone_number,
            "message": message,
            "notification_type": NotificationType.LOW_STOCK_ALERT,
            "success": result["success"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return result
    
    @router.post("/notify/otp")
    async def send_otp(
        phone_number: str = Body(...),
        otp_code: str = Body(...)
    ):
        """Send OTP verification code"""
        message = SMSTemplates.otp_verification(otp_code)
        result = await send_sms(phone_number, message)
        
        await db["sms_logs"].insert_one({
            "phone_number": phone_number,
            "notification_type": NotificationType.OTP_VERIFICATION,
            "success": result["success"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return result
    
    @router.get("/logs")
    async def get_sms_logs(
        limit: int = 50,
        notification_type: Optional[str] = None
    ):
        """Get SMS logs"""
        query = {}
        if notification_type:
            query["notification_type"] = notification_type
        
        logs = await db["sms_logs"].find(
            query,
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        return {"logs": logs, "total": len(logs)}
    
    @router.get("/stats")
    async def get_sms_stats():
        """Get SMS statistics"""
        pipeline = [
            {
                "$group": {
                    "_id": "$notification_type",
                    "total": {"$sum": 1},
                    "successful": {"$sum": {"$cond": ["$success", 1, 0]}},
                    "failed": {"$sum": {"$cond": ["$success", 0, 1]}}
                }
            }
        ]
        
        stats = await db["sms_logs"].aggregate(pipeline).to_list(100)
        
        total_sent = sum(s["total"] for s in stats)
        total_success = sum(s["successful"] for s in stats)
        
        return {
            "total_sent": total_sent,
            "total_successful": total_success,
            "total_failed": total_sent - total_success,
            "success_rate": round((total_success / total_sent * 100) if total_sent > 0 else 0, 2),
            "by_type": stats
        }
    
    return router


# Utility functions for other modules to use
class SMSNotifier:
    """Helper class for sending notifications from other modules"""
    
    def __init__(self, db):
        self.db = db
    
    async def notify_prescription_ready(self, patient_phone: str, patient_name: str, pharmacy_name: str, tracking_code: str):
        """Notify patient that prescription is ready"""
        message = SMSTemplates.prescription_ready(patient_name, pharmacy_name, tracking_code)
        result = await send_sms(patient_phone, message)
        
        await self.db["sms_logs"].insert_one({
            "phone_number": patient_phone,
            "message": message,
            "notification_type": NotificationType.PRESCRIPTION_READY,
            "success": result["success"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return result
    
    async def notify_prescription_received(self, patient_phone: str, patient_name: str, pharmacy_name: str):
        """Notify patient that pharmacy received prescription"""
        message = SMSTemplates.prescription_received(patient_name, pharmacy_name)
        result = await send_sms(patient_phone, message)
        
        await self.db["sms_logs"].insert_one({
            "phone_number": patient_phone,
            "message": message,
            "notification_type": NotificationType.PRESCRIPTION_RECEIVED,
            "success": result["success"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return result
    
    async def notify_appointment_reminder(self, patient_phone: str, patient_name: str, doctor_name: str, date: str, time: str, hospital: str):
        """Send appointment reminder"""
        message = SMSTemplates.appointment_reminder(patient_name, doctor_name, date, time, hospital)
        result = await send_sms(patient_phone, message)
        
        await self.db["sms_logs"].insert_one({
            "phone_number": patient_phone,
            "message": message,
            "notification_type": NotificationType.APPOINTMENT_REMINDER,
            "success": result["success"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return result
    
    async def notify_lab_results(self, patient_phone: str, patient_name: str, test_type: str):
        """Notify patient that lab results are ready"""
        message = SMSTemplates.lab_results_ready(patient_name, test_type)
        result = await send_sms(patient_phone, message)
        
        await self.db["sms_logs"].insert_one({
            "phone_number": patient_phone,
            "message": message,
            "notification_type": NotificationType.LAB_RESULTS_READY,
            "success": result["success"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return result
    
    async def notify_delivery_status(self, patient_phone: str, patient_name: str, status: str, tracking_code: str):
        """Send delivery status update"""
        message = SMSTemplates.delivery_update(patient_name, status, tracking_code)
        result = await send_sms(patient_phone, message)
        
        await self.db["sms_logs"].insert_one({
            "phone_number": patient_phone,
            "message": message,
            "notification_type": NotificationType.DELIVERY_UPDATE,
            "success": result["success"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return result
    
    async def send_otp(self, phone: str, otp_code: str):
        """Send OTP code"""
        message = SMSTemplates.otp_verification(otp_code)
        result = await send_sms(phone, message)
        
        await self.db["sms_logs"].insert_one({
            "phone_number": phone,
            "notification_type": NotificationType.OTP_VERIFICATION,
            "success": result["success"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return result
    
    async def send_custom(self, phone: str, message: str, notification_type: str = "custom"):
        """Send custom SMS"""
        result = await send_sms(phone, message)
        
        await self.db["sms_logs"].insert_one({
            "phone_number": phone,
            "message": message,
            "notification_type": notification_type,
            "success": result["success"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return result
