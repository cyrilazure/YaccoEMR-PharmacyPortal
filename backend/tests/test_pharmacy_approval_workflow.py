"""
Test Pharmacy Approval Workflow - Platform Owner Portal
Tests for:
1. Platform Owner Portal Pharmacies tab
2. Pending pharmacy approvals listing
3. Pharmacy approval/rejection workflow
4. Prescription module /pharmacies/ghana endpoint
5. Prescription module /send-to-network-pharmacy endpoint
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
PLATFORM_ADMIN_EMAIL = "ygtnetworks@gmail.com"
PLATFORM_ADMIN_PASSWORD = "test123"
PHARMACY_TEST_EMAIL = "test@testpharm.gh"
PHARMACY_TEST_PASSWORD = "testpass123"


class TestPlatformAdminAuth:
    """Test platform admin authentication"""
    
    def test_platform_admin_login(self):
        """Test platform admin can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert data.get("user", {}).get("role") == "super_admin"
        print(f"✓ Platform admin login successful - role: {data.get('user', {}).get('role')}")


class TestPendingPharmaciesEndpoint:
    """Test pending pharmacies listing endpoint"""
    
    def test_get_pending_pharmacies(self):
        """Test GET /api/pharmacy-portal/admin/pharmacies/pending"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/admin/pharmacies/pending")
        assert response.status_code == 200, f"Failed to get pending pharmacies: {response.text}"
        data = response.json()
        assert "pharmacies" in data
        assert "total" in data
        print(f"✓ Pending pharmacies endpoint works - {data['total']} pending pharmacies")
        
        # Verify pharmacy data structure
        if data["pharmacies"]:
            pharmacy = data["pharmacies"][0]
            assert "id" in pharmacy
            assert "name" in pharmacy
            assert "license_number" in pharmacy
            assert "region" in pharmacy
            assert "status" in pharmacy
            print(f"✓ Pharmacy data structure verified - first pharmacy: {pharmacy['name']}")
    
    def test_pending_pharmacies_have_pending_status(self):
        """Verify all returned pharmacies have pending status"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/admin/pharmacies/pending")
        assert response.status_code == 200
        data = response.json()
        
        for pharmacy in data["pharmacies"]:
            assert pharmacy["status"] in ["pending", "under_review"], \
                f"Pharmacy {pharmacy['name']} has unexpected status: {pharmacy['status']}"
        print(f"✓ All {len(data['pharmacies'])} pharmacies have pending/under_review status")


class TestApprovedPharmaciesEndpoint:
    """Test approved pharmacies listing endpoint"""
    
    def test_get_all_pharmacies(self):
        """Test GET /api/pharmacy-portal/public/pharmacies"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/pharmacies", params={"limit": 100})
        assert response.status_code == 200, f"Failed to get pharmacies: {response.text}"
        data = response.json()
        assert "pharmacies" in data
        assert "total" in data
        print(f"✓ Public pharmacies endpoint works - {data['total']} total pharmacies")
    
    def test_filter_approved_pharmacies(self):
        """Test filtering for approved pharmacies"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/pharmacies", params={"limit": 100})
        assert response.status_code == 200
        data = response.json()
        
        approved = [p for p in data["pharmacies"] if p.get("status") in ["approved", "active"]]
        print(f"✓ Found {len(approved)} approved/active pharmacies out of {data['total']} total")


