"""
Real-time WebSocket Notification System for Pharmacy Portal
Provides instant notifications when prescriptions are sent to pharmacies
"""

import uuid
import asyncio
from datetime import datetime, timezone
from typing import Dict, Set, Optional, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from enum import Enum

pharmacy_ws_router = APIRouter(prefix="/api/pharmacy-ws", tags=["Pharmacy WebSocket"])


# ============== Enums ==============

class PharmacyNotificationType(str, Enum):
    PRESCRIPTION_RECEIVED = "prescription_received"
    PRESCRIPTION_UPDATE = "prescription_update"
    SUPPLY_REQUEST_RECEIVED = "supply_request_received"
    SUPPLY_REQUEST_UPDATE = "supply_request_update"
    INVENTORY_ALERT = "inventory_alert"
    APPROVAL_STATUS = "approval_status"
    SYSTEM_MESSAGE = "system_message"


# ============== WebSocket Connection Manager ==============

class PharmacyNotificationManager:
    """
    Manages WebSocket connections for pharmacy real-time notifications.
    Enables instant alerts when prescriptions are sent from hospitals.
    """
    
    def __init__(self):
        # pharmacy_id -> Set of WebSocket connections
        self.connections: Dict[str, Set[WebSocket]] = {}
        # All connections for stats
        self._all_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket, pharmacy_id: str):
        """Connect a pharmacy client to receive real-time notifications"""
        await websocket.accept()
        
        if pharmacy_id not in self.connections:
            self.connections[pharmacy_id] = set()
        
        self.connections[pharmacy_id].add(websocket)
        self._all_connections.add(websocket)
        
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to pharmacy notification service",
            "pharmacy_id": pharmacy_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        print(f"[WS] Pharmacy {pharmacy_id} connected. Total: {len(self._all_connections)} connections")
    
    def disconnect(self, websocket: WebSocket, pharmacy_id: str):
        """Disconnect a pharmacy client"""
        if pharmacy_id in self.connections:
            self.connections[pharmacy_id].discard(websocket)
            if not self.connections[pharmacy_id]:
                del self.connections[pharmacy_id]
        
        self._all_connections.discard(websocket)
        print(f"[WS] Pharmacy {pharmacy_id} disconnected. Total: {len(self._all_connections)} connections")
    
    async def send_notification(self, pharmacy_id: str, notification: dict):
        """
        Send a notification to all connected clients for a specific pharmacy.
        Returns True if at least one client received the notification.
        """
        if pharmacy_id not in self.connections:
            print(f"[WS] No connections for pharmacy {pharmacy_id}")
            return False
        
        disconnected = set()
        sent = False
        
        for ws in self.connections[pharmacy_id]:
            try:
                await ws.send_json(notification)
                sent = True
            except Exception as e:
                print(f"[WS] Failed to send to {pharmacy_id}: {e}")
                disconnected.add(ws)
        
        # Clean up disconnected clients
        for ws in disconnected:
            self.connections[pharmacy_id].discard(ws)
            self._all_connections.discard(ws)
        
        if not self.connections[pharmacy_id]:
            del self.connections[pharmacy_id]
        
        return sent
    
    async def broadcast_to_all(self, notification: dict):
        """Broadcast notification to all connected pharmacies"""
        for pharmacy_id in list(self.connections.keys()):
            await self.send_notification(pharmacy_id, notification)
    
    def is_pharmacy_connected(self, pharmacy_id: str) -> bool:
        """Check if a pharmacy has any active connections"""
        return pharmacy_id in self.connections and len(self.connections[pharmacy_id]) > 0
    
    def get_stats(self) -> dict:
        """Get connection statistics"""
        return {
            "total_connections": len(self._all_connections),
            "pharmacies_connected": len(self.connections),
            "pharmacy_ids": list(self.connections.keys())
        }


# Global singleton instance
pharmacy_notification_manager = PharmacyNotificationManager()


