"""
Pharmacy Supply Chain & Inventory Management Module
Track drug inventory, stock levels, reorder alerts, and expiry tracking
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from enum import Enum

inventory_router = APIRouter(prefix="/api/inventory", tags=["Pharmacy Inventory"])


# ============== Enums ==============

class StockStatus(str, Enum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    EXPIRED = "expired"
    EXPIRING_SOON = "expiring_soon"


class TransactionType(str, Enum):
    RECEIVED = "received"  # Stock received from supplier
    DISPENSED = "dispensed"  # Dispensed to patient
    RETURNED = "returned"  # Returned from patient
    ADJUSTED = "adjusted"  # Stock adjustment (audit)
    EXPIRED = "expired"  # Removed due to expiry
    TRANSFERRED = "transferred"  # Transferred to another location
    DAMAGED = "damaged"  # Removed due to damage


class ReorderStatus(str, Enum):
    PENDING = "pending"
    ORDERED = "ordered"
    RECEIVED = "received"
    CANCELLED = "cancelled"


# ============== Pydantic Models ==============

class InventoryItemCreate(BaseModel):
    drug_code: str
    drug_name: str
    generic_name: Optional[str] = None
    manufacturer: Optional[str] = None
    batch_number: str
    expiry_date: str  # YYYY-MM-DD
    quantity: int
    unit: str = "tablets"
    unit_cost: float
    selling_price: float
    reorder_level: int = 50  # Trigger reorder when stock falls below this
    location: Optional[str] = None  # Storage location
    nhis_code: Optional[str] = None  # NHIS tariff code
    fda_registration: Optional[str] = None


class StockTransaction(BaseModel):
    item_id: str
    transaction_type: TransactionType
    quantity: int
    reference_number: Optional[str] = None  # PO number, prescription ID, etc.
    notes: Optional[str] = None


class ReorderRequest(BaseModel):
    item_id: str
    quantity: int
    supplier_id: Optional[str] = None
    notes: Optional[str] = None


class InventoryAdjustment(BaseModel):
    item_id: str
    new_quantity: int
    reason: str


# ============== Sample Suppliers ==============

PHARMACY_SUPPLIERS = [
    {
        "id": "SUP-001",
        "name": "Ernest Chemist Wholesale",
        "contact": "0302-999000",
        "email": "wholesale@ernestchemist.com",
        "address": "Ring Road, Accra",
        "lead_time_days": 2
    },
    {
        "id": "SUP-002",
        "name": "Kinapharma Distribution",
        "contact": "0302-228800",
        "email": "orders@kinapharma.com",
        "address": "North Industrial Area, Accra",
        "lead_time_days": 3
    },
    {
        "id": "SUP-003",
        "name": "Tobinco Pharmaceuticals",
        "contact": "0303-204500",
        "email": "sales@tobinco.com",
        "address": "Tema Industrial Area",
        "lead_time_days": 2
    },
    {
        "id": "SUP-004",
        "name": "Letap Pharmaceuticals",
        "contact": "0302-815500",
        "email": "distribution@letap.com",
        "address": "Spintex Road, Accra",
        "lead_time_days": 3
    },
    {
        "id": "SUP-005",
        "name": "GNDP - Ghana National Drug Programme",
        "contact": "0302-684444",
        "email": "orders@gndp.gov.gh",
        "address": "Ministry of Health, Accra",
        "lead_time_days": 7
    }
]


def create_inventory_endpoints(db, get_current_user):
    """Create inventory management API endpoints"""
    
    # ============== Inventory Items ==============
    
    @inventory_router.get("/items")
    async def get_inventory_items(
        search: Optional[str] = None,
        status: Optional[str] = None,
        low_stock_only: bool = False,
        expiring_soon: bool = False,  # Within 90 days
        limit: int = Query(100, ge=1, le=500),
        offset: int = Query(0, ge=0),
        user: dict = Depends(get_current_user)
    ):
        """Get inventory items"""
        query = {"organization_id": user.get("organization_id")}
        
        if search:
            query["$or"] = [
                {"drug_name": {"$regex": search, "$options": "i"}},
                {"drug_code": {"$regex": search, "$options": "i"}},
                {"generic_name": {"$regex": search, "$options": "i"}},
                {"batch_number": {"$regex": search, "$options": "i"}}
            ]
        
        if status:
            query["stock_status"] = status
        
        if low_stock_only:
            query["$expr"] = {"$lte": ["$quantity", "$reorder_level"]}
        
        if expiring_soon:
            expiry_threshold = (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d")
            query["expiry_date"] = {"$lte": expiry_threshold}
        
        items = await db["inventory"].find(query, {"_id": 0}).sort("drug_name", 1).skip(offset).limit(limit).to_list(limit)
        total = await db["inventory"].count_documents(query)
        
        # Update stock status based on current quantity and expiry
        for item in items:
            item["stock_status"] = _calculate_stock_status(item)
        
        return {"items": items, "total": total}
    
    @inventory_router.post("/items")
    async def add_inventory_item(
        data: InventoryItemCreate,
        user: dict = Depends(get_current_user)
    ):
        """Add new inventory item"""
        allowed_roles = ["pharmacist", "pharmacy_tech", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        item_id = str(uuid.uuid4())
        
        item_doc = {
            "id": item_id,
            "drug_code": data.drug_code,
            "drug_name": data.drug_name,
            "generic_name": data.generic_name,
            "manufacturer": data.manufacturer,
            "batch_number": data.batch_number,
            "expiry_date": data.expiry_date,
            "quantity": data.quantity,
            "unit": data.unit,
            "unit_cost": data.unit_cost,
            "selling_price": data.selling_price,
            "reorder_level": data.reorder_level,
            "location": data.location,
            "nhis_code": data.nhis_code,
            "fda_registration": data.fda_registration,
            "stock_status": StockStatus.IN_STOCK.value,
            "total_value": data.quantity * data.unit_cost,
            "organization_id": user.get("organization_id"),
            "created_by": user.get("id"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["inventory"].insert_one(item_doc)
        
        if "_id" in item_doc:
            del item_doc["_id"]
        
        # Record transaction
        await _record_transaction(
            db, item_id, TransactionType.RECEIVED, data.quantity,
            f"Initial stock - {data.batch_number}", user
        )
        
        return {"message": "Inventory item added", "item": item_doc}
    
    @inventory_router.get("/items/{item_id}")
    async def get_inventory_item(
        item_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Get inventory item details"""
        item = await db["inventory"].find_one({"id": item_id}, {"_id": 0})
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        item["stock_status"] = _calculate_stock_status(item)
        
        # Get recent transactions
        transactions = await db["inventory_transactions"].find(
            {"item_id": item_id}, {"_id": 0}
        ).sort("created_at", -1).limit(20).to_list(20)
        
        return {"item": item, "recent_transactions": transactions}
    
    @inventory_router.put("/items/{item_id}")
    async def update_inventory_item(
        item_id: str,
        data: InventoryItemCreate,
        user: dict = Depends(get_current_user)
    ):
        """Update inventory item"""
        allowed_roles = ["pharmacist", "pharmacy_tech", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        update_data = {
            "drug_code": data.drug_code,
            "drug_name": data.drug_name,
            "generic_name": data.generic_name,
            "manufacturer": data.manufacturer,
            "batch_number": data.batch_number,
            "expiry_date": data.expiry_date,
            "unit": data.unit,
            "unit_cost": data.unit_cost,
            "selling_price": data.selling_price,
            "reorder_level": data.reorder_level,
            "location": data.location,
            "nhis_code": data.nhis_code,
            "fda_registration": data.fda_registration,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["inventory"].update_one({"id": item_id}, {"$set": update_data})
        
        return {"message": "Item updated"}
    
    # ============== Stock Transactions ==============
    
    @inventory_router.post("/transactions")
    async def record_transaction(
        data: StockTransaction,
        user: dict = Depends(get_current_user)
    ):
        """Record a stock transaction"""
        allowed_roles = ["pharmacist", "pharmacy_tech", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        item = await db["inventory"].find_one({"id": data.item_id})
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Calculate new quantity
        if data.transaction_type in [TransactionType.RECEIVED, TransactionType.RETURNED]:
            new_quantity = item["quantity"] + data.quantity
        else:
            new_quantity = item["quantity"] - data.quantity
            if new_quantity < 0:
                raise HTTPException(status_code=400, detail="Insufficient stock")
        
        # Update inventory
        await db["inventory"].update_one(
            {"id": data.item_id},
            {"$set": {
                "quantity": new_quantity,
                "total_value": new_quantity * item["unit_cost"],
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Record transaction
        transaction_id = await _record_transaction(
            db, data.item_id, data.transaction_type, data.quantity,
            data.notes, user, data.reference_number
        )
        
        return {
            "message": "Transaction recorded",
            "transaction_id": transaction_id,
            "new_quantity": new_quantity
        }
    
    @inventory_router.get("/transactions")
    async def get_transactions(
        item_id: Optional[str] = None,
        transaction_type: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        limit: int = Query(100, ge=1, le=500),
        user: dict = Depends(get_current_user)
    ):
        """Get stock transactions"""
        query = {"organization_id": user.get("organization_id")}
        
        if item_id:
            query["item_id"] = item_id
        if transaction_type:
            query["transaction_type"] = transaction_type
        if from_date:
            query["created_at"] = {"$gte": from_date}
        if to_date:
            if "created_at" in query:
                query["created_at"]["$lte"] = to_date + "T23:59:59"
            else:
                query["created_at"] = {"$lte": to_date + "T23:59:59"}
        
        transactions = await db["inventory_transactions"].find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
        
        return {"transactions": transactions, "total": len(transactions)}
    
    # ============== Stock Adjustments ==============
    
    @inventory_router.post("/adjust")
    async def adjust_stock(
        data: InventoryAdjustment,
        user: dict = Depends(get_current_user)
    ):
        """Adjust stock quantity (for audits, corrections)"""
        allowed_roles = ["pharmacist", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        item = await db["inventory"].find_one({"id": data.item_id})
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        old_quantity = item["quantity"]
        difference = data.new_quantity - old_quantity
        
        await db["inventory"].update_one(
            {"id": data.item_id},
            {"$set": {
                "quantity": data.new_quantity,
                "total_value": data.new_quantity * item["unit_cost"],
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Record adjustment
        await _record_transaction(
            db, data.item_id, TransactionType.ADJUSTED, abs(difference),
            f"Stock adjustment: {data.reason}. Old: {old_quantity}, New: {data.new_quantity}",
            user
        )
        
        return {
            "message": "Stock adjusted",
            "old_quantity": old_quantity,
            "new_quantity": data.new_quantity,
            "difference": difference
        }
    
    # ============== Reorder Management ==============
    
    @inventory_router.get("/reorder-alerts")
    async def get_reorder_alerts(user: dict = Depends(get_current_user)):
        """Get items that need reordering"""
        items = await db["inventory"].find(
            {
                "organization_id": user.get("organization_id"),
                "$expr": {"$lte": ["$quantity", "$reorder_level"]}
            },
            {"_id": 0}
        ).sort("quantity", 1).to_list(200)
        
        return {"items": items, "total": len(items)}
    
    @inventory_router.post("/reorder")
    async def create_reorder_request(
        data: ReorderRequest,
        user: dict = Depends(get_current_user)
    ):
        """Create a reorder request"""
        allowed_roles = ["pharmacist", "pharmacy_tech", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        item = await db["inventory"].find_one({"id": data.item_id})
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        reorder_id = str(uuid.uuid4())
        po_number = f"PO-{datetime.now().strftime('%Y%m%d')}-{reorder_id[:8].upper()}"
        
        reorder_doc = {
            "id": reorder_id,
            "po_number": po_number,
            "item_id": data.item_id,
            "drug_name": item["drug_name"],
            "drug_code": item["drug_code"],
            "quantity_ordered": data.quantity,
            "unit_cost": item["unit_cost"],
            "total_cost": data.quantity * item["unit_cost"],
            "supplier_id": data.supplier_id,
            "notes": data.notes,
            "status": ReorderStatus.PENDING.value,
            "organization_id": user.get("organization_id"),
            "requested_by": user.get("id"),
            "requested_by_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "received_at": None
        }
        
        await db["reorder_requests"].insert_one(reorder_doc)
        
        if "_id" in reorder_doc:
            del reorder_doc["_id"]
        
        return {"message": "Reorder request created", "reorder": reorder_doc}
    
    @inventory_router.get("/reorders")
    async def get_reorder_requests(
        status: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """Get reorder requests"""
        query = {"organization_id": user.get("organization_id")}
        if status:
            query["status"] = status
        
        reorders = await db["reorder_requests"].find(query, {"_id": 0}).sort("requested_at", -1).to_list(100)
        
        return {"reorders": reorders, "total": len(reorders)}
    
    @inventory_router.put("/reorders/{reorder_id}/receive")
    async def receive_reorder(
        reorder_id: str,
        quantity_received: int,
        batch_number: str,
        expiry_date: str,
        user: dict = Depends(get_current_user)
    ):
        """Mark reorder as received and update inventory"""
        allowed_roles = ["pharmacist", "pharmacy_tech", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        reorder = await db["reorder_requests"].find_one({"id": reorder_id})
        if not reorder:
            raise HTTPException(status_code=404, detail="Reorder not found")
        
        # Update reorder status
        await db["reorder_requests"].update_one(
            {"id": reorder_id},
            {"$set": {
                "status": ReorderStatus.RECEIVED.value,
                "quantity_received": quantity_received,
                "received_at": datetime.now(timezone.utc).isoformat(),
                "received_by": user.get("id")
            }}
        )
        
        # Update inventory
        item = await db["inventory"].find_one({"id": reorder["item_id"]})
        if item:
            new_quantity = item["quantity"] + quantity_received
            await db["inventory"].update_one(
                {"id": reorder["item_id"]},
                {"$set": {
                    "quantity": new_quantity,
                    "batch_number": batch_number,
                    "expiry_date": expiry_date,
                    "total_value": new_quantity * item["unit_cost"],
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # Record transaction
            await _record_transaction(
                db, reorder["item_id"], TransactionType.RECEIVED, quantity_received,
                f"Received from PO: {reorder['po_number']}", user, reorder["po_number"]
            )
        
        return {"message": "Reorder received", "quantity_received": quantity_received}
    
    # ============== Expiry Management ==============
    
    @inventory_router.get("/expiring")
    async def get_expiring_items(
        days: int = Query(90, description="Days until expiry"),
        user: dict = Depends(get_current_user)
    ):
        """Get items expiring within specified days"""
        expiry_threshold = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        
        items = await db["inventory"].find(
            {
                "organization_id": user.get("organization_id"),
                "expiry_date": {"$lte": expiry_threshold},
                "quantity": {"$gt": 0}
            },
            {"_id": 0}
        ).sort("expiry_date", 1).to_list(200)
        
        # Calculate days until expiry
        today = datetime.now().date()
        for item in items:
            expiry = datetime.strptime(item["expiry_date"], "%Y-%m-%d").date()
            item["days_until_expiry"] = (expiry - today).days
            item["is_expired"] = item["days_until_expiry"] < 0
        
        return {"items": items, "total": len(items)}
    
    @inventory_router.post("/items/{item_id}/dispose")
    async def dispose_expired_item(
        item_id: str,
        quantity: int,
        reason: str = "Expired",
        user: dict = Depends(get_current_user)
    ):
        """Dispose of expired items"""
        allowed_roles = ["pharmacist", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        item = await db["inventory"].find_one({"id": item_id})
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        if quantity > item["quantity"]:
            raise HTTPException(status_code=400, detail="Quantity exceeds current stock")
        
        new_quantity = item["quantity"] - quantity
        
        await db["inventory"].update_one(
            {"id": item_id},
            {"$set": {
                "quantity": new_quantity,
                "total_value": new_quantity * item["unit_cost"],
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        await _record_transaction(
            db, item_id, TransactionType.EXPIRED, quantity,
            f"Disposed: {reason}", user
        )
        
        return {"message": f"Disposed {quantity} units", "remaining": new_quantity}
    
    # ============== Suppliers ==============
    
    @inventory_router.get("/suppliers")
    async def get_suppliers():
        """Get list of suppliers"""
        return {"suppliers": PHARMACY_SUPPLIERS, "total": len(PHARMACY_SUPPLIERS)}
    
    # ============== Dashboard ==============
    
    @inventory_router.get("/dashboard")
    async def get_inventory_dashboard(user: dict = Depends(get_current_user)):
        """Get inventory dashboard stats"""
        org_id = user.get("organization_id")
        
        # Total items
        total_items = await db["inventory"].count_documents({"organization_id": org_id})
        
        # Low stock items
        low_stock = await db["inventory"].count_documents({
            "organization_id": org_id,
            "$expr": {"$lte": ["$quantity", "$reorder_level"]}
        })
        
        # Out of stock
        out_of_stock = await db["inventory"].count_documents({
            "organization_id": org_id,
            "quantity": 0
        })
        
        # Expiring within 30 days
        expiry_30 = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        expiring_soon = await db["inventory"].count_documents({
            "organization_id": org_id,
            "expiry_date": {"$lte": expiry_30},
            "quantity": {"$gt": 0}
        })
        
        # Total inventory value
        items = await db["inventory"].find({"organization_id": org_id}, {"total_value": 1}).to_list(10000)
        total_value = sum(item.get("total_value", 0) for item in items)
        
        # Pending reorders
        pending_reorders = await db["reorder_requests"].count_documents({
            "organization_id": org_id,
            "status": ReorderStatus.PENDING.value
        })
        
        return {
            "summary": {
                "total_items": total_items,
                "low_stock": low_stock,
                "out_of_stock": out_of_stock,
                "expiring_soon": expiring_soon
            },
            "financials": {
                "total_inventory_value": round(total_value, 2)
            },
            "reorders": {
                "pending": pending_reorders
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    return inventory_router


# ============== Helper Functions ==============

def _calculate_stock_status(item):
    """Calculate stock status based on quantity and expiry"""
    today = datetime.now().date()
    expiry = datetime.strptime(item["expiry_date"], "%Y-%m-%d").date()
    
    if expiry < today:
        return StockStatus.EXPIRED.value
    
    if item["quantity"] == 0:
        return StockStatus.OUT_OF_STOCK.value
    
    if item["quantity"] <= item.get("reorder_level", 50):
        return StockStatus.LOW_STOCK.value
    
    if (expiry - today).days <= 90:
        return StockStatus.EXPIRING_SOON.value
    
    return StockStatus.IN_STOCK.value


async def _record_transaction(db, item_id, transaction_type, quantity, notes, user, reference=None):
    """Record inventory transaction"""
    transaction_id = str(uuid.uuid4())
    
    item = await db["inventory"].find_one({"id": item_id}, {"drug_name": 1, "drug_code": 1})
    
    transaction_doc = {
        "id": transaction_id,
        "item_id": item_id,
        "drug_name": item.get("drug_name") if item else None,
        "drug_code": item.get("drug_code") if item else None,
        "transaction_type": transaction_type.value if hasattr(transaction_type, "value") else transaction_type,
        "quantity": quantity,
        "reference_number": reference,
        "notes": notes,
        "user_id": user.get("id") if user else None,
        "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}" if user else None,
        "organization_id": user.get("organization_id") if user else None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db["inventory_transactions"].insert_one(transaction_doc)
    return transaction_id