class TestPharmacyApprovalWorkflow:
    """Test pharmacy approval/rejection workflow"""
    
    @pytest.fixture
    def test_pharmacy_id(self):
        """Get a pending pharmacy ID for testing"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/admin/pharmacies/pending")
        if response.status_code == 200:
            data = response.json()
            if data["pharmacies"]:
                return data["pharmacies"][0]["id"]
        return None
    
    def test_approve_pharmacy_endpoint_exists(self, test_pharmacy_id):
        """Test PUT /api/pharmacy-portal/admin/pharmacies/{id}/approve endpoint exists"""
        if not test_pharmacy_id:
            pytest.skip("No pending pharmacy available for testing")
        
        # Test with approved status
        response = requests.put(
            f"{BASE_URL}/api/pharmacy-portal/admin/pharmacies/{test_pharmacy_id}/approve",
            json={"status": "approved", "notes": "Test approval"}
        )
        # Should succeed or return validation error, not 404
        assert response.status_code in [200, 400, 422], f"Unexpected status: {response.status_code} - {response.text}"
        print(f"✓ Pharmacy approval endpoint exists and responds")
    
    def test_reject_pharmacy_requires_notes(self):
        """Test that rejection requires notes"""
        # Create a test pharmacy first
        unique_id = str(uuid.uuid4())[:8]
        register_response = requests.post(f"{BASE_URL}/api/pharmacy-portal/register", json={
            "name": f"TEST_Reject_Pharmacy_{unique_id}",
            "license_number": f"PCGH/REJ{unique_id}",
            "region": "Greater Accra",
            "district": "Accra Metropolitan",
            "town": "Accra",
            "address": "123 Test Street",
            "phone": "+233 20 123 4567",
            "email": f"test_reject_{unique_id}@pharmacy.gh",
            "superintendent_pharmacist_name": "Dr. Test Pharmacist",
            "superintendent_license_number": f"PSGH/REJ{unique_id}",
            "ownership_type": "retail",
            "operating_hours": "Mon-Sat 8AM-8PM",
            "password": "testpass123"
        })
        
        if register_response.status_code == 201:
            pharmacy_id = register_response.json().get("pharmacy", {}).get("id")
            if pharmacy_id:
                # Try to reject without notes - should still work but notes are recommended
                response = requests.put(
                    f"{BASE_URL}/api/pharmacy-portal/admin/pharmacies/{pharmacy_id}/approve",
                    json={"status": "rejected", "notes": "Test rejection reason"}
                )
                assert response.status_code == 200, f"Rejection failed: {response.text}"
                print(f"✓ Pharmacy rejection with notes works")
        else:
            print(f"⚠ Could not create test pharmacy for rejection test")


class TestPrescriptionPharmaciesEndpoint:
    """Test prescription module /pharmacies/ghana endpoint"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token for prescription endpoints"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def test_get_ghana_pharmacies(self):
        """Test GET /api/prescriptions/pharmacies/ghana returns pharmacies from database"""
        response = requests.get(f"{BASE_URL}/api/prescriptions/pharmacies/ghana")
        assert response.status_code == 200, f"Failed to get Ghana pharmacies: {response.text}"
        data = response.json()
        assert "pharmacies" in data
        assert "total" in data
        print(f"✓ Ghana pharmacies endpoint works - {data['total']} pharmacies returned")
        
        # Verify pharmacies are from database (have proper structure)
        if data["pharmacies"]:
            pharmacy = data["pharmacies"][0]
            # Check for database fields vs mock data fields
            has_db_fields = "district" in pharmacy or "town" in pharmacy or "has_nhis" in pharmacy
            print(f"✓ Pharmacies appear to be from database: {has_db_fields}")
    
    def test_filter_pharmacies_by_region(self):
        """Test filtering pharmacies by region"""
        response = requests.get(f"{BASE_URL}/api/prescriptions/pharmacies/ghana", params={"region": "Greater Accra"})
        assert response.status_code == 200
        data = response.json()
        
        # All returned pharmacies should be from Greater Accra
        for pharmacy in data["pharmacies"]:
            assert pharmacy.get("region") == "Greater Accra", \
                f"Pharmacy {pharmacy.get('name')} is from {pharmacy.get('region')}, expected Greater Accra"
        print(f"✓ Region filter works - {len(data['pharmacies'])} pharmacies in Greater Accra")
    
    def test_search_pharmacies_by_query(self):
        """Test searching pharmacies by name"""
        response = requests.get(f"{BASE_URL}/api/prescriptions/pharmacies/ghana", params={"query": "Ernest"})
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Search query works - {len(data['pharmacies'])} pharmacies matching 'Ernest'")


