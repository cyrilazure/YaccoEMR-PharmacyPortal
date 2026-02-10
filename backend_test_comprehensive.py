#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Yacco EMR - All Phases (1, 2, 3)
Tests: Billing Enhancements, Finance Settings, Bed Management, Ambulance Module
"""

import requests
import sys
import json
from datetime import datetime, timedelta
import jwt

class ComprehensiveEMRTester:
    def __init__(self, base_url="https://unified-emr.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test users from review request
        self.test_users = {
            "super_admin": {"email": "ygtnetworks@gmail.com", "password": "test123"},
            "it_admin": {"email": "it_admin@yacco.health", "password": "test123"},
            "biller": {"email": "biller@yacco.health", "password": "test123"},
            "physician": {"email": "internist@yacco.health", "password": "test123"},
            "nurse": {"email": "testnurse@hospital.com", "password": "test123"},
            "bed_manager": {"email": "bed_manager@yacco.health", "password": "test123"},
            "radiologist": {"email": "radiologist@yacco.health", "password": "test123"}
        }
        
        # Tokens for different users
        self.tokens = {}
        self.user_ids = {}
        
        # Test data storage
        self.test_patient_id = None
        self.test_invoice_id = None
        self.test_bank_account_id = None
        self.test_mobile_money_id = None
        self.test_ward_id = None
        self.test_bed_id = None
        self.test_admission_id = None
        self.test_vehicle_id = None
        self.test_ambulance_request_id = None
        self.test_radiology_order_id = None

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

    def make_request(self, method, endpoint, data=None, params=None, token=None):
        """Make HTTP request with proper headers"""
        url = f"{self.api_base}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, params=params)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=params)
            else:
                return None, f"Unsupported method: {method}"

            return response, None
        except Exception as e:
            return None, str(e)

    def login_user(self, user_type):
        """Login a user and store token"""
        if user_type not in self.test_users:
            return False
        
        user = self.test_users[user_type]
        response, error = self.make_request('POST', 'auth/login', user)
        
        if error or response.status_code != 200:
            return False
        
        data = response.json()
        self.tokens[user_type] = data.get('token')
        self.user_ids[user_type] = data.get('user', {}).get('id')
        return True

    # ============ PHASE 1: BILLING ENHANCEMENTS ============
    
    def test_billing_invoices_list(self):
        """Test GET /api/billing/invoices - Should return invoices WITHOUT 520 error"""
        if not self.login_user('biller'):
            self.log_test("Billing Invoices List", False, "Failed to login as biller")
            return False
        
        response, error = self.make_request('GET', 'billing/invoices', token=self.tokens['biller'])
        
        if error:
            self.log_test("Billing Invoices List", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_invoices = 'invoices' in data
            is_list = isinstance(data.get('invoices', []), list)
            success = has_invoices and is_list
            self.log_test("Billing Invoices List", success, f"Status: {response.status_code}, Has invoices: {has_invoices}")
            return success
        else:
            self.log_test("Billing Invoices List", False, f"Status: {response.status_code}")
            return False

    def test_service_codes_all(self):
        """Test GET /api/billing/service-codes - All 70 codes"""
        if not self.login_user('biller'):
            self.log_test("Service Codes - All", False, "Failed to login as biller")
            return False
        
        response, error = self.make_request('GET', 'billing/service-codes', token=self.tokens['biller'])
        
        if error:
            self.log_test("Service Codes - All", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            codes = data.get('service_codes', [])
            total = data.get('total', len(codes))
            success = total >= 70 and len(codes) >= 70
            self.log_test("Service Codes - All", success, f"Total: {total}, Expected: >=70")
            return success
        else:
            self.log_test("Service Codes - All", False, f"Status: {response.status_code}")
            return False

    def test_service_codes_by_category(self):
        """Test GET /api/billing/service-codes?category=consumable - 15 items"""
        if not self.login_user('biller'):
            self.log_test("Service Codes - Consumable", False, "Failed to login as biller")
            return False
        
        categories = {
            'consumable': 15,
            'medication': 6,
            'admission': 5,
            'surgery': 4
        }
        
        all_passed = True
        for category, expected_count in categories.items():
            response, error = self.make_request('GET', 'billing/service-codes', 
                                               params={'category': category}, 
                                               token=self.tokens['biller'])
            
            if error or response.status_code != 200:
                self.log_test(f"Service Codes - {category.title()}", False, f"Status: {response.status_code if response else 'Error'}")
                all_passed = False
                continue
            
            data = response.json()
            codes = data.get('service_codes', [])
            actual_count = len(codes)
            success = actual_count >= expected_count
            self.log_test(f"Service Codes - {category.title()}", success, 
                         f"Expected: >={expected_count}, Got: {actual_count}")
            if not success:
                all_passed = False
        
        return all_passed

    def test_invoice_reversal_flow(self):
        """Test Invoice Reversal Flow - Create → Send → Reverse"""
        if not self.login_user('biller'):
            self.log_test("Invoice Reversal Flow", False, "Failed to login as biller")
            return False
        
        # First create a patient
        if not self.login_user('physician'):
            self.log_test("Invoice Reversal Flow - Create Patient", False, "Failed to login as physician")
            return False
        
        patient_data = {
            "first_name": "Invoice",
            "last_name": "Test",
            "date_of_birth": "1990-01-01",
            "gender": "male",
            "payment_type": "cash"
        }
        
        response, error = self.make_request('POST', 'patients', patient_data, token=self.tokens['physician'])
        if error or response.status_code != 200:
            self.log_test("Invoice Reversal Flow - Create Patient", False, f"Status: {response.status_code if response else 'Error'}")
            return False
        
        self.test_patient_id = response.json().get('id')
        
        # Create invoice
        invoice_data = {
            "patient_id": self.test_patient_id,
            "patient_name": "Invoice Test",
            "line_items": [
                {"description": "Consultation", "service_code": "OPD-001", "quantity": 1, "unit_price": 50.0}
            ],
            "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        }
        
        response, error = self.make_request('POST', 'billing/invoices', invoice_data, token=self.tokens['biller'])
        if error or response.status_code != 200:
            self.log_test("Invoice Reversal Flow - Create", False, f"Status: {response.status_code if response else 'Error'}")
            return False
        
        self.test_invoice_id = response.json().get('id')
        
        # Send invoice
        response, error = self.make_request('PUT', f'billing/invoices/{self.test_invoice_id}/send', 
                                           token=self.tokens['biller'])
        if error or response.status_code != 200:
            self.log_test("Invoice Reversal Flow - Send", False, f"Status: {response.status_code if response else 'Error'}")
            return False
        
        # Reverse invoice
        reverse_data = {"reason": "Test reversal"}
        response, error = self.make_request('POST', f'billing/invoices/{self.test_invoice_id}/reverse', 
                                           reverse_data, token=self.tokens['biller'])
        
        if error or response.status_code != 200:
            self.log_test("Invoice Reversal Flow", False, f"Status: {response.status_code if response else 'Error'}")
            return False
        
        data = response.json()
        is_reversed = data.get('status') == 'reversed'
        has_timestamp = 'reversed_at' in data
        has_reason = 'reversal_reason' in data
        
        success = is_reversed and has_timestamp and has_reason
        self.log_test("Invoice Reversal Flow", success, f"Status: {data.get('status')}, Reversed: {is_reversed}")
        return success

    def test_payment_methods(self):
        """Test Payment Methods - Record payment with each of 7 methods"""
        if not self.test_invoice_id or not self.login_user('biller'):
            self.log_test("Payment Methods", False, "No invoice or failed to login")
            return False
        
        # Create a new invoice for payment testing
        invoice_data = {
            "patient_id": self.test_patient_id,
            "patient_name": "Payment Test",
            "line_items": [
                {"description": "Lab Test", "service_code": "LAB-001", "quantity": 1, "unit_price": 100.0}
            ],
            "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        }
        
        response, error = self.make_request('POST', 'billing/invoices', invoice_data, token=self.tokens['biller'])
        if error or response.status_code != 200:
            self.log_test("Payment Methods - Create Invoice", False, "Failed to create invoice")
            return False
        
        payment_invoice_id = response.json().get('id')
        
        payment_methods = ['cash', 'nhis_insurance', 'visa', 'mastercard', 'mobile_money', 'bank_transfer']
        
        all_passed = True
        for method in payment_methods:
            payment_data = {
                "invoice_id": payment_invoice_id,
                "amount": 10.0,
                "payment_method": method,
                "reference": f"TEST-{method.upper()}-001"
            }
            
            response, error = self.make_request('POST', 'billing/payments', payment_data, token=self.tokens['biller'])
            
            if error or response.status_code != 200:
                self.log_test(f"Payment Method - {method}", False, f"Status: {response.status_code if response else 'Error'}")
                all_passed = False
                continue
            
            data = response.json()
            correct_method = data.get('payment_method') == method
            self.log_test(f"Payment Method - {method}", correct_method, f"Method: {data.get('payment_method')}")
            if not correct_method:
                all_passed = False
        
        return all_passed

    def test_paystack_initialization(self):
        """Test Paystack Integration - POST /api/billing/paystack/initialize"""
        if not self.test_invoice_id or not self.login_user('biller'):
            self.log_test("Paystack Initialization", False, "No invoice or failed to login")
            return False
        
        paystack_data = {
            "invoice_id": self.test_invoice_id,
            "email": "test@example.com",
            "callback_url": "https://example.com/callback"
        }
        
        response, error = self.make_request('POST', 'billing/paystack/initialize', paystack_data, 
                                           token=self.tokens['biller'])
        
        if error:
            self.log_test("Paystack Initialization", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_authorization_url = 'authorization_url' in data
            has_reference = 'reference' in data
            has_subaccount = 'subaccount' in data or 'settlement_bank' in data
            
            success = has_authorization_url and has_reference
            self.log_test("Paystack Initialization", success, 
                         f"Has URL: {has_authorization_url}, Has Ref: {has_reference}, Has Subaccount: {has_subaccount}")
            return success
        else:
            self.log_test("Paystack Initialization", False, f"Status: {response.status_code}")
            return False

    # ============ PHASE 2: FINANCE SETTINGS & BED MANAGEMENT ============
    
    def test_bank_account_management(self):
        """Test Bank Account Management - CRUD operations"""
        if not self.login_user('biller'):
            self.log_test("Bank Account Management", False, "Failed to login as biller")
            return False
        
        # Create bank account
        bank_data = {
            "bank_name": "Test Bank",
            "account_number": "1234567890",
            "account_name": "Test Hospital Account",
            "branch": "Main Branch",
            "is_primary": True
        }
        
        response, error = self.make_request('POST', 'finance/bank-accounts', bank_data, 
                                           token=self.tokens['biller'])
        
        if error or response.status_code != 200:
            self.log_test("Bank Account - Create", False, f"Status: {response.status_code if response else 'Error'}")
            return False
        
        self.test_bank_account_id = response.json().get('id')
        self.log_test("Bank Account - Create", True, f"ID: {self.test_bank_account_id}")
        
        # List bank accounts
        response, error = self.make_request('GET', 'finance/bank-accounts', token=self.tokens['biller'])
        if error or response.status_code != 200:
            self.log_test("Bank Account - List", False, f"Status: {response.status_code if response else 'Error'}")
            return False
        
        data = response.json()
        accounts = data.get('accounts', [])
        self.log_test("Bank Account - List", len(accounts) > 0, f"Count: {len(accounts)}")
        
        # Update bank account
        update_data = {"branch": "Updated Branch"}
        response, error = self.make_request('PUT', f'finance/bank-accounts/{self.test_bank_account_id}', 
                                           update_data, token=self.tokens['biller'])
        
        if error or response.status_code != 200:
            self.log_test("Bank Account - Update", False, f"Status: {response.status_code if response else 'Error'}")
            return False
        
        self.log_test("Bank Account - Update", True, "Updated successfully")
        
        return True

    def test_mobile_money_accounts(self):
        """Test Mobile Money Accounts - Create and List"""
        if not self.login_user('biller'):
            self.log_test("Mobile Money Accounts", False, "Failed to login as biller")
            return False
        
        # Create mobile money account
        momo_data = {
            "provider": "MTN",
            "mobile_number": "0241234567",
            "account_name": "Test Hospital MoMo",
            "is_primary": False
        }
        
        response, error = self.make_request('POST', 'finance/mobile-money-accounts', momo_data, 
                                           token=self.tokens['biller'])
        
        if error or response.status_code != 200:
            self.log_test("Mobile Money - Create", False, f"Status: {response.status_code if response else 'Error'}")
            return False
        
        self.test_mobile_money_id = response.json().get('id')
        self.log_test("Mobile Money - Create", True, f"ID: {self.test_mobile_money_id}")
        
        # List mobile money accounts
        response, error = self.make_request('GET', 'finance/mobile-money-accounts', token=self.tokens['biller'])
        if error or response.status_code != 200:
            self.log_test("Mobile Money - List", False, f"Status: {response.status_code if response else 'Error'}")
            return False
        
        data = response.json()
        accounts = data.get('accounts', [])
        self.log_test("Mobile Money - List", len(accounts) > 0, f"Count: {len(accounts)}")
        
        return True

    def test_hospital_prefix(self):
        """Test Hospital Prefix - GET /api/beds/hospital-prefix"""
        if not self.login_user('bed_manager'):
            self.log_test("Hospital Prefix", False, "Failed to login as bed_manager")
            return False
        
        response, error = self.make_request('GET', 'beds/hospital-prefix', token=self.tokens['bed_manager'])
        
        if error:
            self.log_test("Hospital Prefix", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_prefix = 'prefix' in data
            has_hospital_name = 'hospital_name' in data
            prefix = data.get('prefix', '')
            
            success = has_prefix and has_hospital_name and len(prefix) > 0
            self.log_test("Hospital Prefix", success, f"Prefix: {prefix}, Hospital: {data.get('hospital_name')}")
            return success
        else:
            self.log_test("Hospital Prefix", False, f"Status: {response.status_code}")
            return False

    def test_bed_management_flow(self):
        """Test Bed Management - Wards, Beds, Admissions, Transfers, Discharges"""
        if not self.login_user('bed_manager'):
            self.log_test("Bed Management Flow", False, "Failed to login as bed_manager")
            return False
        
        # List wards
        response, error = self.make_request('GET', 'beds/wards', token=self.tokens['bed_manager'])
        if error or response.status_code != 200:
            self.log_test("Bed Management - List Wards", False, f"Status: {response.status_code if response else 'Error'}")
            return False
        
        data = response.json()
        wards = data.get('wards', [])
        self.log_test("Bed Management - List Wards", True, f"Count: {len(wards)}")
        
        if len(wards) > 0:
            self.test_ward_id = wards[0].get('id')
        
        # List beds
        response, error = self.make_request('GET', 'beds/beds', token=self.tokens['bed_manager'])
        if error or response.status_code != 200:
            self.log_test("Bed Management - List Beds", False, f"Status: {response.status_code if response else 'Error'}")
            return False
        
        data = response.json()
        beds = data.get('beds', [])
        self.log_test("Bed Management - List Beds", True, f"Count: {len(beds)}")
        
        if len(beds) > 0:
            self.test_bed_id = beds[0].get('id')
        
        # Test nurse can admit patient
        if not self.login_user('nurse'):
            self.log_test("Bed Management - Nurse Admit", False, "Failed to login as nurse")
            return False
        
        if self.test_patient_id and self.test_bed_id:
            admission_data = {
                "patient_id": self.test_patient_id,
                "bed_id": self.test_bed_id,
                "admission_type": "emergency",
                "admitting_diagnosis": "Test diagnosis"
            }
            
            response, error = self.make_request('POST', 'beds/admissions/create', admission_data, 
                                               token=self.tokens['nurse'])
            
            if error or response.status_code != 200:
                self.log_test("Bed Management - Nurse Admit", False, f"Status: {response.status_code if response else 'Error'}")
            else:
                self.test_admission_id = response.json().get('id')
                self.log_test("Bed Management - Nurse Admit", True, f"Admission ID: {self.test_admission_id}")
        
        return True

    # ============ PHASE 3: AMBULANCE MODULE ============
    
    def test_ambulance_fleet_management(self):
        """Test Ambulance Fleet Management - Register, List, Filter, Update Status"""
        if not self.login_user('it_admin'):
            self.log_test("Ambulance Fleet Management", False, "Failed to login as it_admin")
            return False
        
        # Register vehicle
        vehicle_data = {
            "vehicle_number": "AMB-001",
            "vehicle_type": "basic",
            "make": "Toyota",
            "model": "Hiace",
            "year": 2022,
            "status": "available"
        }
        
        response, error = self.make_request('POST', 'ambulance/vehicles', vehicle_data, 
                                           token=self.tokens['it_admin'])
        
        if error or response.status_code != 200:
            self.log_test("Ambulance - Register Vehicle", False, f"Status: {response.status_code if response else 'Error'}")
            return False
        
        self.test_vehicle_id = response.json().get('id')
        self.log_test("Ambulance - Register Vehicle", True, f"Vehicle ID: {self.test_vehicle_id}")
        
        # List all vehicles
        response, error = self.make_request('GET', 'ambulance/vehicles', token=self.tokens['it_admin'])
        if error or response.status_code != 200:
            self.log_test("Ambulance - List Vehicles", False, f"Status: {response.status_code if response else 'Error'}")
            return False
        
        data = response.json()
        vehicles = data.get('vehicles', [])
        self.log_test("Ambulance - List Vehicles", len(vehicles) > 0, f"Count: {len(vehicles)}")
        
        # Filter by status
        response, error = self.make_request('GET', 'ambulance/vehicles', 
                                           params={'status': 'available'}, 
                                           token=self.tokens['it_admin'])
        if error or response.status_code != 200:
            self.log_test("Ambulance - Filter by Status", False, f"Status: {response.status_code if response else 'Error'}")
            return False
        
        data = response.json()
        available_vehicles = data.get('vehicles', [])
        self.log_test("Ambulance - Filter by Status", True, f"Available: {len(available_vehicles)}")
        
        # Update vehicle status
        response, error = self.make_request('PUT', f'ambulance/vehicles/{self.test_vehicle_id}/status', 
                                           {'status': 'maintenance'}, 
                                           token=self.tokens['it_admin'])
        
        if error or response.status_code != 200:
            self.log_test("Ambulance - Update Status", False, f"Status: {response.status_code if response else 'Error'}")
            return False
        
        self.log_test("Ambulance - Update Status", True, "Status updated to maintenance")
        
        return True

    def test_ambulance_request_workflow(self):
        """Test Ambulance Request Workflow - Complete End-to-End"""
        # 1. Physician creates request
        if not self.login_user('physician'):
            self.log_test("Ambulance Request - Create", False, "Failed to login as physician")
            return False
        
        request_data = {
            "patient_id": self.test_patient_id if self.test_patient_id else "test-patient-id",
            "patient_name": "Test Patient",
            "pickup_location": "Emergency Room",
            "destination": "ICU",
            "priority": "emergency",
            "reason": "Critical condition"
        }
        
        response, error = self.make_request('POST', 'ambulance/requests', request_data, 
                                           token=self.tokens['physician'])
        
        if error or response.status_code != 200:
            self.log_test("Ambulance Request - Create", False, f"Status: {response.status_code if response else 'Error'}")
            return False
        
        self.test_ambulance_request_id = response.json().get('id')
        self.log_test("Ambulance Request - Create", True, f"Request ID: {self.test_ambulance_request_id}")
        
        # 2. List requests
        response, error = self.make_request('GET', 'ambulance/requests', token=self.tokens['physician'])
        if error or response.status_code != 200:
            self.log_test("Ambulance Request - List", False, f"Status: {response.status_code if response else 'Error'}")
            return False
        
        data = response.json()
        requests_list = data.get('requests', [])
        self.log_test("Ambulance Request - List", len(requests_list) > 0, f"Count: {len(requests_list)}")
        
        # 3. IT Admin approves
        if not self.login_user('it_admin'):
            self.log_test("Ambulance Request - Approve", False, "Failed to login as it_admin")
            return False
        
        response, error = self.make_request('PUT', f'ambulance/requests/{self.test_ambulance_request_id}/approve', 
                                           token=self.tokens['it_admin'])
        
        if error or response.status_code != 200:
            self.log_test("Ambulance Request - Approve", False, f"Status: {response.status_code if response else 'Error'}")
            return False
        
        self.log_test("Ambulance Request - Approve", True, "Request approved")
        
        # 4. Dispatch vehicle
        if self.test_vehicle_id:
            dispatch_data = {"vehicle_id": self.test_vehicle_id}
            response, error = self.make_request('POST', f'ambulance/requests/{self.test_ambulance_request_id}/dispatch', 
                                               dispatch_data, token=self.tokens['it_admin'])
            
            if error or response.status_code != 200:
                self.log_test("Ambulance Request - Dispatch", False, f"Status: {response.status_code if response else 'Error'}")
            else:
                self.log_test("Ambulance Request - Dispatch", True, "Vehicle dispatched")
        
        # 5. Update status to en_route
        status_data = {"status": "en_route"}
        response, error = self.make_request('PUT', f'ambulance/requests/{self.test_ambulance_request_id}/update-status', 
                                           status_data, token=self.tokens['it_admin'])
        
        if error or response.status_code != 200:
            self.log_test("Ambulance Request - En Route", False, f"Status: {response.status_code if response else 'Error'}")
        else:
            self.log_test("Ambulance Request - En Route", True, "Status: en_route")
        
        # 6. Update status to arrived
        status_data = {"status": "arrived"}
        response, error = self.make_request('PUT', f'ambulance/requests/{self.test_ambulance_request_id}/update-status', 
                                           status_data, token=self.tokens['it_admin'])
        
        if error or response.status_code != 200:
            self.log_test("Ambulance Request - Arrived", False, f"Status: {response.status_code if response else 'Error'}")
        else:
            self.log_test("Ambulance Request - Arrived", True, "Status: arrived")
        
        # 7. Update status to completed
        status_data = {"status": "completed"}
        response, error = self.make_request('PUT', f'ambulance/requests/{self.test_ambulance_request_id}/update-status', 
                                           status_data, token=self.tokens['it_admin'])
        
        if error or response.status_code != 200:
            self.log_test("Ambulance Request - Completed", False, f"Status: {response.status_code if response else 'Error'}")
        else:
            self.log_test("Ambulance Request - Completed", True, "Status: completed")
        
        return True

    def test_ambulance_dashboard(self):
        """Test Ambulance Dashboard - GET /api/ambulance/dashboard"""
        if not self.login_user('it_admin'):
            self.log_test("Ambulance Dashboard", False, "Failed to login as it_admin")
            return False
        
        response, error = self.make_request('GET', 'ambulance/dashboard', token=self.tokens['it_admin'])
        
        if error:
            self.log_test("Ambulance Dashboard", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_fleet = 'fleet' in data
            has_requests = 'requests' in data
            has_staff = 'staff' in data
            
            success = has_fleet and has_requests and has_staff
            self.log_test("Ambulance Dashboard", success, 
                         f"Fleet: {has_fleet}, Requests: {has_requests}, Staff: {has_staff}")
            return success
        else:
            self.log_test("Ambulance Dashboard", False, f"Status: {response.status_code}")
            return False

    def test_ambulance_access_control(self):
        """Test Ambulance Access Control - Role-based permissions"""
        # Test physician can create request
        if not self.login_user('physician'):
            self.log_test("Ambulance Access - Physician Create", False, "Failed to login as physician")
            return False
        
        request_data = {
            "patient_id": "test-patient",
            "patient_name": "Test",
            "pickup_location": "ER",
            "destination": "ICU",
            "priority": "routine",
            "reason": "Transfer"
        }
        
        response, error = self.make_request('POST', 'ambulance/requests', request_data, 
                                           token=self.tokens['physician'])
        
        physician_can_create = response and response.status_code == 200
        self.log_test("Ambulance Access - Physician Create", physician_can_create, 
                     f"Status: {response.status_code if response else 'Error'}")
        
        # Test biller CANNOT create request (403)
        if not self.login_user('biller'):
            self.log_test("Ambulance Access - Biller Denied", False, "Failed to login as biller")
            return False
        
        response, error = self.make_request('POST', 'ambulance/requests', request_data, 
                                           token=self.tokens['biller'])
        
        biller_denied = response and response.status_code == 403
        self.log_test("Ambulance Access - Biller Denied", biller_denied, 
                     f"Status: {response.status_code if response else 'Error'}")
        
        return physician_can_create and biller_denied

    # ============ INTEGRATION TESTS ============
    
    def test_radiology_integration(self):
        """Test Radiology Integration - Modalities, Orders, Access Control"""
        if not self.login_user('physician'):
            self.log_test("Radiology Integration", False, "Failed to login as physician")
            return False
        
        # Get modalities
        response, error = self.make_request('GET', 'radiology/modalities', token=self.tokens['physician'])
        if error or response.status_code != 200:
            self.log_test("Radiology - Modalities", False, f"Status: {response.status_code if response else 'Error'}")
            return False
        
        modalities = response.json()  # Returns a list directly
        has_8_modalities = isinstance(modalities, list) and len(modalities) >= 8
        self.log_test("Radiology - Modalities", has_8_modalities, f"Count: {len(modalities) if isinstance(modalities, list) else 'N/A'}, Expected: >=8")
        
        # Create radiology order
        if self.test_patient_id:
            order_data = {
                "patient_id": self.test_patient_id,
                "modality": "xray",
                "study_type": "chest_xray",
                "clinical_indication": "Suspected pneumonia",
                "priority": "routine"
            }
            
            response, error = self.make_request('POST', 'radiology/orders/create', order_data, 
                                               token=self.tokens['physician'])
            
            if error or response.status_code != 200:
                self.log_test("Radiology - Create Order", False, f"Status: {response.status_code if response else 'Error'}")
            else:
                self.test_radiology_order_id = response.json().get('id')
                self.log_test("Radiology - Create Order", True, f"Order ID: {self.test_radiology_order_id}")
        
        # Test access control - radiologist CAN create reports
        if not self.login_user('radiologist'):
            self.log_test("Radiology - Access Control", False, "Failed to login as radiologist")
            return False
        
        # Radiologist CAN create reports
        if self.test_radiology_order_id:
            report_data = {
                "order_id": self.test_radiology_order_id,
                "findings": "Test findings",
                "impression": "Test impression"
            }
            
            response, error = self.make_request('POST', 'radiology/reports/create', report_data, 
                                               token=self.tokens['radiologist'])
            
            radiologist_can_report = response and response.status_code == 200
            self.log_test("Radiology - Radiologist Can Report", radiologist_can_report, 
                         f"Status: {response.status_code if response else 'Error'}")
        
        return True

    # ============ MAIN TEST RUNNER ============
    
    def run_all_tests(self):
        """Run all comprehensive tests"""
        print("=" * 80)
        print("🧪 COMPREHENSIVE BACKEND TESTING - ALL PHASES (1, 2, 3)")
        print("=" * 80)
        print(f"Backend URL: {self.base_url}")
        print("=" * 80)
        
        print("\n📋 PHASE 1: BILLING ENHANCEMENTS")
        print("-" * 80)
        self.test_billing_invoices_list()
        self.test_service_codes_all()
        self.test_service_codes_by_category()
        self.test_invoice_reversal_flow()
        self.test_payment_methods()
        self.test_paystack_initialization()
        
        print("\n📋 PHASE 2: FINANCE SETTINGS & BED MANAGEMENT")
        print("-" * 80)
        self.test_bank_account_management()
        self.test_mobile_money_accounts()
        self.test_hospital_prefix()
        self.test_bed_management_flow()
        
        print("\n📋 PHASE 3: AMBULANCE MODULE")
        print("-" * 80)
        self.test_ambulance_fleet_management()
        self.test_ambulance_request_workflow()
        self.test_ambulance_dashboard()
        self.test_ambulance_access_control()
        
        print("\n📋 INTEGRATION TESTS")
        print("-" * 80)
        self.test_radiology_integration()
        
        # Print summary
        print("\n" + "=" * 80)
        print(f"📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        # Print failed tests
        failed_tests = [t for t in self.test_results if not t['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            print("-" * 80)
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        
        print("\n" + "=" * 80)
        return self.tests_passed == self.tests_run


if __name__ == "__main__":
    tester = ComprehensiveEMRTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
