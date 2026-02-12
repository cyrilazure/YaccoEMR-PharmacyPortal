"""
Voice Dictation Module Tests
Tests for voice dictation API endpoints including:
- GET /api/voice-dictation/medical-terms
- POST /api/voice-dictation/correct-terminology
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_CREDENTIALS = {
    "radiologist": {"email": "radiologist@yacco.health", "password": "test123"},
    "nurse": {"email": "nursing_supervisor@yacco.health", "password": "test123"},
    "super_admin": {"email": "ygtnetworks@gmail.com", "password": "test123"}
}


class TestVoiceDictationAPI:
    """Voice Dictation API endpoint tests"""
    
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
    
    def test_get_medical_terms_endpoint_exists(self):
        """Test GET /api/voice-dictation/medical-terms endpoint exists and returns data"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        response = self.session.get(f"{BASE_URL}/api/voice-dictation/medical-terms")
        
        # Should return 200 OK
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Validate response structure
        data = response.json()
        assert "terms_count" in data, "Response should contain terms_count"
        assert "abbreviations_count" in data, "Response should contain abbreviations_count"
        assert "categories" in data, "Response should contain categories"
        
        # Validate data types
        assert isinstance(data["terms_count"], int), "terms_count should be an integer"
        assert isinstance(data["abbreviations_count"], int), "abbreviations_count should be an integer"
        assert isinstance(data["categories"], list), "categories should be a list"
        
        # Validate counts are reasonable
        assert data["terms_count"] > 0, "Should have at least some medical terms"
        assert data["abbreviations_count"] > 0, "Should have at least some abbreviations"
        
        print(f"✓ Medical terms endpoint returned: {data['terms_count']} terms, {data['abbreviations_count']} abbreviations")
    
    def test_correct_terminology_basic(self):
        """Test POST /api/voice-dictation/correct-terminology with basic text"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        # Test with text that should NOT be corrected
        response = self.session.post(
            f"{BASE_URL}/api/voice-dictation/correct-terminology",
            json={
                "text": "Patient presents with normal findings.",
                "context": "general"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "original_text" in data, "Response should contain original_text"
        assert "corrected_text" in data, "Response should contain corrected_text"
        assert "corrections_made" in data, "Response should contain corrections_made"
        
        # For normal text, should return same text with no corrections
        assert data["original_text"] == "Patient presents with normal findings."
        assert isinstance(data["corrections_made"], list)
        
        print(f"✓ Basic terminology correction works - no corrections needed for normal text")
    
    def test_correct_terminology_pneumonia(self):
        """Test medical terminology correction for 'new monia' -> 'pneumonia'"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        response = self.session.post(
            f"{BASE_URL}/api/voice-dictation/correct-terminology",
            json={
                "text": "Patient diagnosed with new monia in the right lung.",
                "context": "radiology"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Should correct 'new monia' to 'pneumonia'
        assert "pneumonia" in data["corrected_text"].lower(), f"Expected 'pneumonia' in corrected text, got: {data['corrected_text']}"
        assert len(data["corrections_made"]) > 0, "Should have at least one correction"
        
        # Verify correction details
        correction = data["corrections_made"][0]
        assert "original" in correction, "Correction should have original field"
        assert "corrected" in correction, "Correction should have corrected field"
        
        print(f"✓ Pneumonia correction works: '{data['original_text']}' -> '{data['corrected_text']}'")
        print(f"  Corrections made: {data['corrections_made']}")
    
    def test_correct_terminology_hypertension(self):
        """Test medical terminology correction for 'high pertension' -> 'hypertension'"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        response = self.session.post(
            f"{BASE_URL}/api/voice-dictation/correct-terminology",
            json={
                "text": "Patient has history of high pertension.",
                "context": "clinical"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Should correct 'high pertension' to 'hypertension'
        assert "hypertension" in data["corrected_text"].lower(), f"Expected 'hypertension' in corrected text, got: {data['corrected_text']}"
        
        print(f"✓ Hypertension correction works: '{data['original_text']}' -> '{data['corrected_text']}'")
    
    def test_correct_terminology_tachycardia(self):
        """Test medical terminology correction for 'tacky cardia' -> 'tachycardia'"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        response = self.session.post(
            f"{BASE_URL}/api/voice-dictation/correct-terminology",
            json={
                "text": "ECG shows tacky cardia with rate of 120.",
                "context": "clinical"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Should correct 'tacky cardia' to 'tachycardia'
        assert "tachycardia" in data["corrected_text"].lower(), f"Expected 'tachycardia' in corrected text, got: {data['corrected_text']}"
        
        print(f"✓ Tachycardia correction works: '{data['original_text']}' -> '{data['corrected_text']}'")
    
    def test_correct_terminology_radiology_context(self):
        """Test medical terminology correction with radiology context"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        response = self.session.post(
            f"{BASE_URL}/api/voice-dictation/correct-terminology",
            json={
                "text": "Chest X-ray shows consolodation in the left lower lobe.",
                "context": "radiology"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Should correct 'consolodation' to 'consolidation'
        assert "consolidation" in data["corrected_text"].lower(), f"Expected 'consolidation' in corrected text, got: {data['corrected_text']}"
        
        print(f"✓ Radiology context correction works: '{data['original_text']}' -> '{data['corrected_text']}'")
    
    def test_correct_terminology_nursing_context(self):
        """Test medical terminology correction with nursing context"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        response = self.session.post(
            f"{BASE_URL}/api/voice-dictation/correct-terminology",
            json={
                "text": "Patient showing signs of a dema in lower extremities.",
                "context": "nursing"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Should correct 'a dema' to 'edema'
        assert "edema" in data["corrected_text"].lower(), f"Expected 'edema' in corrected text, got: {data['corrected_text']}"
        
        print(f"✓ Nursing context correction works: '{data['original_text']}' -> '{data['corrected_text']}'")
    
    def test_correct_terminology_multiple_corrections(self):
        """Test medical terminology correction with multiple terms to correct"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        response = self.session.post(
            f"{BASE_URL}/api/voice-dictation/correct-terminology",
            json={
                "text": "Patient with new monia and tacky cardia, showing signs of a dema.",
                "context": "clinical"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Should correct multiple terms
        corrected = data["corrected_text"].lower()
        assert "pneumonia" in corrected, f"Expected 'pneumonia' in corrected text"
        assert "tachycardia" in corrected, f"Expected 'tachycardia' in corrected text"
        assert "edema" in corrected, f"Expected 'edema' in corrected text"
        
        # Should have multiple corrections
        assert len(data["corrections_made"]) >= 3, f"Expected at least 3 corrections, got {len(data['corrections_made'])}"
        
        print(f"✓ Multiple corrections work: {len(data['corrections_made'])} corrections made")
        for c in data["corrections_made"]:
            print(f"  - '{c.get('original')}' -> '{c.get('corrected')}'")
    
    def test_correct_terminology_empty_text(self):
        """Test medical terminology correction with empty text"""
        if not self.authenticated:
            pytest.skip("Authentication failed - skipping authenticated tests")
        
        response = self.session.post(
            f"{BASE_URL}/api/voice-dictation/correct-terminology",
            json={
                "text": "",
                "context": "general"
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["corrected_text"] == "", "Empty text should return empty corrected text"
        assert len(data["corrections_made"]) == 0, "Empty text should have no corrections"
        
        print(f"✓ Empty text handling works correctly")
    
    def test_correct_terminology_unauthorized(self):
        """Test that unauthenticated requests are rejected"""
        # Create new session without auth
        unauth_session = requests.Session()
        unauth_session.headers.update({"Content-Type": "application/json"})
        
        response = unauth_session.post(
            f"{BASE_URL}/api/voice-dictation/correct-terminology",
            json={
                "text": "Test text",
                "context": "general"
            }
        )
        
        # Should return 401 Unauthorized or 403 Forbidden
        assert response.status_code in [401, 403], f"Expected 401/403 for unauthorized request, got {response.status_code}"
        
        print(f"✓ Unauthorized requests are properly rejected (status: {response.status_code})")
    
    def test_medical_terms_unauthorized(self):
        """Test that unauthenticated requests to medical-terms are rejected"""
        # Create new session without auth
        unauth_session = requests.Session()
        
        response = unauth_session.get(f"{BASE_URL}/api/voice-dictation/medical-terms")
        
        # Should return 401 Unauthorized or 403 Forbidden
        assert response.status_code in [401, 403], f"Expected 401/403 for unauthorized request, got {response.status_code}"
        
        print(f"✓ Unauthorized requests to medical-terms are properly rejected (status: {response.status_code})")


class TestVoiceDictationWithDifferentRoles:
    """Test voice dictation access with different user roles"""
    
    def test_nurse_can_access_voice_dictation(self):
        """Test that nurse role can access voice dictation endpoints"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login as nurse
        login_response = session.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_CREDENTIALS["nurse"]
        )
        
        if login_response.status_code != 200:
            pytest.skip("Nurse login failed - skipping test")
        
        data = login_response.json()
        token = data.get("access_token") or data.get("token")
        if token:
            session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Test medical terms endpoint
        response = session.get(f"{BASE_URL}/api/voice-dictation/medical-terms")
        assert response.status_code == 200, f"Nurse should be able to access medical-terms, got {response.status_code}"
        
        # Test terminology correction
        response = session.post(
            f"{BASE_URL}/api/voice-dictation/correct-terminology",
            json={"text": "Patient has new monia", "context": "nursing"}
        )
        assert response.status_code == 200, f"Nurse should be able to use terminology correction, got {response.status_code}"
        
        print(f"✓ Nurse role can access voice dictation endpoints")
    
    def test_super_admin_can_access_voice_dictation(self):
        """Test that super_admin role can access voice dictation endpoints"""
        session = requests.Session()
        session.headers.update({"Content-Type": "application/json"})
        
        # Login as super_admin
        login_response = session.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_CREDENTIALS["super_admin"]
        )
        
        if login_response.status_code != 200:
            pytest.skip("Super admin login failed - skipping test")
        
        data = login_response.json()
        token = data.get("access_token") or data.get("token")
        if token:
            session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Test medical terms endpoint
        response = session.get(f"{BASE_URL}/api/voice-dictation/medical-terms")
        assert response.status_code == 200, f"Super admin should be able to access medical-terms, got {response.status_code}"
        
        print(f"✓ Super admin role can access voice dictation endpoints")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
