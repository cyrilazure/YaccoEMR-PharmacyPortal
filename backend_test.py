#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
import jwt

class YaccoEMRTester:
    def __init__(self, base_url="https://emr-postgres-move.preview.emergentagent.com"):
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
        self.appointment_id = None
        self.test_hospital_id = None
        self.initial_department_count = 0

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

    def test_nurse_region_login(self):
        """Test Nurse Login via Region-Based Auth - POST /api/regions/auth/login"""
        login_data = {
            "email": "testnurse@hospital.com",
            "password": "test123",
            "hospital_id": "e717ed11-7955-4884-8d6b-a529f918c34f",
            "location_id": "b61d7896-b4ef-436b-868e-94a60b55c64c"
        }
        
        response, error = self.make_request('POST', 'regions/auth/login', login_data)
        if error:
            self.log_test("Nurse Region-Based Login", False, error)
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
            details = f"Email: {user.get('email')}, Role: {user.get('role')}, Hospital: {login_data['hospital_id']}"
            self.log_test("Nurse Region-Based Login", success, details)
            return success
        elif response.status_code == 401:
            # Nurse user doesn't exist, let's create one first
            return self.create_nurse_user_and_region_login()
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Nurse Region-Based Login", False, error_msg)
            return False

    def create_nurse_user_and_region_login(self):
        """Create nurse user with organization context and login via region auth"""
        # First register a nurse user with organization_id
        nurse_data = {
            "email": "testnurse@hospital.com",
            "password": "test123",
            "first_name": "Test",
            "last_name": "Nurse",
            "role": "nurse",
            "department": "Emergency Department",
            "organization_id": "e717ed11-7955-4884-8d6b-a529f918c34f"
        }
        
        response, error = self.make_request('POST', 'auth/register', nurse_data)
        if error:
            self.log_test("Create Nurse User for Region Auth", False, error)
            return False
        
        if response.status_code in [200, 201]:
            # Registration successful, now login via region auth
            return self.test_nurse_region_login()
        elif response.status_code == 400:
            # User already exists, try region login again
            return self.test_nurse_region_login()
        else:
            self.log_test("Create Nurse User for Region Auth", False, f"Status: {response.status_code}")
            return False

    def test_nurse_current_shift_before_clock_in(self):
        """Test Get Current Shift before clock-in - should be null"""
        if not self.nurse_token:
            self.log_test("Get Current Shift (Before Clock-In)", False, "No nurse token")
            return False
        
        # Switch to nurse token
        original_token = self.token
        self.token = self.nurse_token
        
        response, error = self.make_request('GET', 'nurse/current-shift')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Get Current Shift (Before Clock-In)", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            active_shift = data.get('active_shift')
            
            # Should be null if not clocked in
            success = active_shift is None
            details = f"Active Shift: {active_shift}"
            self.log_test("Get Current Shift (Before Clock-In)", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Get Current Shift (Before Clock-In)", False, error_msg)
            return False

    def test_nurse_clock_out_if_active(self):
        """Test Clock Out if already clocked in - POST /api/nurse/shifts/clock-out"""
        if not self.nurse_token:
            self.log_test("Clock Out (If Active)", False, "No nurse token")
            return False
        
        # Switch to nurse token
        original_token = self.token
        self.token = self.nurse_token
        
        response, error = self.make_request('POST', 'nurse/shifts/clock-out', params={"handoff_notes": "Test"})
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Clock Out (If Active)", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            message = data.get('message', '')
            success = 'clocked out' in message.lower()
            details = f"Message: {message}"
            self.log_test("Clock Out (If Active)", success, details)
            return success
        elif response.status_code == 400:
            # Expected if no active shift
            details = "No active shift found (expected)"
            self.log_test("Clock Out (If Active)", True, details)
            return True
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Clock Out (If Active)", False, error_msg)
            return False

    def test_nurse_clock_in_night_shift(self):
        """Test Clock In with night shift - POST /api/nurse/shifts/clock-in"""
        if not self.nurse_token:
            self.log_test("Nurse Clock In (Night Shift)", False, "No nurse token")
            return False
        
        # Switch to nurse token
        original_token = self.token
        self.token = self.nurse_token
        
        clock_in_data = {
            "shift_type": "night"
        }
        
        response, error = self.make_request('POST', 'nurse/shifts/clock-in', clock_in_data)
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Nurse Clock In (Night Shift)", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            shift = data.get('shift', {})
            self.nurse_shift_id = shift.get('id')
            
            has_shift_id = bool(self.nurse_shift_id)
            correct_shift_type = shift.get('shift_type') == 'night'
            is_active = shift.get('is_active') == True
            
            success = has_shift_id and correct_shift_type and is_active
            details = f"Shift ID: {self.nurse_shift_id}, Type: {shift.get('shift_type')}, Active: {shift.get('is_active')}"
            self.log_test("Nurse Clock In (Night Shift)", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Nurse Clock In (Night Shift)", False, error_msg)
            return False

    def test_nurse_current_shift_after_clock_in(self):
        """Test Get Current Shift after clock-in - should have active_shift"""
        if not self.nurse_token:
            self.log_test("Get Current Shift (After Clock-In)", False, "No nurse token")
            return False
        
        # Switch to nurse token
        original_token = self.token
        self.token = self.nurse_token
        
        response, error = self.make_request('GET', 'nurse/current-shift')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Get Current Shift (After Clock-In)", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            active_shift = data.get('active_shift')
            
            if active_shift:
                has_shift_id = bool(active_shift.get('id'))
                is_active = active_shift.get('is_active') == True
                has_shift_type = bool(active_shift.get('shift_type'))
                
                success = has_shift_id and is_active and has_shift_type
                details = f"Active Shift: {active_shift.get('id')}, Type: {active_shift.get('shift_type')}, Active: {active_shift.get('is_active')}"
                self.log_test("Get Current Shift (After Clock-In)", success, details)
                return success
            else:
                self.log_test("Get Current Shift (After Clock-In)", False, "No active shift found after clock-in")
                return False
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Get Current Shift (After Clock-In)", False, error_msg)
            return False

    def test_nurse_mar_due_endpoint(self):
        """Test MAR Due Endpoint - GET /api/nurse/mar/due?window_minutes=60"""
        if not self.nurse_token:
            self.log_test("MAR Due Endpoint", False, "No nurse token")
            return False
        
        # Switch to nurse token
        original_token = self.token
        self.token = self.nurse_token
        
        response, error = self.make_request('GET', 'nurse/mar/due', params={"window_minutes": 60})
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("MAR Due Endpoint", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_overdue = 'overdue' in data
            has_upcoming = 'upcoming' in data
            has_total = 'total' in data
            no_access_error = 'Access restricted' not in str(data)
            
            success = has_overdue and has_upcoming and has_total and no_access_error
            details = f"Response: {data}"
            self.log_test("MAR Due Endpoint", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
                # Check if it's an access restriction error
                if 'Access restricted' in error_msg:
                    self.log_test("MAR Due Endpoint", False, f"Access restricted error: {error_msg}")
                else:
                    self.log_test("MAR Due Endpoint", False, error_msg)
            except:
                error_msg = f'Status: {response.status_code}'
                self.log_test("MAR Due Endpoint", False, error_msg)
            return False

    def test_nurse_dashboard_stats(self):
        """Test Dashboard Stats - GET /api/nurse/dashboard/stats"""
        if not self.nurse_token:
            self.log_test("Nurse Dashboard Stats", False, "No nurse token")
            return False
        
        # Switch to nurse token
        original_token = self.token
        self.token = self.nurse_token
        
        response, error = self.make_request('GET', 'nurse/dashboard/stats')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Nurse Dashboard Stats", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_active_shift = 'active_shift' in data
            
            success = has_active_shift
            details = f"Has active_shift data: {has_active_shift}"
            self.log_test("Nurse Dashboard Stats", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Nurse Dashboard Stats", False, error_msg)
            return False

    def test_nurse_final_clock_out(self):
        """Test Final Clock Out - POST /api/nurse/shifts/clock-out"""
        if not self.nurse_token:
            self.log_test("Final Clock Out", False, "No nurse token")
            return False
        
        # Switch to nurse token
        original_token = self.token
        self.token = self.nurse_token
        
        response, error = self.make_request('POST', 'nurse/shifts/clock-out', params={"handoff_notes": "Handoff"})
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Final Clock Out", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            message = data.get('message', '')
            success = 'clocked out' in message.lower()
            details = f"Message: {message}"
            self.log_test("Final Clock Out", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Final Clock Out", False, error_msg)
            return False

    def test_verify_final_clock_out(self):
        """Test Verify Clock Out - GET /api/nurse/current-shift should be null"""
        if not self.nurse_token:
            self.log_test("Verify Final Clock Out", False, "No nurse token")
            return False
        
        # Switch to nurse token
        original_token = self.token
        self.token = self.nurse_token
        
        response, error = self.make_request('GET', 'nurse/current-shift')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Verify Final Clock Out", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            active_shift = data.get('active_shift')
            
            # Should be null after clock out
            success = active_shift is None
            details = f"Active Shift after clock out: {active_shift}"
            self.log_test("Verify Final Clock Out", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Verify Final Clock Out", False, error_msg)
            return False

    def run_nurse_portal_clock_flow_tests(self):
        """Run Nurse Portal Clock In/Out Flow Tests as specified in review request"""
        print("🧪 Starting Nurse Portal Clock In/Out Flow Testing")
        print("=" * 60)
        print("Test User: testnurse@hospital.com / test123")
        print("Hospital ID: e717ed11-7955-4884-8d6b-a529f918c34f")
        print("Location ID: b61d7896-b4ef-436b-868e-94a60b55c64c")
        print("=" * 60)
        
        # Test sequence for nurse portal clock in/out flow
        tests = [
            self.test_health_check,
            self.test_nurse_region_login,
            self.test_nurse_current_shift_before_clock_in,
            self.test_nurse_clock_out_if_active,
            self.test_nurse_clock_in_night_shift,
            self.test_nurse_current_shift_after_clock_in,
            self.test_nurse_mar_due_endpoint,
            self.test_nurse_dashboard_stats,
            self.test_nurse_final_clock_out,
            self.test_verify_final_clock_out
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_test(test.__name__, False, f"Exception: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 NURSE PORTAL CLOCK IN/OUT FLOW TEST SUMMARY")
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

    def test_super_admin_auth_me(self):
        """Test Super Admin Auth Me - GET /api/auth/me with super admin token"""
        if not self.super_admin_token:
            self.log_test("Super Admin Auth Me", False, "No super admin token")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', 'auth/me')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Super Admin Auth Me", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify user details
            is_super_admin = data.get('role') == 'super_admin'
            has_email = data.get('email') == 'ygtnetworks@gmail.com'
            has_id = bool(data.get('id'))
            
            success = is_super_admin and has_email and has_id
            details = f"Role: {data.get('role')}, Email: {data.get('email')}, ID: {data.get('id')}"
            self.log_test("Super Admin Auth Me", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Super Admin Auth Me", False, error_msg)
            return False

    def test_super_admin_system_stats(self):
        """Test Super Admin System Stats - GET /api/admin/system/stats"""
        if not self.super_admin_token:
            self.log_test("Super Admin System Stats", False, "No super admin token")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', 'admin/system/stats')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Super Admin System Stats", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify response structure
            has_organizations = 'organizations' in data
            has_users_by_role = 'users_by_role' in data
            has_activity_trend = 'activity_trend' in data
            has_timestamp = 'timestamp' in data
            
            success = has_organizations and has_users_by_role and has_activity_trend and has_timestamp
            details = f"Organizations: {has_organizations}, Users by Role: {has_users_by_role}, Activity Trend: {has_activity_trend}"
            self.log_test("Super Admin System Stats", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Super Admin System Stats", False, error_msg)
            return False

    def test_super_admin_system_health(self):
        """Test Super Admin System Health - GET /api/admin/system/health"""
        if not self.super_admin_token:
            self.log_test("Super Admin System Health", False, "No super admin token")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', 'admin/system/health')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Super Admin System Health", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify response structure
            has_status = 'status' in data
            has_checks = 'checks' in data
            has_stats = 'stats' in data
            has_timestamp = 'timestamp' in data
            
            success = has_status and has_checks and has_stats and has_timestamp
            details = f"Status: {data.get('status')}, Checks: {len(data.get('checks', []))}, Stats: {bool(data.get('stats'))}"
            self.log_test("Super Admin System Health", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Super Admin System Health", False, error_msg)
            return False

    def test_super_admin_organizations_pending(self):
        """Test Super Admin Organizations Pending - GET /api/organizations/pending"""
        if not self.super_admin_token:
            self.log_test("Super Admin Organizations Pending", False, "No super admin token")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', 'organizations/pending')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Super Admin Organizations Pending", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            
            # Should return a dict with organizations key
            has_organizations = 'organizations' in data
            has_count = 'count' in data
            organizations_list = data.get('organizations', [])
            is_list = isinstance(organizations_list, list)
            
            success = has_organizations and has_count and is_list
            details = f"Successfully returned {len(organizations_list)} pending organizations"
            self.log_test("Super Admin Organizations Pending", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Super Admin Organizations Pending", False, error_msg)
            return False

    def run_super_admin_review_tests(self):
        """Run Super Admin tests for the review request"""
        print("🧪 Starting Super Admin Backend Testing - Review Request")
        print("=" * 60)
        print("Testing Super Admin Login and Access to Platform Owner Endpoints")
        print("=" * 60)
        
        # Test sequence for super admin review request
        tests = [
            self.test_health_check,
            self.test_super_admin_login,
            self.test_super_admin_auth_me,
            self.test_super_admin_system_stats,
            self.test_super_admin_system_health,
            self.test_super_admin_organizations_pending
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_test(test.__name__, False, f"Exception: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 SUPER ADMIN TEST SUMMARY")
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

    def test_mrn_auto_generation(self):
        """Test MRN Auto-Generation - POST /api/patients with empty mrn field"""
        if not self.super_admin_token:
            self.log_test("MRN Auto-Generation", False, "No super admin token")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        patient_data = {
            "first_name": "Auto",
            "last_name": "MRN",
            "date_of_birth": "1992-03-10",
            "gender": "female",
            "mrn": "",  # Empty MRN field to test auto-generation
            "payment_type": "cash"
        }
        
        response, error = self.make_request('POST', 'patients', patient_data)
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("MRN Auto-Generation", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            generated_mrn = data.get('mrn')
            
            # Verify MRN was auto-generated and starts with MRN-
            has_mrn = bool(generated_mrn)
            starts_with_mrn = generated_mrn.startswith('MRN') if generated_mrn else False
            is_not_empty = generated_mrn != "" if generated_mrn else False
            
            success = has_mrn and starts_with_mrn and is_not_empty
            details = f"Generated MRN: {generated_mrn}, Starts with MRN: {starts_with_mrn}"
            self.log_test("MRN Auto-Generation", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("MRN Auto-Generation", False, error_msg)
            return False

    def test_force_clock_out_setup(self):
        """Setup for Force Clock-Out test - Login as nurse and clock in"""
        # First login as nurse via region-based auth
        login_data = {
            "email": "testnurse@hospital.com",
            "password": "test123",
            "hospital_id": "e717ed11-7955-4884-8d6b-a529f918c34f",
            "location_id": "b61d7896-b4ef-436b-868e-94a60b55c64c"
        }
        
        response, error = self.make_request('POST', 'regions/auth/login', login_data)
        if error:
            self.log_test("Force Clock-Out Setup (Nurse Login)", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.nurse_token = data.get('token')
            user = data.get('user', {})
            self.nurse_user_id = user.get('id')
            
            # Now clock in as nurse
            original_token = self.token
            self.token = self.nurse_token
            
            clock_in_data = {
                "shift_type": "morning"
            }
            
            response, error = self.make_request('POST', 'nurse/shifts/clock-in', clock_in_data)
            
            # Restore original token
            self.token = original_token
            
            if error:
                self.log_test("Force Clock-Out Setup (Clock In)", False, error)
                return False
            
            if response.status_code == 200:
                data = response.json()
                shift = data.get('shift', {})
                self.nurse_shift_id = shift.get('id')
                
                success = bool(self.nurse_shift_id)
                details = f"Nurse ID: {self.nurse_user_id}, Shift ID: {self.nurse_shift_id}"
                self.log_test("Force Clock-Out Setup", success, details)
                return success
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', f'Status: {response.status_code}')
                except:
                    error_msg = f'Status: {response.status_code}'
                self.log_test("Force Clock-Out Setup (Clock In)", False, error_msg)
                return False
        elif response.status_code == 401:
            # Nurse user doesn't exist, create one first
            return self.create_nurse_user_and_force_clock_out_setup()
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Force Clock-Out Setup (Nurse Login)", False, error_msg)
            return False

    def create_nurse_user_and_force_clock_out_setup(self):
        """Create nurse user and setup for force clock-out test"""
        # First register a nurse user with organization context
        nurse_data = {
            "email": "testnurse@hospital.com",
            "password": "test123",
            "first_name": "Test",
            "last_name": "Nurse",
            "role": "nurse",
            "department": "Emergency Department",
            "organization_id": "e717ed11-7955-4884-8d6b-a529f918c34f"
        }
        
        response, error = self.make_request('POST', 'auth/register', nurse_data)
        if error:
            self.log_test("Create Nurse User for Force Clock-Out", False, error)
            return False
        
        if response.status_code in [200, 201]:
            # Registration successful, now setup force clock-out test
            return self.test_force_clock_out_setup()
        elif response.status_code == 400:
            # User already exists, try setup again
            return self.test_force_clock_out_setup()
        else:
            self.log_test("Create Nurse User for Force Clock-Out", False, f"Status: {response.status_code}")
            return False

    def test_force_clock_out_as_super_admin(self):
        """Test Force Clock-Out as super_admin - POST /api/nursing-supervisor/force-clock-out/{nurse_id}"""
        if not self.super_admin_token or not self.nurse_user_id:
            self.log_test("Force Clock-Out (Super Admin)", False, "Missing super admin token or nurse user ID")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('POST', f'nursing-supervisor/force-clock-out/{self.nurse_user_id}', 
                                          params={"reason": "Test force clock-out"})
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Force Clock-Out (Super Admin)", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            message = data.get('message', '')
            
            success = 'clocked out' in message.lower()
            details = f"Message: {message}"
            self.log_test("Force Clock-Out (Super Admin)", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Force Clock-Out (Super Admin)", False, error_msg)
            return False

    def test_handoff_notes_api(self):
        """Test Handoff Notes API - GET /api/nursing-supervisor/handoff-notes?hours=24"""
        if not self.super_admin_token:
            self.log_test("Handoff Notes API", False, "No super admin token")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', 'nursing-supervisor/handoff-notes', params={"hours": 24})
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Handoff Notes API", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify response structure
            has_handoff_notes = 'handoff_notes' in data
            has_total = 'total' in data
            handoff_notes = data.get('handoff_notes', [])
            is_list = isinstance(handoff_notes, list)
            
            # Check if handoff notes include patient info
            has_patient_info = True
            if handoff_notes:
                for note in handoff_notes:
                    if 'patients' not in note:
                        has_patient_info = False
                        break
            
            success = has_handoff_notes and has_total and is_list
            details = f"Handoff notes count: {len(handoff_notes)}, Has patient info: {has_patient_info}"
            self.log_test("Handoff Notes API", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Handoff Notes API", False, error_msg)
            return False

    def test_create_appointment(self):
        """Test Create Appointment - POST /api/appointments"""
        if not self.super_admin_token or not self.test_patient_id:
            self.log_test("Create Appointment", False, "Missing super admin token or patient ID")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        appointment_data = {
            "patient_id": self.test_patient_id,
            "provider_id": self.super_admin_id,
            "appointment_type": "follow_up",
            "date": "2025-02-06",
            "start_time": "10:00",
            "end_time": "10:30",
            "reason": "Follow-up appointment"
        }
        
        response, error = self.make_request('POST', 'appointments', appointment_data)
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Create Appointment", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            appointment_id = data.get('id')
            
            # Verify appointment fields
            has_id = bool(appointment_id)
            correct_patient = data.get('patient_id') == self.test_patient_id
            correct_provider = data.get('provider_id') == self.super_admin_id
            correct_type = data.get('appointment_type') == 'follow_up'
            correct_date = data.get('date') == '2025-02-06'
            
            success = has_id and correct_patient and correct_provider and correct_type and correct_date
            details = f"Appointment ID: {appointment_id}, Patient: {correct_patient}, Provider: {correct_provider}"
            self.log_test("Create Appointment", success, details)
            
            # Store appointment ID for next test
            self.appointment_id = appointment_id
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Create Appointment", False, error_msg)
            return False

    def test_get_appointments(self):
        """Test Get Appointments - GET /api/appointments"""
        if not self.super_admin_token:
            self.log_test("Get Appointments", False, "No super admin token")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', 'appointments')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Get Appointments", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            
            # Should return a list of appointments
            is_list = isinstance(data, list)
            has_appointments = len(data) > 0 if is_list else False
            
            # Check if our created appointment is in the list
            found_appointment = False
            if is_list and hasattr(self, 'appointment_id'):
                for appt in data:
                    if appt.get('id') == self.appointment_id:
                        found_appointment = True
                        break
            
            success = is_list and (has_appointments or not hasattr(self, 'appointment_id'))
            details = f"Appointments count: {len(data) if is_list else 'N/A'}, Found created appointment: {found_appointment}"
            self.log_test("Get Appointments", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Get Appointments", False, error_msg)
            return False

    def test_email_service_status(self):
        """Test Email Service Status Endpoint - GET /api/email/status"""
        response, error = self.make_request('GET', 'email/status')
        if error:
            self.log_test("Email Service Status", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify required fields are present
            has_service = 'service' in data
            has_status = 'status' in data
            has_provider = 'provider' in data
            has_sender_email = 'sender_email' in data
            has_message = 'message' in data
            
            # Verify service field value
            correct_service = data.get('service') == 'email'
            
            # Status should be either 'active' or 'inactive'
            valid_status = data.get('status') in ['active', 'inactive']
            
            success = has_service and has_status and has_provider and has_sender_email and has_message and correct_service and valid_status
            details = f"Service: {data.get('service')}, Status: {data.get('status')}, Provider: {data.get('provider')}, Sender: {data.get('sender_email')}"
            self.log_test("Email Service Status", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Email Service Status", False, error_msg)
            return False

    def test_backend_health_check(self):
        """Test Backend Health Check - GET /api/health"""
        response, error = self.make_request('GET', 'health')
        if error:
            self.log_test("Backend Health Check", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify required fields are present
            has_status = 'status' in data
            has_timestamp = 'timestamp' in data
            
            # Verify status is healthy
            is_healthy = data.get('status') == 'healthy'
            
            success = has_status and has_timestamp and is_healthy
            details = f"Status: {data.get('status')}, Timestamp: {data.get('timestamp')}"
            self.log_test("Backend Health Check", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Backend Health Check", False, error_msg)
            return False

    def test_get_hospital_admins_list(self):
        """Test Get Hospital Admins List - GET /api/regions/admin/hospital-admins"""
        if not self.super_admin_token:
            self.log_test("Get Hospital Admins List", False, "No super admin token")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', 'regions/admin/hospital-admins')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Get Hospital Admins List", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            
            # Should return a dict with hospitals key
            hospitals = data.get('hospitals', [])
            is_list = isinstance(hospitals, list)
            has_hospitals = len(hospitals) > 0 if is_list else False
            
            # Store first hospital_id for department testing (nested under hospital.id)
            if has_hospitals:
                self.test_hospital_id = hospitals[0].get('hospital', {}).get('id')
            
            success = is_list and has_hospitals and bool(self.test_hospital_id)
            details = f"Hospitals count: {len(hospitals) if is_list else 'N/A'}, First Hospital ID: {getattr(self, 'test_hospital_id', 'None')}"
            self.log_test("Get Hospital Admins List", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Get Hospital Admins List", False, error_msg)
            return False

    def test_get_hospital_departments_before_seeding(self):
        """Test Get Hospital Departments Before Seeding - GET /api/hospital/{hospital_id}/admin/departments"""
        if not self.super_admin_token or not hasattr(self, 'test_hospital_id'):
            self.log_test("Get Hospital Departments (Before Seeding)", False, "No super admin token or hospital ID")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', f'hospital/{self.test_hospital_id}/admin/departments')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Get Hospital Departments (Before Seeding)", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            
            # Should return departments list and total count
            departments = data.get('departments', [])
            total = data.get('total', 0)
            is_list = isinstance(departments, list)
            
            # Store initial department count
            self.initial_department_count = total
            
            success = is_list and 'total' in data
            details = f"Initial departments count: {total}, Hospital ID: {self.test_hospital_id}"
            self.log_test("Get Hospital Departments (Before Seeding)", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Get Hospital Departments (Before Seeding)", False, error_msg)
            return False

    def test_seed_departments_endpoint(self):
        """Test Seed Departments Endpoint - POST /api/regions/admin/hospitals/{hospital_id}/seed-departments"""
        if not self.super_admin_token or not hasattr(self, 'test_hospital_id'):
            self.log_test("Seed Departments Endpoint", False, "No super admin token or hospital ID")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('POST', f'regions/admin/hospitals/{self.test_hospital_id}/seed-departments')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Seed Departments Endpoint", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            message = data.get('message', '')
            
            # Should either seed departments or return "already has departments"
            is_seeded = 'created' in message.lower() and 'departments' in message.lower()
            already_has = 'already has' in message.lower() and 'departments' in message.lower()
            
            success = is_seeded or already_has
            details = f"Message: {message}"
            self.log_test("Seed Departments Endpoint", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Seed Departments Endpoint", False, error_msg)
            return False

    def test_get_hospital_departments_after_seeding(self):
        """Test Get Hospital Departments After Seeding - GET /api/hospital/{hospital_id}/admin/departments"""
        if not self.super_admin_token or not hasattr(self, 'test_hospital_id'):
            self.log_test("Get Hospital Departments (After Seeding)", False, "No super admin token or hospital ID")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', f'hospital/{self.test_hospital_id}/admin/departments')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Get Hospital Departments (After Seeding)", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            
            # Should return departments list and total count
            departments = data.get('departments', [])
            total = data.get('total', 0)
            is_list = isinstance(departments, list)
            
            # Compare with initial count
            initial_count = getattr(self, 'initial_department_count', 0)
            departments_exist = total > 0
            
            success = is_list and 'total' in data and departments_exist
            details = f"Final departments count: {total}, Initial count: {initial_count}, Departments exist: {departments_exist}"
            self.log_test("Get Hospital Departments (After Seeding)", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Get Hospital Departments (After Seeding)", False, error_msg)
            return False

    def run_department_seeding_tests(self):
        """Run Department Auto-Seeding Tests as specified in review request"""
        print("🧪 Starting Department Auto-Seeding Testing")
        print("=" * 60)
        print("Testing Department Auto-Seeding Functionality:")
        print("1. Login as Super Admin (ygtnetworks@gmail.com / test123)")
        print("2. Get list of hospitals")
        print("3. Check existing departments for a hospital")
        print("4. Test seed departments endpoint")
        print("5. Verify departments after seeding")
        print("=" * 60)
        
        # Test sequence for department seeding
        tests = [
            self.test_health_check,
            self.test_super_admin_login,
            self.test_get_hospital_admins_list,
            self.test_get_hospital_departments_before_seeding,
            self.test_seed_departments_endpoint,
            self.test_get_hospital_departments_after_seeding
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_test(test.__name__, False, f"Exception: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 DEPARTMENT AUTO-SEEDING TEST SUMMARY")
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

    def run_review_request_tests(self):
        """Run tests for the specific review request"""
        print("🧪 Starting Yacco EMR Backend Testing - Review Request")
        print("=" * 60)
        print("Testing Review Request Items:")
        print("1. Email Service Status Endpoint: GET /api/email/status")
        print("2. Backend Health Check: GET /api/health")
        print("3. Super Admin Login: POST /api/auth/login (ygtnetworks@gmail.com / test123)")
        print("=" * 60)
        
        # Test sequence for review request
        tests = [
            self.test_email_service_status,
            self.test_backend_health_check,
            self.test_super_admin_login
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_test(test.__name__, False, f"Exception: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 REVIEW REQUEST TEST SUMMARY")
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

    def run_review_tests(self):
        """Run all tests for the review request"""
        print("🧪 Starting Yacco EMR Backend Testing - Review Request")
        print("=" * 60)
        print("Testing specific fixes:")
        print("1. MRN Auto-Generation")
        print("2. Force Clock-Out (as super_admin)")
        print("3. Handoff Notes API")
        print("4. Appointments")
        print("=" * 60)
        
        # Test sequence for review request
        tests = [
            self.test_health_check,
            self.test_super_admin_login,
            self.test_mrn_auto_generation,
            self.test_force_clock_out_setup,
            self.test_force_clock_out_as_super_admin,
            self.test_handoff_notes_api,
            self.test_patient_creation_with_mrn_and_payment,  # Create patient for appointments
            self.test_create_appointment,
            self.test_get_appointments
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

    def test_prescribing_drug_database(self):
        """Test e-Prescribing Drug Database - GET /api/prescriptions/drugs/database"""
        if not self.super_admin_token:
            self.log_test("e-Prescribing Drug Database", False, "No super admin token")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', 'prescriptions/drugs/database')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("e-Prescribing Drug Database", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify response structure
            has_drugs = 'drugs' in data
            has_total = 'total' in data
            drugs_list = data.get('drugs', [])
            is_list = isinstance(drugs_list, list)
            has_drugs_data = len(drugs_list) > 0 if is_list else False
            
            # Check drug structure
            drug_structure_valid = True
            if has_drugs_data:
                first_drug = drugs_list[0]
                required_fields = ['name', 'generic', 'class', 'forms', 'strengths']
                drug_structure_valid = all(field in first_drug for field in required_fields)
            
            success = has_drugs and has_total and is_list and has_drugs_data and drug_structure_valid
            details = f"Drugs count: {len(drugs_list) if is_list else 'N/A'}, Total: {data.get('total')}, Structure valid: {drug_structure_valid}"
            self.log_test("e-Prescribing Drug Database", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("e-Prescribing Drug Database", False, error_msg)
            return False

    def test_prescribing_drug_search(self):
        """Test e-Prescribing Drug Search - GET /api/prescriptions/drugs/search?query=amox"""
        if not self.super_admin_token:
            self.log_test("e-Prescribing Drug Search", False, "No super admin token")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', 'prescriptions/drugs/search', params={"query": "amox"})
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("e-Prescribing Drug Search", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            
            # Should return a list of drugs matching "amox"
            is_list = isinstance(data, list)
            has_results = len(data) > 0 if is_list else False
            
            # Check if results contain amoxicillin-related drugs
            amox_found = False
            if has_results:
                for drug in data:
                    if 'amox' in drug.get('name', '').lower() or 'amox' in drug.get('generic', '').lower():
                        amox_found = True
                        break
            
            success = is_list and has_results and amox_found
            details = f"Results count: {len(data) if is_list else 'N/A'}, Amoxicillin found: {amox_found}"
            self.log_test("e-Prescribing Drug Search", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("e-Prescribing Drug Search", False, error_msg)
            return False

    def test_nhis_tariff_codes(self):
        """Test NHIS Tariff Codes - GET /api/nhis/tariff-codes"""
        if not self.super_admin_token:
            self.log_test("NHIS Tariff Codes", False, "No super admin token")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', 'nhis/tariff-codes')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("NHIS Tariff Codes", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            
            # Should return a list of tariff codes
            is_list = isinstance(data, list)
            has_codes = len(data) > 0 if is_list else False
            
            # Check tariff code structure
            code_structure_valid = True
            if has_codes:
                first_code = data[0]
                required_fields = ['code', 'description', 'category', 'price']
                code_structure_valid = all(field in first_code for field in required_fields)
            
            # Look for specific Ghana NHIS codes
            ghana_codes_found = False
            if has_codes:
                for code in data:
                    if code.get('code', '').startswith(('OPD', 'LAB', 'IMG')):
                        ghana_codes_found = True
                        break
            
            success = is_list and has_codes and code_structure_valid and ghana_codes_found
            details = f"Codes count: {len(data) if is_list else 'N/A'}, Structure valid: {code_structure_valid}, Ghana codes: {ghana_codes_found}"
            self.log_test("NHIS Tariff Codes", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("NHIS Tariff Codes", False, error_msg)
            return False

    def test_nhis_diagnosis_codes(self):
        """Test NHIS ICD-10 Diagnosis Codes - GET /api/nhis/diagnosis-codes"""
        if not self.super_admin_token:
            self.log_test("NHIS ICD-10 Diagnosis Codes", False, "No super admin token")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', 'nhis/diagnosis-codes')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("NHIS ICD-10 Diagnosis Codes", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            
            # Should return a list of ICD-10 codes
            is_list = isinstance(data, list)
            has_codes = len(data) > 0 if is_list else False
            
            # Check ICD-10 code structure
            code_structure_valid = True
            if has_codes:
                first_code = data[0]
                required_fields = ['code', 'description']
                code_structure_valid = all(field in first_code for field in required_fields)
            
            # Look for specific ICD-10 codes common in Ghana
            ghana_icd_found = False
            if has_codes:
                for code in data:
                    if code.get('code') in ['B50', 'B54', 'E11', 'I10']:  # Malaria, Diabetes, Hypertension
                        ghana_icd_found = True
                        break
            
            success = is_list and has_codes and code_structure_valid and ghana_icd_found
            details = f"ICD-10 codes count: {len(data) if is_list else 'N/A'}, Structure valid: {code_structure_valid}, Ghana ICD codes: {ghana_icd_found}"
            self.log_test("NHIS ICD-10 Diagnosis Codes", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("NHIS ICD-10 Diagnosis Codes", False, error_msg)
            return False

    def test_radiology_modalities(self):
        """Test Radiology Modalities - GET /api/radiology/modalities"""
        if not self.super_admin_token:
            self.log_test("Radiology Modalities", False, "No super admin token")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', 'radiology/modalities')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Radiology Modalities", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            
            # Should return a list of imaging modalities
            is_list = isinstance(data, list)
            has_modalities = len(data) > 0 if is_list else False
            
            # Check modality structure
            modality_structure_valid = True
            if has_modalities:
                first_modality = data[0]
                required_fields = ['value', 'name']
                modality_structure_valid = all(field in first_modality for field in required_fields)
            
            # Look for common imaging modalities
            common_modalities = ['xray', 'ct', 'mri', 'ultrasound']
            modalities_found = []
            if has_modalities:
                for modality in data:
                    if modality.get('value') in common_modalities:
                        modalities_found.append(modality.get('value'))
            
            success = is_list and has_modalities and modality_structure_valid and len(modalities_found) >= 3
            details = f"Modalities count: {len(data) if is_list else 'N/A'}, Structure valid: {modality_structure_valid}, Common modalities: {modalities_found}"
            self.log_test("Radiology Modalities", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Radiology Modalities", False, error_msg)
            return False

    def test_radiology_study_types(self):
        """Test Radiology Study Types - GET /api/radiology/study-types"""
        if not self.super_admin_token:
            self.log_test("Radiology Study Types", False, "No super admin token")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', 'radiology/study-types')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Radiology Study Types", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            
            # Should return a dict with modalities as keys
            is_dict = isinstance(data, dict)
            has_modalities = len(data) > 0 if is_dict else False
            
            # Check for X-ray studies
            has_xray_studies = 'xray' in data if is_dict else False
            xray_studies_valid = False
            if has_xray_studies:
                xray_studies = data.get('xray', [])
                xray_studies_valid = isinstance(xray_studies, list) and len(xray_studies) > 0
                if xray_studies_valid and len(xray_studies) > 0:
                    first_study = xray_studies[0]
                    required_fields = ['code', 'name', 'body_part']
                    xray_studies_valid = all(field in first_study for field in required_fields)
            
            # Check for CT studies
            has_ct_studies = 'ct' in data if is_dict else False
            
            success = is_dict and has_modalities and has_xray_studies and xray_studies_valid and has_ct_studies
            details = f"Modalities: {list(data.keys()) if is_dict else 'N/A'}, X-ray studies: {len(data.get('xray', [])) if has_xray_studies else 0}, CT studies: {len(data.get('ct', [])) if has_ct_studies else 0}"
            self.log_test("Radiology Study Types", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Radiology Study Types", False, error_msg)
            return False

    def test_bed_management_wards(self):
        """Test Bed Management Wards - GET /api/beds/wards (should be empty initially)"""
        if not self.super_admin_token:
            self.log_test("Bed Management Wards (Initial)", False, "No super admin token")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', 'beds/wards')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Bed Management Wards (Initial)", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            
            # Should return wards structure
            has_wards = 'wards' in data
            has_total = 'total' in data
            wards_list = data.get('wards', [])
            is_list = isinstance(wards_list, list)
            
            # Initially should be empty or have minimal wards
            ward_count = len(wards_list) if is_list else 0
            
            success = has_wards and has_total and is_list
            details = f"Wards count: {ward_count}, Total: {data.get('total')}, Structure valid: {success}"
            self.log_test("Bed Management Wards (Initial)", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Bed Management Wards (Initial)", False, error_msg)
            return False

    def test_bed_management_seed_defaults(self):
        """Test Bed Management Seed Defaults - POST /api/beds/wards/seed-defaults"""
        if not self.super_admin_token:
            self.log_test("Bed Management Seed Defaults", False, "No super admin token")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('POST', 'beds/wards/seed-defaults')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Bed Management Seed Defaults", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            
            # Should return success message and count
            has_message = 'message' in data
            message = data.get('message', '')
            
            # Check if wards were created or already existed
            wards_created = 'Created' in message or 'already exist' in message
            has_count = 'count' in data or 'skipped' in data
            
            success = has_message and wards_created
            details = f"Message: {message}, Count/Skipped: {data.get('count', data.get('skipped', 'N/A'))}"
            self.log_test("Bed Management Seed Defaults", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Bed Management Seed Defaults", False, error_msg)
            return False

    def test_bed_management_census(self):
        """Test Bed Management Census - GET /api/beds/census"""
        if not self.super_admin_token:
            self.log_test("Bed Management Census", False, "No super admin token")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', 'beds/census')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Bed Management Census", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            
            # Should return census structure
            has_summary = 'summary' in data
            has_wards = 'wards' in data
            has_timestamp = 'timestamp' in data
            has_critical_care = 'critical_care' in data
            
            # Check summary structure
            summary_valid = False
            if has_summary:
                summary = data.get('summary', {})
                required_fields = ['total_beds', 'occupied', 'available', 'overall_occupancy']
                summary_valid = all(field in summary for field in required_fields)
            
            # Check wards structure
            wards_valid = False
            if has_wards:
                wards = data.get('wards', [])
                wards_valid = isinstance(wards, list)
            
            success = has_summary and has_wards and has_timestamp and has_critical_care and summary_valid and wards_valid
            details = f"Summary valid: {summary_valid}, Wards count: {len(data.get('wards', [])) if wards_valid else 'N/A'}, Critical care: {has_critical_care}"
            self.log_test("Bed Management Census", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Bed Management Census", False, error_msg)
            return False

    def run_yacco_emr_new_modules_tests(self):
        """Run tests for the new Yacco EMR backend modules as specified in review request"""
        print("🧪 Starting Yacco EMR New Backend Modules Testing")
        print("=" * 60)
        print("Testing: e-Prescribing, NHIS Claims, Radiology, Bed Management")
        print("Backend URL: https://emr-postgres-move.preview.emergentagent.com")
        print("Super Admin: ygtnetworks@gmail.com / test123")
        print("=" * 60)
        
        # Test sequence for new backend modules
        tests = [
            self.test_health_check,
            self.test_super_admin_login,
            self.test_prescribing_drug_database,
            self.test_prescribing_drug_search,
            self.test_nhis_tariff_codes,
            self.test_nhis_diagnosis_codes,
            self.test_radiology_modalities,
            self.test_radiology_study_types,
            self.test_bed_management_wards,
            self.test_bed_management_seed_defaults,
            self.test_bed_management_census
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_test(test.__name__, False, f"Exception: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 YACCO EMR NEW MODULES TEST SUMMARY")
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
    
    # Run the new Yacco EMR modules tests as specified in the review request
    success = tester.run_yacco_emr_new_modules_tests()
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)