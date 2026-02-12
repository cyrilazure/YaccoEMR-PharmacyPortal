"""
Test P0 Features for Ghana EMR Platform:
1. IT Admin Permission Management (supply_chain:manage for pharmacists)
2. FDA Barcode Lookup for Inventory
3. 2FA QR Code Generation
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
SUPER_ADMIN_EMAIL = "ygtnetworks@gmail.com"
SUPER_ADMIN_PASSWORD = "test123"
IT_ADMIN_EMAIL = "it_admin@yacco.health"
IT_ADMIN_PASSWORD = "test123"
PHARMACIST_EMAIL = "pharmacist@yacco.health"
PHARMACIST_PASSWORD = "test123"
HOSPITAL_ID = "008cca73-b733-4224-afa3-992c02c045a4"


class TestAuthentication:
    """Test authentication for different user types"""
    
    def test_super_admin_login(self):
        """Test super admin can login via /api/auth/login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Super admin login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Token not in response"
        assert data.get("user", {}).get("role") == "super_admin"
        print(f"✅ Super admin login successful: {data['user']['email']}")
    
    def test_it_admin_login(self):
        """Test IT admin can login via regions auth"""
        response = requests.post(f"{BASE_URL}/api/regions/auth/login", json={
            "email": IT_ADMIN_EMAIL,
            "password": IT_ADMIN_PASSWORD,
            "hospital_id": HOSPITAL_ID
        })
        assert response.status_code == 200, f"IT admin login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Token not in response"
        assert data.get("user", {}).get("role") == "hospital_it_admin"
        print(f"✅ IT admin login successful: {data['user']['email']}")
    
    def test_pharmacist_login(self):
        """Test pharmacist can login via regions auth"""
        response = requests.post(f"{BASE_URL}/api/regions/auth/login", json={
            "email": PHARMACIST_EMAIL,
            "password": PHARMACIST_PASSWORD,
            "hospital_id": HOSPITAL_ID
        })
        assert response.status_code == 200, f"Pharmacist login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Token not in response"
        assert data.get("user", {}).get("role") == "pharmacist"
        print(f"✅ Pharmacist login successful: {data['user']['email']}")


