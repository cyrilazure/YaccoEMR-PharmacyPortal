#!/usr/bin/env python3
"""
Ambulance Portal & Emergency Transport Module Testing
Test Phase 3 - Complete ambulance workflow from request to completion
"""

import requests
import sys
import json
from datetime import datetime, timedelta, timezone

class AmbulanceModuleTester:
    def __init__(self, base_url="https://medconnect-222.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
        # Test data storage
        self.it_admin_token = None
        self.it_admin_id = None
        self.physician_token = None
        self.physician_id = None
        self.nurse_token = None
        self.nurse_id = None
        self.biller_token = None
        self.biller_id = None
        
        self.vehicle_id = None
        self.request_id = None
        self.shift_id = None
        self.patient_id = None

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

    def test_it_admin_login(self):
        """Test IT Admin Login"""
        login_data = {
            "email": "it_admin@yacco.health",
            "password": "test123"
        }
        
        response, error = self.make_request('POST', 'auth/login', login_data)
        if error:
            self.log_test("IT Admin Login", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.it_admin_token = data.get('token')
            user = data.get('user', {})
            self.it_admin_id = user.get('id')
            
            success = bool(self.it_admin_token) and user.get('role') == 'hospital_it_admin'
            details = f"Role: {user.get('role')}, Email: {user.get('email')}"
            self.log_test("IT Admin Login", success, details)
            
            # Set token for subsequent requests
            self.token = self.it_admin_token
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("IT Admin Login", False, error_msg)
            return False

    def test_register_vehicle(self):
        """Test Register Ambulance Vehicle - POST /api/ambulance/vehicles"""
        if not self.it_admin_token:
            self.log_test("Register Ambulance Vehicle", False, "No IT admin token")
            return False
        
        vehicle_data = {
            "vehicle_number": "GW-5678-22",
            "vehicle_type": "emergency_response",
            "equipment_level": "advanced",
            "make_model": "Toyota Hiace Ambulance",
            "year": 2022,
            "capacity": 2,
            "has_oxygen": True,
            "has_defibrillator": True,
            "has_stretcher": True,
            "has_ventilator": False,
            "notes": "Advanced life support ambulance"
        }
        
        response, error = self.make_request('POST', 'ambulance/vehicles', vehicle_data)
        if error:
            self.log_test("Register Ambulance Vehicle", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            vehicle = data.get('vehicle', {})
            self.vehicle_id = vehicle.get('id')
            
            success = (
                bool(self.vehicle_id) and
                vehicle.get('vehicle_number') == 'GW-5678-22' and
                vehicle.get('vehicle_type') == 'emergency_response' and
                vehicle.get('equipment_level') == 'advanced' and
                vehicle.get('status') == 'available'
            )
            
            details = f"Vehicle ID: {self.vehicle_id}, Number: {vehicle.get('vehicle_number')}, Status: {vehicle.get('status')}"
            self.log_test("Register Ambulance Vehicle", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Register Ambulance Vehicle", False, error_msg)
            return False

    def test_list_vehicles(self):
        """Test List All Vehicles - GET /api/ambulance/vehicles"""
        if not self.it_admin_token:
            self.log_test("List All Vehicles", False, "No IT admin token")
            return False
        
        response, error = self.make_request('GET', 'ambulance/vehicles')
        if error:
            self.log_test("List All Vehicles", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            vehicles = data.get('vehicles', [])
            total = data.get('total', 0)
            
            # Check if our registered vehicle is in the list
            found_vehicle = False
            if self.vehicle_id:
                for v in vehicles:
                    if v.get('id') == self.vehicle_id:
                        found_vehicle = True
                        break
            
            success = isinstance(vehicles, list) and total > 0 and found_vehicle
            details = f"Total vehicles: {total}, Found registered vehicle: {found_vehicle}"
            self.log_test("List All Vehicles", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("List All Vehicles", False, error_msg)
            return False

    def test_update_vehicle_status(self):
        """Test Update Vehicle Status - PUT /api/ambulance/vehicles/{id}/status"""
        if not self.it_admin_token or not self.vehicle_id:
            self.log_test("Update Vehicle Status", False, "No IT admin token or vehicle ID")
            return False
        
        response, error = self.make_request(
            'PUT', 
            f'ambulance/vehicles/{self.vehicle_id}/status',
            params={"status": "maintenance", "notes": "Routine maintenance"}
        )
        if error:
            self.log_test("Update Vehicle Status", False, error)
            return False
        
        if response.status_code == 200:
            # Verify status was updated by fetching vehicles
            verify_response, verify_error = self.make_request('GET', 'ambulance/vehicles')
            if verify_response and verify_response.status_code == 200:
                vehicles = verify_response.json().get('vehicles', [])
                updated_vehicle = next((v for v in vehicles if v.get('id') == self.vehicle_id), None)
                
                success = updated_vehicle and updated_vehicle.get('status') == 'maintenance'
                details = f"Status updated to: {updated_vehicle.get('status') if updated_vehicle else 'N/A'}"
                self.log_test("Update Vehicle Status", success, details)
                
                # Change back to available for dispatch tests
                self.make_request(
                    'PUT', 
                    f'ambulance/vehicles/{self.vehicle_id}/status',
                    params={"status": "available"}
                )
                return success
            else:
                self.log_test("Update Vehicle Status", False, "Could not verify status update")
                return False
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Update Vehicle Status", False, error_msg)
            return False

    def test_create_test_patient(self):
        """Create a test patient for ambulance request"""
        if not self.it_admin_token:
            self.log_test("Create Test Patient", False, "No IT admin token")
            return False
        
        patient_data = {
            "first_name": "Test",
            "last_name": "Patient",
            "date_of_birth": "1980-05-15",
            "gender": "male",
            "mrn": "MRN-001",
            "payment_type": "insurance"
        }
        
        response, error = self.make_request('POST', 'patients', patient_data)
        if error:
            self.log_test("Create Test Patient", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            self.patient_id = data.get('id')
            
            success = bool(self.patient_id)
            details = f"Patient ID: {self.patient_id}, MRN: {data.get('mrn')}"
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

    def test_create_physician_user(self):
        """Create a physician user for testing request creation"""
        # Get organization_id from IT admin
        org_id = None
        if self.it_admin_token:
            original_token = self.token
            self.token = self.it_admin_token
            response, error = self.make_request('GET', 'auth/me')
            if response and response.status_code == 200:
                org_id = response.json().get('organization_id')
            self.token = original_token
        
        physician_data = {
            "email": "test.physician@yacco.health",
            "password": "test123",
            "first_name": "Test",
            "last_name": "Physician",
            "role": "physician",
            "department": "Emergency Medicine",
            "organization_id": org_id
        }
        
        response, error = self.make_request('POST', 'auth/register', physician_data)
        if error:
            self.log_test("Create Physician User", False, error)
            return False
        
        if response.status_code in [200, 201]:
            data = response.json()
            self.physician_token = data.get('token')
            user = data.get('user', {})
            self.physician_id = user.get('id')
            
            success = bool(self.physician_token)
            details = f"Physician ID: {self.physician_id}"
            self.log_test("Create Physician User", success, details)
            return success
        elif response.status_code == 400:
            # User already exists, try to login
            login_data = {"email": "test.physician@yacco.health", "password": "test123"}
            login_response, login_error = self.make_request('POST', 'auth/login', login_data)
            if login_response and login_response.status_code == 200:
                data = login_response.json()
                self.physician_token = data.get('token')
                user = data.get('user', {})
                self.physician_id = user.get('id')
                self.log_test("Create Physician User", True, "User already exists, logged in")
                return True
            else:
                self.log_test("Create Physician User", False, "User exists but login failed")
                return False
        else:
            self.log_test("Create Physician User", False, f"Status: {response.status_code}")
            return False

    def test_create_ambulance_request(self):
        """Test Create Ambulance Request - POST /api/ambulance/requests"""
        if not self.physician_token or not self.patient_id:
            self.log_test("Create Ambulance Request", False, "No physician token or patient ID")
            return False
        
        # Switch to physician token
        original_token = self.token
        self.token = self.physician_token
        
        request_data = {
            "patient_id": self.patient_id,
            "patient_name": "Test Patient",
            "patient_mrn": "MRN-001",
            "pickup_location": "Emergency Ward",
            "destination_facility": "Korle-Bu Teaching Hospital",
            "destination_address": "Korle-Bu, Accra",
            "referral_reason": "Acute MI - needs cardiac catheterization",
            "diagnosis_summary": "STEMI, requires urgent PCI",
            "trip_type": "emergency",
            "priority_level": "emergency",
            "special_requirements": "Cardiac monitoring required",
            "physician_notes": "Patient unstable, requires immediate transfer"
        }
        
        response, error = self.make_request('POST', 'ambulance/requests', request_data)
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Create Ambulance Request", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            request = data.get('request', {})
            self.request_id = request.get('id')
            request_number = request.get('request_number')
            
            # Verify request_number format: AMB-YYYYMMDD-XXXXXXXX
            valid_format = request_number and request_number.startswith('AMB-')
            
            success = (
                bool(self.request_id) and
                valid_format and
                request.get('status') == 'requested' and
                request.get('trip_type') == 'emergency' and
                request.get('priority_level') == 'emergency'
            )
            
            details = f"Request ID: {self.request_id}, Number: {request_number}, Status: {request.get('status')}"
            self.log_test("Create Ambulance Request", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Create Ambulance Request", False, error_msg)
            return False

    def test_list_requests(self):
        """Test List Requests - GET /api/ambulance/requests"""
        if not self.it_admin_token:
            self.log_test("List Ambulance Requests", False, "No IT admin token")
            return False
        
        response, error = self.make_request('GET', 'ambulance/requests')
        if error:
            self.log_test("List Ambulance Requests", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            requests = data.get('requests', [])
            total = data.get('total', 0)
            
            # Check if our created request is in the list
            found_request = False
            if self.request_id:
                for r in requests:
                    if r.get('id') == self.request_id:
                        found_request = True
                        break
            
            success = isinstance(requests, list) and total > 0 and found_request
            details = f"Total requests: {total}, Found created request: {found_request}"
            self.log_test("List Ambulance Requests", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("List Ambulance Requests", False, error_msg)
            return False

    def test_approve_request(self):
        """Test Approve Request - PUT /api/ambulance/requests/{id}/approve"""
        if not self.it_admin_token or not self.request_id:
            self.log_test("Approve Ambulance Request", False, "No IT admin token or request ID")
            return False
        
        response, error = self.make_request('PUT', f'ambulance/requests/{self.request_id}/approve')
        if error:
            self.log_test("Approve Ambulance Request", False, error)
            return False
        
        if response.status_code == 200:
            # Verify status was updated by fetching requests
            verify_response, verify_error = self.make_request('GET', 'ambulance/requests')
            if verify_response and verify_response.status_code == 200:
                requests = verify_response.json().get('requests', [])
                approved_request = next((r for r in requests if r.get('id') == self.request_id), None)
                
                success = (
                    approved_request and 
                    approved_request.get('status') == 'approved' and
                    approved_request.get('approved_at') is not None
                )
                
                details = f"Status: {approved_request.get('status') if approved_request else 'N/A'}, Approved at: {approved_request.get('approved_at') if approved_request else 'N/A'}"
                self.log_test("Approve Ambulance Request", success, details)
                return success
            else:
                self.log_test("Approve Ambulance Request", False, "Could not verify approval")
                return False
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Approve Ambulance Request", False, error_msg)
            return False

    def test_dispatch_ambulance(self):
        """Test Dispatch Ambulance - POST /api/ambulance/requests/{id}/dispatch"""
        if not self.it_admin_token or not self.request_id or not self.vehicle_id:
            self.log_test("Dispatch Ambulance", False, "Missing required data")
            return False
        
        dispatch_data = {
            "request_id": self.request_id,
            "vehicle_id": self.vehicle_id,
            "driver_id": self.it_admin_id,
            "paramedic_id": self.it_admin_id,
            "estimated_arrival": "15 minutes",
            "notes": "Dispatched with full crew"
        }
        
        response, error = self.make_request('POST', f'ambulance/requests/{self.request_id}/dispatch', dispatch_data)
        if error:
            self.log_test("Dispatch Ambulance", False, error)
            return False
        
        if response.status_code == 200:
            # Verify dispatch by checking request and vehicle status
            verify_response, verify_error = self.make_request('GET', 'ambulance/requests')
            vehicle_response, vehicle_error = self.make_request('GET', 'ambulance/vehicles')
            
            if verify_response and verify_response.status_code == 200 and vehicle_response and vehicle_response.status_code == 200:
                requests = verify_response.json().get('requests', [])
                vehicles = vehicle_response.json().get('vehicles', [])
                
                dispatched_request = next((r for r in requests if r.get('id') == self.request_id), None)
                dispatched_vehicle = next((v for v in vehicles if v.get('id') == self.vehicle_id), None)
                
                success = (
                    dispatched_request and
                    dispatched_request.get('status') == 'dispatched' and
                    dispatched_request.get('vehicle_id') == self.vehicle_id and
                    dispatched_vehicle and
                    dispatched_vehicle.get('status') == 'in_use'
                )
                
                details = f"Request status: {dispatched_request.get('status') if dispatched_request else 'N/A'}, Vehicle status: {dispatched_vehicle.get('status') if dispatched_vehicle else 'N/A'}"
                self.log_test("Dispatch Ambulance", success, details)
                return success
            else:
                self.log_test("Dispatch Ambulance", False, "Could not verify dispatch")
                return False
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Dispatch Ambulance", False, error_msg)
            return False

    def test_update_status_en_route(self):
        """Test Update Status to En Route - PUT /api/ambulance/requests/{id}/update-status"""
        if not self.it_admin_token or not self.request_id:
            self.log_test("Update Status: En Route", False, "No IT admin token or request ID")
            return False
        
        update_data = {
            "status": "en_route",
            "notes": "Ambulance en route to pickup location"
        }
        
        response, error = self.make_request('PUT', f'ambulance/requests/{self.request_id}/update-status', update_data)
        if error:
            self.log_test("Update Status: En Route", False, error)
            return False
        
        if response.status_code == 200:
            # Verify status update
            verify_response, verify_error = self.make_request('GET', 'ambulance/requests')
            if verify_response and verify_response.status_code == 200:
                requests = verify_response.json().get('requests', [])
                updated_request = next((r for r in requests if r.get('id') == self.request_id), None)
                
                success = updated_request and updated_request.get('status') == 'en_route'
                details = f"Status: {updated_request.get('status') if updated_request else 'N/A'}"
                self.log_test("Update Status: En Route", success, details)
                return success
            else:
                self.log_test("Update Status: En Route", False, "Could not verify status update")
                return False
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Update Status: En Route", False, error_msg)
            return False

    def test_update_status_arrived(self):
        """Test Update Status to Arrived - PUT /api/ambulance/requests/{id}/update-status"""
        if not self.it_admin_token or not self.request_id:
            self.log_test("Update Status: Arrived", False, "No IT admin token or request ID")
            return False
        
        update_data = {
            "status": "arrived",
            "notes": "Arrived at pickup location",
            "actual_pickup_time": datetime.now(timezone.utc).isoformat()
        }
        
        response, error = self.make_request('PUT', f'ambulance/requests/{self.request_id}/update-status', update_data)
        if error:
            self.log_test("Update Status: Arrived", False, error)
            return False
        
        if response.status_code == 200:
            # Verify status update
            verify_response, verify_error = self.make_request('GET', 'ambulance/requests')
            if verify_response and verify_response.status_code == 200:
                requests = verify_response.json().get('requests', [])
                updated_request = next((r for r in requests if r.get('id') == self.request_id), None)
                
                success = updated_request and updated_request.get('status') == 'arrived'
                details = f"Status: {updated_request.get('status') if updated_request else 'N/A'}"
                self.log_test("Update Status: Arrived", success, details)
                return success
            else:
                self.log_test("Update Status: Arrived", False, "Could not verify status update")
                return False
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Update Status: Arrived", False, error_msg)
            return False

    def test_update_status_completed(self):
        """Test Update Status to Completed - PUT /api/ambulance/requests/{id}/update-status"""
        if not self.it_admin_token or not self.request_id:
            self.log_test("Update Status: Completed", False, "No IT admin token or request ID")
            return False
        
        update_data = {
            "status": "completed",
            "notes": "Patient delivered to destination facility",
            "actual_arrival_time": datetime.now(timezone.utc).isoformat(),
            "mileage": 25.5
        }
        
        response, error = self.make_request('PUT', f'ambulance/requests/{self.request_id}/update-status', update_data)
        if error:
            self.log_test("Update Status: Completed", False, error)
            return False
        
        if response.status_code == 200:
            # Verify status update and vehicle freed
            verify_response, verify_error = self.make_request('GET', 'ambulance/requests')
            vehicle_response, vehicle_error = self.make_request('GET', 'ambulance/vehicles')
            
            if verify_response and verify_response.status_code == 200 and vehicle_response and vehicle_response.status_code == 200:
                requests = verify_response.json().get('requests', [])
                vehicles = vehicle_response.json().get('vehicles', [])
                
                completed_request = next((r for r in requests if r.get('id') == self.request_id), None)
                freed_vehicle = next((v for v in vehicles if v.get('id') == self.vehicle_id), None)
                
                success = (
                    completed_request and
                    completed_request.get('status') == 'completed' and
                    completed_request.get('completed_at') is not None and
                    freed_vehicle and
                    freed_vehicle.get('status') == 'available' and
                    freed_vehicle.get('total_trips', 0) > 0
                )
                
                details = f"Request status: {completed_request.get('status') if completed_request else 'N/A'}, Vehicle status: {freed_vehicle.get('status') if freed_vehicle else 'N/A'}, Total trips: {freed_vehicle.get('total_trips', 0) if freed_vehicle else 0}"
                self.log_test("Update Status: Completed", success, details)
                return success
            else:
                self.log_test("Update Status: Completed", False, "Could not verify completion")
                return False
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Update Status: Completed", False, error_msg)
            return False

    def test_dashboard_stats(self):
        """Test Dashboard Stats - GET /api/ambulance/dashboard"""
        if not self.it_admin_token:
            self.log_test("Dashboard Stats", False, "No IT admin token")
            return False
        
        response, error = self.make_request('GET', 'ambulance/dashboard')
        if error:
            self.log_test("Dashboard Stats", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify dashboard structure
            has_fleet = 'fleet' in data
            has_requests = 'requests' in data
            has_staff = 'staff' in data
            
            fleet = data.get('fleet', {})
            requests = data.get('requests', {})
            staff = data.get('staff', {})
            
            success = (
                has_fleet and has_requests and has_staff and
                'total' in fleet and 'available' in fleet and 'in_use' in fleet and
                'active' in requests and 'completed_today' in requests and
                'total_emergency' in requests and 'total_scheduled' in requests and
                'active_shifts' in staff
            )
            
            details = f"Fleet: {fleet.get('total', 0)} total, {fleet.get('available', 0)} available, {fleet.get('in_use', 0)} in use | Requests: {requests.get('active', 0)} active, {requests.get('completed_today', 0)} completed today | Staff: {staff.get('active_shifts', 0)} active shifts"
            self.log_test("Dashboard Stats", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Dashboard Stats", False, error_msg)
            return False

    def test_staff_clock_in(self):
        """Test Staff Clock In - POST /api/ambulance/staff/clock-in"""
        if not self.it_admin_token or not self.vehicle_id:
            self.log_test("Staff Clock In", False, "No IT admin token or vehicle ID")
            return False
        
        clock_in_data = {
            "vehicle_id": self.vehicle_id,
            "shift_type": "day"
        }
        
        response, error = self.make_request('POST', 'ambulance/staff/clock-in', params=clock_in_data)
        if error:
            self.log_test("Staff Clock In", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            shift = data.get('shift', {})
            self.shift_id = shift.get('id')
            
            success = (
                bool(self.shift_id) and
                shift.get('vehicle_id') == self.vehicle_id and
                shift.get('shift_type') == 'day' and
                shift.get('clock_in') is not None and
                shift.get('clock_out') is None
            )
            
            details = f"Shift ID: {self.shift_id}, Vehicle: {shift.get('vehicle_id')}, Type: {shift.get('shift_type')}"
            self.log_test("Staff Clock In", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = str(error_data.get('detail', f'Status: {response.status_code}'))
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Staff Clock In", False, error_msg)
            return False

    def test_get_active_shifts(self):
        """Test Get Active Shifts - GET /api/ambulance/staff/active-shifts"""
        if not self.it_admin_token:
            self.log_test("Get Active Shifts", False, "No IT admin token")
            return False
        
        response, error = self.make_request('GET', 'ambulance/staff/active-shifts')
        if error:
            self.log_test("Get Active Shifts", False, error)
            return False
        
        if response.status_code == 200:
            data = response.json()
            shifts = data.get('shifts', [])
            total = data.get('total', 0)
            
            # Check if our shift is in the list
            found_shift = False
            if self.shift_id:
                for s in shifts:
                    if s.get('id') == self.shift_id:
                        found_shift = True
                        break
            
            success = isinstance(shifts, list) and total > 0 and found_shift
            details = f"Total active shifts: {total}, Found our shift: {found_shift}"
            self.log_test("Get Active Shifts", success, details)
            return success
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Get Active Shifts", False, error_msg)
            return False

    def test_staff_clock_out(self):
        """Test Staff Clock Out - POST /api/ambulance/staff/clock-out"""
        if not self.it_admin_token or not self.shift_id:
            self.log_test("Staff Clock Out", False, "No IT admin token or shift ID")
            return False
        
        response, error = self.make_request('POST', 'ambulance/staff/clock-out', params={"shift_id": self.shift_id})
        if error:
            self.log_test("Staff Clock Out", False, error)
            return False
        
        if response.status_code == 200:
            # Verify clock out by checking active shifts
            verify_response, verify_error = self.make_request('GET', 'ambulance/staff/active-shifts')
            if verify_response and verify_response.status_code == 200:
                shifts = verify_response.json().get('shifts', [])
                
                # Our shift should not be in active shifts anymore
                found_shift = any(s.get('id') == self.shift_id for s in shifts)
                
                success = not found_shift
                details = f"Shift {self.shift_id} still active: {found_shift}"
                self.log_test("Staff Clock Out", success, details)
                return success
            else:
                self.log_test("Staff Clock Out", False, "Could not verify clock out")
                return False
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', f'Status: {response.status_code}')
            except:
                error_msg = f'Status: {response.status_code}'
            self.log_test("Staff Clock Out", False, error_msg)
            return False

    def test_create_nurse_user(self):
        """Create a nurse user for access control testing"""
        # Get organization_id from IT admin
        org_id = None
        if self.it_admin_token:
            original_token = self.token
            self.token = self.it_admin_token
            response, error = self.make_request('GET', 'auth/me')
            if response and response.status_code == 200:
                org_id = response.json().get('organization_id')
            self.token = original_token
        
        nurse_data = {
            "email": "test.nurse@yacco.health",
            "password": "test123",
            "first_name": "Test",
            "last_name": "Nurse",
            "role": "nurse",
            "department": "Emergency Department",
            "organization_id": org_id
        }
        
        response, error = self.make_request('POST', 'auth/register', nurse_data)
        if error:
            self.log_test("Create Nurse User", False, error)
            return False
        
        if response.status_code in [200, 201]:
            data = response.json()
            self.nurse_token = data.get('token')
            user = data.get('user', {})
            self.nurse_id = user.get('id')
            
            success = bool(self.nurse_token)
            details = f"Nurse ID: {self.nurse_id}"
            self.log_test("Create Nurse User", success, details)
            return success
        elif response.status_code == 400:
            # User already exists, try to login
            login_data = {"email": "test.nurse@yacco.health", "password": "test123"}
            login_response, login_error = self.make_request('POST', 'auth/login', login_data)
            if login_response and login_response.status_code == 200:
                data = login_response.json()
                self.nurse_token = data.get('token')
                user = data.get('user', {})
                self.nurse_id = user.get('id')
                self.log_test("Create Nurse User", True, "User already exists, logged in")
                return True
            else:
                self.log_test("Create Nurse User", False, "User exists but login failed")
                return False
        else:
            self.log_test("Create Nurse User", False, f"Status: {response.status_code}")
            return False

    def test_nurse_can_create_request(self):
        """Test Nurse Can Create Request - Access Control"""
        if not self.nurse_token or not self.patient_id:
            self.log_test("Nurse Can Create Request", False, "No nurse token or patient ID")
            return False
        
        # Switch to nurse token
        original_token = self.token
        self.token = self.nurse_token
        
        request_data = {
            "patient_id": self.patient_id,
            "patient_name": "Test Patient",
            "patient_mrn": "MRN-001",
            "pickup_location": "Ward 3",
            "destination_facility": "Ridge Hospital",
            "referral_reason": "Specialist consultation",
            "trip_type": "scheduled",
            "priority_level": "routine"
        }
        
        response, error = self.make_request('POST', 'ambulance/requests', request_data)
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Nurse Can Create Request", False, error)
            return False
        
        # Nurse should be able to create requests (200)
        success = response.status_code == 200
        details = f"Status: {response.status_code}, Nurse allowed to create request: {success}"
        self.log_test("Nurse Can Create Request", success, details)
        return success

    def test_create_biller_user(self):
        """Create a biller user for access control testing"""
        # Get organization_id from IT admin
        org_id = None
        if self.it_admin_token:
            original_token = self.token
            self.token = self.it_admin_token
            response, error = self.make_request('GET', 'auth/me')
            if response and response.status_code == 200:
                org_id = response.json().get('organization_id')
            self.token = original_token
        
        biller_data = {
            "email": "test.biller@yacco.health",
            "password": "test123",
            "first_name": "Test",
            "last_name": "Biller",
            "role": "biller",
            "department": "Billing",
            "organization_id": org_id
        }
        
        response, error = self.make_request('POST', 'auth/register', biller_data)
        if error:
            self.log_test("Create Biller User", False, error)
            return False
        
        if response.status_code in [200, 201]:
            data = response.json()
            self.biller_token = data.get('token')
            user = data.get('user', {})
            self.biller_id = user.get('id')
            
            success = bool(self.biller_token)
            details = f"Biller ID: {self.biller_id}"
            self.log_test("Create Biller User", success, details)
            return success
        elif response.status_code == 400:
            # User already exists, try to login
            login_data = {"email": "test.biller@yacco.health", "password": "test123"}
            login_response, login_error = self.make_request('POST', 'auth/login', login_data)
            if login_response and login_response.status_code == 200:
                data = login_response.json()
                self.biller_token = data.get('token')
                user = data.get('user', {})
                self.biller_id = user.get('id')
                self.log_test("Create Biller User", True, "User already exists, logged in")
                return True
            else:
                self.log_test("Create Biller User", False, "User exists but login failed")
                return False
        else:
            self.log_test("Create Biller User", False, f"Status: {response.status_code}")
            return False

    def test_biller_cannot_create_request(self):
        """Test Biller Cannot Create Request - Access Control (403)"""
        if not self.biller_token or not self.patient_id:
            self.log_test("Biller Cannot Create Request", False, "No biller token or patient ID")
            return False
        
        # Switch to biller token
        original_token = self.token
        self.token = self.biller_token
        
        request_data = {
            "patient_id": self.patient_id,
            "patient_name": "Test Patient",
            "patient_mrn": "MRN-001",
            "pickup_location": "Ward 3",
            "destination_facility": "Ridge Hospital",
            "referral_reason": "Specialist consultation",
            "trip_type": "scheduled",
            "priority_level": "routine"
        }
        
        response, error = self.make_request('POST', 'ambulance/requests', request_data)
        
        # Restore original token
        self.token = original_token
        
        if error:
            self.log_test("Biller Cannot Create Request", False, error)
            return False
        
        # Biller should NOT be able to create requests (403)
        success = response.status_code == 403
        details = f"Status: {response.status_code}, Biller correctly denied: {success}"
        self.log_test("Biller Cannot Create Request", success, details)
        return success

    def test_only_admin_can_approve(self):
        """Test Only Admin Can Approve Requests - Access Control"""
        if not self.physician_token or not self.patient_id:
            self.log_test("Only Admin Can Approve", False, "No physician token or patient ID")
            return False
        
        # First create a request as physician
        original_token = self.token
        self.token = self.physician_token
        
        request_data = {
            "patient_id": self.patient_id,
            "patient_name": "Test Patient",
            "patient_mrn": "MRN-001",
            "pickup_location": "Ward 5",
            "destination_facility": "37 Military Hospital",
            "referral_reason": "Specialist consultation",
            "trip_type": "scheduled",
            "priority_level": "routine"
        }
        
        create_response, create_error = self.make_request('POST', 'ambulance/requests', request_data)
        
        if create_response and create_response.status_code == 200:
            test_request_id = create_response.json().get('request', {}).get('id')
            
            # Try to approve as physician (should fail with 403)
            approve_response, approve_error = self.make_request('PUT', f'ambulance/requests/{test_request_id}/approve')
            
            # Restore original token
            self.token = original_token
            
            if approve_response:
                # Physician should NOT be able to approve (403)
                success = approve_response.status_code == 403
                details = f"Physician approval status: {approve_response.status_code}, Correctly denied: {success}"
                self.log_test("Only Admin Can Approve", success, details)
                return success
            else:
                self.log_test("Only Admin Can Approve", False, "No response from approve endpoint")
                return False
        else:
            self.token = original_token
            self.log_test("Only Admin Can Approve", False, "Could not create test request")
            return False

    def run_all_tests(self):
        """Run all ambulance module tests"""
        print("🚑 Starting Ambulance Portal & Emergency Transport Module Testing")
        print("=" * 80)
        print("Test Phase 3 - Complete ambulance workflow from request to completion")
        print("Test User: it_admin@yacco.health / test123 (Hospital IT Admin)")
        print("=" * 80)
        
        # Test sequence
        tests = [
            # Authentication
            self.test_it_admin_login,
            
            # Fleet Management
            self.test_register_vehicle,
            self.test_list_vehicles,
            self.test_update_vehicle_status,
            
            # Setup for requests
            self.test_create_test_patient,
            self.test_create_physician_user,
            
            # Request Management
            self.test_create_ambulance_request,
            self.test_list_requests,
            
            # Approval Workflow
            self.test_approve_request,
            
            # Dispatch Workflow
            self.test_dispatch_ambulance,
            
            # Status Updates
            self.test_update_status_en_route,
            self.test_update_status_arrived,
            self.test_update_status_completed,
            
            # Dashboard
            self.test_dashboard_stats,
            
            # Staff Management
            self.test_staff_clock_in,
            self.test_get_active_shifts,
            self.test_staff_clock_out,
            
            # Access Control
            self.test_create_nurse_user,
            self.test_nurse_can_create_request,
            self.test_create_biller_user,
            self.test_biller_cannot_create_request,
            self.test_only_admin_can_approve
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_test(test.__name__, False, f"Exception: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 80)
        print(f"📊 AMBULANCE MODULE TEST SUMMARY")
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
    tester = AmbulanceModuleTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
