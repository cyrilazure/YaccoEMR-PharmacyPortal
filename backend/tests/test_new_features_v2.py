"""
New Features Testing - Voice Dictation AI Expand, PACS Integration, Interventional Radiology
Tests for:
- POST /api/voice-dictation/ai-expand - AI-powered report auto-generation
- GET /api/voice-dictation/analytics - Usage analytics dashboard
- GET /api/voice-dictation/audit-logs - Audit logging
- GET /api/pacs/config - PACS configuration
- GET /api/pacs/status - PACS connectivity status
- POST /api/pacs/studies/search - PACS study search
- GET /api/pacs/viewer/url - DICOM viewer URL generation
- GET /api/interventional-radiology/dashboard - IR dashboard
- POST /api/interventional-radiology/procedures/create - IR procedure creation
- POST /api/interventional-radiology/pre-assessment/create - IR pre-assessment
- POST /api/interventional-radiology/sedation/record - IR sedation monitoring
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_CREDENTIALS = {
    "radiologist": {"email": "radiologist@yacco.health", "password": "test123"},
    "super_admin": {"email": "ygtnetworks@gmail.com", "password": "test123"}
}


class TestVoiceDictationAIExpand:
    """Voice Dictation AI Expand endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as radiologist for testing
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_CREDENTIALS["radiologist"]
        )
        
        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get("access_token") or data.get("token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                self.authenticated = True
            else:
                self.authenticated = False
        else:
            self.authenticated = False
    
    def test_ai_expand_soap_note(self):
        """Test AI expand for SOAP note format"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        response = self.session.post(
            f"{BASE_URL}/api/voice-dictation/ai-expand",
            params={
                "text": "Patient 45yo male chest pain radiating to left arm, sweating, nausea. BP 150/90, HR 100. ECG shows ST elevation. Suspect MI. Start aspirin, nitro, morphine, call cardiology.",
                "note_type": "soap_note",
                "context": "clinical"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "original_text" in data, "Response should contain original_text"
        assert "expanded_text" in data, "Response should contain expanded_text"
        assert "note_type" in data, "Response should contain note_type"
        assert "word_count" in data, "Response should contain word_count"
        
        # Expanded text should be longer than original
        assert len(data["expanded_text"]) > len(data["original_text"]), "Expanded text should be longer"
        assert data["word_count"] > 10, "Word count should be reasonable"
        
        print(f"✓ AI Expand SOAP note works - expanded to {data['word_count']} words")
    
    def test_ai_expand_radiology_report(self):
        """Test AI expand for radiology report format"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        response = self.session.post(
            f"{BASE_URL}/api/voice-dictation/ai-expand",
            params={
                "text": "Chest CT shows 2cm nodule right upper lobe, no lymphadenopathy, no effusion. Recommend follow-up in 3 months.",
                "note_type": "radiology_report",
                "context": "radiology"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "expanded_text" in data
        assert data["note_type"] == "radiology_report"
        
        print(f"✓ AI Expand radiology report works - expanded to {data['word_count']} words")
    
    def test_ai_expand_progress_note(self):
        """Test AI expand for progress note format"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        response = self.session.post(
            f"{BASE_URL}/api/voice-dictation/ai-expand",
            params={
                "text": "Day 3 post-op appendectomy. Patient doing well, tolerating diet, ambulating. Wound clean. Discharge tomorrow.",
                "note_type": "progress_note",
                "context": "clinical"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "expanded_text" in data
        assert data["note_type"] == "progress_note"
        
        print(f"✓ AI Expand progress note works - expanded to {data['word_count']} words")
    
    def test_ai_expand_nursing_assessment(self):
        """Test AI expand for nursing assessment format"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        response = self.session.post(
            f"{BASE_URL}/api/voice-dictation/ai-expand",
            params={
                "text": "Patient alert, oriented. VS stable. Pain 3/10. IV site clean. Foley draining clear urine. Skin intact.",
                "note_type": "nursing_assessment",
                "context": "nursing"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "expanded_text" in data
        assert data["note_type"] == "nursing_assessment"
        
        print(f"✓ AI Expand nursing assessment works - expanded to {data['word_count']} words")


class TestVoiceDictationAnalytics:
    """Voice Dictation Analytics endpoint tests (admin only)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with admin authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as super_admin for analytics access
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_CREDENTIALS["super_admin"]
        )
        
        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get("access_token") or data.get("token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                self.authenticated = True
            else:
                self.authenticated = False
        else:
            self.authenticated = False
    
    def test_get_analytics(self):
        """Test GET /api/voice-dictation/analytics returns usage stats"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        response = self.session.get(f"{BASE_URL}/api/voice-dictation/analytics")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "summary" in data, "Response should contain summary"
        assert "usage_by_role" in data, "Response should contain usage_by_role"
        assert "usage_by_context" in data, "Response should contain usage_by_context"
        assert "top_users" in data, "Response should contain top_users"
        assert "daily_usage" in data, "Response should contain daily_usage"
        
        # Validate summary structure
        summary = data["summary"]
        assert "total_transcriptions" in summary
        assert "total_duration_minutes" in summary
        assert "total_corrections_made" in summary
        assert "avg_duration_seconds" in summary
        
        print(f"✓ Analytics endpoint works - {summary['total_transcriptions']} total transcriptions")
    
    def test_get_analytics_with_date_filter(self):
        """Test analytics with date filters"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        today = datetime.now().strftime("%Y-%m-%d")
        response = self.session.get(
            f"{BASE_URL}/api/voice-dictation/analytics",
            params={"date_from": today, "date_to": today}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "summary" in data
        
        print(f"✓ Analytics with date filter works")
    
    def test_analytics_requires_admin(self):
        """Test that non-admin users cannot access analytics"""
        # Login as radiologist (non-admin)
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        login_response = session.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_CREDENTIALS["radiologist"]
        )
        
        if login_response.status_code != 200:
            pytest.skip("Radiologist login failed")
        
        data = login_response.json()
        token = data.get("access_token") or data.get("token")
        if token:
            session.headers.update({"Authorization": f"Bearer {token}"})
        
        response = session.get(f"{BASE_URL}/api/voice-dictation/analytics")
        
        # Should return 403 Forbidden for non-admin
        assert response.status_code == 403, f"Expected 403 for non-admin, got {response.status_code}"
        
        print(f"✓ Analytics correctly requires admin access")


class TestVoiceDictationAuditLogs:
    """Voice Dictation Audit Logs endpoint tests (admin only)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with admin authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as super_admin for audit logs access
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_CREDENTIALS["super_admin"]
        )
        
        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get("access_token") or data.get("token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                self.authenticated = True
            else:
                self.authenticated = False
        else:
            self.authenticated = False
    
    def test_get_audit_logs(self):
        """Test GET /api/voice-dictation/audit-logs returns logs"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        response = self.session.get(f"{BASE_URL}/api/voice-dictation/audit-logs")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "logs" in data, "Response should contain logs"
        assert "total" in data, "Response should contain total"
        assert "limit" in data, "Response should contain limit"
        assert "skip" in data, "Response should contain skip"
        
        assert isinstance(data["logs"], list), "logs should be a list"
        
        print(f"✓ Audit logs endpoint works - {data['total']} total logs")
    
    def test_get_audit_logs_with_pagination(self):
        """Test audit logs with pagination"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        response = self.session.get(
            f"{BASE_URL}/api/voice-dictation/audit-logs",
            params={"limit": 10, "skip": 0}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["limit"] == 10
        assert data["skip"] == 0
        
        print(f"✓ Audit logs pagination works")
    
    def test_audit_logs_requires_admin(self):
        """Test that non-admin users cannot access audit logs"""
        # Login as radiologist (non-admin)
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        login_response = session.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_CREDENTIALS["radiologist"]
        )
        
        if login_response.status_code != 200:
            pytest.skip("Radiologist login failed")
        
        data = login_response.json()
        token = data.get("access_token") or data.get("token")
        if token:
            session.headers.update({"Authorization": f"Bearer {token}"})
        
        response = session.get(f"{BASE_URL}/api/voice-dictation/audit-logs")
        
        # Should return 403 Forbidden for non-admin
        assert response.status_code == 403, f"Expected 403 for non-admin, got {response.status_code}"
        
        print(f"✓ Audit logs correctly requires admin access")


class TestPACSIntegration:
    """PACS/DICOM Integration endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as radiologist for testing
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_CREDENTIALS["radiologist"]
        )
        
        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get("access_token") or data.get("token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                self.authenticated = True
            else:
                self.authenticated = False
        else:
            self.authenticated = False
    
    def test_get_pacs_config(self):
        """Test GET /api/pacs/config returns configuration"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        response = self.session.get(f"{BASE_URL}/api/pacs/config")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "pacs_host" in data, "Response should contain pacs_host"
        assert "pacs_port" in data, "Response should contain pacs_port"
        assert "ae_title" in data, "Response should contain ae_title"
        assert "wado_url" in data, "Response should contain wado_url"
        assert "is_configured" in data, "Response should contain is_configured"
        assert "status" in data, "Response should contain status"
        
        # In demo mode, status should be demo_mode
        print(f"✓ PACS config endpoint works - status: {data['status']}")
    
    def test_get_pacs_status(self):
        """Test GET /api/pacs/status checks connectivity"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        response = self.session.get(f"{BASE_URL}/api/pacs/status")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "status" in data, "Response should contain status"
        assert "server" in data, "Response should contain server"
        
        # In demo mode, status will be disconnected (no real PACS server)
        print(f"✓ PACS status endpoint works - status: {data['status']}")
    
    def test_search_studies(self):
        """Test POST /api/pacs/studies/search returns studies"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        response = self.session.post(
            f"{BASE_URL}/api/pacs/studies/search",
            json={
                "limit": 10
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "studies" in data, "Response should contain studies"
        assert "total" in data, "Response should contain total"
        assert "mode" in data, "Response should contain mode"
        
        # In demo mode, should return demo studies
        assert data["mode"] == "demo", "Should be in demo mode"
        
        print(f"✓ PACS study search works - {data['total']} studies found (demo mode)")
    
    def test_search_studies_with_filters(self):
        """Test PACS study search with filters"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        response = self.session.post(
            f"{BASE_URL}/api/pacs/studies/search",
            json={
                "modality": "CT",
                "limit": 5
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "studies" in data
        
        print(f"✓ PACS study search with filters works")
    
    def test_get_viewer_url(self):
        """Test GET /api/pacs/viewer/url generates viewer URL"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        test_study_uid = "1.2.840.10008.5.1.4.1.1.2.1"
        
        response = self.session.get(
            f"{BASE_URL}/api/pacs/viewer/url",
            params={"study_uid": test_study_uid}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "status" in data, "Response should contain status"
        
        # If viewer not configured, should return demo info
        if data["status"] == "not_configured":
            assert "demo_viewer_info" in data, "Should contain demo viewer info"
        
        print(f"✓ PACS viewer URL endpoint works - status: {data['status']}")


class TestInterventionalRadiology:
    """Interventional Radiology Module endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as radiologist for testing
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_CREDENTIALS["radiologist"]
        )
        
        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get("access_token") or data.get("token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                self.authenticated = True
                self.user_id = data.get("user", {}).get("id", "test-user")
            else:
                self.authenticated = False
        else:
            self.authenticated = False
    
    def test_get_ir_dashboard(self):
        """Test GET /api/interventional-radiology/dashboard returns schedule"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        response = self.session.get(f"{BASE_URL}/api/interventional-radiology/dashboard")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "today_schedule" in data, "Response should contain today_schedule"
        assert "today_count" in data, "Response should contain today_count"
        assert "status_counts" in data, "Response should contain status_counts"
        assert "in_progress" in data, "Response should contain in_progress"
        assert "in_recovery" in data, "Response should contain in_recovery"
        
        print(f"✓ IR dashboard works - {data['today_count']} procedures today")
    
    def test_create_ir_procedure(self):
        """Test POST /api/interventional-radiology/procedures/create"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        procedure_data = {
            "patient_id": f"TEST_patient_{uuid.uuid4().hex[:8]}",
            "patient_name": "TEST John Doe",
            "patient_mrn": f"MRN{uuid.uuid4().hex[:8].upper()}",
            "procedure_type": "biopsy",
            "procedure_description": "CT-guided liver biopsy",
            "indication": "Liver mass evaluation",
            "laterality": "right",
            "scheduled_date": today,
            "scheduled_time": "10:00",
            "estimated_duration_minutes": 45,
            "sedation_required": "moderate",
            "contrast_required": True,
            "special_equipment": ["biopsy needle", "CT guidance"],
            "attending_physician_id": self.user_id,
            "attending_physician_name": "Dr. Test Radiologist",
            "notes": "Patient on anticoagulation - held for 5 days"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/interventional-radiology/procedures/create",
            json=procedure_data
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        assert "procedure" in data, "Response should contain procedure"
        
        procedure = data["procedure"]
        assert "id" in procedure, "Procedure should have id"
        assert "case_number" in procedure, "Procedure should have case_number"
        assert procedure["procedure_type"] == "biopsy"
        assert procedure["status"] == "scheduled"
        
        # Store procedure_id for subsequent tests
        self.procedure_id = procedure["id"]
        
        print(f"✓ IR procedure creation works - case: {procedure['case_number']}")
        
        return procedure["id"]
    
    def test_create_pre_assessment(self):
        """Test POST /api/interventional-radiology/pre-assessment/create"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        # First create a procedure
        procedure_id = self.test_create_ir_procedure()
        
        assessment_data = {
            "procedure_id": procedure_id,
            "allergies_reviewed": True,
            "allergies_notes": "NKDA",
            "medications_reviewed": True,
            "anticoagulants": ["warfarin"],
            "anticoagulant_held": True,
            "last_dose_date": "2024-01-01",
            "labs_reviewed": True,
            "inr": 1.2,
            "platelets": 250000,
            "creatinine": 1.0,
            "egfr": 90,
            "consent_obtained": True,
            "consent_date": datetime.now().strftime("%Y-%m-%d"),
            "consent_by": "Dr. Test",
            "npo_status": True,
            "npo_since": "midnight",
            "iv_access": True,
            "iv_gauge": "20G",
            "assessment_notes": "Patient cleared for procedure"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/interventional-radiology/pre-assessment/create",
            json=assessment_data
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        assert "assessment" in data, "Response should contain assessment"
        
        assessment = data["assessment"]
        assert assessment["procedure_id"] == procedure_id
        assert assessment["consent_obtained"] == True
        
        print(f"✓ IR pre-assessment creation works")
    
    def test_record_sedation_vitals(self):
        """Test POST /api/interventional-radiology/sedation/record"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        # First create a procedure
        procedure_id = self.test_create_ir_procedure()
        
        sedation_data = {
            "procedure_id": procedure_id,
            "timestamp": datetime.now().isoformat(),
            "heart_rate": 72,
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80,
            "respiratory_rate": 16,
            "oxygen_saturation": 98,
            "sedation_level": "drowsy",
            "medications_given": [
                {"name": "Midazolam", "dose": "2mg", "route": "IV", "time": "10:00"}
            ],
            "notes": "Patient comfortable"
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/interventional-radiology/sedation/record",
            json=sedation_data
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data, "Response should contain message"
        assert "record" in data, "Response should contain record"
        
        record = data["record"]
        assert record["procedure_id"] == procedure_id
        assert record["heart_rate"] == 72
        assert record["oxygen_saturation"] == 98
        
        print(f"✓ IR sedation monitoring works")
    
    def test_get_ir_procedures(self):
        """Test GET /api/interventional-radiology/procedures"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        response = self.session.get(f"{BASE_URL}/api/interventional-radiology/procedures")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "procedures" in data, "Response should contain procedures"
        assert "total" in data, "Response should contain total"
        
        print(f"✓ IR procedures list works - {data['total']} procedures")
    
    def test_get_ir_procedures_with_filters(self):
        """Test IR procedures with status filter"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        response = self.session.get(
            f"{BASE_URL}/api/interventional-radiology/procedures",
            params={"status": "scheduled"}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "procedures" in data
        
        print(f"✓ IR procedures with filter works")


class TestPACSHL7Workflows:
    """PACS HL7 Workflow endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session with authentication"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as radiologist for testing
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_CREDENTIALS["radiologist"]
        )
        
        if login_response.status_code == 200:
            data = login_response.json()
            token = data.get("access_token") or data.get("token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                self.authenticated = True
            else:
                self.authenticated = False
        else:
            self.authenticated = False
    
    def test_send_hl7_adt(self):
        """Test POST /api/pacs/hl7/adt sends ADT message"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        adt_data = {
            "message_type": "ADT",
            "patient_id": f"TEST_{uuid.uuid4().hex[:8]}",
            "patient_name": "TEST Patient ADT",
            "event_type": "A04"  # Patient Registration
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/pacs/hl7/adt",
            json=adt_data
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message_id" in data, "Response should contain message_id"
        assert "status" in data, "Response should contain status"
        assert "event_type" in data, "Response should contain event_type"
        
        print(f"✓ HL7 ADT message works - status: {data['status']}")
    
    def test_send_hl7_orm(self):
        """Test POST /api/pacs/hl7/orm sends ORM message"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        orm_data = {
            "message_type": "ORM",
            "patient_id": f"TEST_{uuid.uuid4().hex[:8]}",
            "patient_name": "TEST Patient ORM",
            "order_data": {
                "order_id": f"ORD-{uuid.uuid4().hex[:8]}",
                "procedure": "CT Chest",
                "priority": "routine"
            }
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/pacs/hl7/orm",
            json=orm_data
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message_id" in data, "Response should contain message_id"
        assert "status" in data, "Response should contain status"
        
        print(f"✓ HL7 ORM message works - status: {data['status']}")
    
    def test_receive_hl7_oru(self):
        """Test POST /api/pacs/hl7/oru receives ORU message"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        oru_data = {
            "message_type": "ORU",
            "patient_id": f"TEST_{uuid.uuid4().hex[:8]}",
            "patient_name": "TEST Patient ORU",
            "result_data": {
                "accession_number": f"ACC-{uuid.uuid4().hex[:8]}",
                "study_status": "completed",
                "report_status": "final"
            }
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/pacs/hl7/oru",
            json=oru_data
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message_id" in data, "Response should contain message_id"
        assert "status" in data, "Response should contain status"
        
        print(f"✓ HL7 ORU message works - status: {data['status']}")
    
    def test_get_modality_worklist(self):
        """Test GET /api/pacs/worklist returns MWL"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        response = self.session.get(f"{BASE_URL}/api/pacs/worklist")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "worklist" in data, "Response should contain worklist"
        assert "total" in data, "Response should contain total"
        assert "ae_title" in data, "Response should contain ae_title"
        
        print(f"✓ Modality worklist works - {data['total']} items")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
