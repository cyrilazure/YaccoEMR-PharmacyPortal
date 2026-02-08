"""
Pharmacy Portal Phase 2 API Tests
Tests for: Drug catalog, inventory management, e-prescription processing, medication dispensing
Global medication database with 200+ drugs
"""

import pytest
import requests
import os
import uuid

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@testpharm.gh"
TEST_PASSWORD = "testpass123"


class TestPharmacyLogin:
    """Test pharmacy login and authentication"""
    
    def test_login_success(self):
        """Should login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/pharmacy-portal/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "token" in data, "Missing token in response"
        assert "user" in data, "Missing user in response"
        assert data["user"]["email"] == TEST_EMAIL
        assert data["user"]["pharmacy_name"] == "Test Pharmacy Accra"
    
    def test_login_invalid_credentials(self):
        """Should fail with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/pharmacy-portal/auth/login", json={
            "email": "wrong@email.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(f"{BASE_URL}/api/pharmacy-portal/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code == 200:
        return response.json()["token"]
    pytest.skip("Authentication failed")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get auth headers for authenticated requests"""
    return {"Authorization": f"Bearer {auth_token}"}


class TestPharmacyDashboard:
    """Test pharmacy dashboard endpoint"""
    
    def test_dashboard_returns_stats(self, auth_headers):
        """Dashboard should return stats"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "today_sales_count" in data
        assert "today_revenue" in data
        assert "pending_prescriptions" in data
        assert "low_stock_count" in data
        assert "total_drugs" in data
        
        # Verify data types
        assert isinstance(data["today_sales_count"], int)
        assert isinstance(data["total_drugs"], int)
        assert data["total_drugs"] == 19, f"Expected 19 drugs, got {data['total_drugs']}"
    
    def test_dashboard_requires_auth(self):
        """Dashboard should require authentication"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/dashboard")
        assert response.status_code in [401, 403]


class TestDrugCatalog:
    """Test drug catalog endpoints"""
    
    def test_get_drugs_list(self, auth_headers):
        """Should return list of drugs"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/drugs", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "drugs" in data
        assert "total" in data
        assert isinstance(data["drugs"], list)
        assert data["total"] == 19, f"Expected 19 drugs, got {data['total']}"
    
    def test_drugs_have_required_fields(self, auth_headers):
        """Each drug should have required fields"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/drugs", headers=auth_headers)
        data = response.json()
        
        if len(data["drugs"]) > 0:
            drug = data["drugs"][0]
            required_fields = ["id", "generic_name", "brand_name", "strength", "dosage_form", "category", "unit_price", "current_stock"]
            for field in required_fields:
                assert field in drug, f"Missing field: {field}"
    
    def test_drugs_include_seeded_medications(self, auth_headers):
        """Should include seeded medications (analgesics, antimalarials, vitamins)"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/drugs", headers=auth_headers)
        data = response.json()
        
        drug_names = [d["generic_name"] for d in data["drugs"]]
        
        # Check for analgesics
        assert "Paracetamol" in drug_names, "Paracetamol should be in catalog"
        
        # Check for antimalarials
        assert "Artemether/Lumefantrine" in drug_names, "Artemether/Lumefantrine should be in catalog"
        
        # Check for vitamins
        assert "Vitamin C" in drug_names, "Vitamin C should be in catalog"
    
    def test_add_drug_to_catalog(self, auth_headers):
        """Should add a new drug to catalog"""
        unique_id = str(uuid.uuid4())[:8]
        drug_data = {
            "generic_name": f"TEST_Drug_{unique_id}",
            "brand_name": f"TestBrand_{unique_id}",
            "manufacturer": "Test Manufacturer",
            "strength": "100mg",
            "dosage_form": "tablet",
            "category": "pharmacy_only",
            "unit_price": 5.50,
            "pack_size": 10,
            "reorder_level": 20
        }
        
        response = requests.post(f"{BASE_URL}/api/pharmacy-portal/drugs", json=drug_data, headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data, "Missing drug ID in response"
    
    def test_drugs_requires_auth(self):
        """Drugs endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/drugs")
        assert response.status_code in [401, 403]


class TestMedicationDatabase:
    """Test global medication database search"""
    
    def test_search_medications(self, auth_headers):
        """Should search medications in global database"""
        response = requests.get(
            f"{BASE_URL}/api/pharmacy-portal/medications/search",
            params={"query": "paracetamol"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "medications" in data
        assert len(data["medications"]) > 0, "Should find paracetamol"
        
        # Check medication structure
        med = data["medications"][0]
        assert "generic_name" in med
        assert "brand_names" in med
        assert "dosage_forms" in med
        assert "strengths" in med
    
    def test_get_medication_categories(self, auth_headers):
        """Should return medication categories"""
        response = requests.get(
            f"{BASE_URL}/api/pharmacy-portal/medications/categories",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "categories" in data
        assert len(data["categories"]) > 50, "Should have 50+ categories"
        
        # Check for common categories
        category_codes = [c["code"] for c in data["categories"]]
        assert "analgesic" in category_codes
        assert "antimalarial" in category_codes
        assert "vitamin" in category_codes


class TestInventoryManagement:
    """Test inventory management endpoints"""
    
    def test_get_inventory(self, auth_headers):
        """Should return inventory list"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/inventory", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "inventory" in data
        assert "total" in data
        assert isinstance(data["inventory"], list)
    
    def test_get_inventory_alerts(self, auth_headers):
        """Should return inventory alerts (low stock, expiring)"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/inventory/alerts", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "low_stock" in data
        assert "low_stock_count" in data
        assert "expiring_soon" in data
        assert "expiring_soon_count" in data
        
        # All 19 drugs should be low stock (0 stock)
        assert data["low_stock_count"] == 19, f"Expected 19 low stock items, got {data['low_stock_count']}"
    
    def test_get_reorder_suggestions(self, auth_headers):
        """Should return reorder suggestions"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/reorder/suggestions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "suggestions" in data
        assert "total_items" in data
        assert data["total_items"] == 19, f"Expected 19 reorder suggestions, got {data['total_items']}"
        
        # Check suggestion structure
        if len(data["suggestions"]) > 0:
            suggestion = data["suggestions"][0]
            assert "drug_id" in suggestion
            assert "drug_name" in suggestion
            assert "current_stock" in suggestion
            assert "reorder_level" in suggestion
            assert "suggested_quantity" in suggestion
            assert "priority" in suggestion
    
    def test_inventory_requires_auth(self):
        """Inventory endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/inventory")
        assert response.status_code in [401, 403]


class TestSalesManagement:
    """Test sales management endpoints"""
    
    def test_get_sales(self, auth_headers):
        """Should return sales list"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/sales", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "sales" in data
        assert "total" in data
        assert "total_revenue" in data
        assert isinstance(data["sales"], list)
    
    def test_sales_requires_auth(self):
        """Sales endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/sales")
        assert response.status_code in [401, 403]


class TestPrescriptionManagement:
    """Test prescription management endpoints"""
    
    def test_get_incoming_prescriptions(self, auth_headers):
        """Should return incoming prescriptions"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/prescriptions/incoming", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "prescriptions" in data
        assert "total" in data
        assert isinstance(data["prescriptions"], list)
    
    def test_prescriptions_requires_auth(self):
        """Prescriptions endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/prescriptions/incoming")
        assert response.status_code in [401, 403]


class TestStaffManagement:
    """Test staff management endpoints"""
    
    def test_get_staff_list(self, auth_headers):
        """Should return staff list"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/admin/staff", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "staff" in data
        assert "total" in data
        assert data["total"] >= 1, "Should have at least 1 staff member"
        
        # Check staff structure
        if len(data["staff"]) > 0:
            staff = data["staff"][0]
            assert "id" in staff
            assert "email" in staff
            assert "first_name" in staff
            assert "last_name" in staff
            assert "role" in staff
            assert "department" in staff
            assert "is_active" in staff
    
    def test_create_staff_member(self, auth_headers):
        """Should create a new staff member"""
        unique_id = str(uuid.uuid4())[:8]
        staff_data = {
            "email": f"test_staff_{unique_id}@testpharm.gh",
            "first_name": "Test",
            "last_name": f"Staff_{unique_id}",
            "phone": f"+233201234{unique_id[:4]}",
            "role": "pharmacist",
            "department": "dispensary",
            "license_number": f"PSGH/TEST{unique_id}"
        }
        
        response = requests.post(f"{BASE_URL}/api/pharmacy-portal/admin/staff", json=staff_data, headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "id" in data, "Missing staff ID in response"
        assert "default_password" in data, "Missing default_password in response"
    
    def test_staff_requires_auth(self):
        """Staff endpoint should require authentication"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/admin/staff")
        assert response.status_code in [401, 403]


class TestDrugSeeding:
    """Test drug seeding from global database"""
    
    def test_seed_drugs_endpoint_exists(self, auth_headers):
        """Seed drugs endpoint should exist"""
        # Test with empty categories (should seed all)
        response = requests.post(
            f"{BASE_URL}/api/pharmacy-portal/drugs/seed",
            json={"categories": []},
            headers=auth_headers
        )
        # Should return 200 even if drugs already exist (skipped)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "added" in data
        assert "skipped" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
