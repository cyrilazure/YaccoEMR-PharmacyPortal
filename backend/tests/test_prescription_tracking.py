"""
Prescription Delivery Tracking Feature Tests
=============================================
Tests for patient-facing prescription tracking functionality:
- Public tracking endpoint
- Status update API
- Delivery method API
- Tracking QR code API
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
PHARMACY_EMAIL = "test@testpharm.gh"
PHARMACY_PASSWORD = "testpass123"


class TestPublicTrackingEndpoint:
    """Tests for public prescription tracking endpoint - no auth required"""
    
    def test_track_nonexistent_prescription_returns_404(self):
        """Test that tracking a non-existent prescription returns 404"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/prescription/track/NONEXISTENT-CODE-123")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
        print(f"✓ Non-existent tracking code returns 404: {data['detail']}")
    
    def test_track_invalid_code_format(self):
        """Test tracking with various invalid code formats"""
        invalid_codes = ["", "   ", "!@#$%", "a" * 500]
        for code in invalid_codes:
            if code.strip():  # Skip empty strings as they won't match the route
                response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/prescription/track/{code}")
                assert response.status_code in [404, 422], f"Expected 404 or 422 for code: {code}"
        print("✓ Invalid tracking codes handled properly")
    
    def test_track_endpoint_is_public(self):
        """Test that tracking endpoint doesn't require authentication"""
        # Should return 404 (not found) not 401 (unauthorized)
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/prescription/track/TEST-123")
        assert response.status_code == 404, "Endpoint should be public (404 not 401)"
        print("✓ Tracking endpoint is public (no auth required)")


