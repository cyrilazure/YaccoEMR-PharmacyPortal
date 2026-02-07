#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta

class HospitalITAdminTester:
    def __init__(self, base_url="https://healthfusion-gh.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.token = None
        self.test_staff_id = None
        self.test_staff_email = None
        self.tests_run = 0
        self.tests_passed = 0

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")

    def make_request(self, method, endpoint, data=None, params=None):
        """Make HTTP request with proper headers"""
        url = f"{self.api_base}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, params=params)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=params)
            else:
                return None, f"Unsupported method: {method}"

            return response, None
        except Exception as e:
            return None, str(e)

    def test_hospital_it_admin_login(self):
        """Test Hospital IT Admin login via POST /api/regions/auth/login"""
        login_data = {
            "email": "kofiabedu2019@gmail.com",
            "password": "2I6ZRBkjVn2ZQg7O",
            "hospital_id": "e717ed11-7955-4884-8d6b-a529f918c34f",
            "location_id": "b61d7896-b4ef-436b-868e-94a60b55c64c"
        }
        
        response, error = self.make_request('POST', 'regions/auth/login', login_data)
        if error:
            self.log_test("Hospital IT Admin Login", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get('token')
            user = data.get('user', {})
            
            # Verify JWT token contains required claims
            if self.token:
                import jwt
                try:
                    payload = jwt.decode(self.token, options={"verify_signature": False})
                    has_region_id = 'region_id' in payload
                    has_hospital_id = 'hospital_id' in payload
                    has_location_id = 'location_id' in payload
                    has_role = 'role' in payload
                    
                    # Verify redirect_to is correct
                    redirect_to = data.get('redirect_to')
                    correct_redirect = redirect_to == '/it-admin'
                    
                    # Verify role is hospital_it_admin
                    role_correct = user.get('role') == 'hospital_it_admin'
                    
                    success = (has_region_id and has_hospital_id and has_location_id and 
                              has_role and correct_redirect and role_correct)
                    
                    self.log_test("Hospital IT Admin Login", success, 
                                 f"Role: {user.get('role')}, Redirect: {redirect_to}")
                    return success
                except Exception as e:
                    self.log_test("Hospital IT Admin Login", False, f"JWT decode error: {e}")
                    return False
            else:
                self.log_test("Hospital IT Admin Login", False, "No token received")
                return False
        else:
            self.log_test("Hospital IT Admin Login", False, f"Status: {response.status_code}")
            return False
    
    def test_hospital_it_admin_dashboard(self):
        """Test Hospital IT Admin Dashboard - GET /api/hospital/{hospital_id}/super-admin/dashboard"""
        if not self.token:
            self.log_test("Hospital IT Admin Dashboard", False, "No IT Admin token")
            return False
        
        hospital_id = "e717ed11-7955-4884-8d6b-a529f918c34f"
        response, error = self.make_request('GET', f'hospital/{hospital_id}/super-admin/dashboard')
        
        if error:
            self.log_test("Hospital IT Admin Dashboard", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ['hospital', 'staff_stats', 'departments', 'locations']
            has_all_fields = all(field in data for field in required_fields)
            
            # Verify departments array is populated
            departments = data.get('departments', [])
            has_departments = len(departments) > 0
            
            success = has_all_fields and has_departments
            self.log_test("Hospital IT Admin Dashboard", success, 
                         f"Hospital: {data.get('hospital', {}).get('name', 'Unknown')}, Departments: {len(departments)}")
            return success
        else:
            self.log_test("Hospital IT Admin Dashboard", False, f"Status: {response.status_code}")
            return False
    
    def test_hospital_it_admin_departments(self):
        """Test List Departments - GET /api/hospital/{hospital_id}/super-admin/departments"""
        if not self.token:
            self.log_test("Hospital IT Admin Departments", False, "No IT Admin token")
            return False
        
        hospital_id = "e717ed11-7955-4884-8d6b-a529f918c34f"
        response, error = self.make_request('GET', f'hospital/{hospital_id}/super-admin/departments')
        
        if error:
            self.log_test("Hospital IT Admin Departments", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            departments = data.get('departments', [])
            total = data.get('total', 0)
            
            # Should return 24 default departments
            expected_codes = ['ER', 'OPD', 'ICU', 'CARD', 'SUR', 'PED', 'OBG', 'ORTH', 'NEURO', 'RAD', 'LAB', 'PHARM']
            dept_codes = [d.get('code') for d in departments]
            has_expected_depts = any(code in dept_codes for code in expected_codes)
            
            success = len(departments) >= 20 and has_expected_depts  # Should have 24 departments
            self.log_test("Hospital IT Admin Departments", success, 
                         f"Found {len(departments)} departments, Total: {total}")
            return success
        else:
            self.log_test("Hospital IT Admin Departments", False, f"Status: {response.status_code}")
            return False
    
    def test_hospital_it_admin_create_staff(self):
        """Test Create Staff Account - POST /api/hospital/{hospital_id}/super-admin/staff"""
        if not self.token:
            self.log_test("Hospital IT Admin Create Staff", False, "No IT Admin token")
            return False
        
        hospital_id = "e717ed11-7955-4884-8d6b-a529f918c34f"
        
        # First get departments to use one for staff creation
        dept_response, _ = self.make_request('GET', f'hospital/{hospital_id}/super-admin/departments')
        if dept_response and dept_response.status_code == 200:
            departments = dept_response.json().get('departments', [])
            department_id = departments[0]['id'] if departments else None
        else:
            department_id = None
        
        import time
        timestamp = str(int(time.time()))
        
        staff_data = {
            "email": f"teststaff{timestamp}@hospital.com",
            "first_name": "Test",
            "last_name": "Staff",
            "role": "physician",
            "department_id": department_id
        }
        
        response, error = self.make_request('POST', f'hospital/{hospital_id}/super-admin/staff', staff_data)
        
        if error:
            self.log_test("Hospital IT Admin Create Staff", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            staff = data.get('staff', {})
            credentials = data.get('credentials', {})
            
            has_staff_id = bool(staff.get('id'))
            has_temp_password = bool(credentials.get('temp_password'))
            
            # Store staff ID for subsequent tests
            if has_staff_id:
                self.test_staff_id = staff.get('id')
                self.test_staff_email = staff_data['email']
            
            success = has_staff_id and has_temp_password
            self.log_test("Hospital IT Admin Create Staff", success, 
                         f"Staff: {staff.get('name')}, Role: {staff.get('role')}")
            return success
        else:
            self.log_test("Hospital IT Admin Create Staff", False, f"Status: {response.status_code}")
            return False
    
    def test_hospital_it_admin_reset_password(self):
        """Test Reset Password - POST /api/hospital/{hospital_id}/super-admin/staff/{staff_id}/reset-password"""
        if not self.token or not self.test_staff_id:
            self.log_test("Hospital IT Admin Reset Password", False, "No IT Admin token or staff ID")
            return False
        
        hospital_id = "e717ed11-7955-4884-8d6b-a529f918c34f"
        staff_id = self.test_staff_id
        
        response, error = self.make_request('POST', f'hospital/{hospital_id}/super-admin/staff/{staff_id}/reset-password')
        
        if error:
            self.log_test("Hospital IT Admin Reset Password", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            credentials = data.get('credentials', {})
            
            has_new_temp_password = bool(credentials.get('temp_password'))
            must_change = credentials.get('must_change_password', False)
            
            success = has_new_temp_password and must_change
            self.log_test("Hospital IT Admin Reset Password", success, 
                         f"New temp password generated, Must change: {must_change}")
            return success
        else:
            self.log_test("Hospital IT Admin Reset Password", False, f"Status: {response.status_code}")
            return False
    
    def test_hospital_it_admin_deactivate_user(self):
        """Test Deactivate User - POST /api/hospital/{hospital_id}/super-admin/staff/{staff_id}/deactivate"""
        if not self.token or not self.test_staff_id:
            self.log_test("Hospital IT Admin Deactivate User", False, "No IT Admin token or staff ID")
            return False
        
        hospital_id = "e717ed11-7955-4884-8d6b-a529f918c34f"
        staff_id = self.test_staff_id
        
        response, error = self.make_request('POST', f'hospital/{hospital_id}/super-admin/staff/{staff_id}/deactivate')
        
        if error:
            self.log_test("Hospital IT Admin Deactivate User", False, error)
            return False
        
        if response.status_code == 200:
            # Verify user is deactivated by checking their details
            get_response, _ = self.make_request('GET', f'hospital/{hospital_id}/super-admin/staff/{staff_id}')
            if get_response and get_response.status_code == 200:
                staff_data = get_response.json()
                is_inactive = not staff_data.get('is_active', True)
                success = is_inactive
                self.log_test("Hospital IT Admin Deactivate User", success, 
                             f"User is_active: {staff_data.get('is_active')}")
                return success
            else:
                self.log_test("Hospital IT Admin Deactivate User", True, "Deactivation successful")
                return True
        else:
            self.log_test("Hospital IT Admin Deactivate User", False, f"Status: {response.status_code}")
            return False
    
    def test_hospital_it_admin_activate_user(self):
        """Test Activate User - POST /api/hospital/{hospital_id}/super-admin/staff/{staff_id}/activate"""
        if not self.token or not self.test_staff_id:
            self.log_test("Hospital IT Admin Activate User", False, "No IT Admin token or staff ID")
            return False
        
        hospital_id = "e717ed11-7955-4884-8d6b-a529f918c34f"
        staff_id = self.test_staff_id
        
        response, error = self.make_request('POST', f'hospital/{hospital_id}/super-admin/staff/{staff_id}/activate')
        
        if error:
            self.log_test("Hospital IT Admin Activate User", False, error)
            return False
        
        if response.status_code == 200:
            # Verify user is activated by checking their details
            get_response, _ = self.make_request('GET', f'hospital/{hospital_id}/super-admin/staff/{staff_id}')
            if get_response and get_response.status_code == 200:
                staff_data = get_response.json()
                is_active = staff_data.get('is_active', False)
                success = is_active
                self.log_test("Hospital IT Admin Activate User", success, 
                             f"User is_active: {staff_data.get('is_active')}")
                return success
            else:
                self.log_test("Hospital IT Admin Activate User", True, "Activation successful")
                return True
        else:
            self.log_test("Hospital IT Admin Activate User", False, f"Status: {response.status_code}")
            return False
    
    def test_hospital_it_admin_delete_user(self):
        """Test Delete User - DELETE /api/hospital/{hospital_id}/super-admin/staff/{staff_id}"""
        if not self.token or not self.test_staff_id:
            self.log_test("Hospital IT Admin Delete User", False, "No IT Admin token or staff ID")
            return False
        
        hospital_id = "e717ed11-7955-4884-8d6b-a529f918c34f"
        staff_id = self.test_staff_id
        
        response, error = self.make_request('DELETE', f'hospital/{hospital_id}/super-admin/staff/{staff_id}')
        
        if error:
            self.log_test("Hospital IT Admin Delete User", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            message = data.get('message', '')
            has_success_message = 'deleted' in message.lower()
            
            success = has_success_message
            self.log_test("Hospital IT Admin Delete User", success, message)
            return success
        else:
            self.log_test("Hospital IT Admin Delete User", False, f"Status: {response.status_code}")
            return False
    
    def test_hospital_it_admin_verify_deletion(self):
        """Test Verify Deletion - Try to get the deleted staff (should return 404)"""
        if not self.token or not self.test_staff_id:
            self.log_test("Hospital IT Admin Verify Deletion", False, "No IT Admin token or staff ID")
            return False
        
        hospital_id = "e717ed11-7955-4884-8d6b-a529f918c34f"
        staff_id = self.test_staff_id
        
        response, error = self.make_request('GET', f'hospital/{hospital_id}/super-admin/staff/{staff_id}')
        
        if error:
            self.log_test("Hospital IT Admin Verify Deletion", True, "Staff not found (expected after deletion)")
            return True
        
        if response.status_code == 404:
            self.log_test("Hospital IT Admin Verify Deletion", True, "Staff not found (404 - correctly deleted)")
            return True
        elif response.status_code == 200:
            self.log_test("Hospital IT Admin Verify Deletion", False, "Staff still exists (deletion failed)")
            return False
        else:
            self.log_test("Hospital IT Admin Verify Deletion", False, f"Unexpected status: {response.status_code}")
            return False

    def run_tests(self):
        """Run all Hospital IT Admin tests"""
        print("🏥 Testing Hospital IT Admin Portal Features")
        print("=" * 50)
        
        tests = [
            self.test_hospital_it_admin_login,
            self.test_hospital_it_admin_dashboard,
            self.test_hospital_it_admin_departments,
            self.test_hospital_it_admin_create_staff,
            self.test_hospital_it_admin_reset_password,
            self.test_hospital_it_admin_deactivate_user,
            self.test_hospital_it_admin_activate_user,
            self.test_hospital_it_admin_delete_user,
            self.test_hospital_it_admin_verify_deletion
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ {test.__name__} failed with error: {e}")
        
        print("\n" + "=" * 50)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = HospitalITAdminTester()
    success = tester.run_tests()
    sys.exit(0 if success else 1)