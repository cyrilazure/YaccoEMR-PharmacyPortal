"""
Supply Chain & Inventory Management Module for Yacco EMR
Manage pharmacy inventory, stock levels, expiry tracking, and procurement
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from enum import Enum

supply_chain_router = APIRouter(prefix="/api/supply-chain", tags=["Supply Chain & Inventory"])


# ============== Enums ==============

class StockStatus(str, Enum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    EXPIRED = "expired"
    EXPIRING_SOON = "expiring_soon"


class MovementType(str, Enum):
    RECEIVED = "received"
    DISPENSED = "dispensed"
    TRANSFERRED = "transferred"
    RETURNED = "returned"
    EXPIRED = "expired"
    DAMAGED = "damaged"
    ADJUSTMENT = "adjustment"


class OrderStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    ORDERED = "ordered"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class UnitOfMeasure(str, Enum):
    TABLET = "tablet"
    CAPSULE = "capsule"
    VIAL = "vial"
    AMPULE = "ampule"
    BOTTLE = "bottle"
    TUBE = "tube"
    SACHET = "sachet"
    BOX = "box"
    PACK = "pack"
    UNIT = "unit"


# ============== Pydantic Models ==============

class InventoryItemCreate(BaseModel):
    drug_name: str
    drug_code: Optional[str] = None
    fda_registration: Optional[str] = None
    manufacturer: Optional[str] = None
    category: Optional[str] = None
    unit_of_measure: UnitOfMeasure = UnitOfMeasure.TABLET
    unit_cost: float = 0.0
    selling_price: float = 0.0
    reorder_level: int = 10
    max_stock_level: int = 1000
    storage_location: Optional[str] = None
    storage_conditions: Optional[str] = None  # e.g., "Room temp", "Refrigerated"
    is_controlled: bool = False
    schedule: Optional[str] = None  # OTC, POM, CD


class StockReceiptCreate(BaseModel):
    inventory_item_id: str
    quantity: int
    batch_number: str
    expiry_date: str  # YYYY-MM-DD
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    purchase_order_id: Optional[str] = None
    unit_cost: Optional[float] = None
    invoice_number: Optional[str] = None
    notes: Optional[str] = None


class StockMovementCreate(BaseModel):
    inventory_item_id: str
    batch_id: str
    quantity: int
    movement_type: MovementType
    reference_id: Optional[str] = None  # Prescription ID, Transfer ID, etc.
    reference_type: Optional[str] = None  # prescription, transfer, etc.
    destination: Optional[str] = None  # For transfers
    reason: Optional[str] = None
    notes: Optional[str] = None


class PurchaseOrderCreate(BaseModel):
    supplier_id: Optional[str] = None
    supplier_name: str
    expected_date: Optional[str] = None
    items: List[dict]  # [{inventory_item_id, drug_name, quantity, unit_cost}]
    notes: Optional[str] = None


class SupplierCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    payment_terms: Optional[str] = None
    is_active: bool = True


# ============== Seed Data: Common Ghana Pharmaceutical Suppliers ==============

SEED_SUPPLIERS = [
    {"name": "Ernest Chemist Ltd", "city": "Accra", "region": "Greater Accra", "phone": "+233 302 500 100"},
    {"name": "Kinapharma Ltd", "city": "Accra", "region": "Greater Accra", "phone": "+233 302 812 321"},
    {"name": "mPharma Ghana", "city": "Accra", "region": "Greater Accra", "phone": "+233 302 763 000"},
    {"name": "Tobinco Pharmaceuticals", "city": "Accra", "region": "Greater Accra", "phone": "+233 302 400 200"},
    {"name": "Atlantic Lifesciences", "city": "Tema", "region": "Greater Accra", "phone": "+233 303 200 100"},
    {"name": "Dannex Ayrton Starwin", "city": "Accra", "region": "Greater Accra", "phone": "+233 302 666 333"},
    {"name": "Entrance Pharmaceuticals", "city": "Kumasi", "region": "Ashanti", "phone": "+233 322 199 100"},
    {"name": "Kama Healthcare", "city": "Tema", "region": "Greater Accra", "phone": "+233 303 307 000"},
]


def create_supply_chain_endpoints(db, get_current_user):
    """Create supply chain and inventory API endpoints"""
    
    # ============== Inventory Items ==============
    
    @supply_chain_router.get("/inventory")
    async def get_inventory(
        search: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        low_stock_only: bool = False,
        limit: int = Query(100, ge=1, le=500),
        offset: int = Query(0, ge=0),
        user: dict = Depends(get_current_user)
    ):
        """Get pharmacy inventory items"""
        query = {"organization_id": user.get("organization_id"), "is_active": True}
        
        if search:
            query["$or"] = [
                {"drug_name": {"$regex": search, "$options": "i"}},
                {"drug_code": {"$regex": search, "$options": "i"}},
                {"fda_registration": {"$regex": search, "$options": "i"}}
            ]
        
        if category:
            query["category"] = category
        
        if low_stock_only:
            # Get items where current stock <= reorder level
            query["$expr"] = {"$lte": ["$current_stock", "$reorder_level"]}
        
        items = await db["inventory_items"].find(query, {"_id": 0}).sort("drug_name", 1).skip(offset).limit(limit).to_list(limit)
        total = await db["inventory_items"].count_documents(query)
        
        # Enhance with stock status
        for item in items:
            stock = item.get("current_stock", 0)
            reorder = item.get("reorder_level", 10)
            if stock == 0:
                item["stock_status"] = StockStatus.OUT_OF_STOCK.value
            elif stock <= reorder:
                item["stock_status"] = StockStatus.LOW_STOCK.value
            else:
                item["stock_status"] = StockStatus.IN_STOCK.value
        
        return {"items": items, "total": total, "limit": limit, "offset": offset}
    
    @supply_chain_router.post("/inventory")
    async def create_inventory_item(
        data: InventoryItemCreate,
        user: dict = Depends(get_current_user)
    ):
        """Add new item to inventory catalog"""
        allowed_roles = ["pharmacist", "pharmacy_tech", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        item_id = str(uuid.uuid4())
        drug_code = data.drug_code or f"DRG-{item_id[:8].upper()}"
        
        item_doc = {
            "id": item_id,
            "drug_name": data.drug_name,
            "drug_code": drug_code,
            "fda_registration": data.fda_registration,
            "manufacturer": data.manufacturer,
            "category": data.category,
            "unit_of_measure": data.unit_of_measure.value if hasattr(data.unit_of_measure, "value") else data.unit_of_measure,
            "unit_cost": data.unit_cost,
            "selling_price": data.selling_price,
            "reorder_level": data.reorder_level,
            "max_stock_level": data.max_stock_level,
            "current_stock": 0,
            "storage_location": data.storage_location,
            "storage_conditions": data.storage_conditions,
            "is_controlled": data.is_controlled,
            "schedule": data.schedule,
            "organization_id": user.get("organization_id"),
            "is_active": True,
            "created_by_id": user.get("id"),
            "created_by_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["inventory_items"].insert_one(item_doc)
        
        if "_id" in item_doc:
            del item_doc["_id"]
        
        return {"message": "Inventory item created", "item": item_doc}
    
    @supply_chain_router.get("/inventory/{item_id}")
    async def get_inventory_item(
        item_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Get inventory item details with batch info"""
        item = await db["inventory_items"].find_one({"id": item_id}, {"_id": 0})
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Get batches for this item
        batches = await db["inventory_batches"].find(
            {"inventory_item_id": item_id, "quantity_remaining": {"$gt": 0}},
            {"_id": 0}
        ).sort("expiry_date", 1).to_list(100)
        
        item["batches"] = batches
        return item
    
    @supply_chain_router.put("/inventory/{item_id}")
    async def update_inventory_item(
        item_id: str,
        data: InventoryItemCreate,
        user: dict = Depends(get_current_user)
    ):
        """Update inventory item"""
        allowed_roles = ["pharmacist", "pharmacy_tech", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        update_data = data.model_dump()
        update_data["unit_of_measure"] = update_data["unit_of_measure"].value if hasattr(update_data["unit_of_measure"], "value") else update_data["unit_of_measure"]
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await db["inventory_items"].update_one({"id": item_id}, {"$set": update_data})
        
        return {"message": "Item updated"}
    
    # ============== Stock Receipts / Receiving ==============
    
    @supply_chain_router.post("/stock/receive")
    async def receive_stock(
        data: StockReceiptCreate,
        user: dict = Depends(get_current_user)
    ):
        """Receive stock into inventory"""
        allowed_roles = ["pharmacist", "pharmacy_tech", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Verify item exists
        item = await db["inventory_items"].find_one({"id": data.inventory_item_id})
        if not item:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        
        batch_id = str(uuid.uuid4())
        receipt_id = str(uuid.uuid4())
        
        # Create batch record
        batch_doc = {
            "id": batch_id,
            "inventory_item_id": data.inventory_item_id,
            "drug_name": item.get("drug_name"),
            "batch_number": data.batch_number,
            "expiry_date": data.expiry_date,
            "quantity_received": data.quantity,
            "quantity_remaining": data.quantity,
            "unit_cost": data.unit_cost or item.get("unit_cost", 0),
            "supplier_id": data.supplier_id,
            "supplier_name": data.supplier_name,
            "purchase_order_id": data.purchase_order_id,
            "invoice_number": data.invoice_number,
            "organization_id": user.get("organization_id"),
            "received_by_id": user.get("id"),
            "received_by_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "received_at": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["inventory_batches"].insert_one(batch_doc)
        
        # Create stock movement record
        movement_doc = {
            "id": receipt_id,
            "inventory_item_id": data.inventory_item_id,
            "batch_id": batch_id,
            "drug_name": item.get("drug_name"),
            "movement_type": MovementType.RECEIVED.value,
            "quantity": data.quantity,
            "reference_id": data.purchase_order_id,
            "reference_type": "purchase_order" if data.purchase_order_id else None,
            "notes": data.notes,
            "organization_id": user.get("organization_id"),
            "performed_by_id": user.get("id"),
            "performed_by_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["stock_movements"].insert_one(movement_doc)
        
        # Update item's current stock
        await db["inventory_items"].update_one(
            {"id": data.inventory_item_id},
            {"$inc": {"current_stock": data.quantity}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Remove _id before returning
        if "_id" in batch_doc:
            del batch_doc["_id"]
        
        # Create activity log for auditing
        activity_log = {
            "id": str(uuid.uuid4()),
            "action": "stock_received",
            "module": "pharmacy_inventory",
            "entity_type": "inventory_batch",
            "entity_id": batch_id,
            "description": f"Received {data.quantity} units of {item.get('drug_name')} (Batch: {data.batch_number})",
            "details": {
                "drug_name": item.get("drug_name"),
                "quantity": data.quantity,
                "batch_number": data.batch_number,
                "expiry_date": data.expiry_date,
                "supplier": data.supplier_name,
                "unit_cost": data.unit_cost,
                "new_stock_level": (item.get("current_stock", 0) + data.quantity)
            },
            "user_id": user.get("id"),
            "user_email": user.get("email"),
            "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "user_role": user.get("role"),
            "organization_id": user.get("organization_id"),
            "ip_address": None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await db["pharmacy_activity_logs"].insert_one(activity_log)
        
        return {
            "message": "Stock received successfully",
            "batch": batch_doc,
            "new_stock_level": (item.get("current_stock", 0) + data.quantity)
        }
    
    @supply_chain_router.get("/stock/batches")
    async def get_batches(
        inventory_item_id: Optional[str] = None,
        expiring_within_days: Optional[int] = None,
        user: dict = Depends(get_current_user)
    ):
        """Get stock batches"""
        query = {"organization_id": user.get("organization_id"), "quantity_remaining": {"$gt": 0}}
        
        if inventory_item_id:
            query["inventory_item_id"] = inventory_item_id
        
        if expiring_within_days:
            expiry_threshold = (datetime.now(timezone.utc) + timedelta(days=expiring_within_days)).strftime("%Y-%m-%d")
            query["expiry_date"] = {"$lte": expiry_threshold}
        
        batches = await db["inventory_batches"].find(query, {"_id": 0}).sort("expiry_date", 1).to_list(500)
        
        return {"batches": batches, "total": len(batches)}
    
    # ============== Stock Movements (Dispense, Transfer, etc.) ==============
    
    @supply_chain_router.post("/stock/movement")
    async def record_stock_movement(
        data: StockMovementCreate,
        user: dict = Depends(get_current_user)
    ):
        """Record stock movement (dispense, transfer, adjustment, etc.)"""
        allowed_roles = ["pharmacist", "pharmacy_tech", "nurse", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Verify batch exists and has enough stock
        batch = await db["inventory_batches"].find_one({"id": data.batch_id})
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        
        # For outgoing movements, check stock availability
        outgoing_types = [MovementType.DISPENSED, MovementType.TRANSFERRED, MovementType.EXPIRED, MovementType.DAMAGED]
        if data.movement_type in outgoing_types:
            if batch.get("quantity_remaining", 0) < data.quantity:
                raise HTTPException(status_code=400, detail=f"Insufficient stock. Available: {batch.get('quantity_remaining', 0)}")
        
        movement_id = str(uuid.uuid4())
        
        movement_doc = {
            "id": movement_id,
            "inventory_item_id": data.inventory_item_id,
            "batch_id": data.batch_id,
            "drug_name": batch.get("drug_name"),
            "batch_number": batch.get("batch_number"),
            "movement_type": data.movement_type.value if hasattr(data.movement_type, "value") else data.movement_type,
            "quantity": data.quantity,
            "reference_id": data.reference_id,
            "reference_type": data.reference_type,
            "destination": data.destination,
            "reason": data.reason,
            "notes": data.notes,
            "organization_id": user.get("organization_id"),
            "performed_by_id": user.get("id"),
            "performed_by_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["stock_movements"].insert_one(movement_doc)
        
        # Update batch and item quantities
        quantity_change = -data.quantity if data.movement_type in outgoing_types else data.quantity
        
        await db["inventory_batches"].update_one(
            {"id": data.batch_id},
            {"$inc": {"quantity_remaining": quantity_change}}
        )
        
        await db["inventory_items"].update_one(
            {"id": data.inventory_item_id},
            {"$inc": {"current_stock": quantity_change}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        return {"message": "Stock movement recorded", "movement_id": movement_id}
    
    @supply_chain_router.get("/stock/movements")
    async def get_stock_movements(
        inventory_item_id: Optional[str] = None,
        batch_id: Optional[str] = None,
        movement_type: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        limit: int = Query(100, ge=1, le=500),
        user: dict = Depends(get_current_user)
    ):
        """Get stock movement history"""
        query = {"organization_id": user.get("organization_id")}
        
        if inventory_item_id:
            query["inventory_item_id"] = inventory_item_id
        if batch_id:
            query["batch_id"] = batch_id
        if movement_type:
            query["movement_type"] = movement_type
        if from_date:
            query["created_at"] = {"$gte": from_date}
        if to_date:
            query.setdefault("created_at", {})["$lte"] = to_date + "T23:59:59"
        
        movements = await db["stock_movements"].find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
        
        return {"movements": movements, "total": len(movements)}
    
    # ============== Purchase Orders ==============
    
    @supply_chain_router.post("/purchase-orders")
    async def create_purchase_order(
        data: PurchaseOrderCreate,
        user: dict = Depends(get_current_user)
    ):
        """Create purchase order"""
        allowed_roles = ["pharmacist", "pharmacy_tech", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        po_id = str(uuid.uuid4())
        po_number = f"PO-{datetime.now().strftime('%Y%m%d')}-{po_id[:6].upper()}"
        
        # Calculate totals
        total_items = len(data.items)
        total_quantity = sum(item.get("quantity", 0) for item in data.items)
        total_amount = sum(item.get("quantity", 0) * item.get("unit_cost", 0) for item in data.items)
        
        po_doc = {
            "id": po_id,
            "po_number": po_number,
            "supplier_id": data.supplier_id,
            "supplier_name": data.supplier_name,
            "expected_date": data.expected_date,
            "items": data.items,
            "total_items": total_items,
            "total_quantity": total_quantity,
            "total_amount": round(total_amount, 2),
            "status": OrderStatus.DRAFT.value,
            "notes": data.notes,
            "organization_id": user.get("organization_id"),
            "created_by_id": user.get("id"),
            "created_by_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["purchase_orders"].insert_one(po_doc)
        
        if "_id" in po_doc:
            del po_doc["_id"]
        
        return {"message": "Purchase order created", "purchase_order": po_doc}
    
    @supply_chain_router.get("/purchase-orders")
    async def get_purchase_orders(
        status: Optional[str] = None,
        supplier_id: Optional[str] = None,
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        user: dict = Depends(get_current_user)
    ):
        """Get purchase orders"""
        query = {"organization_id": user.get("organization_id")}
        
        if status:
            query["status"] = status
        if supplier_id:
            query["supplier_id"] = supplier_id
        
        orders = await db["purchase_orders"].find(query, {"_id": 0}).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
        total = await db["purchase_orders"].count_documents(query)
        
        return {"orders": orders, "total": total, "limit": limit, "offset": offset}
    
    @supply_chain_router.put("/purchase-orders/{po_id}/status")
    async def update_purchase_order_status(
        po_id: str,
        status: OrderStatus,
        notes: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """Update purchase order status"""
        update_data = {
            "status": status.value if hasattr(status, "value") else status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if notes:
            update_data["status_notes"] = notes
        
        if status == OrderStatus.APPROVED:
            update_data["approved_at"] = datetime.now(timezone.utc).isoformat()
            update_data["approved_by_id"] = user.get("id")
        
        await db["purchase_orders"].update_one({"id": po_id}, {"$set": update_data})
        
        return {"message": f"Purchase order status updated to {status}"}
    
    # ============== Suppliers ==============
    
    @supply_chain_router.get("/suppliers")
    async def get_suppliers(
        search: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """Get suppliers"""
        query = {"organization_id": user.get("organization_id"), "is_active": True}
        
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"city": {"$regex": search, "$options": "i"}}
            ]
        
        suppliers = await db["suppliers"].find(query, {"_id": 0}).sort("name", 1).to_list(200)
        
        return {"suppliers": suppliers, "total": len(suppliers)}
    
    @supply_chain_router.post("/suppliers")
    async def create_supplier(
        data: SupplierCreate,
        user: dict = Depends(get_current_user)
    ):
        """Add new supplier"""
        allowed_roles = ["pharmacist", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        supplier_id = str(uuid.uuid4())
        
        supplier_doc = {
            "id": supplier_id,
            "name": data.name,
            "contact_person": data.contact_person,
            "email": data.email,
            "phone": data.phone,
            "address": data.address,
            "city": data.city,
            "region": data.region,
            "payment_terms": data.payment_terms,
            "is_active": data.is_active,
            "organization_id": user.get("organization_id"),
            "created_by_id": user.get("id"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db["suppliers"].insert_one(supplier_doc)
        
        if "_id" in supplier_doc:
            del supplier_doc["_id"]
        
        return {"message": "Supplier created", "supplier": supplier_doc}
    
    @supply_chain_router.post("/suppliers/seed")
    async def seed_suppliers(user: dict = Depends(get_current_user)):
        """Seed common Ghana pharmaceutical suppliers"""
        allowed_roles = ["hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        created = 0
        for supplier in SEED_SUPPLIERS:
            existing = await db["suppliers"].find_one({
                "name": supplier["name"],
                "organization_id": user.get("organization_id")
            })
            
            if not existing:
                supplier_doc = {
                    "id": str(uuid.uuid4()),
                    **supplier,
                    "is_active": True,
                    "organization_id": user.get("organization_id"),
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db["suppliers"].insert_one(supplier_doc)
                created += 1
        
        return {"message": f"Seeded {created} suppliers", "total_seeded": created}
    
    # ============== Dashboard & Reports ==============
    
    @supply_chain_router.get("/dashboard")
    async def get_inventory_dashboard(user: dict = Depends(get_current_user)):
        """Get inventory dashboard statistics"""
        org_id = user.get("organization_id")
        
        # Inventory stats
        total_items = await db["inventory_items"].count_documents({"organization_id": org_id, "is_active": True})
        
        # Get all items for aggregation
        items = await db["inventory_items"].find({"organization_id": org_id, "is_active": True}, {"_id": 0}).to_list(10000)
        
        out_of_stock = len([i for i in items if i.get("current_stock", 0) == 0])
        low_stock = len([i for i in items if 0 < i.get("current_stock", 0) <= i.get("reorder_level", 10)])
        
        total_value = sum(i.get("current_stock", 0) * i.get("unit_cost", 0) for i in items)
        
        # Expiring items (within 90 days)
        expiry_threshold = (datetime.now(timezone.utc) + timedelta(days=90)).strftime("%Y-%m-%d")
        expiring_batches = await db["inventory_batches"].count_documents({
            "organization_id": org_id,
            "quantity_remaining": {"$gt": 0},
            "expiry_date": {"$lte": expiry_threshold}
        })
        
        # Recent movements
        recent_movements = await db["stock_movements"].find(
            {"organization_id": org_id},
            {"_id": 0}
        ).sort("created_at", -1).limit(10).to_list(10)
        
        # Pending POs
        pending_pos = await db["purchase_orders"].count_documents({
            "organization_id": org_id,
            "status": {"$in": [OrderStatus.SUBMITTED.value, OrderStatus.APPROVED.value, OrderStatus.ORDERED.value]}
        })
        
        return {
            "inventory": {
                "total_items": total_items,
                "out_of_stock": out_of_stock,
                "low_stock": low_stock,
                "total_value": round(total_value, 2)
            },
            "alerts": {
                "expiring_soon": expiring_batches,
                "needs_reorder": low_stock
            },
            "purchase_orders": {
                "pending": pending_pos
            },
            "recent_movements": recent_movements,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    @supply_chain_router.get("/reports/expiring")
    async def get_expiring_items_report(
        days: int = Query(90, ge=1, le=365),
        user: dict = Depends(get_current_user)
    ):
        """Get report of items expiring within specified days"""
        expiry_threshold = (datetime.now(timezone.utc) + timedelta(days=days)).strftime("%Y-%m-%d")
        
        batches = await db["inventory_batches"].find({
            "organization_id": user.get("organization_id"),
            "quantity_remaining": {"$gt": 0},
            "expiry_date": {"$lte": expiry_threshold}
        }, {"_id": 0}).sort("expiry_date", 1).to_list(500)
        
        total_value = sum(b.get("quantity_remaining", 0) * b.get("unit_cost", 0) for b in batches)
        
        return {
            "period_days": days,
            "batches": batches,
            "total_batches": len(batches),
            "total_units_expiring": sum(b.get("quantity_remaining", 0) for b in batches),
            "total_value_at_risk": round(total_value, 2),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    @supply_chain_router.get("/reports/stock-valuation")
    async def get_stock_valuation_report(user: dict = Depends(get_current_user)):
        """Get stock valuation report"""
        items = await db["inventory_items"].find(
            {"organization_id": user.get("organization_id"), "is_active": True},
            {"_id": 0}
        ).to_list(10000)
        
        # Calculate valuations
        by_category = {}
        total_value = 0
        
        for item in items:
            stock = item.get("current_stock", 0)
            cost = item.get("unit_cost", 0)
            value = stock * cost
            total_value += value
            
            category = item.get("category", "Uncategorized")
            if category not in by_category:
                by_category[category] = {"items": 0, "units": 0, "value": 0}
            by_category[category]["items"] += 1
            by_category[category]["units"] += stock
            by_category[category]["value"] += value
        
        # Round values
        for cat in by_category:
            by_category[cat]["value"] = round(by_category[cat]["value"], 2)
        
        return {
            "total_items": len(items),
            "total_units": sum(i.get("current_stock", 0) for i in items),
            "total_value": round(total_value, 2),
            "by_category": by_category,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    @supply_chain_router.get("/alerts")
    async def get_stock_alerts(user: dict = Depends(get_current_user)):
        """Get current stock alerts (low stock and expiring items)"""
        org_id = user.get("organization_id")
        
        # Low stock items
        low_stock_items = await db["inventory_items"].find({
            "organization_id": org_id,
            "is_active": True,
            "$expr": {"$lte": ["$current_stock", "$reorder_level"]},
            "current_stock": {"$gt": 0}
        }, {"_id": 0}).to_list(100)
        
        # Out of stock items
        out_of_stock_items = await db["inventory_items"].find({
            "organization_id": org_id,
            "is_active": True,
            "current_stock": 0
        }, {"_id": 0}).to_list(100)
        
        # Expiring batches (within 90 days)
        expiry_threshold = (datetime.now(timezone.utc) + timedelta(days=90)).strftime("%Y-%m-%d")
        expiring_batches = await db["inventory_batches"].find({
            "organization_id": org_id,
            "quantity_remaining": {"$gt": 0},
            "expiry_date": {"$lte": expiry_threshold}
        }, {"_id": 0}).sort("expiry_date", 1).to_list(100)
        
        return {
            "low_stock": {
                "count": len(low_stock_items),
                "items": low_stock_items[:20]
            },
            "out_of_stock": {
                "count": len(out_of_stock_items),
                "items": out_of_stock_items[:20]
            },
            "expiring_soon": {
                "count": len(expiring_batches),
                "batches": expiring_batches[:20]
            },
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
    
    @supply_chain_router.post("/alerts/send-notifications")
    async def send_stock_alert_notifications(
        user: dict = Depends(get_current_user)
    ):
        """Send notifications to pharmacists about low stock and expiring items"""
        allowed_roles = ["pharmacist", "pharmacy_tech", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        org_id = user.get("organization_id")
        notifications_created = 0
        
        # Get low stock items
        low_stock_items = await db["inventory_items"].find({
            "organization_id": org_id,
            "is_active": True,
            "$expr": {"$lte": ["$current_stock", "$reorder_level"]},
            "current_stock": {"$gt": 0}
        }, {"_id": 0, "id": 1, "drug_name": 1, "current_stock": 1, "reorder_level": 1}).to_list(50)
        
        # Get out of stock items
        out_of_stock = await db["inventory_items"].find({
            "organization_id": org_id,
            "is_active": True,
            "current_stock": 0
        }, {"_id": 0, "id": 1, "drug_name": 1}).to_list(50)
        
        # Get expiring batches (within 30 days - urgent)
        expiry_threshold = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")
        expiring = await db["inventory_batches"].find({
            "organization_id": org_id,
            "quantity_remaining": {"$gt": 0},
            "expiry_date": {"$lte": expiry_threshold}
        }, {"_id": 0, "id": 1, "drug_name": 1, "batch_number": 1, "expiry_date": 1, "quantity_remaining": 1}).to_list(50)
        
        # Find pharmacy staff to notify
        pharmacy_users = await db["users"].find({
            "organization_id": org_id,
            "role": {"$in": ["pharmacist", "pharmacy_tech"]},
            "is_active": True
        }, {"id": 1}).to_list(100)
        
        now = datetime.now(timezone.utc).isoformat()
        
        # Create notifications for each pharmacy staff member
        for pharm_user in pharmacy_users:
            # Low stock alert
            if low_stock_items:
                drug_names = ", ".join([i["drug_name"] for i in low_stock_items[:5]])
                more = f" and {len(low_stock_items) - 5} more" if len(low_stock_items) > 5 else ""
                await db["notifications"].insert_one({
                    "id": str(uuid.uuid4()),
                    "recipient_id": pharm_user["id"],
                    "title": f"Low Stock Alert: {len(low_stock_items)} items",
                    "message": f"The following items are below reorder level: {drug_names}{more}. Please review and create purchase orders.",
                    "notification_type": "low_stock",
                    "priority": "high",
                    "action_url": "/pharmacy",
                    "read": False,
                    "organization_id": org_id,
                    "created_at": now
                })
                notifications_created += 1
            
            # Out of stock alert
            if out_of_stock:
                drug_names = ", ".join([i["drug_name"] for i in out_of_stock[:5]])
                more = f" and {len(out_of_stock) - 5} more" if len(out_of_stock) > 5 else ""
                await db["notifications"].insert_one({
                    "id": str(uuid.uuid4()),
                    "recipient_id": pharm_user["id"],
                    "title": f"Out of Stock: {len(out_of_stock)} items",
                    "message": f"URGENT: The following items are out of stock: {drug_names}{more}. Immediate action required.",
                    "notification_type": "low_stock",
                    "priority": "urgent",
                    "action_url": "/pharmacy",
                    "read": False,
                    "organization_id": org_id,
                    "created_at": now
                })
                notifications_created += 1
            
            # Expiring items alert
            if expiring:
                batch_info = ", ".join([f"{b['drug_name']} ({b['batch_number']})" for b in expiring[:3]])
                more = f" and {len(expiring) - 3} more" if len(expiring) > 3 else ""
                await db["notifications"].insert_one({
                    "id": str(uuid.uuid4()),
                    "recipient_id": pharm_user["id"],
                    "title": f"Expiring Soon: {len(expiring)} batches",
                    "message": f"The following batches will expire within 30 days: {batch_info}{more}. Consider FEFO dispensing.",
                    "notification_type": "expiring_drugs",
                    "priority": "high",
                    "action_url": "/pharmacy",
                    "read": False,
                    "organization_id": org_id,
                    "created_at": now
                })
                notifications_created += 1
        
        return {
            "message": f"Sent {notifications_created} notifications",
            "alerts_summary": {
                "low_stock_items": len(low_stock_items),
                "out_of_stock_items": len(out_of_stock),
                "expiring_batches": len(expiring)
            },
            "recipients": len(pharmacy_users)
        }
    
    @supply_chain_router.get("/activity-logs")
    async def get_pharmacy_activity_logs(
        action: Optional[str] = None,
        user_id: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        limit: int = Query(100, ge=1, le=500),
        offset: int = Query(0, ge=0),
        user: dict = Depends(get_current_user)
    ):
        """Get pharmacy activity logs for auditing"""
        allowed_roles = ["pharmacist", "pharmacy_tech", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized to view activity logs")
        
        query = {"organization_id": user.get("organization_id")}
        
        if action:
            query["action"] = action
        if user_id:
            query["user_id"] = user_id
        if from_date:
            query["timestamp"] = {"$gte": from_date}
        if to_date:
            query.setdefault("timestamp", {})["$lte"] = to_date + "T23:59:59"
        
        logs = await db["pharmacy_activity_logs"].find(query, {"_id": 0}).sort("timestamp", -1).skip(offset).limit(limit).to_list(limit)
        total = await db["pharmacy_activity_logs"].count_documents(query)
        
        return {
            "logs": logs,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    
    return supply_chain_router


# Export for use in server.py
__all__ = ["supply_chain_router", "create_supply_chain_endpoints"]
