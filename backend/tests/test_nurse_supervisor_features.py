#!/usr/bin/env python3
"""
Test Suite for Nurse Supervisor Portal Enhancements
Tests:
1. Bed Management Tab - Bed census data in Nursing Supervisor Dashboard
2. Nurse Assignment - Nurse list population in assignment dialog
3. Ambulance Request Patient Search - Search existing patient and manual entry
4. Ambulance Vehicle Registration - Nursing supervisor role permissions
5. Backend Permissions - nursing_supervisor role in allowed_roles
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://medrecords-gh-1.preview.emergentagent.com').rstrip('/')

# Test credentials
NURSING_SUPERVISOR_EMAIL = "nursing_supervisor@yacco.health"
NURSING_SUPERVISOR_PASSWORD = "test123"
IT_ADMIN_EMAIL = "it_admin@yacco.health"
IT_ADMIN_PASSWORD = "test123"
HOSPITAL_ID = "008cca73-b733-4224-afa3-992c02c045a4"


class TestNursingSupervisorFeatures:
    """Test suite for Nursing Supervisor Portal enhancements"""
    
    @pytest.fixture(scope="class")
    def nursing_supervisor_token(self):
        """Get nursing supervisor authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": NURSING_SUPERVISOR_EMAIL, "password": NURSING_SUPERVISOR_PASSWORD}
        )
        assert response.status_code == 200, f"Nursing supervisor login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in login response"
        return data["token"]
    
    @pytest.fixture(scope="class")
    def it_admin_token(self):
        """Get IT admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": IT_ADMIN_EMAIL, "password": IT_ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"IT admin login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in login response"
        return data["token"]
    
    # ============== Feature 1: Bed Management Tab ==============
    
    def test_bed_census_endpoint(self, nursing_supervisor_token):
        """Test GET /api/beds/census returns bed census data"""
        headers = {"Authorization": f"Bearer {nursing_supervisor_token}"}
        response = requests.get(f"{BASE_URL}/api/beds/census", headers=headers)
        
        assert response.status_code == 200, f"Bed census failed: {response.text}"
        data = response.json()
        
        # Verify census summary structure
        assert "summary" in data, "Missing 'summary' in census response"
        summary = data["summary"]
        
        # Check required fields in summary
        expected_fields = ["total_beds", "available_beds", "occupied_beds", "reserved_beds", "occupancy_rate"]
        for field in expected_fields:
            assert field in summary, f"Missing '{field}' in census summary"
        
        print(f"Bed Census Summary: Total={summary.get('total_beds')}, Available={summary.get('available_beds')}, Occupied={summary.get('occupied_beds')}, Occupancy={summary.get('occupancy_rate')}%")
    
    def test_list_wards_endpoint(self, nursing_supervisor_token):
        """Test GET /api/beds/wards returns ward list"""
        headers = {"Authorization": f"Bearer {nursing_supervisor_token}"}
        response = requests.get(f"{BASE_URL}/api/beds/wards", headers=headers)
        
        assert response.status_code == 200, f"List wards failed: {response.text}"
        data = response.json()
        
        assert "wards" in data, "Missing 'wards' in response"
        wards = data["wards"]
        
        print(f"Found {len(wards)} wards")
        
        # If wards exist, verify structure
        if len(wards) > 0:
            ward = wards[0]
            expected_fields = ["id", "name", "total_beds"]
            for field in expected_fields:
                assert field in ward, f"Missing '{field}' in ward data"
    
    # ============== Feature 2: Nurse Assignment ==============
    
    def test_get_nurses_list(self, nursing_supervisor_token):
        """Test GET /api/nursing-supervisor/nurses returns nurse list with on-shift indicators"""
        headers = {"Authorization": f"Bearer {nursing_supervisor_token}"}
        response = requests.get(
            f"{BASE_URL}/api/nursing-supervisor/nurses",
            headers=headers,
            params={"on_shift_only": "false"}
        )
        
        assert response.status_code == 200, f"Get nurses failed: {response.text}"
        data = response.json()
        
        assert "nurses" in data, "Missing 'nurses' in response"
        nurses = data["nurses"]
        
        print(f"Found {len(nurses)} nurses")
        
        # Verify nurse data structure
        if len(nurses) > 0:
            nurse = nurses[0]
            # Check for required fields
            assert "id" in nurse, "Missing 'id' in nurse data"
            assert "first_name" in nurse or "name" in nurse, "Missing name field in nurse data"
            
            # Check for active_shift indicator (may be null/false if not on shift)
            # This is the key field for on-shift indicators
            print(f"Sample nurse: {nurse.get('first_name', nurse.get('name', 'N/A'))} - active_shift: {nurse.get('active_shift')}")
    
    def test_nursing_supervisor_dashboard(self, nursing_supervisor_token):
        """Test GET /api/nursing-supervisor/dashboard returns dashboard data"""
        headers = {"Authorization": f"Bearer {nursing_supervisor_token}"}
        response = requests.get(f"{BASE_URL}/api/nursing-supervisor/dashboard", headers=headers)
        
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        data = response.json()
        
        print(f"Dashboard data keys: {list(data.keys())}")
    
    # ============== Feature 3: Ambulance Request Patient Search ==============
    
    def test_patient_search_api(self, nursing_supervisor_token):
        """Test patient search API for ambulance request dialog"""
        headers = {"Authorization": f"Bearer {nursing_supervisor_token}"}
        
        # Search for patients
        response = requests.get(
            f"{BASE_URL}/api/patients",
            headers=headers,
            params={"search": "Ghana"}
        )
        
        assert response.status_code == 200, f"Patient search failed: {response.text}"
        data = response.json()
        
        # Response could be a list or dict with patients key
        patients = data if isinstance(data, list) else data.get("patients", data.get("data", []))
        
        print(f"Patient search returned {len(patients) if isinstance(patients, list) else 'N/A'} results")
        
        # Verify patient data structure if results exist
        if isinstance(patients, list) and len(patients) > 0:
            patient = patients[0]
            expected_fields = ["id", "first_name", "last_name"]
            for field in expected_fields:
                assert field in patient, f"Missing '{field}' in patient data"
            print(f"Sample patient: {patient.get('first_name')} {patient.get('last_name')} - MRN: {patient.get('mrn')}")
    
    def test_ambulance_request_creation_with_patient(self, nursing_supervisor_token):
        """Test creating ambulance request with existing patient"""
        headers = {"Authorization": f"Bearer {nursing_supervisor_token}"}
        
        # First get a patient
        patients_response = requests.get(
            f"{BASE_URL}/api/patients",
            headers=headers,
            params={"limit": 1}
        )
        
        if patients_response.status_code == 200:
            patients_data = patients_response.json()
            patients = patients_data if isinstance(patients_data, list) else patients_data.get("patients", patients_data.get("data", []))
            
            if isinstance(patients, list) and len(patients) > 0:
                patient = patients[0]
                patient_id = patient.get("id")
                
                # Create ambulance request with patient
                request_data = {
                    "patient_id": patient_id,
                    "patient_name": f"{patient.get('first_name', '')} {patient.get('last_name', '')}",
                    "patient_phone": patient.get("phone", "0201234567"),
                    "request_type": "emergency",
                    "priority": "high",
                    "pickup_location": "Test Location",
                    "pickup_address": "123 Test Street, Accra",
                    "destination": "ygtworks Health Center",
                    "destination_address": "Hospital Road, Accra",
                    "chief_complaint": "Test emergency request",
                    "notes": "Testing patient search integration"
                }
                
                response = requests.post(
                    f"{BASE_URL}/api/ambulance/requests",
                    headers=headers,
                    json=request_data
                )
                
                # Accept 201 (created) or 200 (success)
                assert response.status_code in [200, 201], f"Create ambulance request failed: {response.text}"
                print(f"Ambulance request created successfully with patient_id: {patient_id}")
    
    # ============== Feature 4: Ambulance Vehicle Registration ==============
    
    def test_nursing_supervisor_can_register_vehicle(self, nursing_supervisor_token):
        """Test that nursing_supervisor role can register ambulance vehicles"""
        headers = {"Authorization": f"Bearer {nursing_supervisor_token}"}
        
        # Generate unique vehicle number
        vehicle_number = f"TEST-NS-{uuid.uuid4().hex[:6].upper()}"
        
        vehicle_data = {
            "vehicle_number": vehicle_number,
            "vehicle_type": "basic_ambulance",
            "equipment_level": "basic",
            "make_model": "Toyota Hiace",
            "year": 2023,
            "capacity": 2,
            "has_oxygen": True,
            "has_defibrillator": False,
            "has_ventilator": False,
            "has_stretcher": True,
            "notes": "Test vehicle registered by nursing supervisor"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ambulance/vehicles",
            headers=headers,
            json=vehicle_data
        )
        
        # Should NOT get 403 Access Denied
        assert response.status_code != 403, f"Nursing supervisor got Access Denied: {response.text}"
        assert response.status_code in [200, 201], f"Vehicle registration failed: {response.text}"
        
        data = response.json()
        assert "id" in data or "vehicle" in data, "Missing vehicle ID in response"
        
        print(f"Vehicle registered successfully: {vehicle_number}")
    
    def test_it_admin_can_register_vehicle(self, it_admin_token):
        """Test that IT admin can also register ambulance vehicles"""
        headers = {"Authorization": f"Bearer {it_admin_token}"}
        
        vehicle_number = f"TEST-IT-{uuid.uuid4().hex[:6].upper()}"
        
        vehicle_data = {
            "vehicle_number": vehicle_number,
            "vehicle_type": "advanced_ambulance",
            "equipment_level": "advanced",
            "make_model": "Mercedes Sprinter",
            "year": 2024,
            "capacity": 3,
            "has_oxygen": True,
            "has_defibrillator": True,
            "has_ventilator": True,
            "has_stretcher": True,
            "notes": "Test vehicle registered by IT admin"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ambulance/vehicles",
            headers=headers,
            json=vehicle_data
        )
        
        assert response.status_code in [200, 201], f"IT admin vehicle registration failed: {response.text}"
        print(f"IT Admin vehicle registered successfully: {vehicle_number}")
    
    # ============== Feature 5: Backend Permissions ==============
    
    def test_nursing_supervisor_bed_management_access(self, nursing_supervisor_token):
        """Test nursing_supervisor has access to bed management endpoints"""
        headers = {"Authorization": f"Bearer {nursing_supervisor_token}"}
        
        # Test various bed management endpoints
        endpoints = [
            "/api/beds/census",
            "/api/beds/wards",
            "/api/beds/rooms",
            "/api/beds/beds"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            assert response.status_code != 403, f"Access denied for {endpoint}"
            assert response.status_code == 200, f"Failed to access {endpoint}: {response.status_code}"
            print(f"✓ Access granted to {endpoint}")
    
    def test_nursing_supervisor_ambulance_access(self, nursing_supervisor_token):
        """Test nursing_supervisor has access to ambulance endpoints"""
        headers = {"Authorization": f"Bearer {nursing_supervisor_token}"}
        
        # Test ambulance endpoints
        endpoints = [
            "/api/ambulance/vehicles",
            "/api/ambulance/requests",
            "/api/ambulance/dashboard"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            assert response.status_code != 403, f"Access denied for {endpoint}"
            assert response.status_code == 200, f"Failed to access {endpoint}: {response.status_code}"
            print(f"✓ Access granted to {endpoint}")
    
    def test_get_ambulance_vehicles_list(self, nursing_supervisor_token):
        """Test GET /api/ambulance/vehicles returns vehicle list"""
        headers = {"Authorization": f"Bearer {nursing_supervisor_token}"}
        response = requests.get(f"{BASE_URL}/api/ambulance/vehicles", headers=headers)
        
        assert response.status_code == 200, f"Get vehicles failed: {response.text}"
        data = response.json()
        
        assert "vehicles" in data, "Missing 'vehicles' in response"
        vehicles = data["vehicles"]
        
        print(f"Found {len(vehicles)} ambulance vehicles")
        
        # Verify vehicle data structure if vehicles exist
        if len(vehicles) > 0:
            vehicle = vehicles[0]
            expected_fields = ["id", "vehicle_number", "vehicle_type", "status"]
            for field in expected_fields:
                assert field in vehicle, f"Missing '{field}' in vehicle data"


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture(scope="class")
    def it_admin_token(self):
        """Get IT admin authentication token for cleanup"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": IT_ADMIN_EMAIL, "password": IT_ADMIN_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def test_cleanup_test_vehicles(self, it_admin_token):
        """Clean up test vehicles created during testing"""
        if not it_admin_token:
            pytest.skip("No admin token for cleanup")
        
        headers = {"Authorization": f"Bearer {it_admin_token}"}
        response = requests.get(f"{BASE_URL}/api/ambulance/vehicles", headers=headers)
        
        if response.status_code == 200:
            vehicles = response.json().get("vehicles", [])
            test_vehicles = [v for v in vehicles if v.get("vehicle_number", "").startswith("TEST-")]
            
            for vehicle in test_vehicles:
                delete_response = requests.delete(
                    f"{BASE_URL}/api/ambulance/vehicles/{vehicle['id']}",
                    headers=headers
                )
                if delete_response.status_code in [200, 204]:
                    print(f"Cleaned up test vehicle: {vehicle['vehicle_number']}")
        
        print("Cleanup completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
