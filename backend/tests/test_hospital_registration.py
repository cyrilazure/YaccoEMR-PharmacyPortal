"""
Hospital Registration and Approval Workflow Tests
Tests for:
- Hospital self-service registration (public endpoint)
- Super Admin approval/rejection workflow
- Organization management endpoints
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "ygtnetworks@gmail.com"
SUPER_ADMIN_PASSWORD = "test123"


class TestHospitalRegistrationEndpoint:
    """Test the public hospital registration endpoint"""
    
    def test_register_hospital_success(self):
        """Test successful hospital registration submission"""
        unique_id = str(uuid.uuid4())[:8]
        registration_data = {
            "name": f"TEST_Hospital_{unique_id}",
            "organization_type": "hospital",
            "license_number": f"LIC-{unique_id}",
            "npi_number": f"NPI-{unique_id}",
            "tax_id": f"TAX-{unique_id}",
            "address_line1": "123 Test Street",
            "address_line2": "Suite 100",
            "city": "Accra",
            "state": "Greater Accra",
            "zip_code": "GA-123",
            "country": "Ghana",
            "phone": "030-1234567",
            "fax": "030-1234568",
            "email": f"test_{unique_id}@hospital.gh",
            "website": "https://testhospital.gh",
            "admin_first_name": "Test",
            "admin_last_name": "Admin",
            "admin_email": f"admin_{unique_id}@hospital.gh",
            "admin_phone": "024-1234567",
            "admin_title": "Hospital Administrator"
        }
        
        response = requests.post(f"{BASE_URL}/api/organizations/register", json=registration_data)
        
        # Should return 200 with pending status
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "organization_id" in data, "Response should contain organization_id"
        assert data.get("status") == "pending", "Status should be 'pending'"
        assert "message" in data, "Response should contain message"
        
        print(f"✅ Hospital registration successful: {data.get('organization_id')}")
        return data.get("organization_id")
    
    def test_register_hospital_duplicate_email(self):
        """Test registration with duplicate email fails"""
        unique_id = str(uuid.uuid4())[:8]
        registration_data = {
            "name": f"TEST_Hospital_Dup_{unique_id}",
            "organization_type": "hospital",
            "license_number": f"LIC-DUP-{unique_id}",
            "address_line1": "123 Test Street",
            "city": "Accra",
            "state": "Greater Accra",
            "zip_code": "GA-123",
            "country": "Ghana",
            "phone": "030-1234567",
            "email": f"dup_{unique_id}@hospital.gh",
            "admin_first_name": "Test",
            "admin_last_name": "Admin",
            "admin_email": f"dup_admin_{unique_id}@hospital.gh",
            "admin_phone": "024-1234567"
        }
        
        # First registration should succeed
        response1 = requests.post(f"{BASE_URL}/api/organizations/register", json=registration_data)
        assert response1.status_code == 200, f"First registration should succeed: {response1.text}"
        
        # Second registration with same email should fail
        response2 = requests.post(f"{BASE_URL}/api/organizations/register", json=registration_data)
        assert response2.status_code == 400, f"Duplicate registration should fail with 400: {response2.text}"
        
        print("✅ Duplicate email registration correctly rejected")
    
    def test_register_hospital_missing_required_fields(self):
        """Test registration with missing required fields fails"""
        incomplete_data = {
            "name": "Incomplete Hospital",
            # Missing required fields like license_number, address, etc.
        }
        
        response = requests.post(f"{BASE_URL}/api/organizations/register", json=incomplete_data)
        
        # Should return 422 (validation error)
        assert response.status_code == 422, f"Expected 422 for missing fields, got {response.status_code}"
        
        print("✅ Missing required fields correctly rejected")
    
    def test_register_hospital_invalid_email(self):
        """Test registration with invalid email format fails"""
        unique_id = str(uuid.uuid4())[:8]
        registration_data = {
            "name": f"TEST_Hospital_Invalid_{unique_id}",
            "organization_type": "hospital",
            "license_number": f"LIC-INV-{unique_id}",
            "address_line1": "123 Test Street",
            "city": "Accra",
            "state": "Greater Accra",
            "zip_code": "GA-123",
            "country": "Ghana",
            "phone": "030-1234567",
            "email": "invalid-email-format",  # Invalid email
            "admin_first_name": "Test",
            "admin_last_name": "Admin",
            "admin_email": "also-invalid",  # Invalid email
            "admin_phone": "024-1234567"
        }
        
        response = requests.post(f"{BASE_URL}/api/organizations/register", json=registration_data)
        
        # Should return 422 (validation error)
        assert response.status_code == 422, f"Expected 422 for invalid email, got {response.status_code}"
        
        print("✅ Invalid email format correctly rejected")


class TestSuperAdminAuthentication:
    """Test Super Admin authentication for approval workflow"""
    
    def test_super_admin_login_success(self):
        """Test Super Admin can login successfully"""
        login_data = {
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        
        # Note: May require OTP verification, so we check for either success or OTP required
        if response.status_code == 200:
            data = response.json()
            assert "token" in data, "Response should contain token"
            print(f"✅ Super Admin login successful")
            return data.get("token")
        elif response.status_code == 403 and "2FA_REQUIRED" in response.text:
            print("⚠️ Super Admin login requires 2FA - skipping token-based tests")
            pytest.skip("2FA required for Super Admin login")
        else:
            # Try init login flow
            init_response = requests.post(f"{BASE_URL}/api/auth/login/init", json=login_data)
            if init_response.status_code == 200:
                data = init_response.json()
                if data.get("otp_required"):
                    print("⚠️ Super Admin login requires OTP verification")
                    pytest.skip("OTP required for Super Admin login")
            
            pytest.fail(f"Super Admin login failed: {response.status_code} - {response.text}")
    
    def test_super_admin_login_invalid_credentials(self):
        """Test Super Admin login with invalid credentials fails"""
        login_data = {
            "email": SUPER_ADMIN_EMAIL,
            "password": "wrongpassword"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        
        assert response.status_code == 401, f"Expected 401 for invalid credentials, got {response.status_code}"
        
        print("✅ Invalid credentials correctly rejected")


class TestOrganizationListEndpoint:
    """Test organization listing endpoints (requires Super Admin auth)"""
    
    @pytest.fixture
    def super_admin_token(self):
        """Get Super Admin token for authenticated requests"""
        login_data = {
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        
        if response.status_code == 200:
            return response.json().get("token")
        elif response.status_code == 403:
            pytest.skip("2FA required for Super Admin login")
        else:
            # Try init login
            init_response = requests.post(f"{BASE_URL}/api/auth/login/init", json=login_data)
            if init_response.status_code == 200 and init_response.json().get("otp_required"):
                pytest.skip("OTP required for Super Admin login")
            pytest.skip(f"Could not authenticate Super Admin: {response.status_code}")
    
    def test_list_organizations_requires_auth(self):
        """Test that listing organizations requires authentication"""
        response = requests.get(f"{BASE_URL}/api/organizations/")
        
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        
        print("✅ Organization list correctly requires authentication")
    
    def test_list_organizations_with_auth(self, super_admin_token):
        """Test listing organizations with Super Admin auth"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/organizations/", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "organizations" in data, "Response should contain organizations list"
        assert isinstance(data["organizations"], list), "Organizations should be a list"
        
        print(f"✅ Listed {len(data['organizations'])} organizations")
    
    def test_list_pending_organizations(self, super_admin_token):
        """Test listing pending organizations"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/organizations/pending", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "organizations" in data, "Response should contain organizations list"
        assert "count" in data, "Response should contain count"
        
        print(f"✅ Found {data['count']} pending organizations")


class TestApprovalWorkflow:
    """Test the approval/rejection workflow for hospital registrations"""
    
    @pytest.fixture
    def super_admin_token(self):
        """Get Super Admin token for authenticated requests"""
        login_data = {
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        
        if response.status_code == 200:
            return response.json().get("token")
        elif response.status_code == 403:
            pytest.skip("2FA required for Super Admin login")
        else:
            init_response = requests.post(f"{BASE_URL}/api/auth/login/init", json=login_data)
            if init_response.status_code == 200 and init_response.json().get("otp_required"):
                pytest.skip("OTP required for Super Admin login")
            pytest.skip(f"Could not authenticate Super Admin: {response.status_code}")
    
    @pytest.fixture
    def registered_hospital(self):
        """Create a test hospital registration"""
        unique_id = str(uuid.uuid4())[:8]
        registration_data = {
            "name": f"TEST_Approval_Hospital_{unique_id}",
            "organization_type": "hospital",
            "license_number": f"LIC-APPR-{unique_id}",
            "address_line1": "456 Approval Street",
            "city": "Kumasi",
            "state": "Ashanti",
            "zip_code": "KS-456",
            "country": "Ghana",
            "phone": "032-1234567",
            "email": f"approval_{unique_id}@hospital.gh",
            "admin_first_name": "Approval",
            "admin_last_name": "Test",
            "admin_email": f"approval_admin_{unique_id}@hospital.gh",
            "admin_phone": "024-9876543"
        }
        
        response = requests.post(f"{BASE_URL}/api/organizations/register", json=registration_data)
        assert response.status_code == 200, f"Failed to create test hospital: {response.text}"
        
        return response.json().get("organization_id")
    
    def test_approve_organization(self, super_admin_token, registered_hospital):
        """Test approving a pending organization"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        approval_data = {
            "notes": "Approved for testing",
            "subscription_plan": "standard",
            "max_users": 50,
            "max_patients": 10000
        }
        
        response = requests.post(
            f"{BASE_URL}/api/organizations/{registered_hospital}/approve",
            json=approval_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        assert "admin_email" in data, "Response should contain admin_email"
        assert "temp_password" in data, "Response should contain temp_password"
        
        print(f"✅ Organization approved: {registered_hospital}")
        print(f"   Admin email: {data.get('admin_email')}")
    
    def test_reject_organization(self, super_admin_token):
        """Test rejecting a pending organization"""
        # First create a hospital to reject
        unique_id = str(uuid.uuid4())[:8]
        registration_data = {
            "name": f"TEST_Reject_Hospital_{unique_id}",
            "organization_type": "hospital",
            "license_number": f"LIC-REJ-{unique_id}",
            "address_line1": "789 Reject Street",
            "city": "Tamale",
            "state": "Northern",
            "zip_code": "TM-789",
            "country": "Ghana",
            "phone": "037-1234567",
            "email": f"reject_{unique_id}@hospital.gh",
            "admin_first_name": "Reject",
            "admin_last_name": "Test",
            "admin_email": f"reject_admin_{unique_id}@hospital.gh",
            "admin_phone": "024-1111111"
        }
        
        reg_response = requests.post(f"{BASE_URL}/api/organizations/register", json=registration_data)
        assert reg_response.status_code == 200, f"Failed to create test hospital: {reg_response.text}"
        
        org_id = reg_response.json().get("organization_id")
        
        # Now reject it
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        rejection_data = {
            "reason": "Invalid license number - test rejection"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/organizations/{org_id}/reject",
            json=rejection_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        assert "reason" in data, "Response should contain reason"
        
        print(f"✅ Organization rejected: {org_id}")
    
    def test_approve_requires_auth(self, registered_hospital):
        """Test that approval requires authentication"""
        approval_data = {"notes": "Test"}
        
        response = requests.post(
            f"{BASE_URL}/api/organizations/{registered_hospital}/approve",
            json=approval_data
        )
        
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        
        print("✅ Approval correctly requires authentication")
    
    def test_approve_nonexistent_organization(self, super_admin_token):
        """Test approving a non-existent organization fails"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        approval_data = {"notes": "Test"}
        
        response = requests.post(
            f"{BASE_URL}/api/organizations/nonexistent-id-12345/approve",
            json=approval_data,
            headers=headers
        )
        
        assert response.status_code == 404, f"Expected 404 for non-existent org, got {response.status_code}"
        
        print("✅ Non-existent organization correctly returns 404")


class TestOrganizationTypes:
    """Test different organization types can be registered"""
    
    def test_register_clinic(self):
        """Test registering a clinic"""
        unique_id = str(uuid.uuid4())[:8]
        registration_data = {
            "name": f"TEST_Clinic_{unique_id}",
            "organization_type": "clinic",
            "license_number": f"LIC-CLI-{unique_id}",
            "address_line1": "100 Clinic Road",
            "city": "Cape Coast",
            "state": "Central",
            "zip_code": "CC-100",
            "country": "Ghana",
            "phone": "033-1234567",
            "email": f"clinic_{unique_id}@clinic.gh",
            "admin_first_name": "Clinic",
            "admin_last_name": "Admin",
            "admin_email": f"clinic_admin_{unique_id}@clinic.gh",
            "admin_phone": "024-2222222"
        }
        
        response = requests.post(f"{BASE_URL}/api/organizations/register", json=registration_data)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        print("✅ Clinic registration successful")
    
    def test_register_medical_center(self):
        """Test registering a medical center"""
        unique_id = str(uuid.uuid4())[:8]
        registration_data = {
            "name": f"TEST_Medical_Center_{unique_id}",
            "organization_type": "medical_center",
            "license_number": f"LIC-MC-{unique_id}",
            "address_line1": "200 Medical Center Ave",
            "city": "Takoradi",
            "state": "Western",
            "zip_code": "TK-200",
            "country": "Ghana",
            "phone": "031-1234567",
            "email": f"medcenter_{unique_id}@medcenter.gh",
            "admin_first_name": "Medical",
            "admin_last_name": "Admin",
            "admin_email": f"medcenter_admin_{unique_id}@medcenter.gh",
            "admin_phone": "024-3333333"
        }
        
        response = requests.post(f"{BASE_URL}/api/organizations/register", json=registration_data)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        print("✅ Medical Center registration successful")


class TestEndToEndRegistrationFlow:
    """Test the complete registration to approval flow"""
    
    @pytest.fixture
    def super_admin_token(self):
        """Get Super Admin token for authenticated requests"""
        login_data = {
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        
        if response.status_code == 200:
            return response.json().get("token")
        elif response.status_code == 403:
            pytest.skip("2FA required for Super Admin login")
        else:
            init_response = requests.post(f"{BASE_URL}/api/auth/login/init", json=login_data)
            if init_response.status_code == 200 and init_response.json().get("otp_required"):
                pytest.skip("OTP required for Super Admin login")
            pytest.skip(f"Could not authenticate Super Admin: {response.status_code}")
    
    def test_full_registration_approval_flow(self, super_admin_token):
        """Test complete flow: Register -> List Pending -> Approve -> Verify Active"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        # Step 1: Register a new hospital
        unique_id = str(uuid.uuid4())[:8]
        registration_data = {
            "name": f"TEST_E2E_Hospital_{unique_id}",
            "organization_type": "hospital",
            "license_number": f"LIC-E2E-{unique_id}",
            "address_line1": "999 E2E Test Street",
            "city": "Accra",
            "state": "Greater Accra",
            "zip_code": "GA-999",
            "country": "Ghana",
            "phone": "030-9999999",
            "email": f"e2e_{unique_id}@hospital.gh",
            "admin_first_name": "E2E",
            "admin_last_name": "Test",
            "admin_email": f"e2e_admin_{unique_id}@hospital.gh",
            "admin_phone": "024-9999999"
        }
        
        reg_response = requests.post(f"{BASE_URL}/api/organizations/register", json=registration_data)
        assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"
        
        org_id = reg_response.json().get("organization_id")
        print(f"Step 1: ✅ Hospital registered with ID: {org_id}")
        
        # Step 2: Verify it appears in pending list
        pending_response = requests.get(f"{BASE_URL}/api/organizations/pending", headers=headers)
        assert pending_response.status_code == 200, f"Failed to get pending list: {pending_response.text}"
        
        pending_orgs = pending_response.json().get("organizations", [])
        org_ids = [org.get("id") for org in pending_orgs]
        assert org_id in org_ids, f"Registered org {org_id} not found in pending list"
        print(f"Step 2: ✅ Hospital found in pending list")
        
        # Step 3: Approve the organization
        approval_data = {
            "notes": "E2E test approval",
            "subscription_plan": "standard",
            "max_users": 100
        }
        
        approve_response = requests.post(
            f"{BASE_URL}/api/organizations/{org_id}/approve",
            json=approval_data,
            headers=headers
        )
        assert approve_response.status_code == 200, f"Approval failed: {approve_response.text}"
        
        approval_result = approve_response.json()
        admin_email = approval_result.get("admin_email")
        temp_password = approval_result.get("temp_password")
        print(f"Step 3: ✅ Hospital approved")
        print(f"   Admin credentials: {admin_email} / {temp_password}")
        
        # Step 4: Verify it's no longer in pending list
        pending_response2 = requests.get(f"{BASE_URL}/api/organizations/pending", headers=headers)
        pending_orgs2 = pending_response2.json().get("organizations", [])
        org_ids2 = [org.get("id") for org in pending_orgs2]
        assert org_id not in org_ids2, f"Approved org {org_id} should not be in pending list"
        print(f"Step 4: ✅ Hospital no longer in pending list")
        
        # Step 5: Verify it appears in active organizations
        all_orgs_response = requests.get(f"{BASE_URL}/api/organizations/?status=active", headers=headers)
        assert all_orgs_response.status_code == 200, f"Failed to get active orgs: {all_orgs_response.text}"
        
        all_orgs = all_orgs_response.json().get("organizations", [])
        active_org = next((org for org in all_orgs if org.get("id") == org_id), None)
        assert active_org is not None, f"Approved org {org_id} not found in active list"
        assert active_org.get("status") == "active", f"Org status should be 'active', got {active_org.get('status')}"
        print(f"Step 5: ✅ Hospital found in active organizations with status 'active'")
        
        print("\n🎉 E2E Registration Flow Test PASSED!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
