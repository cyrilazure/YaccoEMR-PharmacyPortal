"""
Test suite for Radiology Module - Radiologist Portal and Workflow
Tests: Dashboard, Orders, Reports, Notes, Assignment, Timeline
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
RADIOLOGIST_EMAIL = "radiologist@yacco.health"
RADIOLOGIST_PASSWORD = "test123"
PHYSICIAN_EMAIL = "physician@yacco.health"
PHYSICIAN_PASSWORD = "test123"


class TestRadiologyAuth:
    """Test radiologist authentication"""
    
    def test_radiologist_login(self):
        """Test radiologist can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": RADIOLOGIST_EMAIL,
            "password": RADIOLOGIST_PASSWORD
        })
        print(f"Login response status: {response.status_code}")
        print(f"Login response: {response.json()}")
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data or "token" in data, "No token in response"
        
        # Store token for other tests
        token = data.get("access_token") or data.get("token")
        assert token is not None
        return token


class TestRadiologyDashboard:
    """Test radiologist dashboard endpoint"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers for radiologist"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": RADIOLOGIST_EMAIL,
            "password": RADIOLOGIST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Login failed: {response.text}")
        data = response.json()
        token = data.get("access_token") or data.get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_radiologist_dashboard(self, auth_headers):
        """Test GET /api/radiology/dashboard/radiologist"""
        response = requests.get(
            f"{BASE_URL}/api/radiology/dashboard/radiologist",
            headers=auth_headers
        )
        print(f"Dashboard response status: {response.status_code}")
        print(f"Dashboard response: {response.json()}")
        
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        data = response.json()
        
        # Verify dashboard structure
        assert "stats" in data, "Missing stats in dashboard"
        stats = data["stats"]
        
        # Check expected stat fields
        expected_stats = ["pending_review", "stat_pending", "my_assigned", "my_reports_today", "critical_pending", "total_queue"]
        for stat in expected_stats:
            assert stat in stats, f"Missing stat: {stat}"
        
        # Verify other dashboard sections
        assert "assigned_studies" in data, "Missing assigned_studies"
        assert "unassigned_studies" in data, "Missing unassigned_studies"
        assert "stat_studies" in data, "Missing stat_studies"
        assert "my_recent_reports" in data, "Missing my_recent_reports"
        assert "critical_findings" in data, "Missing critical_findings"


class TestRadiologyOrders:
    """Test radiology orders endpoints"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers for radiologist"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": RADIOLOGIST_EMAIL,
            "password": RADIOLOGIST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Login failed: {response.text}")
        data = response.json()
        token = data.get("access_token") or data.get("token")
        return {"Authorization": f"Bearer {token}"}
    
    @pytest.fixture
    def physician_headers(self):
        """Get auth headers for physician (to create orders)"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": PHYSICIAN_EMAIL,
            "password": PHYSICIAN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Physician login failed: {response.text}")
        data = response.json()
        token = data.get("access_token") or data.get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_radiology_queue(self, auth_headers):
        """Test GET /api/radiology/orders/queue"""
        response = requests.get(
            f"{BASE_URL}/api/radiology/orders/queue",
            headers=auth_headers
        )
        print(f"Queue response status: {response.status_code}")
        
        assert response.status_code == 200, f"Queue failed: {response.text}"
        data = response.json()
        
        assert "orders" in data, "Missing orders in queue"
        assert "stats" in data, "Missing stats in queue"
    
    def test_get_worklist(self, auth_headers):
        """Test GET /api/radiology/worklist"""
        response = requests.get(
            f"{BASE_URL}/api/radiology/worklist",
            headers=auth_headers
        )
        print(f"Worklist response status: {response.status_code}")
        
        # Worklist might return 404 if endpoint doesn't exist
        if response.status_code == 404:
            print("Worklist endpoint not found - may use queue instead")
            pytest.skip("Worklist endpoint not implemented")
        
        assert response.status_code == 200, f"Worklist failed: {response.text}"
    
    def test_get_modalities(self, auth_headers):
        """Test GET /api/radiology/modalities"""
        response = requests.get(
            f"{BASE_URL}/api/radiology/modalities",
            headers=auth_headers
        )
        print(f"Modalities response status: {response.status_code}")
        
        assert response.status_code == 200, f"Modalities failed: {response.text}"
        data = response.json()
        
        # Should return list of modalities
        assert isinstance(data, list), "Modalities should be a list"
        assert len(data) > 0, "Should have at least one modality"
        
        # Check modality structure
        modality = data[0]
        assert "value" in modality, "Modality missing value"
        assert "name" in modality, "Modality missing name"
    
    def test_get_study_types(self, auth_headers):
        """Test GET /api/radiology/study-types"""
        response = requests.get(
            f"{BASE_URL}/api/radiology/study-types",
            headers=auth_headers
        )
        print(f"Study types response status: {response.status_code}")
        
        assert response.status_code == 200, f"Study types failed: {response.text}"
        data = response.json()
        
        # Should return dict of study types by modality
        assert isinstance(data, dict), "Study types should be a dict"


class TestRadiologyOrderAssignment:
    """Test order assignment to radiologist"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers for radiologist"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": RADIOLOGIST_EMAIL,
            "password": RADIOLOGIST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Login failed: {response.text}")
        data = response.json()
        token = data.get("access_token") or data.get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_assign_order_to_self(self, auth_headers):
        """Test POST /api/radiology/orders/{order_id}/assign - claim study"""
        # First get an order from the queue
        queue_response = requests.get(
            f"{BASE_URL}/api/radiology/orders/queue",
            headers=auth_headers
        )
        
        if queue_response.status_code != 200:
            pytest.skip("Could not get queue")
        
        queue_data = queue_response.json()
        orders = queue_data.get("orders", [])
        
        if not orders:
            print("No orders in queue to assign")
            pytest.skip("No orders available to test assignment")
        
        # Try to assign first order
        order_id = orders[0]["id"]
        response = requests.post(
            f"{BASE_URL}/api/radiology/orders/{order_id}/assign",
            headers=auth_headers
        )
        print(f"Assign response status: {response.status_code}")
        print(f"Assign response: {response.json()}")
        
        assert response.status_code == 200, f"Assignment failed: {response.text}"
        data = response.json()
        assert "message" in data, "Missing message in response"