def create_pharmacy_ws_endpoints(db):
    """Create WebSocket endpoints for pharmacy notifications"""
    
    @pharmacy_ws_router.websocket("/connect/{pharmacy_id}")
    async def pharmacy_websocket_endpoint(websocket: WebSocket, pharmacy_id: str):
        """
        WebSocket endpoint for pharmacy real-time notifications.
        
        Connect using: ws://domain/api/pharmacy-ws/connect/{pharmacy_id}
        
        Messages received:
        - {"type": "connected", "pharmacy_id": "...", "timestamp": "..."}
        - {"type": "prescription_received", "data": {...}, "timestamp": "..."}
        - {"type": "pong"} - response to ping
        
        Messages to send:
        - {"type": "ping"} - keep-alive
        - {"type": "ack", "notification_id": "..."} - acknowledge notification
        """
        await pharmacy_notification_manager.connect(websocket, pharmacy_id)
        
        try:
            while True:
                # Wait for incoming messages (ping/pong or acknowledgments)
                data = await websocket.receive_json()
                
                if data.get("type") == "ping":
                    # Respond to keep-alive ping
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                
                elif data.get("type") == "ack":
                    # Client acknowledging receipt of notification
                    notification_id = data.get("notification_id")
                    if notification_id:
                        await db["pharmacy_notifications"].update_one(
                            {"id": notification_id, "pharmacy_id": pharmacy_id},
                            {"$set": {
                                "acknowledged": True,
                                "acknowledged_at": datetime.now(timezone.utc).isoformat()
                            }}
                        )
                
                elif data.get("type") == "mark_read":
                    # Mark notifications as read
                    notification_ids = data.get("notification_ids", [])
                    if notification_ids:
                        await db["pharmacy_notifications"].update_many(
                            {"id": {"$in": notification_ids}, "pharmacy_id": pharmacy_id},
                            {"$set": {
                                "read": True,
                                "read_at": datetime.now(timezone.utc).isoformat()
                            }}
                        )
                        await websocket.send_json({
                            "type": "read_confirmed",
                            "notification_ids": notification_ids
                        })
                        
        except WebSocketDisconnect:
            pharmacy_notification_manager.disconnect(websocket, pharmacy_id)
        except Exception as e:
            print(f"[WS] Error for pharmacy {pharmacy_id}: {e}")
            pharmacy_notification_manager.disconnect(websocket, pharmacy_id)
    
    @pharmacy_ws_router.get("/stats")
    async def get_websocket_stats():
        """Get WebSocket connection statistics"""
        return pharmacy_notification_manager.get_stats()
    
    @pharmacy_ws_router.get("/pharmacy/{pharmacy_id}/connected")
    async def check_pharmacy_connected(pharmacy_id: str):
        """Check if a pharmacy is currently connected"""
        return {
            "pharmacy_id": pharmacy_id,
            "connected": pharmacy_notification_manager.is_pharmacy_connected(pharmacy_id)
        }
    
    return pharmacy_ws_router


# ============== Notification Sending Functions ==============

async def notify_prescription_received(
    db,
    pharmacy_id: str,
    prescription_data: dict,
    priority: str = "high"
):
    """
    Send real-time notification when a prescription is sent to a pharmacy.
    
    Call this function from the prescription module when routing a prescription.
    
    Args:
        db: Database connection
        pharmacy_id: Target pharmacy ID
        prescription_data: Dict with prescription details (rx_number, patient_name, etc.)
        priority: Notification priority (low, medium, high, urgent)
    
    Returns:
        notification_id: ID of the stored notification
    """
    notification_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Build notification payload
    notification = {
        "id": notification_id,
        "type": PharmacyNotificationType.PRESCRIPTION_RECEIVED.value,
        "priority": priority,
        "title": "New Prescription",
        "message": f"From {prescription_data.get('hospital_name', 'Hospital')}: {prescription_data.get('patient_name', 'Patient')}",
        "data": {
            "prescription_id": prescription_data.get("prescription_id"),
            "routing_id": prescription_data.get("routing_id"),
            "rx_number": prescription_data.get("rx_number"),
            "patient_name": prescription_data.get("patient_name"),
            "hospital_name": prescription_data.get("hospital_name"),
            "prescriber_name": prescription_data.get("prescriber_name"),
            "medication_count": len(prescription_data.get("medications", [])),
            "medications_preview": [
                m.get("medication_name", m.get("name", "Unknown")) 
                for m in prescription_data.get("medications", [])[:3]
            ]
        },
        "pharmacy_id": pharmacy_id,
        "timestamp": now,
        "read": False,
        "acknowledged": False,
        "sound": True,  # Play notification sound
        "created_at": now
    }
    
    # Store notification in database for history
    await db["pharmacy_notifications"].insert_one({
        **notification,
        "_stored": True
    })
    
    # Send real-time WebSocket notification
    ws_message = {
        "type": "notification",
        "notification_type": PharmacyNotificationType.PRESCRIPTION_RECEIVED.value,
        "notification": notification,
        "timestamp": now
    }
    
    sent = await pharmacy_notification_manager.send_notification(pharmacy_id, ws_message)
    
    print(f"[NOTIFY] Prescription {prescription_data.get('rx_number')} -> Pharmacy {pharmacy_id} | WS Sent: {sent}")
    
    return notification_id


