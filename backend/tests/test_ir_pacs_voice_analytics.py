"""
Test Suite for IR Portal, PACS Integration, and Voice Dictation Analytics
Tests the new features:
- Interventional Radiology Portal (Dashboard, Status Board, Procedures)
- PACS/DICOM Integration (Config, Status, Study Search)
- Voice Dictation Analytics (Overview, Top Users, Audit Logs)
"""

import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
RADIOLOGIST_EMAIL = "radiologist@yacco.health"
RADIOLOGIST_PASSWORD = "test123"
ADMIN_EMAIL = "it_admin@yacco.health"  # hospital_it_admin has access to voice analytics
ADMIN_PASSWORD = "test123"


class TestAuthentication:
    """Test authentication for different user roles"""
    
    def test_radiologist_login(self):
        """Test radiologist login flow"""
        # Step 1: Get regions (note: API returns {"regions": [...]} format)
        response = requests.get(f"{BASE_URL}/api/regions/")
        assert response.status_code == 200
        data = response.json()
        regions = data.get("regions", [])
        assert len(regions) > 0
        print(f"SUCCESS: Found {len(regions)} regions")
        
        # Find Greater Accra Region
        greater_accra = next((r for r in regions if "Greater Accra" in r.get("name", "")), None)
        assert greater_accra is not None, "Greater Accra Region not found"
        region_id = greater_accra.get("id")
        print(f"SUCCESS: Found Greater Accra Region: {region_id}")
        
        # Step 2: Get hospitals in region
        response = requests.get(f"{BASE_URL}/api/regions/{region_id}/hospitals")
        assert response.status_code == 200
        hospitals_data = response.json()
        hospitals = hospitals_data.get("hospitals", [])
        assert len(hospitals) > 0
        print(f"SUCCESS: Found {len(hospitals)} hospitals in Greater Accra")
        
        # Find ygtworks Health Center
        hospital = next((h for h in hospitals if "ygtworks" in h.get("name", "").lower()), None)
        if not hospital:
            hospital = hospitals[0]  # Use first hospital if ygtworks not found
        hospital_id = hospital.get("id")
        print(f"SUCCESS: Using hospital: {hospital.get('name')}")
        
        # Step 3: Login
        login_data = {
            "email": RADIOLOGIST_EMAIL,
            "password": RADIOLOGIST_PASSWORD,
            "hospital_id": hospital_id
        }
        response = requests.post(f"{BASE_URL}/api/regions/auth/login", json=login_data)
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["role"] == "radiologist"
        print(f"SUCCESS: Radiologist logged in - {data['user']['first_name']} {data['user']['last_name']}")
        return data["token"], hospital_id
    
    def test_super_admin_login(self):
        """Test super admin login flow"""
        # Step 1: Get regions
        response = requests.get(f"{BASE_URL}/api/regions/")
        assert response.status_code == 200
        data = response.json()
        regions = data.get("regions", [])
        
        # Find Greater Accra Region
        greater_accra = next((r for r in regions if "Greater Accra" in r.get("name", "")), None)
        assert greater_accra is not None
        region_id = greater_accra.get("id")
        
        # Step 2: Get hospitals
        response = requests.get(f"{BASE_URL}/api/regions/{region_id}/hospitals")
        assert response.status_code == 200
        hospitals_data = response.json()
        hospitals = hospitals_data.get("hospitals", [])
        hospital = next((h for h in hospitals if "ygtworks" in h.get("name", "").lower()), hospitals[0])
        hospital_id = hospital.get("id")
        
        # Step 3: Login
        login_data = {
            "email": SUPER_ADMIN_EMAIL,
            "password": SUPER_ADMIN_PASSWORD,
            "hospital_id": hospital_id
        }
        response = requests.post(f"{BASE_URL}/api/regions/auth/login", json=login_data)
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert data["user"]["role"] == "super_admin"
        print(f"SUCCESS: Super Admin logged in - {data['user']['first_name']} {data['user']['last_name']}")
        return data["token"], hospital_id


@pytest.fixture(scope="module")
def radiologist_auth():
    """Get radiologist authentication token"""
    test = TestAuthentication()
    return test.test_radiologist_login()


@pytest.fixture(scope="module")
def admin_auth():
    """Get super admin authentication token"""
    test = TestAuthentication()
    return test.test_super_admin_login()


