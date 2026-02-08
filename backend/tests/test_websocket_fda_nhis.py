"""
Test WebSocket Notifications, FDA Module, and NHIS Module
Tests for real-time prescription notifications and Ghana regulatory integrations
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://healthfusion-gh.preview.emergentagent.com').rstrip('/')


class TestWebSocketStats:
    """WebSocket notification system stats endpoint tests"""
    
    def test_websocket_stats_endpoint_exists(self):
        """Test /api/pharmacy-ws/stats returns connection statistics"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-ws/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_connections" in data
        assert "pharmacies_connected" in data
        assert "pharmacy_ids" in data
        assert isinstance(data["total_connections"], int)
        assert isinstance(data["pharmacies_connected"], int)
        assert isinstance(data["pharmacy_ids"], list)
    
    def test_websocket_pharmacy_connected_check(self):
        """Test /api/pharmacy-ws/pharmacy/{id}/connected endpoint"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-ws/pharmacy/test-pharmacy-id/connected")
        assert response.status_code == 200
        
        data = response.json()
        assert "pharmacy_id" in data
        assert "connected" in data
        assert data["pharmacy_id"] == "test-pharmacy-id"
        assert isinstance(data["connected"], bool)
    
    def test_websocket_pharmacy_connected_with_real_id(self):
        """Test pharmacy connected check with real pharmacy ID"""
        # Use the test pharmacy ID from login
        pharmacy_id = "1fdc5060-4c29-4a61-a112-9a5078e24a0e"
        response = requests.get(f"{BASE_URL}/api/pharmacy-ws/pharmacy/{pharmacy_id}/connected")
        assert response.status_code == 200
        
        data = response.json()
        assert data["pharmacy_id"] == pharmacy_id
        # Should be false since no WebSocket connection is active
        assert data["connected"] == False


class TestFDAModule:
    """Ghana FDA integration module tests"""
    
    def test_fda_registered_drugs_endpoint(self):
        """Test /api/fda/drugs returns registered drugs list"""
        response = requests.get(f"{BASE_URL}/api/fda/drugs?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "drugs" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert len(data["drugs"]) <= 10
        assert data["total"] > 0
    
    def test_fda_drug_has_required_fields(self):
        """Test FDA drug entries have all required fields"""
        response = requests.get(f"{BASE_URL}/api/fda/drugs?limit=1")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["drugs"]) > 0
        
        drug = data["drugs"][0]
        required_fields = [
            "registration_number", "trade_name", "generic_name",
            "manufacturer", "country_of_origin", "dosage_form",
            "strength", "pack_size", "schedule", "category",
            "status", "registration_date", "expiry_date",
            "active_ingredients", "indications", "contraindications",
            "side_effects", "storage_conditions"
        ]
        for field in required_fields:
            assert field in drug, f"Missing field: {field}"
    
    def test_fda_verify_drug_by_registration_number(self):
        """Test POST /api/fda/verify with registration number"""
        response = requests.post(
            f"{BASE_URL}/api/fda/verify",
            json={"registration_number": "FDA/dD-22-3456"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "verified" in data
        assert "registration_number" in data
        assert "trade_name" in data
        assert "manufacturer" in data
        assert "status" in data
        assert "message" in data
        
        # Coartem should be verified and active
        assert data["verified"] == True
        assert data["trade_name"] == "Coartem"
        assert data["status"] == "active"
    
    def test_fda_verify_drug_not_found(self):
        """Test FDA verify returns not found for invalid registration"""
        response = requests.post(
            f"{BASE_URL}/api/fda/verify",
            json={"registration_number": "INVALID-REG-NUMBER"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["verified"] == False
        assert data["status"] == "not_found"
    
    def test_fda_verify_by_trade_name(self):
        """Test FDA verify by trade name"""
        response = requests.post(
            f"{BASE_URL}/api/fda/verify",
            json={"trade_name": "Panadol"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "verified" in data
        assert "trade_name" in data
    
    def test_fda_drug_search(self):
        """Test /api/fda/drugs/search endpoint"""
        response = requests.get(f"{BASE_URL}/api/fda/drugs/search?q=amox")
        assert response.status_code == 200
        
        data = response.json()
        assert "drugs" in data
        assert "total" in data
        assert "query" in data
        assert data["query"] == "amox"
    
    def test_fda_get_drug_by_registration_number(self):
        """Test /api/fda/drugs/{registration_number} endpoint"""
        # URL encode the registration number
        reg_number = "FDA%2FdD-22-3456"
        response = requests.get(f"{BASE_URL}/api/fda/drugs/{reg_number}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["registration_number"] == "FDA/dD-22-3456"
        assert data["trade_name"] == "Coartem"
    
    def test_fda_schedules_endpoint(self):
        """Test /api/fda/schedules returns drug schedule types"""
        response = requests.get(f"{BASE_URL}/api/fda/schedules")
        assert response.status_code == 200
        
        data = response.json()
        assert "schedules" in data
        assert len(data["schedules"]) >= 4  # OTC, POM, CD, POM_A
    
    def test_fda_categories_endpoint(self):
        """Test /api/fda/categories returns drug categories"""
        response = requests.get(f"{BASE_URL}/api/fda/categories")
        assert response.status_code == 200
        
        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) >= 5
    
    def test_fda_stats_endpoint(self):
        """Test /api/fda/stats returns statistics"""
        response = requests.get(f"{BASE_URL}/api/fda/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_registered" in data
        assert "by_schedule" in data
        assert "by_category" in data
        assert "by_status" in data
        assert "controlled_drugs" in data
        assert "active_registrations" in data
    
    def test_fda_manufacturers_endpoint(self):
        """Test /api/fda/manufacturers returns manufacturer list"""
        response = requests.get(f"{BASE_URL}/api/fda/manufacturers")
        assert response.status_code == 200
        
        data = response.json()
        assert "manufacturers" in data
        assert len(data["manufacturers"]) > 0
    
    def test_fda_alerts_endpoint(self):
        """Test /api/fda/alerts returns safety alerts"""
        response = requests.get(f"{BASE_URL}/api/fda/alerts")
        assert response.status_code == 200
        
        data = response.json()
        assert "alerts" in data
        assert "last_updated" in data


class TestNHISModule:
    """NHIS (National Health Insurance Scheme) module tests"""
    
    @pytest.fixture
    def physician_token(self):
        """Get physician authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "physician@yacco.health", "password": "test123"}
        )
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Physician login failed")
    
    def test_nhis_tariff_endpoint(self):
        """Test /api/nhis/tariff returns drug tariff list"""
        response = requests.get(f"{BASE_URL}/api/nhis/tariff")
        assert response.status_code == 200
        
        data = response.json()
        assert "drugs" in data
        assert "total" in data
        assert len(data["drugs"]) > 0
    
    def test_nhis_tariff_drug_has_required_fields(self):
        """Test NHIS tariff entries have required fields"""
        response = requests.get(f"{BASE_URL}/api/nhis/tariff")
        assert response.status_code == 200
        
        data = response.json()
        drug = data["drugs"][0]
        
        assert "code" in drug
        assert "name" in drug
        assert "nhis_price" in drug
        assert "covered" in drug
    
    def test_nhis_tariff_covered_only_filter(self):
        """Test NHIS tariff covered_only filter"""
        response = requests.get(f"{BASE_URL}/api/nhis/tariff?covered_only=true")
        assert response.status_code == 200
        
        data = response.json()
        # All returned drugs should be covered
        for drug in data["drugs"]:
            assert drug["covered"] == True
    
    def test_nhis_tariff_search(self):
        """Test NHIS tariff search functionality"""
        response = requests.get(f"{BASE_URL}/api/nhis/tariff?search=paracet")
        assert response.status_code == 200
        
        data = response.json()
        assert "drugs" in data
    
    def test_nhis_verify_member_requires_auth(self):
        """Test NHIS verify-member requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/nhis/verify-member",
            json={"membership_id": "NHIS-2024-001234"}
        )
        assert response.status_code == 403  # Not authenticated
    
    def test_nhis_verify_member_success(self, physician_token):
        """Test NHIS verify-member with valid membership ID"""
        response = requests.post(
            f"{BASE_URL}/api/nhis/verify-member",
            json={"membership_id": "NHIS-2024-001234"},
            headers={"Authorization": f"Bearer {physician_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "membership_id" in data
        assert "full_name" in data
        assert "status" in data
        assert "verified" in data
        assert "message" in data
        
        # This is a valid test member
        assert data["verified"] == True
        assert data["full_name"] == "Kofi Mensah Asante"
        assert data["status"] == "active"
    
    def test_nhis_verify_member_not_found(self, physician_token):
        """Test NHIS verify-member with invalid membership ID"""
        response = requests.post(
            f"{BASE_URL}/api/nhis/verify-member",
            json={"membership_id": "INVALID-NHIS-ID"},
            headers={"Authorization": f"Bearer {physician_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["verified"] == False
        assert data["status"] == "not_found"
    
    def test_nhis_verify_expired_member(self, physician_token):
        """Test NHIS verify-member with expired membership"""
        response = requests.post(
            f"{BASE_URL}/api/nhis/verify-member",
            json={"membership_id": "NHIS-2022-009012"},
            headers={"Authorization": f"Bearer {physician_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["verified"] == False
        assert data["status"] == "expired"
    
    def test_nhis_claims_endpoint(self, physician_token):
        """Test /api/nhis/claims returns claims list"""
        response = requests.get(
            f"{BASE_URL}/api/nhis/claims",
            headers={"Authorization": f"Bearer {physician_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "claims" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data


class TestPrescriptionRouting:
    """Prescription routing to network pharmacy tests"""
    
    @pytest.fixture
    def physician_token(self):
        """Get physician authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "physician@yacco.health", "password": "test123"}
        )
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Physician login failed")
    
    def test_send_to_network_pharmacy_requires_auth(self):
        """Test send-to-network-pharmacy requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/prescriptions/send-to-network-pharmacy",
            json={
                "prescription_id": "test-prescription-id",
                "pharmacy_id": "test-pharmacy-id"
            }
        )
        assert response.status_code == 403
    
    def test_send_to_network_pharmacy_validates_prescription(self, physician_token):
        """Test send-to-network-pharmacy validates prescription exists"""
        response = requests.post(
            f"{BASE_URL}/api/prescriptions/send-to-network-pharmacy",
            json={
                "prescription_id": "non-existent-prescription",
                "pharmacy_id": "1fdc5060-4c29-4a61-a112-9a5078e24a0e"
            },
            headers={"Authorization": f"Bearer {physician_token}"}
        )
        # Should return 404 for non-existent prescription
        assert response.status_code == 404
        assert "Prescription not found" in response.json().get("detail", "")
    
    def test_send_to_network_pharmacy_validates_pharmacy(self, physician_token):
        """Test send-to-network-pharmacy validates pharmacy exists"""
        # First create a test prescription
        # For now, just test that the endpoint validates pharmacy
        response = requests.post(
            f"{BASE_URL}/api/prescriptions/send-to-network-pharmacy",
            json={
                "prescription_id": "test-prescription-id",
                "pharmacy_id": "non-existent-pharmacy-id"
            },
            headers={"Authorization": f"Bearer {physician_token}"}
        )
        # Should return error (either 404 for prescription or pharmacy)
        assert response.status_code in [404, 400]


class TestPharmacyDashboardAuth:
    """Pharmacy dashboard authentication tests"""
    
    def test_pharmacy_login_success(self):
        """Test pharmacy portal login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/pharmacy-portal/auth/login",
            json={"email": "test@testpharm.gh", "password": "testpass123"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert "pharmacy" in data
        
        # Verify user data
        assert data["user"]["email"] == "test@testpharm.gh"
        assert "pharmacy_id" in data["user"]
        
        # Verify pharmacy data
        assert data["pharmacy"]["name"] == "Test Pharmacy Accra"
        assert data["pharmacy"]["status"] == "approved"
    
    def test_pharmacy_login_invalid_credentials(self):
        """Test pharmacy portal login with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/pharmacy-portal/auth/login",
            json={"email": "invalid@test.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
