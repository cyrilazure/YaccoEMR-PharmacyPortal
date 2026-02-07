"""
Billing Shifts Module for Yacco EMR
Handles shift-based billing, clock-in/out, and role-based financial visibility
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid

router = APIRouter(prefix="/api/billing-shifts", tags=["Billing Shifts"])

# ============ ENUMS ============
class ShiftStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    RECONCILED = "reconciled"
    FLAGGED = "flagged"

class PaymentModeType(str, Enum):
    CASH = "cash"
    MOBILE_MONEY = "mobile_money"
    CARD = "card"
    INSURANCE = "insurance"
    BANK_TRANSFER = "bank_transfer"

# ============ MODELS ============
class ShiftClockIn(BaseModel):
    shift_type: str = "day"  # day, evening, night
    notes: Optional[str] = None

class ShiftClockOut(BaseModel):
    closing_notes: Optional[str] = None
    actual_cash: Optional[float] = None  # For reconciliation

class ShiftSummary(BaseModel):
    id: str
    biller_id: str
    biller_name: str
    hospital_id: str
    shift_type: str
    status: str
    start_time: str
    end_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    
    # Financial Totals
    total_invoices: int = 0
    total_invoice_amount: float = 0.0
    total_payments: int = 0
    total_payments_amount: float = 0.0
    
    # Payment Mode Breakdown
    cash_collected: float = 0.0
    mobile_money_collected: float = 0.0
    card_payments: float = 0.0
    insurance_billed: float = 0.0
    bank_transfers: float = 0.0
    
    # Reconciliation
    expected_cash: float = 0.0
    actual_cash: Optional[float] = None
    discrepancy: Optional[float] = None
    reconciliation_status: Optional[str] = None
    
    closing_notes: Optional[str] = None

class AdminFinancialDashboard(BaseModel):
    # Daily
    daily_revenue: float = 0.0
    daily_invoices: int = 0
    daily_payments: int = 0
    
    # Weekly
    weekly_revenue: float = 0.0
    weekly_invoices: int = 0
    
    # Monthly
    monthly_revenue: float = 0.0
    monthly_invoices: int = 0
    
    # Payment Mode Distribution
    payment_modes: Dict[str, float] = {}
    
    # Outstanding
    total_outstanding: float = 0.0
    pending_insurance_claims: float = 0.0
    
    # Shifts Overview
    active_shifts: int = 0
    completed_shifts_today: int = 0


def create_billing_shifts_router(db, get_current_user):
    """Create billing shifts router with database dependency"""
    
    # ============ SHIFT MANAGEMENT ============
    
    @router.post("/clock-in")
    async def clock_in_shift(data: ShiftClockIn, current_user: dict = Depends(get_current_user)):
        """Clock in to start a billing shift"""
        allowed_roles = ['biller', 'senior_biller', 'cashier', 'hospital_admin', 'finance_manager']
        if current_user.get('role') not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized to manage billing shifts")
        
        # Check if user already has an active shift
        existing_shift = await db.billing_shifts.find_one({
            "biller_id": current_user['id'],
            "status": ShiftStatus.ACTIVE.value
        })
        
        if existing_shift:
            raise HTTPException(status_code=400, detail="You already have an active shift. Please clock out first.")
        
        # Create new shift
        shift = {
            "id": str(uuid.uuid4()),
            "biller_id": current_user['id'],
            "biller_name": f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}".strip(),
            "biller_email": current_user.get('email'),
            "hospital_id": current_user.get('hospital_id'),
            "shift_type": data.shift_type,
            "status": ShiftStatus.ACTIVE.value,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "end_time": None,
            "duration_minutes": None,
            
            # Financial Totals - Start at zero
            "total_invoices": 0,
            "total_invoice_amount": 0.0,
            "total_payments": 0,
            "total_payments_amount": 0.0,
            
            # Payment Mode Breakdown
            "cash_collected": 0.0,
            "mobile_money_collected": 0.0,
            "card_payments": 0.0,
            "insurance_billed": 0.0,
            "bank_transfers": 0.0,
            
            # Reconciliation
            "expected_cash": 0.0,
            "actual_cash": None,
            "discrepancy": None,
            "reconciliation_status": None,
            
            "notes": data.notes,
            "closing_notes": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.billing_shifts.insert_one(shift)
        
        # Log audit
        await db.billing_audit_logs.insert_one({
            "id": str(uuid.uuid4()),
            "action": "shift_clock_in",
            "user_id": current_user['id'],
            "user_name": shift['biller_name'],
            "shift_id": shift['id'],
            "hospital_id": current_user.get('hospital_id'),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": {"shift_type": data.shift_type}
        })
        
        return {"message": "Shift started successfully", "shift": {k: v for k, v in shift.items() if k != '_id'}}
    
    @router.post("/clock-out")
    async def clock_out_shift(data: ShiftClockOut, current_user: dict = Depends(get_current_user)):
        """Clock out to end a billing shift"""
        # Find active shift
        shift = await db.billing_shifts.find_one({
            "biller_id": current_user['id'],
            "status": ShiftStatus.ACTIVE.value
        })
        
        if not shift:
            raise HTTPException(status_code=404, detail="No active shift found")
        
        end_time = datetime.now(timezone.utc)
        start_time = datetime.fromisoformat(shift['start_time'].replace('Z', '+00:00'))
        duration = int((end_time - start_time).total_seconds() / 60)
        
        # Calculate discrepancy if actual cash provided
        discrepancy = None
        reconciliation_status = None
        if data.actual_cash is not None:
            discrepancy = data.actual_cash - shift.get('expected_cash', 0)
            if abs(discrepancy) < 0.01:
                reconciliation_status = "balanced"
            elif discrepancy > 0:
                reconciliation_status = "overage"
            else:
                reconciliation_status = "shortage"
        
        # Update shift
        update_data = {
            "status": ShiftStatus.CLOSED.value,
            "end_time": end_time.isoformat(),
            "duration_minutes": duration,
            "closing_notes": data.closing_notes,
            "actual_cash": data.actual_cash,
            "discrepancy": discrepancy,
            "reconciliation_status": reconciliation_status,
            "closed_at": end_time.isoformat()
        }
        
        await db.billing_shifts.update_one(
            {"id": shift['id']},
            {"$set": update_data}
        )
        
        # Log audit
        await db.billing_audit_logs.insert_one({
            "id": str(uuid.uuid4()),
            "action": "shift_clock_out",
            "user_id": current_user['id'],
            "user_name": shift['biller_name'],
            "shift_id": shift['id'],
            "hospital_id": current_user.get('hospital_id'),
            "timestamp": end_time.isoformat(),
            "details": {
                "duration_minutes": duration,
                "total_invoices": shift.get('total_invoices', 0),
                "total_payments": shift.get('total_payments_amount', 0),
                "reconciliation_status": reconciliation_status
            }
        })
        
        # Get updated shift
        updated_shift = await db.billing_shifts.find_one({"id": shift['id']})
        
        return {
            "message": "Shift closed successfully",
            "shift": {k: v for k, v in updated_shift.items() if k != '_id'}
        }
    
    @router.get("/active")
    async def get_active_shift(current_user: dict = Depends(get_current_user)):
        """Get current user's active shift"""
        shift = await db.billing_shifts.find_one({
            "biller_id": current_user['id'],
            "status": ShiftStatus.ACTIVE.value
        })
        
        if not shift:
            return {"active_shift": None}
        
        return {"active_shift": {k: v for k, v in shift.items() if k != '_id'}}
    
    @router.get("/my-shifts")
    async def get_my_shifts(
        limit: int = 10,
        current_user: dict = Depends(get_current_user)
    ):
        """Get current user's shift history"""
        shifts = await db.billing_shifts.find({
            "biller_id": current_user['id']
        }).sort("start_time", -1).limit(limit).to_list(length=limit)
        
        return {"shifts": [{k: v for k, v in s.items() if k != '_id'} for s in shifts]}
    
    # ============ SHIFT-SCOPED FINANCIAL DATA (BILLER VIEW) ============
    
    @router.get("/dashboard/biller")
    async def get_biller_dashboard(current_user: dict = Depends(get_current_user)):
        """Get biller's shift-scoped financial dashboard"""
        # Get active shift
        active_shift = await db.billing_shifts.find_one({
            "biller_id": current_user['id'],
            "status": ShiftStatus.ACTIVE.value
        })
        
        if not active_shift:
            # Return empty dashboard if no active shift
            return {
                "has_active_shift": False,
                "shift": None,
                "shift_metrics": {
                    "invoices_generated": 0,
                    "invoices_amount": 0.0,
                    "payments_received": 0,
                    "payments_amount": 0.0,
                    "cash_collected": 0.0,
                    "mobile_money_collected": 0.0,
                    "card_payments": 0.0,
                    "insurance_billed": 0.0
                },
                "outstanding": await get_outstanding_balances(db, current_user.get('hospital_id')),
                "recent_payments": []
            }
        
        # Get shift duration
        start_time = datetime.fromisoformat(active_shift['start_time'].replace('Z', '+00:00'))
        duration = int((datetime.now(timezone.utc) - start_time).total_seconds() / 60)
        
        # Get recent payments for this shift
        recent_payments = await db.billing_payments.find({
            "recorded_by": current_user['id'],
            "created_at": {"$gte": active_shift['start_time']}
        }).sort("created_at", -1).limit(10).to_list(length=10)
        
        return {
            "has_active_shift": True,
            "shift": {
                "id": active_shift['id'],
                "shift_type": active_shift['shift_type'],
                "start_time": active_shift['start_time'],
                "duration_minutes": duration
            },
            "shift_metrics": {
                "invoices_generated": active_shift.get('total_invoices', 0),
                "invoices_amount": active_shift.get('total_invoice_amount', 0.0),
                "payments_received": active_shift.get('total_payments', 0),
                "payments_amount": active_shift.get('total_payments_amount', 0.0),
                "cash_collected": active_shift.get('cash_collected', 0.0),
                "mobile_money_collected": active_shift.get('mobile_money_collected', 0.0),
                "card_payments": active_shift.get('card_payments', 0.0),
                "insurance_billed": active_shift.get('insurance_billed', 0.0),
                "bank_transfers": active_shift.get('bank_transfers', 0.0)
            },
            "outstanding": await get_outstanding_balances(db, current_user.get('hospital_id')),
            "recent_payments": [{k: v for k, v in p.items() if k != '_id'} for p in recent_payments]
        }
    
    # ============ ADMIN FINANCIAL DASHBOARD ============
    
    @router.get("/dashboard/admin")
    async def get_admin_financial_dashboard(current_user: dict = Depends(get_current_user)):
        """Get full financial dashboard for administrators"""
        allowed_roles = ['hospital_admin', 'finance_manager', 'admin']
        if current_user.get('role') not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized to view admin financial dashboard")
        
        hospital_id = current_user.get('hospital_id')
        now = datetime.now(timezone.utc)
        
        # Date ranges
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
        
        # Daily metrics
        daily_invoices = await db.invoices.find({
            "hospital_id": hospital_id,
            "created_at": {"$gte": today_start}
        }).to_list(length=None)
        
        daily_payments = await db.billing_payments.find({
            "hospital_id": hospital_id,
            "created_at": {"$gte": today_start}
        }).to_list(length=None)
        
        # Weekly metrics
        weekly_invoices = await db.invoices.find({
            "hospital_id": hospital_id,
            "created_at": {"$gte": week_start}
        }).to_list(length=None)
        
        weekly_payments = await db.billing_payments.find({
            "hospital_id": hospital_id,
            "created_at": {"$gte": week_start}
        }).to_list(length=None)
        
        # Monthly metrics
        monthly_invoices = await db.invoices.find({
            "hospital_id": hospital_id,
            "created_at": {"$gte": month_start}
        }).to_list(length=None)
        
        monthly_payments = await db.billing_payments.find({
            "hospital_id": hospital_id,
            "created_at": {"$gte": month_start}
        }).to_list(length=None)
        
        # Calculate payment mode distribution (monthly)
        payment_modes = {
            "cash": 0.0,
            "mobile_money": 0.0,
            "card": 0.0,
            "insurance": 0.0,
            "bank_transfer": 0.0
        }
        
        for p in monthly_payments:
            method = p.get('payment_method', 'cash').lower()
            amount = p.get('amount', 0)
            
            if 'cash' in method:
                payment_modes['cash'] += amount
            elif 'mobile' in method or 'momo' in method:
                payment_modes['mobile_money'] += amount
            elif 'card' in method or 'visa' in method or 'master' in method:
                payment_modes['card'] += amount
            elif 'insurance' in method or 'nhis' in method:
                payment_modes['insurance'] += amount
            elif 'bank' in method or 'transfer' in method:
                payment_modes['bank_transfer'] += amount
            else:
                payment_modes['cash'] += amount
        
        # Outstanding balances
        outstanding = await get_outstanding_balances(db, hospital_id)
        
        # Pending insurance claims
        pending_claims = await db.insurance_claims.find({
            "hospital_id": hospital_id,
            "status": {"$in": ["submitted", "pending", "acknowledged"]}
        }).to_list(length=None)
        
        pending_claims_value = sum(c.get('total_claimed', 0) for c in pending_claims)
        
        # Active shifts
        active_shifts = await db.billing_shifts.count_documents({
            "hospital_id": hospital_id,
            "status": ShiftStatus.ACTIVE.value
        })
        
        # Completed shifts today
        completed_shifts_today = await db.billing_shifts.count_documents({
            "hospital_id": hospital_id,
            "status": ShiftStatus.CLOSED.value,
            "end_time": {"$gte": today_start}
        })
        
        # Daily revenue trend (last 7 days)
        daily_trend = []
        for i in range(7):
            day = now - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()
            
            day_payments = await db.billing_payments.find({
                "hospital_id": hospital_id,
                "created_at": {"$gte": day_start, "$lte": day_end}
            }).to_list(length=None)
            
            daily_trend.append({
                "date": day.strftime("%Y-%m-%d"),
                "day": day.strftime("%a"),
                "revenue": sum(p.get('amount', 0) for p in day_payments),
                "count": len(day_payments)
            })
        
        daily_trend.reverse()
        
        return {
            "daily": {
                "revenue": sum(p.get('amount', 0) for p in daily_payments),
                "invoices_count": len(daily_invoices),
                "invoices_value": sum(i.get('total', 0) for i in daily_invoices),
                "payments_count": len(daily_payments)
            },
            "weekly": {
                "revenue": sum(p.get('amount', 0) for p in weekly_payments),
                "invoices_count": len(weekly_invoices),
                "invoices_value": sum(i.get('total', 0) for i in weekly_invoices),
                "payments_count": len(weekly_payments)
            },
            "monthly": {
                "revenue": sum(p.get('amount', 0) for p in monthly_payments),
                "invoices_count": len(monthly_invoices),
                "invoices_value": sum(i.get('total', 0) for i in monthly_invoices),
                "payments_count": len(monthly_payments)
            },
            "payment_modes": payment_modes,
            "outstanding": outstanding,
            "pending_insurance_claims": pending_claims_value,
            "shifts": {
                "active": active_shifts,
                "completed_today": completed_shifts_today
            },
            "daily_trend": daily_trend
        }
    
    # ============ ALL SHIFTS VIEW (ADMIN ONLY) ============
    
    @router.get("/all-shifts")
    async def get_all_shifts(
        status: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        biller_id: Optional[str] = None,
        limit: int = 50,
        current_user: dict = Depends(get_current_user)
    ):
        """Get all shifts for admin view"""
        allowed_roles = ['hospital_admin', 'finance_manager', 'admin', 'senior_biller']
        if current_user.get('role') not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized to view all shifts")
        
        query = {"hospital_id": current_user.get('hospital_id')}
        
        if status:
            query["status"] = status
        if biller_id:
            query["biller_id"] = biller_id
        if date_from:
            query["start_time"] = {"$gte": date_from}
        if date_to:
            if "start_time" in query:
                query["start_time"]["$lte"] = date_to
            else:
                query["start_time"] = {"$lte": date_to}
        
        shifts = await db.billing_shifts.find(query).sort("start_time", -1).limit(limit).to_list(length=limit)
        
        return {"shifts": [{k: v for k, v in s.items() if k != '_id'} for s in shifts]}
    
    # ============ SHIFT RECONCILIATION (ADMIN) ============
    
    @router.post("/shifts/{shift_id}/reconcile")
    async def reconcile_shift(
        shift_id: str,
        actual_cash: float,
        notes: Optional[str] = None,
        current_user: dict = Depends(get_current_user)
    ):
        """Admin reconciliation of a closed shift"""
        allowed_roles = ['hospital_admin', 'finance_manager', 'admin']
        if current_user.get('role') not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized to reconcile shifts")
        
        shift = await db.billing_shifts.find_one({"id": shift_id})
        if not shift:
            raise HTTPException(status_code=404, detail="Shift not found")
        
        if shift['status'] == ShiftStatus.ACTIVE.value:
            raise HTTPException(status_code=400, detail="Cannot reconcile an active shift")
        
        expected = shift.get('expected_cash', 0)
        discrepancy = actual_cash - expected
        
        if abs(discrepancy) < 0.01:
            recon_status = "balanced"
        elif discrepancy > 0:
            recon_status = "overage"
        else:
            recon_status = "shortage"
        
        await db.billing_shifts.update_one(
            {"id": shift_id},
            {"$set": {
                "status": ShiftStatus.RECONCILED.value,
                "actual_cash": actual_cash,
                "discrepancy": discrepancy,
                "reconciliation_status": recon_status,
                "reconciled_by": current_user['id'],
                "reconciled_at": datetime.now(timezone.utc).isoformat(),
                "reconciliation_notes": notes
            }}
        )
        
        # Log audit
        await db.billing_audit_logs.insert_one({
            "id": str(uuid.uuid4()),
            "action": "shift_reconciliation",
            "user_id": current_user['id'],
            "user_name": f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}",
            "shift_id": shift_id,
            "hospital_id": current_user.get('hospital_id'),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": {
                "expected_cash": expected,
                "actual_cash": actual_cash,
                "discrepancy": discrepancy,
                "status": recon_status
            }
        })
        
        return {
            "message": f"Shift reconciled as {recon_status}",
            "discrepancy": discrepancy,
            "status": recon_status
        }
    
    @router.post("/shifts/{shift_id}/flag")
    async def flag_shift_discrepancy(
        shift_id: str,
        reason: str,
        current_user: dict = Depends(get_current_user)
    ):
        """Flag a shift for discrepancy review"""
        allowed_roles = ['hospital_admin', 'finance_manager', 'admin']
        if current_user.get('role') not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        await db.billing_shifts.update_one(
            {"id": shift_id},
            {"$set": {
                "status": ShiftStatus.FLAGGED.value,
                "flagged_by": current_user['id'],
                "flagged_at": datetime.now(timezone.utc).isoformat(),
                "flag_reason": reason
            }}
        )
        
        return {"message": "Shift flagged for review"}
    
    # ============ BILLING AUDIT LOGS ============
    
    @router.get("/audit-logs")
    async def get_billing_audit_logs(
        action: Optional[str] = None,
        user_id: Optional[str] = None,
        date_from: Optional[str] = None,
        limit: int = 100,
        current_user: dict = Depends(get_current_user)
    ):
        """Get billing audit logs"""
        allowed_roles = ['hospital_admin', 'finance_manager', 'admin']
        if current_user.get('role') not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized to view audit logs")
        
        query = {"hospital_id": current_user.get('hospital_id')}
        
        if action:
            query["action"] = action
        if user_id:
            query["user_id"] = user_id
        if date_from:
            query["timestamp"] = {"$gte": date_from}
        
        logs = await db.billing_audit_logs.find(query).sort("timestamp", -1).limit(limit).to_list(length=limit)
        
        return {"logs": [{k: v for k, v in log.items() if k != '_id'} for log in logs]}
    
    return router