class TestInterventionalRadiologyDashboard:
    """Test IR Dashboard endpoints"""
    
    def test_ir_dashboard(self, radiologist_auth):
        """Test IR dashboard endpoint"""
        token, _ = radiologist_auth
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/interventional-radiology/dashboard", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify dashboard structure
        assert "today_schedule" in data
        assert "today_count" in data
        assert "status_counts" in data
        assert "in_progress" in data
        assert "in_recovery" in data
        
        print(f"SUCCESS: IR Dashboard - Today's count: {data['today_count']}, Status counts: {data['status_counts']}")
    
    def test_ir_procedures_list(self, radiologist_auth):
        """Test IR procedures list endpoint"""
        token, _ = radiologist_auth
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/interventional-radiology/procedures", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "procedures" in data
        assert "total" in data
        print(f"SUCCESS: IR Procedures - Total: {data['total']}")
    
    def test_create_ir_procedure(self, radiologist_auth):
        """Test creating a new IR procedure"""
        token, _ = radiologist_auth
        headers = {"Authorization": f"Bearer {token}"}
        
        procedure_data = {
            "patient_id": "TEST_PATIENT_001",
            "patient_name": "TEST John Doe",
            "patient_mrn": "TEST_MRN_001",
            "procedure_type": "angiography",
            "procedure_description": "TEST Diagnostic Angiography",
            "indication": "Suspected peripheral artery disease",
            "laterality": "right",
            "scheduled_date": datetime.now().strftime("%Y-%m-%d"),
            "scheduled_time": "14:00",
            "estimated_duration_minutes": 90,
            "sedation_required": "moderate",
            "contrast_required": True,
            "attending_physician_id": "test_physician",
            "attending_physician_name": "Dr. Test Radiologist",
            "notes": "TEST procedure for automated testing"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/interventional-radiology/procedures/create",
            json=procedure_data,
            headers=headers
        )
        assert response.status_code == 200, f"Failed to create procedure: {response.text}"
        data = response.json()
        
        assert "procedure" in data
        assert "case_number" in data["procedure"]
        assert data["procedure"]["patient_name"] == "TEST John Doe"
        print(f"SUCCESS: Created IR Procedure - Case: {data['procedure']['case_number']}")
        return data["procedure"]["id"]
    
    def test_get_ir_procedure_details(self, radiologist_auth):
        """Test getting IR procedure details"""
        token, _ = radiologist_auth
        headers = {"Authorization": f"Bearer {token}"}
        
        # First create a procedure
        procedure_id = self.test_create_ir_procedure(radiologist_auth)
        
        # Get details
        response = requests.get(
            f"{BASE_URL}/api/interventional-radiology/procedures/{procedure_id}",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "procedure" in data
        assert data["procedure"]["id"] == procedure_id
        print(f"SUCCESS: Got IR Procedure details for {procedure_id}")
    
    def test_update_procedure_status(self, radiologist_auth):
        """Test updating IR procedure status"""
        token, _ = radiologist_auth
        headers = {"Authorization": f"Bearer {token}"}
        
        # First create a procedure
        procedure_id = self.test_create_ir_procedure(radiologist_auth)
        
        # Update status to pre_procedure
        response = requests.put(
            f"{BASE_URL}/api/interventional-radiology/procedures/{procedure_id}/status",
            params={"status": "pre_procedure"},
            headers=headers
        )
        assert response.status_code == 200
        print(f"SUCCESS: Updated procedure status to pre_procedure")
    
    def test_create_pre_assessment(self, radiologist_auth):
        """Test creating pre-procedure assessment"""
        token, _ = radiologist_auth
        headers = {"Authorization": f"Bearer {token}"}
        
        # First create a procedure
        procedure_id = self.test_create_ir_procedure(radiologist_auth)
        
        assessment_data = {
            "procedure_id": procedure_id,
            "allergies_reviewed": True,
            "allergies_notes": "No known allergies",
            "medications_reviewed": True,
            "anticoagulants": ["aspirin"],
            "anticoagulant_held": True,
            "last_dose_date": "2025-01-05",
            "labs_reviewed": True,
            "inr": 1.1,
            "platelets": 250000,
            "creatinine": 0.9,
            "egfr": 90,
            "consent_obtained": True,
            "consent_date": datetime.now().strftime("%Y-%m-%d"),
            "npo_status": True,
            "npo_since": "midnight",
            "iv_access": True,
            "iv_gauge": "18G",
            "assessment_notes": "Patient ready for procedure"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/interventional-radiology/pre-assessment/create",
            json=assessment_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "assessment" in data
        print(f"SUCCESS: Created pre-procedure assessment")
    
    def test_record_sedation_vitals(self, radiologist_auth):
        """Test recording sedation monitoring vitals"""
        token, _ = radiologist_auth
        headers = {"Authorization": f"Bearer {token}"}
        
        # First create a procedure
        procedure_id = self.test_create_ir_procedure(radiologist_auth)
        
        vitals_data = {
            "procedure_id": procedure_id,
            "timestamp": datetime.now().isoformat(),
            "heart_rate": 72,
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80,
            "respiratory_rate": 16,
            "oxygen_saturation": 98,
            "sedation_level": "drowsy",
            "notes": "Patient comfortable"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/interventional-radiology/sedation/record",
            json=vitals_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "record" in data
        print(f"SUCCESS: Recorded sedation vitals")
    
    def test_get_sedation_records(self, radiologist_auth):
        """Test getting sedation records for a procedure"""
        token, _ = radiologist_auth
        headers = {"Authorization": f"Bearer {token}"}
        
        # First create a procedure and record vitals
        procedure_id = self.test_create_ir_procedure(radiologist_auth)
        
        # Record some vitals
        vitals_data = {
            "procedure_id": procedure_id,
            "timestamp": datetime.now().isoformat(),
            "heart_rate": 75,
            "blood_pressure_systolic": 118,
            "blood_pressure_diastolic": 78,
            "respiratory_rate": 14,
            "oxygen_saturation": 99,
            "sedation_level": "alert"
        }
        requests.post(
            f"{BASE_URL}/api/interventional-radiology/sedation/record",
            json=vitals_data,
            headers=headers
        )
        
        # Get records
        response = requests.get(
            f"{BASE_URL}/api/interventional-radiology/sedation/{procedure_id}",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "records" in data
        assert "total" in data
        print(f"SUCCESS: Got {data['total']} sedation records")


class TestPACSIntegration:
    """Test PACS/DICOM Integration endpoints"""
    
    def test_pacs_config(self, radiologist_auth):
        """Test PACS configuration endpoint"""
        token, _ = radiologist_auth
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/pacs/config", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify config structure
        assert "pacs_host" in data
        assert "pacs_port" in data
        assert "ae_title" in data
        assert "status" in data
        
        print(f"SUCCESS: PACS Config - Host: {data['pacs_host']}, Status: {data['status']}")
    
    def test_pacs_status(self, radiologist_auth):
        """Test PACS status endpoint"""
        token, _ = radiologist_auth
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/pacs/status", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        print(f"SUCCESS: PACS Status - {data['status']}")
    
    def test_pacs_study_search(self, radiologist_auth):
        """Test PACS study search endpoint"""
        token, _ = radiologist_auth
        headers = {"Authorization": f"Bearer {token}"}
        
        search_data = {
            "patient_id": "",
            "patient_name": "",
            "accession_number": "",
            "modality": None,
            "limit": 10
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pacs/studies/search",
            json=search_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "studies" in data
        assert "mode" in data
        print(f"SUCCESS: PACS Study Search - Mode: {data['mode']}, Studies: {len(data['studies'])}")
    
    def test_pacs_viewer_url(self, radiologist_auth):
        """Test PACS viewer URL generation"""
        token, _ = radiologist_auth
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/pacs/viewer/url",
            params={
                "study_uid": "1.2.840.113619.2.5.1762583153.215519.978957063.121",
                "accession_number": "ACC001",
                "patient_id": "DEMO001"
            },
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        print(f"SUCCESS: PACS Viewer URL - Status: {data['status']}")
    
    def test_pacs_worklist(self, radiologist_auth):
        """Test PACS modality worklist"""
        token, _ = radiologist_auth
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/pacs/worklist", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "worklist" in data
        assert "total" in data
        print(f"SUCCESS: PACS Worklist - Total: {data['total']}")
    
    def test_pacs_hl7_adt(self, radiologist_auth):
        """Test PACS HL7 ADT message"""
        token, _ = radiologist_auth
        headers = {"Authorization": f"Bearer {token}"}
        
        adt_data = {
            "message_type": "ADT",
            "patient_id": "TEST_PATIENT_002",
            "patient_name": "TEST Jane Smith",
            "event_type": "A04"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pacs/hl7/adt",
            json=adt_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "message_id" in data
        assert "status" in data
        print(f"SUCCESS: HL7 ADT - Message ID: {data['message_id']}, Status: {data['status']}")
    
    def test_pacs_hl7_orm(self, radiologist_auth):
        """Test PACS HL7 ORM (Order) message"""
        token, _ = radiologist_auth
        headers = {"Authorization": f"Bearer {token}"}
        
        orm_data = {
            "message_type": "ORM",
            "patient_id": "TEST_PATIENT_002",
            "patient_name": "TEST Jane Smith",
            "order_data": {
                "order_id": "TEST_ORDER_001",
                "procedure": "CT Chest",
                "priority": "routine"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/pacs/hl7/orm",
            json=orm_data,
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "message_id" in data
        print(f"SUCCESS: HL7 ORM - Message ID: {data['message_id']}")


class TestVoiceDictationAnalytics:
    """Test Voice Dictation Analytics endpoints (Admin only)"""
    
    def test_voice_analytics_admin_access(self, admin_auth):
        """Test voice analytics with admin access"""
        token, _ = admin_auth
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/voice-dictation/analytics", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify analytics structure
        assert "summary" in data
        assert "usage_by_role" in data
        assert "usage_by_context" in data
        assert "top_users" in data
        assert "daily_usage" in data
        
        summary = data["summary"]
        print(f"SUCCESS: Voice Analytics - Total transcriptions: {summary.get('total_transcriptions', 0)}, Duration: {summary.get('total_duration_minutes', 0)} min")
    
    def test_voice_analytics_non_admin_denied(self, radiologist_auth):
        """Test voice analytics denied for non-admin"""
        token, _ = radiologist_auth
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/voice-dictation/analytics", headers=headers)
        assert response.status_code == 403, "Non-admin should be denied access to analytics"
        print(f"SUCCESS: Voice Analytics correctly denied for non-admin (403)")
    
    def test_voice_audit_logs_admin_access(self, admin_auth):
        """Test voice audit logs with admin access"""
        token, _ = admin_auth
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/voice-dictation/audit-logs",
            params={"limit": 10, "skip": 0},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "logs" in data
        assert "total" in data
        print(f"SUCCESS: Voice Audit Logs - Total: {data['total']}, Retrieved: {len(data['logs'])}")
    
    def test_voice_audit_logs_non_admin_denied(self, radiologist_auth):
        """Test voice audit logs denied for non-admin"""
        token, _ = radiologist_auth
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{BASE_URL}/api/voice-dictation/audit-logs", headers=headers)
        assert response.status_code == 403, "Non-admin should be denied access to audit logs"
        print(f"SUCCESS: Voice Audit Logs correctly denied for non-admin (403)")
    
    def test_voice_analytics_with_date_filter(self, admin_auth):
        """Test voice analytics with date filter"""
        token, _ = admin_auth
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/voice-dictation/analytics",
            params={
                "date_from": "2025-01-01",
                "date_to": "2025-12-31"
            },
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        print(f"SUCCESS: Voice Analytics with date filter works")
    
    def test_voice_audit_logs_with_context_filter(self, admin_auth):
        """Test voice audit logs with context filter"""
        token, _ = admin_auth
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/voice-dictation/audit-logs",
            params={"context": "radiology", "limit": 10},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        print(f"SUCCESS: Voice Audit Logs with context filter - Retrieved: {len(data['logs'])}")


class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_procedures(self, radiologist_auth):
        """Cleanup TEST_ prefixed procedures"""
        token, _ = radiologist_auth
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get all procedures
        response = requests.get(
            f"{BASE_URL}/api/interventional-radiology/procedures",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            test_procedures = [p for p in data.get("procedures", []) if "TEST" in p.get("patient_name", "")]
            print(f"INFO: Found {len(test_procedures)} TEST procedures to cleanup")
        print("SUCCESS: Cleanup check completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
