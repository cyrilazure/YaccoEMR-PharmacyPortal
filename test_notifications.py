#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta

class NotificationTester:
    def __init__(self, base_url="https://admin-control-119.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_patient_id = None
        self.hospital_admin_token = None
        self.hospital_admin_id = None

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

    def setup_test_user(self):
        """Setup test user and patient"""
        # Register/login user
        test_user = {
            "email": "testdoc@test.com",
            "password": "test123",
            "first_name": "Test",
            "last_name": "Doctor",
            "role": "physician",
            "department": "Internal Medicine",
            "specialty": "Cardiology"
        }
        
        response, error = self.make_request('POST', 'auth/register', test_user)
        if response and response.status_code in [200, 201]:
            data = response.json()
            self.token = data.get('token')
            self.user_id = data.get('user', {}).get('id')
        elif response and response.status_code == 400:
            # User exists, try login
            login_data = {"email": "testdoc@test.com", "password": "test123"}
            response, error = self.make_request('POST', 'auth/login', login_data)
            if response and response.status_code == 200:
                data = response.json()
                self.token = data.get('token')
                self.user_id = data.get('user', {}).get('id')

        # Create test patient
        patient_data = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1980-05-15",
            "gender": "male",
            "email": "john.doe@email.com"
        }
        
        response, error = self.make_request('POST', 'patients', patient_data)
        if response and response.status_code == 200:
            data = response.json()
            self.test_patient_id = data.get('id')

        # Setup hospital admin
        super_admin_data = {
            "email": "superadmin@yacco.com",
            "password": "SuperAdmin123!",
            "first_name": "Super",
            "last_name": "Admin",
            "role": "super_admin"
        }
        
        response, error = self.make_request('POST', 'auth/register', super_admin_data)
        if response and response.status_code == 400:
            # Login existing super admin
            login_data = {"email": "superadmin@yacco.com", "password": "SuperAdmin123!"}
            response, error = self.make_request('POST', 'auth/login', login_data)
            if response and response.status_code == 200:
                data = response.json()
                super_admin_token = data.get('token')
                
                # Switch to super admin and create hospital admin
                original_token = self.token
                self.token = super_admin_token
                
                # Create organization first
                import time
                timestamp = str(int(time.time()))
                org_data = {
                    "name": f"Test Hospital {timestamp}",
                    "organization_type": "hospital",
                    "address_line1": "123 Test St",
                    "city": "Test City",
                    "state": "CA",
                    "zip_code": "90210",
                    "country": "USA",
                    "phone": "555-123-4567",
                    "email": f"admin{timestamp}@test.com",
                    "license_number": f"LIC-{timestamp}",
                    "admin_first_name": "Hospital",
                    "admin_last_name": "Admin",
                    "admin_email": f"hadmin{timestamp}@test.com",
                    "admin_phone": "555-111-2222"
                }
                
                response, error = self.make_request('POST', 'organizations/create-by-admin?auto_approve=true', org_data)
                if response and response.status_code == 200:
                    data = response.json()
                    admin_email = data.get('admin_email')
                    temp_password = data.get('temp_password')
                    
                    # Login as hospital admin
                    self.token = original_token
                    login_data = {"email": admin_email, "password": temp_password}
                    response, error = self.make_request('POST', 'auth/login', login_data)
                    if response and response.status_code == 200:
                        data = response.json()
                        self.hospital_admin_token = data.get('token')
                        self.hospital_admin_id = data.get('user', {}).get('id')
                
                self.token = original_token

    def test_notification_types(self):
        """Test getting notification types"""
        response, error = self.make_request('GET', 'notifications/types')
        if error:
            self.log_test("Notification Types", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_types = isinstance(data, list) and len(data) > 0
            type_values = [t.get('value') for t in data]
            expected_types = ['records_request_received', 'emergency_access_used', 'consent_required', 'security_login_new_device']
            has_expected = all(t in type_values for t in expected_types)
            success = has_types and has_expected and len(data) >= 30
            self.log_test("Notification Types", success, f"Found {len(data)} notification types")
            return success
        else:
            self.log_test("Notification Types", False, f"Status: {response.status_code}")
            return False

    def test_notification_priorities(self):
        """Test getting notification priorities"""
        response, error = self.make_request('GET', 'notifications/priorities')
        if error:
            self.log_test("Notification Priorities", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_priorities = isinstance(data, list) and len(data) > 0
            priority_values = [p.get('value') for p in data]
            expected_priorities = ['low', 'normal', 'high', 'urgent', 'critical']
            has_all_priorities = all(p in priority_values for p in expected_priorities)
            success = has_priorities and has_all_priorities
            self.log_test("Notification Priorities", success, f"Found {len(data)} priority levels")
            return success
        else:
            self.log_test("Notification Priorities", False, f"Status: {response.status_code}")
            return False

    def test_create_notification_admin(self):
        """Test creating notification as admin"""
        if not self.hospital_admin_token:
            self.log_test("Create Notification (Admin)", False, "No hospital admin token")
            return False
        
        original_token = self.token
        self.token = self.hospital_admin_token
        
        notification_data = {
            "user_id": self.user_id,
            "notification_type": "general_info",
            "title": "Test Notification",
            "message": "This is a test notification for the comprehensive notification system.",
            "priority": "normal",
            "related_type": "test",
            "related_id": "test-123",
            "action_url": "/dashboard",
            "action_label": "View Dashboard",
            "channels": ["in_app"],
            "expires_in_hours": 24
        }
        
        response, error = self.make_request('POST', 'notifications/send', notification_data)
        self.token = original_token
        
        if error:
            self.log_test("Create Notification (Admin)", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_notification_id = bool(data.get('notification_id'))
            success = has_notification_id
            self.log_test("Create Notification (Admin)", success, f"Notification ID: {data.get('notification_id')}")
            return success
        else:
            self.log_test("Create Notification (Admin)", False, f"Status: {response.status_code}")
            return False

    def test_get_notifications(self):
        """Test getting notifications with filters"""
        response, error = self.make_request('GET', 'notifications')
        if error:
            self.log_test("Get Notifications", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_notifications = 'notifications' in data
            has_total = 'total' in data
            has_unread_count = 'unread_count' in data
            success = has_notifications and has_total and has_unread_count
            notification_count = len(data.get('notifications', []))
            self.log_test("Get Notifications", success, f"Found {notification_count} notifications, {data.get('unread_count', 0)} unread")
            return success
        else:
            self.log_test("Get Notifications", False, f"Status: {response.status_code}")
            return False

    def test_get_unread_count(self):
        """Test getting unread notification count"""
        response, error = self.make_request('GET', 'notifications/unread-count')
        if error:
            self.log_test("Get Unread Count", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_unread_count = 'unread_count' in data
            has_by_priority = 'by_priority' in data
            success = has_unread_count and has_by_priority
            unread_count = data.get('unread_count', 0)
            priority_counts = data.get('by_priority', {})
            self.log_test("Get Unread Count", success, f"Unread: {unread_count}, By priority: {priority_counts}")
            return success
        else:
            self.log_test("Get Unread Count", False, f"Status: {response.status_code}")
            return False

    def test_notification_preferences(self):
        """Test notification preferences"""
        # Get preferences
        response, error = self.make_request('GET', 'notifications/preferences/me')
        if error:
            self.log_test("Get Notification Preferences", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            success = isinstance(data, dict)
            self.log_test("Get Notification Preferences", success, f"Preferences: {list(data.keys()) if isinstance(data, dict) else 'Invalid'}")
        else:
            self.log_test("Get Notification Preferences", False, f"Status: {response.status_code}")
            return False

        # Update preferences
        preferences_data = {
            "email_enabled": True,
            "in_app_enabled": True,
            "priority_threshold": "normal",
            "quiet_hours_enabled": False,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "08:00"
        }
        
        response, error = self.make_request('PUT', 'notifications/preferences/me', preferences_data)
        if error:
            self.log_test("Update Notification Preferences", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_message = 'message' in data
            success = has_message
            self.log_test("Update Notification Preferences", success, data.get('message', ''))
            return success
        else:
            self.log_test("Update Notification Preferences", False, f"Status: {response.status_code}")
            return False

    def test_bulk_notifications(self):
        """Test sending bulk notifications"""
        if not self.hospital_admin_token:
            self.log_test("Bulk Notifications", False, "No hospital admin token")
            return False
        
        original_token = self.token
        self.token = self.hospital_admin_token
        
        bulk_data = {
            "user_ids": [self.user_id],
            "notification_type": "general_info",
            "title": "Bulk Test Notification",
            "message": "This is a bulk notification test.",
            "priority": "normal"
        }
        
        response, error = self.make_request('POST', 'notifications/send-bulk', bulk_data)
        self.token = original_token
        
        if error:
            self.log_test("Bulk Notifications", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_message = 'message' in data
            success = has_message
            self.log_test("Bulk Notifications", success, data.get('message', ''))
            return success
        else:
            self.log_test("Bulk Notifications", False, f"Status: {response.status_code}")
            return False

    def test_expiration_checks(self):
        """Test running expiration checks"""
        if not self.hospital_admin_token:
            self.log_test("Expiration Checks", False, "No hospital admin token")
            return False
        
        original_token = self.token
        self.token = self.hospital_admin_token
        
        response, error = self.make_request('POST', 'notifications/check-expirations')
        self.token = original_token
        
        if error:
            self.log_test("Expiration Checks", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_message = 'message' in data
            has_access_notifications = 'access_expiring_notifications' in data
            has_consent_notifications = 'consent_expiring_notifications' in data
            success = has_message and has_access_notifications and has_consent_notifications
            access_count = data.get('access_expiring_notifications', 0)
            consent_count = data.get('consent_expiring_notifications', 0)
            self.log_test("Expiration Checks", success, f"Access: {access_count}, Consent: {consent_count} notifications sent")
            return success
        else:
            self.log_test("Expiration Checks", False, f"Status: {response.status_code}")
            return False

    def test_emergency_access_alert(self):
        """Test creating emergency access alert"""
        if not self.test_patient_id:
            self.log_test("Emergency Access Alert", False, "No test patient available")
            return False
        
        alert_data = {
            "patient_id": self.test_patient_id,
            "reason": "Medical emergency - patient unconscious, need immediate access to medical history"
        }
        
        response, error = self.make_request('POST', 'notifications/emergency-access-alert', alert_data)
        if error:
            self.log_test("Emergency Access Alert", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_message = 'message' in data
            has_admins_notified = 'admins_notified' in data
            success = has_message and has_admins_notified
            admins_count = data.get('admins_notified', 0)
            self.log_test("Emergency Access Alert", success, f"Notified {admins_count} administrators")
            return success
        else:
            self.log_test("Emergency Access Alert", False, f"Status: {response.status_code}")
            return False

    def test_notification_statistics(self):
        """Test getting notification statistics"""
        if not self.hospital_admin_token:
            self.log_test("Notification Statistics", False, "No hospital admin token")
            return False
        
        original_token = self.token
        self.token = self.hospital_admin_token
        
        response, error = self.make_request('GET', 'notifications/stats/overview', params={'days': 30})
        self.token = original_token
        
        if error:
            self.log_test("Notification Statistics", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ['period_days', 'total_notifications', 'read_count', 'unread_count', 'read_rate_percent', 'by_type', 'by_priority']
            has_all_fields = all(field in data for field in required_fields)
            success = has_all_fields
            total = data.get('total_notifications', 0)
            read_rate = data.get('read_rate_percent', 0)
            self.log_test("Notification Statistics", success, f"Total: {total}, Read rate: {read_rate}%")
            return success
        else:
            self.log_test("Notification Statistics", False, f"Status: {response.status_code}")
            return False

    def run_notification_tests(self):
        """Run comprehensive notification system tests"""
        print("🔔 Testing Comprehensive Notification System")
        print("=" * 50)
        
        # Setup
        print("Setting up test environment...")
        self.setup_test_user()
        
        # Core notification tests
        self.test_notification_types()
        self.test_notification_priorities()
        self.test_create_notification_admin()
        self.test_get_notifications()
        self.test_get_unread_count()
        self.test_notification_preferences()
        self.test_bulk_notifications()
        self.test_expiration_checks()
        self.test_emergency_access_alert()
        self.test_notification_statistics()
        
        # Summary
        print("\n" + "=" * 50)
        print(f"📊 NOTIFICATION SYSTEM TEST RESULTS")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL NOTIFICATION TESTS PASSED!")
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")

if __name__ == "__main__":
    tester = NotificationTester()
    tester.run_notification_tests()