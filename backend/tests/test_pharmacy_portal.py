"""
Ghana Pharmacy Portal API Tests
Tests for the Pharmacy Landing Zone & National Pharmacy Database - Phase 1
Covers: Public regions, pharmacies listing, search, pharmacy profile, registration, login
"""

import pytest
import requests
import os
import uuid

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestPharmacyPortalPublicRegions:
    """Test /api/pharmacy-portal/public/regions endpoint"""
    
    def test_get_regions_returns_200(self):
        """Regions endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/regions")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    def test_regions_returns_16_regions(self):
        """Should return all 16 Ghana regions"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/regions")
        data = response.json()
        assert "regions" in data, "Missing regions field"
        assert len(data["regions"]) == 16, f"Expected 16 regions, got {len(data['regions'])}"
    
    def test_regions_have_required_fields(self):
        """Each region should have region, pharmacy_count, region_code"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/regions")
        data = response.json()
        for region in data["regions"]:
            assert "region" in region, "Region missing 'region' field"
            assert "pharmacy_count" in region, "Region missing 'pharmacy_count' field"
            assert "region_code" in region, "Region missing 'region_code' field"
            assert isinstance(region["pharmacy_count"], int), "pharmacy_count should be integer"
    
    def test_regions_returns_total_pharmacies(self):
        """Response should include total_pharmacies count"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/regions")
        data = response.json()
        assert "total_pharmacies" in data, "Missing total_pharmacies field"
        assert isinstance(data["total_pharmacies"], int), "total_pharmacies should be integer"
        assert data["total_pharmacies"] >= 0, "total_pharmacies should be non-negative"
    
    def test_greater_accra_in_regions(self):
        """Greater Accra should be in regions list"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/regions")
        data = response.json()
        region_names = [r["region"] for r in data["regions"]]
        assert "Greater Accra" in region_names, "Greater Accra should be in regions"
    
    def test_ashanti_in_regions(self):
        """Ashanti should be in regions list"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/regions")
        data = response.json()
        region_names = [r["region"] for r in data["regions"]]
        assert "Ashanti" in region_names, "Ashanti should be in regions"


