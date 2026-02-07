#!/usr/bin/env python
"""
Nursing Portal and Supervisor Tests for Yacco EMR
"""

import requests
import json
import sys
import os

class NursingPortalTester:
    def __init__(self):
        self.base_url = "https://healthfusion-gh.preview.emergentagent.com/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.nurse_report_id = None
        
    def log_test(self, test_name, passed, details=""):
        """Log test results"""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            print(f"✅ {test_name}: PASSED {details}")
        else:
            print(f"❌ {test_name}: FAILED {details}")
    
    def make_request(self, method, endpoint, data=None):
        """Make HTTP request to API"""
        url = f"{self.base_url}/{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == "PUT":
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return None, f"Unsupported method: {method}"
            
            return response, None
        except requests.exceptions.RequestException as e:
            return None, str(e)
    
    def test_nursing_supervisor_dashboard(self):
        """Test Nursing Supervisor Dashboard - GET /api/nursing-supervisor/dashboard"""
        # Login as IT Admin (who has supervisor access)
        login_data = {
            "email": "kofiabedu2019@gmail.com",
            "password": "2I6ZRBkjVn2ZQg7O",
            "hospital_id": "e717ed11-7955-4884-8d6b-a529f918c34f",
            "location_id": "b61d7896-b4ef-436b-868e-94a60b55c64c"
        }
        
        response, error = self.make_request('POST', 'regions/auth/login', login_data)
        
        if error or response.status_code != 200:
            self.log_test("Nursing Supervisor Dashboard", False, "Failed to login as IT Admin")
            return False
        
        # Use IT Admin token for supervisor access
        it_admin_token = response.json().get('token')
        original_token = self.token
        self.token = it_admin_token
        
        response, error = self.make_request('GET', 'nursing-supervisor/dashboard')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Nursing Supervisor Dashboard", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ['nurses_on_shift', 'total_nurses', 'active_assignments', 'total_patients']
            has_all_fields = all(field in data for field in required_fields)
            self.log_test("Nursing Supervisor Dashboard", has_all_fields, 
                         f"Dashboard stats: {data}")
            return has_all_fields
        else:
            self.log_test("Nursing Supervisor Dashboard", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
    
    def test_nursing_supervisor_nurses_list(self):
        """Test Nursing Supervisor - GET /api/nursing-supervisor/nurses"""
        # Login as IT Admin
        login_data = {
            "email": "kofiabedu2019@gmail.com",
            "password": "2I6ZRBkjVn2ZQg7O",
            "hospital_id": "e717ed11-7955-4884-8d6b-a529f918c34f",
            "location_id": "b61d7896-b4ef-436b-868e-94a60b55c64c"
        }
        
        response, error = self.make_request('POST', 'regions/auth/login', login_data)
        
        if error or response.status_code != 200:
            self.log_test("Nursing Supervisor Nurses List", False, "Failed to login as IT Admin")
            return False
        
        it_admin_token = response.json().get('token')
        original_token = self.token
        self.token = it_admin_token
        
        response, error = self.make_request('GET', 'nursing-supervisor/nurses')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Nursing Supervisor Nurses List", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_nurses = 'nurses' in data and 'total' in data
            self.log_test("Nursing Supervisor Nurses List", has_nurses, 
                         f"Found {data.get('total', 0)} nurses")
            return has_nurses
        else:
            self.log_test("Nursing Supervisor Nurses List", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
    
    def test_nursing_supervisor_current_shifts(self):
        """Test Nursing Supervisor - GET /api/nursing-supervisor/shifts/current"""
        # Login as IT Admin
        login_data = {
            "email": "kofiabedu2019@gmail.com",
            "password": "2I6ZRBkjVn2ZQg7O",
            "hospital_id": "e717ed11-7955-4884-8d6b-a529f918c34f",
            "location_id": "b61d7896-b4ef-436b-868e-94a60b55c64c"
        }
        
        response, error = self.make_request('POST', 'regions/auth/login', login_data)
        
        if error or response.status_code != 200:
            self.log_test("Nursing Supervisor Current Shifts", False, "Failed to login as IT Admin")
            return False
        
        it_admin_token = response.json().get('token')
        original_token = self.token
        self.token = it_admin_token
        
        response, error = self.make_request('GET', 'nursing-supervisor/shifts/current')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Nursing Supervisor Current Shifts", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_shifts = 'active_shifts' in data and 'total_on_shift' in data
            self.log_test("Nursing Supervisor Current Shifts", has_shifts, 
                         f"Found {data.get('total_on_shift', 0)} active shifts")
            return has_shifts
        else:
            self.log_test("Nursing Supervisor Current Shifts", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
    
    def test_nurse_portal_clock_in(self):
        """Test Nurse Portal Clock In - POST /api/nurse/shifts/clock-in"""
        # First create a nurse user
        nurse_data = {
            "email": "testnurse@hospital.com",
            "password": "nurse123",
            "first_name": "Test",
            "last_name": "Nurse",
            "role": "nurse",
            "department": "Medical Ward",
            "organization_id": "e717ed11-7955-4884-8d6b-a529f918c34f"
        }
        
        response, error = self.make_request('POST', 'auth/register', nurse_data)
        if error or response.status_code not in [200, 201]:
            # Try login if user exists
            login_response, login_error = self.make_request('POST', 'auth/login', {
                "email": nurse_data["email"],
                "password": nurse_data["password"]
            })
            if login_error or login_response.status_code != 200:
                self.log_test("Nurse Portal Clock In", False, "Failed to create/login nurse user")
                return False
            nurse_token = login_response.json().get('token')
        else:
            nurse_token = response.json().get('token')
        
        # Use nurse token
        original_token = self.token
        self.token = nurse_token
        
        # Clock in
        clock_in_data = {
            "shift_type": "morning",
            "department_id": "medical-ward",
            "notes": "Starting morning shift"
        }
        
        response, error = self.make_request('POST', 'nurse/shifts/clock-in', clock_in_data)
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Nurse Portal Clock In", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_shift = 'shift' in data and 'message' in data
            self.log_test("Nurse Portal Clock In", has_shift, 
                         f"Clock in successful: {data.get('message', '')}")
            return has_shift
        else:
            self.log_test("Nurse Portal Clock In", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
    
    def run_all_tests(self):
        """Run all nursing portal tests"""
        print("🏥 Starting Nursing Portal and Supervisor Tests...")
        print("=" * 60)
        
        # Nursing Supervisor Tests
        self.test_nursing_supervisor_dashboard()
        self.test_nursing_supervisor_nurses_list()
        self.test_nursing_supervisor_current_shifts()
        
        # Nurse Portal Tests
        self.test_nurse_portal_clock_in()
        
        print("\n" + "=" * 60)
        print(f"🏥 Nursing Portal Tests completed: {self.tests_passed}/{self.tests_run} passed")
        print(f"📊 Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = NursingPortalTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)