class TestITAdminPermissions:
    """Test IT Admin permission management endpoints"""
    
    @pytest.fixture
    def super_admin_token(self):
        """Get super admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Could not authenticate super admin")
    
    @pytest.fixture
    def it_admin_token(self):
        """Get IT admin auth token"""
        response = requests.post(f"{BASE_URL}/api/regions/auth/login", json={
            "email": IT_ADMIN_EMAIL,
            "password": IT_ADMIN_PASSWORD,
            "hospital_id": HOSPITAL_ID
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Could not authenticate IT admin")
    
    def test_get_staff_list(self, super_admin_token):
        """Test getting staff list for hospital"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/hospital/{HOSPITAL_ID}/super-admin/staff",
            headers=headers
        )
        assert response.status_code == 200, f"Failed to get staff list: {response.text}"
        data = response.json()
        assert "staff" in data
        print(f"✅ Staff list retrieved: {len(data['staff'])} staff members")
        return data['staff']
    
    def test_get_staff_permissions_endpoint_exists(self, super_admin_token):
        """Test that the permissions endpoint exists and returns proper structure"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        # First get staff list to find a staff member
        staff_response = requests.get(
            f"{BASE_URL}/api/hospital/{HOSPITAL_ID}/super-admin/staff",
            headers=headers
        )
        
        if staff_response.status_code != 200 or not staff_response.json().get('staff'):
            pytest.skip("No staff members found to test permissions")
        
        staff_id = staff_response.json()['staff'][0]['id']
        
        # Test permissions endpoint
        response = requests.get(
            f"{BASE_URL}/api/hospital/{HOSPITAL_ID}/super-admin/staff/{staff_id}/permissions",
            headers=headers
        )
        assert response.status_code == 200, f"Permissions endpoint failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "staff_id" in data
        assert "current_permissions" in data
        assert "available_permissions" in data
        
        # Verify available permissions include supply_chain:manage
        perm_codes = [p['code'] for p in data['available_permissions']]
        assert "supply_chain:manage" in perm_codes, "supply_chain:manage permission not available"
        
        print(f"✅ Permissions endpoint working. Available permissions: {perm_codes}")
        return data
    
    def test_grant_permission_endpoint(self, super_admin_token):
        """Test granting a permission to a staff member"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        # Get staff list
        staff_response = requests.get(
            f"{BASE_URL}/api/hospital/{HOSPITAL_ID}/super-admin/staff",
            headers=headers
        )
        
        if staff_response.status_code != 200 or not staff_response.json().get('staff'):
            pytest.skip("No staff members found")
        
        # Find a pharmacist or any staff member
        staff_list = staff_response.json()['staff']
        pharmacist = next((s for s in staff_list if s.get('role') == 'pharmacist'), staff_list[0])
        staff_id = pharmacist['id']
        
        # Grant supply_chain:manage permission
        response = requests.post(
            f"{BASE_URL}/api/hospital/{HOSPITAL_ID}/super-admin/staff/{staff_id}/permissions/grant",
            headers=headers,
            params={"permission": "supply_chain:manage"}
        )
        assert response.status_code == 200, f"Grant permission failed: {response.text}"
        data = response.json()
        assert "permissions" in data
        assert "supply_chain:manage" in data['permissions']
        print(f"✅ Permission granted successfully to {pharmacist.get('email', staff_id)}")
    
    def test_revoke_permission_endpoint(self, super_admin_token):
        """Test revoking a permission from a staff member"""
        headers = {"Authorization": f"Bearer {super_admin_token}"}
        
        # Get staff list
        staff_response = requests.get(
            f"{BASE_URL}/api/hospital/{HOSPITAL_ID}/super-admin/staff",
            headers=headers
        )
        
        if staff_response.status_code != 200 or not staff_response.json().get('staff'):
            pytest.skip("No staff members found")
        
        staff_id = staff_response.json()['staff'][0]['id']
        
        # First grant a permission
        requests.post(
            f"{BASE_URL}/api/hospital/{HOSPITAL_ID}/super-admin/staff/{staff_id}/permissions/grant",
            headers=headers,
            params={"permission": "supply_chain:view"}
        )
        
        # Then revoke it
        response = requests.post(
            f"{BASE_URL}/api/hospital/{HOSPITAL_ID}/super-admin/staff/{staff_id}/permissions/revoke",
            headers=headers,
            params={"permission": "supply_chain:view"}
        )
        assert response.status_code == 200, f"Revoke permission failed: {response.text}"
        data = response.json()
        assert "permissions" in data
        assert "supply_chain:view" not in data['permissions']
        print(f"✅ Permission revoked successfully")
    
    def test_it_admin_can_manage_permissions(self, it_admin_token):
        """Test IT admin can manage permissions for staff"""
        headers = {"Authorization": f"Bearer {it_admin_token}"}
        
        # Get staff list
        staff_response = requests.get(
            f"{BASE_URL}/api/hospital/{HOSPITAL_ID}/super-admin/staff",
            headers=headers
        )
        assert staff_response.status_code == 200, f"IT admin cannot access staff list: {staff_response.text}"
        
        if not staff_response.json().get('staff'):
            pytest.skip("No staff members found")
        
        staff_id = staff_response.json()['staff'][0]['id']
        
        # Test permissions endpoint
        response = requests.get(
            f"{BASE_URL}/api/hospital/{HOSPITAL_ID}/super-admin/staff/{staff_id}/permissions",
            headers=headers
        )
        assert response.status_code == 200, f"IT admin cannot access permissions: {response.text}"
        print(f"✅ IT admin can access permission management")


