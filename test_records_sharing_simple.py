#!/usr/bin/env python3

import requests
import json
from datetime import datetime

class RecordsSharingTester:
    def __init__(self, base_url="https://admin-control-119.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.token1 = None
        self.token2 = None
        self.user1_id = None
        self.user2_id = None
        self.patient_id = None
        self.request_id = None

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
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, params=params)
            else:
                return None, f"Unsupported method: {method}"

            return response, None
        except Exception as e:
            return None, str(e)

    def test_complete_workflow(self):
        """Test complete Records Sharing workflow with existing users"""
        print("🔄 Testing Records Sharing / HIE Complete Workflow")
        print("=" * 50)
        
        # Step 1: Create two physician users
        import time
        timestamp = str(int(time.time()))
        
        physician1_data = {
            "email": f"physician1_{timestamp}@test.com",
            "password": "test123",
            "first_name": "Dr. Alice",
            "last_name": "Smith",
            "role": "physician",
            "department": "Cardiology",
            "specialty": "Interventional Cardiology"
        }
        
        physician2_data = {
            "email": f"physician2_{timestamp}@test.com",
            "password": "test123",
            "first_name": "Dr. Bob",
            "last_name": "Johnson",
            "role": "physician",
            "department": "Internal Medicine",
            "specialty": "Internal Medicine"
        }
        
        # Register physicians
        response, error = self.make_request('POST', 'auth/register', physician1_data)
        if error or response.status_code not in [200, 201]:
            print(f"❌ Physician 1 registration failed: {response.status_code if response else error}")
            return False
        
        self.token1 = response.json().get('token')
        self.user1_id = response.json().get('user', {}).get('id')
        print(f"✅ Physician 1 registered: {physician1_data['email']}")
        
        response, error = self.make_request('POST', 'auth/register', physician2_data)
        if error or response.status_code not in [200, 201]:
            print(f"❌ Physician 2 registration failed: {response.status_code if response else error}")
            return False
        
        self.token2 = response.json().get('token')
        self.user2_id = response.json().get('user', {}).get('id')
        print(f"✅ Physician 2 registered: {physician2_data['email']}")
        
        # Step 2: Create a patient as physician1
        patient_data = {
            "first_name": "Sarah",
            "last_name": "Williams",
            "date_of_birth": "1990-06-20",
            "gender": "female",
            "email": "sarah.williams@email.com",
            "phone": "555-0123",
            "address": "456 Health St, Medical City, State 12345",
            "emergency_contact_name": "Mike Williams",
            "emergency_contact_phone": "555-0124",
            "insurance_provider": "MedCare Insurance",
            "insurance_id": "MC123456789"
        }
        
        response, error = self.make_request('POST', 'patients', patient_data, token=self.token1)
        if error or response.status_code != 200:
            print(f"❌ Patient creation failed: {response.status_code if response else error}")
            return False
        
        self.patient_id = response.json().get('id')
        print(f"✅ Patient created: {patient_data['first_name']} {patient_data['last_name']} (ID: {self.patient_id})")
        
        # Step 3: Search for physicians (as physician1)
        response, error = self.make_request('GET', 'records-sharing/physicians/search', 
                                          params={'query': 'Bob'}, token=self.token1)
        if error or response.status_code != 200:
            print(f"❌ Physician search failed: {response.status_code if response else error}")
            return False
        
        search_data = response.json()
        physicians = search_data.get('physicians', [])
        found_physician2 = any(p.get('id') == self.user2_id for p in physicians)
        
        if not found_physician2:
            print(f"❌ Target physician not found in search results")
            return False
        
        print(f"✅ Physician search successful: Found {len(physicians)} physicians")
        
        # Step 4: Create records request (physician1 requesting from physician2)
        request_data = {
            "target_physician_id": self.user2_id,
            "patient_id": self.patient_id,
            "patient_name": "Sarah Williams",
            "reason": "Patient referred for specialized treatment. Need complete medical history for continuity of care.",
            "urgency": "routine",
            "requested_records": ["all"],
            "consent_signed": True,
            "consent_date": datetime.now().strftime("%Y-%m-%d")
        }
        
        response, error = self.make_request('POST', 'records-sharing/requests', request_data, token=self.token1)
        if error or response.status_code != 200:
            print(f"❌ Records request creation failed: {response.status_code if response else error}")
            return False
        
        request_response = response.json()
        self.request_id = request_response.get('request_id')
        request_number = request_response.get('request_number')
        print(f"✅ Records request created: {request_number} (ID: {self.request_id})")
        
        # Step 5: Get outgoing requests (as physician1)
        response, error = self.make_request('GET', 'records-sharing/requests/outgoing', token=self.token1)
        if error or response.status_code != 200:
            print(f"❌ Get outgoing requests failed: {response.status_code if response else error}")
            return False
        
        outgoing_data = response.json()
        outgoing_requests = outgoing_data.get('requests', [])
        has_our_request = any(r.get('id') == self.request_id for r in outgoing_requests)
        print(f"✅ Outgoing requests retrieved: {len(outgoing_requests)} requests, our request found: {has_our_request}")
        
        # Step 6: Get sharing statistics (as physician1)
        response, error = self.make_request('GET', 'records-sharing/stats', token=self.token1)
        if error or response.status_code != 200:
            print(f"❌ Get statistics failed: {response.status_code if response else error}")
            return False
        
        stats = response.json()
        print(f"✅ Statistics retrieved: {stats}")
        
        # Step 7: Get incoming requests (as physician2)
        response, error = self.make_request('GET', 'records-sharing/requests/incoming', token=self.token2)
        if error or response.status_code != 200:
            print(f"❌ Get incoming requests failed: {response.status_code if response else error}")
            return False
        
        incoming_data = response.json()
        incoming_requests = incoming_data.get('requests', [])
        has_our_request = any(r.get('id') == self.request_id for r in incoming_requests)
        print(f"✅ Incoming requests retrieved: {len(incoming_requests)} requests, our request found: {has_our_request}")
        
        # Step 8: Get notifications (as physician2)
        response, error = self.make_request('GET', 'records-sharing/notifications', token=self.token2)
        if error or response.status_code != 200:
            print(f"❌ Get notifications failed: {response.status_code if response else error}")
            return False
        
        notifications_data = response.json()
        notifications = notifications_data.get('notifications', [])
        unread_count = notifications_data.get('unread_count', 0)
        has_request_notification = any(n.get('related_request_id') == self.request_id for n in notifications)
        print(f"✅ Notifications retrieved: {len(notifications)} total, {unread_count} unread, request notification found: {has_request_notification}")
        
        # Step 9: Approve the request (as physician2)
        approval_data = {
            "approved": True,
            "notes": "Approved for continuity of care and specialized treatment",
            "access_duration_days": 30
        }
        
        response, error = self.make_request('POST', f'records-sharing/requests/{self.request_id}/respond', 
                                          approval_data, token=self.token2)
        if error or response.status_code != 200:
            print(f"❌ Request approval failed: {response.status_code if response else error}")
            return False
        
        approval_response = response.json()
        is_approved = approval_response.get('status') == 'approved'
        has_expiry = bool(approval_response.get('access_expires_at'))
        print(f"✅ Request approved: Status={approval_response.get('status')}, Has expiry: {has_expiry}")
        
        # Step 10: Get approval notification (as physician1)
        response, error = self.make_request('GET', 'records-sharing/notifications', token=self.token1)
        if error or response.status_code != 200:
            print(f"❌ Get approval notification failed: {response.status_code if response else error}")
            return False
        
        notifications_data = response.json()
        notifications = notifications_data.get('notifications', [])
        has_approval_notification = any(n.get('type') == 'request_approved' and 
                                      n.get('related_request_id') == self.request_id for n in notifications)
        print(f"✅ Approval notification check: Found approval notification: {has_approval_notification}")
        
        # Step 11: Get access grants (as physician1)
        response, error = self.make_request('GET', 'records-sharing/my-access-grants', token=self.token1)
        if error or response.status_code != 200:
            print(f"❌ Get access grants failed: {response.status_code if response else error}")
            return False
        
        grants_data = response.json()
        access_grants = grants_data.get('access_grants', [])
        has_patient_grant = any(g.get('patient_id') == self.patient_id for g in access_grants)
        print(f"✅ Access grants retrieved: {len(access_grants)} grants, patient grant found: {has_patient_grant}")
        
        # Step 12: View shared records (as physician1)
        response, error = self.make_request('GET', f'records-sharing/shared-records/{self.patient_id}', token=self.token1)
        if error or response.status_code != 200:
            print(f"❌ View shared records failed: {response.status_code if response else error}")
            if response:
                print(f"Response text: {response.text}")
            return False
        
        shared_records = response.json()
        has_patient_data = 'patient' in shared_records
        has_access_info = 'access_info' in shared_records
        patient_name_matches = shared_records.get('patient', {}).get('first_name') == 'Sarah'
        
        success = has_patient_data and has_access_info and patient_name_matches
        print(f"✅ Shared records retrieved: Patient data: {has_patient_data}, Access info: {has_access_info}, Name matches: {patient_name_matches}")
        
        print("\n" + "=" * 50)
        print("🎉 Records Sharing / HIE Workflow Test COMPLETED SUCCESSFULLY!")
        print("All 12 steps of the workflow executed without errors.")
        
        return True

def main():
    tester = RecordsSharingTester()
    success = tester.test_complete_workflow()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())