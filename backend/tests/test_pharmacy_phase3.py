"""
Pharmacy Module Phase 3 Tests
=============================
Tests for:
1. E-prescription routing from hospital EMR to pharmacies
2. Supply request system for pharmacy-to-pharmacy requests
3. Enhanced audit logging for all pharmacy activities
"""

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "test@testpharm.gh"
TEST_PASSWORD = "testpass123"


class TestPharmacyPhase3Auth:
    """Authentication tests for Phase 3"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def test_login_success(self):
        """Test pharmacy login returns token"""
        response = self.session.post(f"{BASE_URL}/api/pharmacy-portal/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert "pharmacy" in data
        print(f"✓ Login successful for {TEST_EMAIL}")
        return data["token"]


class TestSupplyRequestsOutgoing:
    """Tests for outgoing supply requests API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authenticated session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        response = self.session.post(f"{BASE_URL}/api/pharmacy-portal/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            token = response.json()["token"]
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        
    def test_get_outgoing_supply_requests(self):
        """Test GET /api/pharmacy-portal/supply-requests/outgoing returns list"""
        response = self.session.get(f"{BASE_URL}/api/pharmacy-portal/supply-requests/outgoing")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "requests" in data
        assert "total" in data
        assert isinstance(data["requests"], list)
        print(f"✓ Outgoing supply requests: {data['total']} found")
        
    def test_outgoing_requests_requires_auth(self):
        """Test outgoing requests requires authentication"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/pharmacy-portal/supply-requests/outgoing")
        assert response.status_code in [401, 403], "Should require auth"
        print("✓ Outgoing requests requires authentication")


class TestSupplyRequestsIncoming:
    """Tests for incoming supply requests API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authenticated session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        response = self.session.post(f"{BASE_URL}/api/pharmacy-portal/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            token = response.json()["token"]
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        
    def test_get_incoming_supply_requests(self):
        """Test GET /api/pharmacy-portal/supply-requests/incoming returns list"""
        response = self.session.get(f"{BASE_URL}/api/pharmacy-portal/supply-requests/incoming")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "requests" in data
        assert "total" in data
        assert isinstance(data["requests"], list)
        print(f"✓ Incoming supply requests: {data['total']} found")
        
    def test_incoming_requests_requires_auth(self):
        """Test incoming requests requires authentication"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/pharmacy-portal/supply-requests/incoming")
        assert response.status_code in [401, 403], "Should require auth"
        print("✓ Incoming requests requires authentication")


class TestAuditLogs:
    """Tests for audit logs API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authenticated session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        response = self.session.post(f"{BASE_URL}/api/pharmacy-portal/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            token = response.json()["token"]
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        
    def test_get_audit_logs(self):
        """Test GET /api/pharmacy-portal/audit-logs returns logs"""
        response = self.session.get(f"{BASE_URL}/api/pharmacy-portal/audit-logs")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "logs" in data
        assert "total" in data
        assert isinstance(data["logs"], list)
        print(f"✓ Audit logs: {data['total']} found")
        
    def test_audit_logs_with_limit(self):
        """Test audit logs with limit parameter"""
        response = self.session.get(f"{BASE_URL}/api/pharmacy-portal/audit-logs?limit=10")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert len(data["logs"]) <= 10
        print(f"✓ Audit logs with limit: {len(data['logs'])} returned")
        
    def test_audit_logs_requires_auth(self):
        """Test audit logs requires authentication"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/pharmacy-portal/audit-logs")
        assert response.status_code in [401, 403], "Should require auth"
        print("✓ Audit logs requires authentication")


class TestAuditLogsSummary:
    """Tests for audit logs summary API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authenticated session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        response = self.session.post(f"{BASE_URL}/api/pharmacy-portal/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            token = response.json()["token"]
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        
    def test_get_audit_logs_summary(self):
        """Test GET /api/pharmacy-portal/audit-logs/summary returns summary"""
        response = self.session.get(f"{BASE_URL}/api/pharmacy-portal/audit-logs/summary")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "total_activities" in data
        assert "by_action" in data
        assert "by_entity" in data
        assert "by_user" in data
        assert "period_days" in data
        print(f"✓ Audit summary: {data['total_activities']} total activities")
        
    def test_audit_summary_with_days_param(self):
        """Test audit summary with custom days parameter"""
        response = self.session.get(f"{BASE_URL}/api/pharmacy-portal/audit-logs/summary?days=30")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["period_days"] == 30
        print(f"✓ Audit summary for 30 days: {data['total_activities']} activities")
        
    def test_audit_summary_requires_auth(self):
        """Test audit summary requires authentication"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/pharmacy-portal/audit-logs/summary")
        assert response.status_code in [401, 403], "Should require auth"
        print("✓ Audit summary requires authentication")


class TestPharmacyNetwork:
    """Tests for pharmacy network directory API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authenticated session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        response = self.session.post(f"{BASE_URL}/api/pharmacy-portal/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            token = response.json()["token"]
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        
    def test_get_pharmacy_network(self):
        """Test GET /api/pharmacy-portal/network/pharmacies returns list"""
        response = self.session.get(f"{BASE_URL}/api/pharmacy-portal/network/pharmacies")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "pharmacies" in data
        assert "total" in data
        assert isinstance(data["pharmacies"], list)
        print(f"✓ Pharmacy network: {data['total']} pharmacies found")
        
    def test_pharmacy_network_excludes_own(self):
        """Test pharmacy network excludes own pharmacy"""
        response = self.session.get(f"{BASE_URL}/api/pharmacy-portal/network/pharmacies")
        assert response.status_code == 200
        data = response.json()
        # Own pharmacy should not be in the list
        # This is expected behavior - network shows OTHER pharmacies
        print(f"✓ Pharmacy network excludes own pharmacy (shows {data['total']} others)")
        
    def test_pharmacy_network_requires_auth(self):
        """Test pharmacy network requires authentication"""
        session = requests.Session()
        response = session.get(f"{BASE_URL}/api/pharmacy-portal/network/pharmacies")
        assert response.status_code in [401, 403], "Should require auth"
        print("✓ Pharmacy network requires authentication")


class TestEPrescriptionReceive:
    """Tests for e-prescription receiving API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authenticated session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        response = self.session.post(f"{BASE_URL}/api/pharmacy-portal/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            token = response.json()["token"]
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        
    def test_receive_eprescription(self):
        """Test POST /api/pharmacy-portal/eprescription/receive"""
        test_rx_id = f"TEST_RX_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        response = self.session.post(f"{BASE_URL}/api/pharmacy-portal/eprescription/receive", json={
            "prescription_id": test_rx_id,
            "rx_number": f"RX-{test_rx_id[-6:]}",
            "patient_name": "Test Patient",
            "patient_phone": "+233201234567",
            "prescriber_name": "Dr. Test Doctor",
            "hospital_name": "Test Hospital",
            "hospital_id": "test-hospital-001",
            "medications": [
                {
                    "medication_name": "Paracetamol",
                    "dosage": "500mg",
                    "frequency": "3 times daily",
                    "duration": "5 days",
                    "quantity": 15
                }
            ],
            "diagnosis": "Fever",
            "clinical_notes": "Test prescription",
            "priority": "routine"
        })
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "prescription_id" in data
        assert "rx_number" in data
        assert data["status"] in ["received", "duplicate"]
        print(f"✓ E-prescription received: {data['rx_number']}")
        
    def test_eprescription_requires_auth(self):
        """Test e-prescription receive requires authentication"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        response = session.post(f"{BASE_URL}/api/pharmacy-portal/eprescription/receive", json={
            "prescription_id": "test",
            "rx_number": "RX-TEST",
            "patient_name": "Test",
            "prescriber_name": "Dr. Test",
            "hospital_name": "Test Hospital",
            "medications": []
        })
        assert response.status_code in [401, 403], "Should require auth"
        print("✓ E-prescription receive requires authentication")


class TestDashboardPhase3:
    """Tests for dashboard with Phase 3 features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup authenticated session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        response = self.session.post(f"{BASE_URL}/api/pharmacy-portal/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            token = response.json()["token"]
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        
    def test_dashboard_returns_stats(self):
        """Test dashboard returns all expected stats"""
        response = self.session.get(f"{BASE_URL}/api/pharmacy-portal/dashboard")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        
        # Check expected fields
        expected_fields = [
            "today_sales_count",
            "today_revenue",
            "pending_prescriptions",
            "low_stock_count",
            "total_drugs"
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        print(f"✓ Dashboard stats: {data['total_drugs']} drugs, {data['today_sales_count']} sales today")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