class TestFDABarcodeLookup:
    """Test FDA barcode lookup endpoint for inventory"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Could not authenticate")
    
    def test_barcode_lookup_known_barcode(self, auth_token):
        """Test barcode lookup with a known barcode returns drug info"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Test with known barcode from mock database
        response = requests.get(
            f"{BASE_URL}/api/fda/lookup/barcode",
            headers=headers,
            params={"barcode": "5000456123456"}
        )
        assert response.status_code == 200, f"Barcode lookup failed: {response.text}"
        data = response.json()
        
        assert data.get("found") == True, "Expected drug to be found"
        assert "drug" in data
        drug = data["drug"]
        assert "name" in drug
        assert "manufacturer" in drug
        assert "category" in drug
        print(f"✅ Barcode lookup successful: {drug['name']} by {drug['manufacturer']}")
    
    def test_barcode_lookup_unknown_barcode(self, auth_token):
        """Test barcode lookup with unknown barcode returns not found"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/fda/lookup/barcode",
            headers=headers,
            params={"barcode": "9999999999999"}
        )
        assert response.status_code == 200, f"Barcode lookup failed: {response.text}"
        data = response.json()
        
        assert data.get("found") == False, "Expected drug not to be found"
        assert "message" in data
        print(f"✅ Unknown barcode handled correctly: {data['message']}")
    
    def test_barcode_lookup_multiple_known_barcodes(self, auth_token):
        """Test multiple known barcodes from mock database"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        known_barcodes = [
            ("5000456123456", "Paracetamol"),
            ("5000789456123", "Amoxicillin"),
            ("5001234567890", "Artemether"),
            ("5009876543210", "Metformin"),
            ("5005551234567", "Omeprazole"),
        ]
        
        for barcode, expected_name_part in known_barcodes:
            response = requests.get(
                f"{BASE_URL}/api/fda/lookup/barcode",
                headers=headers,
                params={"barcode": barcode}
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get("found") == True, f"Barcode {barcode} should be found"
            assert expected_name_part.lower() in data['drug']['name'].lower(), \
                f"Expected {expected_name_part} in drug name"
            print(f"✅ Barcode {barcode}: {data['drug']['name']}")


class TestTwoFactorAuth:
    """Test 2FA setup and QR code generation"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Could not authenticate")
    
    def test_2fa_status_endpoint(self, auth_token):
        """Test 2FA status endpoint returns proper structure"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/2fa/status",
            headers=headers
        )
        assert response.status_code == 200, f"2FA status failed: {response.text}"
        data = response.json()
        
        assert "enabled" in data
        assert "verified" in data
        assert "backup_codes_remaining" in data
        print(f"✅ 2FA status: enabled={data['enabled']}, verified={data['verified']}")
    
    def test_2fa_setup_generates_qr_code(self, auth_token):
        """Test 2FA setup generates QR code and manual entry key"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/2fa/setup",
            headers=headers
        )
        
        # May return 400 if already enabled
        if response.status_code == 400:
            data = response.json()
            if "already enabled" in data.get("detail", "").lower():
                print("⚠️ 2FA already enabled for this user - skipping setup test")
                pytest.skip("2FA already enabled")
        
        assert response.status_code == 200, f"2FA setup failed: {response.text}"
        data = response.json()
        
        # Verify QR code is present and properly formatted
        assert "qr_code" in data, "QR code not in response"
        assert data["qr_code"].startswith("data:image/png;base64,"), \
            "QR code should be base64 PNG data URL"
        
        # Verify manual entry key is present
        assert "manual_entry_key" in data or "secret" in data, \
            "Manual entry key not in response"
        
        # Verify backup codes are generated
        assert "backup_codes" in data, "Backup codes not in response"
        assert len(data["backup_codes"]) >= 5, "Should have at least 5 backup codes"
        
        # Verify issuer and account info
        assert "issuer" in data, "Issuer not in response"
        assert "account_name" in data, "Account name not in response"
        
        print(f"✅ 2FA setup successful:")
        print(f"   - QR code generated: {len(data['qr_code'])} chars")
        print(f"   - Manual key: {data.get('manual_entry_key', data.get('secret', 'N/A'))[:20]}...")
        print(f"   - Backup codes: {len(data['backup_codes'])} codes")
        print(f"   - Issuer: {data['issuer']}")
        print(f"   - Account: {data['account_name']}")


class TestPharmacyPortalIntegration:
    """Test Pharmacy Portal inventory integration"""
    
    @pytest.fixture
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Could not authenticate")
    
    def test_inventory_endpoint(self, auth_token):
        """Test inventory endpoint is accessible"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/supply-chain/inventory",
            headers=headers
        )
        assert response.status_code == 200, f"Inventory endpoint failed: {response.text}"
        data = response.json()
        assert "items" in data
        print(f"✅ Inventory endpoint working: {len(data['items'])} items")
    
    def test_create_inventory_item_with_barcode(self, auth_token):
        """Test creating inventory item with barcode field"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        item_data = {
            "drug_name": "TEST_Barcode_Drug_001",
            "drug_code": "TEST-BC-001",
            "manufacturer": "Test Manufacturer",
            "category": "Analgesics & NSAIDs",
            "unit_of_measure": "tablet",
            "unit_cost": 5.50,
            "selling_price": 8.00,
            "reorder_level": 50,
            "max_stock_level": 500,
            "fda_registration": "FDA/TEST-001",
            "barcode": "5000456123456"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/supply-chain/inventory",
            headers=headers,
            json=item_data
        )
        assert response.status_code in [200, 201], f"Create inventory failed: {response.text}"
        data = response.json()
        assert "id" in data or "item" in data
        print(f"✅ Inventory item created with barcode")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