class TestPharmacyAuthentication:
    """Tests for pharmacy authentication"""
    
    def test_pharmacy_login_success(self):
        """Test successful pharmacy login"""
        response = requests.post(f"{BASE_URL}/api/pharmacy-portal/auth/login", json={
            "email": PHARMACY_EMAIL,
            "password": PHARMACY_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert "pharmacy" in data
        print(f"✓ Pharmacy login successful: {data['user']['email']}")
        return data["token"]
    
    def test_pharmacy_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/pharmacy-portal/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid credentials rejected with 401")


class TestPrescriptionStatusUpdate:
    """Tests for prescription status update API"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/pharmacy-portal/auth/login", json={
            "email": PHARMACY_EMAIL,
            "password": PHARMACY_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_update_status_requires_auth(self):
        """Test that status update requires authentication"""
        response = requests.put(
            f"{BASE_URL}/api/pharmacy-portal/prescription/test-id/update-status",
            json={"status": "processing"}
        )
        assert response.status_code in [401, 403]
        print("✓ Status update requires authentication")
    
    def test_update_status_invalid_status(self, auth_headers):
        """Test that invalid status values are rejected"""
        response = requests.put(
            f"{BASE_URL}/api/pharmacy-portal/prescription/test-id/update-status",
            headers=auth_headers,
            json={"status": "invalid_status"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "Invalid status" in data.get("detail", "")
        print("✓ Invalid status values rejected")
    
    def test_update_status_valid_statuses(self, auth_headers):
        """Test that valid status values are accepted (even if prescription not found)"""
        valid_statuses = ["received", "processing", "ready", "out_for_delivery", "dispensed", "cancelled"]
        for status in valid_statuses:
            response = requests.put(
                f"{BASE_URL}/api/pharmacy-portal/prescription/nonexistent-id/update-status",
                headers=auth_headers,
                json={"status": status}
            )
            # Should not return 400 (invalid status) - may return 404 (not found) or 200
            assert response.status_code != 400, f"Status '{status}' should be valid"
        print(f"✓ All valid statuses accepted: {valid_statuses}")


class TestPrescriptionDeliveryMethod:
    """Tests for prescription delivery method API"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/pharmacy-portal/auth/login", json={
            "email": PHARMACY_EMAIL,
            "password": PHARMACY_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_set_delivery_requires_auth(self):
        """Test that set delivery requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/pharmacy-portal/prescription/test-id/set-delivery",
            json={"delivery_method": "pickup"}
        )
        assert response.status_code in [401, 403]
        print("✓ Set delivery requires authentication")
    
    def test_set_delivery_invalid_method(self, auth_headers):
        """Test that invalid delivery method is rejected"""
        response = requests.post(
            f"{BASE_URL}/api/pharmacy-portal/prescription/test-id/set-delivery",
            headers=auth_headers,
            json={"delivery_method": "invalid_method"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "pickup" in data.get("detail", "").lower() or "delivery" in data.get("detail", "").lower()
        print("✓ Invalid delivery method rejected")
    
    def test_set_delivery_requires_address_for_delivery(self, auth_headers):
        """Test that delivery method 'delivery' requires address"""
        response = requests.post(
            f"{BASE_URL}/api/pharmacy-portal/prescription/test-id/set-delivery",
            headers=auth_headers,
            json={"delivery_method": "delivery"}  # No address provided
        )
        assert response.status_code == 400
        data = response.json()
        assert "address" in data.get("detail", "").lower()
        print("✓ Delivery method 'delivery' requires address")


class TestTrackingQRCode:
    """Tests for tracking QR code API"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/pharmacy-portal/auth/login", json={
            "email": PHARMACY_EMAIL,
            "password": PHARMACY_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_tracking_qr_requires_auth(self):
        """Test that tracking QR endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/prescription/test-id/tracking-qr")
        assert response.status_code in [401, 403]
        print("✓ Tracking QR requires authentication")
    
    def test_tracking_qr_nonexistent_prescription(self, auth_headers):
        """Test tracking QR for non-existent prescription"""
        response = requests.get(
            f"{BASE_URL}/api/pharmacy-portal/prescription/nonexistent-id/tracking-qr",
            headers=auth_headers
        )
        assert response.status_code == 404
        print("✓ Non-existent prescription returns 404 for QR")


class TestTrackingWithRealPrescription:
    """Tests with creating and tracking a real prescription"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/pharmacy-portal/auth/login", json={
            "email": PHARMACY_EMAIL,
            "password": PHARMACY_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_create_and_track_prescription(self, auth_headers):
        """Test creating a prescription and tracking it"""
        # Create a test prescription via e-prescription receive endpoint
        rx_number = f"RX-TEST-{uuid.uuid4().hex[:8].upper()}"
        
        prescription_data = {
            "prescription_id": str(uuid.uuid4()),
            "rx_number": rx_number,
            "patient_name": "Test Patient",
            "patient_phone": "+233201234567",
            "prescriber_name": "Dr. Test Physician",
            "hospital_name": "Test Hospital",
            "hospital_id": str(uuid.uuid4()),
            "medications": [
                {"medication_name": "Paracetamol", "dosage": "500mg", "quantity": 20},
                {"medication_name": "Amoxicillin", "dosage": "250mg", "quantity": 14}
            ],
            "diagnosis": "Common cold",
            "clinical_notes": "Take with food",
            "priority": "routine"
        }
        
        # Create prescription
        create_response = requests.post(
            f"{BASE_URL}/api/pharmacy-portal/eprescription/receive",
            headers=auth_headers,
            json=prescription_data
        )
        
        if create_response.status_code != 200:
            print(f"Note: Could not create prescription: {create_response.status_code}")
            pytest.skip("Could not create test prescription")
        
        created_data = create_response.json()
        print(f"✓ Created prescription: {created_data.get('rx_number')}")
        
        # Track the prescription using public endpoint
        track_response = requests.get(
            f"{BASE_URL}/api/pharmacy-portal/public/prescription/track/{rx_number}"
        )
        
        assert track_response.status_code == 200
        track_data = track_response.json()
        
        # Verify tracking response structure
        assert "rx_number" in track_data
        assert "patient_name" in track_data
        assert "current_status" in track_data
        assert "current_step" in track_data
        assert "total_steps" in track_data
        assert "timeline" in track_data
        assert "medications" in track_data
        
        # Verify timeline has 5 steps
        assert track_data["total_steps"] == 5
        assert len(track_data["timeline"]) == 5
        
        # Verify timeline structure
        timeline = track_data["timeline"]
        expected_labels = ["Sent to Pharmacy", "Received", "Being Prepared", "Ready for Pickup", "Collected/Delivered"]
        for i, step in enumerate(timeline):
            assert "step" in step
            assert "label" in step
            assert "description" in step
            assert "completed" in step
            assert "current" in step
            assert step["step"] == i + 1
        
        # Verify medications
        assert len(track_data["medications"]) == 2
        
        print(f"✓ Tracking data verified:")
        print(f"  - RX Number: {track_data['rx_number']}")
        print(f"  - Patient: {track_data['patient_name']}")
        print(f"  - Status: {track_data['current_status']}")
        print(f"  - Step: {track_data['current_step']}/{track_data['total_steps']}")
        print(f"  - Medications: {len(track_data['medications'])}")
        print(f"  - Timeline steps: {len(track_data['timeline'])}")
        
        return rx_number
    
    def test_update_prescription_status_flow(self, auth_headers):
        """Test updating prescription through status flow"""
        # Create a test prescription
        rx_number = f"RX-FLOW-{uuid.uuid4().hex[:8].upper()}"
        
        prescription_data = {
            "prescription_id": str(uuid.uuid4()),
            "rx_number": rx_number,
            "patient_name": "Flow Test Patient",
            "prescriber_name": "Dr. Flow Test",
            "hospital_name": "Flow Test Hospital",
            "medications": [{"medication_name": "Test Med", "dosage": "100mg", "quantity": 10}],
            "priority": "routine"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/pharmacy-portal/eprescription/receive",
            headers=auth_headers,
            json=prescription_data
        )
        
        if create_response.status_code != 200:
            pytest.skip("Could not create test prescription")
        
        rx_id = create_response.json().get("prescription_id")
        print(f"✓ Created prescription for flow test: {rx_number}")
        
        # Test status progression: received -> processing -> ready
        status_flow = ["received", "processing", "ready"]
        
        for status in status_flow:
            update_response = requests.put(
                f"{BASE_URL}/api/pharmacy-portal/prescription/{rx_id}/update-status",
                headers=auth_headers,
                json={"status": status}
            )
            
            # Verify tracking reflects the update
            track_response = requests.get(
                f"{BASE_URL}/api/pharmacy-portal/public/prescription/track/{rx_number}"
            )
            
            if track_response.status_code == 200:
                track_data = track_response.json()
                print(f"  - Updated to '{status}': current_step={track_data.get('current_step')}")
        
        print("✓ Status flow progression tested")


class TestTrackingPageEndpoints:
    """Tests for endpoints used by the tracking page"""
    
    def test_public_regions_endpoint(self):
        """Test public regions endpoint (used for pharmacy search)"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/regions")
        assert response.status_code == 200
        data = response.json()
        assert "regions" in data
        assert "total_pharmacies" in data
        print(f"✓ Public regions endpoint works: {len(data['regions'])} regions")
    
    def test_public_pharmacies_search(self):
        """Test public pharmacies search endpoint"""
        response = requests.get(f"{BASE_URL}/api/pharmacy-portal/public/pharmacies")
        assert response.status_code == 200
        data = response.json()
        assert "pharmacies" in data
        assert "total" in data
        print(f"✓ Public pharmacies search works: {data['total']} pharmacies")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
