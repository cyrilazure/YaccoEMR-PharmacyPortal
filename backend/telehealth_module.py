"""
Telehealth Video Module for Yacco EMR
Supports:
- WebRTC peer-to-peer video calls (no external API needed)
- Dyte integration ready (when API key provided)
- Video session management
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid
import json
import os
import asyncio

telehealth_router = APIRouter(prefix="/api/telehealth", tags=["Telehealth Video"])

# ============ Configuration ============

# Check for Dyte API key (optional)
DYTE_API_KEY = os.environ.get('DYTE_API_KEY')
DYTE_ORG_ID = os.environ.get('DYTE_ORG_ID')
DYTE_ENABLED = bool(DYTE_API_KEY and DYTE_ORG_ID)

# ============ Enums ============

class SessionStatus(str, Enum):
    SCHEDULED = "scheduled"
    WAITING = "waiting"  # Provider/patient waiting
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class ParticipantRole(str, Enum):
    PROVIDER = "provider"
    PATIENT = "patient"
    INTERPRETER = "interpreter"
    CAREGIVER = "caregiver"

class SessionType(str, Enum):
    VIDEO = "video"
    AUDIO = "audio"
    CHAT = "chat"

# ============ Models ============

class TelehealthSessionCreate(BaseModel):
    patient_id: str
    patient_name: str
    provider_id: str
    provider_name: str
    appointment_id: Optional[str] = None
    scheduled_time: str  # ISO datetime string
    session_type: SessionType = SessionType.VIDEO
    reason: Optional[str] = None
    notes: Optional[str] = None
    duration_minutes: int = 30

class TelehealthSession(TelehealthSessionCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    room_id: str = Field(default_factory=lambda: f"room_{uuid.uuid4().hex[:12]}")
    status: SessionStatus = SessionStatus.SCHEDULED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    actual_duration_minutes: Optional[int] = None
    recording_enabled: bool = False
    waiting_room_enabled: bool = True
    # Dyte-specific (if enabled)
    dyte_meeting_id: Optional[str] = None

class Participant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: str
    user_name: str
    role: ParticipantRole
    joined_at: Optional[datetime] = None
    left_at: Optional[datetime] = None
    is_connected: bool = False
    # WebRTC connection info
    ice_candidates: List[Dict] = []
    sdp_offer: Optional[str] = None
    sdp_answer: Optional[str] = None

class JoinSessionRequest(BaseModel):
    user_id: str
    user_name: str
    role: ParticipantRole

class WebRTCSignal(BaseModel):
    type: str  # "offer", "answer", "ice-candidate"
    data: Dict[str, Any]
    from_user: str
    to_user: Optional[str] = None

# ============ WebRTC Connection Manager ============

class ConnectionManager:
    """Manages WebSocket connections for WebRTC signaling"""
    
    def __init__(self):
        # room_id -> {user_id -> websocket}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # user_id -> room_id
        self.user_rooms: Dict[str, str] = {}
    
    async def connect(self, websocket: WebSocket, room_id: str, user_id: str):
        await websocket.accept()
        
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
        
        self.active_connections[room_id][user_id] = websocket
        self.user_rooms[user_id] = room_id
        
        # Notify others in the room
        await self.broadcast_to_room(room_id, {
            "type": "user-joined",
            "user_id": user_id,
            "room_id": room_id,
            "participant_count": len(self.active_connections[room_id])
        }, exclude=user_id)
    
    def disconnect(self, room_id: str, user_id: str):
        if room_id in self.active_connections:
            if user_id in self.active_connections[room_id]:
                del self.active_connections[room_id][user_id]
            
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
        
        if user_id in self.user_rooms:
            del self.user_rooms[user_id]
    
    async def broadcast_to_room(self, room_id: str, message: dict, exclude: str = None):
        if room_id not in self.active_connections:
            return
        
        for user_id, connection in self.active_connections[room_id].items():
            if user_id != exclude:
                try:
                    await connection.send_json(message)
                except:
                    pass
    
    async def send_to_user(self, room_id: str, user_id: str, message: dict):
        if room_id in self.active_connections:
            if user_id in self.active_connections[room_id]:
                try:
                    await self.active_connections[room_id][user_id].send_json(message)
                except:
                    pass
    
    def get_room_participants(self, room_id: str) -> List[str]:
        if room_id in self.active_connections:
            return list(self.active_connections[room_id].keys())
        return []

# Global connection manager
manager = ConnectionManager()

# ============ API Factory ============

def create_telehealth_endpoints(db, get_current_user):
    """Create telehealth API endpoints with database dependency"""
    
    @telehealth_router.get("/config", response_model=dict)
    async def get_telehealth_config(user: dict = Depends(get_current_user)):
        """Get telehealth configuration and feature availability"""
        return {
            "webrtc_enabled": True,
            "dyte_enabled": DYTE_ENABLED,
            "features": {
                "video_call": True,
                "audio_only": True,
                "screen_share": True,
                "chat": True,
                "recording": DYTE_ENABLED,  # Recording requires Dyte
                "waiting_room": True
            },
            "ice_servers": [
                {"urls": "stun:stun.l.google.com:19302"},
                {"urls": "stun:stun1.l.google.com:19302"},
                {"urls": "stun:stun2.l.google.com:19302"}
            ]
        }
    
    @telehealth_router.post("/sessions", response_model=dict)
    async def create_telehealth_session(session: TelehealthSessionCreate, user: dict = Depends(get_current_user)):
        """Create a new telehealth video session"""
        telehealth_session = TelehealthSession(**session.model_dump())
        
        session_dict = telehealth_session.model_dump()
        session_dict['created_at'] = session_dict['created_at'].isoformat()
        
        await db["telehealth_sessions"].insert_one(session_dict)
        
        return {
            "message": "Telehealth session created",
            "session": session_dict,
            "join_url": f"/telehealth/{telehealth_session.id}"
        }
    
    @telehealth_router.get("/sessions", response_model=dict)
    async def get_telehealth_sessions(
        provider_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        status: Optional[str] = None,
        date: Optional[str] = None,
        user: dict = Depends(get_current_user)
    ):
        """Get telehealth sessions with optional filters"""
        query = {}
        
        if provider_id:
            query["provider_id"] = provider_id
        if patient_id:
            query["patient_id"] = patient_id
        if status:
            query["status"] = status
        if date:
            # Filter by date
            query["scheduled_time"] = {"$regex": f"^{date}"}
        
        sessions = await db["telehealth_sessions"].find(query, {"_id": 0}).sort("scheduled_time", -1).to_list(100)
        return {"sessions": sessions}
    
    @telehealth_router.get("/sessions/{session_id}", response_model=dict)
    async def get_telehealth_session(session_id: str, user: dict = Depends(get_current_user)):
        """Get a specific telehealth session"""
        session = await db["telehealth_sessions"].find_one({"id": session_id})
        
        if not session:
            raise HTTPException(status_code=404, detail="Telehealth session not found")
        
        # Get participants
        participants = await db["telehealth_participants"].find({"session_id": session_id}, {"_id": 0}).to_list(10)
        
        return {
            "session": session,
            "participants": participants,
            "room_id": session.get("room_id")
        }
    
    @telehealth_router.post("/sessions/{session_id}/join", response_model=dict)
    async def join_telehealth_session(session_id: str, request: JoinSessionRequest, user: dict = Depends(get_current_user)):
        """Join a telehealth session"""
        session = await db["telehealth_sessions"].find_one({"id": session_id})
        
        if not session:
            raise HTTPException(status_code=404, detail="Telehealth session not found")
        
        if session.get("status") in [SessionStatus.COMPLETED.value, SessionStatus.CANCELLED.value]:
            raise HTTPException(status_code=400, detail="Session is no longer active")
        
        # Create participant record
        participant = Participant(
            session_id=session_id,
            user_id=request.user_id,
            user_name=request.user_name,
            role=request.role,
            joined_at=datetime.now(timezone.utc)
        )
        
        participant_dict = participant.model_dump()
        participant_dict['joined_at'] = participant_dict['joined_at'].isoformat() if participant_dict['joined_at'] else None
        
        # Upsert participant
        await db["telehealth_participants"].update_one(
            {"session_id": session_id, "user_id": request.user_id},
            {"$set": participant_dict},
            upsert=True
        )
        
        # Update session status if needed
        if session.get("status") == SessionStatus.SCHEDULED.value:
            await db["telehealth_sessions"].update_one(
                {"id": session_id},
                {"$set": {"status": SessionStatus.WAITING.value}}
            )
        
        return {
            "message": "Joined session successfully",
            "room_id": session.get("room_id"),
            "participant_id": participant.id,
            "ice_servers": [
                {"urls": "stun:stun.l.google.com:19302"},
                {"urls": "stun:stun1.l.google.com:19302"}
            ]
        }
    
    @telehealth_router.post("/sessions/{session_id}/start", response_model=dict)
    async def start_telehealth_session(session_id: str, user: dict = Depends(get_current_user)):
        """Start the telehealth session (call begins)"""
        result = await db["telehealth_sessions"].update_one(
            {"id": session_id},
            {"$set": {
                "status": SessionStatus.IN_PROGRESS.value,
                "started_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session started", "status": SessionStatus.IN_PROGRESS.value}
    
    @telehealth_router.post("/sessions/{session_id}/end", response_model=dict)
    async def end_telehealth_session(session_id: str, notes: Optional[str] = None, user: dict = Depends(get_current_user)):
        """End the telehealth session"""
        session = await db["telehealth_sessions"].find_one({"id": session_id})
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Calculate duration
        started_at = session.get("started_at")
        actual_duration = None
        if started_at:
            start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00')) if isinstance(started_at, str) else started_at
            actual_duration = int((datetime.now(timezone.utc) - start_time).total_seconds() / 60)
        
        update_data = {
            "status": SessionStatus.COMPLETED.value,
            "ended_at": datetime.now(timezone.utc).isoformat(),
            "actual_duration_minutes": actual_duration
        }
        
        if notes:
            update_data["notes"] = notes
        
        await db["telehealth_sessions"].update_one(
            {"id": session_id},
            {"$set": update_data}
        )
        
        # Update all participants as disconnected
        await db["telehealth_participants"].update_many(
            {"session_id": session_id},
            {"$set": {
                "is_connected": False,
                "left_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {
            "message": "Session ended",
            "duration_minutes": actual_duration
        }
    
    @telehealth_router.put("/sessions/{session_id}/status", response_model=dict)
    async def update_session_status(session_id: str, status: SessionStatus, user: dict = Depends(get_current_user)):
        """Update telehealth session status"""
        result = await db["telehealth_sessions"].update_one(
            {"id": session_id},
            {"$set": {"status": status.value}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": f"Status updated to {status.value}"}
    
    @telehealth_router.get("/sessions/{session_id}/participants", response_model=dict)
    async def get_session_participants(session_id: str, user: dict = Depends(get_current_user)):
        """Get participants in a telehealth session"""
        participants = await db["telehealth_participants"].find({"session_id": session_id}).to_list(10)
        return {"participants": participants}
    
    @telehealth_router.post("/sessions/from-appointment/{appointment_id}", response_model=dict)
    async def create_session_from_appointment(appointment_id: str, user: dict = Depends(get_current_user)):
        """Create telehealth session from an existing appointment"""
        # Get appointment
        appointment = await db["appointments"].find_one({"id": appointment_id})
        
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        # Check if session already exists
        existing = await db["telehealth_sessions"].find_one({"appointment_id": appointment_id})
        if existing:
            return {
                "message": "Session already exists",
                "session": existing,
                "existing": True
            }
        
        # Get patient info
        patient = await db["patients"].find_one({"id": appointment.get("patient_id")})
        patient_name = f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip() if patient else "Unknown Patient"
        
        # Create session
        session = TelehealthSession(
            patient_id=appointment.get("patient_id"),
            patient_name=patient_name,
            provider_id=appointment.get("provider_id", user.get("id")),
            provider_name=appointment.get("provider_name", f"{user.get('first_name', '')} {user.get('last_name', '')}"),
            appointment_id=appointment_id,
            scheduled_time=appointment.get("appointment_time"),
            reason=appointment.get("reason"),
            duration_minutes=appointment.get("duration_minutes", 30)
        )
        
        session_dict = session.model_dump()
        session_dict['created_at'] = session_dict['created_at'].isoformat()
        
        await db["telehealth_sessions"].insert_one(session_dict)
        
        # Update appointment type
        await db["appointments"].update_one(
            {"id": appointment_id},
            {"$set": {"visit_type": "telehealth", "telehealth_session_id": session.id}}
        )
        
        return {
            "message": "Telehealth session created from appointment",
            "session": session_dict,
            "existing": False
        }
    
    @telehealth_router.get("/upcoming", response_model=dict)
    async def get_upcoming_telehealth_sessions(user: dict = Depends(get_current_user)):
        """Get upcoming telehealth sessions for current user"""
        user_id = user.get("id")
        
        # Get sessions where user is provider or patient
        sessions = await db["telehealth_sessions"].find({
            "$or": [
                {"provider_id": user_id},
                {"patient_id": user_id}
            ],
            "status": {"$in": [SessionStatus.SCHEDULED.value, SessionStatus.WAITING.value]}
        }).sort("scheduled_time", 1).to_list(20)
        
        return {"sessions": sessions}
    
    # ============ WebSocket for WebRTC Signaling ============
    
    @telehealth_router.websocket("/ws/{room_id}/{user_id}")
    async def websocket_endpoint(websocket: WebSocket, room_id: str, user_id: str):
        """
        WebSocket endpoint for WebRTC signaling
        
        Message types:
        - offer: WebRTC SDP offer
        - answer: WebRTC SDP answer
        - ice-candidate: ICE candidate
        - chat: Text chat message
        - leave: User leaving
        """
        await manager.connect(websocket, room_id, user_id)
        
        # Send current participants to new user
        participants = manager.get_room_participants(room_id)
        await websocket.send_json({
            "type": "room-info",
            "participants": participants,
            "room_id": room_id
        })
        
        try:
            while True:
                data = await websocket.receive_json()
                message_type = data.get("type")
                
                if message_type == "offer":
                    # Forward SDP offer to specific user or broadcast
                    target_user = data.get("to_user")
                    if target_user:
                        await manager.send_to_user(room_id, target_user, {
                            "type": "offer",
                            "sdp": data.get("sdp"),
                            "from_user": user_id
                        })
                    else:
                        await manager.broadcast_to_room(room_id, {
                            "type": "offer",
                            "sdp": data.get("sdp"),
                            "from_user": user_id
                        }, exclude=user_id)
                
                elif message_type == "answer":
                    # Forward SDP answer to specific user
                    target_user = data.get("to_user")
                    if target_user:
                        await manager.send_to_user(room_id, target_user, {
                            "type": "answer",
                            "sdp": data.get("sdp"),
                            "from_user": user_id
                        })
                
                elif message_type == "ice-candidate":
                    # Forward ICE candidate
                    target_user = data.get("to_user")
                    if target_user:
                        await manager.send_to_user(room_id, target_user, {
                            "type": "ice-candidate",
                            "candidate": data.get("candidate"),
                            "from_user": user_id
                        })
                    else:
                        await manager.broadcast_to_room(room_id, {
                            "type": "ice-candidate",
                            "candidate": data.get("candidate"),
                            "from_user": user_id
                        }, exclude=user_id)
                
                elif message_type == "chat":
                    # Broadcast chat message
                    await manager.broadcast_to_room(room_id, {
                        "type": "chat",
                        "message": data.get("message"),
                        "from_user": user_id,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                
                elif message_type == "leave":
                    break
                
                elif message_type == "ping":
                    await websocket.send_json({"type": "pong"})
        
        except WebSocketDisconnect:
            pass
        finally:
            manager.disconnect(room_id, user_id)
            await manager.broadcast_to_room(room_id, {
                "type": "user-left",
                "user_id": user_id,
                "participant_count": len(manager.get_room_participants(room_id))
            })
    
    # ============ Dyte Integration (Ready for API Key) ============
    
    @telehealth_router.post("/dyte/create-meeting", response_model=dict)
    async def create_dyte_meeting(session_id: str, user: dict = Depends(get_current_user)):
        """
        Create a Dyte meeting for a telehealth session
        Requires DYTE_API_KEY and DYTE_ORG_ID environment variables
        """
        if not DYTE_ENABLED:
            return {
                "message": "Dyte integration not configured",
                "dyte_enabled": False,
                "instructions": "Set DYTE_API_KEY and DYTE_ORG_ID environment variables to enable Dyte integration"
            }
        
        # This would be the Dyte API call when key is provided
        # For now, return instructions
        return {
            "message": "Dyte integration ready",
            "dyte_enabled": True,
            "session_id": session_id,
            "note": "Implement Dyte API call here with your API key"
        }
    
    @telehealth_router.get("/dyte/status", response_model=dict)
    async def get_dyte_status(user: dict = Depends(get_current_user)):
        """Check Dyte integration status"""
        return {
            "dyte_enabled": DYTE_ENABLED,
            "dyte_org_id": DYTE_ORG_ID[:8] + "..." if DYTE_ORG_ID else None,
            "api_key_configured": bool(DYTE_API_KEY),
            "features_available": {
                "cloud_recording": DYTE_ENABLED,
                "transcription": DYTE_ENABLED,
                "analytics": DYTE_ENABLED
            }
        }
    
    return telehealth_router
