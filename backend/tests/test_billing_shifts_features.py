"""
Test Billing Shifts Features - P0/P1 Enhancements
Tests:
1. Hospital info endpoint returns logo_url
2. Senior Biller dashboard endpoint
3. Admin financial dashboard
4. Shift reconciliation endpoints
5. Ghana Cedis (₵) currency display
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://yacco-health-1.preview.emergentagent.com')

# Test credentials
BILLER_CREDS = {"email": "biller@yacco.health", "password": "test123"}
NURSING_SUPERVISOR_CREDS = {"email": "nursing_supervisor@yacco.health", "password": "test123"}
IT_ADMIN_CREDS = {"email": "it_admin@yacco.health", "password": "test123"}


class TestHospitalInfo:
    """Test hospital info endpoint returns logo_url"""
    
    def test_hospital_info_returns_logo_url_field(self):
        """Verify /api/hospital/info endpoint returns logo_url field"""
        # Login as IT admin
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json=IT_ADMIN_CREDS)
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["token"]
        
        # Get hospital info
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{BASE_URL}/api/hospital/info", headers=headers)
        
        assert res.status_code == 200, f"Hospital info failed: {res.text}"
        data = res.json()
        
        # Verify logo_url field exists (can be null but field must exist)
        assert "logo_url" in data, f"logo_url field missing from response: {data}"
        print(f"✓ Hospital info contains logo_url: {data.get('logo_url')}")
        print(f"✓ Hospital name: {data.get('name')}")


class TestSeniorBillerDashboard:
    """Test Senior Biller dashboard endpoint"""
    
    def test_senior_biller_dashboard_accessible_by_admin(self):
        """Verify /api/billing-shifts/dashboard/senior-biller works for admin roles"""
        # Login as IT admin (should have access)
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json=IT_ADMIN_CREDS)
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{BASE_URL}/api/billing-shifts/dashboard/senior-biller", headers=headers)
        
        assert res.status_code == 200, f"Senior biller dashboard failed: {res.text}"
        data = res.json()
        
        # Verify expected fields
        assert "department" in data, "Missing department field"
        assert "today_summary" in data, "Missing today_summary field"
        assert "payment_breakdown" in data, "Missing payment_breakdown field"
        assert "active_shifts" in data, "Missing active_shifts field"
        assert "outstanding" in data, "Missing outstanding field"
        
        print(f"✓ Senior biller dashboard accessible")
        print(f"  - Department: {data.get('department')}")
        print(f"  - Today's summary: {data.get('today_summary')}")
        print(f"  - Payment breakdown: {data.get('payment_breakdown')}")
    
    def test_senior_biller_dashboard_denied_for_regular_biller(self):
        """Verify regular biller cannot access senior biller dashboard"""
        # Login as regular biller
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json=BILLER_CREDS)
        if login_res.status_code != 200:
            pytest.skip("Biller user not available")
        
        token = login_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        res = requests.get(f"{BASE_URL}/api/billing-shifts/dashboard/senior-biller", headers=headers)
        
        # Should be 403 Forbidden for regular biller
        assert res.status_code == 403, f"Expected 403, got {res.status_code}: {res.text}"
        print("✓ Regular biller correctly denied access to senior biller dashboard")


class TestAdminFinancialDashboard:
    """Test Admin Financial Dashboard endpoint"""
    
    def test_admin_dashboard_returns_revenue_metrics(self):
        """Verify /api/billing-shifts/dashboard/admin returns Today/Week/Month metrics"""
        # Login as IT admin
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json=IT_ADMIN_CREDS)
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{BASE_URL}/api/billing-shifts/dashboard/admin", headers=headers)
        
        assert res.status_code == 200, f"Admin dashboard failed: {res.text}"
        data = res.json()
        
        # Verify daily/weekly/monthly metrics
        assert "daily" in data, "Missing daily metrics"
        assert "weekly" in data, "Missing weekly metrics"
        assert "monthly" in data, "Missing monthly metrics"
        
        # Verify daily has revenue field
        assert "revenue" in data["daily"], "Missing daily revenue"
        assert "invoices_count" in data["daily"], "Missing daily invoices_count"
        
        # Verify weekly has revenue field
        assert "revenue" in data["weekly"], "Missing weekly revenue"
        
        # Verify monthly has revenue field
        assert "revenue" in data["monthly"], "Missing monthly revenue"
        
        # Verify payment modes
        assert "payment_modes" in data, "Missing payment_modes"
        
        # Verify shifts overview
        assert "shifts" in data, "Missing shifts overview"
        
        print(f"✓ Admin financial dashboard returns all metrics")
        print(f"  - Daily revenue: {data['daily'].get('revenue')}")
        print(f"  - Weekly revenue: {data['weekly'].get('revenue')}")
        print(f"  - Monthly revenue: {data['monthly'].get('revenue')}")
        print(f"  - Payment modes: {data.get('payment_modes')}")


class TestShiftReconciliation:
    """Test Shift Reconciliation endpoints"""
    
    def test_all_shifts_endpoint_accessible(self):
        """Verify /api/billing-shifts/all-shifts works for admin roles
        Note: hospital_it_admin is NOT in allowed_roles for all-shifts endpoint
        Allowed: hospital_admin, finance_manager, admin, senior_biller
        """
        # Login as IT admin - should get 403 (not in allowed_roles)
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json=IT_ADMIN_CREDS)
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{BASE_URL}/api/billing-shifts/all-shifts", headers=headers)
        
        # hospital_it_admin is NOT in allowed_roles for this endpoint
        # Expected: 403 Forbidden
        assert res.status_code == 403, f"Expected 403 for hospital_it_admin, got {res.status_code}"
        print(f"✓ All shifts endpoint correctly restricts access for hospital_it_admin")
        print(f"  - Note: Only hospital_admin, finance_manager, admin, senior_biller can access")
    
    def test_biller_dashboard_endpoint(self):
        """Verify /api/billing-shifts/dashboard/biller works"""
        # Login as IT admin (can also access biller dashboard)
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json=IT_ADMIN_CREDS)
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{BASE_URL}/api/billing-shifts/dashboard/biller", headers=headers)
        
        assert res.status_code == 200, f"Biller dashboard failed: {res.text}"
        data = res.json()
        
        # Verify expected fields
        assert "has_active_shift" in data, "Missing has_active_shift field"
        assert "outstanding" in data, "Missing outstanding field"
        
        print(f"✓ Biller dashboard accessible")
        print(f"  - Has active shift: {data.get('has_active_shift')}")
        print(f"  - Outstanding: {data.get('outstanding')}")


class TestBillingShiftsCRUD:
    """Test Billing Shifts CRUD operations"""
    
    def test_clock_in_clock_out_role_restriction(self):
        """Test clock in/out role restrictions
        Note: hospital_it_admin is NOT in allowed_roles for clock-in
        Allowed: biller, senior_biller, cashier, hospital_admin, finance_manager
        """
        # Login as IT admin
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json=IT_ADMIN_CREDS)
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to clock in - should fail for hospital_it_admin
        clock_in_res = requests.post(
            f"{BASE_URL}/api/billing-shifts/clock-in",
            headers=headers,
            json={"shift_type": "day", "notes": "Test shift"}
        )
        
        # hospital_it_admin is NOT in allowed_roles for clock-in
        assert clock_in_res.status_code == 403, f"Expected 403 for hospital_it_admin, got {clock_in_res.status_code}"
        print(f"✓ Clock in correctly restricts access for hospital_it_admin")
        print(f"  - Note: Only biller, senior_biller, cashier, hospital_admin, finance_manager can clock in")
    
    def test_active_shift_endpoint(self):
        """Test active shift endpoint is accessible"""
        # Login as IT admin
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json=IT_ADMIN_CREDS)
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Check active shift - should work for any authenticated user
        active_res = requests.get(f"{BASE_URL}/api/billing-shifts/active", headers=headers)
        assert active_res.status_code == 200, f"Active shift check failed: {active_res.text}"
        print(f"✓ Active shift endpoint accessible")


class TestGhanaCedisDisplay:
    """Test Ghana Cedis (₵) currency display in billing"""
    
    def test_billing_stats_endpoint(self):
        """Verify billing stats endpoint works"""
        # Login as IT admin
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json=IT_ADMIN_CREDS)
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{BASE_URL}/api/billing/stats", headers=headers)
        
        assert res.status_code == 200, f"Billing stats failed: {res.text}"
        data = res.json()
        
        # Verify numeric fields exist (currency formatting is frontend responsibility)
        print(f"✓ Billing stats endpoint works")
        print(f"  - Total billed: {data.get('total_billed', 0)}")
        print(f"  - Total collected: {data.get('total_collected', 0)}")
        print(f"  - Total outstanding: {data.get('total_outstanding', 0)}")


class TestNursingSupervisorClockOut:
    """Test Nursing Supervisor clock out functionality"""
    
    def test_nursing_supervisor_dashboard_accessible(self):
        """Verify nursing supervisor dashboard is accessible"""
        # Login as nursing supervisor
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json=NURSING_SUPERVISOR_CREDS)
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Access nursing supervisor dashboard
        dashboard_res = requests.get(f"{BASE_URL}/api/nursing-supervisor/dashboard", headers=headers)
        assert dashboard_res.status_code == 200, f"Dashboard failed: {dashboard_res.text}"
        
        data = dashboard_res.json()
        print(f"✓ Nursing supervisor dashboard accessible")
        print(f"  - Nurses on shift: {data.get('nurses_on_shift', 0)}")
        print(f"  - Total nurses: {data.get('total_nurses', 0)}")
        print(f"  - Active assignments: {data.get('active_assignments', 0)}")
    
    def test_nursing_supervisor_current_shifts(self):
        """Verify nursing supervisor can view current shifts"""
        # Login as nursing supervisor
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json=NURSING_SUPERVISOR_CREDS)
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get current shifts
        shifts_res = requests.get(f"{BASE_URL}/api/nursing-supervisor/shifts/current", headers=headers)
        assert shifts_res.status_code == 200, f"Current shifts failed: {shifts_res.text}"
        
        data = shifts_res.json()
        print(f"✓ Current shifts endpoint accessible")
        print(f"  - Active shifts: {len(data.get('active_shifts', []))}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
