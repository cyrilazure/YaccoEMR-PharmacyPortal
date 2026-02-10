"""
Internal Staff Chat Module for Yacco Health EMR
================================================
Real-time messaging between hospital staff members.
REFACTORED to use db_service_v2 for database abstraction.

Features:
- Direct messages between any staff members
- Group chats by department or role
- Real-time message delivery via WebSocket
- Message history and search
- Read receipts
- File attachments support
- Typing indicators
"""

import uuid
import os
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from enum import Enum
import logging
import asyncio

from security import get_current_user, TokenPayload, audit_log
from db_service_v2 import get_db_service

logger = logging.getLogger(__name__)


# ============== Enums ==============

class ChatType(str, Enum):
    DIRECT = "direct"
    GROUP = "group"
    DEPARTMENT = "department"
    BROADCAST = "broadcast"


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"


# ============== Pydantic Models ==============

class MessageCreate(BaseModel):
    """Create a new message"""
    content: str
    message_type: MessageType = MessageType.TEXT
    attachment_url: Optional[str] = None
    attachment_name: Optional[str] = None


class ConversationCreate(BaseModel):
    """Create a new conversation"""
    chat_type: ChatType = ChatType.DIRECT
    participant_ids: List[str]
    name: Optional[str] = None  # For group chats
    department_id: Optional[str] = None  # For department chats


class ConversationUpdate(BaseModel):
    """Update conversation settings"""
    name: Optional[str] = None
    add_participants: Optional[List[str]] = None
    remove_participants: Optional[List[str]] = None


# ============== WebSocket Connection Manager ==============

class ConnectionManager:
    """Manages WebSocket connections for real-time chat"""
    
    def __init__(self):
        # user_id -> WebSocket connection
        self.active_connections: Dict[str, WebSocket] = {}
        # conversation_id -> set of user_ids
        self.conversation_subscribers: Dict[str, set] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept and store a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"User {user_id} connected to chat")
    
    def disconnect(self, user_id: str):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected from chat")
    
    def subscribe_to_conversation(self, user_id: str, conversation_id: str):
        """Subscribe a user to a conversation"""
        if conversation_id not in self.conversation_subscribers:
            self.conversation_subscribers[conversation_id] = set()
        self.conversation_subscribers[conversation_id].add(user_id)
    
    def unsubscribe_from_conversation(self, user_id: str, conversation_id: str):
        """Unsubscribe a user from a conversation"""
        if conversation_id in self.conversation_subscribers:
            self.conversation_subscribers[conversation_id].discard(user_id)
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send a message to a specific user"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {e}")
                self.disconnect(user_id)
    
    async def broadcast_to_conversation(self, conversation_id: str, message: dict, exclude_user: str = None):
        """Broadcast a message to all users in a conversation"""
        if conversation_id in self.conversation_subscribers:
            for user_id in self.conversation_subscribers[conversation_id]:
                if user_id != exclude_user:
                    await self.send_to_user(user_id, message)
    
    async def send_typing_indicator(self, conversation_id: str, user_id: str, user_name: str, is_typing: bool):
        """Send typing indicator to conversation participants"""
        message = {
            "type": "typing",
            "conversation_id": conversation_id,
            "user_id": user_id,
            "user_name": user_name,
            "is_typing": is_typing
        }
        await self.broadcast_to_conversation(conversation_id, message, exclude_user=user_id)


# Global connection manager
chat_manager = ConnectionManager()


# ============== Module Factory ==============

