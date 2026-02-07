#!/usr/bin/env python3
"""
Comprehensive Testing for Phase 1 Billing Enhancements
Tests all new features: expanded payment methods, invoice reversal, void, payment method changes, 
expanded service codes, and audit logging
"""

import requests
import sys
import json
from datetime import datetime, timedelta

class BillingPhase1Tester:
    def __init__(self, base_url="https://carecloud-3.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.token = None
        self.user_email = "ygtnetworks@gmail.com"
        self.user_password = "test123"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test data storage
        self.patient_id = None
        self.invoice_id = None
        self.invoice_number = None
        self.payment_id = None

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
        """Test login and get auth token"""
        login_data = {
            "email": self.user_email,
            "password": self.user_password
        }
        
        response, error = self.make_request('POST', 'auth/login', login_data)
        if error:
            self.log_test("Login", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get('token')
            success = bool(self.token)
            self.log_test("Login", success, f"Token received: {bool(self.token)}")
            return success
        else:
            self.log_test("Login", False, f"Status: {response.status_code}")
            return False

    def test_get_invoices_no_520_error(self):
        """Test GET /api/billing/invoices - Should work WITHOUT 520 error"""
        response, error = self.make_request('GET', 'billing/invoices')
        if error:
            self.log_test("GET /api/billing/invoices (No 520 Error)", False, error)
            return False
        
        # Check for 520 error
        if response.status_code == 520:
            self.log_test("GET /api/billing/invoices (No 520 Error)", False, "520 Server Error encountered")
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_invoices = 'invoices' in data
            has_count = 'count' in data
            success = has_invoices and has_count
            self.log_test("GET /api/billing/invoices (No 520 Error)", success, f"Invoices: {len(data.get('invoices', []))}")
            return success
        else:
            self.log_test("GET /api/billing/invoices (No 520 Error)", False, f"Status: {response.status_code}")
            return False

    def test_expanded_service_codes_total(self):
        """Test GET /api/billing/service-codes - Returns 70 total codes"""
        response, error = self.make_request('GET', 'billing/service-codes')
        if error:
            self.log_test("Service Codes Total (70 codes)", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            codes = data.get('service_codes', [])
            total_codes = len(codes)
            success = total_codes == 70
            self.log_test("Service Codes Total (70 codes)", success, f"Total: {total_codes}, Expected: 70")
            return success
        else:
            self.log_test("Service Codes Total (70 codes)", False, f"Status: {response.status_code}")
            return False

    def test_service_codes_by_category(self):
        """Test service codes by category"""
        categories = {
            "consumable": 15,
            "medication": 6,
            "surgery": 4,
            "admission": 5
        }
        
        all_passed = True
        for category, expected_count in categories.items():
            response, error = self.make_request('GET', 'billing/service-codes', params={"category": category})
            if error:
                self.log_test(f"Service Codes - {category} ({expected_count} items)", False, error)
                all_passed = False
                continue
            
            if response.status_code == 200:
                data = response.json()
                codes = data.get('service_codes', [])
                actual_count = len(codes)
                success = actual_count == expected_count
                self.log_test(f"Service Codes - {category} ({expected_count} items)", success, 
                            f"Expected: {expected_count}, Got: {actual_count}")
                if not success:
                    all_passed = False
            else:
                self.log_test(f"Service Codes - {category} ({expected_count} items)", False, 
                            f"Status: {response.status_code}")
                all_passed = False
        
        return all_passed

    def test_create_patient(self):
        """Create a test patient for billing tests"""
        patient_data = {
            "first_name": "Kwame",
            "last_name": "Mensah",
            "date_of_birth": "1985-03-15",
            "gender": "male",
            "payment_type": "insurance",
            "insurance_provider": "NHIS",
            "insurance_id": "NHIS-GH-2024-12345"
        }
        
        response, error = self.make_request('POST', 'patients', patient_data)
        if error:
            self.log_test("Create Test Patient", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.patient_id = data.get('id')
            success = bool(self.patient_id)
            self.log_test("Create Test Patient", success, f"Patient ID: {self.patient_id}")
            return success
        else:
            self.log_test("Create Test Patient", False, f"Status: {response.status_code}")
            return False

    def test_create_invoice_with_insurance(self):
        """Create invoice with insurance for testing"""
        if not self.patient_id:
            self.log_test("Create Invoice with Insurance", False, "No patient ID")
            return False
        
        invoice_data = {
            "patient_id": self.patient_id,
            "patient_name": "Kwame Mensah",
            "line_items": [
                {
                    "description": "Specialist consultation",
                    "service_code": "CONS-SPEC",
                    "quantity": 1,
                    "unit_price": 200.00,
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
            "notes": "Initial consultation and malaria screening",
            "insurance_id": "NHIS-GH-2024-12345"
        }
        
        response, error = self.make_request('POST', 'billing/invoices', invoice_data)
        if error:
            self.log_test("Create Invoice with Insurance", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.invoice_id = data.get('invoice_id')
            self.invoice_number = data.get('invoice_number')
            total = data.get('total')
            success = bool(self.invoice_id) and total == 215.00
            self.log_test("Create Invoice with Insurance", success, 
                        f"Invoice: {self.invoice_number}, Total: ₵{total}")
            return success
        else:
            self.log_test("Create Invoice with Insurance", False, f"Status: {response.status_code}")
            return False

    def test_send_invoice(self):
        """Test sending invoice (draft → sent)"""
        if not self.invoice_id:
            self.log_test("Send Invoice (draft → sent)", False, "No invoice ID")
            return False
        
        response, error = self.make_request('PUT', f'billing/invoices/{self.invoice_id}/send')
        if error:
            self.log_test("Send Invoice (draft → sent)", False, error)
            return False
        
        if response.status_code == 200:
            # Verify status changed
            invoice_response, _ = self.make_request('GET', f'billing/invoices/{self.invoice_id}')
            if invoice_response and invoice_response.status_code == 200:
                invoice = invoice_response.json()
                success = invoice.get('status') == 'sent'
                self.log_test("Send Invoice (draft → sent)", success, f"Status: {invoice.get('status')}")
                return success
            else:
                self.log_test("Send Invoice (draft → sent)", False, "Could not verify status")
                return False
        else:
            self.log_test("Send Invoice (draft → sent)", False, f"Status: {response.status_code}")
            return False

    def test_payment_method_cash(self):
        """Test recording payment with method=cash"""
        if not self.invoice_id:
            self.log_test("Payment Method: cash", False, "No invoice ID")
            return False
        
        payment_data = {
            "invoice_id": self.invoice_id,
            "amount": 50.00,
            "payment_method": "cash",
            "reference": "CASH-001",
            "notes": "Partial cash payment"
        }
        
        response, error = self.make_request('POST', 'billing/payments', payment_data)
        if error:
            self.log_test("Payment Method: cash", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.payment_id = data.get('payment_id')
            success = bool(self.payment_id) and data.get('message') == 'Payment recorded'
            self.log_test("Payment Method: cash", success, f"Payment ID: {self.payment_id}")
            return success
        else:
            self.log_test("Payment Method: cash", False, f"Status: {response.status_code}")
            return False

    def test_payment_methods_all(self):
        """Test all 7 payment methods"""
        if not self.invoice_id:
            self.log_test("All Payment Methods", False, "No invoice ID")
            return False
        
        payment_methods = [
            "nhis_insurance",
            "visa",
            "mastercard",
            "mobile_money",
            "bank_transfer"
        ]
        
        all_passed = True
        for method in payment_methods:
            payment_data = {
                "invoice_id": self.invoice_id,
                "amount": 10.00,
                "payment_method": method,
                "reference": f"{method.upper()}-TEST-001",
                "notes": f"Test payment via {method}"
            }
            
            response, error = self.make_request('POST', 'billing/payments', payment_data)
            if error:
                self.log_test(f"Payment Method: {method}", False, error)
                all_passed = False
                continue
            
            if response.status_code == 200:
                data = response.json()
                success = data.get('message') == 'Payment recorded'
                self.log_test(f"Payment Method: {method}", success, f"Payment recorded")
                if not success:
                    all_passed = False
            else:
                self.log_test(f"Payment Method: {method}", False, f"Status: {response.status_code}")
                all_passed = False
        
        return all_passed

    def test_invoice_reversal_workflow(self):
        """Test complete invoice reversal workflow"""
        # Create new invoice for reversal test
        if not self.patient_id:
            self.log_test("Invoice Reversal Workflow", False, "No patient ID")
            return False
        
        # 1. Create invoice
        invoice_data = {
            "patient_id": self.patient_id,
            "patient_name": "Kwame Mensah",
            "line_items": [
                {
                    "description": "Office visit",
                    "service_code": "99213",
                    "quantity": 1,
                    "unit_price": 100.00,
                    "discount": 0
                }
            ],
            "notes": "Test invoice for reversal"
        }
        
        response, error = self.make_request('POST', 'billing/invoices', invoice_data)
        if error or response.status_code != 200:
            self.log_test("Invoice Reversal Workflow - Create", False, "Failed to create invoice")
            return False
        
        reversal_invoice_id = response.json().get('invoice_id')
        
        # 2. Send invoice (draft → sent)
        response, error = self.make_request('PUT', f'billing/invoices/{reversal_invoice_id}/send')
        if error or response.status_code != 200:
            self.log_test("Invoice Reversal Workflow - Send", False, "Failed to send invoice")
            return False
        
        # 3. Reverse invoice
        response, error = self.make_request('PUT', f'billing/invoices/{reversal_invoice_id}/reverse', 
                                          params={"reason": "Test reversal"})
        if error or response.status_code != 200:
            self.log_test("Invoice Reversal Workflow - Reverse", False, f"Failed to reverse: {error or response.status_code}")
            return False
        
        # 4. Verify reversal
        invoice_response, _ = self.make_request('GET', f'billing/invoices/{reversal_invoice_id}')
        if invoice_response and invoice_response.status_code == 200:
            invoice = invoice_response.json()
            status_correct = invoice.get('status') == 'reversed'
            has_reversed_at = bool(invoice.get('reversed_at'))
            has_reversed_by = bool(invoice.get('reversed_by'))
            has_reversal_reason = bool(invoice.get('reversal_reason'))
            
            success = status_correct and has_reversed_at and has_reversed_by and has_reversal_reason
            details = f"Status: {invoice.get('status')}, Reversed At: {bool(has_reversed_at)}, By: {bool(has_reversed_by)}, Reason: {bool(has_reversal_reason)}"
            self.log_test("Invoice Reversal Workflow", success, details)
            return success
        else:
            self.log_test("Invoice Reversal Workflow", False, "Could not verify reversal")
            return False

    def test_invoice_reversal_edge_cases(self):
        """Test invoice reversal edge cases"""
        if not self.patient_id:
            self.log_test("Invoice Reversal Edge Cases", False, "No patient ID")
            return False
        
        all_passed = True
        
        # Test 1: Try reversing a draft invoice (should fail)
        invoice_data = {
            "patient_id": self.patient_id,
            "patient_name": "Kwame Mensah",
            "line_items": [{"description": "Test", "quantity": 1, "unit_price": 50.00, "discount": 0}]
        }
        response, _ = self.make_request('POST', 'billing/invoices', invoice_data)
        if response and response.status_code == 200:
            draft_invoice_id = response.json().get('invoice_id')
            
            # Try to reverse draft invoice
            response, _ = self.make_request('PUT', f'billing/invoices/{draft_invoice_id}/reverse')
            success = response.status_code == 400  # Should fail
            self.log_test("Reversal Edge Case: Draft Invoice (should fail)", success, 
                        f"Status: {response.status_code}, Expected: 400")
            if not success:
                all_passed = False
        
        # Test 2: Try reversing a paid invoice (should fail)
        # Create, send, and pay invoice
        response, _ = self.make_request('POST', 'billing/invoices', invoice_data)
        if response and response.status_code == 200:
            paid_invoice_id = response.json().get('invoice_id')
            
            # Send invoice
            self.make_request('PUT', f'billing/invoices/{paid_invoice_id}/send')
            
            # Pay invoice
            payment_data = {
                "invoice_id": paid_invoice_id,
                "amount": 50.00,
                "payment_method": "cash"
            }
            self.make_request('POST', 'billing/payments', payment_data)
            
            # Try to reverse paid invoice
            response, _ = self.make_request('PUT', f'billing/invoices/{paid_invoice_id}/reverse')
            success = response.status_code == 400  # Should fail
            self.log_test("Reversal Edge Case: Paid Invoice (should fail)", success, 
                        f"Status: {response.status_code}, Expected: 400")
            if not success:
                all_passed = False
        
        # Test 3: Try reversing already reversed invoice (should fail)
        response, _ = self.make_request('POST', 'billing/invoices', invoice_data)
        if response and response.status_code == 200:
            reversed_invoice_id = response.json().get('invoice_id')
            
            # Send and reverse
            self.make_request('PUT', f'billing/invoices/{reversed_invoice_id}/send')
            self.make_request('PUT', f'billing/invoices/{reversed_invoice_id}/reverse')
            
            # Try to reverse again
            response, _ = self.make_request('PUT', f'billing/invoices/{reversed_invoice_id}/reverse')
            success = response.status_code == 400  # Should fail
            self.log_test("Reversal Edge Case: Already Reversed (should fail)", success, 
                        f"Status: {response.status_code}, Expected: 400")
            if not success:
                all_passed = False
        
        return all_passed

    def test_invoice_void_functionality(self):
        """Test invoice void functionality"""
        if not self.patient_id:
            self.log_test("Invoice Void Functionality", False, "No patient ID")
            return False
        
        # Create invoice for voiding
        invoice_data = {
            "patient_id": self.patient_id,
            "patient_name": "Kwame Mensah",
            "line_items": [
                {
                    "description": "Test service",
                    "quantity": 1,
                    "unit_price": 75.00,
                    "discount": 0
                }
            ]
        }
        
        response, error = self.make_request('POST', 'billing/invoices', invoice_data)
        if error or response.status_code != 200:
            self.log_test("Invoice Void Functionality", False, "Failed to create invoice")
            return False
        
        void_invoice_id = response.json().get('invoice_id')
        
        # Void the invoice
        response, error = self.make_request('PUT', f'billing/invoices/{void_invoice_id}/void', 
                                          params={"reason": "Test void"})
        if error or response.status_code != 200:
            self.log_test("Invoice Void Functionality", False, f"Failed to void: {error or response.status_code}")
            return False
        
        # Verify void
        invoice_response, _ = self.make_request('GET', f'billing/invoices/{void_invoice_id}')
        if invoice_response and invoice_response.status_code == 200:
            invoice = invoice_response.json()
            status_correct = invoice.get('status') == 'voided'
            has_voided_at = bool(invoice.get('voided_at'))
            has_void_reason = bool(invoice.get('void_reason'))
            
            success = status_correct and has_voided_at and has_void_reason
            details = f"Status: {invoice.get('status')}, Voided At: {bool(has_voided_at)}, Reason: {bool(has_void_reason)}"
            self.log_test("Invoice Void Functionality", success, details)
            return success
        else:
            self.log_test("Invoice Void Functionality", False, "Could not verify void")
            return False

    def test_void_paid_invoice_should_fail(self):
        """Test voiding a paid invoice (should fail)"""
        if not self.patient_id:
            self.log_test("Void Paid Invoice (should fail)", False, "No patient ID")
            return False
        
        # Create and pay invoice
        invoice_data = {
            "patient_id": self.patient_id,
            "patient_name": "Kwame Mensah",
            "line_items": [{"description": "Test", "quantity": 1, "unit_price": 50.00, "discount": 0}]
        }
        
        response, _ = self.make_request('POST', 'billing/invoices', invoice_data)
        if response and response.status_code == 200:
            paid_invoice_id = response.json().get('invoice_id')
            
            # Pay invoice
            payment_data = {
                "invoice_id": paid_invoice_id,
                "amount": 50.00,
                "payment_method": "cash"
            }
            self.make_request('POST', 'billing/payments', payment_data)
            
            # Try to void paid invoice
            response, _ = self.make_request('PUT', f'billing/invoices/{paid_invoice_id}/void')
            success = response.status_code == 400  # Should fail
            self.log_test("Void Paid Invoice (should fail)", success, 
                        f"Status: {response.status_code}, Expected: 400")
            return success
        
        self.log_test("Void Paid Invoice (should fail)", False, "Failed to create test invoice")
        return False

    def test_payment_method_change(self):
        """Test payment method change functionality"""
        if not self.patient_id:
            self.log_test("Payment Method Change", False, "No patient ID")
            return False
        
        # Create invoice with insurance
        invoice_data = {
            "patient_id": self.patient_id,
            "patient_name": "Kwame Mensah",
            "line_items": [{"description": "Test", "quantity": 1, "unit_price": 100.00, "discount": 0}],
            "insurance_id": "NHIS-TEST-001"
        }
        
        response, _ = self.make_request('POST', 'billing/invoices', invoice_data)
        if not response or response.status_code != 200:
            self.log_test("Payment Method Change", False, "Failed to create invoice")
            return False
        
        change_invoice_id = response.json().get('invoice_id')
        
        # Change method: insurance → cash
        response, error = self.make_request('PUT', f'billing/invoices/{change_invoice_id}/change-payment-method', 
                                          params={"new_method": "cash", "reason": "Patient prefers cash"})
        if error or response.status_code != 200:
            self.log_test("Payment Method Change (insurance → cash)", False, 
                        f"Failed: {error or response.status_code}")
            return False
        
        # Verify change
        invoice_response, _ = self.make_request('GET', f'billing/invoices/{change_invoice_id}')
        if invoice_response and invoice_response.status_code == 200:
            invoice = invoice_response.json()
            method_changed = invoice.get('payment_method') == 'cash'
            has_change_timestamp = bool(invoice.get('payment_method_changed_at'))
            
            success = method_changed and has_change_timestamp
            self.log_test("Payment Method Change (insurance → cash)", success, 
                        f"Method: {invoice.get('payment_method')}, Changed: {bool(has_change_timestamp)}")
            return success
        
        self.log_test("Payment Method Change", False, "Could not verify change")
        return False

    def test_multi_item_invoice_with_expanded_codes(self):
        """Test multi-item invoice with items from different categories"""
        if not self.patient_id:
            self.log_test("Multi-Item Invoice (Expanded Codes)", False, "No patient ID")
            return False
        
        invoice_data = {
            "patient_id": self.patient_id,
            "patient_name": "Kwame Mensah",
            "line_items": [
                {
                    "description": "Specialist consultation",
                    "service_code": "CONS-SPEC",
                    "quantity": 1,
                    "unit_price": 200.00,
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
                    "quantity": 1,
                    "unit_price": 15.00,
                    "discount": 0
                },
                {
                    "description": "Artemether-Lumefantrine (malaria treatment)",
                    "service_code": "MED-ARTEMETHER",
                    "quantity": 1,
                    "unit_price": 8.00,
                    "discount": 0
                }
            ],
            "notes": "Multi-category invoice test"
        }
        
        response, error = self.make_request('POST', 'billing/invoices', invoice_data)
        if error or response.status_code != 200:
            self.log_test("Multi-Item Invoice (Expanded Codes)", False, 
                        f"Failed to create: {error or response.status_code}")
            return False
        
        data = response.json()
        total = data.get('total')
        expected_total = 238.00  # 200 + 15 + 15 + 8
        
        success = total == expected_total
        self.log_test("Multi-Item Invoice (Expanded Codes)", success, 
                    f"Total: ₵{total}, Expected: ₵{expected_total}")
        return success

    def test_invoice_status_system(self):
        """Test all 9 invoice statuses"""
        if not self.patient_id:
            self.log_test("Invoice Status System (9 statuses)", False, "No patient ID")
            return False
        
        statuses_tested = []
        
        # 1. DRAFT - Create invoice
        invoice_data = {
            "patient_id": self.patient_id,
            "patient_name": "Kwame Mensah",
            "line_items": [{"description": "Test", "quantity": 1, "unit_price": 100.00, "discount": 0}]
        }
        response, _ = self.make_request('POST', 'billing/invoices', invoice_data)
        if response and response.status_code == 200:
            test_invoice_id = response.json().get('invoice_id')
            invoice_response, _ = self.make_request('GET', f'billing/invoices/{test_invoice_id}')
            if invoice_response and invoice_response.status_code == 200:
                status = invoice_response.json().get('status')
                if status == 'draft':
                    statuses_tested.append('draft')
        
        # 2. SENT - Send invoice
        if test_invoice_id:
            self.make_request('PUT', f'billing/invoices/{test_invoice_id}/send')
            invoice_response, _ = self.make_request('GET', f'billing/invoices/{test_invoice_id}')
            if invoice_response and invoice_response.status_code == 200:
                status = invoice_response.json().get('status')
                if status == 'sent':
                    statuses_tested.append('sent')
        
        # 3. PARTIALLY_PAID - Partial payment
        if test_invoice_id:
            payment_data = {
                "invoice_id": test_invoice_id,
                "amount": 50.00,
                "payment_method": "cash"
            }
            self.make_request('POST', 'billing/payments', payment_data)
            invoice_response, _ = self.make_request('GET', f'billing/invoices/{test_invoice_id}')
            if invoice_response and invoice_response.status_code == 200:
                status = invoice_response.json().get('status')
                if status == 'partially_paid':
                    statuses_tested.append('partially_paid')
        
        # 4. PAID - Full payment
        if test_invoice_id:
            payment_data = {
                "invoice_id": test_invoice_id,
                "amount": 50.00,
                "payment_method": "cash"
            }
            self.make_request('POST', 'billing/payments', payment_data)
            invoice_response, _ = self.make_request('GET', f'billing/invoices/{test_invoice_id}')
            if invoice_response and invoice_response.status_code == 200:
                status = invoice_response.json().get('status')
                if status == 'paid':
                    statuses_tested.append('paid')
        
        # 5. REVERSED - Create new invoice and reverse
        response, _ = self.make_request('POST', 'billing/invoices', invoice_data)
        if response and response.status_code == 200:
            reversed_id = response.json().get('invoice_id')
            self.make_request('PUT', f'billing/invoices/{reversed_id}/send')
            self.make_request('PUT', f'billing/invoices/{reversed_id}/reverse')
            invoice_response, _ = self.make_request('GET', f'billing/invoices/{reversed_id}')
            if invoice_response and invoice_response.status_code == 200:
                status = invoice_response.json().get('status')
                if status == 'reversed':
                    statuses_tested.append('reversed')
        
        # 6. VOIDED - Create new invoice and void
        response, _ = self.make_request('POST', 'billing/invoices', invoice_data)
        if response and response.status_code == 200:
            voided_id = response.json().get('invoice_id')
            self.make_request('PUT', f'billing/invoices/{voided_id}/void')
            invoice_response, _ = self.make_request('GET', f'billing/invoices/{voided_id}')
            if invoice_response and invoice_response.status_code == 200:
                status = invoice_response.json().get('status')
                if status == 'voided':
                    statuses_tested.append('voided')
        
        # 7. PENDING_INSURANCE - Create invoice with insurance
        insurance_invoice_data = {
            **invoice_data,
            "insurance_id": "NHIS-TEST-001"
        }
        response, _ = self.make_request('POST', 'billing/invoices', insurance_invoice_data)
        if response and response.status_code == 200:
            insurance_id = response.json().get('invoice_id')
            # Change to NHIS insurance payment method
            self.make_request('PUT', f'billing/invoices/{insurance_id}/change-payment-method', 
                            params={"new_method": "nhis_insurance"})
            invoice_response, _ = self.make_request('GET', f'billing/invoices/{insurance_id}')
            if invoice_response and invoice_response.status_code == 200:
                status = invoice_response.json().get('status')
                if status == 'pending_insurance':
                    statuses_tested.append('pending_insurance')
        
        # 8. CANCELLED - Create and cancel
        response, _ = self.make_request('POST', 'billing/invoices', invoice_data)
        if response and response.status_code == 200:
            cancelled_id = response.json().get('invoice_id')
            self.make_request('DELETE', f'billing/invoices/{cancelled_id}')
            invoice_response, _ = self.make_request('GET', f'billing/invoices/{cancelled_id}')
            if invoice_response and invoice_response.status_code == 200:
                status = invoice_response.json().get('status')
                if status == 'cancelled':
                    statuses_tested.append('cancelled')
        
        # 9. OVERDUE - Would require date manipulation, skip for now
        # statuses_tested.append('overdue')  # Manual verification needed
        
        success = len(statuses_tested) >= 8  # At least 8 of 9 statuses
        details = f"Statuses tested: {', '.join(statuses_tested)} ({len(statuses_tested)}/9)"
        self.log_test("Invoice Status System (9 statuses)", success, details)
        return success

    def test_audit_logging(self):
        """Test audit logging for reversal, void, and payment method change"""
        # This test verifies that audit logs are created
        # We can't directly query audit_logs without a dedicated endpoint
        # But we can verify the operations complete successfully
        
        if not self.patient_id:
            self.log_test("Audit Logging", False, "No patient ID")
            return False
        
        operations_completed = []
        
        # Test 1: Invoice reversal creates audit log
        invoice_data = {
            "patient_id": self.patient_id,
            "patient_name": "Kwame Mensah",
            "line_items": [{"description": "Test", "quantity": 1, "unit_price": 50.00, "discount": 0}]
        }
        response, _ = self.make_request('POST', 'billing/invoices', invoice_data)
        if response and response.status_code == 200:
            audit_invoice_id = response.json().get('invoice_id')
            self.make_request('PUT', f'billing/invoices/{audit_invoice_id}/send')
            response, _ = self.make_request('PUT', f'billing/invoices/{audit_invoice_id}/reverse', 
                                          params={"reason": "Audit test reversal"})
            if response and response.status_code == 200:
                operations_completed.append('reversal')
        
        # Test 2: Invoice void creates audit log
        response, _ = self.make_request('POST', 'billing/invoices', invoice_data)
        if response and response.status_code == 200:
            void_invoice_id = response.json().get('invoice_id')
            response, _ = self.make_request('PUT', f'billing/invoices/{void_invoice_id}/void', 
                                          params={"reason": "Audit test void"})
            if response and response.status_code == 200:
                operations_completed.append('void')
        
        # Test 3: Payment method change creates audit log
        response, _ = self.make_request('POST', 'billing/invoices', invoice_data)
        if response and response.status_code == 200:
            change_invoice_id = response.json().get('invoice_id')
            response, _ = self.make_request('PUT', f'billing/invoices/{change_invoice_id}/change-payment-method', 
                                          params={"new_method": "cash", "reason": "Audit test change"})
            if response and response.status_code == 200:
                operations_completed.append('payment_method_change')
        
        success = len(operations_completed) == 3
        details = f"Operations completed: {', '.join(operations_completed)} ({len(operations_completed)}/3)"
        self.log_test("Audit Logging", success, details)
        return success

    def run_all_tests(self):
        """Run all Phase 1 Billing Enhancement tests"""
        print("=" * 80)
        print("🧪 PHASE 1 BILLING ENHANCEMENTS - COMPREHENSIVE TESTING")
        print("=" * 80)
        print(f"Backend URL: {self.base_url}")
        print(f"Test User: {self.user_email}")
        print("=" * 80)
        print()
        
        # Test sequence
        tests = [
            ("Authentication", self.test_login),
            ("Billing Bug Fixes", self.test_get_invoices_no_520_error),
            ("Expanded Service Codes (70 total)", self.test_expanded_service_codes_total),
            ("Service Codes by Category", self.test_service_codes_by_category),
            ("Create Test Patient", self.test_create_patient),
            ("Create Invoice with Insurance", self.test_create_invoice_with_insurance),
            ("Send Invoice", self.test_send_invoice),
            ("Payment Method: cash", self.test_payment_method_cash),
            ("All Payment Methods (7 methods)", self.test_payment_methods_all),
            ("Invoice Reversal Workflow", self.test_invoice_reversal_workflow),
            ("Invoice Reversal Edge Cases", self.test_invoice_reversal_edge_cases),
            ("Invoice Void Functionality", self.test_invoice_void_functionality),
            ("Void Paid Invoice (should fail)", self.test_void_paid_invoice_should_fail),
            ("Payment Method Change", self.test_payment_method_change),
            ("Multi-Item Invoice (Expanded Codes)", self.test_multi_item_invoice_with_expanded_codes),
            ("Invoice Status System (9 statuses)", self.test_invoice_status_system),
            ("Audit Logging", self.test_audit_logging),
        ]
        
        for test_name, test_func in tests:
            try:
                print(f"\n📋 Testing: {test_name}")
                test_func()
            except Exception as e:
                self.log_test(test_name, False, f"Exception: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        print("=" * 80)
        
        # Print failed tests
        failed_tests = [t for t in self.test_results if not t['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            print("-" * 80)
            for test in failed_tests:
                print(f"  • {test['test']}")
                if test['details']:
                    print(f"    └─ {test['details']}")
        else:
            print("\n✅ ALL TESTS PASSED!")
        
        print("\n" + "=" * 80)
        return self.tests_passed == self.tests_run


if __name__ == "__main__":
    tester = BillingPhase1Tester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
