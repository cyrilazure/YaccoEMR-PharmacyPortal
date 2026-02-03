#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta

class YaccoEMRTester:
    def __init__(self, base_url="https://github-flow.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_patient_id = None
        self.lab_order_id = None
        self.telehealth_session_id = None
        self.test_results = []
        # Organization module variables
        self.test_org_id = None
        self.super_admin_token = None
        self.super_admin_id = None
        self.hospital_admin_token = None
        self.hospital_admin_id = None
        self.hospital_admin_email = None
        self.hospital_admin_temp_password = None
        self.test_staff_email = None
        self.test_staff_temp_password = None

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

    def test_user_registration(self):
        """Test user registration with physician role"""
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
        if error:
            self.log_test("User Registration", False, error)
            return False
        
        if response.status_code in [200, 201]:
            data = response.json()
            self.token = data.get('token')
            self.user_id = data.get('user', {}).get('id')
            self.log_test("User Registration", True, "User authenticated")
            return True
        elif response.status_code == 400:
            # User already exists, try login
            return self.test_user_login()
        else:
            self.log_test("User Registration", False, f"Status: {response.status_code}")
            return False

    def test_user_login(self):
        """Test user login"""
        login_data = {
            "email": "testdoc@test.com",
            "password": "test123"
        }
        
        response, error = self.make_request('POST', 'auth/login', login_data)
        if error:
            self.log_test("User Login", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get('token')
            self.user_id = data.get('user', {}).get('id')
            self.log_test("User Login", True, f"Token received")
            return True
        else:
            self.log_test("User Login", False, f"Status: {response.status_code}")
            return False

    def test_get_current_user(self):
        """Test getting current user info"""
        response, error = self.make_request('GET', 'auth/me')
        if error:
            self.log_test("Get Current User", False, error)
            return False
        
        success = response.status_code == 200
        self.log_test("Get Current User", success, f"Status: {response.status_code}")
        return success

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        response, error = self.make_request('GET', 'dashboard/stats')
        if error:
            self.log_test("Dashboard Stats", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ['total_patients', 'today_appointments', 'pending_orders', 'recent_notes']
            has_all_fields = all(field in data for field in required_fields)
            self.log_test("Dashboard Stats", has_all_fields, f"Fields: {list(data.keys())}")
            return has_all_fields
        else:
            self.log_test("Dashboard Stats", False, f"Status: {response.status_code}")
            return False

    def test_patient_creation(self):
        """Test patient registration"""
        patient_data = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1980-05-15",
            "gender": "male",
            "email": "john.doe@email.com",
            "phone": "555-0123",
            "address": "123 Main St, City, State 12345",
            "emergency_contact_name": "Jane Doe",
            "emergency_contact_phone": "555-0124",
            "insurance_provider": "Blue Cross",
            "insurance_id": "BC123456789"
        }
        
        response, error = self.make_request('POST', 'patients', patient_data)
        if error:
            self.log_test("Patient Creation", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.test_patient_id = data.get('id')
            self.log_test("Patient Creation", True, f"Patient ID: {self.test_patient_id}")
            return True
        else:
            self.log_test("Patient Creation", False, f"Status: {response.status_code}")
            return False

    def test_patient_list(self):
        """Test patient list retrieval"""
        response, error = self.make_request('GET', 'patients')
        if error:
            self.log_test("Patient List", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.log_test("Patient List", True, f"Found {len(data)} patients")
            return True
        else:
            self.log_test("Patient List", False, f"Status: {response.status_code}")
            return False

    def test_patient_search(self):
        """Test patient search functionality"""
        response, error = self.make_request('GET', 'patients', params={'search': 'John'})
        if error:
            self.log_test("Patient Search", False, error)
            return False
        
        success = response.status_code == 200
        self.log_test("Patient Search", success, f"Status: {response.status_code}")
        return success

    def test_vitals_creation(self):
        """Test adding vitals to patient"""
        if not self.test_patient_id:
            self.log_test("Vitals Creation", False, "No test patient available")
            return False
        
        vitals_data = {
            "patient_id": self.test_patient_id,
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80,
            "heart_rate": 72,
            "respiratory_rate": 16,
            "temperature": 98.6,
            "oxygen_saturation": 98,
            "weight": 70.5,
            "height": 175,
            "notes": "Normal vitals"
        }
        
        response, error = self.make_request('POST', 'vitals', vitals_data)
        if error:
            self.log_test("Vitals Creation", False, error)
            return False
        
        success = response.status_code == 200
        self.log_test("Vitals Creation", success, f"Status: {response.status_code}")
        return success

    def test_problem_creation(self):
        """Test adding problem/diagnosis"""
        if not self.test_patient_id:
            self.log_test("Problem Creation", False, "No test patient available")
            return False
        
        problem_data = {
            "patient_id": self.test_patient_id,
            "description": "Hypertension",
            "icd_code": "I10",
            "onset_date": "2024-01-01",
            "status": "active",
            "notes": "Essential hypertension"
        }
        
        response, error = self.make_request('POST', 'problems', problem_data)
        if error:
            self.log_test("Problem Creation", False, error)
            return False
        
        success = response.status_code == 200
        self.log_test("Problem Creation", success, f"Status: {response.status_code}")
        return success

    def test_medication_creation(self):
        """Test adding medication"""
        if not self.test_patient_id:
            self.log_test("Medication Creation", False, "No test patient available")
            return False
        
        medication_data = {
            "patient_id": self.test_patient_id,
            "name": "Lisinopril",
            "dosage": "10mg",
            "frequency": "once daily",
            "route": "oral",
            "start_date": "2024-01-01",
            "status": "active",
            "notes": "For hypertension"
        }
        
        response, error = self.make_request('POST', 'medications', medication_data)
        if error:
            self.log_test("Medication Creation", False, error)
            return False
        
        success = response.status_code == 200
        self.log_test("Medication Creation", success, f"Status: {response.status_code}")
        return success

    def test_allergy_creation(self):
        """Test adding allergy"""
        if not self.test_patient_id:
            self.log_test("Allergy Creation", False, "No test patient available")
            return False
        
        allergy_data = {
            "patient_id": self.test_patient_id,
            "allergen": "Penicillin",
            "reaction": "Rash",
            "severity": "moderate",
            "notes": "Developed rash after taking penicillin"
        }
        
        response, error = self.make_request('POST', 'allergies', allergy_data)
        if error:
            self.log_test("Allergy Creation", False, error)
            return False
        
        success = response.status_code == 200
        self.log_test("Allergy Creation", success, f"Status: {response.status_code}")
        return success

    def test_clinical_note_creation(self):
        """Test creating clinical note"""
        if not self.test_patient_id:
            self.log_test("Clinical Note Creation", False, "No test patient available")
            return False
        
        note_data = {
            "patient_id": self.test_patient_id,
            "note_type": "progress_note",
            "chief_complaint": "Follow-up for hypertension",
            "subjective": "Patient reports feeling well, no chest pain or shortness of breath",
            "objective": "BP 130/85, HR 70, regular rhythm",
            "assessment": "Hypertension, well controlled",
            "plan": "Continue current medications, follow up in 3 months"
        }
        
        response, error = self.make_request('POST', 'notes', note_data)
        if error:
            self.log_test("Clinical Note Creation", False, error)
            return False
        
        success = response.status_code == 200
        self.log_test("Clinical Note Creation", success, f"Status: {response.status_code}")
        return success

    def test_order_creation(self):
        """Test placing orders"""
        if not self.test_patient_id:
            self.log_test("Order Creation", False, "No test patient available")
            return False
        
        # Test lab order
        lab_order = {
            "patient_id": self.test_patient_id,
            "order_type": "lab",
            "description": "CBC with Differential",
            "priority": "routine",
            "instructions": "Fasting not required",
            "diagnosis": "Routine screening"
        }
        
        response, error = self.make_request('POST', 'orders', lab_order)
        if error:
            self.log_test("Lab Order Creation", False, error)
            return False
        
        success = response.status_code == 200
        self.log_test("Lab Order Creation", success, f"Status: {response.status_code}")
        return success

    def test_appointment_creation(self):
        """Test scheduling appointment"""
        if not self.test_patient_id or not self.user_id:
            self.log_test("Appointment Creation", False, "Missing patient or user ID")
            return False
        
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        appointment_data = {
            "patient_id": self.test_patient_id,
            "provider_id": self.user_id,
            "appointment_type": "follow_up",
            "date": tomorrow,
            "start_time": "10:00",
            "end_time": "10:30",
            "reason": "Hypertension follow-up",
            "notes": "Regular follow-up appointment"
        }
        
        response, error = self.make_request('POST', 'appointments', appointment_data)
        if error:
            self.log_test("Appointment Creation", False, error)
            return False
        
        success = response.status_code == 200
        self.log_test("Appointment Creation", success, f"Status: {response.status_code}")
        return success

    def test_orders_list(self):
        """Test retrieving orders"""
        response, error = self.make_request('GET', 'orders')
        if error:
            self.log_test("Orders List", False, error)
            return False
        
        success = response.status_code == 200
        if success:
            data = response.json()
            self.log_test("Orders List", True, f"Found {len(data)} orders")
        else:
            self.log_test("Orders List", False, f"Status: {response.status_code}")
        return success

    def test_appointments_list(self):
        """Test retrieving appointments"""
        today = datetime.now().strftime("%Y-%m-%d")
        response, error = self.make_request('GET', 'appointments', params={'date': today})
        if error:
            self.log_test("Appointments List", False, error)
            return False
        
        success = response.status_code == 200
        if success:
            data = response.json()
            self.log_test("Appointments List", True, f"Found {len(data)} appointments for today")
        else:
            self.log_test("Appointments List", False, f"Status: {response.status_code}")
        return success

    def test_ai_note_generation(self):
        """Test AI-assisted note generation"""
        if not self.test_patient_id:
            self.log_test("AI Note Generation", False, "No test patient available")
            return False
        
        ai_request = {
            "patient_id": self.test_patient_id,
            "note_type": "progress_note",
            "symptoms": "Patient complains of chest pain and shortness of breath",
            "findings": "BP 140/90, HR 85, clear lungs, no murmurs",
            "context": "45-year-old male with history of hypertension"
        }
        
        response, error = self.make_request('POST', 'ai/generate-note', ai_request)
        if error:
            self.log_test("AI Note Generation", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_note = 'generated_note' in data and len(data['generated_note']) > 0
            self.log_test("AI Note Generation", has_note, f"Generated note length: {len(data.get('generated_note', ''))}")
            return has_note
        else:
            self.log_test("AI Note Generation", False, f"Status: {response.status_code}")
            return False

    # ============ LAB RESULTS MODULE TESTS ============
    
    def test_lab_panels(self):
        """Test getting available lab panels"""
        response, error = self.make_request('GET', 'lab/panels')
        if error:
            self.log_test("Lab Panels", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            panels = data.get('panels', [])
            has_panels = len(panels) > 0
            panel_codes = [p.get('code') for p in panels]
            expected_panels = ['CBC', 'CMP', 'LIPID']
            has_expected = all(code in panel_codes for code in expected_panels)
            success = has_panels and has_expected
            self.log_test("Lab Panels", success, f"Found {len(panels)} panels: {panel_codes}")
            return success
        else:
            self.log_test("Lab Panels", False, f"Status: {response.status_code}")
            return False

    def test_lab_order_creation(self):
        """Test creating lab order"""
        if not self.test_patient_id or not self.user_id:
            self.log_test("Lab Order Creation", False, "Missing patient or user ID")
            return False
        
        lab_order = {
            "patient_id": self.test_patient_id,
            "patient_name": "John Doe",
            "ordering_provider_id": self.user_id,
            "ordering_provider_name": "Test Doctor",
            "panel_code": "CBC",
            "panel_name": "Complete Blood Count",
            "priority": "routine"
        }
        
        response, error = self.make_request('POST', 'lab/orders', lab_order)
        if error:
            self.log_test("Lab Order Creation", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            order = data.get('order', {})
            self.lab_order_id = order.get('id')
            has_order_id = bool(self.lab_order_id)
            has_accession = bool(order.get('accession_number'))
            success = has_order_id and has_accession
            self.log_test("Lab Order Creation", success, f"Order ID: {self.lab_order_id}")
            return success
        else:
            self.log_test("Lab Order Creation", False, f"Status: {response.status_code}")
            return False

    def test_get_patient_lab_orders(self):
        """Test getting patient's lab orders"""
        if not self.test_patient_id:
            self.log_test("Get Patient Lab Orders", False, "No test patient available")
            return False
        
        response, error = self.make_request('GET', f'lab/orders/{self.test_patient_id}')
        if error:
            self.log_test("Get Patient Lab Orders", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            orders = data.get('orders', [])
            has_orders = len(orders) > 0
            self.log_test("Get Patient Lab Orders", has_orders, f"Found {len(orders)} orders")
            return has_orders
        else:
            self.log_test("Get Patient Lab Orders", False, f"Status: {response.status_code}")
            return False

    def test_simulate_lab_results(self):
        """Test simulating lab results"""
        if not hasattr(self, 'lab_order_id') or not self.lab_order_id:
            self.log_test("Simulate Lab Results", False, "No lab order available")
            return False
        
        response, error = self.make_request('POST', f'lab/results/simulate/{self.lab_order_id}?scenario=mixed')
        if error:
            self.log_test("Simulate Lab Results", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('result', {})
            results = result.get('results', [])
            has_results = len(results) > 0
            has_values = all(r.get('value') is not None for r in results)
            success = has_results and has_values
            self.log_test("Simulate Lab Results", success, f"Generated {len(results)} test results")
            return success
        else:
            self.log_test("Simulate Lab Results", False, f"Status: {response.status_code}")
            return False

    def test_get_patient_lab_results(self):
        """Test getting patient's lab results"""
        if not self.test_patient_id:
            self.log_test("Get Patient Lab Results", False, "No test patient available")
            return False
        
        response, error = self.make_request('GET', f'lab/results/{self.test_patient_id}')
        if error:
            self.log_test("Get Patient Lab Results", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            has_results = len(results) > 0
            if has_results:
                # Check structure of first result
                first_result = results[0]
                has_structure = all(key in first_result for key in ['patient_id', 'panel_code', 'results'])
                success = has_structure
                self.log_test("Get Patient Lab Results", success, f"Found {len(results)} lab results")
            else:
                self.log_test("Get Patient Lab Results", True, "No results found (expected after simulation)")
                success = True
            return success
        else:
            self.log_test("Get Patient Lab Results", False, f"Status: {response.status_code}")
            return False

    def test_hl7_oru_parsing(self):
        """Test HL7 ORU message parsing"""
        hl7_message = {
            "raw_message": "MSH|^~\\&|LAB_SYS|LAB|EMR|HOSP|20240115120000||ORU^R01|MSG001|P|2.5.1\nPID|1||test-patient-1^^^HOSP^MR||DOE^JOHN^A||19800101|M\nOBR|1|ORD001|ACC001|CBC^Complete Blood Count|||20240115100000\nOBX|1|NM|WBC^White Blood Cell Count||7.5|K/uL|4.5-11.0|N|||F\nOBX|2|NM|RBC^Red Blood Cell Count||5.2|M/uL|4.5-5.5|N|||F\nOBX|3|NM|HGB^Hemoglobin||14.5|g/dL|12.0-17.5|N|||F"
        }
        
        response, error = self.make_request('POST', 'lab/hl7/oru', hl7_message)
        if error:
            self.log_test("HL7 ORU Parsing", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_result_id = bool(data.get('result_id'))
            tests_received = data.get('tests_received', 0)
            has_ack = bool(data.get('ack'))
            success = has_result_id and tests_received > 0 and has_ack
            self.log_test("HL7 ORU Parsing", success, f"Parsed {tests_received} tests, ACK: {bool(has_ack)}")
            return success
        else:
            self.log_test("HL7 ORU Parsing", False, f"Status: {response.status_code}")
            return False

    # ============ TELEHEALTH MODULE TESTS ============
    
    def test_telehealth_config(self):
        """Test telehealth configuration"""
        response, error = self.make_request('GET', 'telehealth/config')
        if error:
            self.log_test("Telehealth Config", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ['webrtc_enabled', 'dyte_enabled', 'features', 'ice_servers']
            has_all_fields = all(field in data for field in required_fields)
            webrtc_enabled = data.get('webrtc_enabled', False)
            has_ice_servers = len(data.get('ice_servers', [])) > 0
            success = has_all_fields and webrtc_enabled and has_ice_servers
            self.log_test("Telehealth Config", success, f"WebRTC: {webrtc_enabled}, ICE servers: {len(data.get('ice_servers', []))}")
            return success
        else:
            self.log_test("Telehealth Config", False, f"Status: {response.status_code}")
            return False

    def test_telehealth_session_creation(self):
        """Test creating telehealth session"""
        if not self.test_patient_id or not self.user_id:
            self.log_test("Telehealth Session Creation", False, "Missing patient or user ID")
            return False
        
        # Schedule for future date
        future_time = (datetime.now() + timedelta(hours=1)).isoformat()
        
        session_data = {
            "patient_id": self.test_patient_id,
            "patient_name": "John Doe",
            "provider_id": self.user_id,
            "provider_name": "Test Doctor",
            "scheduled_time": future_time,
            "session_type": "video",
            "reason": "Follow-up consultation",
            "duration_minutes": 30
        }
        
        response, error = self.make_request('POST', 'telehealth/sessions', session_data)
        if error:
            self.log_test("Telehealth Session Creation", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            session = data.get('session', {})
            self.telehealth_session_id = session.get('id')
            has_session_id = bool(self.telehealth_session_id)
            has_room_id = bool(session.get('room_id'))
            has_join_url = bool(data.get('join_url'))
            success = has_session_id and has_room_id and has_join_url
            self.log_test("Telehealth Session Creation", success, f"Session ID: {self.telehealth_session_id}")
            return success
        else:
            self.log_test("Telehealth Session Creation", False, f"Status: {response.status_code}")
            return False

    def test_get_telehealth_session(self):
        """Test getting telehealth session details"""
        if not hasattr(self, 'telehealth_session_id') or not self.telehealth_session_id:
            self.log_test("Get Telehealth Session", False, "No telehealth session available")
            return False
        
        response, error = self.make_request('GET', f'telehealth/sessions/{self.telehealth_session_id}')
        if error:
            self.log_test("Get Telehealth Session", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            session = data.get('session', {})
            has_session = bool(session.get('id'))
            has_room_id = bool(data.get('room_id'))
            participants = data.get('participants', [])
            success = has_session and has_room_id
            self.log_test("Get Telehealth Session", success, f"Session found, {len(participants)} participants")
            return success
        else:
            self.log_test("Get Telehealth Session", False, f"Status: {response.status_code}")
            return False

    def test_join_telehealth_session(self):
        """Test joining telehealth session"""
        if not hasattr(self, 'telehealth_session_id') or not self.telehealth_session_id or not self.user_id:
            self.log_test("Join Telehealth Session", False, "Missing session or user ID")
            return False
        
        join_data = {
            "user_id": self.user_id,
            "user_name": "Test Doctor",
            "role": "provider"
        }
        
        response, error = self.make_request('POST', f'telehealth/sessions/{self.telehealth_session_id}/join', join_data)
        if error:
            self.log_test("Join Telehealth Session", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_room_id = bool(data.get('room_id'))
            has_participant_id = bool(data.get('participant_id'))
            has_ice_servers = len(data.get('ice_servers', [])) > 0
            success = has_room_id and has_participant_id and has_ice_servers
            self.log_test("Join Telehealth Session", success, f"Joined successfully, ICE servers: {len(data.get('ice_servers', []))}")
            return success
        else:
            self.log_test("Join Telehealth Session", False, f"Status: {response.status_code}")
            return False

    def test_start_telehealth_session(self):
        """Test starting telehealth session"""
        if not hasattr(self, 'telehealth_session_id') or not self.telehealth_session_id:
            self.log_test("Start Telehealth Session", False, "No telehealth session available")
            return False
        
        response, error = self.make_request('POST', f'telehealth/sessions/{self.telehealth_session_id}/start')
        if error:
            self.log_test("Start Telehealth Session", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            success = status == 'in_progress'
            self.log_test("Start Telehealth Session", success, f"Status: {status}")
            return success
        else:
            self.log_test("Start Telehealth Session", False, f"Status: {response.status_code}")
            return False

    def test_get_upcoming_telehealth_sessions(self):
        """Test getting upcoming telehealth sessions"""
        response, error = self.make_request('GET', 'telehealth/upcoming')
        if error:
            self.log_test("Get Upcoming Telehealth Sessions", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            sessions = data.get('sessions', [])
            # Success if we get a response (may be empty)
            self.log_test("Get Upcoming Telehealth Sessions", True, f"Found {len(sessions)} upcoming sessions")
            return True
        else:
            self.log_test("Get Upcoming Telehealth Sessions", False, f"Status: {response.status_code}")
            return False

    def test_dyte_integration_status(self):
        """Test Dyte integration status"""
        response, error = self.make_request('GET', 'telehealth/dyte/status')
        if error:
            self.log_test("Dyte Integration Status", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_status = 'dyte_enabled' in data
            has_features = 'features_available' in data
            success = has_status and has_features
            dyte_enabled = data.get('dyte_enabled', False)
            self.log_test("Dyte Integration Status", success, f"Dyte enabled: {dyte_enabled}")
            return success
        else:
            self.log_test("Dyte Integration Status", False, f"Status: {response.status_code}")
            return False

    # ============ FHIR R4 API TESTS ============
    
    def test_fhir_capability_statement(self):
        """Test FHIR metadata endpoint"""
        response, error = self.make_request('GET', 'fhir/metadata')
        if error:
            self.log_test("FHIR Capability Statement", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ['resourceType', 'status', 'fhirVersion', 'rest']
            has_all_fields = all(field in data for field in required_fields)
            is_capability = data.get('resourceType') == 'CapabilityStatement'
            success = has_all_fields and is_capability
            self.log_test("FHIR Capability Statement", success, f"ResourceType: {data.get('resourceType')}")
            return success
        else:
            self.log_test("FHIR Capability Statement", False, f"Status: {response.status_code}")
            return False

    def test_fhir_patient_bundle(self):
        """Test FHIR Patient search endpoint"""
        response, error = self.make_request('GET', 'fhir/Patient')
        if error:
            self.log_test("FHIR Patient Bundle", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            is_bundle = data.get('resourceType') == 'Bundle'
            has_entries = 'entry' in data and 'total' in data
            success = is_bundle and has_entries
            entry_count = len(data.get('entry', []))
            self.log_test("FHIR Patient Bundle", success, f"Bundle with {entry_count} patients")
            return success
        else:
            self.log_test("FHIR Patient Bundle", False, f"Status: {response.status_code}")
            return False

    def test_fhir_observation_bundle(self):
        """Test FHIR Observation search endpoint (vitals)"""
        response, error = self.make_request('GET', 'fhir/Observation')
        if error:
            self.log_test("FHIR Observation Bundle", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            is_bundle = data.get('resourceType') == 'Bundle'
            has_entries = 'entry' in data and 'total' in data
            success = is_bundle and has_entries
            entry_count = len(data.get('entry', []))
            self.log_test("FHIR Observation Bundle", success, f"Bundle with {entry_count} observations")
            return success
        else:
            self.log_test("FHIR Observation Bundle", False, f"Status: {response.status_code}")
            return False

    def test_fhir_condition_bundle(self):
        """Test FHIR Condition search endpoint (problems)"""
        response, error = self.make_request('GET', 'fhir/Condition')
        if error:
            self.log_test("FHIR Condition Bundle", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            is_bundle = data.get('resourceType') == 'Bundle'
            has_entries = 'entry' in data and 'total' in data
            success = is_bundle and has_entries
            entry_count = len(data.get('entry', []))
            self.log_test("FHIR Condition Bundle", success, f"Bundle with {entry_count} conditions")
            return success
        else:
            self.log_test("FHIR Condition Bundle", False, f"Status: {response.status_code}")
            return False

    def test_fhir_medication_request_bundle(self):
        """Test FHIR MedicationRequest search endpoint"""
        response, error = self.make_request('GET', 'fhir/MedicationRequest')
        if error:
            self.log_test("FHIR MedicationRequest Bundle", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            is_bundle = data.get('resourceType') == 'Bundle'
            has_entries = 'entry' in data and 'total' in data
            success = is_bundle and has_entries
            entry_count = len(data.get('entry', []))
            self.log_test("FHIR MedicationRequest Bundle", success, f"Bundle with {entry_count} medications")
            return success
        else:
            self.log_test("FHIR MedicationRequest Bundle", False, f"Status: {response.status_code}")
            return False

    def test_fhir_allergy_intolerance_bundle(self):
        """Test FHIR AllergyIntolerance search endpoint"""
        response, error = self.make_request('GET', 'fhir/AllergyIntolerance')
        if error:
            self.log_test("FHIR AllergyIntolerance Bundle", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            is_bundle = data.get('resourceType') == 'Bundle'
            has_entries = 'entry' in data and 'total' in data
            success = is_bundle and has_entries
            entry_count = len(data.get('entry', []))
            self.log_test("FHIR AllergyIntolerance Bundle", success, f"Bundle with {entry_count} allergies")
            return success
        else:
            self.log_test("FHIR AllergyIntolerance Bundle", False, f"Status: {response.status_code}")
            return False

    def test_fhir_service_request_bundle(self):
        """Test FHIR ServiceRequest search endpoint (orders)"""
        response, error = self.make_request('GET', 'fhir/ServiceRequest')
        if error:
            self.log_test("FHIR ServiceRequest Bundle", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            is_bundle = data.get('resourceType') == 'Bundle'
            has_entries = 'entry' in data and 'total' in data
            success = is_bundle and has_entries
            entry_count = len(data.get('entry', []))
            self.log_test("FHIR ServiceRequest Bundle", success, f"Bundle with {entry_count} service requests")
            return success
        else:
            self.log_test("FHIR ServiceRequest Bundle", False, f"Status: {response.status_code}")
            return False

    def test_fhir_appointment_bundle(self):
        """Test FHIR Appointment search endpoint"""
        response, error = self.make_request('GET', 'fhir/Appointment')
        if error:
            self.log_test("FHIR Appointment Bundle", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            is_bundle = data.get('resourceType') == 'Bundle'
            has_entries = 'entry' in data and 'total' in data
            success = is_bundle and has_entries
            entry_count = len(data.get('entry', []))
            self.log_test("FHIR Appointment Bundle", success, f"Bundle with {entry_count} appointments")
            return success
        else:
            self.log_test("FHIR Appointment Bundle", False, f"Status: {response.status_code}")
            return False

    def test_fhir_patient_by_id(self):
        """Test FHIR Patient by ID endpoint"""
        if not self.test_patient_id:
            self.log_test("FHIR Patient by ID", False, "No test patient available")
            return False
        
        response, error = self.make_request('GET', f'fhir/Patient/{self.test_patient_id}')
        if error:
            self.log_test("FHIR Patient by ID", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            is_patient = data.get('resourceType') == 'Patient'
            has_id = data.get('id') == self.test_patient_id
            success = is_patient and has_id
            self.log_test("FHIR Patient by ID", success, f"Patient resource: {data.get('resourceType')}")
            return success
        else:
            self.log_test("FHIR Patient by ID", False, f"Status: {response.status_code}")
            return False

    # ============ ORGANIZATION MODULE TESTS ============
    
    def test_organization_self_registration(self):
        """Test self-service hospital registration"""
        import time
        timestamp = str(int(time.time()))
        
        org_data = {
            "name": f"Test General Hospital {timestamp}",
            "organization_type": "hospital",
            "address_line1": "123 Medical Drive",
            "city": "Test City",
            "state": "CA",
            "zip_code": "90210",
            "country": "USA",
            "phone": "555-123-4567",
            "email": f"admin{timestamp}@testgeneral.com",
            "license_number": f"LIC-{timestamp}",
            "admin_first_name": "John",
            "admin_last_name": "Admin",
            "admin_email": f"john{timestamp}@testgeneral.com",
            "admin_phone": "555-111-2222"
        }
        
        response, error = self.make_request('POST', 'organizations/register', org_data)
        if error:
            self.log_test("Organization Self Registration", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_org_id = bool(data.get('organization_id'))
            status_pending = data.get('status') == 'pending'
            success = has_org_id and status_pending
            if success:
                self.test_org_id = data.get('organization_id')
            self.log_test("Organization Self Registration", success, f"Status: {data.get('status')}")
            return success
        else:
            self.log_test("Organization Self Registration", False, f"Status: {response.status_code}")
            return False

    def test_super_admin_registration(self):
        """Test creating super admin user"""
        super_admin_data = {
            "email": "superadmin@yacco.com",
            "password": "SuperAdmin123!",
            "first_name": "Super",
            "last_name": "Admin",
            "role": "super_admin"
        }
        
        response, error = self.make_request('POST', 'auth/register', super_admin_data)
        if error:
            self.log_test("Super Admin Registration", False, error)
            return False
        
        if response.status_code in [200, 201]:
            data = response.json()
            self.super_admin_token = data.get('token')
            self.super_admin_id = data.get('user', {}).get('id')
            success = bool(self.super_admin_token)
            self.log_test("Super Admin Registration", success, "Super admin created")
            return success
        elif response.status_code == 400:
            # User already exists, try login
            return self.test_super_admin_login()
        else:
            self.log_test("Super Admin Registration", False, f"Status: {response.status_code}")
            return False

    def test_super_admin_login(self):
        """Test super admin login"""
        login_data = {
            "email": "superadmin@yacco.com",
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

    def test_super_admin_list_organizations(self):
        """Test super admin listing organizations"""
        if not hasattr(self, 'super_admin_token') or not self.super_admin_token:
            self.log_test("Super Admin List Organizations", False, "No super admin token")
            return False
        
        # Temporarily switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', 'organizations/')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Super Admin List Organizations", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_orgs = 'organizations' in data
            has_counts = 'pending_count' in data and 'active_count' in data
            success = has_orgs and has_counts
            org_count = len(data.get('organizations', []))
            self.log_test("Super Admin List Organizations", success, f"Found {org_count} organizations")
            return success
        else:
            self.log_test("Super Admin List Organizations", False, f"Status: {response.status_code}")
            return False

    def test_super_admin_get_pending_organizations(self):
        """Test super admin getting pending organizations"""
        if not hasattr(self, 'super_admin_token') or not self.super_admin_token:
            self.log_test("Super Admin Get Pending Organizations", False, "No super admin token")
            return False
        
        # Temporarily switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', 'organizations/pending')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Super Admin Get Pending Organizations", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_orgs = 'organizations' in data
            has_count = 'count' in data
            success = has_orgs and has_count
            pending_count = data.get('count', 0)
            self.log_test("Super Admin Get Pending Organizations", success, f"Found {pending_count} pending organizations")
            return success
        else:
            self.log_test("Super Admin Get Pending Organizations", False, f"Status: {response.status_code}")
            return False

    def test_super_admin_approve_organization(self):
        """Test super admin approving organization"""
        if not hasattr(self, 'super_admin_token') or not self.super_admin_token:
            self.log_test("Super Admin Approve Organization", False, "No super admin token")
            return False
        
        if not hasattr(self, 'test_org_id') or not self.test_org_id:
            self.log_test("Super Admin Approve Organization", False, "No test organization available")
            return False
        
        # Temporarily switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        approval_data = {
            "subscription_plan": "standard",
            "max_users": 50,
            "max_patients": 10000,
            "notes": "Test approval"
        }
        
        response, error = self.make_request('POST', f'organizations/{self.test_org_id}/approve', approval_data)
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Super Admin Approve Organization", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_admin_email = bool(data.get('admin_email'))
            has_temp_password = bool(data.get('temp_password'))
            success = has_admin_email and has_temp_password
            if success:
                self.hospital_admin_email = data.get('admin_email')
                self.hospital_admin_temp_password = data.get('temp_password')
            self.log_test("Super Admin Approve Organization", success, f"Admin email: {data.get('admin_email')}")
            return success
        else:
            self.log_test("Super Admin Approve Organization", False, f"Status: {response.status_code}")
            return False

    def test_super_admin_create_organization_directly(self):
        """Test super admin creating organization directly"""
        if not hasattr(self, 'super_admin_token') or not self.super_admin_token:
            self.log_test("Super Admin Create Organization Directly", False, "No super admin token")
            return False
        
        # Temporarily switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        import time
        timestamp = str(int(time.time()))
        
        org_data = {
            "name": f"Direct Created Hospital {timestamp}",
            "organization_type": "hospital",
            "address_line1": "456 Healthcare Blvd",
            "city": "Medical City",
            "state": "TX",
            "zip_code": "75001",
            "country": "USA",
            "phone": "555-987-6543",
            "email": f"admin{timestamp}@directhospital.com",
            "license_number": f"LIC-{timestamp}",
            "admin_first_name": "Direct",
            "admin_last_name": "Admin",
            "admin_email": f"direct{timestamp}@directhospital.com",
            "admin_phone": "555-999-8888"
        }
        
        response, error = self.make_request('POST', 'organizations/create-by-admin?auto_approve=true', org_data)
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Super Admin Create Organization Directly", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            auto_approved = data.get('auto_approved', False)
            has_admin_creds = bool(data.get('admin_email')) and bool(data.get('temp_password'))
            success = auto_approved and has_admin_creds
            self.log_test("Super Admin Create Organization Directly", success, f"Auto-approved: {auto_approved}")
            return success
        else:
            self.log_test("Super Admin Create Organization Directly", False, f"Status: {response.status_code}")
            return False

    def test_super_admin_platform_stats(self):
        """Test super admin platform statistics"""
        if not hasattr(self, 'super_admin_token') or not self.super_admin_token:
            self.log_test("Super Admin Platform Stats", False, "No super admin token")
            return False
        
        # Temporarily switch to super admin token
        original_token = self.token
        self.token = self.super_admin_token
        
        response, error = self.make_request('GET', 'organizations/stats/platform')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Super Admin Platform Stats", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ['total_organizations', 'active_organizations', 'pending_organizations', 'total_users', 'total_patients']
            has_all_fields = all(field in data for field in required_fields)
            self.log_test("Super Admin Platform Stats", has_all_fields, f"Stats: {data}")
            return has_all_fields
        else:
            self.log_test("Super Admin Platform Stats", False, f"Status: {response.status_code}")
            return False

    def test_hospital_admin_login(self):
        """Test hospital admin login with temp password"""
        if not hasattr(self, 'hospital_admin_email') or not hasattr(self, 'hospital_admin_temp_password'):
            self.log_test("Hospital Admin Login", False, "No hospital admin credentials available")
            return False
        
        login_data = {
            "email": self.hospital_admin_email,
            "password": self.hospital_admin_temp_password
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

    def test_hospital_admin_get_my_organization(self):
        """Test hospital admin getting their organization"""
        if not hasattr(self, 'hospital_admin_token') or not self.hospital_admin_token:
            self.log_test("Hospital Admin Get My Organization", False, "No hospital admin token")
            return False
        
        # Temporarily switch to hospital admin token
        original_token = self.token
        self.token = self.hospital_admin_token
        
        response, error = self.make_request('GET', 'organizations/my-organization')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Hospital Admin Get My Organization", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_org = 'organization' in data
            org = data.get('organization', {})
            has_org_details = bool(org.get('name')) and bool(org.get('id'))
            success = has_org and has_org_details
            self.log_test("Hospital Admin Get My Organization", success, f"Org: {org.get('name')}")
            return success
        else:
            self.log_test("Hospital Admin Get My Organization", False, f"Status: {response.status_code}")
            return False

    def test_hospital_admin_create_staff(self):
        """Test hospital admin creating staff account"""
        if not hasattr(self, 'hospital_admin_token') or not self.hospital_admin_token:
            self.log_test("Hospital Admin Create Staff", False, "No hospital admin token")
            return False
        
        # Temporarily switch to hospital admin token
        original_token = self.token
        self.token = self.hospital_admin_token
        
        import time
        timestamp = str(int(time.time()))
        
        staff_data = {
            "email": f"doctor{timestamp}@testgeneral.com",
            "first_name": "Jane",
            "last_name": "Doctor",
            "role": "physician",
            "department": "Internal Medicine"
        }
        
        response, error = self.make_request('POST', 'organizations/staff/create', staff_data)
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Hospital Admin Create Staff", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_user_id = bool(data.get('user_id'))
            has_temp_password = bool(data.get('temp_password'))
            success = has_user_id and has_temp_password
            if success:
                self.test_staff_email = data.get('email')
                self.test_staff_temp_password = data.get('temp_password')
            self.log_test("Hospital Admin Create Staff", success, f"Staff ID: {data.get('user_id')}")
            return success
        else:
            self.log_test("Hospital Admin Create Staff", False, f"Status: {response.status_code}")
            return False

    def test_hospital_admin_list_staff(self):
        """Test hospital admin listing staff"""
        if not hasattr(self, 'hospital_admin_token') or not self.hospital_admin_token:
            self.log_test("Hospital Admin List Staff", False, "No hospital admin token")
            return False
        
        # Temporarily switch to hospital admin token
        original_token = self.token
        self.token = self.hospital_admin_token
        
        response, error = self.make_request('GET', 'organizations/staff')
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Hospital Admin List Staff", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_staff = 'staff' in data
            has_count = 'count' in data
            success = has_staff and has_count
            staff_count = data.get('count', 0)
            self.log_test("Hospital Admin List Staff", success, f"Found {staff_count} staff members")
            return success
        else:
            self.log_test("Hospital Admin List Staff", False, f"Status: {response.status_code}")
            return False

    def test_hospital_admin_invite_staff(self):
        """Test hospital admin inviting staff"""
        if not hasattr(self, 'hospital_admin_token') or not self.hospital_admin_token:
            self.log_test("Hospital Admin Invite Staff", False, "No hospital admin token")
            return False
        
        # Temporarily switch to hospital admin token
        original_token = self.token
        self.token = self.hospital_admin_token
        
        import time
        timestamp = str(int(time.time()))
        
        staff_data = {
            "email": f"nurse{timestamp}@testgeneral.com",
            "first_name": "Mary",
            "last_name": "Nurse",
            "role": "nurse",
            "department": "Emergency"
        }
        
        response, error = self.make_request('POST', 'organizations/staff/invite', staff_data)
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Hospital Admin Invite Staff", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            has_invitation_id = bool(data.get('invitation_id'))
            has_invitation_token = bool(data.get('invitation_token'))
            has_link = bool(data.get('invitation_link'))
            success = has_invitation_id and has_invitation_token and has_link
            self.log_test("Hospital Admin Invite Staff", success, f"Invitation ID: {data.get('invitation_id')}")
            return success
        else:
            self.log_test("Hospital Admin Invite Staff", False, f"Status: {response.status_code}")
            return False

    def test_data_isolation_verification(self):
        """Test data isolation between organizations"""
        # This test verifies that users from different organizations cannot see each other's data
        
        # First, create a patient with hospital admin
        if not hasattr(self, 'hospital_admin_token') or not self.hospital_admin_token:
            self.log_test("Data Isolation Verification", False, "No hospital admin token")
            return False
        
        # Switch to hospital admin token and create patient
        original_token = self.token
        self.token = self.hospital_admin_token
        
        patient_data = {
            "first_name": "Hospital",
            "last_name": "Patient",
            "date_of_birth": "1990-01-01",
            "gender": "male",
            "email": "hospital.patient@test.com"
        }
        
        response, error = self.make_request('POST', 'patients', patient_data)
        if error or response.status_code != 200:
            self.token = original_token
            self.log_test("Data Isolation Verification", False, "Failed to create hospital patient")
            return False
        
        hospital_patient_id = response.json().get('id')
        
        # Switch back to regular user (different org) and try to access hospital patient
        self.token = original_token
        
        response, error = self.make_request('GET', f'patients/{hospital_patient_id}')
        
        # Should get 404 or 403 since patient belongs to different org
        isolation_working = response.status_code in [403, 404]
        
        self.log_test("Data Isolation Verification", isolation_working, 
                     f"Cross-org access blocked: {response.status_code}")
        return isolation_working

    def run_all_tests(self):
        """Run comprehensive backend API tests"""
        print("🏥 Starting Yacco EMR Backend API Tests")
        print("=" * 50)
        
        # Core authentication tests
        if not self.test_health_check():
            return False
        
        if not self.test_user_registration():
            return False
        
        if not self.test_get_current_user():
            return False
        
        # Dashboard functionality
        self.test_dashboard_stats()
        
        # Patient management tests
        self.test_patient_creation()
        self.test_patient_list()
        self.test_patient_search()
        
        # Clinical data tests
        self.test_vitals_creation()
        self.test_problem_creation()
        self.test_medication_creation()
        self.test_allergy_creation()
        self.test_clinical_note_creation()
        
        # Orders and appointments
        self.test_order_creation()
        self.test_appointment_creation()
        self.test_orders_list()
        self.test_appointments_list()
        
        # AI functionality
        self.test_ai_note_generation()
        
        # ============ LAB RESULTS MODULE TESTS ============
        print("\n🧪 Testing Lab Results Module")
        print("-" * 30)
        self.test_lab_panels()
        self.test_lab_order_creation()
        self.test_get_patient_lab_orders()
        self.test_simulate_lab_results()
        self.test_get_patient_lab_results()
        self.test_hl7_oru_parsing()
        
        # ============ TELEHEALTH MODULE TESTS ============
        print("\n📹 Testing Telehealth Video Module")
        print("-" * 30)
        self.test_telehealth_config()
        self.test_telehealth_session_creation()
        self.test_get_telehealth_session()
        self.test_join_telehealth_session()
        self.test_start_telehealth_session()
        self.test_get_upcoming_telehealth_sessions()
        self.test_dyte_integration_status()
        
        # FHIR R4 API Tests
        print("\n🔗 Testing FHIR R4 Interoperability APIs")
        print("-" * 30)
        self.test_fhir_capability_statement()
        self.test_fhir_patient_bundle()
        self.test_fhir_observation_bundle()
        self.test_fhir_condition_bundle()
        self.test_fhir_medication_request_bundle()
        self.test_fhir_allergy_intolerance_bundle()
        self.test_fhir_service_request_bundle()
        self.test_fhir_appointment_bundle()
        self.test_fhir_patient_by_id()
        
        # ============ ORGANIZATION MODULE TESTS ============
        print("\n🏥 Testing Multi-Tenant Organization Module")
        print("-" * 30)
        self.test_organization_self_registration()
        self.test_super_admin_registration()
        self.test_super_admin_list_organizations()
        self.test_super_admin_get_pending_organizations()
        self.test_super_admin_approve_organization()
        self.test_super_admin_create_organization_directly()
        self.test_super_admin_platform_stats()
        self.test_hospital_admin_login()
        self.test_hospital_admin_get_my_organization()
        self.test_hospital_admin_create_staff()
        self.test_hospital_admin_list_staff()
        self.test_hospital_admin_invite_staff()
        self.test_data_isolation_verification()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        return self.tests_passed == self.tests_run

def main():
    tester = YaccoEMRTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())