def create_staff_chat_router(db) -> APIRouter:
    """Create the staff chat router with database dependency"""
    
    router = APIRouter(prefix="/api/chat", tags=["Staff Chat"])
    
    # ============== Helper Functions ==============
    
    async def get_user_details(user_id: str) -> dict:
        """Get user details for chat"""
        db_svc = get_db_service()
        user = await db_svc.find_one("users", {"id": user_id}, {"password_hash": 0})
        return user
    
    async def get_conversation(conversation_id: str) -> dict:
        """Get conversation by ID"""
        db_svc = get_db_service()
        conversation = await db_svc.get_by_id("chat_conversations", conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation
    
    async def user_in_conversation(user_id: str, conversation_id: str) -> bool:
        """Check if user is a participant in the conversation"""
        db_svc = get_db_service()
        conversation = await db_svc.find_one("chat_conversations", {
            "id": conversation_id,
            "participant_ids": user_id
        })
        return conversation is not None
    
    # ============== Conversations ==============
    
    @router.post("/conversations", response_model=dict)
    async def create_conversation(
        data: ConversationCreate,
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """
        Create a new conversation.
        - DIRECT: One-on-one chat between two users
        - GROUP: Multi-user chat with custom name
        - DEPARTMENT: Chat for all members of a department
        """
        db_svc = get_db_service()
        now = datetime.now(timezone.utc)
        
        # Ensure current user is in participants
        participant_ids = list(set(data.participant_ids + [current_user.user_id]))
        
        # For direct chats, check if conversation already exists
        if data.chat_type == ChatType.DIRECT and len(participant_ids) == 2:
            existing = await db_svc.find_one("chat_conversations", {
                "chat_type": "direct",
                "participant_ids": {"$all": participant_ids, "$size": 2}
            })
            
            if existing:
                return {"success": True, "conversation": existing, "existing": True}
        
        # Get participant details for display
        participants = []
        for pid in participant_ids:
            user = await get_user_details(pid)
            if user:
                participants.append({
                    "id": user["id"],
                    "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                    "role": user.get("role"),
                    "email": user.get("email")
                })
        
        # Generate conversation name for direct chats
        conversation_name = data.name
        if not conversation_name and data.chat_type == ChatType.DIRECT:
            other_user = next((p for p in participants if p["id"] != current_user.user_id), None)
            conversation_name = other_user["name"] if other_user else "Direct Message"
        
        conversation = {
            "id": str(uuid.uuid4()),
            "chat_type": data.chat_type.value,
            "name": conversation_name,
            "participant_ids": participant_ids,
            "participants": participants,
            "organization_id": current_user.organization_id,
            "department_id": data.department_id,
            "created_by": current_user.user_id,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "last_message": None,
            "last_message_at": None,
            "unread_counts": {pid: 0 for pid in participant_ids}
        }
        
        await db_svc.insert("chat_conversations", conversation, generate_id=False)
        
        logger.info(f"Created {data.chat_type.value} conversation: {conversation['id']}")
        
        return {"success": True, "conversation": conversation}
    
    @router.get("/conversations", response_model=dict)
    async def list_conversations(
        limit: int = Query(50, le=100),
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """List all conversations for the current user"""
        db_svc = get_db_service()
        conversations = await db_svc.find(
            "chat_conversations",
            {"participant_ids": current_user.user_id},
            sort=[("last_message_at", -1)],
            limit=limit
        )
        
        # Calculate unread count for each conversation
        for conv in conversations:
            unread_counts = conv.get("unread_counts", {})
            conv["unread_count"] = unread_counts.get(current_user.user_id, 0)
        
        return {
            "conversations": conversations,
            "total": len(conversations)
        }
    
    @router.get("/conversations/{conversation_id}", response_model=dict)
    async def get_conversation_details(
        conversation_id: str,
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """Get conversation details"""
        if not await user_in_conversation(current_user.user_id, conversation_id):
            raise HTTPException(status_code=403, detail="Not a member of this conversation")
        
        conversation = await get_conversation(conversation_id)
        return {"conversation": conversation}
    
    # ============== Messages ==============
    
    @router.post("/conversations/{conversation_id}/messages", response_model=dict)
    async def send_message(
        conversation_id: str,
        message: MessageCreate,
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """Send a message to a conversation"""
        db_svc = get_db_service()
        
        if not await user_in_conversation(current_user.user_id, conversation_id):
            raise HTTPException(status_code=403, detail="Not a member of this conversation")
        
        conversation = await get_conversation(conversation_id)
        
        # Get sender details
        sender = await get_user_details(current_user.user_id)
        sender_name = f"{sender.get('first_name', '')} {sender.get('last_name', '')}".strip() if sender else "Unknown"
        
        now = datetime.now(timezone.utc)
        
        msg = {
            "id": str(uuid.uuid4()),
            "conversation_id": conversation_id,
            "sender_id": current_user.user_id,
            "sender_name": sender_name,
            "sender_role": sender.get("role") if sender else None,
            "content": message.content,
            "message_type": message.message_type.value,
            "attachment_url": message.attachment_url,
            "attachment_name": message.attachment_name,
            "sent_at": now.isoformat(),
            "read_by": [current_user.user_id],
            "organization_id": current_user.organization_id
        }
        
        await db_svc.insert("chat_messages", msg, generate_id=False)
        
        # Update conversation with last message
        unread_counts = conversation.get("unread_counts", {})
        for pid in conversation["participant_ids"]:
            if pid != current_user.user_id:
                unread_counts[pid] = unread_counts.get(pid, 0) + 1
        
        await db_svc.update_by_id("chat_conversations", conversation_id, {
            "last_message": message.content[:100],
            "last_message_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "unread_counts": unread_counts
        })
        
        # Broadcast to connected users
        broadcast_msg = {
            "type": "message",
            "conversation_id": conversation_id,
            "message": msg
        }
        await chat_manager.broadcast_to_conversation(
            conversation_id, broadcast_msg, exclude_user=current_user.user_id
        )
        
        return {"success": True, "message": msg}
    
    @router.get("/conversations/{conversation_id}/messages", response_model=dict)
    async def get_messages(
        conversation_id: str,
        limit: int = Query(50, le=200),
        before: Optional[str] = None,
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """Get messages from a conversation"""
        db_svc = get_db_service()
        
        if not await user_in_conversation(current_user.user_id, conversation_id):
            raise HTTPException(status_code=403, detail="Not a member of this conversation")
        
        query = {"conversation_id": conversation_id}
        if before:
            query["sent_at"] = {"$lt": before}
        
        messages = await db_svc.find(
            "chat_messages",
            query,
            sort=[("sent_at", -1)],
            limit=limit
        )
        
        # Mark messages as read - use direct MongoDB for $addToSet
        await db_svc.collection("chat_messages").update_many(
            {
                "conversation_id": conversation_id,
                "sender_id": {"$ne": current_user.user_id},
                "read_by": {"$ne": current_user.user_id}
            },
            {"$addToSet": {"read_by": current_user.user_id}}
        )
        
        # Reset unread count for this user - use direct MongoDB for nested field update
        await db_svc.collection("chat_conversations").update_one(
            {"id": conversation_id},
            {"$set": {f"unread_counts.{current_user.user_id}": 0}}
        )
        
        return {
            "messages": list(reversed(messages)),  # Chronological order
            "conversation_id": conversation_id,
            "total": len(messages)
        }
    
    # ============== Mark as Read ==============
    
    @router.post("/conversations/{conversation_id}/read", response_model=dict)
    async def mark_as_read(
        conversation_id: str,
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """Mark all messages in a conversation as read"""
        db_svc = get_db_service()
        
        if not await user_in_conversation(current_user.user_id, conversation_id):
            raise HTTPException(status_code=403, detail="Not a member of this conversation")
        
        # Use direct MongoDB for $addToSet
        await db_svc.collection("chat_messages").update_many(
            {
                "conversation_id": conversation_id,
                "sender_id": {"$ne": current_user.user_id},
                "read_by": {"$ne": current_user.user_id}
            },
            {"$addToSet": {"read_by": current_user.user_id}}
        )
        
        await db_svc.collection("chat_conversations").update_one(
            {"id": conversation_id},
            {"$set": {f"unread_counts.{current_user.user_id}": 0}}
        )
        
        return {"success": True}
    
    # ============== Search ==============
    
    @router.get("/search", response_model=dict)
    async def search_messages(
        query: str = Query(..., min_length=2),
        limit: int = 20,
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """Search messages across all user's conversations"""
        db_svc = get_db_service()
        
        # Get user's conversations
        conversations = await db_svc.find(
            "chat_conversations",
            {"participant_ids": current_user.user_id},
            projection={"id": 1},
            limit=1000
        )
        
        conversation_ids = [c["id"] for c in conversations]
        
        # Search messages
        messages = await db_svc.find(
            "chat_messages",
            {
                "conversation_id": {"$in": conversation_ids},
                "content": {"$regex": query, "$options": "i"}
            },
            sort=[("sent_at", -1)],
            limit=limit
        )
        
        return {
            "messages": messages,
            "query": query,
            "total": len(messages)
        }
    
    # ============== Users Search ==============
    
    @router.get("/users/search", response_model=dict)
    async def search_users_for_chat(
        query: str = Query(..., min_length=2),
        limit: int = 20,
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """Search for users to start a conversation with"""
        db_svc = get_db_service()
        
        users = await db_svc.find(
            "users",
            {
                "organization_id": current_user.organization_id,
                "id": {"$ne": current_user.user_id},
                "is_active": True,
                "$or": [
                    {"first_name": {"$regex": query, "$options": "i"}},
                    {"last_name": {"$regex": query, "$options": "i"}},
                    {"email": {"$regex": query, "$options": "i"}}
                ]
            },
            projection={"password_hash": 0},
            limit=limit
        )
        
        return {
            "users": [{
                "id": u["id"],
                "name": f"{u.get('first_name', '')} {u.get('last_name', '')}".strip(),
                "email": u.get("email"),
                "role": u.get("role"),
                "department": u.get("department")
            } for u in users],
            "total": len(users)
        }
    
    # ============== Unread Count ==============
    
    @router.get("/unread-count", response_model=dict)
    async def get_unread_count(
        current_user: TokenPayload = Depends(get_current_user)
    ):
        """Get total unread message count for the current user"""
        db_svc = get_db_service()
        
        conversations = await db_svc.find(
            "chat_conversations",
            {"participant_ids": current_user.user_id},
            projection={"unread_counts": 1},
            limit=1000
        )
        
        total_unread = sum(
            c.get("unread_counts", {}).get(current_user.user_id, 0)
            for c in conversations
        )
        
        return {"unread_count": total_unread}
    
    return router


# ============== WebSocket Endpoint ==============

def create_chat_websocket_router(db) -> APIRouter:
    """Create WebSocket router for real-time chat"""
    
    ws_router = APIRouter(tags=["Chat WebSocket"])
    
    @ws_router.websocket("/ws/chat/{token}")
    async def chat_websocket(websocket: WebSocket, token: str):
        """
        WebSocket endpoint for real-time chat.
        Connect with: ws://host/ws/chat/{jwt_token}
        """
        from security import decode_access_token
        
        try:
            # Verify token
            payload = decode_access_token(token)
            if not payload:
                await websocket.close(code=4001, reason="Invalid token")
                return
            
            user_id = payload.user_id
            db_svc = get_db_service()
            
            # Connect
            await chat_manager.connect(websocket, user_id)
            
            # Subscribe to user's conversations
            conversations = await db_svc.find(
                "chat_conversations",
                {"participant_ids": user_id},
                projection={"id": 1},
                limit=1000
            )
            
            for conv in conversations:
                chat_manager.subscribe_to_conversation(user_id, conv["id"])
            
            # Send connection confirmation
            await websocket.send_json({
                "type": "connected",
                "user_id": user_id,
                "conversations": len(conversations)
            })
            
            # Listen for messages
            while True:
                data = await websocket.receive_json()
                
                if data.get("type") == "typing":
                    # Handle typing indicator
                    conversation_id = data.get("conversation_id")
                    is_typing = data.get("is_typing", False)
                    user_name = data.get("user_name", "Someone")
                    
                    await chat_manager.send_typing_indicator(
                        conversation_id, user_id, user_name, is_typing
                    )
                
                elif data.get("type") == "subscribe":
                    # Subscribe to a new conversation
                    conversation_id = data.get("conversation_id")
                    chat_manager.subscribe_to_conversation(user_id, conversation_id)
                
                elif data.get("type") == "ping":
                    # Heartbeat
                    await websocket.send_json({"type": "pong"})
        
        except WebSocketDisconnect:
            chat_manager.disconnect(user_id)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            chat_manager.disconnect(user_id)
    
    return ws_router


# Create default router for import
staff_chat_router = APIRouter(prefix="/api/chat", tags=["Staff Chat"])
