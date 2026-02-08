#!/usr/bin/env python3

import requests
import json

def test_endpoint(method, url, data=None, headers=None):
    """Test a single endpoint"""
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=headers, timeout=30)
        
        print(f"{method} {url}")
        print(f"Status: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Response: {response.text}")
        
        return response
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    base_url = "https://yacco-health.preview.emergentagent.com/api"
    
    print("🧪 Testing Nurse Shift Management - Complete Workflow")
    print("=" * 60)
    
    # Step 1: Login as super admin to create nurse user
    print("\n1. Login as Super Admin")
    login_data = {
        "email": "ygtnetworks@gmail.com",
        "password": "test123"
    }
    
    response = test_endpoint('POST', f"{base_url}/auth/login", login_data)
    
    if response and response.status_code == 200:
        data = response.json()
        super_admin_token = data.get('token')
        
        # Step 2: Create nurse user using super admin
        print("\n2. Creating Nurse User via Super Admin")
        headers = {'Authorization': f'Bearer {super_admin_token}', 'Content-Type': 'application/json'}
        
        nurse_data = {
            "email": "testnurse@hospital.com",
            "password": "test123",
            "first_name": "Test",
            "last_name": "Nurse",
            "role": "nurse",
            "department": "Emergency Department"
        }
        
        response = test_endpoint('POST', f"{base_url}/auth/register", nurse_data, headers)
        
        if response and response.status_code in [200, 201]:
            print("✅ Nurse user created successfully")
        elif response and response.status_code == 400:
            print("ℹ️ Nurse user already exists")
        
        # Step 3: Try to login as nurse
        print("\n3. Login as Nurse")
        nurse_login_data = {
            "email": "testnurse@hospital.com",
            "password": "test123"
        }
        
        response = test_endpoint('POST', f"{base_url}/auth/login", nurse_login_data)
        
        if response and response.status_code == 200:
            data = response.json()
            nurse_token = data.get('token')
            user = data.get('user', {})
            
            print(f"✅ Nurse login successful - Role: {user.get('role')}")
            
            # Now test nurse functionality
            nurse_headers = {'Authorization': f'Bearer {nurse_token}', 'Content-Type': 'application/json'}
            
            # Step 4: Test nurse shift clock-in
            print("\n4. Testing Nurse Shift Clock-In")
            clock_in_data = {
                "shift_type": "morning"
            }
            
            response = test_endpoint('POST', f"{base_url}/nurse/shifts/clock-in", clock_in_data, nurse_headers)
            
            if response and response.status_code == 200:
                print("✅ Clock-in successful")
                
                # Step 5: Test get current shift
                print("\n5. Testing Get Current Shift")
                response = test_endpoint('GET', f"{base_url}/nurse/current-shift", None, nurse_headers)
                
                if response and response.status_code == 200:
                    print("✅ Get current shift successful")
                    
                    # Step 6: Test clock-out
                    print("\n6. Testing Nurse Shift Clock-Out")
                    response = test_endpoint('POST', f"{base_url}/nurse/shifts/clock-out", None, nurse_headers)
                    
                    if response and response.status_code == 200:
                        print("✅ Clock-out successful")
                        print("\n🎉 All nurse shift management tests passed!")
                    else:
                        print("❌ Clock-out failed")
                else:
                    print("❌ Get current shift failed")
            else:
                print("❌ Clock-in failed")
        else:
            print("❌ Nurse login failed")
    else:
        print("❌ Super admin login failed")

if __name__ == "__main__":
    main()