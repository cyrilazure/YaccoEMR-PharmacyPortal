#!/usr/bin/env python3
"""
Comprehensive Test Suite for Bed Management Module
Tests ward management, bed management, admissions, transfers, and discharge workflows
"""

import requests
import sys
import json
from datetime import datetime

class BedManagementTester:
    def __init__(self, base_url="https://careflow-183.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test data storage
        self.bed_manager_token = None
        self.bed_manager_id = None
        self.ward_ids = []
        self.room_ids = []
        self.bed_ids = []
        self.patient_id = "688a22b7-e785-4aeb-93aa-87ce5a5c3635"  # Existing patient Ghana
        self.admission_id = None
        self.transfer_bed_id = None

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

    # ============== Authentication Tests ==============
    
    def test_bed_manager_login(self):
        """Test Bed Manager Login"""
        login_data = {
            "email": "bed_manager@yacco.health",
            "password": "test123"
        }
        
        response, error = self.make_request('POST', 'auth/login', login_data)
        if error:
            self.log_test("Bed Manager Login", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.bed_manager_token = data.get('token')
            user = data.get('user', {})
            self.bed_manager_id = user.get('id')
            
            is_bed_manager = user.get('role') == 'bed_manager'
            has_token = bool(self.bed_manager_token)
            
            success = is_bed_manager and has_token
            details = f"Email: {user.get('email')}, Role: {user.get('role')}"
            self.log_test("Bed Manager Login", success, details)
            
            # Set token for subsequent requests
            self.token = self.bed_manager_token
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Bed Manager Login", False, error_msg)
            return False

    # ============== Ward Management Tests ==============
    
    def test_get_wards_empty(self):
        """Test GET /api/beds/wards - Should be empty initially"""
        if not self.token:
            self.log_test("Get Wards (Empty)", False, "No token")
            return False
        
        response, error = self.make_request('GET', 'beds/wards')
        if error:
            self.log_test("Get Wards (Empty)", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            wards = data.get('wards', [])
            total = data.get('total', 0)
            
            # Store initial count (may not be empty if already seeded)
            success = isinstance(wards, list) and 'total' in data
            details = f"Initial wards count: {total}"
            self.log_test("Get Wards (Initial Check)", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Get Wards (Empty)", False, error_msg)
            return False

    def test_seed_default_wards(self):
        """Test POST /api/beds/wards/seed-defaults - Seed 14 default wards"""
        if not self.token:
            self.log_test("Seed Default Wards", False, "No token")
            return False
        
        response, error = self.make_request('POST', 'beds/wards/seed-defaults')
        if error:
            self.log_test("Seed Default Wards", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            message = data.get('message', '')
            count = data.get('count', 0)
            skipped = data.get('skipped', False)
            
            # Success if either created or already exists
            success = ('created' in message.lower() or 'already' in message.lower())
            details = f"Message: {message}, Count: {count}, Skipped: {skipped}"
            self.log_test("Seed Default Wards", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Seed Default Wards", False, error_msg)
            return False

    def test_get_wards_after_seeding(self):
        """Test GET /api/beds/wards - Should have 14 wards after seeding"""
        if not self.token:
            self.log_test("Get Wards (After Seeding)", False, "No token")
            return False
        
        response, error = self.make_request('GET', 'beds/wards')
        if error:
            self.log_test("Get Wards (After Seeding)", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            wards = data.get('wards', [])
            total = data.get('total', 0)
            
            # Should have 14 default wards
            has_wards = total >= 14
            is_list = isinstance(wards, list)
            
            # Store ward IDs for later tests
            if wards:
                self.ward_ids = [w.get('id') for w in wards if w.get('id')]
            
            success = has_wards and is_list
            details = f"Total wards: {total}, Ward IDs stored: {len(self.ward_ids)}"
            self.log_test("Get Wards (After Seeding)", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Get Wards (After Seeding)", False, error_msg)
            return False

    def test_filter_wards_by_type(self):
        """Test GET /api/beds/wards?ward_type=icu - Filter by ward type"""
        if not self.token:
            self.log_test("Filter Wards by Type", False, "No token")
            return False
        
        response, error = self.make_request('GET', 'beds/wards', params={"ward_type": "icu"})
        if error:
            self.log_test("Filter Wards by Type", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            wards = data.get('wards', [])
            
            # Check if all returned wards are ICU type
            all_icu = all(w.get('ward_type') == 'icu' for w in wards)
            
            success = all_icu
            details = f"ICU wards found: {len(wards)}, All ICU: {all_icu}"
            self.log_test("Filter Wards by Type", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Filter Wards by Type", False, error_msg)
            return False

    def test_seed_wards_idempotency(self):
        """Test POST /api/beds/wards/seed-defaults - Should skip if already exists"""
        if not self.token:
            self.log_test("Seed Wards Idempotency", False, "No token")
            return False
        
        response, error = self.make_request('POST', 'beds/wards/seed-defaults')
        if error:
            self.log_test("Seed Wards Idempotency", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            message = data.get('message', '')
            skipped = data.get('skipped', False)
            
            # Should skip since wards already exist
            success = skipped or 'already' in message.lower()
            details = f"Message: {message}, Skipped: {skipped}"
            self.log_test("Seed Wards Idempotency", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Seed Wards Idempotency", False, error_msg)
            return False

    # ============== Bed Management Tests ==============
    
    def test_bulk_create_beds(self):
        """Test POST /api/beds/beds/bulk-create - Create rooms and beds for a ward"""
        if not self.token or not self.ward_ids:
            self.log_test("Bulk Create Beds", False, "No token or ward IDs")
            return False
        
        # Use first ward for bulk creation
        ward_id = self.ward_ids[0]
        
        response, error = self.make_request('POST', 'beds/beds/bulk-create', params={
            "ward_id": ward_id,
            "room_prefix": "R",
            "beds_per_room": 4,
            "num_rooms": 5
        })
        if error:
            self.log_test("Bulk Create Beds", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            rooms_created = data.get('rooms_created', 0)
            beds_created = data.get('beds_created', 0)
            
            # Should create 5 rooms with 20 beds (4 per room)
            success = rooms_created == 5 and beds_created == 20
            details = f"Rooms: {rooms_created}, Beds: {beds_created}"
            self.log_test("Bulk Create Beds", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Bulk Create Beds", False, error_msg)
            return False

    def test_get_all_beds(self):
        """Test GET /api/beds/beds - List all beds"""
        if not self.token:
            self.log_test("Get All Beds", False, "No token")
            return False
        
        response, error = self.make_request('GET', 'beds/beds')
        if error:
            self.log_test("Get All Beds", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            beds = data.get('beds', [])
            total = data.get('total', 0)
            
            # Store bed IDs for later tests
            if beds:
                self.bed_ids = [b.get('id') for b in beds if b.get('id')]
            
            success = total > 0 and isinstance(beds, list)
            details = f"Total beds: {total}, Bed IDs stored: {len(self.bed_ids)}"
            self.log_test("Get All Beds", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Get All Beds", False, error_msg)
            return False

    def test_filter_beds_by_ward(self):
        """Test GET /api/beds/beds?ward_id={ward_id} - Filter beds by ward"""
        if not self.token or not self.ward_ids:
            self.log_test("Filter Beds by Ward", False, "No token or ward IDs")
            return False
        
        ward_id = self.ward_ids[0]
        response, error = self.make_request('GET', 'beds/beds', params={"ward_id": ward_id})
        if error:
            self.log_test("Filter Beds by Ward", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            beds = data.get('beds', [])
            
            # Check if all returned beds belong to the ward
            all_match = all(b.get('ward_id') == ward_id for b in beds)
            
            success = all_match and len(beds) > 0
            details = f"Beds in ward: {len(beds)}, All match: {all_match}"
            self.log_test("Filter Beds by Ward", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Filter Beds by Ward", False, error_msg)
            return False

    def test_filter_beds_by_status(self):
        """Test GET /api/beds/beds?status=available - Filter beds by status"""
        if not self.token:
            self.log_test("Filter Beds by Status", False, "No token")
            return False
        
        response, error = self.make_request('GET', 'beds/beds', params={"status": "available"})
        if error:
            self.log_test("Filter Beds by Status", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            beds = data.get('beds', [])
            
            # Check if all returned beds are available
            all_available = all(b.get('status') == 'available' for b in beds)
            
            success = all_available
            details = f"Available beds: {len(beds)}, All available: {all_available}"
            self.log_test("Filter Beds by Status", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Filter Beds by Status", False, error_msg)
            return False

    # ============== Census Dashboard Tests ==============
    
    def test_get_census_dashboard(self):
        """Test GET /api/beds/census - Get real-time ward census"""
        if not self.token:
            self.log_test("Get Census Dashboard", False, "No token")
            return False
        
        response, error = self.make_request('GET', 'beds/census')
        if error:
            self.log_test("Get Census Dashboard", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            summary = data.get('summary', {})
            critical_care = data.get('critical_care', {})
            wards = data.get('wards', [])
            
            # Verify summary structure
            has_total_beds = 'total_beds' in summary
            has_available = 'available' in summary
            has_occupied = 'occupied' in summary
            has_occupancy_rate = 'overall_occupancy' in summary
            
            # Verify critical care section
            has_critical = 'total' in critical_care
            
            # Verify wards breakdown
            is_wards_list = isinstance(wards, list)
            
            success = has_total_beds and has_available and has_occupied and has_occupancy_rate and has_critical and is_wards_list
            details = f"Total beds: {summary.get('total_beds')}, Available: {summary.get('available')}, Occupied: {summary.get('occupied')}, Occupancy: {summary.get('overall_occupancy')}%"
            self.log_test("Get Census Dashboard", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Get Census Dashboard", False, error_msg)
            return False

    # ============== Admission Workflow Tests ==============
    
    def test_create_admission(self):
        """Test POST /api/beds/admissions/create - Admit patient to bed"""
        if not self.token:
            self.log_test("Create Admission", False, "No token")
            return False
        
        # Get available beds
        response, error = self.make_request('GET', 'beds/beds', params={"status": "available"})
        if error or response.status_code != 200:
            self.log_test("Create Admission", False, "Failed to get available beds")
            return False
        
        available_beds = response.json().get('beds', [])
        if not available_beds:
            self.log_test("Create Admission", False, "No available beds")
            return False
        
        # Use first available bed
        bed_id = available_beds[0].get('id')
        
        admission_data = {
            "patient_id": self.patient_id,
            "bed_id": bed_id,
            "admission_type": "inpatient",
            "admitting_diagnosis": "Pneumonia",
            "admitting_physician_id": self.bed_manager_id,
            "admission_source": "emergency",
            "expected_los": 5,
            "notes": "Test admission",
            "isolation_required": False
        }
        
        response, error = self.make_request('POST', 'beds/admissions/create', admission_data)
        if error:
            self.log_test("Create Admission", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            admission = data.get('admission', {})
            self.admission_id = admission.get('id')
            
            # Verify admission fields
            has_id = bool(self.admission_id)
            correct_patient = admission.get('patient_id') == self.patient_id
            correct_bed = admission.get('bed_id') == bed_id
            correct_status = admission.get('status') == 'admitted'
            
            success = has_id and correct_patient and correct_bed and correct_status
            details = f"Admission ID: {self.admission_id}, Patient: {correct_patient}, Bed: {correct_bed}, Status: {admission.get('status')}"
            self.log_test("Create Admission", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Create Admission", False, error_msg)
            return False

    def test_verify_bed_status_after_admission(self):
        """Test that bed status changes to 'occupied' after admission"""
        if not self.token:
            self.log_test("Verify Bed Status After Admission", False, "No token")
            return False
        
        response, error = self.make_request('GET', 'beds/beds', params={"status": "occupied"})
        if error:
            self.log_test("Verify Bed Status After Admission", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            beds = data.get('beds', [])
            
            # Should have occupied beds
            has_occupied = len(beds) > 0
            
            success = has_occupied
            details = f"Occupied beds count: {len(beds)}"
            self.log_test("Verify Bed Status After Admission", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Verify Bed Status After Admission", False, error_msg)
            return False

    def test_verify_ward_counts_after_admission(self):
        """Test that ward counts update after admission"""
        if not self.token:
            self.log_test("Verify Ward Counts After Admission", False, "No token")
            return False
        
        response, error = self.make_request('GET', 'beds/census')
        if error:
            self.log_test("Verify Ward Counts After Admission", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            summary = data.get('summary', {})
            
            # Verify occupied count increased
            occupied = summary.get('occupied', 0)
            available = summary.get('available', 0)
            
            success = occupied > 0
            details = f"Occupied: {occupied}, Available: {available}"
            self.log_test("Verify Ward Counts After Admission", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Verify Ward Counts After Admission", False, error_msg)
            return False

    def test_get_current_admissions(self):
        """Test GET /api/beds/admissions - List current admissions"""
        if not self.token:
            self.log_test("Get Current Admissions", False, "No token")
            return False
        
        response, error = self.make_request('GET', 'beds/admissions')
        if error:
            self.log_test("Get Current Admissions", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            admissions = data.get('admissions', [])
            total = data.get('total', 0)
            
            # Should have at least our admission
            has_admissions = total > 0
            is_list = isinstance(admissions, list)
            
            success = has_admissions and is_list
            details = f"Total admissions: {total}"
            self.log_test("Get Current Admissions", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Get Current Admissions", False, error_msg)
            return False

    def test_get_patient_admission_history(self):
        """Test GET /api/beds/admissions/patient/{patient_id} - Get patient admission history"""
        if not self.token:
            self.log_test("Get Patient Admission History", False, "No token")
            return False
        
        response, error = self.make_request('GET', f'beds/admissions/patient/{self.patient_id}')
        if error:
            self.log_test("Get Patient Admission History", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            admissions = data.get('admissions', [])
            total = data.get('total', 0)
            
            # Should have at least our admission
            has_admissions = total > 0
            is_list = isinstance(admissions, list)
            
            success = has_admissions and is_list
            details = f"Patient admission history count: {total}"
            self.log_test("Get Patient Admission History", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Get Patient Admission History", False, error_msg)
            return False

    # ============== Transfer Workflow Tests ==============
    
    def test_transfer_patient(self):
        """Test POST /api/beds/admissions/{id}/transfer - Transfer patient to different bed"""
        if not self.token or not self.admission_id:
            self.log_test("Transfer Patient", False, "No token or admission ID")
            return False
        
        # Get available beds for transfer
        response, error = self.make_request('GET', 'beds/beds', params={"status": "available"})
        if error or response.status_code != 200:
            self.log_test("Transfer Patient", False, "Failed to get available beds")
            return False
        
        available_beds = response.json().get('beds', [])
        if not available_beds:
            self.log_test("Transfer Patient", False, "No available beds for transfer")
            return False
        
        # Use first available bed for transfer
        self.transfer_bed_id = available_beds[0].get('id')
        
        transfer_data = {
            "to_bed_id": self.transfer_bed_id,
            "transfer_reason": "Better monitoring required",
            "notes": "Test transfer"
        }
        
        response, error = self.make_request('POST', f'beds/admissions/{self.admission_id}/transfer', transfer_data)
        if error:
            self.log_test("Transfer Patient", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            transfer = data.get('transfer', {})
            
            # Verify transfer fields
            correct_to_bed = transfer.get('to_bed_id') == self.transfer_bed_id
            has_from_bed = bool(transfer.get('from_bed_id'))
            has_timestamp = bool(transfer.get('transferred_at'))
            
            success = correct_to_bed and has_from_bed and has_timestamp
            details = f"From bed: {transfer.get('from_bed_number')}, To bed: {transfer.get('to_bed_number')}"
            self.log_test("Transfer Patient", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Transfer Patient", False, error_msg)
            return False

    def test_verify_old_bed_cleaning_status(self):
        """Test that old bed changes to 'cleaning' status after transfer"""
        if not self.token:
            self.log_test("Verify Old Bed Cleaning Status", False, "No token")
            return False
        
        response, error = self.make_request('GET', 'beds/beds', params={"status": "cleaning"})
        if error:
            self.log_test("Verify Old Bed Cleaning Status", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            beds = data.get('beds', [])
            
            # Should have at least one bed in cleaning status after transfer
            has_cleaning = len(beds) > 0
            
            success = has_cleaning
            details = f"Beds in cleaning status: {len(beds)}"
            self.log_test("Verify Old Bed Cleaning Status", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Verify Old Bed Cleaning Status", False, error_msg)
            return False

    def test_verify_new_bed_occupied_status(self):
        """Test that new bed changes to 'occupied' status after transfer"""
        if not self.token or not self.transfer_bed_id:
            self.log_test("Verify New Bed Occupied Status", False, "No token or transfer bed ID")
            return False
        
        response, error = self.make_request('GET', 'beds/beds', params={"status": "occupied"})
        if error:
            self.log_test("Verify New Bed Occupied Status", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            beds = data.get('beds', [])
            
            # Check if new bed is in occupied status
            bed_found = any(b.get('id') == self.transfer_bed_id for b in beds)
            
            success = bed_found
            details = f"New bed {self.transfer_bed_id} found in occupied status: {bed_found}"
            self.log_test("Verify New Bed Occupied Status", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Verify New Bed Occupied Status", False, error_msg)
            return False

    # ============== Discharge Workflow Tests ==============
    
    def test_discharge_patient(self):
        """Test POST /api/beds/admissions/{id}/discharge - Discharge patient"""
        if not self.token or not self.admission_id:
            self.log_test("Discharge Patient", False, "No token or admission ID")
            return False
        
        discharge_data = {
            "discharge_disposition": "home",
            "discharge_diagnosis": "Pneumonia - Resolved",
            "discharge_instructions": "Rest and take medications as prescribed",
            "follow_up_required": True,
            "follow_up_date": "2025-02-15"
        }
        
        response, error = self.make_request('POST', f'beds/admissions/{self.admission_id}/discharge', discharge_data)
        if error:
            self.log_test("Discharge Patient", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            message = data.get('message', '')
            
            success = 'discharged' in message.lower()
            details = f"Message: {message}"
            self.log_test("Discharge Patient", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Discharge Patient", False, error_msg)
            return False

    def test_verify_bed_cleaning_after_discharge(self):
        """Test that bed changes to 'cleaning' status after discharge"""
        if not self.token or not self.transfer_bed_id:
            self.log_test("Verify Bed Cleaning After Discharge", False, "No token or bed ID")
            return False
        
        response, error = self.make_request('GET', 'beds/beds', params={"status": "cleaning"})
        if error:
            self.log_test("Verify Bed Cleaning After Discharge", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            beds = data.get('beds', [])
            
            # Check if bed is in cleaning status
            bed_found = any(b.get('id') == self.transfer_bed_id for b in beds)
            
            success = bed_found
            details = f"Bed {self.transfer_bed_id} found in cleaning status after discharge: {bed_found}"
            self.log_test("Verify Bed Cleaning After Discharge", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Verify Bed Cleaning After Discharge", False, error_msg)
            return False

    def test_verify_ward_counts_after_discharge(self):
        """Test that ward occupied count decreases after discharge"""
        if not self.token:
            self.log_test("Verify Ward Counts After Discharge", False, "No token")
            return False
        
        response, error = self.make_request('GET', 'beds/census')
        if error:
            self.log_test("Verify Ward Counts After Discharge", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            summary = data.get('summary', {})
            
            # Verify census data is present
            has_occupied = 'occupied' in summary
            has_available = 'available' in summary
            
            success = has_occupied and has_available
            details = f"Occupied beds: {summary.get('occupied')}, Available: {summary.get('available')}"
            self.log_test("Verify Ward Counts After Discharge", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Verify Ward Counts After Discharge", False, error_msg)
            return False

    # ============== Edge Case Tests ==============
    
    def test_admit_to_occupied_bed_fails(self):
        """Test that admitting to an occupied bed fails"""
        if not self.token:
            self.log_test("Admit to Occupied Bed (Should Fail)", False, "No token")
            return False
        
        # Get an occupied bed
        response, error = self.make_request('GET', 'beds/beds', params={"status": "occupied"})
        if error or response.status_code != 200:
            self.log_test("Admit to Occupied Bed (Should Fail)", False, "Failed to get occupied beds")
            return False
        
        occupied_beds = response.json().get('beds', [])
        if not occupied_beds:
            self.log_test("Admit to Occupied Bed (Should Fail)", False, "No occupied beds to test with")
            return False
        
        # Try to admit to an occupied bed
        bed_id = occupied_beds[0].get('id')
        
        admission_data = {
            "patient_id": self.patient_id,
            "bed_id": bed_id,
            "admission_type": "inpatient",
            "admitting_diagnosis": "Test",
            "admitting_physician_id": self.bed_manager_id,
            "admission_source": "emergency"
        }
        
        response, error = self.make_request('POST', 'beds/admissions/create', admission_data)
        
        if response.status_code == 400:
            # Expected failure
            success = True
            details = "Correctly rejected admission to occupied bed"
            self.log_test("Admit to Occupied Bed (Should Fail)", success, details)
            return True
        else:
            success = False
            details = f"Unexpected status: {response.status_code}"
            self.log_test("Admit to Occupied Bed (Should Fail)", success, details)
            return False

    def test_transfer_discharged_patient_fails(self):
        """Test that transferring a discharged patient fails"""
        if not self.token or not self.admission_id:
            self.log_test("Transfer Discharged Patient (Should Fail)", False, "No token or admission ID")
            return False
        
        # Try to transfer already discharged patient
        transfer_data = {
            "to_bed_id": self.bed_ids[3] if len(self.bed_ids) > 3 else self.bed_ids[0],
            "transfer_reason": "Test",
            "notes": "Should fail"
        }
        
        response, error = self.make_request('POST', f'beds/admissions/{self.admission_id}/transfer', transfer_data)
        
        if response.status_code == 400:
            # Expected failure
            success = True
            details = "Correctly rejected transfer of discharged patient"
            self.log_test("Transfer Discharged Patient (Should Fail)", success, details)
            return True
        else:
            success = False
            details = f"Unexpected status: {response.status_code}"
            self.log_test("Transfer Discharged Patient (Should Fail)", success, details)
            return False

    def test_discharge_already_discharged_patient_fails(self):
        """Test that discharging already discharged patient fails"""
        if not self.token or not self.admission_id:
            self.log_test("Discharge Already Discharged Patient (Should Fail)", False, "No token or admission ID")
            return False
        
        # Try to discharge already discharged patient
        discharge_data = {
            "discharge_disposition": "home",
            "discharge_diagnosis": "Test",
            "discharge_instructions": "Should fail"
        }
        
        response, error = self.make_request('POST', f'beds/admissions/{self.admission_id}/discharge', discharge_data)
        
        if response.status_code == 400:
            # Expected failure
            success = True
            details = "Correctly rejected discharge of already discharged patient"
            self.log_test("Discharge Already Discharged Patient (Should Fail)", success, details)
            return True
        else:
            success = False
            details = f"Unexpected status: {response.status_code}"
            self.log_test("Discharge Already Discharged Patient (Should Fail)", success, details)
            return False

    # ============== Main Test Runner ==============
    
    def run_all_tests(self):
        """Run all bed management tests"""
        print("🏥 Starting Bed Management Module Testing")
        print("=" * 80)
        print("Backend URL:", self.base_url)
        print("Test User: bed_manager@yacco.health / test123")
        print("Patient ID:", self.patient_id)
        print("=" * 80)
        
        # Test sequence
        tests = [
            # Authentication
            self.test_bed_manager_login,
            
            # Ward Management
            self.test_get_wards_empty,
            self.test_seed_default_wards,
            self.test_get_wards_after_seeding,
            self.test_filter_wards_by_type,
            self.test_seed_wards_idempotency,
            
            # Bed Management
            self.test_bulk_create_beds,
            self.test_get_all_beds,
            self.test_filter_beds_by_ward,
            self.test_filter_beds_by_status,
            
            # Census Dashboard
            self.test_get_census_dashboard,
            
            # Admission Workflow
            self.test_create_admission,
            self.test_verify_bed_status_after_admission,
            self.test_verify_ward_counts_after_admission,
            self.test_get_current_admissions,
            self.test_get_patient_admission_history,
            
            # Transfer Workflow
            self.test_transfer_patient,
            self.test_verify_old_bed_cleaning_status,
            self.test_verify_new_bed_occupied_status,
            
            # Discharge Workflow
            self.test_discharge_patient,
            self.test_verify_bed_cleaning_after_discharge,
            self.test_verify_ward_counts_after_discharge,
            
            # Edge Cases
            self.test_admit_to_occupied_bed_fails,
            self.test_transfer_discharged_patient_fails,
            self.test_discharge_already_discharged_patient_fails,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_test(test.__name__, False, f"Exception: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 80)
        print(f"📊 BED MANAGEMENT MODULE TEST SUMMARY")
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
            print(f"\n✅ ALL TESTS PASSED!")
        
        return self.tests_passed == self.tests_run


if __name__ == "__main__":
    tester = BedManagementTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
