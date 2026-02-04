#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta

class AdminPortalTester:
    def __init__(self, base_url="https://portal-index.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.hospital_admin_token = None
        self.hospital_admin_id = None
        self.super_admin_token = None
        self.super_admin_id = None
        self.test_permission_group_id = None

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

    def test_setup_regular_user(self):
        """Setup a regular user for testing"""
        user_data = {
            "email": "testdoc@admintest.com",
            "password": "TestDoc123!",
            "first_name": "Test",
            "last_name": "Doctor",
            "role": "physician"
        }
        
        response, error = self.make_request('POST', 'auth/register', user_data)
        if error:
            return self.test_login_regular_user()
        
        if response.status_code in [200, 201]:
            data = response.json()
            self.token = data.get('token')
            self.user_id = data.get('user', {}).get('id')
            return bool(self.token)
        elif response.status_code == 400:
            return self.test_login_regular_user()
        return False

    def test_login_regular_user(self):
        """Login regular user"""
        login_data = {
            "email": "testdoc@admintest.com",
            "password": "TestDoc123!"
        }
        
        response, error = self.make_request('POST', 'auth/login', login_data)
        if error or response.status_code != 200:
            return False
        
        data = response.json()
        self.token = data.get('token')
        self.user_id = data.get('user', {}).get('id')
        return bool(self.token)

    def test_hospital_admin_setup(self):
        """Test creating hospital admin user for admin portal testing"""
        hospital_admin_data = {
            "email": "hospitaladmin@admintest.com",
            "password": "HospitalAdmin123!",
            "first_name": "Hospital",
            "last_name": "Admin",
            "role": "hospital_admin"
        }
        
        response, error = self.make_request('POST', 'auth/register', hospital_admin_data)
        if error:
            self.log_test("Hospital Admin Setup", False, error)
            return False
        
        if response.status_code in [200, 201]:
            data = response.json()
            self.hospital_admin_token = data.get('token')
            self.hospital_admin_id = data.get('user', {}).get('id')
            success = bool(self.hospital_admin_token)
            self.log_test("Hospital Admin Setup", success, "Hospital admin created")
            return success
        elif response.status_code == 400:
            # User already exists, try login
            return self.test_hospital_admin_login()
        else:
            self.log_test("Hospital Admin Setup", False, f"Status: {response.status_code}")
            return False
    
    def test_hospital_admin_login(self):
        """Test hospital admin login"""
        login_data = {
            "email": "hospitaladmin@admintest.com",
            "password": "HospitalAdmin123!"
        }
        
        response, error = self.make_request('POST', 'auth/login', login_data)
        if error:
            self.log_test("Hospital Admin Login", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.hospital_admin_token = data.get('token')
            self.hospital_admin_id = data.get('user', {}).get('id')
            success = bool(self.hospital_admin_token)
            self.log_test("Hospital Admin Login", success, "Hospital admin authenticated")
            return success
        else:
            self.log_test("Hospital Admin Login", False, f"Status: {response.status_code}")
            return False
    
    def test_super_admin_setup(self):
        """Test creating super admin user"""
        super_admin_data = {
            "email": "superadmin@admintest.com",
            "password": "SuperAdmin123!",
            "first_name": "Super",
            "last_name": "Admin",
            "role": "super_admin"
        }
        
        response, error = self.make_request('POST', 'auth/register', super_admin_data)
        if error:
            self.log_test("Super Admin Setup", False, error)
            return False
        
        if response.status_code in [200, 201]:
            data = response.json()
            self.super_admin_token = data.get('token')
            self.super_admin_id = data.get('user', {}).get('id')
            success = bool(self.super_admin_token)
            self.log_test("Super Admin Setup", success, "Super admin created")
            return success
        elif response.status_code == 400:
            # User already exists, try login
            return self.test_super_admin_login()
        else:
            self.log_test("Super Admin Setup", False, f"Status: {response.status_code}")
            return False
    
    def test_super_admin_login(self):
        """Test super admin login"""
        login_data = {
            "email": "superadmin@admintest.com",
            "password": "SuperAdmin123!"
        }
        
        response, error = self.make_request('POST', 'auth/login', login_data)
        if error:
            self.log_test("Super Admin Login", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.super_admin_token = data.get('token')
            self.super_admin_id = data.get('user', {}).get('id')
            success = bool(self.super_admin_token)
            self.log_test("Super Admin Login", success, "Super admin authenticated")
            return success
        else:
            self.log_test("Super Admin Login", False, f"Status: {response.status_code}")
            return False

    # Hospital Admin Tests
    def test_permission_groups(self):
        """Test getting permission groups (Hospital Admin)"""
        if not self.hospital_admin_token:
            self.log_test("Permission Groups", False, "No hospital admin token")
            return False
        
        # Switch to hospital admin token
        original_token = self.token
        self.token = self.hospital_admin_token
        
        response, error = self.make_request('GET', 'admin/permission-groups')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Permission Groups", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_groups = 'groups' in data and len(data['groups']) > 0
            success = has_groups
            self.log_test("Permission Groups", success, f"Found {len(data.get('groups', []))} permission groups")
            return success
        else:
            self.log_test("Permission Groups", False, f"Status: {response.status_code}")
            return False
    
    def test_available_permissions(self):
        """Test getting available permissions (Hospital Admin)"""
        if not self.hospital_admin_token:
            self.log_test("Available Permissions", False, "No hospital admin token")
            return False
        
        # Switch to hospital admin token
        original_token = self.token
        self.token = self.hospital_admin_token
        
        response, error = self.make_request('GET', 'admin/available-permissions')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Available Permissions", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_permissions = 'permissions' in data and len(data['permissions']) > 0
            has_categories = 'categories' in data and len(data['categories']) > 0
            success = has_permissions and has_categories
            self.log_test("Available Permissions", success, f"Found {len(data.get('permissions', []))} permissions in {len(data.get('categories', []))} categories")
            return success
        else:
            self.log_test("Available Permissions", False, f"Status: {response.status_code}")
            return False
    
    def test_create_permission_group(self):
        """Test creating a custom permission group (Hospital Admin)"""
        if not self.hospital_admin_token:
            self.log_test("Create Permission Group", False, "No hospital admin token")
            return False
        
        # Switch to hospital admin token
        original_token = self.token
        self.token = self.hospital_admin_token
        
        group_data = {
            "name": "Test Custom Group",
            "description": "Custom group for testing",
            "permissions": ["patient:view", "patient:update", "order:view"]
        }
        
        response, error = self.make_request('POST', 'admin/permission-groups', group_data)
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Create Permission Group", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_group = 'group' in data and data['group'].get('name') == group_data['name']
            success = has_group
            if success:
                self.test_permission_group_id = data['group'].get('id')
            self.log_test("Create Permission Group", success, f"Created group: {data.get('group', {}).get('name')}")
            return success
        else:
            self.log_test("Create Permission Group", False, f"Status: {response.status_code}")
            return False
    
    def test_update_permission_group(self):
        """Test updating a permission group (Hospital Admin)"""
        if not self.hospital_admin_token:
            self.log_test("Update Permission Group", False, "No hospital admin token")
            return False
        
        if not self.test_permission_group_id:
            self.log_test("Update Permission Group", False, "No test permission group available")
            return False
        
        # Switch to hospital admin token
        original_token = self.token
        self.token = self.hospital_admin_token
        
        update_data = {
            "name": "Updated Test Group",
            "description": "Updated description",
            "permissions": ["patient:view", "patient:update", "order:view", "order:create"]
        }
        
        response, error = self.make_request('PUT', f'admin/permission-groups/{self.test_permission_group_id}', update_data)
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Update Permission Group", False, error)
            return False
        
        success = response.status_code == 200
        self.log_test("Update Permission Group", success, f"Status: {response.status_code}")
        return success
    
    def test_user_management(self):
        """Test user management endpoints (Hospital Admin)"""
        if not self.hospital_admin_token:
            self.log_test("User Management", False, "No hospital admin token")
            return False
        
        # Switch to hospital admin token
        original_token = self.token
        self.token = self.hospital_admin_token
        
        response, error = self.make_request('GET', 'admin/users')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("User Management", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_users = 'users' in data
            has_pagination = 'total' in data and 'page' in data
            success = has_users and has_pagination
            user_count = len(data.get('users', []))
            self.log_test("User Management", success, f"Found {user_count} users with pagination")
            return success
        else:
            self.log_test("User Management", False, f"Status: {response.status_code}")
            return False
    
    def test_user_search_filter(self):
        """Test user search and filtering (Hospital Admin)"""
        if not self.hospital_admin_token:
            self.log_test("User Search/Filter", False, "No hospital admin token")
            return False
        
        # Switch to hospital admin token
        original_token = self.token
        self.token = self.hospital_admin_token
        
        # Test search
        response, error = self.make_request('GET', 'admin/users', params={'search': 'test'})
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("User Search/Filter", False, error)
            return False
        
        success = response.status_code == 200
        if success:
            data = response.json()
            user_count = len(data.get('users', []))
            self.log_test("User Search/Filter", success, f"Search returned {user_count} users")
        else:
            self.log_test("User Search/Filter", False, f"Status: {response.status_code}")
        return success
    
    def test_user_role_update(self):
        """Test updating user role (Hospital Admin)"""
        if not self.hospital_admin_token:
            self.log_test("User Role Update", False, "No hospital admin token")
            return False
        
        if not self.user_id:
            self.log_test("User Role Update", False, "No test user available")
            return False
        
        # Switch to hospital admin token
        original_token = self.token
        self.token = self.hospital_admin_token
        
        role_data = {
            "user_id": self.user_id,
            "role": "nurse",
            "department_id": None,
            "permissions_groups": [],
            "custom_permissions": []
        }
        
        response, error = self.make_request('PUT', f'admin/users/{self.user_id}/role', role_data)
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("User Role Update", False, error)
            return False
        
        success = response.status_code == 200
        self.log_test("User Role Update", success, f"Status: {response.status_code}")
        return success
    
    def test_bulk_user_actions(self):
        """Test bulk user actions (Hospital Admin)"""
        if not self.hospital_admin_token:
            self.log_test("Bulk User Actions", False, "No hospital admin token")
            return False
        
        if not self.user_id:
            self.log_test("Bulk User Actions", False, "No test user available")
            return False
        
        # Switch to hospital admin token
        original_token = self.token
        self.token = self.hospital_admin_token
        
        bulk_action = {
            "user_ids": [self.user_id],
            "action": "activate",
            "reason": "Test activation"
        }
        
        response, error = self.make_request('POST', 'admin/users/bulk-action', bulk_action)
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Bulk User Actions", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_results = 'success' in data and 'failed' in data
            success = has_results and data.get('success', 0) > 0
            self.log_test("Bulk User Actions", success, f"Success: {data.get('success', 0)}, Failed: {data.get('failed', 0)}")
            return success
        else:
            self.log_test("Bulk User Actions", False, f"Status: {response.status_code}")
            return False
    
    def test_user_activity(self):
        """Test getting user activity logs (Hospital Admin)"""
        if not self.hospital_admin_token:
            self.log_test("User Activity", False, "No hospital admin token")
            return False
        
        if not self.user_id:
            self.log_test("User Activity", False, "No test user available")
            return False
        
        # Switch to hospital admin token
        original_token = self.token
        self.token = self.hospital_admin_token
        
        response, error = self.make_request('GET', f'admin/users/{self.user_id}/activity')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("User Activity", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_user = 'user' in data
            has_logs = 'activity_logs' in data
            has_logins = 'login_history' in data
            success = has_user and has_logs and has_logins
            log_count = len(data.get('activity_logs', []))
            self.log_test("User Activity", success, f"Found {log_count} activity logs")
            return success
        else:
            self.log_test("User Activity", False, f"Status: {response.status_code}")
            return False
    
    def test_dashboard_stats(self):
        """Test admin dashboard statistics (Hospital Admin)"""
        if not self.hospital_admin_token:
            self.log_test("Dashboard Stats", False, "No hospital admin token")
            return False
        
        # Switch to hospital admin token
        original_token = self.token
        self.token = self.hospital_admin_token
        
        response, error = self.make_request('GET', 'admin/dashboard/stats')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Dashboard Stats", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ['users', 'role_distribution', 'patients', 'activity_24h']
            has_all_fields = all(field in data for field in required_fields)
            success = has_all_fields
            self.log_test("Dashboard Stats", success, f"Dashboard stats: {list(data.keys())}")
            return success
        else:
            self.log_test("Dashboard Stats", False, f"Status: {response.status_code}")
            return False
    
    def test_sharing_policies(self):
        """Test sharing policies management (Hospital Admin)"""
        if not self.hospital_admin_token:
            self.log_test("Sharing Policies", False, "No hospital admin token")
            return False
        
        # Switch to hospital admin token
        original_token = self.token
        self.token = self.hospital_admin_token
        
        response, error = self.make_request('GET', 'admin/sharing-policies', params={'direction': 'incoming'})
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Sharing Policies", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_policies = 'policies' in data
            has_direction = 'direction' in data
            success = has_policies and has_direction
            policy_count = len(data.get('policies', []))
            self.log_test("Sharing Policies", success, f"Found {policy_count} sharing policies")
            return success
        else:
            self.log_test("Sharing Policies", False, f"Status: {response.status_code}")
            return False

    # Super Admin Tests
    def test_security_policies(self):
        """Test security policies management (Super Admin)"""
        if not self.super_admin_token:
            self.log_test("Security Policies", False, "No super admin token")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', 'admin/security-policies')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Security Policies", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_policies = 'policies' in data and len(data['policies']) > 0
            success = has_policies
            policy_count = len(data.get('policies', []))
            policy_types = [p.get('policy_type') for p in data.get('policies', [])]
            self.log_test("Security Policies", success, f"Found {policy_count} policies: {policy_types}")
            return success
        else:
            self.log_test("Security Policies", False, f"Status: {response.status_code}")
            return False
    
    def test_create_security_policy(self):
        """Test creating/updating security policy (Super Admin)"""
        if not self.super_admin_token:
            self.log_test("Create Security Policy", False, "No super admin token")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        policy_data = {
            "policy_type": "password",
            "name": "Test Password Policy",
            "description": "Test password policy for admin portal",
            "settings": {
                "min_length": 12,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_numbers": True,
                "require_special": True,
                "max_age_days": 90
            },
            "applies_to_roles": ["physician", "nurse"]
        }
        
        response, error = self.make_request('POST', 'admin/security-policies', policy_data)
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Create Security Policy", False, error)
            return False
        
        success = response.status_code == 200
        if success:
            data = response.json()
            message = data.get('message', '')
            self.log_test("Create Security Policy", success, message)
        else:
            self.log_test("Create Security Policy", False, f"Status: {response.status_code}")
        return success
    
    def test_toggle_security_policy(self):
        """Test toggling security policy (Super Admin)"""
        if not self.super_admin_token:
            self.log_test("Toggle Security Policy", False, "No super admin token")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('PUT', 'admin/security-policies/password/toggle', params={'is_active': 'true'})
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Toggle Security Policy", False, error)
            return False
        
        success = response.status_code == 200
        if success:
            data = response.json()
            message = data.get('message', '')
            self.log_test("Toggle Security Policy", success, message)
        else:
            self.log_test("Toggle Security Policy", False, f"Status: {response.status_code}")
        return success
    
    def test_system_health(self):
        """Test system health check (Super Admin)"""
        if not self.super_admin_token:
            self.log_test("System Health", False, "No super admin token")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', 'admin/system/health')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("System Health", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_status = 'status' in data
            has_checks = 'checks' in data and len(data['checks']) > 0
            has_stats = 'stats' in data
            success = has_status and has_checks and has_stats
            status = data.get('status', 'unknown')
            check_count = len(data.get('checks', []))
            self.log_test("System Health", success, f"Status: {status}, {check_count} health checks")
            return success
        else:
            self.log_test("System Health", False, f"Status: {response.status_code}")
            return False
    
    def test_system_stats(self):
        """Test platform statistics (Super Admin)"""
        if not self.super_admin_token:
            self.log_test("System Stats", False, "No super admin token")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', 'admin/system/stats')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("System Stats", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_orgs = 'organizations' in data
            has_users = 'users_by_role' in data
            has_activity = 'activity_trend' in data
            success = has_orgs and has_users and has_activity
            self.log_test("System Stats", success, f"Platform stats: {list(data.keys())}")
            return success
        else:
            self.log_test("System Stats", False, f"Status: {response.status_code}")
            return False
    
    def test_system_audit_logs(self):
        """Test system-wide audit logs (Super Admin)"""
        if not self.super_admin_token:
            self.log_test("System Audit Logs", False, "No super admin token")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', 'admin/system/audit-logs', params={'days': '7'})
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("System Audit Logs", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_logs = 'logs' in data
            has_pagination = 'total' in data and 'page' in data
            success = has_logs and has_pagination
            log_count = len(data.get('logs', []))
            total = data.get('total', 0)
            self.log_test("System Audit Logs", success, f"Found {log_count}/{total} audit logs")
            return success
        else:
            self.log_test("System Audit Logs", False, f"Status: {response.status_code}")
            return False
    
    def test_security_alerts(self):
        """Test security alerts (Super Admin)"""
        if not self.super_admin_token:
            self.log_test("Security Alerts", False, "No super admin token")
            return False
        
        # Switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', 'admin/system/security-alerts', params={'hours': '24'})
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Security Alerts", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_alerts = 'alerts' in data
            has_summary = 'summary' in data
            has_total = 'total' in data
            success = has_alerts and has_summary and has_total
            alert_count = data.get('total', 0)
            self.log_test("Security Alerts", success, f"Found {alert_count} security alerts")
            return success
        else:
            self.log_test("Security Alerts", False, f"Status: {response.status_code}")
            return False

    # Access Control Tests
    def test_access_control_hospital_admin(self):
        """Test that hospital admin cannot access super admin endpoints"""
        if not self.hospital_admin_token:
            self.log_test("Access Control (Hospital Admin)", False, "No hospital admin token")
            return False
        
        # Switch to hospital admin token
        original_token = self.token
        self.token = self.hospital_admin_token
        
        # Try to access super admin endpoint
        response, error = self.make_request('GET', 'admin/system/health')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Access Control (Hospital Admin)", False, error)
            return False
        
        # Should get 403 Forbidden
        success = response.status_code == 403
        self.log_test("Access Control (Hospital Admin)", success, f"Hospital admin correctly denied super admin access: {response.status_code}")
        return success
    
    def test_access_control_regular_user(self):
        """Test that regular users cannot access admin endpoints"""
        if not self.token:
            self.log_test("Access Control (Regular User)", False, "No regular user token")
            return False
        
        # Try to access admin endpoint with regular user token
        response, error = self.make_request('GET', 'admin/permission-groups')
        
        if error:
            self.log_test("Access Control (Regular User)", False, error)
            return False
        
        # Should get 403 Forbidden
        success = response.status_code == 403
        self.log_test("Access Control (Regular User)", success, f"Regular user correctly denied admin access: {response.status_code}")
        return success

    def run_all_tests(self):
        """Run all admin portal tests"""
        print("🔧 Starting Admin Portal Backend API Tests")
        print("=" * 50)
        
        # Setup test users
        print("\n🔧 Setting up Test Users")
        print("-" * 30)
        if not self.test_setup_regular_user():
            print("❌ Failed to setup regular user")
            return False
        
        if not self.test_hospital_admin_setup():
            print("❌ Failed to setup hospital admin")
            return False
        
        if not self.test_super_admin_setup():
            print("❌ Failed to setup super admin")
            return False
        
        # Hospital Admin Tests
        print("\n👥 Testing Hospital Admin Features")
        print("-" * 30)
        self.test_permission_groups()
        self.test_available_permissions()
        self.test_create_permission_group()
        self.test_update_permission_group()
        self.test_user_management()
        self.test_user_search_filter()
        self.test_user_role_update()
        self.test_bulk_user_actions()
        self.test_user_activity()
        self.test_dashboard_stats()
        self.test_sharing_policies()
        
        # Super Admin Tests
        print("\n🔒 Testing Super Admin Features")
        print("-" * 30)
        self.test_security_policies()
        self.test_create_security_policy()
        self.test_toggle_security_policy()
        self.test_system_health()
        self.test_system_stats()
        self.test_system_audit_logs()
        self.test_security_alerts()
        
        # Access Control Tests
        print("\n🛡️ Testing Access Control")
        print("-" * 30)
        self.test_access_control_hospital_admin()
        self.test_access_control_regular_user()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = AdminPortalTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())