async def get_outstanding_balances(db, hospital_id: str) -> dict:
    """Get outstanding balances - this is persistent and doesn't reset with shifts"""
    # Unpaid/partially paid invoices
    outstanding_invoices = await db.invoices.find({
        "hospital_id": hospital_id,
        "status": {"$in": ["sent", "partially_paid", "overdue", "pending_insurance"]}
    }).to_list(length=None)
    
    total_outstanding = sum(i.get('balance_due', 0) for i in outstanding_invoices)
    partially_paid_count = len([i for i in outstanding_invoices if i.get('status') == 'partially_paid'])
    unpaid_count = len([i for i in outstanding_invoices if i.get('status') in ['sent', 'overdue']])
    
    # Pending insurance
    pending_insurance = await db.insurance_claims.find({
        "hospital_id": hospital_id,
        "status": {"$in": ["submitted", "pending", "acknowledged"]}
    }).to_list(length=None)
    
    pending_insurance_value = sum(c.get('total_claimed', 0) for c in pending_insurance)
    
    return {
        "total_outstanding": total_outstanding,
        "partially_paid_count": partially_paid_count,
        "unpaid_count": unpaid_count,
        "pending_insurance_claims": len(pending_insurance),
        "pending_insurance_value": pending_insurance_value
    }


async def update_shift_on_invoice(db, user_id: str, invoice_amount: float, hospital_id: str):
    """Update active shift when invoice is created"""
    shift = await db.billing_shifts.find_one({
        "biller_id": user_id,
        "status": ShiftStatus.ACTIVE.value
    })
    
    if shift:
        await db.billing_shifts.update_one(
            {"id": shift['id']},
            {"$inc": {
                "total_invoices": 1,
                "total_invoice_amount": invoice_amount
            }}
        )