class TestRadiologyReports:
    """Test structured radiology reports"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers for radiologist"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": RADIOLOGIST_EMAIL,
            "password": RADIOLOGIST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Login failed: {response.text}")
        data = response.json()
        token = data.get("access_token") or data.get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_create_draft_report(self, auth_headers):
        """Test POST /api/radiology/reports/create - save draft"""
        # First get an order to create report for
        queue_response = requests.get(
            f"{BASE_URL}/api/radiology/orders/queue",
            headers=auth_headers
        )
        
        if queue_response.status_code != 200:
            pytest.skip("Could not get queue")
        
        queue_data = queue_response.json()
        orders = queue_data.get("orders", [])
        
        if not orders:
            print("No orders in queue to create report for")
            pytest.skip("No orders available to test report creation")
        
        order_id = orders[0]["id"]
        
        # Create draft report
        report_data = {
            "order_id": order_id,
            "study_quality": "diagnostic",
            "technique": "Standard technique",
            "clinical_indication": "Test indication",
            "findings_text": "TEST_DRAFT: Normal findings",
            "impression": "TEST_DRAFT: No acute abnormality",
            "recommendations": "Follow up as needed",
            "critical_finding": False,
            "status": "draft"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/radiology/reports/create",
            headers=auth_headers,
            json=report_data
        )
        print(f"Create report response status: {response.status_code}")
        print(f"Create report response: {response.json()}")
        
        assert response.status_code == 200, f"Create report failed: {response.text}"
        data = response.json()
        assert "report" in data, "Missing report in response"
        assert data["report"]["status"] == "draft", "Report should be draft"
        
        return data["report"]["id"]
    
    def test_create_finalized_report(self, auth_headers):
        """Test POST /api/radiology/reports/create with finalized status"""
        # First get an order to create report for
        queue_response = requests.get(
            f"{BASE_URL}/api/radiology/orders/queue",
            headers=auth_headers
        )
        
        if queue_response.status_code != 200:
            pytest.skip("Could not get queue")
        
        queue_data = queue_response.json()
        orders = queue_data.get("orders", [])
        
        if len(orders) < 2:
            print("Not enough orders in queue")
            pytest.skip("Not enough orders to test finalized report")
        
        # Use second order to avoid conflict with draft test
        order_id = orders[1]["id"] if len(orders) > 1 else orders[0]["id"]
        
        # Create finalized report
        report_data = {
            "order_id": order_id,
            "study_quality": "diagnostic",
            "technique": "Standard technique",
            "clinical_indication": "Test indication",
            "findings_text": "TEST_FINAL: Normal chest radiograph",
            "impression": "TEST_FINAL: No acute cardiopulmonary abnormality",
            "recommendations": "No follow up needed",
            "critical_finding": False,
            "status": "finalized"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/radiology/reports/create",
            headers=auth_headers,
            json=report_data
        )
        print(f"Finalize report response status: {response.status_code}")
        
        assert response.status_code == 200, f"Finalize report failed: {response.text}"
        data = response.json()
        assert "report" in data, "Missing report in response"
        assert data["report"]["status"] == "finalized", "Report should be finalized"


class TestRadiologyNotes:
    """Test radiologist notes (addendums, procedure notes)"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers for radiologist"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": RADIOLOGIST_EMAIL,
            "password": RADIOLOGIST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Login failed: {response.text}")
        data = response.json()
        token = data.get("access_token") or data.get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_create_note(self, auth_headers):
        """Test POST /api/radiology/notes/create"""
        # Get a patient ID first
        patients_response = requests.get(
            f"{BASE_URL}/api/patients",
            headers=auth_headers
        )
        
        if patients_response.status_code != 200:
            pytest.skip("Could not get patients")
        
        patients = patients_response.json()
        if not patients:
            pytest.skip("No patients available")
        
        patient_id = patients[0]["id"]
        
        # Create note
        note_data = {
            "patient_id": patient_id,
            "note_type": "procedure_note",
            "content": "TEST_NOTE: Patient tolerated procedure well",
            "urgency": "routine"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/radiology/notes/create",
            headers=auth_headers,
            json=note_data
        )
        print(f"Create note response status: {response.status_code}")
        print(f"Create note response: {response.json()}")
        
        assert response.status_code == 200, f"Create note failed: {response.text}"
        data = response.json()
        assert "note" in data, "Missing note in response"
        assert data["note"]["note_type"] == "procedure_note"