async def notify_supply_request(
    db,
    target_pharmacy_id: str,
    request_data: dict
):
    """Send notification for incoming supply request"""
    notification_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    notification = {
        "id": notification_id,
        "type": PharmacyNotificationType.SUPPLY_REQUEST_RECEIVED.value,
        "priority": "medium",
        "title": "Supply Request",
        "message": f"Request from {request_data.get('requesting_pharmacy_name', 'Pharmacy')}",
        "data": {
            "request_id": request_data.get("request_id"),
            "requesting_pharmacy_name": request_data.get("requesting_pharmacy_name"),
            "item_count": len(request_data.get("items", [])),
            "items_preview": [
                f"{i.get('drug_name')} x{i.get('quantity')}" 
                for i in request_data.get("items", [])[:3]
            ]
        },
        "pharmacy_id": target_pharmacy_id,
        "timestamp": now,
        "read": False,
        "sound": True,
        "created_at": now
    }
    
    await db["pharmacy_notifications"].insert_one(notification)
    
    await pharmacy_notification_manager.send_notification(target_pharmacy_id, {
        "type": "notification",
        "notification_type": PharmacyNotificationType.SUPPLY_REQUEST_RECEIVED.value,
        "notification": notification,
        "timestamp": now
    })
    
    return notification_id


async def notify_inventory_alert(
    db,
    pharmacy_id: str,
    alert_type: str,
    items: list
):
    """Send inventory alert notification (low stock, expiring, expired)"""
    notification_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    titles = {
        "low_stock": f"{len(items)} Low Stock Items",
        "expiring": f"{len(items)} Items Expiring Soon",
        "expired": f"{len(items)} Expired Items"
    }
    
    notification = {
        "id": notification_id,
        "type": PharmacyNotificationType.INVENTORY_ALERT.value,
        "priority": "urgent" if alert_type == "expired" else "high",
        "title": titles.get(alert_type, "Inventory Alert"),
        "message": f"Review your inventory for {alert_type.replace('_', ' ')} items",
        "data": {
            "alert_type": alert_type,
            "item_count": len(items),
            "items": items[:10]
        },
        "pharmacy_id": pharmacy_id,
        "timestamp": now,
        "read": False,
        "sound": alert_type == "expired",
        "created_at": now
    }
    
    await db["pharmacy_notifications"].insert_one(notification)
    
    await pharmacy_notification_manager.send_notification(pharmacy_id, {
        "type": "notification",
        "notification_type": PharmacyNotificationType.INVENTORY_ALERT.value,
        "notification": notification,
        "timestamp": now
    })
    
    return notification_id


async def notify_pharmacy_approved(
    db,
    pharmacy_id: str,
    pharmacy_name: str
):
    """Send notification when pharmacy registration is approved"""
    notification_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    notification = {
        "id": notification_id,
        "type": PharmacyNotificationType.APPROVAL_STATUS.value,
        "priority": "high",
        "title": "Registration Approved!",
        "message": f"Congratulations! {pharmacy_name} is now active in the Yacco Health network.",
        "data": {
            "pharmacy_id": pharmacy_id,
            "pharmacy_name": pharmacy_name,
            "status": "approved"
        },
        "pharmacy_id": pharmacy_id,
        "timestamp": now,
        "read": False,
        "sound": True,
        "created_at": now
    }
    
    await db["pharmacy_notifications"].insert_one(notification)
    
    await pharmacy_notification_manager.send_notification(pharmacy_id, {
        "type": "notification",
        "notification_type": PharmacyNotificationType.APPROVAL_STATUS.value,
        "notification": notification,
        "timestamp": now
    })
    
    return notification_id
