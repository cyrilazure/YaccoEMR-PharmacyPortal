#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
import jwt

class YaccoEMRTester:
    def __init__(self, base_url="https://portal-index.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test variables for review request
        self.super_admin_token = None
        self.super_admin_id = None
        self.test_patient_id = None
        self.test_patient_mrn = None
        self.cash_patient_id = None
        self.nurse_token = None
        self.nurse_user_id = None
        self.nurse_shift_id = None

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

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

    def test_health_check(self):
        """Test basic API health"""
        response, error = self.make_request('GET', '')
        if error:
            self.log_test("Health Check", False, error)
            return False
        
        success = response.status_code == 200
        self.log_test("Health Check", success, f"Status: {response.status_code}")
        return success

    def test_super_admin_login(self):
        """Test Super Admin Login - POST /api/auth/login with ygtnetworks@gmail.com / test123"""
        login_data = {
            "email": "ygtnetworks@gmail.com",
            "password": "test123"
        }
        
        response, error = self.make_request('POST', 'auth/login', login_data)
        if error:
            self.log_test("Super Admin Login", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.super_admin_token = data.get('token')
            user = data.get('user', {})
            self.super_admin_id = user.get('id')
            
            # Verify user role is super_admin
            is_super_admin = user.get('role') == 'super_admin'
            has_token = bool(self.super_admin_token)
            
            # Verify JWT token contains role=super_admin
            if has_token:
                try:
                    payload = jwt.decode(self.super_admin_token, options={"verify_signature": False})
                    token_role = payload.get('role')
                    role_matches = token_role == 'super_admin'
                    success = is_super_admin and has_token and role_matches
                    
                    details = f"Email: {user.get('email')}, Role: {user.get('role')}, Token Role: {token_role}"
                    self.log_test("Super Admin Login", success, details)
                    
                    # Set token for subsequent requests
                    self.token = self.super_admin_token
                    return success
                except Exception as e:
                    self.log_test("Super Admin Login", False, f"JWT decode error: {e}")
                    return False
            else:
                self.log_test("Super Admin Login", False, "No token received")
                return False
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Super Admin Login", False, error_msg)
            return False

    def test_patient_creation_with_mrn_and_payment(self):
        """Test Patient Creation with MRN and Payment Type - POST /api/patients"""
        if not self.super_admin_token:
            self.log_test("Patient Creation with MRN and Payment", False, "No super admin token")
            return False
        
        patient_data = {
            "first_name": "Test",
            "last_name": "Patient",
            "date_of_birth": "1990-01-15",
            "gender": "male",
            "mrn": "MRN-CUSTOM-001",
            "payment_type": "insurance",
            "insurance_provider": "NHIS",
            "insurance_id": "NHIS-12345678",
            "adt_notification": True
        }
        
        response, error = self.make_request('POST', 'patients', patient_data)
        if error:
            self.log_test("Patient Creation with MRN and Payment", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.test_patient_id = data.get('id')
            self.test_patient_mrn = data.get('mrn')
            
            # Verify all required fields are present
            has_id = bool(self.test_patient_id)
            has_mrn = data.get('mrn') == "MRN-CUSTOM-001"
            has_payment_type = data.get('payment_type') == "insurance"
            has_insurance_provider = data.get('insurance_provider') == "NHIS"
            has_insurance_id = data.get('insurance_id') == "NHIS-12345678"
            has_adt_notification = data.get('adt_notification') == True
            
            success = all([has_id, has_mrn, has_payment_type, has_insurance_provider, 
                          has_insurance_id, has_adt_notification])
            
            details = f"ID: {self.test_patient_id}, MRN: {data.get('mrn')}, Payment: {data.get('payment_type')}, Insurance: {data.get('insurance_provider')}"
            self.log_test("Patient Creation with MRN and Payment", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Patient Creation with MRN and Payment", False, error_msg)
            return False

    def test_patient_creation_cash_payment(self):
        """Test Patient Creation with Cash Payment - POST /api/patients"""
        if not self.super_admin_token:
            self.log_test("Patient Creation with Cash Payment", False, "No super admin token")
            return False
        
        patient_data = {
            "first_name": "Cash",
            "last_name": "Patient",
            "date_of_birth": "1985-06-20",
            "gender": "female",
            "payment_type": "cash",
            "adt_notification": True
        }
        
        response, error = self.make_request('POST', 'patients', patient_data)
        if error:
            self.log_test("Patient Creation with Cash Payment", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.cash_patient_id = data.get('id')
            
            # Verify cash payment fields
            has_id = bool(self.cash_patient_id)
            has_payment_type = data.get('payment_type') == "cash"
            no_insurance_provider = data.get('insurance_provider') is None
            no_insurance_id = data.get('insurance_id') is None
            has_adt_notification = data.get('adt_notification') == True
            
            success = all([has_id, has_payment_type, no_insurance_provider, 
                          no_insurance_id, has_adt_notification])
            
            details = f"ID: {self.cash_patient_id}, Payment: {data.get('payment_type')}, No Insurance Info: {no_insurance_provider and no_insurance_id}"
            self.log_test("Patient Creation with Cash Payment", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Patient Creation with Cash Payment", False, error_msg)
            return False

    def test_nurse_login(self):
        """Test Nurse Login - testnurse@hospital.com / test123"""
        login_data = {
            "email": "testnurse@hospital.com",
            "password": "test123"
        }
        
        response, error = self.make_request('POST', 'auth/login', login_data)
        if error:
            self.log_test("Nurse Login", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.nurse_token = data.get('token')
            user = data.get('user', {})
            self.nurse_user_id = user.get('id')
            
            # Verify user role is nurse
            is_nurse = user.get('role') == 'nurse'
            has_token = bool(self.nurse_token)
            
            success = is_nurse and has_token
            details = f"Email: {user.get('email')}, Role: {user.get('role')}"
            self.log_test("Nurse Login", success, details)
            return success
        elif response.status_code == 401:
            # Nurse user doesn't exist, let's create one first
            return self.create_nurse_user_and_login()
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Nurse Login", False, error_msg)
            return False

    def create_nurse_user_and_login(self):
        """Create nurse user and login"""
        # First register a nurse user
        nurse_data = {
            "email": "testnurse@hospital.com",
            "password": "test123",
            "first_name": "Test",
            "last_name": "Nurse",
            "role": "nurse",
            "department": "Emergency Department"
        }
        
        response, error = self.make_request('POST', 'auth/register', nurse_data)
        if error:
            self.log_test("Create Nurse User", False, error)
            return False
        
        if response.status_code in [200, 201]:
            # Registration successful, now login
            return self.test_nurse_login()
        elif response.status_code == 400:
            # User already exists, try login again
            return self.test_nurse_login()
        else:
            self.log_test("Create Nurse User", False, f"Status: {response.status_code}")
            return False

    def test_nurse_shift_clock_in(self):
        """Test Nurse Shift Clock-In - POST /api/nurse/shifts/clock-in"""
        if not self.nurse_token:
            self.log_test("Nurse Shift Clock-In", False, "No nurse token")
            return False
        
        # Switch to nurse token
        original_token = self.token
        self.token = self.nurse_token
        
        clock_in_data = {
            "shift_type": "morning"
        }
        
        response, error = self.make_request('POST', 'nurse/shifts/clock-in', clock_in_data)
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Nurse Shift Clock-In", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            shift = data.get('shift', {})
            self.nurse_shift_id = shift.get('id')
            
            has_shift_id = bool(self.nurse_shift_id)
            correct_shift_type = shift.get('shift_type') == 'morning'
            is_active = shift.get('status') == 'active'
            
            success = has_shift_id and correct_shift_type and is_active
            details = f"Shift ID: {self.nurse_shift_id}, Type: {shift.get('shift_type')}, Status: {shift.get('status')}"
            self.log_test("Nurse Shift Clock-In", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Nurse Shift Clock-In", False, error_msg)
            return False

    def test_nurse_current_shift(self):
        """Test Get Current Shift - GET /api/nurse/current-shift"""
        if not self.nurse_token:
            self.log_test("Get Current Shift", False, "No nurse token")
            return False
        
        # Switch to nurse token
        original_token = self.token
        self.token = self.nurse_token
        
        response, error = self.make_request('GET', 'nurse/current-shift')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Get Current Shift", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            active_shift = data.get('active_shift')
            
            if active_shift:
                has_shift_id = bool(active_shift.get('id'))
                is_active = active_shift.get('status') == 'active'
                has_shift_type = bool(active_shift.get('shift_type'))
                
                success = has_shift_id and is_active and has_shift_type
                details = f"Active Shift: {active_shift.get('id')}, Type: {active_shift.get('shift_type')}"
                self.log_test("Get Current Shift", success, details)
                return success
            else:
                self.log_test("Get Current Shift", False, "No active shift found")
                return False
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Get Current Shift", False, error_msg)
            return False

    def test_nurse_shift_clock_out(self):
        """Test Nurse Shift Clock-Out - POST /api/nurse/shifts/clock-out"""
        if not self.nurse_token:
            self.log_test("Nurse Shift Clock-Out", False, "No nurse token")
            return False
        
        # Switch to nurse token
        original_token = self.token
        self.token = self.nurse_token
        
        response, error = self.make_request('POST', 'nurse/shifts/clock-out')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Nurse Shift Clock-Out", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            shift = data.get('shift', {})
            
            is_completed = shift.get('status') == 'completed'
            has_end_time = bool(shift.get('end_time'))
            
            success = is_completed and has_end_time
            details = f"Status: {shift.get('status')}, End Time: {shift.get('end_time')}"
            self.log_test("Nurse Shift Clock-Out", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Nurse Shift Clock-Out", False, error_msg)
            return False

    def run_review_tests(self):
        """Run all tests for the review request"""
        print("🧪 Starting Yacco EMR Backend Testing - Review Request")
        print("=" * 60)
        
        # Test sequence for review request
        tests = [
            self.test_health_check,
            self.test_super_admin_login,
            self.test_patient_creation_with_mrn_and_payment,
            self.test_patient_creation_cash_payment,
            self.test_nurse_login,
            self.test_nurse_shift_clock_in,
            self.test_nurse_current_shift,
            self.test_nurse_shift_clock_out
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_test(test.__name__, False, f"Exception: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY")
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Print failed tests
        failed_tests = [t for t in self.test_results if not t['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = YaccoEMRTester()
    success = tester.run_review_tests()
    sys.exit(0 if success else 1)