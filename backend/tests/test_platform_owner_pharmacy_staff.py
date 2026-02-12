"""
Platform Owner Pharmacy Staff Management Tests
==============================================
Tests for the new Platform Owner endpoints that manage pharmacy staff
across all pharmacies without requiring pharmacy-specific authentication.

Endpoints tested:
- GET /api/pharmacy-portal/platform-owner/staff - List all pharmacy staff
- GET /api/pharmacy-portal/platform-owner/staff/{staff_id} - Get staff details
- PUT /api/pharmacy-portal/platform-owner/staff/{staff_id} - Edit staff
- PUT /api/pharmacy-portal/platform-owner/staff/{staff_id}/suspend - Suspend staff
- PUT /api/pharmacy-portal/platform-owner/staff/{staff_id}/activate - Activate staff
- PUT /api/pharmacy-portal/platform-owner/staff/{staff_id}/unlock - Unlock staff
- PUT /api/pharmacy-portal/platform-owner/staff/{staff_id}/deactivate - Deactivate staff
- PUT /api/pharmacy-portal/platform-owner/staff/{staff_id}/reset-password - Reset password
- DELETE /api/pharmacy-portal/platform-owner/staff/{staff_id} - Delete staff
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestPlatformOwnerStaffListEndpoint:
    """Test GET /api/pharmacy-portal/platform-owner/staff"""
    
    def test_list_all_pharmacy_staff_endpoint_exists(self):
        """Verify the endpoint exists and returns 200"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_list_all_pharmacy_staff_returns_correct_structure(self):
        """Verify response has staff array and total count"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff")
        assert response.status_code == 200
        
        data = response.json()
        assert "staff" in data, "Response should contain 'staff' key"
        assert "total" in data, "Response should contain 'total' key"
        assert isinstance(data["staff"], list), "staff should be a list"
        assert isinstance(data["total"], int), "total should be an integer"
    
    def test_list_all_pharmacy_staff_no_passwords_exposed(self):
        """Verify passwords are not exposed in the response"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff")
        assert response.status_code == 200
        
        data = response.json()
        for staff in data.get("staff", []):
            assert "password" not in staff, "Password should not be exposed"


