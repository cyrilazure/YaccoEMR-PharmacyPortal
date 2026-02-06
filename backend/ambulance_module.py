"""
Ambulance Portal & Emergency Transport Module for Yacco EMR
Manage ambulance fleet, dispatch requests, and patient referrals
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from enum import Enum

ambulance_router = APIRouter(prefix="/api/ambulance", tags=["Ambulance"])


# ============== ENUMS ==============

class VehicleType(str, Enum):
    BASIC_AMBULANCE = "basic_ambulance"
    ADVANCED_AMBULANCE = "advanced_ambulance"
    PATIENT_TRANSPORT = "patient_transport"
    EMERGENCY_RESPONSE = "emergency_response"
    ICU_AMBULANCE = "icu_ambulance"
    NEONATAL_AMBULANCE = "neonatal_ambulance"


class EquipmentLevel(str, Enum):
    BASIC = "basic"  # Basic life support
    INTERMEDIATE = "intermediate"  # Intermediate life support
    ADVANCED = "advanced"  # Advanced life support
    CRITICAL = "critical"  # ICU level equipment


class RequestStatus(str, Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    DISPATCHED = "dispatched"
    EN_ROUTE = "en_route"
    ARRIVED = "arrived"
    TRANSPORTING = "transporting"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TripType(str, Enum):
    EMERGENCY = "emergency"
    SCHEDULED = "scheduled"
    INTER_FACILITY = "inter_facility"
    DISCHARGE = "discharge"


class VehicleStatus(str, Enum):
    AVAILABLE = "available"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    OUT_OF_SERVICE = "out_of_service"


# ============== PYDANTIC MODELS ==============

class AmbulanceVehicleCreate(BaseModel):
    vehicle_number: str  # Plate number
    vehicle_type: VehicleType
    equipment_level: EquipmentLevel
    make_model: Optional[str] = None
    year: Optional[int] = None
    capacity: int = 1  # Number of patients
    has_oxygen: bool = True
    has_defibrillator: bool = False
    has_ventilator: bool = False
    has_stretcher: bool = True
    notes: Optional[str] = None


class AmbulanceRequestCreate(BaseModel):
    patient_id: str
    patient_name: str
    patient_mrn: str
    pickup_location: str
    destination_facility: str
    destination_address: Optional[str] = None
    referral_reason: str
    diagnosis_summary: Optional[str] = None
    trip_type: TripType = TripType.EMERGENCY
    priority_level: str = "routine"  # routine, urgent, emergency
    special_requirements: Optional[str] = None
    physician_notes: Optional[str] = None
    requesting_physician_id: Optional[str] = None


class AmbulanceDispatch(BaseModel):
    request_id: str
    vehicle_id: str
    driver_id: Optional[str] = None
    paramedic_id: Optional[str] = None
    estimated_arrival: Optional[str] = None
    notes: Optional[str] = None


class TripUpdate(BaseModel):
    status: RequestStatus
    notes: Optional[str] = None
    actual_pickup_time: Optional[str] = None
    actual_arrival_time: Optional[str] = None
    mileage: Optional[float] = None


# ============== HELPER FUNCTIONS ==============

def create_ambulance_endpoints(db, get_current_user):
    """Create ambulance management API endpoints"""
    
    # ============== FLEET MANAGEMENT ==============
    
    @ambulance_router.get("/vehicles")
    async def get_vehicles(
        status: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """Get ambulance fleet"""
        query = {"organization_id": user.get("organization_id"), "is_active": True}
        if status:
            query["status"] = status
        
        vehicles = await db.ambulance_vehicles.find(query, {"_id": 0}).sort("vehicle_number", 1).to_list(100)
        return {"vehicles": vehicles, "total": len(vehicles)}
    
    @ambulance_router.post("/vehicles")
    async def create_vehicle(
        data: AmbulanceVehicleCreate,
        user: dict = Depends(get_current_user)
    ):
        """Register new ambulance vehicle"""
        allowed_roles = ["hospital_admin", "hospital_it_admin", "facility_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        vehicle_id = str(uuid.uuid4())
        vehicle_doc = {
            "id": vehicle_id,
            "vehicle_number": data.vehicle_number,
            "vehicle_type": data.vehicle_type,
            "equipment_level": data.equipment_level,
            "make_model": data.make_model,
            "year": data.year,
            "capacity": data.capacity,
            "has_oxygen": data.has_oxygen,
            "has_defibrillator": data.has_defibrillator,
            "has_ventilator": data.has_ventilator,
            "has_stretcher": data.has_stretcher,
            "status": VehicleStatus.AVAILABLE,
            "current_trip_id": None,
            "total_trips": 0,
            "total_mileage": 0,
            "notes": data.notes,
            "organization_id": user.get("organization_id"),
            "is_active": True,
            "created_by": user.get("id"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.ambulance_vehicles.insert_one(vehicle_doc)
        vehicle_doc.pop("_id", None)
        
        return {"message": "Ambulance vehicle registered", "vehicle": vehicle_doc}
    
    @ambulance_router.put("/vehicles/{vehicle_id}/status")
    async def update_vehicle_status(
        vehicle_id: str,
        status: VehicleStatus,
        notes: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """Update vehicle status"""
        await db.ambulance_vehicles.update_one(
            {"id": vehicle_id},
            {"$set": {
                "status": status,
                "status_notes": notes,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        return {"message": "Vehicle status updated"}
    
    # ============== REQUEST MANAGEMENT ==============
    
    @ambulance_router.get("/requests")
    async def get_requests(
        status: Optional[str] = None,
        trip_type: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """Get ambulance requests"""
        query = {"organization_id": user.get("organization_id")}
        
        if status:
            query["status"] = status
        else:
            # Default: active requests
            query["status"] = {"$in": [
                RequestStatus.REQUESTED,
                RequestStatus.APPROVED,
                RequestStatus.DISPATCHED,
                RequestStatus.EN_ROUTE,
                RequestStatus.TRANSPORTING
            ]}
        
        if trip_type:
            query["trip_type"] = trip_type
        
        requests = await db.ambulance_requests.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
        return {"requests": requests, "total": len(requests)}
    
    @ambulance_router.post("/requests")
    async def create_request(
        data: AmbulanceRequestCreate,
        user: dict = Depends(get_current_user)
    ):
        """Create ambulance/transfer request"""
        allowed_roles = ["physician", "nurse", "nursing_supervisor", "facility_admin", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        request_id = str(uuid.uuid4())
        request_number = f"AMB-{datetime.now().strftime('%Y%m%d')}-{request_id[:8].upper()}"
        
        request_doc = {
            "id": request_id,
            "request_number": request_number,
            "patient_id": data.patient_id,
            "patient_name": data.patient_name,
            "patient_mrn": data.patient_mrn,
            "pickup_location": data.pickup_location,
            "destination_facility": data.destination_facility,
            "destination_address": data.destination_address,
            "referral_reason": data.referral_reason,
            "diagnosis_summary": data.diagnosis_summary,
            "trip_type": data.trip_type,
            "priority_level": data.priority_level,
            "special_requirements": data.special_requirements,
            "physician_notes": data.physician_notes,
            "requesting_physician_id": data.requesting_physician_id or user.get("id"),
            "requesting_physician": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "status": RequestStatus.REQUESTED,
            "vehicle_id": None,
            "driver_id": None,
            "paramedic_id": None,
            "requested_at": datetime.now(timezone.utc).isoformat(),
            "approved_at": None,
            "dispatched_at": None,
            "completed_at": None,
            "organization_id": user.get("organization_id"),
            "created_by": user.get("id"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.ambulance_requests.insert_one(request_doc)
        request_doc.pop("_id", None)
        
        # Audit log
        await db.audit_logs.insert_one({
            "id": str(uuid.uuid4()),
            "action": "ambulance_requested",
            "resource_type": "ambulance_request",
            "resource_id": request_id,
            "user_id": user.get("id"),
            "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "organization_id": user.get("organization_id"),
            "details": {
                "request_number": request_number,
                "patient_name": data.patient_name,
                "trip_type": data.trip_type,
                "priority": data.priority_level
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {"message": "Ambulance request created", "request": request_doc}
    
    @ambulance_router.put("/requests/{request_id}/approve")
    async def approve_request(
        request_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Approve ambulance request"""
        allowed_roles = ["facility_admin", "hospital_admin", "super_admin"]
        if user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Admin approval required")
        
        await db.ambulance_requests.update_one(
            {"id": request_id},
            {"$set": {
                "status": RequestStatus.APPROVED,
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "approved_by": user.get("id")
            }}
        )
        
        return {"message": "Request approved"}
    
    @ambulance_router.post("/requests/{request_id}/dispatch")
    async def dispatch_ambulance(
        request_id: str,
        data: AmbulanceDispatch,
        user: dict = Depends(get_current_user)
    ):
        """Dispatch ambulance to request"""
        request = await db.ambulance_requests.find_one({"id": request_id})
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        # Update request
        await db.ambulance_requests.update_one(
            {"id": request_id},
            {"$set": {
                "status": RequestStatus.DISPATCHED,
                "vehicle_id": data.vehicle_id,
                "driver_id": data.driver_id,
                "paramedic_id": data.paramedic_id,
                "estimated_arrival": data.estimated_arrival,
                "dispatched_at": datetime.now(timezone.utc).isoformat(),
                "dispatch_notes": data.notes
            }}
        )
        
        # Update vehicle status
        await db.ambulance_vehicles.update_one(
            {"id": data.vehicle_id},
            {"$set": {
                "status": VehicleStatus.IN_USE,
                "current_trip_id": request_id
            }}
        )
        
        return {"message": "Ambulance dispatched"}
    
    @ambulance_router.put("/requests/{request_id}/update-status")
    async def update_trip_status(
        request_id: str,
        data: TripUpdate,
        user: dict = Depends(get_current_user)
    ):
        """Update trip status (en route, arrived, completed)"""
        update_data = {
            "status": data.status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if data.notes:
            update_data["status_notes"] = data.notes
        if data.actual_pickup_time:
            update_data["actual_pickup_time"] = data.actual_pickup_time
        if data.actual_arrival_time:
            update_data["actual_arrival_time"] = data.actual_arrival_time
        if data.mileage:
            update_data["mileage"] = data.mileage
        
        # If completed, free up vehicle
        if data.status == RequestStatus.COMPLETED:
            update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            # Get request to find vehicle
            request = await db.ambulance_requests.find_one({"id": request_id})
            if request and request.get("vehicle_id"):
                await db.ambulance_vehicles.update_one(
                    {"id": request["vehicle_id"]},
                    {
                        "$set": {"status": VehicleStatus.AVAILABLE, "current_trip_id": None},
                        "$inc": {"total_trips": 1, "total_mileage": data.mileage or 0}
                    }
                )
        
        await db.ambulance_requests.update_one({"id": request_id}, {"$set": update_data})
        
        return {"message": f"Status updated to {data.status}"}
    
    # ============== STAFF MANAGEMENT ==============
    
    @ambulance_router.post("/staff/clock-in")
    async def clock_in(
        vehicle_id: str,
        shift_type: str,
        user: dict = Depends(get_current_user)
    ):
        """Clock in for ambulance shift"""
        shift_id = str(uuid.uuid4())
        shift_doc = {
            "id": shift_id,
            "staff_id": user.get("id"),
            "staff_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
            "vehicle_id": vehicle_id,
            "shift_type": shift_type,
            "clock_in": datetime.now(timezone.utc).isoformat(),
            "clock_out": None,
            "trips_completed": 0,
            "organization_id": user.get("organization_id"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.ambulance_shifts.insert_one(shift_doc)
        shift_doc.pop("_id", None)
        
        return {"message": "Clocked in", "shift": shift_doc}
    
    @ambulance_router.post("/staff/clock-out")
    async def clock_out(shift_id: str, user: dict = Depends(get_current_user)):
        """Clock out from shift"""
        await db.ambulance_shifts.update_one(
            {"id": shift_id, "staff_id": user.get("id")},
            {"$set": {"clock_out": datetime.now(timezone.utc).isoformat()}}
        )
        return {"message": "Clocked out"}
    
    @ambulance_router.get("/staff/active-shifts")
    async def get_active_shifts(user: dict = Depends(get_current_user)):
        """Get active ambulance shifts"""
        shifts = await db.ambulance_shifts.find(
            {"organization_id": user.get("organization_id"), "clock_out": None},
            {"_id": 0}
        ).to_list(50)
        return {"shifts": shifts, "total": len(shifts)}
    
    # ============== DASHBOARD & REPORTS ==============
    
    @ambulance_router.get("/dashboard")
    async def get_dashboard(user: dict = Depends(get_current_user)):
        """Get ambulance operations dashboard"""
        org_id = user.get("organization_id")
        
        # Vehicle stats
        total_vehicles = await db.ambulance_vehicles.count_documents({"organization_id": org_id, "is_active": True})
        available_vehicles = await db.ambulance_vehicles.count_documents(
            {"organization_id": org_id, "status": VehicleStatus.AVAILABLE}
        )
        in_use_vehicles = await db.ambulance_vehicles.count_documents(
            {"organization_id": org_id, "status": VehicleStatus.IN_USE}
        )
        
        # Request stats
        all_requests = await db.ambulance_requests.find({"organization_id": org_id}, {"_id": 0}).to_list(1000)
        
        active_requests = len([r for r in all_requests if r["status"] in [
            RequestStatus.REQUESTED, RequestStatus.APPROVED, RequestStatus.DISPATCHED,
            RequestStatus.EN_ROUTE, RequestStatus.TRANSPORTING
        ]])
        
        completed_today = len([r for r in all_requests 
            if r.get("completed_at", "").startswith(datetime.now().strftime("%Y-%m-%d"))])
        
        emergency_trips = len([r for r in all_requests if r["trip_type"] == TripType.EMERGENCY])
        scheduled_trips = len([r for r in all_requests if r["trip_type"] == TripType.SCHEDULED])
        
        # Active shifts
        active_shifts = await db.ambulance_shifts.count_documents(
            {"organization_id": org_id, "clock_out": None}
        )
        
        return {
            "fleet": {
                "total": total_vehicles,
                "available": available_vehicles,
                "in_use": in_use_vehicles,
                "maintenance": total_vehicles - available_vehicles - in_use_vehicles
            },
            "requests": {
                "active": active_requests,
                "completed_today": completed_today,
                "total_emergency": emergency_trips,
                "total_scheduled": scheduled_trips
            },
            "staff": {
                "active_shifts": active_shifts
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    return ambulance_router


__all__ = ["ambulance_router", "create_ambulance_endpoints"]
