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
    base_url = "https://ghana-emr.preview.emergentagent.com/api"
    
    print("🧪 Testing Complete Nurse Workflow")
    print("=" * 60)
    
    # Step 1: Create nurse user
    print("\n1. Creating Nurse User")
    nurse_data = {
        "email": "testnurse@hospital.com",
        "password": "test123",
        "first_name": "Test",
        "last_name": "Nurse",
        "role": "nurse",
        "department": "Emergency Department"
    }
    
    response = test_endpoint('POST', f"{base_url}/auth/register", nurse_data)
    
    if response and response.status_code in [200, 201]:
        print("✅ Nurse user created successfully")
        data = response.json()
        nurse_token = data.get('token')
        user = data.get('user', {})
        
    elif response and response.status_code == 400:
        print("ℹ️ Nurse user already exists, trying to login")
        
        # Try to login
        login_data = {
            "email": "testnurse@hospital.com",
            "password": "test123"
        }
        
        response = test_endpoint('POST', f"{base_url}/auth/login", login_data)
        
        if response and response.status_code == 200:
            print("✅ Nurse login successful")
            data = response.json()
            nurse_token = data.get('token')
            user = data.get('user', {})
        else:
            print("❌ Nurse login failed")
            return
    else:
        print("❌ Failed to create nurse user")
        return
    
    # Now test nurse functionality
    headers = {'Authorization': f'Bearer {nurse_token}', 'Content-Type': 'application/json'}
    
    print(f"\n2. Nurse User Info: {user.get('first_name')} {user.get('last_name')}, Role: {user.get('role')}")
    
    # Test nurse shift clock-in
    print("\n3. Testing Nurse Shift Clock-In")
    clock_in_data = {
        "shift_type": "morning"
    }
    
    response = test_endpoint('POST', f"{base_url}/nurse/shifts/clock-in", clock_in_data, headers)
    
    if response and response.status_code == 200:
        print("✅ Clock-in successful")
        
        # Test get current shift
        print("\n4. Testing Get Current Shift")
        response = test_endpoint('GET', f"{base_url}/nurse/current-shift", None, headers)
        
        if response and response.status_code == 200:
            print("✅ Get current shift successful")
            
            # Test clock-out
            print("\n5. Testing Nurse Shift Clock-Out")
            response = test_endpoint('POST', f"{base_url}/nurse/shifts/clock-out", None, headers)
            
            if response and response.status_code == 200:
                print("✅ Clock-out successful")
                print("\n🎉 All nurse shift management tests passed!")
            else:
                print("❌ Clock-out failed")
        else:
            print("❌ Get current shift failed")
    else:
        print("❌ Clock-in failed")

if __name__ == "__main__":
    main()