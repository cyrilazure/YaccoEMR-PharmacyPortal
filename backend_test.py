#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class YaccoHealthAPITester:
    def __init__(self, base_url="http://localhost:8001/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_credentials = {"email": "admin@yacco.health", "password": "admin123"}
        
        print(f"🏥 Yacco Health Backend API Tester")
        print(f"📡 Testing against: {self.base_url}")
        print("=" * 60)

    def run_test(self, name, method, endpoint, expected_status, data=None, requires_auth=False):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        headers = {'Content-Type': 'application/json'}
        
        if requires_auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 [{self.tests_run}] Testing: {name}")
        print(f"   📍 {method} {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"   ✅ PASS - Status: {response.status_code}")
                try:
                    response_data = response.json() if response.text else {}
                    if response_data:
                        print(f"   📄 Response: {json.dumps(response_data, indent=2)[:200]}...")
                except:
                    print(f"   📄 Response: {response.text[:100]}...")
            else:
                print(f"   ❌ FAIL - Expected {expected_status}, got {response.status_code}")
                print(f"   📄 Response: {response.text[:200]}...")

            return success, response.json() if response.text and 'json' in response.headers.get('content-type', '') else {}

        except requests.exceptions.Timeout:
            print(f"   ⏰ TIMEOUT - Request took too long")
            return False, {}
        except requests.exceptions.ConnectionError:
            print(f"   🔌 CONNECTION ERROR - Could not connect to {url}")
            return False, {}
        except Exception as e:
            print(f"   ❌ ERROR - {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test the health check endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "health",
            200
        )
        return success and response.get('status') == 'healthy'

    def test_seed_data(self):
        """Test the seed data endpoint"""
        success, response = self.run_test(
            "Seed Data Creation",
            "POST",
            "seed",
            200
        )
        return success and 'admin_email' in response

    def test_login(self):
        """Test login endpoint and store token"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data=self.admin_credentials
        )
        
        if success and 'token' in response:
            self.token = response['token']
            print(f"   🔑 Token acquired: {self.token[:20]}...")
            return True
        return False

    def test_auth_me(self):
        """Test the /auth/me endpoint to verify token"""
        success, response = self.run_test(
            "Get Current User (/auth/me)",
            "GET",
            "auth/me",
            200,
            requires_auth=True
        )
        return success and response.get('role') == 'it_admin'

    def test_logout(self):
        """Test logout endpoint"""
        success, response = self.run_test(
            "Logout",
            "POST",
            "auth/logout",
            200,
            requires_auth=True
        )
        return success

    def test_stats(self):
        """Test the stats endpoint"""
        success, response = self.run_test(
            "Dashboard Stats",
            "GET",
            "stats",
            200,
            requires_auth=True
        )
        required_fields = ['total_users', 'total_facilities', 'total_pharmacies', 'active_users', 'regions_covered']
        has_required_fields = all(field in response for field in required_fields)
        return success and has_required_fields

    def test_users_crud(self):
        """Test Users CRUD operations"""
        # Test GET users
        get_success, users_data = self.run_test(
            "Get All Users",
            "GET",
            "users",
            200,
            requires_auth=True
        )
        
        if not get_success:
            return False

        # Test POST create user
        new_user_data = {
            "name": "Test User",
            "email": f"test.{datetime.now().strftime('%H%M%S')}@test.yacco.health",
            "password": "testpass123",
            "role": "physician",
            "region_id": "greater-accra",
            "phone": "+233244123456",
            "is_active": True
        }
        
        create_success, created_user = self.run_test(
            "Create New User",
            "POST",
            "users",
            200,
            data=new_user_data,
            requires_auth=True
        )
        
        if not create_success or 'id' not in created_user:
            return False

        user_id = created_user['id']

        # Test GET specific user
        get_user_success, user_detail = self.run_test(
            f"Get User by ID",
            "GET",
            f"users/{user_id}",
            200,
            requires_auth=True
        )

        # Test PUT update user
        update_data = {
            "name": "Updated Test User",
            "phone": "+233244999888"
        }
        
        update_success, updated_user = self.run_test(
            "Update User",
            "PUT",
            f"users/{user_id}",
            200,
            data=update_data,
            requires_auth=True
        )

        # Test DELETE user
        delete_success, _ = self.run_test(
            "Delete User",
            "DELETE",
            f"users/{user_id}",
            200,
            requires_auth=True
        )

        return all([get_success, create_success, get_user_success, update_success, delete_success])

    def test_facilities_crud(self):
        """Test Facilities CRUD operations"""
        # Test GET facilities
        get_success, facilities_data = self.run_test(
            "Get All Facilities",
            "GET",
            "facilities",
            200,
            requires_auth=True
        )
        
        if not get_success:
            return False

        # Test POST create facility
        new_facility_data = {
            "name": f"Test Facility {datetime.now().strftime('%H%M%S')}",
            "facility_type": "clinic",
            "region_id": "central",
            "address": "Test Address, Cape Coast",
            "phone": "+233332123456",
            "email": "test.facility@test.com",
            "is_active": True,
            "nhis_registered": True
        }
        
        create_success, created_facility = self.run_test(
            "Create New Facility",
            "POST",
            "facilities",
            200,
            data=new_facility_data,
            requires_auth=True
        )
        
        if not create_success or 'id' not in created_facility:
            return False

        facility_id = created_facility['id']

        # Test GET specific facility
        get_facility_success, facility_detail = self.run_test(
            f"Get Facility by ID",
            "GET",
            f"facilities/{facility_id}",
            200,
            requires_auth=True
        )

        # Test PUT update facility
        update_data = {
            "name": "Updated Test Facility",
            "phone": "+233332999888"
        }
        
        update_success, updated_facility = self.run_test(
            "Update Facility",
            "PUT",
            f"facilities/{facility_id}",
            200,
            data=update_data,
            requires_auth=True
        )

        # Test DELETE facility
        delete_success, _ = self.run_test(
            "Delete Facility",
            "DELETE",
            f"facilities/{facility_id}",
            200,
            requires_auth=True
        )

        return all([get_success, create_success, get_facility_success, update_success, delete_success])

    def test_regions(self):
        """Test regions endpoint"""
        success, response = self.run_test(
            "Get Ghana Regions",
            "GET",
            "regions",
            200
        )
        return success and len(response) == 16

    def test_unauthorized_access(self):
        """Test that protected endpoints require authentication"""
        # Test stats without token
        temp_token = self.token
        self.token = None
        
        success, response = self.run_test(
            "Unauthorized Stats Access (should fail)",
            "GET",
            "stats",
            401
        )
        
        # Restore token
        self.token = temp_token
        return success  # Success means it properly returned 401

    def run_all_tests(self):
        """Run all backend tests in sequence"""
        print("\n🚀 Starting comprehensive backend API testing...\n")
        
        # Core infrastructure tests
        tests = [
            ("Health Check", self.test_health_check),
            ("Seed Data", self.test_seed_data),
            ("Admin Login", self.test_login),
            ("Auth Me", self.test_auth_me),
            ("Dashboard Stats", self.test_stats),
            ("Users CRUD", self.test_users_crud),
            ("Facilities CRUD", self.test_facilities_crud),
            ("Ghana Regions", self.test_regions),
            ("Unauthorized Access Check", self.test_unauthorized_access),
            ("Logout", self.test_logout),
        ]

        failed_tests = []
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                if not result:
                    failed_tests.append(test_name)
            except Exception as e:
                print(f"   💥 EXCEPTION in {test_name}: {str(e)}")
                failed_tests.append(test_name)
                
        # Print final results
        print("\n" + "=" * 60)
        print(f"🏁 FINAL RESULTS")
        print(f"📊 Tests Run: {self.tests_run}")
        print(f"✅ Tests Passed: {self.tests_passed}")
        print(f"❌ Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"📈 Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if failed_tests:
            print(f"\n❌ Failed Test Categories:")
            for test in failed_tests:
                print(f"   • {test}")
        else:
            print(f"\n🎉 ALL TESTS PASSED!")
            
        print("=" * 60)
        
        return len(failed_tests) == 0

def main():
    """Main test runner"""
    tester = YaccoHealthAPITester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⏹️  Testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n💥 Fatal error during testing: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)