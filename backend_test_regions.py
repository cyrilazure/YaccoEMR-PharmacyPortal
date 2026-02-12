#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import time

class YaccoEMRRegionsHospitalsTester:
    def __init__(self, base_url="https://c2268c5e-71c6-4e43-9de5-db8608466ebc.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

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
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, params=params, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=params, timeout=30)
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
        try:
            data = response.json()
            message = data.get('message', '')
            has_yacco = 'Yacco EMR API' in message
            details = f"Status: {response.status_code}, Message: {message}, Has Yacco: {has_yacco}"
        except:
            details = f"Status: {response.status_code}"
            
        self.log_test("Health Check", success, details)
        return success

    def test_regions_endpoint(self):
        """Test GET /api/regions/ - Should return 16 regions with hospital counts"""
        response, error = self.make_request('GET', 'regions')
        if error:
            self.log_test("Regions Endpoint", False, error)
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                # Check if response has regions
                regions = data.get('regions', [])
                is_list = isinstance(regions, list)
                region_count = len(regions)
                has_16_regions = region_count == 16
                
                # Check if regions have hospital counts
                has_hospital_counts = True
                region_names = []
                for region in regions[:5]:  # Check first 5 regions
                    region_names.append(region.get('name', 'Unknown'))
                    if 'hospital_count' not in region:
                        has_hospital_counts = False
                        break
                
                success = is_list and has_16_regions and has_hospital_counts
                details = f"Count: {region_count}/16, Has hospital counts: {has_hospital_counts}, Sample regions: {region_names[:3]}"
                self.log_test("Regions Endpoint", success, details)
                return success
                
            except json.JSONDecodeError:
                self.log_test("Regions Endpoint", False, "Invalid JSON response")
                return False
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Regions Endpoint", False, error_msg)
            return False

    def test_greater_accra_hospitals(self):
        """Test GET /api/regions/greater-accra/hospitals - Should show Ashaiman Polyclinic and Korle Bu"""
        response, error = self.make_request('GET', 'regions/greater-accra/hospitals')
        if error:
            self.log_test("Greater Accra Hospitals", False, error)
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                hospitals = data.get('hospitals', [])
                is_list = isinstance(hospitals, list)
                hospital_count = len(hospitals)
                
                # Look for Ashaiman Polyclinic and Korle Bu
                hospital_names = [h.get('name', '').lower() for h in hospitals]
                has_ashaiman = any('ashaiman' in name for name in hospital_names)
                has_korle_bu = any('korle bu' in name or 'korle-bu' in name for name in hospital_names)
                
                success = is_list and hospital_count > 0 and (has_ashaiman or has_korle_bu)
                details = f"Count: {hospital_count}, Has Ashaiman: {has_ashaiman}, Has Korle Bu: {has_korle_bu}, Names: {[h.get('name', '') for h in hospitals[:3]]}"
                self.log_test("Greater Accra Hospitals", success, details)
                return success
                
            except json.JSONDecodeError:
                self.log_test("Greater Accra Hospitals", False, "Invalid JSON response")
                return False
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Greater Accra Hospitals", False, error_msg)
            return False

    def test_eastern_region_hospitals(self):
        """Test GET /api/regions/eastern/hospitals - Should show Eastern Region Regional Health Center"""
        response, error = self.make_request('GET', 'regions/eastern/hospitals')
        if error:
            self.log_test("Eastern Region Hospitals", False, error)
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                hospitals = data.get('hospitals', [])
                is_list = isinstance(hospitals, list)
                hospital_count = len(hospitals)
                
                # Look for Eastern Region Regional Health Center
                hospital_names = [h.get('name', '').lower() for h in hospitals]
                has_eastern_regional = any('eastern' in name and 'regional' in name for name in hospital_names)
                
                success = is_list and hospital_count > 0 and has_eastern_regional
                details = f"Count: {hospital_count}, Has Eastern Regional: {has_eastern_regional}, Names: {[h.get('name', '') for h in hospitals]}"
                self.log_test("Eastern Region Hospitals", success, details)
                return success
                
            except json.JSONDecodeError:
                self.log_test("Eastern Region Hospitals", False, "Invalid JSON response")
                return False
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Eastern Region Hospitals", False, error_msg)
            return False

    def test_super_admin_login(self):
        """Test Super admin login: ygtnetworks@gmail.com / test123"""
        login_data = {
            "email": "ygtnetworks@gmail.com",
            "password": "test123"
        }
        
        response, error = self.make_request('POST', 'auth/login', login_data)
        if error:
            self.log_test("Super Admin Login", False, error)
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                token = data.get('token')
                user = data.get('user', {})
                role = user.get('role')
                email = user.get('email')
                
                success = bool(token) and role == 'super_admin' and email == 'ygtnetworks@gmail.com'
                details = f"Token: {bool(token)}, Role: {role}, Email: {email}"
                
                if success:
                    self.token = token
                    
                self.log_test("Super Admin Login", success, details)
                return success
                
            except json.JSONDecodeError:
                self.log_test("Super Admin Login", False, "Invalid JSON response")
                return False
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Super Admin Login", False, error_msg)
            return False

    def test_ashaiman_physician_login(self):
        """Test Physician login at Ashaiman: physicianicu@pysicianicu.com"""
        login_data = {
            "email": "physicianicu@pysicianicu.com",
            "password": "oQH7yw1HWq6ZRTzE"
        }
        
        response, error = self.make_request('POST', 'auth/login', login_data)
        if error:
            self.log_test("Ashaiman Physician Login", False, error)
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                token = data.get('token')
                user = data.get('user', {})
                role = user.get('role')
                email = user.get('email')
                
                success = bool(token) and role in ['physician', 'doctor'] and email == 'physicianicu@pysicianicu.com'
                details = f"Token: {bool(token)}, Role: {role}, Email: {email}"
                self.log_test("Ashaiman Physician Login", success, details)
                return success
                
            except json.JSONDecodeError:
                self.log_test("Ashaiman Physician Login", False, "Invalid JSON response")
                return False
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Ashaiman Physician Login", False, error_msg)
            return False

    def test_eastern_itadmin_login(self):
        """Test IT admin login at Eastern: itadmin@eastern.com"""
        login_data = {
            "email": "itadmin@eastern.com", 
            "password": "prueHX1C97H0AQqN"
        }
        
        response, error = self.make_request('POST', 'auth/login', login_data)
        if error:
            self.log_test("Eastern IT Admin Login", False, error)
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                token = data.get('token')
                user = data.get('user', {})
                role = user.get('role')
                email = user.get('email')
                
                success = bool(token) and 'admin' in role.lower() and email == 'itadmin@eastern.com'
                details = f"Token: {bool(token)}, Role: {role}, Email: {email}"
                self.log_test("Eastern IT Admin Login", success, details)
                return success
                
            except json.JSONDecodeError:
                self.log_test("Eastern IT Admin Login", False, "Invalid JSON response")
                return False
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Eastern IT Admin Login", False, error_msg)
            return False

    def test_auth_me_endpoint(self):
        """Test /api/auth/me endpoint with authenticated user"""
        if not self.token:
            self.log_test("Auth Me Endpoint", False, "No token available")
            return False
            
        response, error = self.make_request('GET', 'auth/me')
        if error:
            self.log_test("Auth Me Endpoint", False, error)
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                has_id = bool(data.get('id'))
                has_email = bool(data.get('email'))
                has_role = bool(data.get('role'))
                has_name = bool(data.get('first_name')) and bool(data.get('last_name'))
                
                success = has_id and has_email and has_role and has_name
                details = f"ID: {bool(data.get('id'))}, Email: {data.get('email', '')}, Role: {data.get('role', '')}"
                self.log_test("Auth Me Endpoint", success, details)
                return success
                
            except json.JSONDecodeError:
                self.log_test("Auth Me Endpoint", False, "Invalid JSON response")
                return False
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Auth Me Endpoint", False, error_msg)
            return False

    def test_hospital_count_verification(self):
        """Test that we have 9 hospitals across 8 regions as mentioned in PRD"""
        if not self.token:
            self.log_test("Hospital Count Verification", False, "No token available")
            return False
            
        # Get all regions first
        response, error = self.make_request('GET', 'regions')
        if error or response.status_code != 200:
            self.log_test("Hospital Count Verification", False, "Failed to get regions")
            return False
        
        try:
            regions_data = response.json()
            regions = regions_data.get('regions', [])
            
            total_hospitals = 0
            regions_with_hospitals = 0
            region_details = []
            
            for region in regions:
                hospital_count = region.get('hospital_count', 0)
                if hospital_count > 0:
                    regions_with_hospitals += 1
                total_hospitals += hospital_count
                
                if hospital_count > 0:
                    region_details.append(f"{region.get('name', 'Unknown')}: {hospital_count}")
            
            # According to PRD: 9 hospitals across 8 regions
            expected_hospitals = 9
            expected_regions = 8
            
            success = total_hospitals >= expected_hospitals and regions_with_hospitals >= expected_regions
            details = f"Total hospitals: {total_hospitals} (expected: ≥{expected_hospitals}), Regions with hospitals: {regions_with_hospitals} (expected: ≥{expected_regions}), Details: {region_details[:5]}"
            self.log_test("Hospital Count Verification", success, details)
            return success
            
        except json.JSONDecodeError:
            self.log_test("Hospital Count Verification", False, "Invalid JSON response")
            return False

    def run_all_tests(self):
        """Run all tests according to review request requirements"""
        print("🧪 Starting Yacco EMR Regions & Hospitals Backend Testing")
        print("=" * 80)
        print("Testing data restoration after GitHub main-TESTING-STAGE branch restore")
        print("Expected: 16 regions, 9 hospitals across 8 regions")
        print("=" * 80)
        
        # Test sequence
        tests = [
            self.test_health_check,
            self.test_regions_endpoint,
            self.test_greater_accra_hospitals,
            self.test_eastern_region_hospitals,
            self.test_super_admin_login,
            self.test_auth_me_endpoint,
            self.test_hospital_count_verification,
            self.test_ashaiman_physician_login,
            self.test_eastern_itadmin_login,
        ]
        
        for test in tests:
            try:
                test()
                time.sleep(0.5)  # Small delay between tests
            except Exception as e:
                self.log_test(test.__name__, False, f"Exception: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 80)
        print(f"📊 YACCO EMR REGIONS & HOSPITALS TEST SUMMARY")
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
        else:
            print(f"\n✅ ALL TESTS PASSED!")
        
        # Print passed tests summary
        passed_tests = [t for t in self.test_results if t['success']]
        if passed_tests:
            print(f"\n✅ PASSED TESTS:")
            for test in passed_tests:
                print(f"  - {test['test']}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = YaccoEMRRegionsHospitalsTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())