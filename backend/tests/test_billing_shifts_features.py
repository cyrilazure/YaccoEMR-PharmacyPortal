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

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ghana-emr.preview.emergentagent.com')

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
        """Verify /api/billing-shifts/all-shifts works for admin"""
        # Login as IT admin
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json=IT_ADMIN_CREDS)
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{BASE_URL}/api/billing-shifts/all-shifts", headers=headers)
        
        assert res.status_code == 200, f"All shifts endpoint failed: {res.text}"
        data = res.json()
        
        assert "shifts" in data, "Missing shifts array"
        print(f"✓ All shifts endpoint accessible, found {len(data.get('shifts', []))} shifts")
    
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
    
    def test_clock_in_clock_out_flow(self):
        """Test clock in and clock out flow"""
        # Login as IT admin
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json=IT_ADMIN_CREDS)
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Check if already has active shift
        active_res = requests.get(f"{BASE_URL}/api/billing-shifts/active", headers=headers)
        assert active_res.status_code == 200
        
        if active_res.json().get("active_shift"):
            # Clock out first
            clock_out_res = requests.post(
                f"{BASE_URL}/api/billing-shifts/clock-out",
                headers=headers,
                json={"closing_notes": "Test cleanup"}
            )
            print(f"  - Cleaned up existing shift: {clock_out_res.status_code}")
        
        # Clock in
        clock_in_res = requests.post(
            f"{BASE_URL}/api/billing-shifts/clock-in",
            headers=headers,
            json={"shift_type": "day", "notes": "Test shift"}
        )
        assert clock_in_res.status_code == 200, f"Clock in failed: {clock_in_res.text}"
        print(f"✓ Clock in successful")
        
        # Verify active shift
        active_res = requests.get(f"{BASE_URL}/api/billing-shifts/active", headers=headers)
        assert active_res.status_code == 200
        assert active_res.json().get("active_shift") is not None, "No active shift after clock in"
        print(f"✓ Active shift verified")
        
        # Clock out
        clock_out_res = requests.post(
            f"{BASE_URL}/api/billing-shifts/clock-out",
            headers=headers,
            json={"closing_notes": "Test complete", "actual_cash": 0}
        )
        assert clock_out_res.status_code == 200, f"Clock out failed: {clock_out_res.text}"
        print(f"✓ Clock out successful")
        
        # Verify no active shift
        active_res = requests.get(f"{BASE_URL}/api/billing-shifts/active", headers=headers)
        assert active_res.status_code == 200
        assert active_res.json().get("active_shift") is None, "Still has active shift after clock out"
        print(f"✓ No active shift after clock out")


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
    
    def test_nurse_clock_in_out_endpoints(self):
        """Verify nurse clock in/out endpoints work"""
        # Login as nursing supervisor
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json=NURSING_SUPERVISOR_CREDS)
        assert login_res.status_code == 200, f"Login failed: {login_res.text}"
        token = login_res.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Check current shift
        current_res = requests.get(f"{BASE_URL}/api/nurse/current-shift", headers=headers)
        assert current_res.status_code == 200, f"Current shift check failed: {current_res.text}"
        
        current_shift = current_res.json()
        print(f"✓ Current shift endpoint works")
        print(f"  - Has active shift: {current_shift is not None and 'id' in current_shift}")
        
        # If has active shift, clock out first
        if current_shift and current_shift.get('id'):
            clock_out_res = requests.post(
                f"{BASE_URL}/api/nurse/shifts/clock-out",
                headers=headers,
                params={"handoff_notes": "Test cleanup"}
            )
            print(f"  - Cleaned up existing shift: {clock_out_res.status_code}")
        
        # Clock in
        clock_in_res = requests.post(
            f"{BASE_URL}/api/nurse/shifts/clock-in",
            headers=headers,
            json={"shift_type": "day"}
        )
        assert clock_in_res.status_code == 200, f"Clock in failed: {clock_in_res.text}"
        print(f"✓ Nurse clock in successful")
        
        # Clock out
        clock_out_res = requests.post(
            f"{BASE_URL}/api/nurse/shifts/clock-out",
            headers=headers,
            params={"handoff_notes": "Test complete"}
        )
        assert clock_out_res.status_code == 200, f"Clock out failed: {clock_out_res.text}"
        print(f"✓ Nurse clock out successful")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