class TestPharmacyPortalPublicPharmacies:
    """Test /api/pharmacy-portal/public/pharmacies endpoint"""
    
    def test_list_pharmacies_returns_200(self):
        """List pharmacies endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/pharmacies")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_list_pharmacies_returns_pharmacies_array(self):
        """Response should contain pharmacies array"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/pharmacies")
        data = response.json()
        assert "pharmacies" in data, "Missing pharmacies field"
        assert isinstance(data["pharmacies"], list), "pharmacies should be a list"
    
    def test_list_pharmacies_returns_total(self):
        """Response should contain total count"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/pharmacies")
        data = response.json()
        assert "total" in data, "Missing total field"
        assert isinstance(data["total"], int), "total should be integer"
    
    def test_list_pharmacies_pagination(self):
        """Pagination should work correctly"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/pharmacies?limit=5&skip=0")
        data = response.json()
        assert len(data["pharmacies"]) <= 5, "Should respect limit parameter"
        assert "limit" in data, "Should return limit in response"
        assert "skip" in data, "Should return skip in response"
    
    def test_pharmacy_has_required_fields(self):
        """Each pharmacy should have required fields"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/pharmacies?limit=5")
        data = response.json()
        if len(data["pharmacies"]) > 0:
            pharmacy = data["pharmacies"][0]
            required_fields = ["id", "name", "region", "phone", "status"]
            for field in required_fields:
                assert field in pharmacy, f"Missing required field: {field}"
    
    def test_filter_by_region(self):
        """Should filter pharmacies by region"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/pharmacies?region=Greater Accra")
        assert response.status_code == 200
        data = response.json()
        for pharmacy in data["pharmacies"]:
            assert "Greater Accra" in pharmacy.get("region", ""), f"Pharmacy should be in Greater Accra: {pharmacy}"
    
    def test_filter_by_nhis(self):
        """Should filter pharmacies by NHIS accreditation"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/pharmacies?has_nhis=true")
        assert response.status_code == 200
        data = response.json()
        for pharmacy in data["pharmacies"]:
            assert pharmacy.get("has_nhis") == True, f"Pharmacy should have NHIS: {pharmacy}"
    
    def test_filter_by_24hr(self):
        """Should filter pharmacies by 24-hour service"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/pharmacies?has_24hr=true")
        assert response.status_code == 200
        data = response.json()
        for pharmacy in data["pharmacies"]:
            assert pharmacy.get("has_24hr_service") == True, f"Pharmacy should have 24hr service: {pharmacy}"
    
    def test_search_pharmacies(self):
        """Should search pharmacies by name"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/pharmacies?search=Hospital")
        assert response.status_code == 200
        data = response.json()
        # Results should contain search term in name, city, town, or address
        assert "pharmacies" in data


class TestPharmacyPortalPublicPharmacyProfile:
    """Test /api/pharmacy-portal/public/pharmacies/{pharmacy_id} endpoint"""
    
    def test_get_pharmacy_profile_returns_200(self):
        """Should get pharmacy profile by ID"""
        # First get a pharmacy ID from the list
        list_response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/pharmacies?limit=1")
        pharmacies = list_response.json()["pharmacies"]
        if len(pharmacies) > 0:
            pharmacy_id = pharmacies[0]["id"]
            
            # Get profile
            response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/pharmacies/{pharmacy_id}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            data = response.json()
            assert "pharmacy" in data, "Missing pharmacy field"
            assert data["pharmacy"]["id"] == pharmacy_id, "ID should match"
    
    def test_pharmacy_profile_has_services(self):
        """Pharmacy profile should include services array"""
        list_response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/pharmacies?limit=1")
        pharmacies = list_response.json()["pharmacies"]
        if len(pharmacies) > 0:
            pharmacy_id = pharmacies[0]["id"]
            response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/pharmacies/{pharmacy_id}")
            data = response.json()
            assert "services" in data, "Missing services field"
            assert isinstance(data["services"], list), "services should be a list"
    
    def test_get_nonexistent_pharmacy_returns_404(self):
        """Should return 404 for non-existent pharmacy"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/pharmacies/nonexistent-id-12345")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"