class TestRadiologyTimeline:
    """Test order status timeline"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers for radiologist"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": RADIOLOGIST_EMAIL,
            "password": RADIOLOGIST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Login failed: {response.text}")
        data = response.json()
        token = data.get("access_token") or data.get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_order_timeline(self, auth_headers):
        """Test GET /api/radiology/orders/{order_id}/timeline"""
        # First get an order
        queue_response = requests.get(
            f"{BASE_URL}/api/radiology/orders/queue",
            headers=auth_headers
        )
        
        if queue_response.status_code != 200:
            pytest.skip("Could not get queue")
        
        queue_data = queue_response.json()
        orders = queue_data.get("orders", [])
        
        if not orders:
            pytest.skip("No orders available")
        
        order_id = orders[0]["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/radiology/orders/{order_id}/timeline",
            headers=auth_headers
        )
        print(f"Timeline response status: {response.status_code}")
        
        # Timeline endpoint might not exist
        if response.status_code == 404:
            print("Timeline endpoint not found")
            pytest.skip("Timeline endpoint not implemented")
        
        assert response.status_code == 200, f"Timeline failed: {response.text}"


class TestRadiologyRBAC:
    """Test RBAC for radiologist role"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers for radiologist"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": RADIOLOGIST_EMAIL,
            "password": RADIOLOGIST_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Login failed: {response.text}")
        data = response.json()
        token = data.get("access_token") or data.get("token")
        return {"Authorization": f"Bearer {token}"}
    
    def test_radiologist_can_access_dashboard(self, auth_headers):
        """Verify radiologist role can access dashboard"""
        response = requests.get(
            f"{BASE_URL}/api/radiology/dashboard/radiologist",
            headers=auth_headers
        )
        assert response.status_code == 200, "Radiologist should access dashboard"
    
    def test_radiologist_can_create_reports(self, auth_headers):
        """Verify radiologist role can create reports"""
        # Get an order first
        queue_response = requests.get(
            f"{BASE_URL}/api/radiology/orders/queue",
            headers=auth_headers
        )
        
        if queue_response.status_code != 200:
            pytest.skip("Could not get queue")
        
        queue_data = queue_response.json()
        orders = queue_data.get("orders", [])
        
        if not orders:
            pytest.skip("No orders available")
        
        # Try to create a report
        report_data = {
            "order_id": orders[0]["id"],
            "findings_text": "TEST_RBAC: Test findings",
            "impression": "TEST_RBAC: Test impression",
            "status": "draft"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/radiology/reports/create",
            headers=auth_headers,
            json=report_data
        )
        
        # Should be 200 (success) not 403 (forbidden)
        assert response.status_code != 403, "Radiologist should be able to create reports"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
