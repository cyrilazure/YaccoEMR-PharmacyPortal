"""
Hospital Dashboard Module
Provides location-specific dashboard data:
- Overview statistics
- Department/unit summaries
- User activity
- Notifications & alerts
- Role-based routing
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid

hospital_dashboard_router = APIRouter(prefix="/api/hospital", tags=["Hospital Dashboard"])

# Role portal mapping
ROLE_PORTALS = {
    "physician": "physician",
    "nurse": "nurse",
    "scheduler": "scheduler",
    "biller": "billing",
    "hospital_admin": "admin",
    "admin": "admin",
    "receptionist": "reception",
    "lab_tech": "lab",
    "pharmacist": "pharmacy",
    "department_head": "department"
}

# ============ API Factory ============

def create_hospital_dashboard_endpoints(db, get_current_user):
    """Create hospital dashboard API endpoints"""
    
    def verify_hospital_access(user: dict, hospital_id: str):
        """Verify user has access to this hospital"""
        if user.get("role") == "super_admin":
            return True
        if user.get("organization_id") != hospital_id:
            raise HTTPException(status_code=403, detail="Not authorized for this hospital")
        return True
    
    # ============ Main Dashboard ============
    
    @hospital_dashboard_router.get("/{hospital_id}/dashboard")
    async def get_hospital_dashboard(
        hospital_id: str,
        location_id: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """
        Get hospital main dashboard data.
        Scoped to location if provided.
        """
        verify_hospital_access(user, hospital_id)
        
        # Use user's location if not specified
        if not location_id:
            location_id = user.get("location_id")
        
        # Get hospital info
        hospital = await db["hospitals"].find_one(
            {"id": hospital_id},
            {"_id": 0, "admin_password": 0}
        )
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        
        # Get location info
        location = None
        if location_id:
            location = await db["hospital_locations"].find_one(
                {"id": location_id},
                {"_id": 0}
            )
        
        # Build stats query (scoped to location if applicable)
        base_query = {"organization_id": hospital_id}
        if location_id:
            base_query["location_id"] = location_id
        
        # ============ Statistics ============
        
        # User counts
        total_users = await db["users"].count_documents({
            **base_query, "is_active": True
        })
        
        # Role distribution
        role_counts = await db["users"].aggregate([
            {"$match": {**base_query, "is_active": True}},
            {"$group": {"_id": "$role", "count": {"$sum": 1}}}
        ]).to_list(20)
        
        # Today's appointments
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        todays_appointments = await db["appointments"].count_documents({
            "organization_id": hospital_id,
            "date": {"$gte": today_start.isoformat(), "$lt": today_end.isoformat()}
        })
        
        # Active patients (seen in last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        active_patients = await db["encounters"].aggregate([
            {"$match": {
                "organization_id": hospital_id,
                "created_at": {"$gte": thirty_days_ago.isoformat()}
            }},
            {"$group": {"_id": "$patient_id"}},
            {"$count": "total"}
        ]).to_list(1)
        
        # Pending orders
        pending_orders = await db["orders"].count_documents({
            "organization_id": hospital_id,
            "status": {"$in": ["pending", "in_progress"]}
        })
        
        # ============ Departments & Units ============
        
        dept_query = {"organization_id": hospital_id, "is_active": True}
        if location_id:
            dept_query["location_id"] = location_id
        
        departments = await db["departments"].find(
            dept_query,
            {"_id": 0}
        ).sort("name", 1).to_list(50)
        
        # Enrich departments with user counts
        for dept in departments:
            dept["user_count"] = await db["users"].count_documents({
                "organization_id": hospital_id,
                "department_id": dept["id"],
                "is_active": True
            })
        
        # ============ Recent Activity ============
        
        recent_activity = await db["audit_logs"].find({
            "organization_id": hospital_id
        }).sort("timestamp", -1).limit(10).to_list(10)
        
        # ============ Notifications ============
        
        notifications = await db["notifications"].find({
            "organization_id": hospital_id,
            "read": False,
            "$or": [
                {"user_id": user["id"]},
                {"role": user.get("role")},
                {"broadcast": True}
            ]
        }).sort("created_at", -1).limit(10).to_list(10)
        
        # ============ Quick Links (Role-Based) ============
        
        user_role = user.get("role", "physician")
        portal = ROLE_PORTALS.get(user_role, "dashboard")
        
        quick_links = [
            {
                "label": "My Portal",
                "url": f"/hospital/{hospital_id}/{portal}",
                "icon": "layout-dashboard"
            },
            {
                "label": "Patients",
                "url": f"/hospital/{hospital_id}/patients",
                "icon": "users"
            },
            {
                "label": "Appointments",
                "url": f"/hospital/{hospital_id}/appointments",
                "icon": "calendar"
            }
        ]
        
        if user_role in ["hospital_admin", "admin", "super_admin"]:
            quick_links.extend([
                {
                    "label": "Admin Dashboard",
                    "url": f"/hospital/{hospital_id}/admin",
                    "icon": "settings"
                },
                {
                    "label": "Staff Management",
                    "url": f"/hospital/{hospital_id}/admin/users",
                    "icon": "users-cog"
                }
            ])
        
        return {
            "hospital": {
                "id": hospital["id"],
                "name": hospital["name"],
                "region_id": hospital.get("region_id"),
                "city": hospital.get("city"),
                "status": hospital.get("status")
            },
            "location": location,
            "user": {
                "id": user["id"],
                "name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
                "role": user.get("role"),
                "portal": portal
            },
            "stats": {
                "total_users": total_users,
                "todays_appointments": todays_appointments,
                "active_patients": active_patients[0]["total"] if active_patients else 0,
                "pending_orders": pending_orders
            },
            "role_distribution": {r["_id"]: r["count"] for r in role_counts},
            "departments": departments,
            "recent_activity": recent_activity,
            "notifications": notifications,
            "quick_links": quick_links,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    # ============ Role-Specific Portals ============
    
    @hospital_dashboard_router.get("/{hospital_id}/physician")
    async def get_physician_portal(
        hospital_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Physician portal dashboard"""
        verify_hospital_access(user, hospital_id)
        
        # Get physician's data
        physician_id = user["id"]
        
        # Today's schedule
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        todays_appointments = await db["appointments"].find({
            "provider_id": physician_id,
            "date": {"$gte": today_start.isoformat(), "$lt": today_end.isoformat()}
        }).sort("time", 1).to_list(50)
        
        # Pending tasks
        pending_orders = await db["orders"].count_documents({
            "provider_id": physician_id,
            "status": "pending"
        })
        
        pending_notes = await db["encounters"].count_documents({
            "provider_id": physician_id,
            "status": "in_progress"
        })
        
        # Recent patients
        recent_patients = await db["encounters"].aggregate([
            {"$match": {"provider_id": physician_id}},
            {"$sort": {"created_at": -1}},
            {"$limit": 10},
            {"$lookup": {
                "from": "patients",
                "localField": "patient_id",
                "foreignField": "id",
                "as": "patient"
            }},
            {"$unwind": "$patient"}
        ]).to_list(10)
        
        return {
            "portal": "physician",
            "user": {
                "id": user["id"],
                "name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
                "specialty": user.get("specialty")
            },
            "todays_appointments": todays_appointments,
            "stats": {
                "todays_patients": len(todays_appointments),
                "pending_orders": pending_orders,
                "pending_notes": pending_notes
            },
            "recent_patients": recent_patients
        }
    
    @hospital_dashboard_router.get("/{hospital_id}/nurse")
    async def get_nurse_portal(
        hospital_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Nurse portal dashboard"""
        verify_hospital_access(user, hospital_id)
        
        location_id = user.get("location_id")
        
        # Patients in unit/location
        patients_query = {"organization_id": hospital_id}
        if location_id:
            patients_query["location_id"] = location_id
        
        # Pending vitals
        pending_vitals = await db["tasks"].count_documents({
            **patients_query,
            "type": "vitals",
            "status": "pending"
        })
        
        # Medication administration
        pending_meds = await db["medication_tasks"].count_documents({
            **patients_query,
            "status": "pending",
            "scheduled_time": {"$lte": datetime.now(timezone.utc).isoformat()}
        })
        
        # Patient list
        patients = await db["patients"].find({
            **patients_query,
            "status": "admitted"
        }).limit(20).to_list(20)
        
        return {
            "portal": "nurse",
            "user": {
                "id": user["id"],
                "name": f"{user.get('first_name', '')} {user.get('last_name', '')}"
            },
            "stats": {
                "pending_vitals": pending_vitals,
                "pending_medications": pending_meds,
                "patients_in_unit": len(patients)
            },
            "patients": patients
        }
    
    @hospital_dashboard_router.get("/{hospital_id}/scheduler")
    async def get_scheduler_portal(
        hospital_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Scheduler portal dashboard"""
        verify_hospital_access(user, hospital_id)
        
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = today + timedelta(days=7)
        
        # This week's appointments
        appointments = await db["appointments"].find({
            "organization_id": hospital_id,
            "date": {"$gte": today.isoformat(), "$lt": week_end.isoformat()}
        }).to_list(200)
        
        # Appointment counts by day
        by_day = {}
        for apt in appointments:
            day = apt.get("date", "")[:10]
            by_day[day] = by_day.get(day, 0) + 1
        
        # Available providers
        providers = await db["users"].find({
            "organization_id": hospital_id,
            "role": "physician",
            "is_active": True
        }, {"_id": 0, "password": 0}).to_list(100)
        
        return {
            "portal": "scheduler",
            "user": {
                "id": user["id"],
                "name": f"{user.get('first_name', '')} {user.get('last_name', '')}"
            },
            "stats": {
                "this_week_appointments": len(appointments),
                "available_providers": len(providers)
            },
            "appointments_by_day": by_day,
            "providers": providers
        }
    
    @hospital_dashboard_router.get("/{hospital_id}/billing")
    async def get_billing_portal(
        hospital_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Billing portal dashboard"""
        verify_hospital_access(user, hospital_id)
        
        # Pending invoices
        pending_invoices = await db["invoices"].count_documents({
            "organization_id": hospital_id,
            "status": "pending"
        })
        
        # Overdue invoices
        overdue_invoices = await db["invoices"].count_documents({
            "organization_id": hospital_id,
            "status": "overdue"
        })
        
        # This month's revenue
        month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        revenue = await db["payments"].aggregate([
            {"$match": {
                "organization_id": hospital_id,
                "created_at": {"$gte": month_start.isoformat()}
            }},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
        ]).to_list(1)
        
        return {
            "portal": "billing",
            "user": {
                "id": user["id"],
                "name": f"{user.get('first_name', '')} {user.get('last_name', '')}"
            },
            "stats": {
                "pending_invoices": pending_invoices,
                "overdue_invoices": overdue_invoices,
                "monthly_revenue": revenue[0]["total"] if revenue else 0
            }
        }
    
    # ============ Location Management ============
    
    @hospital_dashboard_router.get("/{hospital_id}/locations")
    async def list_hospital_locations(
        hospital_id: str,
        user: dict = Depends(get_current_user)
    ):
        """List all locations for a hospital"""
        verify_hospital_access(user, hospital_id)
        
        locations = await db["hospital_locations"].find(
            {"hospital_id": hospital_id, "is_active": True},
            {"_id": 0}
        ).sort("name", 1).to_list(50)
        
        # Enrich with user counts
        for loc in locations:
            loc["user_count"] = await db["users"].count_documents({
                "organization_id": hospital_id,
                "location_id": loc["id"],
                "is_active": True
            })
        
        return {"locations": locations, "total": len(locations)}
    
    # ============ Department Portal ============
    
    @hospital_dashboard_router.get("/{hospital_id}/department/{dept_id}")
    async def get_department_portal(
        hospital_id: str,
        dept_id: str,
        user: dict = Depends(get_current_user)
    ):
        """Department-specific portal"""
        verify_hospital_access(user, hospital_id)
        
        department = await db["departments"].find_one(
            {"id": dept_id, "organization_id": hospital_id},
            {"_id": 0}
        )
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
        
        # Get department users
        users = await db["users"].find({
            "organization_id": hospital_id,
            "department_id": dept_id,
            "is_active": True
        }, {"_id": 0, "password": 0}).to_list(100)
        
        # Get units
        units = await db["units"].find({
            "organization_id": hospital_id,
            "department_id": dept_id,
            "is_active": True
        }, {"_id": 0}).to_list(50)
        
        return {
            "department": department,
            "users": users,
            "units": units,
            "stats": {
                "total_users": len(users),
                "total_units": len(units)
            }
        }
    
    return hospital_dashboard_router


# Export
__all__ = ["hospital_dashboard_router", "create_hospital_dashboard_endpoints", "ROLE_PORTALS"]