class TestPlatformOwnerStaffDetailsEndpoint:
    """Test GET /api/pharmacy-portal/platform-owner/staff/{staff_id}"""
    
    def test_get_staff_details_nonexistent(self):
        """Verify 404 for non-existent staff"""
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{fake_id}")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_get_staff_details_existing(self):
        """Verify getting details of existing staff"""
        # First get list of staff
        list_response = requests.get(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff")
        assert list_response.status_code == 200
        
        staff_list = list_response.json().get("staff", [])
        if len(staff_list) == 0:
            pytest.skip("No pharmacy staff available for testing")
        
        staff_id = staff_list[0]["id"]
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{staff_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "staff" in data, "Response should contain 'staff' key"
        assert data["staff"]["id"] == staff_id, "Staff ID should match"
        assert "password" not in data["staff"], "Password should not be exposed"


class TestPlatformOwnerStaffEditEndpoint:
    """Test PUT /api/pharmacy-portal/platform-owner/staff/{staff_id}"""
    
    def test_edit_staff_nonexistent(self):
        """Verify 404 for non-existent staff"""
        fake_id = str(uuid.uuid4())
        response = requests.put(
            f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{fake_id}",
            json={"first_name": "Test"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_edit_staff_existing(self):
        """Verify editing existing staff"""
        # First get list of staff
        list_response = requests.get(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff")
        assert list_response.status_code == 200
        
        staff_list = list_response.json().get("staff", [])
        if len(staff_list) == 0:
            pytest.skip("No pharmacy staff available for testing")
        
        staff_id = staff_list[0]["id"]
        original_first_name = staff_list[0].get("first_name", "")
        
        # Edit the staff
        new_first_name = f"TEST_Updated_{uuid.uuid4().hex[:6]}"
        response = requests.put(
            f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{staff_id}",
            json={"first_name": new_first_name}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify the change
        verify_response = requests.get(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{staff_id}")
        assert verify_response.status_code == 200
        assert verify_response.json()["staff"]["first_name"] == new_first_name
        
        # Restore original name
        requests.put(
            f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{staff_id}",
            json={"first_name": original_first_name}
        )


class TestPlatformOwnerStaffSuspendEndpoint:
    """Test PUT /api/pharmacy-portal/platform-owner/staff/{staff_id}/suspend"""
    
    def test_suspend_staff_nonexistent(self):
        """Verify 404 for non-existent staff"""
        fake_id = str(uuid.uuid4())
        response = requests.put(
            f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{fake_id}/suspend",
            json={"reason": "Test suspension"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_suspend_staff_existing(self):
        """Verify suspending existing staff"""
        # First get list of staff
        list_response = requests.get(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff")
        assert list_response.status_code == 200
        
        staff_list = list_response.json().get("staff", [])
        if len(staff_list) == 0:
            pytest.skip("No pharmacy staff available for testing")
        
        staff_id = staff_list[0]["id"]
        
        # Suspend the staff
        response = requests.put(
            f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{staff_id}/suspend",
            json={"reason": "Test suspension by platform owner"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert "suspended" in response.json().get("message", "").lower()
        
        # Verify the status change
        verify_response = requests.get(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{staff_id}")
        assert verify_response.status_code == 200
        staff_data = verify_response.json()["staff"]
        assert staff_data.get("status") == "suspended" or staff_data.get("is_active") == False


class TestPlatformOwnerStaffActivateEndpoint:
    """Test PUT /api/pharmacy-portal/platform-owner/staff/{staff_id}/activate"""
    
    def test_activate_staff_nonexistent(self):
        """Verify 404 for non-existent staff"""
        fake_id = str(uuid.uuid4())
        response = requests.put(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{fake_id}/activate")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_activate_staff_existing(self):
        """Verify activating existing staff"""
        # First get list of staff
        list_response = requests.get(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff")
        assert list_response.status_code == 200
        
        staff_list = list_response.json().get("staff", [])
        if len(staff_list) == 0:
            pytest.skip("No pharmacy staff available for testing")
        
        staff_id = staff_list[0]["id"]
        
        # Activate the staff
        response = requests.put(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{staff_id}/activate")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert "activated" in response.json().get("message", "").lower()
        
        # Verify the status change
        verify_response = requests.get(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{staff_id}")
        assert verify_response.status_code == 200
        staff_data = verify_response.json()["staff"]
        assert staff_data.get("status") == "active" or staff_data.get("is_active") == True


class TestPlatformOwnerStaffUnlockEndpoint:
    """Test PUT /api/pharmacy-portal/platform-owner/staff/{staff_id}/unlock"""
    
    def test_unlock_staff_nonexistent(self):
        """Verify 404 for non-existent staff"""
        fake_id = str(uuid.uuid4())
        response = requests.put(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{fake_id}/unlock")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_unlock_staff_existing(self):
        """Verify unlocking existing staff"""
        # First get list of staff
        list_response = requests.get(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff")
        assert list_response.status_code == 200
        
        staff_list = list_response.json().get("staff", [])
        if len(staff_list) == 0:
            pytest.skip("No pharmacy staff available for testing")
        
        staff_id = staff_list[0]["id"]
        
        # Unlock the staff
        response = requests.put(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{staff_id}/unlock")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert "unlocked" in response.json().get("message", "").lower()


class TestPlatformOwnerStaffDeactivateEndpoint:
    """Test PUT /api/pharmacy-portal/platform-owner/staff/{staff_id}/deactivate"""
    
    def test_deactivate_staff_nonexistent(self):
        """Verify 404 for non-existent staff"""
        fake_id = str(uuid.uuid4())
        response = requests.put(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{fake_id}/deactivate")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_deactivate_staff_existing(self):
        """Verify deactivating existing staff"""
        # First get list of staff
        list_response = requests.get(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff")
        assert list_response.status_code == 200
        
        staff_list = list_response.json().get("staff", [])
        if len(staff_list) == 0:
            pytest.skip("No pharmacy staff available for testing")
        
        staff_id = staff_list[0]["id"]
        
        # Deactivate the staff
        response = requests.put(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{staff_id}/deactivate")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert "deactivated" in response.json().get("message", "").lower()
        
        # Verify the status change
        verify_response = requests.get(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{staff_id}")
        assert verify_response.status_code == 200
        staff_data = verify_response.json()["staff"]
        assert staff_data.get("status") == "deactivated" or staff_data.get("is_active") == False
        
        # Re-activate for cleanup
        requests.put(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{staff_id}/activate")


class TestPlatformOwnerStaffResetPasswordEndpoint:
    """Test PUT /api/pharmacy-portal/platform-owner/staff/{staff_id}/reset-password"""
    
    def test_reset_password_nonexistent(self):
        """Verify 404 for non-existent staff"""
        fake_id = str(uuid.uuid4())
        response = requests.put(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{fake_id}/reset-password")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    def test_reset_password_existing(self):
        """Verify resetting password for existing staff"""
        # First get list of staff
        list_response = requests.get(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff")
        assert list_response.status_code == 200
        
        staff_list = list_response.json().get("staff", [])
        if len(staff_list) == 0:
            pytest.skip("No pharmacy staff available for testing")
        
        staff_id = staff_list[0]["id"]
        
        # Reset password
        response = requests.put(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{staff_id}/reset-password")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        assert "temp_password" in data, "Response should contain temp_password"
        assert len(data["temp_password"]) >= 6, "Temp password should be at least 6 characters"


class TestPlatformOwnerStaffDeleteEndpoint:
    """Test DELETE /api/pharmacy-portal/platform-owner/staff/{staff_id}"""
    
    def test_delete_staff_nonexistent(self):
        """Verify 404 for non-existent staff"""
        fake_id = str(uuid.uuid4())
        response = requests.delete(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{fake_id}")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"


class TestEndToEndPlatformOwnerStaffWorkflow:
    """End-to-end test for platform owner staff management workflow"""
    
    def test_full_staff_management_workflow(self):
        """Test complete workflow: list -> get details -> suspend -> activate -> unlock"""
        # Step 1: List all staff
        list_response = requests.get(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff")
        assert list_response.status_code == 200
        
        staff_list = list_response.json().get("staff", [])
        if len(staff_list) == 0:
            pytest.skip("No pharmacy staff available for testing")
        
        staff_id = staff_list[0]["id"]
        
        # Step 2: Get staff details
        details_response = requests.get(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{staff_id}")
        assert details_response.status_code == 200
        assert details_response.json()["staff"]["id"] == staff_id
        
        # Step 3: Suspend staff
        suspend_response = requests.put(
            f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{staff_id}/suspend",
            json={"reason": "E2E test suspension"}
        )
        assert suspend_response.status_code == 200
        
        # Step 4: Verify suspended
        verify_suspended = requests.get(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{staff_id}")
        assert verify_suspended.status_code == 200
        assert verify_suspended.json()["staff"].get("status") == "suspended" or \
               verify_suspended.json()["staff"].get("is_active") == False
        
        # Step 5: Activate staff
        activate_response = requests.put(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{staff_id}/activate")
        assert activate_response.status_code == 200
        
        # Step 6: Verify activated
        verify_activated = requests.get(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{staff_id}")
        assert verify_activated.status_code == 200
        assert verify_activated.json()["staff"].get("status") == "active" or \
               verify_activated.json()["staff"].get("is_active") == True
        
        # Step 7: Unlock staff (should work even if not locked)
        unlock_response = requests.put(f"{BASE_URL}/api/pharmacy-portal/platform-owner/staff/{staff_id}/unlock")
        assert unlock_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
