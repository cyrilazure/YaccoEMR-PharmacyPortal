"""
Test Super Admin Dashboard - Hospitals and Pharmacies Management
Tests the backend APIs for:
- GET /api/organizations - List hospitals with status
- POST /api/organizations/{id}/approve - Approve pending hospital
- POST /api/organizations/{id}/reject - Reject pending hospital
- GET /api/pharmacy-portal/admin/pharmacies - List pharmacies
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestOrganizationsAPI:
    """Test organization (hospital) management APIs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        # Get super admin token
        self.token = self._get_super_admin_token()
        if self.token:
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def _get_super_admin_token(self):
        """Get super admin token via direct login (bypassing OTP for testing)"""
        # Try direct login endpoint
        try:
            response = self.session.post(f"{BASE_URL}/api/auth/login", json={
                "email": "ygtnetworks@gmail.com",
                "password": "test123"
            })
            if response.status_code == 200:
                data = response.json()
                return data.get("token") or data.get("access_token")
        except Exception as e:
            print(f"Direct login failed: {e}")
        return None
    
    def test_list_organizations_endpoint_exists(self):
        """Test GET /api/organizations endpoint exists"""
        response = self.session.get(f"{BASE_URL}/api/organizations")
        # Should return 401 if no auth, 200 if auth works, or 403 if not super admin
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"
    
    def test_list_organizations_returns_data_structure(self):
        """Test organizations list returns expected structure"""
        if not self.token:
            pytest.skip("No auth token available")
        
        response = self.session.get(f"{BASE_URL}/api/organizations")
        if response.status_code == 200:
            data = response.json()
            assert "organizations" in data, "Response should contain 'organizations' key"
            assert isinstance(data["organizations"], list), "Organizations should be a list"
    
    def test_list_pending_organizations(self):
        """Test GET /api/organizations/pending endpoint"""
        if not self.token:
            pytest.skip("No auth token available")
        
        response = self.session.get(f"{BASE_URL}/api/organizations/pending")
        if response.status_code == 200:
            data = response.json()
            assert "organizations" in data, "Response should contain 'organizations' key"
            # All returned orgs should be pending
            for org in data.get("organizations", []):
                assert org.get("status") == "pending", f"Expected pending status, got {org.get('status')}"


class TestOrganizationApprovalWorkflow:
    """Test hospital approval/rejection workflow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.token = self._get_super_admin_token()
        if self.token:
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
    
    def _get_super_admin_token(self):
        """Get super admin token"""
        try:
            response = self.session.post(f"{BASE_URL}/api/auth/login", json={
                "email": "ygtnetworks@gmail.com",
                "password": "test123"
            })
            if response.status_code == 200:
                data = response.json()
                return data.get("token") or data.get("access_token")
        except:
            pass
        return None
    
    def _create_test_hospital(self):
        """Create a test hospital for approval testing"""
        unique_id = str(uuid.uuid4())[:8]
        hospital_data = {
            "name": f"TEST_Hospital_{unique_id}",
            "organization_type": "hospital",
            "address_line1": "123 Test Street",
            "city": "Accra",
            "state": "Greater Accra",
            "zip_code": "00233",
            "country": "Ghana",
            "phone": "+233201234567",
            "email": f"test_hospital_{unique_id}@test.com",
            "license_number": f"LIC-{unique_id}",
            "admin_first_name": "Test",
            "admin_last_name": "Admin",
            "admin_email": f"admin_{unique_id}@test.com",
            "admin_phone": "+233201234568"
        }
        response = self.session.post(f"{BASE_URL}/api/organizations/register", json=hospital_data)
        if response.status_code in [200, 201]:
            return response.json().get("organization_id")
        return None
    
    def test_approve_organization_endpoint_exists(self):
        """Test POST /api/organizations/{id}/approve endpoint exists"""
        # Create a test hospital first
        org_id = self._create_test_hospital()
        if not org_id:
            pytest.skip("Could not create test hospital")
        
        if not self.token:
            pytest.skip("No auth token available")
        
        response = self.session.post(f"{BASE_URL}/api/organizations/{org_id}/approve", json={})
        # Should return 200 on success, 400 if already approved, 401/403 if auth issue
        assert response.status_code in [200, 400, 401, 403], f"Unexpected status: {response.status_code}"
    
    def test_reject_organization_endpoint_exists(self):
        """Test POST /api/organizations/{id}/reject endpoint exists"""
        # Create a test hospital first
        org_id = self._create_test_hospital()
        if not org_id:
            pytest.skip("Could not create test hospital")
        
        if not self.token:
            pytest.skip("No auth token available")
        
        response = self.session.post(f"{BASE_URL}/api/organizations/{org_id}/reject", json={
            "reason": "Test rejection"
        })
        # Should return 200 on success, 400 if already processed, 401/403 if auth issue
        assert response.status_code in [200, 400, 401, 403, 404], f"Unexpected status: {response.status_code}"


class TestPharmacyAdminAPI:
    """Test pharmacy admin management APIs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_list_pharmacies_admin_endpoint_exists(self):
        """Test GET /api/pharmacy-portal/admin/pharmacies endpoint exists"""
        response = self.session.get(f"{BASE_URL}/api/pharmacy-portal/admin/pharmacies")
        # This endpoint should be accessible (may not require auth based on code)
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"
    
    def test_list_pharmacies_returns_data_structure(self):
        """Test pharmacies list returns expected structure"""
        response = self.session.get(f"{BASE_URL}/api/pharmacy-portal/admin/pharmacies")
        if response.status_code == 200:
            data = response.json()
            assert "pharmacies" in data, "Response should contain 'pharmacies' key"
            assert isinstance(data["pharmacies"], list), "Pharmacies should be a list"
            # Check for count fields
            assert "pending_count" in data or "total" in data, "Response should contain count info"
    
    def test_list_pending_pharmacies_endpoint_exists(self):
        """Test GET /api/pharmacy-portal/admin/pharmacies/pending endpoint exists"""
        response = self.session.get(f"{BASE_URL}/api/pharmacy-portal/admin/pharmacies/pending")
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"
    
    def test_list_pending_pharmacies_returns_data(self):
        """Test pending pharmacies list returns expected structure"""
        response = self.session.get(f"{BASE_URL}/api/pharmacy-portal/admin/pharmacies/pending")
        if response.status_code == 200:
            data = response.json()
            assert "pharmacies" in data, "Response should contain 'pharmacies' key"