async def update_shift_on_payment(db, user_id: str, amount: float, payment_method: str, hospital_id: str):
    """Update active shift when payment is received"""
    shift = await db.billing_shifts.find_one({
        "biller_id": user_id,
        "status": ShiftStatus.ACTIVE.value
    })
    
    if shift:
        update = {
            "total_payments": 1,
            "total_payments_amount": amount
        }
        
        # Categorize payment method
        method_lower = payment_method.lower()
        if 'cash' in method_lower:
            update["cash_collected"] = amount
            update["expected_cash"] = amount  # Track expected cash
        elif 'mobile' in method_lower or 'momo' in method_lower:
            update["mobile_money_collected"] = amount
        elif 'card' in method_lower or 'visa' in method_lower or 'master' in method_lower:
            update["card_payments"] = amount
        elif 'insurance' in method_lower or 'nhis' in method_lower:
            update["insurance_billed"] = amount
        elif 'bank' in method_lower or 'transfer' in method_lower:
            update["bank_transfers"] = amount
        else:
            update["cash_collected"] = amount
            update["expected_cash"] = amount
        
        await db.billing_shifts.update_one(
            {"id": shift['id']},
            {"$inc": update}
        )


async def log_billing_action(db, action: str, user: dict, details: dict):
    """Log a billing action for audit"""
    await db.billing_audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "action": action,
        "user_id": user.get('id'),
        "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
        "hospital_id": user.get('hospital_id'),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": details
    })
