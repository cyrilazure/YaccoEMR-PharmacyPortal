"""
Billing Module for Yacco EMR
Handles invoices, payments via Paystack, and insurance claims
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid
import hmac
import hashlib
import os
import requests

router = APIRouter(prefix="/api/billing", tags=["Billing"])

# ============ ENUMS ============
class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class PaymentMethod(str, Enum):
    CASH = "cash"
    CARD = "card"
    PAYSTACK = "paystack"
    INSURANCE = "insurance"
    BANK_TRANSFER = "bank_transfer"

class ClaimStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    PARTIAL = "partial"

# ============ MODELS ============
class LineItem(BaseModel):
    description: str
    service_code: Optional[str] = None  # CPT code
    quantity: int = 1
    unit_price: float
    discount: float = 0

class InvoiceCreate(BaseModel):
    patient_id: str
    patient_name: str
    encounter_id: Optional[str] = None
    line_items: List[LineItem]
    notes: Optional[str] = None
    due_date: Optional[str] = None
    insurance_id: Optional[str] = None

class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    patient_id: str
    patient_name: str
    encounter_id: Optional[str] = None
    line_items: List[dict]
    subtotal: float
    discount: float
    tax: float
    total: float
    amount_paid: float
    balance_due: float
    status: str
    notes: Optional[str] = None
    due_date: str
    created_at: str
    paid_at: Optional[str] = None
    organization_id: Optional[str] = None

class PaymentCreate(BaseModel):
    invoice_id: str
    amount: float
    payment_method: PaymentMethod
    reference: Optional[str] = None
    notes: Optional[str] = None

class InsuranceClaimCreate(BaseModel):
    invoice_id: str
    patient_id: str
    insurance_provider: str
    insurance_id: str
    subscriber_name: str
    subscriber_id: str
    diagnosis_codes: List[str]  # ICD-10 codes
    procedure_codes: List[str]  # CPT codes

# ============ SERVICE CODES ============
SERVICE_CODES = {
    # Office Visits
    "99201": {"description": "Office visit, new patient, minimal", "price": 50.00},
    "99202": {"description": "Office visit, new patient, low", "price": 90.00},
    "99203": {"description": "Office visit, new patient, moderate", "price": 130.00},
    "99204": {"description": "Office visit, new patient, moderate-high", "price": 190.00},
    "99205": {"description": "Office visit, new patient, high", "price": 250.00},
    "99211": {"description": "Office visit, established, minimal", "price": 30.00},
    "99212": {"description": "Office visit, established, low", "price": 60.00},
    "99213": {"description": "Office visit, established, moderate", "price": 100.00},
    "99214": {"description": "Office visit, established, moderate-high", "price": 150.00},
    "99215": {"description": "Office visit, established, high", "price": 200.00},
    
    # Lab Tests
    "80053": {"description": "Comprehensive metabolic panel", "price": 45.00},
    "85025": {"description": "Complete blood count (CBC)", "price": 35.00},
    "80061": {"description": "Lipid panel", "price": 40.00},
    "84443": {"description": "TSH (thyroid)", "price": 55.00},
    "82947": {"description": "Glucose, blood", "price": 20.00},
    "81001": {"description": "Urinalysis", "price": 25.00},
    
    # Imaging
    "71046": {"description": "Chest X-ray, 2 views", "price": 150.00},
    "73030": {"description": "Shoulder X-ray", "price": 120.00},
    "73600": {"description": "Ankle X-ray", "price": 110.00},
    "70553": {"description": "MRI brain with contrast", "price": 1200.00},
    "74177": {"description": "CT abdomen/pelvis with contrast", "price": 800.00},
    
    # Procedures
    "12001": {"description": "Simple wound repair", "price": 180.00},
    "69210": {"description": "Ear wax removal", "price": 75.00},
    "17110": {"description": "Wart destruction", "price": 150.00},
    "20610": {"description": "Joint injection, major", "price": 200.00},
    
    # Telehealth
    "99441": {"description": "Telehealth E/M, 5-10 min", "price": 45.00},
    "99442": {"description": "Telehealth E/M, 11-20 min", "price": 75.00},
    "99443": {"description": "Telehealth E/M, 21-30 min", "price": 110.00},
}


def setup_routes(db, get_current_user):
    """Setup billing routes with database and auth dependency"""
    
    PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY', '')
    PAYSTACK_PUBLIC_KEY = os.environ.get('PAYSTACK_PUBLIC_KEY', '')
    
    # ============ SERVICE CODES ============
    @router.get("/service-codes")
    async def get_service_codes(category: Optional[str] = None):
        """Get available service/CPT codes"""
        codes = []
        for code, details in SERVICE_CODES.items():
            codes.append({
                "code": code,
                "description": details["description"],
                "price": details["price"]
            })
        return {"service_codes": codes}
    
    # ============ INVOICES ============
    @router.post("/invoices")
    async def create_invoice(
        invoice_data: InvoiceCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Create a new invoice"""
        # Calculate totals
        subtotal = sum(
            (item.quantity * item.unit_price) - item.discount 
            for item in invoice_data.line_items
        )
        total_discount = sum(item.discount for item in invoice_data.line_items)
        tax = 0  # Healthcare typically tax-exempt
        total = subtotal + tax
        
        # Generate invoice number
        inv_count = await db.invoices.count_documents({})
        invoice_number = f"INV-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{inv_count + 1:05d}"
        
        # Set due date
        due_date = invoice_data.due_date or (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        
        invoice_doc = {
            "id": str(uuid.uuid4()),
            "invoice_number": invoice_number,
            "patient_id": invoice_data.patient_id,
            "patient_name": invoice_data.patient_name,
            "encounter_id": invoice_data.encounter_id,
            "line_items": [item.model_dump() for item in invoice_data.line_items],
            "subtotal": subtotal,
            "discount": total_discount,
            "tax": tax,
            "total": total,
            "amount_paid": 0,
            "balance_due": total,
            "status": InvoiceStatus.DRAFT,
            "notes": invoice_data.notes,
            "due_date": due_date,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user["id"],
            "paid_at": None,
            "organization_id": current_user.get("organization_id"),
            "insurance_id": invoice_data.insurance_id,
            "payments": []
        }
        
        await db.invoices.insert_one(invoice_doc)
        invoice_doc.pop("_id", None)
        
        return {
            "message": "Invoice created",
            "invoice_id": invoice_doc["id"],
            "invoice_number": invoice_number,
            "total": total
        }
    
    @router.get("/invoices")
    async def get_invoices(
        status: Optional[str] = None,
        patient_id: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Get all invoices"""
        query = {}
        org_id = current_user.get("organization_id")
        
        if org_id and current_user.get("role") != "super_admin":
            query["organization_id"] = org_id
        
        if status:
            query["status"] = status
        
        if patient_id:
            query["patient_id"] = patient_id
        
        invoices = await db.invoices.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
        
        # Clean up _id from nested payments array
        for invoice in invoices:
            if invoice.get("payments"):
                for payment in invoice["payments"]:
                    payment.pop("_id", None)
        
        return {"invoices": invoices, "count": len(invoices)}
    
    @router.get("/invoices/{invoice_id}")
    async def get_invoice(invoice_id: str, current_user: dict = Depends(get_current_user)):
        """Get invoice by ID"""
        invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Clean up _id from nested payments array
        if invoice.get("payments"):
            for payment in invoice["payments"]:
                payment.pop("_id", None)
        
        return invoice
    
    @router.put("/invoices/{invoice_id}/send")
    async def send_invoice(invoice_id: str, current_user: dict = Depends(get_current_user)):
        """Mark invoice as sent to patient"""
        result = await db.invoices.update_one(
            {"id": invoice_id},
            {"$set": {"status": InvoiceStatus.SENT}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        return {"message": "Invoice sent"}
    
    @router.delete("/invoices/{invoice_id}")
    async def cancel_invoice(invoice_id: str, current_user: dict = Depends(get_current_user)):
        """Cancel an invoice"""
        invoice = await db.invoices.find_one({"id": invoice_id})
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        if invoice["status"] == InvoiceStatus.PAID:
            raise HTTPException(status_code=400, detail="Cannot cancel a paid invoice")
        
        await db.invoices.update_one(
            {"id": invoice_id},
            {"$set": {"status": InvoiceStatus.CANCELLED}}
        )
        
        return {"message": "Invoice cancelled"}
    
    # ============ PAYMENTS ============
    @router.post("/payments")
    async def record_payment(
        payment_data: PaymentCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Record a payment against an invoice"""
        invoice = await db.invoices.find_one({"id": payment_data.invoice_id})
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        if invoice["status"] == InvoiceStatus.PAID:
            raise HTTPException(status_code=400, detail="Invoice already paid in full")
        
        # Create payment record
        payment_id = str(uuid.uuid4())
        payment_doc = {
            "id": payment_id,
            "invoice_id": payment_data.invoice_id,
            "amount": payment_data.amount,
            "payment_method": payment_data.payment_method,
            "reference": payment_data.reference,
            "notes": payment_data.notes,
            "recorded_by": current_user["id"],
            "recorded_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.payments.insert_one(payment_doc)
        
        # Update invoice
        new_amount_paid = invoice["amount_paid"] + payment_data.amount
        new_balance = invoice["total"] - new_amount_paid
        
        new_status = InvoiceStatus.SENT
        if new_balance <= 0:
            new_status = InvoiceStatus.PAID
        elif new_amount_paid > 0:
            new_status = InvoiceStatus.PARTIALLY_PAID
        
        update_data = {
            "amount_paid": new_amount_paid,
            "balance_due": max(0, new_balance),
            "status": new_status
        }
        
        if new_status == InvoiceStatus.PAID:
            update_data["paid_at"] = datetime.now(timezone.utc).isoformat()
        
        await db.invoices.update_one(
            {"id": payment_data.invoice_id},
            {
                "$set": update_data,
                "$push": {"payments": payment_doc}
            }
        )
        
        return {
            "message": "Payment recorded",
            "payment_id": payment_id,
            "new_balance": max(0, new_balance),
            "status": new_status
        }
    
    @router.get("/payments/invoice/{invoice_id}")
    async def get_invoice_payments(invoice_id: str, current_user: dict = Depends(get_current_user)):
        """Get all payments for an invoice"""
        payments = await db.payments.find({"invoice_id": invoice_id}, {"_id": 0}).to_list(100)
        return {"payments": payments}
    
    # ============ PAYSTACK INTEGRATION ============
    @router.post("/paystack/initialize")
    async def initialize_paystack_payment(
        invoice_id: str,
        email: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Initialize a Paystack payment"""
        if not PAYSTACK_SECRET_KEY:
            raise HTTPException(status_code=500, detail="Paystack not configured")
        
        invoice = await db.invoices.find_one({"id": invoice_id})
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        if invoice["balance_due"] <= 0:
            raise HTTPException(status_code=400, detail="No balance due")
        
        # Amount in kobo (multiply by 100)
        amount_kobo = int(invoice["balance_due"] * 100)
        reference = f"YACCO-{invoice['invoice_number']}-{str(uuid.uuid4())[:8]}"
        
        try:
            response = requests.post(
                "https://api.paystack.co/transaction/initialize",
                headers={
                    "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "email": email,
                    "amount": amount_kobo,
                    "reference": reference,
                    "callback_url": f"{os.environ.get('FRONTEND_URL', '')}/billing/verify",
                    "metadata": {
                        "invoice_id": invoice_id,
                        "invoice_number": invoice["invoice_number"],
                        "patient_id": invoice["patient_id"]
                    }
                }
            )
            
            data = response.json()
            
            if not data.get("status"):
                raise HTTPException(status_code=400, detail=data.get("message", "Payment initialization failed"))
            
            # Store transaction reference
            await db.paystack_transactions.insert_one({
                "id": str(uuid.uuid4()),
                "reference": reference,
                "invoice_id": invoice_id,
                "amount": invoice["balance_due"],
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            
            return {
                "authorization_url": data["data"]["authorization_url"],
                "reference": reference,
                "access_code": data["data"]["access_code"]
            }
            
        except requests.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Payment service error: {str(e)}")
    
    @router.get("/paystack/verify/{reference}")
    async def verify_paystack_payment(reference: str):
        """Verify a Paystack payment"""
        if not PAYSTACK_SECRET_KEY:
            raise HTTPException(status_code=500, detail="Paystack not configured")
        
        try:
            response = requests.get(
                f"https://api.paystack.co/transaction/verify/{reference}",
                headers={"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
            )
            
            data = response.json()
            
            if not data.get("status"):
                raise HTTPException(status_code=400, detail="Verification failed")
            
            transaction_data = data.get("data", {})
            
            if transaction_data.get("status") == "success":
                # Find the stored transaction
                stored_tx = await db.paystack_transactions.find_one({"reference": reference})
                
                if stored_tx:
                    # Record payment
                    invoice = await db.invoices.find_one({"id": stored_tx["invoice_id"]})
                    
                    if invoice:
                        amount_paid = transaction_data.get("amount", 0) / 100  # Convert from kobo
                        
                        payment_doc = {
                            "id": str(uuid.uuid4()),
                            "invoice_id": stored_tx["invoice_id"],
                            "amount": amount_paid,
                            "payment_method": PaymentMethod.PAYSTACK,
                            "reference": reference,
                            "notes": "Paystack online payment",
                            "recorded_by": "system",
                            "recorded_at": datetime.now(timezone.utc).isoformat()
                        }
                        
                        await db.payments.insert_one(payment_doc)
                        
                        # Update invoice
                        new_amount_paid = invoice["amount_paid"] + amount_paid
                        new_balance = invoice["total"] - new_amount_paid
                        
                        new_status = InvoiceStatus.PAID if new_balance <= 0 else InvoiceStatus.PARTIALLY_PAID
                        
                        await db.invoices.update_one(
                            {"id": stored_tx["invoice_id"]},
                            {
                                "$set": {
                                    "amount_paid": new_amount_paid,
                                    "balance_due": max(0, new_balance),
                                    "status": new_status,
                                    "paid_at": datetime.now(timezone.utc).isoformat() if new_status == InvoiceStatus.PAID else None
                                },
                                "$push": {"payments": payment_doc}
                            }
                        )
                        
                        # Update transaction status
                        await db.paystack_transactions.update_one(
                            {"reference": reference},
                            {"$set": {"status": "success", "verified_at": datetime.now(timezone.utc).isoformat()}}
                        )
                
                return {
                    "status": "success",
                    "message": "Payment verified and recorded",
                    "amount": transaction_data.get("amount", 0) / 100,
                    "reference": reference
                }
            else:
                return {
                    "status": transaction_data.get("status", "failed"),
                    "message": "Payment not successful"
                }
                
        except requests.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Verification error: {str(e)}")
    
    @router.post("/paystack/webhook")
    async def paystack_webhook(request: Request):
        """Handle Paystack webhook events"""
        if not PAYSTACK_SECRET_KEY:
            return {"status": "ignored"}
        
        # Verify signature
        signature = request.headers.get("x-paystack-signature")
        body = await request.body()
        
        computed_signature = hmac.new(
            PAYSTACK_SECRET_KEY.encode(),
            body,
            hashlib.sha512
        ).hexdigest()
        
        if signature != computed_signature:
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        import json
        payload = json.loads(body)
        event = payload.get("event")
        data = payload.get("data", {})
        
        if event == "charge.success":
            reference = data.get("reference")
            
            # Process the successful payment
            stored_tx = await db.paystack_transactions.find_one({"reference": reference})
            
            if stored_tx and stored_tx.get("status") == "pending":
                # Verify and process (similar to verify endpoint)
                await verify_paystack_payment(reference)
        
        return {"status": "processed"}
    
    @router.get("/paystack/config")
    async def get_paystack_config():
        """Get Paystack public key for frontend"""
        return {
            "public_key": PAYSTACK_PUBLIC_KEY,
            "enabled": bool(PAYSTACK_SECRET_KEY)
        }
    
    # ============ INSURANCE CLAIMS (MOCK 837) ============
    @router.post("/claims")
    async def create_insurance_claim(
        claim_data: InsuranceClaimCreate,
        current_user: dict = Depends(get_current_user)
    ):
        """Create a mock 837 insurance claim"""
        invoice = await db.invoices.find_one({"id": claim_data.invoice_id})
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Generate claim number
        claim_count = await db.insurance_claims.count_documents({})
        claim_number = f"CLM-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{claim_count + 1:06d}"
        
        # Build mock 837 segments
        edi_segments = generate_mock_837(claim_data, invoice, claim_number, current_user)
        
        claim_doc = {
            "id": str(uuid.uuid4()),
            "claim_number": claim_number,
            "invoice_id": claim_data.invoice_id,
            "patient_id": claim_data.patient_id,
            "insurance_provider": claim_data.insurance_provider,
            "insurance_id": claim_data.insurance_id,
            "subscriber_name": claim_data.subscriber_name,
            "subscriber_id": claim_data.subscriber_id,
            "diagnosis_codes": claim_data.diagnosis_codes,
            "procedure_codes": claim_data.procedure_codes,
            "total_charges": invoice["total"],
            "status": ClaimStatus.DRAFT,
            "edi_content": edi_segments,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user["id"],
            "submitted_at": None,
            "response": None,
            "organization_id": current_user.get("organization_id")
        }
        
        await db.insurance_claims.insert_one(claim_doc)
        
        return {
            "message": "Insurance claim created",
            "claim_id": claim_doc["id"],
            "claim_number": claim_number,
            "edi_preview": edi_segments[:500] + "..."  # Preview of EDI content
        }
    
    @router.get("/claims")
    async def get_claims(
        status: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Get insurance claims"""
        query = {}
        org_id = current_user.get("organization_id")
        
        if org_id and current_user.get("role") != "super_admin":
            query["organization_id"] = org_id
        
        if status:
            query["status"] = status
        
        claims = await db.insurance_claims.find(query, {"_id": 0, "edi_content": 0}).sort("created_at", -1).to_list(500)
        
        return {"claims": claims, "count": len(claims)}
    
    @router.get("/claims/{claim_id}")
    async def get_claim(claim_id: str, current_user: dict = Depends(get_current_user)):
        """Get claim details including EDI content"""
        claim = await db.insurance_claims.find_one({"id": claim_id}, {"_id": 0})
        
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        return claim
    
    @router.post("/claims/{claim_id}/submit")
    async def submit_claim(claim_id: str, current_user: dict = Depends(get_current_user)):
        """Submit claim (mock - simulates sending to clearinghouse)"""
        claim = await db.insurance_claims.find_one({"id": claim_id})
        
        if not claim:
            raise HTTPException(status_code=404, detail="Claim not found")
        
        if claim["status"] != ClaimStatus.DRAFT:
            raise HTTPException(status_code=400, detail="Claim already submitted")
        
        # Simulate submission
        await db.insurance_claims.update_one(
            {"id": claim_id},
            {"$set": {
                "status": ClaimStatus.SUBMITTED,
                "submitted_at": datetime.now(timezone.utc).isoformat(),
                "response": {
                    "acknowledgment": "Claim received",
                    "tracking_number": f"TRK-{str(uuid.uuid4())[:12].upper()}",
                    "estimated_processing": "5-7 business days"
                }
            }}
        )
        
        return {"message": "Claim submitted successfully"}
    
    # ============ DASHBOARD STATS ============
    @router.get("/stats")
    async def get_billing_stats(current_user: dict = Depends(get_current_user)):
        """Get billing statistics"""
        query = {}
        org_id = current_user.get("organization_id")
        
        if org_id and current_user.get("role") != "super_admin":
            query["organization_id"] = org_id
        
        # Get all invoices
        invoices = await db.invoices.find(query, {"_id": 0}).to_list(10000)
        
        total_billed = sum(inv["total"] for inv in invoices)
        total_collected = sum(inv["amount_paid"] for inv in invoices)
        total_outstanding = sum(inv["balance_due"] for inv in invoices)
        
        paid_count = len([inv for inv in invoices if inv["status"] == InvoiceStatus.PAID])
        pending_count = len([inv for inv in invoices if inv["status"] in [InvoiceStatus.DRAFT, InvoiceStatus.SENT]])
        overdue_count = len([inv for inv in invoices if inv["status"] == InvoiceStatus.OVERDUE])
        
        # Claims stats
        claims = await db.insurance_claims.find(query, {"_id": 0}).to_list(10000)
        claims_submitted = len([c for c in claims if c["status"] == ClaimStatus.SUBMITTED])
        claims_approved = len([c for c in claims if c["status"] == ClaimStatus.APPROVED])
        
        return {
            "total_billed": total_billed,
            "total_collected": total_collected,
            "total_outstanding": total_outstanding,
            "collection_rate": (total_collected / total_billed * 100) if total_billed > 0 else 0,
            "invoices": {
                "total": len(invoices),
                "paid": paid_count,
                "pending": pending_count,
                "overdue": overdue_count
            },
            "claims": {
                "total": len(claims),
                "submitted": claims_submitted,
                "approved": claims_approved
            }
        }
    
    return router


def generate_mock_837(claim_data, invoice, claim_number, current_user):
    """Generate mock 837 Professional claim EDI content"""
    now = datetime.now(timezone.utc)
    
    segments = []
    
    # ISA - Interchange Control Header
    segments.append(f"ISA*00*          *00*          *ZZ*YACCOEMR       *ZZ*{claim_data.insurance_provider[:15].ljust(15)}*{now.strftime('%y%m%d')}*{now.strftime('%H%M')}*^*00501*{claim_number[-9:]}*0*P*:~")
    
    # GS - Functional Group Header
    segments.append(f"GS*HC*YACCOEMR*{claim_data.insurance_provider[:15]}*{now.strftime('%Y%m%d')}*{now.strftime('%H%M%S')}*1*X*005010X222A1~")
    
    # ST - Transaction Set Header
    segments.append("ST*837*0001*005010X222A1~")
    
    # BHT - Beginning of Hierarchical Transaction
    segments.append(f"BHT*0019*00*{claim_number}*{now.strftime('%Y%m%d')}*{now.strftime('%H%M')}*CH~")
    
    # NM1 - Submitter Name
    segments.append(f"NM1*41*2*YACCO EMR HEALTHCARE*****46*{current_user.get('organization_id', 'ORG001')[:10]}~")
    
    # NM1 - Receiver Name
    segments.append(f"NM1*40*2*{claim_data.insurance_provider}*****46*{claim_data.insurance_id[:10]}~")
    
    # HL - Billing Provider Hierarchical Level
    segments.append("HL*1**20*1~")
    
    # NM1 - Billing Provider
    segments.append(f"NM1*85*2*YACCO MEDICAL CENTER*****XX*1234567890~")
    segments.append("N3*123 HEALTHCARE DRIVE~")
    segments.append("N4*MEDICAL CITY*ST*12345~")
    
    # HL - Subscriber Hierarchical Level
    segments.append("HL*2*1*22*0~")
    
    # SBR - Subscriber Information
    segments.append(f"SBR*P*18*******CI~")
    
    # NM1 - Subscriber Name
    segments.append(f"NM1*IL*1*{claim_data.subscriber_name.split()[-1] if ' ' in claim_data.subscriber_name else claim_data.subscriber_name}*{claim_data.subscriber_name.split()[0] if ' ' in claim_data.subscriber_name else ''}****MI*{claim_data.subscriber_id}~")
    
    # NM1 - Patient Name
    segments.append(f"NM1*QC*1*{invoice['patient_name'].split()[-1] if ' ' in invoice['patient_name'] else invoice['patient_name']}*{invoice['patient_name'].split()[0] if ' ' in invoice['patient_name'] else ''}~")
    
    # CLM - Claim Information
    segments.append(f"CLM*{claim_number}*{invoice['total']}***11:B:1*Y*A*Y*Y~")
    
    # DTP - Date of Service
    segments.append(f"DTP*472*D8*{now.strftime('%Y%m%d')}~")
    
    # HI - Diagnosis Codes
    for i, dx in enumerate(claim_data.diagnosis_codes[:12]):
        qualifier = "ABK" if i == 0 else "ABF"
        segments.append(f"HI*{qualifier}:{dx.replace('.', '')}~")
    
    # LX/SV1 - Service Lines
    for i, item in enumerate(invoice["line_items"], 1):
        segments.append(f"LX*{i}~")
        cpt_code = item.get("service_code", "99213")
        segments.append(f"SV1*HC:{cpt_code}*{item['unit_price']}*UN*{item['quantity']}***1~")
        segments.append(f"DTP*472*D8*{now.strftime('%Y%m%d')}~")
    
    # SE - Transaction Set Trailer
    segments.append(f"SE*{len(segments) + 1}*0001~")
    
    # GE - Functional Group Trailer
    segments.append("GE*1*1~")
    
    # IEA - Interchange Control Trailer
    segments.append(f"IEA*1*{claim_number[-9:]}~")
    
    return "\n".join(segments)
