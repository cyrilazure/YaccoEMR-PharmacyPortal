"""
Staff Chat Module API Tests
===========================
Tests for the Internal Staff Chat feature allowing hospital staff to communicate.

Features tested:
- GET /api/chat/conversations - List user's conversations
- GET /api/chat/unread-count - Get total unread message count
- GET /api/chat/users/search - Search users to start conversation
- POST /api/chat/conversations - Create new conversation
- POST /api/chat/conversations/{id}/messages - Send message
- GET /api/chat/conversations/{id}/messages - Get messages
- POST /api/chat/conversations/{id}/read - Mark as read
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://medconnect-223.preview.emergentagent.com')

# Test credentials
NURSING_SUPERVISOR_CREDS = {
    "email": "nursing_supervisor@yacco.health",
    "password": "test123"
}

PHYSICIAN_CREDS = {
    "email": "physician@yacco.health",
    "password": "test123"
}

# Fallback super admin credentials
SUPER_ADMIN_CREDS = {
    "email": "ygtnetworks@gmail.com",
    "password": "test123"
}


class TestStaffChatAPI:
    """Staff Chat API endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token - try nursing_supervisor first, then super_admin"""
        # Try nursing supervisor first
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=NURSING_SUPERVISOR_CREDS
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Logged in as nursing_supervisor: {data.get('user', {}).get('email')}")
            return data.get("token")
        
        # Try physician
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=PHYSICIAN_CREDS
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Logged in as physician: {data.get('user', {}).get('email')}")
            return data.get("token")
        
        # Fallback to super admin
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=SUPER_ADMIN_CREDS
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Logged in as super_admin: {data.get('user', {}).get('email')}")
            return data.get("token")
        
        pytest.skip(f"Authentication failed - cannot proceed with tests. Status: {response.status_code}")
    
    @pytest.fixture(scope="class")
    def second_user_token(self):
        """Get second user token for conversation testing"""
        # Try super admin as second user
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=SUPER_ADMIN_CREDS
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("token"), data.get("user", {}).get("id")
        return None, None
    
    @pytest.fixture(scope="class")
    def api_client(self, auth_token):
        """Create authenticated API client"""
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth_token}"
        })
        return session
    
    # ============== Health Check ==============
    
    def test_api_health(self):
        """Test API is healthy before running chat tests"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✅ API health check passed")
    
    # ============== GET /api/chat/conversations ==============
    
    def test_get_conversations_success(self, api_client):
        """Test listing conversations for authenticated user"""
        response = api_client.get(f"{BASE_URL}/api/chat/conversations")
        assert response.status_code == 200
        
        data = response.json()
        assert "conversations" in data
        assert isinstance(data["conversations"], list)
        assert "total" in data
        print(f"✅ GET /api/chat/conversations - Found {data['total']} conversations")
    
    def test_get_conversations_unauthorized(self):
        """Test conversations endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/chat/conversations")
        assert response.status_code in [401, 403]
        print("✅ GET /api/chat/conversations - Unauthorized access blocked")
    
    # ============== GET /api/chat/unread-count ==============
    
    def test_get_unread_count_success(self, api_client):
        """Test getting unread message count"""
        response = api_client.get(f"{BASE_URL}/api/chat/unread-count")
        assert response.status_code == 200
        
        data = response.json()
        assert "unread_count" in data
        assert isinstance(data["unread_count"], int)
        assert data["unread_count"] >= 0
        print(f"✅ GET /api/chat/unread-count - Unread count: {data['unread_count']}")
    
    def test_get_unread_count_unauthorized(self):
        """Test unread count endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/chat/unread-count")
        assert response.status_code in [401, 403]
        print("✅ GET /api/chat/unread-count - Unauthorized access blocked")
    
    # ============== GET /api/chat/users/search ==============
    
    def test_search_users_success(self, api_client):
        """Test searching users for new conversation"""
        response = api_client.get(f"{BASE_URL}/api/chat/users/search?query=admin")
        assert response.status_code == 200
        
        data = response.json()
        assert "users" in data
        assert isinstance(data["users"], list)
        assert "total" in data
        print(f"✅ GET /api/chat/users/search - Found {data['total']} users matching 'admin'")
        
        # Verify user structure if results exist
        if data["users"]:
            user = data["users"][0]
            assert "id" in user
            assert "name" in user
            print(f"   Sample user: {user.get('name')} ({user.get('role')})")
    
    def test_search_users_min_query_length(self, api_client):
        """Test user search requires minimum 2 characters"""
        response = api_client.get(f"{BASE_URL}/api/chat/users/search?query=a")
        # Should return 422 (validation error) for query < 2 chars
        assert response.status_code == 422
        print("✅ GET /api/chat/users/search - Minimum query length enforced")
    
    def test_search_users_unauthorized(self):
        """Test user search requires authentication"""
        response = requests.get(f"{BASE_URL}/api/chat/users/search?query=test")
        assert response.status_code in [401, 403]
        print("✅ GET /api/chat/users/search - Unauthorized access blocked")
    
    # ============== POST /api/chat/conversations ==============
    
    def test_create_conversation_success(self, api_client, second_user_token):
        """Test creating a new direct conversation"""
        second_token, second_user_id = second_user_token
        
        if not second_user_id:
            # Search for a user to chat with
            search_response = api_client.get(f"{BASE_URL}/api/chat/users/search?query=admin")
            if search_response.status_code == 200:
                users = search_response.json().get("users", [])
                if users:
                    second_user_id = users[0]["id"]
        
        if not second_user_id:
            pytest.skip("No second user found to create conversation with")
        
        response = api_client.post(
            f"{BASE_URL}/api/chat/conversations",
            json={
                "chat_type": "direct",
                "participant_ids": [second_user_id]
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("success") == True
        assert "conversation" in data
        
        conversation = data["conversation"]
        assert "id" in conversation
        assert "chat_type" in conversation
        assert "participant_ids" in conversation
        
        print(f"✅ POST /api/chat/conversations - Created conversation: {conversation['id']}")
        return conversation["id"]
    
    def test_create_conversation_unauthorized(self):
        """Test conversation creation requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/chat/conversations",
            json={"chat_type": "direct", "participant_ids": ["test-id"]}
        )
        assert response.status_code in [401, 403]
        print("✅ POST /api/chat/conversations - Unauthorized access blocked")
    
    # ============== Full Conversation Flow ==============
    
    def test_full_conversation_flow(self, api_client, second_user_token):
        """Test complete conversation flow: create -> send message -> get messages -> mark read"""
        second_token, second_user_id = second_user_token
        
        # Step 1: Find a user to chat with
        search_response = api_client.get(f"{BASE_URL}/api/chat/users/search?query=admin")
        if search_response.status_code != 200:
            pytest.skip("Cannot search users")
        
        users = search_response.json().get("users", [])
        if not users:
            # Try searching for any user
            search_response = api_client.get(f"{BASE_URL}/api/chat/users/search?query=test")
            users = search_response.json().get("users", [])
        
        if not users:
            pytest.skip("No users found to create conversation with")
        
        target_user_id = users[0]["id"]
        print(f"   Target user: {users[0].get('name')} ({users[0].get('role')})")
        
        # Step 2: Create conversation
        create_response = api_client.post(
            f"{BASE_URL}/api/chat/conversations",
            json={
                "chat_type": "direct",
                "participant_ids": [target_user_id]
            }
        )
        assert create_response.status_code == 200
        conversation = create_response.json()["conversation"]
        conversation_id = conversation["id"]
        print(f"✅ Step 1: Created conversation {conversation_id}")
        
        # Step 3: Send a message
        test_message = f"TEST_CHAT_MESSAGE_{int(time.time())}"
        send_response = api_client.post(
            f"{BASE_URL}/api/chat/conversations/{conversation_id}/messages",
            json={
                "content": test_message,
                "message_type": "text"
            }
        )
        assert send_response.status_code == 200
        
        send_data = send_response.json()
        assert send_data.get("success") == True
        assert "message" in send_data
        
        message = send_data["message"]
        assert message["content"] == test_message
        assert "id" in message
        assert "sender_id" in message
        assert "sent_at" in message
        print(f"✅ Step 2: Sent message: {message['id']}")
        
        # Step 4: Get messages
        get_response = api_client.get(f"{BASE_URL}/api/chat/conversations/{conversation_id}/messages")
        assert get_response.status_code == 200
        
        messages_data = get_response.json()
        assert "messages" in messages_data
        assert len(messages_data["messages"]) > 0
        
        # Verify our message is in the list
        message_contents = [m["content"] for m in messages_data["messages"]]
        assert test_message in message_contents
        print(f"✅ Step 3: Retrieved {len(messages_data['messages'])} messages")
        
        # Step 5: Mark as read
        read_response = api_client.post(f"{BASE_URL}/api/chat/conversations/{conversation_id}/read")
        assert read_response.status_code == 200
        assert read_response.json().get("success") == True
        print("✅ Step 4: Marked conversation as read")
        
        # Step 6: Verify conversation appears in list
        list_response = api_client.get(f"{BASE_URL}/api/chat/conversations")
        assert list_response.status_code == 200
        
        conversations = list_response.json()["conversations"]
        conv_ids = [c["id"] for c in conversations]
        assert conversation_id in conv_ids
        print("✅ Step 5: Conversation appears in list")
        
        print("✅ Full conversation flow completed successfully!")
    
    # ============== Error Cases ==============
    
    def test_get_messages_invalid_conversation(self, api_client):
        """Test getting messages from non-existent conversation"""
        response = api_client.get(f"{BASE_URL}/api/chat/conversations/invalid-id-12345/messages")
        assert response.status_code in [403, 404]
        print("✅ GET messages - Invalid conversation handled correctly")
    
    def test_send_message_invalid_conversation(self, api_client):
        """Test sending message to non-existent conversation"""
        response = api_client.post(
            f"{BASE_URL}/api/chat/conversations/invalid-id-12345/messages",
            json={"content": "test", "message_type": "text"}
        )
        assert response.status_code in [403, 404]
        print("✅ POST message - Invalid conversation handled correctly")
    
    def test_mark_read_invalid_conversation(self, api_client):
        """Test marking non-existent conversation as read"""
        response = api_client.post(f"{BASE_URL}/api/chat/conversations/invalid-id-12345/read")
        assert response.status_code in [403, 404]
        print("✅ POST mark read - Invalid conversation handled correctly")


class TestStaffChatDataValidation:
    """Test data validation for Staff Chat API"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=SUPER_ADMIN_CREDS
        )
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture(scope="class")
    def api_client(self, auth_token):
        """Create authenticated API client"""
        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth_token}"
        })
        return session
    
    def test_create_conversation_empty_participants(self, api_client):
        """Test creating conversation with empty participants list"""
        response = api_client.post(
            f"{BASE_URL}/api/chat/conversations",
            json={
                "chat_type": "direct",
                "participant_ids": []
            }
        )
        # Should still work - current user will be added
        assert response.status_code in [200, 422]
        print("✅ Empty participants handled")
    
    def test_send_empty_message(self, api_client):
        """Test sending empty message content"""
        # First create a conversation
        search_response = api_client.get(f"{BASE_URL}/api/chat/users/search?query=admin")
        if search_response.status_code != 200:
            pytest.skip("Cannot search users")
        
        users = search_response.json().get("users", [])
        if not users:
            pytest.skip("No users found")
        
        create_response = api_client.post(
            f"{BASE_URL}/api/chat/conversations",
            json={"chat_type": "direct", "participant_ids": [users[0]["id"]]}
        )
        if create_response.status_code != 200:
            pytest.skip("Cannot create conversation")
        
        conversation_id = create_response.json()["conversation"]["id"]
        
        # Try sending empty message
        response = api_client.post(
            f"{BASE_URL}/api/chat/conversations/{conversation_id}/messages",
            json={"content": "", "message_type": "text"}
        )
        # Empty content should be rejected or handled
        print(f"   Empty message response: {response.status_code}")
        assert response.status_code in [200, 422]  # Either accepted or validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
