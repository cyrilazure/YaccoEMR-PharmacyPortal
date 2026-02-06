"""
Finance Settings Module for Yacco EMR
Hospital banking and financial account management
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/api/finance", tags=["Finance Settings"])

# ============ MODELS ============

class BankAccountCreate(BaseModel):
    bank_name: str
    account_name: str
    account_number: str
    branch: Optional[str] = None
    swift_code: Optional[str] = None
    account_type: str = "current"  # current, savings
    currency: str = "GHS"
    is_primary: bool = False
    bank_code: Optional[str] = None  # Ghana bank code for Paystack (e.g., "057" for GCB)
    enable_paystack_settlement: bool = True  # Auto-settle Paystack payments to this account

class MobileMoneyAccountCreate(BaseModel):
    provider: str  # MTN, Vodafone, AirtelTigo
    account_name: str
    mobile_number: str
    wallet_id: Optional[str] = None
    is_primary: bool = False


def create_finance_endpoints(db, get_current_user):
    """Create finance settings API endpoints"""
    
    # ============ BANK ACCOUNTS ============
    
    @router.get("/bank-accounts")
    async def get_bank_accounts(user: dict = Depends(get_current_user)):
        """Get hospital bank accounts"""
        # Only finance, billing admin, hospital admin, super admin can view
        allowed_roles = ["biller", "hospital_admin", "hospital_it_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Access denied - Finance role required")
        
        org_id = user.get("organization_id")
        if not org_id and user.get("role") != "super_admin":
            raise HTTPException(status_code=400, detail="No organization context")
        
        query = {"organization_id": org_id} if org_id else {}
        accounts = await db.bank_accounts.find(query, {"_id": 0}).to_list(50)
        
        return {"accounts": accounts, "total": len(accounts)}
    
    @router.post("/bank-accounts")
    async def create_bank_account(
        data: BankAccountCreate,
        user: dict = Depends(get_current_user)
    ):
        """Add bank account for hospital"""
        allowed_roles = ["biller", "hospital_admin", "hospital_it_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Access denied - Finance role required")
        
        org_id = user.get("organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="No organization context")
        
        # If setting as primary, unset other primary accounts
        if data.is_primary:
            await db.bank_accounts.update_many(
                {"organization_id": org_id},
                {"$set": {"is_primary": False}}
            )
        
        account_id = str(uuid.uuid4())
        account_doc = {
            "id": account_id,
            "organization_id": org_id,
            "bank_name": data.bank_name,
            "account_name": data.account_name,
            "account_number": data.account_number,
            "branch": data.branch,
            "swift_code": data.swift_code,
            "account_type": data.account_type,
            "currency": data.currency,
            "is_primary": data.is_primary,
            "is_active": True,
            "created_by": user.get("id"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.bank_accounts.insert_one(account_doc)
        account_doc.pop("_id", None)
        
        # Audit log
        await db.audit_logs.insert_one({
            "id": str(uuid.uuid4()),
            "action": "bank_account_added",
            "resource_type": "bank_account",
            "resource_id": account_id,
            "user_id": user.get("id"),
            "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": org_id,
            "details": {"bank_name": data.bank_name, "account_number": data.account_number},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {"message": "Bank account added", "account": account_doc}
    
    @router.put("/bank-accounts/{account_id}")
    async def update_bank_account(
        account_id: str,
        data: BankAccountCreate,
        user: dict = Depends(get_current_user)
    ):
        """Update bank account"""
        allowed_roles = ["biller", "hospital_admin", "hospital_it_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Access denied")
        
        account = await db.bank_accounts.find_one({"id": account_id})
        if not account:
            raise HTTPException(status_code=404, detail="Bank account not found")
        
        # If setting as primary, unset others
        if data.is_primary:
            await db.bank_accounts.update_many(
                {"organization_id": account["organization_id"]},
                {"$set": {"is_primary": False}}
            )
        
        await db.bank_accounts.update_one(
            {"id": account_id},
            {"$set": {
                "bank_name": data.bank_name,
                "account_name": data.account_name,
                "account_number": data.account_number,
                "branch": data.branch,
                "swift_code": data.swift_code,
                "account_type": data.account_type,
                "is_primary": data.is_primary,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {"message": "Bank account updated"}
    
    @router.delete("/bank-accounts/{account_id}")
    async def delete_bank_account(account_id: str, user: dict = Depends(get_current_user)):
        """Delete bank account"""
        allowed_roles = ["hospital_admin", "hospital_it_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        await db.bank_accounts.update_one(
            {"id": account_id},
            {"$set": {"is_active": False, "deleted_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        return {"message": "Bank account removed"}
    
    # ============ MOBILE MONEY ACCOUNTS ============
    
    @router.get("/mobile-money-accounts")
    async def get_mobile_money_accounts(user: dict = Depends(get_current_user)):
        """Get mobile money accounts"""
        allowed_roles = ["biller", "hospital_admin", "hospital_it_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Access denied")
        
        org_id = user.get("organization_id")
        query = {"organization_id": org_id} if org_id else {}
        accounts = await db.mobile_money_accounts.find(query, {"_id": 0}).to_list(50)
        
        return {"accounts": accounts, "total": len(accounts)}
    
    @router.post("/mobile-money-accounts")
    async def create_mobile_money_account(
        data: MobileMoneyAccountCreate,
        user: dict = Depends(get_current_user)
    ):
        """Add mobile money account"""
        allowed_roles = ["biller", "hospital_admin", "hospital_it_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Access denied")
        
        org_id = user.get("organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="No organization context")
        
        # If primary, unset others
        if data.is_primary:
            await db.mobile_money_accounts.update_many(
                {"organization_id": org_id},
                {"$set": {"is_primary": False}}
            )
        
        account_id = str(uuid.uuid4())
        account_doc = {
            "id": account_id,
            "organization_id": org_id,
            "provider": data.provider,
            "account_name": data.account_name,
            "mobile_number": data.mobile_number,
            "wallet_id": data.wallet_id,
            "is_primary": data.is_primary,
            "is_active": True,
            "created_by": user.get("id"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.mobile_money_accounts.insert_one(account_doc)
        account_doc.pop("_id", None)
        
        return {"message": "Mobile money account added", "account": account_doc}
    
    return router


__all__ = ["router", "create_finance_endpoints"]
