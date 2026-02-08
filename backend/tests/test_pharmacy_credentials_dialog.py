"""
Test cases for Pharmacy Staff Credentials Dialog feature
Tests staff creation and password reset endpoints to verify they return credentials
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPharmacyStaffCreation:
    """Test staff creation returns default_password"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token for pharmacy IT admin"""
        response = requests.post(
            f"{BASE_URL}/api/pharmacy-portal/auth/login",
            json={"email": "anita@pharmacy.com", "password": "test123"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_create_staff_returns_default_password(self):
        """Test that creating staff returns default_password in response"""
        import time
        timestamp = int(time.time())
        
        staff_data = {
            "email": f"test_cred_{timestamp}@pharmacy.com",
            "first_name": "Test",
            "last_name": "Credentials",
            "phone": "+233501234567",
            "role": "pharmacist",
            "department": "dispensary"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pharmacy-portal/admin/staff",
            json=staff_data,
            headers=self.headers
        )
        
        # Status code assertion
        assert response.status_code == 200, f"Staff creation failed: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "staff_id" in data, "Response should contain staff_id"
        assert "default_password" in data, "Response should contain default_password"
        assert "message" in data, "Response should contain message"
        
        # Verify password format (last 8 digits of phone)
        default_password = data["default_password"]
        assert len(default_password) >= 6, "Password should be at least 6 characters"
        assert default_password == "01234567", f"Expected password '01234567', got '{default_password}'"
        
        print(f"SUCCESS: Staff created with default_password: {default_password}")
    
    def test_create_staff_response_structure(self):
        """Test the complete response structure of staff creation"""
        import time
        timestamp = int(time.time())
        
        staff_data = {
            "email": f"test_struct_{timestamp}@pharmacy.com",
            "first_name": "Structure",
            "last_name": "Test",
            "phone": "+233509876543",
            "role": "pharmacy_technician",
            "department": "inventory"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pharmacy-portal/admin/staff",
            json=staff_data,
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected fields
        expected_fields = ["message", "staff_id", "default_password", "note"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify message content
        assert "successfully" in data["message"].lower(), "Message should indicate success"
        
        # Verify note content
        assert "temporary password" in data["note"].lower(), "Note should mention temporary password"


class TestPharmacyPasswordReset:
    """Test password reset returns temp_password"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token and create a test staff member"""
        # Login
        response = requests.post(
            f"{BASE_URL}/api/pharmacy-portal/auth/login",
            json={"email": "anita@pharmacy.com", "password": "test123"}
        )
        assert response.status_code == 200
        self.token = response.json().get("token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Get existing staff list
        staff_response = requests.get(
            f"{BASE_URL}/api/pharmacy-portal/admin/staff",
            headers=self.headers
        )
        assert staff_response.status_code == 200
        staff_list = staff_response.json().get("staff", [])
        
        # Find a non-admin staff member to reset password
        self.test_staff = None
        for staff in staff_list:
            if staff.get("role") != "pharmacy_it_admin":
                self.test_staff = staff
                break
        
        assert self.test_staff is not None, "No non-admin staff found for testing"
    
    def test_reset_password_returns_temp_password(self):
        """Test that password reset returns temp_password in response"""
        staff_id = self.test_staff["id"]
        
        response = requests.put(
            f"{BASE_URL}/api/pharmacy-portal/admin/staff/{staff_id}/reset-password",
            headers=self.headers
        )
        
        # Status code assertion
        assert response.status_code == 200, f"Password reset failed: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "message" in data, "Response should contain message"
        assert "temp_password" in data, "Response should contain temp_password"
        
        # Verify message
        assert "reset" in data["message"].lower(), "Message should mention reset"
        
        # Verify password format
        temp_password = data["temp_password"]
        assert len(temp_password) >= 6, "Temp password should be at least 6 characters"
        
        print(f"SUCCESS: Password reset with temp_password: {temp_password}")
    
    def test_reset_password_for_nonexistent_staff(self):
        """Test password reset for non-existent staff returns 404"""
        response = requests.put(
            f"{BASE_URL}/api/pharmacy-portal/admin/staff/nonexistent-id-12345/reset-password",
            headers=self.headers
        )
        
        assert response.status_code == 404, "Should return 404 for non-existent staff"


class TestPharmacyStaffEndpoints:
    """Test staff management endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token"""
        response = requests.post(
            f"{BASE_URL}/api/pharmacy-portal/auth/login",
            json={"email": "anita@pharmacy.com", "password": "test123"}
        )
        assert response.status_code == 200
        self.token = response.json().get("token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_get_staff_list(self):
        """Test getting staff list"""
        response = requests.get(
            f"{BASE_URL}/api/pharmacy-portal/admin/staff",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "staff" in data, "Response should contain staff list"
        assert isinstance(data["staff"], list), "Staff should be a list"
        
        # Verify staff structure
        if len(data["staff"]) > 0:
            staff = data["staff"][0]
            expected_fields = ["id", "email", "first_name", "last_name", "role"]
            for field in expected_fields:
                assert field in staff, f"Staff should have {field} field"
            
            # Verify password is not exposed
            assert "password" not in staff, "Password should not be exposed in staff list"
    
    def test_get_staff_details(self):
        """Test getting staff details"""
        # First get staff list
        list_response = requests.get(
            f"{BASE_URL}/api/pharmacy-portal/admin/staff",
            headers=self.headers
        )
        staff_list = list_response.json().get("staff", [])
        
        if len(staff_list) > 0:
            staff_id = staff_list[0]["id"]
            
            response = requests.get(
                f"{BASE_URL}/api/pharmacy-portal/admin/staff/{staff_id}",
                headers=self.headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "staff" in data, "Response should contain staff details"
            
            # Verify password is not exposed
            assert "password" not in data["staff"], "Password should not be exposed"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
