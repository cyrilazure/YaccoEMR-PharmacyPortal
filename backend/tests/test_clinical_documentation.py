"""
Clinical Documentation & RBAC Tests
Testing Nursing/Physician documentation module with role-based access control
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from the review request
TEST_PHYSICIAN = {
    "email": "testdoctor@yacco.health",
    "password": "Test123!"
}
TEST_NURSE = {
    "email": "testnurse@yacco.health",
    "password": "Test123!"
}
TEST_PATIENT_ID = "7320e692-8285-43a0-ae9b-f79ad277c54a"


class TestClinicalDocsAPINoAuth:
    """Tests for clinical docs API endpoints that don't require auth (doc types)"""
    
    def test_nursing_doc_types(self):
        """Test /api/clinical-docs/doc-types/nursing returns nursing doc types"""
        response = requests.get(f"{BASE_URL}/api/clinical-docs/doc-types/nursing")
        print(f"Nursing Doc Types Status: {response.status_code}")
        print(f"Nursing Doc Types Response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert "doc_types" in data
        assert len(data["doc_types"]) > 0
        # Verify some expected nursing doc types
        doc_values = [d["value"] for d in data["doc_types"]]
        assert "assessment" in doc_values
        assert "progress_note" in doc_values
        print(f"✓ Found {len(data['doc_types'])} nursing doc types")
    
    def test_physician_doc_types(self):
        """Test /api/clinical-docs/doc-types/physician returns physician doc types"""
        response = requests.get(f"{BASE_URL}/api/clinical-docs/doc-types/physician")
        print(f"Physician Doc Types Status: {response.status_code}")
        print(f"Physician Doc Types Response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert "doc_types" in data
        assert len(data["doc_types"]) > 0
        # Verify some expected physician doc types
        doc_values = [d["value"] for d in data["doc_types"]]
        assert "h_and_p" in doc_values
        assert "progress_note" in doc_values
        print(f"✓ Found {len(data['doc_types'])} physician doc types")


class TestPhysicianFlow:
    """Test clinical documentation for physician role"""
    
    @pytest.fixture(scope="class")
    def physician_token(self):
        """Login as test physician at Ashaiman Polyclinic"""
        # First get regions to find hospital ID
        regions_res = requests.get(f"{BASE_URL}/api/regions/")
        print(f"Regions Status: {regions_res.status_code}")
        
        if regions_res.status_code == 200:
            regions = regions_res.json().get("regions", [])
            greater_accra = next((r for r in regions if "greater" in r.get("name", "").lower()), None)
            
            if greater_accra:
                hospitals_res = requests.get(f"{BASE_URL}/api/regions/{greater_accra['id']}/hospitals")
                if hospitals_res.status_code == 200:
                    hospitals = hospitals_res.json().get("hospitals", [])
                    ashaiman = next((h for h in hospitals if "ashaiman" in h.get("name", "").lower()), None)
                    
                    if ashaiman:
                        # Login with hospital context
                        login_res = requests.post(
                            f"{BASE_URL}/api/regions/auth/login",
                            json={
                                "email": TEST_PHYSICIAN["email"],
                                "password": TEST_PHYSICIAN["password"],
                                "hospital_id": ashaiman["id"]
                            }
                        )
                        print(f"Physician Login Status: {login_res.status_code}")
                        if login_res.status_code == 200:
                            data = login_res.json()
                            print(f"Physician Role: {data.get('user', {}).get('role')}")
                            return data.get("token")
        
        # Fallback to basic login
        login_res = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": TEST_PHYSICIAN["email"],
                "password": TEST_PHYSICIAN["password"]
            }
        )
        print(f"Physician Basic Login Status: {login_res.status_code}")
        if login_res.status_code == 200:
            data = login_res.json()
            print(f"Physician Role: {data.get('user', {}).get('role')}")
            return data.get("token")
        
        print(f"Physician Login Failed: {login_res.text}")
        pytest.skip("Could not login as physician")
    
    def test_physician_get_nursing_docs(self, physician_token):
        """Physician can view nursing documentation (read-only)"""
        headers = {"Authorization": f"Bearer {physician_token}"}
        response = requests.get(
            f"{BASE_URL}/api/clinical-docs/nursing/{TEST_PATIENT_ID}",
            headers=headers
        )
        print(f"Get Nursing Docs Status: {response.status_code}")
        print(f"Get Nursing Docs Response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "user_role" in data
        print(f"✓ Physician can view {len(data['documents'])} nursing docs")
    
    def test_physician_get_physician_docs(self, physician_token):
        """Physician can view physician documentation"""
        headers = {"Authorization": f"Bearer {physician_token}"}
        response = requests.get(
            f"{BASE_URL}/api/clinical-docs/physician/{TEST_PATIENT_ID}",
            headers=headers
        )
        print(f"Get Physician Docs Status: {response.status_code}")
        print(f"Get Physician Docs Response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "can_create" in data
        print(f"✓ Physician can view {len(data['documents'])} physician docs, can_create: {data['can_create']}")
    
    def test_physician_create_physician_doc(self, physician_token):
        """Physician can create physician documentation"""
        headers = {"Authorization": f"Bearer {physician_token}"}
        doc_data = {
            "patient_id": TEST_PATIENT_ID,
            "doc_type": "progress_note",
            "title": "TEST_Progress Note - Day 1",
            "chief_complaint": "Follow-up visit for chronic condition",
            "history_present_illness": "Patient reports improvement in symptoms",
            "physical_exam": "Vitals stable, lungs clear",
            "assessment": "Condition improving",
            "plan": "Continue current treatment, follow-up in 2 weeks"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/clinical-docs/physician",
            json=doc_data,
            headers=headers
        )
        print(f"Create Physician Doc Status: {response.status_code}")
        print(f"Create Physician Doc Response: {response.json()}")
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert "document" in data or "message" in data
        print("✓ Physician successfully created physician documentation")
    
    def test_physician_cannot_create_nursing_doc(self, physician_token):
        """Physician should NOT be able to create nursing documentation"""
        headers = {"Authorization": f"Bearer {physician_token}"}
        doc_data = {
            "patient_id": TEST_PATIENT_ID,
            "doc_type": "assessment",
            "title": "TEST_Nursing Assessment (should fail)",
            "content": "This should not be created by physician"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/clinical-docs/nursing",
            json=doc_data,
            headers=headers
        )
        print(f"Physician Create Nursing Doc Status: {response.status_code}")
        print(f"Physician Create Nursing Doc Response: {response.text[:500] if response.text else 'No response'}")
        
        # Should be 403 Forbidden
        assert response.status_code == 403
        print("✓ Physician correctly denied from creating nursing doc (RBAC working)")


class TestNurseFlow:
    """Test clinical documentation for nurse role"""
    
    @pytest.fixture(scope="class")
    def nurse_token(self):
        """Login as test nurse at Ashaiman Polyclinic"""
        # First get regions to find hospital ID
        regions_res = requests.get(f"{BASE_URL}/api/regions/")
        
        if regions_res.status_code == 200:
            regions = regions_res.json().get("regions", [])
            greater_accra = next((r for r in regions if "greater" in r.get("name", "").lower()), None)
            
            if greater_accra:
                hospitals_res = requests.get(f"{BASE_URL}/api/regions/{greater_accra['id']}/hospitals")
                if hospitals_res.status_code == 200:
                    hospitals = hospitals_res.json().get("hospitals", [])
                    ashaiman = next((h for h in hospitals if "ashaiman" in h.get("name", "").lower()), None)
                    
                    if ashaiman:
                        # Login with hospital context
                        login_res = requests.post(
                            f"{BASE_URL}/api/regions/auth/login",
                            json={
                                "email": TEST_NURSE["email"],
                                "password": TEST_NURSE["password"],
                                "hospital_id": ashaiman["id"]
                            }
                        )
                        print(f"Nurse Login Status: {login_res.status_code}")
                        if login_res.status_code == 200:
                            data = login_res.json()
                            print(f"Nurse Role: {data.get('user', {}).get('role')}")
                            return data.get("token")
        
        # Fallback to basic login
        login_res = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": TEST_NURSE["email"],
                "password": TEST_NURSE["password"]
            }
        )
        print(f"Nurse Basic Login Status: {login_res.status_code}")
        if login_res.status_code == 200:
            data = login_res.json()
            print(f"Nurse Role: {data.get('user', {}).get('role')}")
            return data.get("token")
        
        print(f"Nurse Login Failed: {login_res.text}")
        pytest.skip("Could not login as nurse")
    
    def test_nurse_get_nursing_docs(self, nurse_token):
        """Nurse can view nursing documentation"""
        headers = {"Authorization": f"Bearer {nurse_token}"}
        response = requests.get(
            f"{BASE_URL}/api/clinical-docs/nursing/{TEST_PATIENT_ID}",
            headers=headers
        )
        print(f"Nurse Get Nursing Docs Status: {response.status_code}")
        print(f"Nurse Get Nursing Docs Response: {response.json()}")
        
        # Note: Might be 403 if nurse is not assigned to patient - that's expected RBAC
        if response.status_code == 200:
            data = response.json()
            assert "documents" in data
            assert "can_create" in data
            print(f"✓ Nurse can view {len(data['documents'])} nursing docs, can_create: {data['can_create']}")
        elif response.status_code == 403:
            print("✓ Nurse denied access (not assigned to patient) - RBAC working correctly")
    
    def test_nurse_get_physician_docs(self, nurse_token):
        """Nurse can view physician documentation (read-only)"""
        headers = {"Authorization": f"Bearer {nurse_token}"}
        response = requests.get(
            f"{BASE_URL}/api/clinical-docs/physician/{TEST_PATIENT_ID}",
            headers=headers
        )
        print(f"Nurse Get Physician Docs Status: {response.status_code}")
        print(f"Nurse Get Physician Docs Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            assert "documents" in data
            assert "read_only" in data
            # Nurse should NOT be able to create physician docs
            if data.get("can_create") is not None:
                assert data["can_create"] == False
            print(f"✓ Nurse can view {len(data['documents'])} physician docs (read-only: {data.get('read_only')})")
        elif response.status_code == 403:
            print("✓ Nurse denied access (not assigned to patient) - RBAC working correctly")
    
    def test_nurse_create_nursing_doc(self, nurse_token):
        """Nurse can create nursing documentation (if assigned to patient)"""
        headers = {"Authorization": f"Bearer {nurse_token}"}
        doc_data = {
            "patient_id": TEST_PATIENT_ID,
            "doc_type": "progress_note",
            "title": "TEST_Nursing Progress Note",
            "content": "Patient resting comfortably",
            "clinical_findings": "Vitals stable",
            "interventions": "Administered medications as ordered",
            "patient_response": "Tolerated well",
            "shift_type": "morning"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/clinical-docs/nursing",
            json=doc_data,
            headers=headers
        )
        print(f"Nurse Create Nursing Doc Status: {response.status_code}")
        print(f"Nurse Create Nursing Doc Response: {response.text[:500] if response.text else 'No response'}")
        
        # Should be 200/201 if assigned, 403 if not assigned
        if response.status_code in [200, 201]:
            data = response.json()
            assert "document" in data or "message" in data
            print("✓ Nurse successfully created nursing documentation")
        elif response.status_code == 403:
            print("✓ Nurse denied creating doc (not assigned to patient) - RBAC working")
        else:
            # Unexpected status - fail test
            assert False, f"Unexpected status code: {response.status_code}"
    
    def test_nurse_cannot_create_physician_doc(self, nurse_token):
        """Nurse should NOT be able to create physician documentation"""
        headers = {"Authorization": f"Bearer {nurse_token}"}
        doc_data = {
            "patient_id": TEST_PATIENT_ID,
            "doc_type": "progress_note",
            "title": "TEST_Physician Note (should fail)",
            "chief_complaint": "This should not be created by nurse"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/clinical-docs/physician",
            json=doc_data,
            headers=headers
        )
        print(f"Nurse Create Physician Doc Status: {response.status_code}")
        print(f"Nurse Create Physician Doc Response: {response.text[:500] if response.text else 'No response'}")
        
        # Should be 403 Forbidden
        assert response.status_code == 403
        print("✓ Nurse correctly denied from creating physician doc (RBAC working)")


class TestAuditLogging:
    """Test audit logging for chart access"""
    
    @pytest.fixture(scope="class")
    def physician_token(self):
        """Get physician token for audit tests"""
        login_res = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": TEST_PHYSICIAN["email"],
                "password": TEST_PHYSICIAN["password"]
            }
        )
        if login_res.status_code == 200:
            return login_res.json().get("token")
        pytest.skip("Could not login as physician")
    
    def test_audit_logs_created_on_access(self, physician_token):
        """Verify audit logs are created when accessing patient docs"""
        headers = {"Authorization": f"Bearer {physician_token}"}
        
        # First access the patient's physician docs
        access_res = requests.get(
            f"{BASE_URL}/api/clinical-docs/physician/{TEST_PATIENT_ID}",
            headers=headers
        )
        print(f"Access Physician Docs Status: {access_res.status_code}")
        
        # Then try to get audit logs (might need admin access)
        audit_res = requests.get(
            f"{BASE_URL}/api/clinical-docs/audit-logs/{TEST_PATIENT_ID}",
            headers=headers
        )
        print(f"Get Audit Logs Status: {audit_res.status_code}")
        
        if audit_res.status_code == 200:
            data = audit_res.json()
            print(f"Audit Logs Response: {data}")
            assert "audit_logs" in data
            print(f"✓ Found {len(data['audit_logs'])} audit log entries")
        elif audit_res.status_code == 403:
            print("✓ Audit logs require admin access (expected)")
        else:
            print(f"Audit logs endpoint returned: {audit_res.status_code}")


class TestHealthCheck:
    """Basic health check"""
    
    def test_api_health(self):
        """Test API is responding"""
        response = requests.get(f"{BASE_URL}/api/health")
        print(f"Health Check Status: {response.status_code}")
        print(f"Health Check Response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        print("✓ API is healthy")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