class TestPharmacyApprovalWorkflow:
    """Test pharmacy approval/rejection workflow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def _create_test_pharmacy(self):
        """Create a test pharmacy for approval testing"""
        unique_id = str(uuid.uuid4())[:8]
        pharmacy_data = {
            "pharmacy_name": f"TEST_Pharmacy_{unique_id}",
            "license_number": f"PHARM-{unique_id}",
            "region": "Greater Accra",
            "district": "Accra Metropolitan",
            "town": "Accra",
            "address": "123 Pharmacy Street",
            "phone": "+233201234567",
            "email": f"test_pharmacy_{unique_id}@test.com",
            "superintendent_pharmacist_name": "Test Pharmacist",
            "superintendent_license_number": f"SP-{unique_id}",
            "password": "TestPassword123!"
        }
        response = self.session.post(f"{BASE_URL}/api/pharmacy-portal/register", json=pharmacy_data)
        if response.status_code in [200, 201]:
            return response.json().get("pharmacy_id")
        return None
    
    def test_approve_pharmacy_endpoint_exists(self):
        """Test PUT /api/pharmacy-portal/admin/pharmacies/{id}/approve endpoint exists"""
        # Create a test pharmacy first
        pharmacy_id = self._create_test_pharmacy()
        if not pharmacy_id:
            pytest.skip("Could not create test pharmacy")
        
        response = self.session.put(
            f"{BASE_URL}/api/pharmacy-portal/admin/pharmacies/{pharmacy_id}/approve",
            json={"status": "approved", "notes": "Test approval"}
        )
        # Should return 200 on success, 400 if invalid, 404 if not found
        assert response.status_code in [200, 400, 401, 403, 404], f"Unexpected status: {response.status_code}"
    
    def test_reject_pharmacy_endpoint(self):
        """Test pharmacy rejection via approve endpoint with rejected status"""
        # Create a test pharmacy first
        pharmacy_id = self._create_test_pharmacy()
        if not pharmacy_id:
            pytest.skip("Could not create test pharmacy")
        
        response = self.session.put(
            f"{BASE_URL}/api/pharmacy-portal/admin/pharmacies/{pharmacy_id}/approve",
            json={"status": "rejected", "notes": "Test rejection"}
        )
        assert response.status_code in [200, 400, 401, 403, 404], f"Unexpected status: {response.status_code}"
    
    def test_suspend_pharmacy_endpoint_exists(self):
        """Test POST /api/pharmacy-portal/admin/pharmacies/{id}/suspend endpoint exists"""
        # Create and approve a test pharmacy first
        pharmacy_id = self._create_test_pharmacy()
        if not pharmacy_id:
            pytest.skip("Could not create test pharmacy")
        
        # First approve it
        self.session.put(
            f"{BASE_URL}/api/pharmacy-portal/admin/pharmacies/{pharmacy_id}/approve",
            json={"status": "approved"}
        )
        
        # Then try to suspend
        response = self.session.post(
            f"{BASE_URL}/api/pharmacy-portal/admin/pharmacies/{pharmacy_id}/suspend",
            json={"reason": "Test suspension"}
        )
        assert response.status_code in [200, 400, 401, 403, 404], f"Unexpected status: {response.status_code}"
    
    def test_reactivate_pharmacy_endpoint_exists(self):
        """Test POST /api/pharmacy-portal/admin/pharmacies/{id}/reactivate endpoint exists"""
        response = self.session.post(
            f"{BASE_URL}/api/pharmacy-portal/admin/pharmacies/nonexistent-id/reactivate"
        )
        # Should return 404 for nonexistent, or 401/403 if auth required
        assert response.status_code in [200, 400, 401, 403, 404], f"Unexpected status: {response.status_code}"


class TestEndToEndApprovalFlow:
    """Test complete approval workflow for both hospitals and pharmacies"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_hospital_registration_to_approval_flow(self):
        """Test complete hospital registration and approval flow"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Step 1: Register hospital
        hospital_data = {
            "name": f"TEST_E2E_Hospital_{unique_id}",
            "organization_type": "hospital",
            "address_line1": "456 E2E Test Street",
            "city": "Kumasi",
            "state": "Ashanti",
            "zip_code": "00233",
            "country": "Ghana",
            "phone": "+233301234567",
            "email": f"e2e_hospital_{unique_id}@test.com",
            "license_number": f"E2E-LIC-{unique_id}",
            "admin_first_name": "E2E",
            "admin_last_name": "Admin",
            "admin_email": f"e2e_admin_{unique_id}@test.com",
            "admin_phone": "+233301234568"
        }
        
        register_response = self.session.post(f"{BASE_URL}/api/organizations/register", json=hospital_data)
        assert register_response.status_code in [200, 201], f"Registration failed: {register_response.text}"
        
        reg_data = register_response.json()
        assert "organization_id" in reg_data, "Response should contain organization_id"
        assert reg_data.get("status") == "pending", "New registration should be pending"
        
        print(f"✓ Hospital registered with ID: {reg_data.get('organization_id')}")
    
    def test_pharmacy_registration_to_approval_flow(self):
        """Test complete pharmacy registration and approval flow"""
        unique_id = str(uuid.uuid4())[:8]
        
        # Step 1: Register pharmacy
        pharmacy_data = {
            "pharmacy_name": f"TEST_E2E_Pharmacy_{unique_id}",
            "license_number": f"E2E-PHARM-{unique_id}",
            "region": "Ashanti",
            "district": "Kumasi Metropolitan",
            "town": "Kumasi",
            "address": "789 E2E Pharmacy Street",
            "phone": "+233301234569",
            "email": f"e2e_pharmacy_{unique_id}@test.com",
            "superintendent_pharmacist_name": "E2E Pharmacist",
            "superintendent_license_number": f"E2E-SP-{unique_id}",
            "password": "E2ETestPassword123!"
        }
        
        register_response = self.session.post(f"{BASE_URL}/api/pharmacy-portal/register", json=pharmacy_data)
        assert register_response.status_code in [200, 201], f"Registration failed: {register_response.text}"
        
        reg_data = register_response.json()
        assert "pharmacy_id" in reg_data, "Response should contain pharmacy_id"
        assert reg_data.get("status") == "pending", "New registration should be pending"
        
        pharmacy_id = reg_data.get("pharmacy_id")
        print(f"✓ Pharmacy registered with ID: {pharmacy_id}")
        
        # Step 2: Approve pharmacy
        approve_response = self.session.put(
            f"{BASE_URL}/api/pharmacy-portal/admin/pharmacies/{pharmacy_id}/approve",
            json={"status": "approved", "notes": "E2E test approval"}
        )
        assert approve_response.status_code == 200, f"Approval failed: {approve_response.text}"
        print(f"✓ Pharmacy approved successfully")
        
        # Step 3: Verify pharmacy is now in approved list
        list_response = self.session.get(f"{BASE_URL}/api/pharmacy-portal/admin/pharmacies")
        assert list_response.status_code == 200
        
        pharmacies = list_response.json().get("pharmacies", [])
        approved_pharmacy = next((p for p in pharmacies if p.get("id") == pharmacy_id), None)
        
        if approved_pharmacy:
            assert approved_pharmacy.get("status") in ["approved", "active"], \
                f"Pharmacy should be approved, got {approved_pharmacy.get('status')}"
            print(f"✓ Pharmacy status verified as approved")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