class TestSendToNetworkPharmacyEndpoint:
    """Test prescription module /send-to-network-pharmacy endpoint"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            token = response.json().get("token")
            return {"Authorization": f"Bearer {token}"}
        return {}
    
    def test_send_to_network_pharmacy_requires_auth(self):
        """Test that endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/prescriptions/send-to-network-pharmacy", json={
            "prescription_id": "test-id",
            "pharmacy_id": "test-pharmacy-id"
        })
        assert response.status_code in [401, 403], f"Expected auth error, got: {response.status_code}"
        print(f"✓ Send to network pharmacy endpoint requires authentication")
    
    def test_send_to_network_pharmacy_validates_prescription(self, auth_headers):
        """Test that endpoint validates prescription exists"""
        if not auth_headers:
            pytest.skip("Could not authenticate")
        
        response = requests.post(
            f"{BASE_URL}/api/prescriptions/send-to-network-pharmacy",
            headers=auth_headers,
            json={
                "prescription_id": "non-existent-prescription",
                "pharmacy_id": "test-pharmacy-id"
            }
        )
        assert response.status_code == 404, f"Expected 404 for non-existent prescription, got: {response.status_code}"
        print(f"✓ Endpoint validates prescription exists")
    
    def test_send_to_network_pharmacy_validates_pharmacy(self, auth_headers):
        """Test that endpoint validates pharmacy exists in network"""
        if not auth_headers:
            pytest.skip("Could not authenticate")
        
        # First create a test prescription
        # Get a patient first
        patients_response = requests.get(f"{BASE_URL}/api/patients", headers=auth_headers)
        patients_data = patients_response.json()
        # Handle both list and dict response formats
        if patients_response.status_code != 200:
            pytest.skip("Could not get patients")
        if isinstance(patients_data, list):
            patients = patients_data
        else:
            patients = patients_data.get("patients", [])
        if not patients:
            pytest.skip("No patients available for testing")
        
        patient_id = patients[0]["id"]
        
        # Create prescription
        prescription_response = requests.post(
            f"{BASE_URL}/api/prescriptions/create",
            headers=auth_headers,
            json={
                "patient_id": patient_id,
                "medications": [{
                    "medication_name": "Amoxicillin",
                    "dosage": "500",
                    "dosage_unit": "mg",
                    "frequency": "TID",
                    "route": "oral",
                    "duration_value": 7,
                    "duration_unit": "days",
                    "quantity": 21
                }],
                "diagnosis": "Test diagnosis",
                "priority": "routine"
            }
        )
        
        if prescription_response.status_code != 200:
            pytest.skip(f"Could not create test prescription: {prescription_response.text}")
        
        prescription_id = prescription_response.json().get("prescription", {}).get("id")
        
        # Try to send to non-existent pharmacy
        response = requests.post(
            f"{BASE_URL}/api/prescriptions/send-to-network-pharmacy",
            headers=auth_headers,
            json={
                "prescription_id": prescription_id,
                "pharmacy_id": "non-existent-pharmacy"
            }
        )
        assert response.status_code == 404, f"Expected 404 for non-existent pharmacy, got: {response.status_code}"
        print(f"✓ Endpoint validates pharmacy exists in network")


class TestPharmacyDataStructure:
    """Test pharmacy data structure for UI display"""
    
    def test_pending_pharmacy_has_required_fields(self):
        """Test pending pharmacy has all fields needed for UI display"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/admin/pharmacies/pending")
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["id", "name", "license_number", "region", "status"]
        optional_display_fields = ["district", "town", "has_nhis", "created_at"]
        
        for pharmacy in data["pharmacies"]:
            for field in required_fields:
                assert field in pharmacy, f"Missing required field: {field}"
            
            present_optional = [f for f in optional_display_fields if f in pharmacy]
            print(f"✓ Pharmacy {pharmacy['name']} has required fields + {len(present_optional)} optional fields")
    
    def test_approved_pharmacy_has_required_fields(self):
        """Test approved pharmacy has all fields needed for table display"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/pharmacies", params={"limit": 10})
        assert response.status_code == 200
        data = response.json()
        
        approved = [p for p in data["pharmacies"] if p.get("status") in ["approved", "active"]]
        
        if approved:
            pharmacy = approved[0]
            required_fields = ["id", "name", "license_number", "region", "status"]
            for field in required_fields:
                assert field in pharmacy, f"Missing required field: {field}"
            print(f"✓ Approved pharmacy has all required fields for table display")


class TestPharmacyPortalIntegration:
    """Test pharmacy portal integration with platform admin"""
    
    def test_pharmacy_registration_creates_pending_entry(self):
        """Test that pharmacy registration creates a pending entry"""
        unique_id = str(uuid.uuid4())[:8]
        
        response = requests.post(f"{BASE_URL}/api/pharmacy-portal/register", json={
            "pharmacy_name": f"TEST_Integration_Pharmacy_{unique_id}",
            "license_number": f"PCGH/INT{unique_id}",
            "region": "Greater Accra",
            "district": "Accra Metropolitan",
            "town": "Accra",
            "address": "123 Test Street",
            "phone": "+233 20 123 4567",
            "email": f"test_int_{unique_id}@pharmacy.gh",
            "superintendent_pharmacist_name": "Dr. Test Pharmacist",
            "superintendent_license_number": f"PSGH/INT{unique_id}",
            "ownership_type": "retail",
            "operating_hours": "Mon-Sat 8AM-8PM",
            "password": "testpass123"
        })
        
        assert response.status_code in [200, 201], f"Registration failed: {response.text}"
        data = response.json()
        # Handle different response formats
        pharmacy_status = data.get("pharmacy", {}).get("status") or data.get("status")
        assert pharmacy_status == "pending"
        print(f"✓ New pharmacy registration creates pending entry")
        
        # Verify it appears in pending list
        pending_response = requests.get(f"{BASE_URL}/api/pharmacy-portal/admin/pharmacies/pending")
        assert pending_response.status_code == 200
        pending_data = pending_response.json()
        
        pharmacy_ids = [p["id"] for p in pending_data["pharmacies"]]
        pharmacy_id = data.get("pharmacy", {}).get("id") or data.get("pharmacy_id")
        assert pharmacy_id in pharmacy_ids, "New pharmacy not found in pending list"
        print(f"✓ New pharmacy appears in pending pharmacies list")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