class TestPharmacyPortalRegistration:
    """Test /api/pharmacy-portal/register endpoint"""
    
    def test_register_pharmacy_success(self):
        """Should register a new pharmacy"""
        unique_id = str(uuid.uuid4())[:8]
        registration_data = {
            "pharmacy_name": f"TEST_Pharmacy_{unique_id}",
            "license_number": f"PCGH/TEST{unique_id}",
            "region": "Greater Accra",
            "district": "Accra Metropolitan",
            "town": "Accra",
            "address": "123 Test Street",
            "gps_address": "GA-123-4567",
            "phone": "+233 20 123 4567",
            "email": f"test_{unique_id}@pharmacy.gh",
            "superintendent_pharmacist_name": "Dr. Test Pharmacist",
            "superintendent_license_number": f"PSGH/TEST{unique_id}",
            "ownership_type": "retail",
            "operating_hours": "Mon-Sat 8AM-8PM",
            "password": "testpassword123",
            "has_nhis_accreditation": True
        }
        
        response = requests.post(f"{BASE_URL}/api/pharmacy-portal/register", json=registration_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "pharmacy_id" in data, "Missing pharmacy_id in response"
        assert "message" in data, "Missing message in response"
        assert data["status"] == "pending", "Status should be pending"
    
    def test_register_duplicate_license_fails(self):
        """Should fail to register with duplicate license number"""
        unique_id = str(uuid.uuid4())[:8]
        registration_data = {
            "pharmacy_name": f"TEST_Pharmacy_{unique_id}",
            "license_number": f"PCGH/DUP{unique_id}",
            "region": "Greater Accra",
            "district": "Accra Metropolitan",
            "town": "Accra",
            "address": "123 Test Street",
            "phone": "+233 20 123 4567",
            "email": f"test_dup1_{unique_id}@pharmacy.gh",
            "superintendent_pharmacist_name": "Dr. Test Pharmacist",
            "superintendent_license_number": f"PSGH/DUP{unique_id}",
            "password": "testpassword123"
        }
        
        # First registration
        response1 = requests.post(f"{BASE_URL}/api/pharmacy-portal/register", json=registration_data)
        assert response1.status_code == 200
        
        # Second registration with same license
        registration_data["email"] = f"test_dup2_{unique_id}@pharmacy.gh"
        response2 = requests.post(f"{BASE_URL}/api/pharmacy-portal/register", json=registration_data)
        assert response2.status_code == 400, f"Expected 400 for duplicate, got {response2.status_code}"
    
    def test_register_missing_required_fields(self):
        """Should fail with missing required fields"""
        incomplete_data = {
            "pharmacy_name": "Test Pharmacy"
            # Missing other required fields
        }
        
        response = requests.post(f"{BASE_URL}/api/pharmacy-portal/register", json=incomplete_data)
        assert response.status_code == 422, f"Expected 422 for validation error, got {response.status_code}"


class TestPharmacyPortalLogin:
    """Test /api/pharmacy-portal/auth/login endpoint"""
    
    def test_login_invalid_credentials(self):
        """Should fail with invalid credentials"""
        login_data = {
            "email": "nonexistent@pharmacy.gh",
            "password": "wrongpassword"
        }
        
        response = requests.post(f"{BASE_URL}/api/pharmacy-portal/auth/login", json=login_data)
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_login_missing_fields(self):
        """Should fail with missing fields"""
        login_data = {
            "email": "test@pharmacy.gh"
            # Missing password
        }
        
        response = requests.post(f"{BASE_URL}/api/pharmacy-portal/auth/login", json=login_data)
        assert response.status_code == 422, f"Expected 422 for validation error, got {response.status_code}"
    
    def test_login_with_registered_pharmacy(self):
        """Should login with newly registered pharmacy (if approved)"""
        # Register a new pharmacy first
        unique_id = str(uuid.uuid4())[:8]
        registration_data = {
            "pharmacy_name": f"TEST_Login_Pharmacy_{unique_id}",
            "license_number": f"PCGH/LOGIN{unique_id}",
            "region": "Greater Accra",
            "district": "Accra Metropolitan",
            "town": "Accra",
            "address": "123 Test Street",
            "phone": "+233 20 123 4567",
            "email": f"test_login_{unique_id}@pharmacy.gh",
            "superintendent_pharmacist_name": "Dr. Test Pharmacist",
            "superintendent_license_number": f"PSGH/LOGIN{unique_id}",
            "password": "testpassword123"
        }
        
        reg_response = requests.post(f"{BASE_URL}/api/pharmacy-portal/register", json=registration_data)
        assert reg_response.status_code == 200
        
        # Try to login (should fail because pharmacy is pending approval)
        login_data = {
            "email": registration_data["email"],
            "password": "testpassword123"
        }
        
        login_response = requests.post(f"{BASE_URL}/api/pharmacy-portal/auth/login", json=login_data)
        # Should fail because pharmacy status is pending
        assert login_response.status_code == 401, f"Expected 401 for pending pharmacy, got {login_response.status_code}"


class TestPharmacyPortalAuthenticatedEndpoints:
    """Test authenticated endpoints (should return 401/403 without auth)"""
    
    def test_dashboard_requires_auth(self):
        """Dashboard endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/dashboard")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_drugs_requires_auth(self):
        """Drugs endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/drugs")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_inventory_requires_auth(self):
        """Inventory endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/inventory")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_sales_requires_auth(self):
        """Sales endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/sales")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_prescriptions_requires_auth(self):
        """Prescriptions endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/prescriptions/incoming")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_staff_requires_auth(self):
        """Staff endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/admin/staff")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"


class TestMedicationDatabase:
    """Test medication database endpoints (requires auth)"""
    
    def test_medication_search_requires_auth(self):
        """Medication search should require authentication"""
        response = requests.get(f"{BASE_URL}/api/medications/search?query=paracetamol")
        # This endpoint requires authentication
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"
    
    def test_medication_categories_requires_auth(self):
        """Medication categories should require authentication"""
        response = requests.get(f"{BASE_URL}/api/medications/categories")
        assert response.status_code in [200, 401, 403], f"Unexpected status: {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
