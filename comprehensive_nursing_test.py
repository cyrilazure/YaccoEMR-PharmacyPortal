#!/usr/bin/env python
"""
Comprehensive Nursing Portal Tests
"""

import requests
import json
import sys

class NursingPortalTester:
    def __init__(self):
        self.base_url = "https://ghana-emr.preview.emergentagent.com/api"
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
    
    def test_nurse_portal_clock_in_out(self):
        """Test Nurse Portal Clock In/Out"""
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
                self.log_test("Nurse Portal Clock In/Out", False, "Failed to create/login nurse user")
                return False
            nurse_token = login_response.json().get('token')
        else:
            nurse_token = response.json().get('token')
        
        # Use nurse token
        original_token = self.token
        self.token = nurse_token
        
        # Test Clock In
        clock_in_data = {
            "shift_type": "morning",
            "department_id": "medical-ward",
            "notes": "Starting morning shift"
        }
        
        response, error = self.make_request('POST', 'nurse/shifts/clock-in', clock_in_data)
        
        if error:
            self.log_test("Nurse Portal Clock In", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.log_test("Nurse Portal Clock In", True, f"Clock in successful: {data.get('message', '')}")
            
            # Test Clock Out
            clock_out_response, clock_out_error = self.make_request('POST', 'nurse/shifts/clock-out', {
                "handoff_notes": "All patients stable, medications administered as scheduled"
            })
            
            if clock_out_error:
                self.log_test("Nurse Portal Clock Out", False, clock_out_error)
            elif clock_out_response.status_code == 200:
                clock_out_data = clock_out_response.json()
                self.log_test("Nurse Portal Clock Out", True, f"Clock out: {clock_out_data.get('message', '')}")
            else:
                self.log_test("Nurse Portal Clock Out", False, f"Status: {clock_out_response.status_code}, Response: {clock_out_response.text}")
        else:
            self.log_test("Nurse Portal Clock In", False, f"Status: {response.status_code}, Response: {response.text}")
        
        # Restore original token
        self.token = original_token
        return True
    
    def test_nurse_shift_reports(self):
        """Test Nurse Shift Reports (Create, List, Update, Submit)"""
        # Login as nurse
        login_response, login_error = self.make_request('POST', 'auth/login', {
            "email": "testnurse@hospital.com",
            "password": "nurse123"
        })
        
        if login_error or login_response.status_code != 200:
            self.log_test("Nurse Shift Reports", False, "Failed to login as nurse")
            return False
        
        nurse_token = login_response.json().get('token')
        original_token = self.token
        self.token = nurse_token
        
        # Create report
        report_data = {
            "shift_id": "test-shift-001",
            "title": "Test Shift Report",
            "content": "Test report content for end of shift",
            "report_type": "end_of_shift",
            "patient_summary": "All patients stable",
            "critical_events": "No critical events",
            "pending_items": "Follow up on lab results",
            "recommendations": "Continue current care plans"
        }
        
        response, error = self.make_request('POST', 'nurse/reports', report_data)
        
        if error:
            self.log_test("Nurse Shift Reports Create", False, error)
        elif response.status_code == 200:
            data = response.json()
            self.log_test("Nurse Shift Reports Create", True, f"Report created: {data.get('message', '')}")
            if 'report' in data:
                self.nurse_report_id = data['report']['id']
        else:
            self.log_test("Nurse Shift Reports Create", False, f"Status: {response.status_code}, Response: {response.text}")
        
        # List reports
        list_response, list_error = self.make_request('GET', 'nurse/reports')
        
        if list_error:
            self.log_test("Nurse Shift Reports List", False, list_error)
        elif list_response.status_code == 200:
            list_data = list_response.json()
            self.log_test("Nurse Shift Reports List", True, f"Found {list_data.get('total', 0)} reports")
        else:
            self.log_test("Nurse Shift Reports List", False, f"Status: {list_response.status_code}")
        
        # Update report (if we have an ID)
        if self.nurse_report_id:
            update_data = {
                "title": "Updated Test Shift Report",
                "content": "Updated report content",
                "recommendations": "Updated recommendations"
            }
            
            update_response, update_error = self.make_request('PUT', f'nurse/reports/{self.nurse_report_id}', update_data)
            
            if update_error:
                self.log_test("Nurse Shift Reports Update", False, update_error)
            elif update_response.status_code == 200:
                self.log_test("Nurse Shift Reports Update", True, "Report updated successfully")
            else:
                self.log_test("Nurse Shift Reports Update", False, f"Status: {update_response.status_code}")
            
            # Submit report
            submit_response, submit_error = self.make_request('POST', f'nurse/reports/{self.nurse_report_id}/submit')
            
            if submit_error:
                self.log_test("Nurse Shift Reports Submit", False, submit_error)
            elif submit_response.status_code == 200:
                self.log_test("Nurse Shift Reports Submit", True, "Report submitted successfully")
            else:
                self.log_test("Nurse Shift Reports Submit", False, f"Status: {submit_response.status_code}")
        
        # Restore original token
        self.token = original_token
        return True
    
    def test_nurse_assigned_medications(self):
        """Test Assigned Patient Medications"""
        # Login as nurse
        login_response, login_error = self.make_request('POST', 'auth/login', {
            "email": "testnurse@hospital.com",
            "password": "nurse123"
        })
        
        if login_error or login_response.status_code != 200:
            self.log_test("Nurse Assigned Patient Medications", False, "Failed to login as nurse")
            return False
        
        nurse_token = login_response.json().get('token')
        original_token = self.token
        self.token = nurse_token
        
        response, error = self.make_request('GET', 'nurse/all-assigned-medications')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Nurse Assigned Patient Medications", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.log_test("Nurse Assigned Patient Medications", True, 
                         f"Found {data.get('total_patients', 0)} patients with {data.get('total_medications', 0)} medications")
            return True
        else:
            self.log_test("Nurse Assigned Patient Medications", False, f"Status: {response.status_code}, Response: {response.text}")
            return False
    
    def test_it_admin_staff_management(self):
        """Test IT Admin Staff Management"""
        # Login as IT Admin
        login_data = {
            "email": "kofiabedu2019@gmail.com",
            "password": "2I6ZRBkjVn2ZQg7O",
            "hospital_id": "e717ed11-7955-4884-8d6b-a529f918c34f",
            "location_id": "b61d7896-b4ef-436b-868e-94a60b55c64c"
        }
        
        response, error = self.make_request('POST', 'regions/auth/login', login_data)
        
        if error or response.status_code != 200:
            self.log_test("IT Admin Staff Management", False, "Failed to login as IT Admin")
            return False
        
        it_admin_token = response.json().get('token')
        original_token = self.token
        self.token = it_admin_token
        
        hospital_id = "e717ed11-7955-4884-8d6b-a529f918c34f"
        
        # View staff details
        staff_response, staff_error = self.make_request('GET', f'hospital/{hospital_id}/super-admin/staff')
        
        if staff_error:
            self.log_test("IT Admin View Staff Details", False, staff_error)
        elif staff_response.status_code == 200:
            staff_data = staff_response.json()
            self.log_test("IT Admin View Staff Details", True, f"Found {staff_data.get('total', 0)} staff members")
            
            # Test unlock account (use first staff member if available)
            staff_list = staff_data.get('staff', [])
            if staff_list:
                staff_id = staff_list[0].get('id')
                unlock_response, unlock_error = self.make_request('POST', f'hospital/{hospital_id}/super-admin/staff/{staff_id}/unlock')
                
                if unlock_error:
                    self.log_test("IT Admin Unlock Account", False, unlock_error)
                elif unlock_response.status_code == 200:
                    self.log_test("IT Admin Unlock Account", True, "Account unlock successful")
                else:
                    self.log_test("IT Admin Unlock Account", False, f"Status: {unlock_response.status_code}")
            else:
                self.log_test("IT Admin Unlock Account", True, "No staff to unlock (expected)")
        else:
            self.log_test("IT Admin View Staff Details", False, f"Status: {staff_response.status_code}")
        
        # Restore original token
        self.token = original_token
        return True
    
    def test_nursing_supervisor_endpoints_access_control(self):
        """Test that nursing supervisor endpoints properly enforce access control"""
        # Login as IT Admin (who should NOT have supervisor access)
        login_data = {
            "email": "kofiabedu2019@gmail.com",
            "password": "2I6ZRBkjVn2ZQg7O",
            "hospital_id": "e717ed11-7955-4884-8d6b-a529f918c34f",
            "location_id": "b61d7896-b4ef-436b-868e-94a60b55c64c"
        }
        
        response, error = self.make_request('POST', 'regions/auth/login', login_data)
        
        if error or response.status_code != 200:
            self.log_test("Nursing Supervisor Access Control", False, "Failed to login as IT Admin")
            return False
        
        it_admin_token = response.json().get('token')
        original_token = self.token
        self.token = it_admin_token
        
        # Test that IT Admin is properly denied access to supervisor endpoints
        endpoints_to_test = [
            'nursing-supervisor/dashboard',
            'nursing-supervisor/nurses',
            'nursing-supervisor/shifts/current',
            'nursing-supervisor/reports'
        ]
        
        access_properly_denied = True
        for endpoint in endpoints_to_test:
            response, error = self.make_request('GET', endpoint)
            if not error and response.status_code == 403:
                # This is expected - access should be denied
                continue
            else:
                access_properly_denied = False
                break
        
        self.log_test("Nursing Supervisor Access Control", access_properly_denied, 
                     "IT Admin properly denied access to supervisor endpoints (403 Forbidden)")
        
        # Restore original token
        self.token = original_token
        return access_properly_denied
    
    def run_all_tests(self):
        """Run all nursing portal tests"""
        print("🏥 Starting Comprehensive Nursing Portal Tests...")
        print("=" * 60)
        
        # Test 1: Nurse Portal Clock In/Out
        self.test_nurse_portal_clock_in_out()
        
        # Test 2: Nurse Shift Reports (Read/Write)
        self.test_nurse_shift_reports()
        
        # Test 3: Assigned Patient Medications
        self.test_nurse_assigned_medications()
        
        # Test 4: IT Admin Staff Management
        self.test_it_admin_staff_management()
        
        # Test 5: Nursing Supervisor Access Control
        self.test_nursing_supervisor_endpoints_access_control()
        
        print("\n" + "=" * 60)
        print(f"🏥 Nursing Portal Tests completed: {self.tests_passed}/{self.tests_run} passed")
        print(f"📊 Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = NursingPortalTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)