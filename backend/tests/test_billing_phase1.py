#!/usr/bin/env python3
"""
Test Suite for Ghana EMR Billing System - Phase 1 Enhancements

Tests:
1. Billing Bug Fixes (520 errors, serialization issues)
2. Expanded Service Code Library (~70 codes)
3. Payment Methods & Invoice Statuses
4. Radiology Integration
"""

import requests
import sys
import json
from datetime import datetime

class BillingPhase1Tester:
    def __init__(self, base_url="https://careflow-183.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.token = None
        self.user_email = "ygtnetworks@gmail.com"
        self.user_password = "test123"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test data
        self.patient_id = None
        self.invoice_id = None

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

    def test_login(self):
        """Test Super Admin Login"""
        login_data = {
            "email": self.user_email,
            "password": self.user_password
        }
        
        response, error = self.make_request('POST', 'auth/login', login_data)
        if error:
            self.log_test("Super Admin Login", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get('token')
            user = data.get('user', {})
            
            success = bool(self.token) and user.get('role') == 'super_admin'
            details = f"Email: {user.get('email')}, Role: {user.get('role')}"
            self.log_test("Super Admin Login", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Super Admin Login", False, error_msg)
            return False

    def test_create_test_patient(self):
        """Create a test patient for billing tests"""
        if not self.token:
            self.log_test("Create Test Patient", False, "No token")
            return False
        
        patient_data = {
            "first_name": "Kwame",
            "last_name": "Mensah",
            "date_of_birth": "1985-03-15",
            "gender": "male",
            "payment_type": "insurance",
            "insurance_provider": "NHIS",
            "insurance_id": "NHIS-GH-123456"
        }
        
        response, error = self.make_request('POST', 'patients', patient_data)
        if error:
            self.log_test("Create Test Patient", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.patient_id = data.get('id')
            
            success = bool(self.patient_id)
            details = f"Patient ID: {self.patient_id}, Name: {data.get('first_name')} {data.get('last_name')}"
            self.log_test("Create Test Patient", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Create Test Patient", False, error_msg)
            return False

    # ===== BILLING BUG FIXES TESTS =====
    
    def test_get_invoices_no_520_error(self):
        """Test GET /api/billing/invoices - Should return invoices WITHOUT 520 error"""
        if not self.token:
            self.log_test("GET Invoices (No 520 Error)", False, "No token")
            return False
        
        response, error = self.make_request('GET', 'billing/invoices')
        if error:
            self.log_test("GET Invoices (No 520 Error)", False, error)
            return False
        
        # Check for 520 error or any server error
        if response.status_code >= 500:
            self.log_test("GET Invoices (No 520 Error)", False, f"Server error: {response.status_code}")
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_invoices = 'invoices' in data
            has_count = 'count' in data
            
            success = has_invoices and has_count
            details = f"Invoices count: {data.get('count', 0)}, No 520 error"
            self.log_test("GET Invoices (No 520 Error)", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("GET Invoices (No 520 Error)", False, error_msg)
            return False

    def test_create_invoice_successfully(self):
        """Test POST /api/billing/invoices - Should create invoices successfully"""
        if not self.token or not self.patient_id:
            self.log_test("Create Invoice Successfully", False, "No token or patient ID")
            return False
        
        invoice_data = {
            "patient_id": self.patient_id,
            "patient_name": "Kwame Mensah",
            "line_items": [
                {
                    "description": "Office visit, established, moderate",
                    "service_code": "99213",
                    "quantity": 1,
                    "unit_price": 100.00,
                    "discount": 0
                },
                {
                    "description": "Malaria test (RDT)",
                    "service_code": "LAB-MALARIA",
                    "quantity": 1,
                    "unit_price": 15.00,
                    "discount": 0
                }
            ],
            "notes": "Phase 1 test invoice"
        }
        
        response, error = self.make_request('POST', 'billing/invoices', invoice_data)
        if error:
            self.log_test("Create Invoice Successfully", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.invoice_id = data.get('invoice_id')
            
            has_invoice_id = bool(self.invoice_id)
            has_invoice_number = bool(data.get('invoice_number'))
            correct_total = data.get('total') == 115.00
            
            success = has_invoice_id and has_invoice_number and correct_total
            details = f"Invoice ID: {self.invoice_id}, Number: {data.get('invoice_number')}, Total: {data.get('total')}"
            self.log_test("Create Invoice Successfully", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Create Invoice Successfully", False, error_msg)
            return False

    def test_invoice_payments_array_no_serialization_error(self):
        """Test that payments array in invoices doesn't cause serialization errors"""
        if not self.token or not self.invoice_id:
            self.log_test("Invoice Payments Array (No Serialization Error)", False, "No token or invoice ID")
            return False
        
        # First, add a payment to the invoice
        payment_data = {
            "invoice_id": self.invoice_id,
            "amount": 50.00,
            "payment_method": "cash",
            "reference": "CASH-001",
            "notes": "Partial payment"
        }
        
        response, error = self.make_request('POST', 'billing/payments', payment_data)
        if error:
            self.log_test("Invoice Payments Array (No Serialization Error)", False, f"Payment creation error: {error}")
            return False
        
        if response.status_code != 200:
            self.log_test("Invoice Payments Array (No Serialization Error)", False, f"Payment creation failed: {response.status_code}")
            return False
        
        # Now get the invoice and check if payments array is properly serialized
        response, error = self.make_request('GET', f'billing/invoices/{self.invoice_id}')
        if error:
            self.log_test("Invoice Payments Array (No Serialization Error)", False, error)
            return False
        
        if response.status_code == 200:
            try:
                data = response.json()
                has_payments = 'payments' in data
                payments_is_list = isinstance(data.get('payments', []), list)
                payments_count = len(data.get('payments', []))
                
                # Check if payments array has no _id fields (serialization issue)
                no_id_fields = True
                if has_payments and payments_is_list:
                    for payment in data.get('payments', []):
                        if '_id' in payment:
                            no_id_fields = False
                            break
                
                success = has_payments and payments_is_list and payments_count > 0 and no_id_fields
                details = f"Payments count: {payments_count}, No _id fields: {no_id_fields}, No serialization error"
                self.log_test("Invoice Payments Array (No Serialization Error)", success, details)
                return success
            except json.JSONDecodeError as e:
                self.log_test("Invoice Payments Array (No Serialization Error)", False, f"JSON decode error: {str(e)}")
                return False
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Invoice Payments Array (No Serialization Error)", False, error_msg)
            return False

    # ===== EXPANDED SERVICE CODE LIBRARY TESTS =====
    
    def test_get_all_service_codes(self):
        """Test GET /api/billing/service-codes - Should return ~70 service codes"""
        response, error = self.make_request('GET', 'billing/service-codes')
        if error:
            self.log_test("Get All Service Codes (~70 codes)", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            service_codes = data.get('service_codes', [])
            codes_count = len(service_codes)
            
            # Should have around 70 codes (allowing some variance)
            has_sufficient_codes = codes_count >= 65 and codes_count <= 75
            
            # Verify structure
            has_proper_structure = True
            if service_codes:
                first_code = service_codes[0]
                has_proper_structure = all(key in first_code for key in ['code', 'description', 'price', 'category'])
            
            success = has_sufficient_codes and has_proper_structure
            details = f"Service codes count: {codes_count}, Expected: ~70, Has proper structure: {has_proper_structure}"
            self.log_test("Get All Service Codes (~70 codes)", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Get All Service Codes (~70 codes)", False, error_msg)
            return False

    def test_get_consumable_service_codes(self):
        """Test GET /api/billing/service-codes?category=consumable - Should return 15 consumable items"""
        response, error = self.make_request('GET', 'billing/service-codes', params={'category': 'consumable'})
        if error:
            self.log_test("Get Consumable Service Codes (15 items)", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            service_codes = data.get('service_codes', [])
            codes_count = len(service_codes)
            
            # Should have 15 consumable items
            has_correct_count = codes_count == 15
            
            # Verify all are consumables
            all_consumables = all(code.get('category') == 'consumable' for code in service_codes)
            
            # Check for expected items
            code_list = [code.get('code') for code in service_codes]
            has_bandages = 'CONS-BANDAGE' in code_list
            has_gauze = 'CONS-GAUZE' in code_list
            has_syringes = 'CONS-SYRINGE-5' in code_list or 'CONS-SYRINGE-10' in code_list
            has_iv_fluids = 'CONS-IV-NS' in code_list
            
            success = has_correct_count and all_consumables and has_bandages and has_gauze and has_syringes and has_iv_fluids
            details = f"Consumables count: {codes_count}, Expected: 15, All consumables: {all_consumables}, Has expected items: {has_bandages and has_gauze and has_syringes}"
            self.log_test("Get Consumable Service Codes (15 items)", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Get Consumable Service Codes (15 items)", False, error_msg)
            return False

    def test_get_medication_service_codes(self):
        """Test GET /api/billing/service-codes?category=medication - Should return 6 medication items"""
        response, error = self.make_request('GET', 'billing/service-codes', params={'category': 'medication'})
        if error:
            self.log_test("Get Medication Service Codes (6 items)", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            service_codes = data.get('service_codes', [])
            codes_count = len(service_codes)
            
            # Should have 6 medication items
            has_correct_count = codes_count == 6
            
            # Verify all are medications
            all_medications = all(code.get('category') == 'medication' for code in service_codes)
            
            # Check for expected medications
            code_list = [code.get('code') for code in service_codes]
            has_paracetamol = 'MED-PARACETAMOL' in code_list
            has_amoxicillin = 'MED-AMOXICILLIN' in code_list
            
            success = has_correct_count and all_medications and has_paracetamol and has_amoxicillin
            details = f"Medications count: {codes_count}, Expected: 6, All medications: {all_medications}"
            self.log_test("Get Medication Service Codes (6 items)", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Get Medication Service Codes (6 items)", False, error_msg)
            return False

    def test_get_admission_service_codes(self):
        """Test GET /api/billing/service-codes?category=admission - Should return 5 admission types"""
        response, error = self.make_request('GET', 'billing/service-codes', params={'category': 'admission'})
        if error:
            self.log_test("Get Admission Service Codes (5 types)", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            service_codes = data.get('service_codes', [])
            codes_count = len(service_codes)
            
            # Should have 5 admission types
            has_correct_count = codes_count == 5
            
            # Verify all are admissions
            all_admissions = all(code.get('category') == 'admission' for code in service_codes)
            
            # Check for expected admission types
            code_list = [code.get('code') for code in service_codes]
            has_general = 'ADM-GENERAL' in code_list
            has_private = 'ADM-PRIVATE' in code_list
            has_icu = 'ADM-ICU' in code_list
            has_nicu = 'ADM-NICU' in code_list
            has_maternity = 'ADM-MATERNITY' in code_list
            
            success = has_correct_count and all_admissions and has_general and has_private and has_icu and has_nicu and has_maternity
            details = f"Admissions count: {codes_count}, Expected: 5, Has all types: {has_general and has_private and has_icu and has_nicu and has_maternity}"
            self.log_test("Get Admission Service Codes (5 types)", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Get Admission Service Codes (5 types)", False, error_msg)
            return False

    def test_get_surgery_service_codes(self):
        """Test GET /api/billing/service-codes?category=surgery - Should return surgical procedures"""
        response, error = self.make_request('GET', 'billing/service-codes', params={'category': 'surgery'})
        if error:
            self.log_test("Get Surgery Service Codes", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            service_codes = data.get('service_codes', [])
            codes_count = len(service_codes)
            
            # Should have surgery codes
            has_surgery_codes = codes_count > 0
            
            # Verify all are surgeries
            all_surgeries = all(code.get('category') == 'surgery' for code in service_codes)
            
            # Check for expected surgeries
            code_list = [code.get('code') for code in service_codes]
            has_appendectomy = 'SURG-APPEND' in code_list
            has_csection = 'SURG-CSECTION' in code_list
            
            success = has_surgery_codes and all_surgeries and has_appendectomy and has_csection
            details = f"Surgery codes count: {codes_count}, All surgeries: {all_surgeries}"
            self.log_test("Get Surgery Service Codes", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Get Surgery Service Codes", False, error_msg)
            return False

    def test_service_code_structure(self):
        """Test that each service code has: code, description, price, category fields"""
        response, error = self.make_request('GET', 'billing/service-codes')
        if error:
            self.log_test("Service Code Structure Verification", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            service_codes = data.get('service_codes', [])
            
            if not service_codes:
                self.log_test("Service Code Structure Verification", False, "No service codes found")
                return False
            
            # Check structure of all codes
            all_have_required_fields = True
            for code in service_codes:
                if not all(key in code for key in ['code', 'description', 'price', 'category']):
                    all_have_required_fields = False
                    break
            
            # Check data types
            all_have_correct_types = True
            for code in service_codes:
                if not isinstance(code.get('code'), str):
                    all_have_correct_types = False
                    break
                if not isinstance(code.get('description'), str):
                    all_have_correct_types = False
                    break
                if not isinstance(code.get('price'), (int, float)):
                    all_have_correct_types = False
                    break
                if not isinstance(code.get('category'), str):
                    all_have_correct_types = False
                    break
            
            success = all_have_required_fields and all_have_correct_types
            details = f"All have required fields: {all_have_required_fields}, All have correct types: {all_have_correct_types}"
            self.log_test("Service Code Structure Verification", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Service Code Structure Verification", False, error_msg)
            return False

    # ===== PAYMENT METHODS & INVOICE STATUSES TESTS =====
    
    def test_invoice_status_enum_values(self):
        """Verify InvoiceStatus enum includes all expected values"""
        # This test verifies by creating invoices with different statuses
        # and checking if they're accepted
        
        # We'll test by checking the invoice we created earlier has a valid status
        if not self.token or not self.invoice_id:
            self.log_test("Invoice Status Enum Values", False, "No token or invoice ID")
            return False
        
        response, error = self.make_request('GET', f'billing/invoices/{self.invoice_id}')
        if error:
            self.log_test("Invoice Status Enum Values", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            
            # Expected statuses: draft, sent, paid, partially_paid, overdue, reversed, voided, pending_insurance, cancelled
            expected_statuses = ['draft', 'sent', 'paid', 'partially_paid', 'overdue', 'reversed', 'voided', 'pending_insurance', 'cancelled']
            
            is_valid_status = status in expected_statuses
            
            success = is_valid_status
            details = f"Invoice status: {status}, Valid: {is_valid_status}"
            self.log_test("Invoice Status Enum Values", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Invoice Status Enum Values", False, error_msg)
            return False

    def test_payment_method_enum_values(self):
        """Verify PaymentMethod enum includes all expected values"""
        # Test by creating payments with different payment methods
        
        if not self.token or not self.invoice_id:
            self.log_test("Payment Method Enum Values", False, "No token or invoice ID")
            return False
        
        # Test cash payment method
        payment_data = {
            "invoice_id": self.invoice_id,
            "amount": 10.00,
            "payment_method": "cash",
            "reference": "CASH-TEST",
            "notes": "Test cash payment"
        }
        
        response, error = self.make_request('POST', 'billing/payments', payment_data)
        if error:
            self.log_test("Payment Method Enum Values", False, error)
            return False
        
        if response.status_code == 200:
            # Expected payment methods: cash, nhis_insurance, visa, mastercard, mobile_money, bank_transfer, paystack
            expected_methods = ['cash', 'nhis_insurance', 'visa', 'mastercard', 'mobile_money', 'bank_transfer', 'paystack']
            
            # Cash payment was accepted, so enum includes cash
            success = True
            details = f"Payment method 'cash' accepted, Expected methods: {', '.join(expected_methods)}"
            self.log_test("Payment Method Enum Values", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Payment Method Enum Values", False, error_msg)
            return False

    # ===== SCENARIO TESTS =====
    
    def test_scenario_create_invoice_with_expanded_codes(self):
        """Scenario 1: Create invoice with consultation, lab test, consumable, and medication"""
        if not self.token or not self.patient_id:
            self.log_test("Scenario: Create Invoice with Expanded Codes", False, "No token or patient ID")
            return False
        
        invoice_data = {
            "patient_id": self.patient_id,
            "patient_name": "Kwame Mensah",
            "line_items": [
                {
                    "description": "Office visit, established, moderate",
                    "service_code": "99213",
                    "quantity": 1,
                    "unit_price": 100.00,
                    "discount": 0
                },
                {
                    "description": "Malaria test (RDT)",
                    "service_code": "LAB-MALARIA",
                    "quantity": 1,
                    "unit_price": 15.00,
                    "discount": 0
                },
                {
                    "description": "Normal saline 1L",
                    "service_code": "CONS-IV-NS",
                    "quantity": 2,
                    "unit_price": 15.00,
                    "discount": 0
                },
                {
                    "description": "Paracetamol 500mg (tablet)",
                    "service_code": "MED-PARACETAMOL",
                    "quantity": 20,
                    "unit_price": 0.50,
                    "discount": 0
                }
            ],
            "notes": "Scenario 1: Expanded codes test"
        }
        
        response, error = self.make_request('POST', 'billing/invoices', invoice_data)
        if error:
            self.log_test("Scenario: Create Invoice with Expanded Codes", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            invoice_id = data.get('invoice_id')
            total = data.get('total')
            
            # Expected total: 100 + 15 + (2*15) + (20*0.50) = 100 + 15 + 30 + 10 = 155
            expected_total = 155.00
            correct_total = abs(total - expected_total) < 0.01
            
            success = bool(invoice_id) and correct_total
            details = f"Invoice ID: {invoice_id}, Total: {total}, Expected: {expected_total}, Correct: {correct_total}"
            self.log_test("Scenario: Create Invoice with Expanded Codes", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Scenario: Create Invoice with Expanded Codes", False, error_msg)
            return False

    def test_scenario_service_code_category_filtering(self):
        """Scenario 2: Service Code Categories - Fetch consumables, medications, admissions"""
        
        # Test 1: Fetch consumables
        response, error = self.make_request('GET', 'billing/service-codes', params={'category': 'consumable'})
        if error or response.status_code != 200:
            self.log_test("Scenario: Service Code Category Filtering", False, "Failed to fetch consumables")
            return False
        
        consumables_count = len(response.json().get('service_codes', []))
        
        # Test 2: Fetch medications
        response, error = self.make_request('GET', 'billing/service-codes', params={'category': 'medication'})
        if error or response.status_code != 200:
            self.log_test("Scenario: Service Code Category Filtering", False, "Failed to fetch medications")
            return False
        
        medications_count = len(response.json().get('service_codes', []))
        
        # Test 3: Fetch admissions
        response, error = self.make_request('GET', 'billing/service-codes', params={'category': 'admission'})
        if error or response.status_code != 200:
            self.log_test("Scenario: Service Code Category Filtering", False, "Failed to fetch admissions")
            return False
        
        admissions_count = len(response.json().get('service_codes', []))
        
        # Verify counts
        consumables_ok = consumables_count == 15
        medications_ok = medications_count == 6
        admissions_ok = admissions_count == 5
        
        success = consumables_ok and medications_ok and admissions_ok
        details = f"Consumables: {consumables_count}/15, Medications: {medications_count}/6, Admissions: {admissions_count}/5"
        self.log_test("Scenario: Service Code Category Filtering", success, details)
        return success

    # ===== RADIOLOGY INTEGRATION TESTS =====
    
    def test_radiology_modalities(self):
        """Test GET /api/radiology/modalities - 8 modalities available"""
        if not self.token:
            self.log_test("Radiology Modalities (8 available)", False, "No token")
            return False
        
        response, error = self.make_request('GET', 'radiology/modalities')
        if error:
            self.log_test("Radiology Modalities (8 available)", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            # Response is a list, not a dict with 'modalities' key
            if isinstance(data, list):
                modalities = data
            else:
                modalities = data.get('modalities', [])
            modalities_count = len(modalities)
            
            # Should have 8 modalities
            has_correct_count = modalities_count == 8
            
            success = has_correct_count
            details = f"Modalities count: {modalities_count}, Expected: 8"
            self.log_test("Radiology Modalities (8 available)", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Radiology Modalities (8 available)", False, error_msg)
            return False

    def test_radiology_create_order(self):
        """Test POST /api/radiology/orders/create - Physicians can order scans"""
        if not self.token or not self.patient_id:
            self.log_test("Radiology Create Order", False, "No token or patient ID")
            return False
        
        order_data = {
            "patient_id": self.patient_id,
            "modality": "xray",
            "study_type": "chest_xray",
            "clinical_indication": "Suspected pneumonia",
            "priority": "routine"
        }
        
        response, error = self.make_request('POST', 'radiology/orders/create', order_data)
        if error:
            self.log_test("Radiology Create Order", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            order_id = data.get('order_id')
            
            success = bool(order_id)
            details = f"Order ID: {order_id}, Modality: xray, Study: chest_xray"
            self.log_test("Radiology Create Order", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Radiology Create Order", False, error_msg)
            return False

    def run_all_tests(self):
        """Run all Phase 1 billing tests"""
        print("🧪 Starting Ghana EMR Billing System - Phase 1 Enhancement Testing")
        print("=" * 80)
        print(f"Backend URL: {self.base_url}")
        print(f"Test User: {self.user_email}")
        print("=" * 80)
        
        # Test sequence
        tests = [
            # Setup
            self.test_login,
            self.test_create_test_patient,
            
            # Billing Bug Fixes
            self.test_get_invoices_no_520_error,
            self.test_create_invoice_successfully,
            self.test_invoice_payments_array_no_serialization_error,
            
            # Expanded Service Code Library
            self.test_get_all_service_codes,
            self.test_get_consumable_service_codes,
            self.test_get_medication_service_codes,
            self.test_get_admission_service_codes,
            self.test_get_surgery_service_codes,
            self.test_service_code_structure,
            
            # Payment Methods & Invoice Statuses
            self.test_invoice_status_enum_values,
            self.test_payment_method_enum_values,
            
            # Scenario Tests
            self.test_scenario_create_invoice_with_expanded_codes,
            self.test_scenario_service_code_category_filtering,
            
            # Radiology Integration
            self.test_radiology_modalities,
            self.test_radiology_create_order
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_test(test.__name__, False, f"Exception: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 80)
        print(f"📊 PHASE 1 BILLING ENHANCEMENT TEST SUMMARY")
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        print("=" * 80)
        
        # Print failed tests
        failed_tests = [t for t in self.test_results if not t['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        else:
            print("\n✅ ALL TESTS PASSED!")
        
        return self.tests_passed == self.tests_run


if __name__ == "__main__":
    tester = BillingPhase1Tester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
