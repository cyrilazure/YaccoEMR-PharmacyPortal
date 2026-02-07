#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta

class HospitalSignupTester:
    def __init__(self, base_url="https://healthfusion-gh.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        # Test variables
        self.super_admin_token = None
        self.test_registration_id = None
        self.test_verification_token = None
        self.test_admin_email = None
        self.test_approved_hospital_id = None
        self.test_approved_admin_email = None
        self.test_approved_admin_password = None
        self.hospital_admin_token = None
        self.hospital_admin_org_id = None

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

    def test_super_admin_login(self):
        """Test super admin login"""
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
            is_super_admin = user.get('role') == 'super_admin'
            has_token = bool(self.super_admin_token)
            success = is_super_admin and has_token
            self.log_test("Super Admin Login", success, f"Role: {user.get('role')}")
            return success
        else:
            self.log_test("Super Admin Login", False, f"Status: {response.status_code}")
            return False

    def test_hospital_signup_flow(self):
        """Test complete hospital signup workflow"""
        import time
        timestamp = str(int(time.time()))
        
        # Step 1: Hospital Registration
        signup_data = {
            "hospital_name": "Test General Hospital",
            "region_id": "volta",
            "address": "123 Medical Street",
            "city": "Ho",
            "phone": "+233-24-1234567",
            "hospital_email": f"info{timestamp}@testhosp.gh",
            "license_number": f"LIC-{timestamp}",
            "admin_first_name": "Dr. John",
            "admin_last_name": "Administrator",
            "admin_email": f"test.admin{timestamp}@testhosp.gh",
            "admin_phone": "+233-24-7654321",
            "accept_terms": True
        }
        
        response, error = self.make_request('POST', 'signup/hospital', signup_data)
        if error:
            self.log_test("Hospital Signup Registration", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            registration_id = data.get('registration_id')
            verification_token = data.get('dev_verification_token')
            
            has_registration_id = bool(registration_id)
            has_verification_token = bool(verification_token)
            
            if has_registration_id and has_verification_token:
                self.test_registration_id = registration_id
                self.test_verification_token = verification_token
                self.test_admin_email = signup_data['admin_email']
                
                self.log_test("Hospital Signup Registration", True, f"Registration ID: {registration_id}")
                return True
            else:
                self.log_test("Hospital Signup Registration", False, "Missing registration ID or token")
                return False
        else:
            self.log_test("Hospital Signup Registration", False, f"Status: {response.status_code}")
            return False

    def test_email_verification(self):
        """Test email verification step"""
        if not self.test_verification_token:
            self.log_test("Email Verification", False, "No verification token available")
            return False
        
        verification_data = {
            "token": self.test_verification_token
        }
        
        response, error = self.make_request('POST', 'signup/verify-email', verification_data)
        if error:
            self.log_test("Email Verification", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            success = status == 'pending_approval'
            self.log_test("Email Verification", success, f"Status: {status}")
            return success
        else:
            self.log_test("Email Verification", False, f"Status: {response.status_code}")
            return False

    def test_super_admin_approve_registration(self):
        """Test super admin approving registration"""
        if not self.test_registration_id:
            self.log_test("Super Admin Approve Registration", False, "No registration ID available")
            return False
        
        if not self.super_admin_token:
            self.log_test("Super Admin Approve Registration", False, "No super admin access")
            return False
        
        # Temporarily switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        approval_data = {
            "approved": True,
            "notes": "Approved for testing purposes"
        }
        
        response, error = self.make_request('POST', f'signup/admin/approve/{self.test_registration_id}', approval_data)
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Super Admin Approve Registration", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            hospital = data.get('hospital', {})
            admin = data.get('admin', {})
            location = data.get('location', {})
            
            has_hospital_id = bool(hospital.get('id'))
            has_admin_creds = bool(admin.get('email')) and bool(admin.get('temp_password'))
            has_location = bool(location.get('id'))
            
            success = status == 'approved' and has_hospital_id and has_admin_creds and has_location
            
            if success:
                self.test_approved_hospital_id = hospital.get('id')
                self.test_approved_admin_email = admin.get('email')
                self.test_approved_admin_password = admin.get('temp_password')
                self.hospital_admin_org_id = hospital.get('id')  # Set this for subsequent tests
            
            self.log_test("Super Admin Approve Registration", success, 
                         f"Status: {status}, Hospital: {hospital.get('name')}")
            return success
        else:
            self.log_test("Super Admin Approve Registration", False, f"Status: {response.status_code}")
            return False

    def test_hospital_admin_dashboard(self):
        """Test hospital admin dashboard access using super admin token"""
        if not self.hospital_admin_org_id:
            self.log_test("Hospital Admin Dashboard", False, "No hospital organization ID")
            return False
        
        if not self.super_admin_token:
            self.log_test("Hospital Admin Dashboard", False, "No super admin token available")
            return False
        
        # Use super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', f'hospital/{self.hospital_admin_org_id}/admin/dashboard')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Hospital Admin Dashboard", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            hospital = data.get('hospital', {})
            stats = data.get('stats', {})
            departments = data.get('departments', [])
            
            has_hospital_info = bool(hospital.get('id'))
            has_stats = 'total_users' in stats
            has_departments = isinstance(departments, list)
            
            success = has_hospital_info and has_stats and has_departments
            self.log_test("Hospital Admin Dashboard", success, 
                         f"Hospital: {hospital.get('name')}, Users: {stats.get('total_users', 0)}")
            return success
        else:
            self.log_test("Hospital Admin Dashboard", False, f"Status: {response.status_code}")
            return False

    def test_hospital_main_dashboard(self):
        """Test hospital main dashboard access"""
        if not self.hospital_admin_org_id:
            self.log_test("Hospital Main Dashboard", False, "No hospital organization ID")
            return False
        
        if not self.super_admin_token:
            self.log_test("Hospital Main Dashboard", False, "No super admin token available")
            return False
        
        # Use super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', f'hospital/{self.hospital_admin_org_id}/dashboard')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Hospital Main Dashboard", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            hospital = data.get('hospital', {})
            user = data.get('user', {})
            stats = data.get('stats', {})
            quick_links = data.get('quick_links', [])
            
            has_hospital_info = bool(hospital.get('id'))
            has_user_info = bool(user.get('id'))
            has_stats = 'total_users' in stats
            has_quick_links = isinstance(quick_links, list) and len(quick_links) > 0
            
            success = has_hospital_info and has_user_info and has_stats and has_quick_links
            self.log_test("Hospital Main Dashboard", success, 
                         f"Hospital: {hospital.get('name')}, Portal: {user.get('portal')}")
            return success
        else:
            self.log_test("Hospital Main Dashboard", False, f"Status: {response.status_code}")
            return False

    def run_tests(self):
        """Run all hospital signup and admin tests"""
        print("🏥 Testing Hospital Signup & Admin Module")
        print("=" * 50)
        
        # Test sequence
        self.test_super_admin_login()
        self.test_hospital_signup_flow()
        self.test_email_verification()
        self.test_super_admin_approve_registration()
        self.test_hospital_admin_dashboard()
        self.test_hospital_main_dashboard()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = HospitalSignupTester()
    success = tester.run_tests()
    sys.exit(0 if success else 1)