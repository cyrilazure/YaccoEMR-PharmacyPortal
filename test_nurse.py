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
    base_url = "https://medrecords-gh.preview.emergentagent.com/api"
    
    print("🧪 Testing Nurse Shift Management")
    print("=" * 60)
    
    # First, try to login as the test nurse
    print("\n1. Testing Nurse Login")
    login_data = {
        "email": "testnurse@hospital.com",
        "password": "test123"
    }
    
    response = test_endpoint('POST', f"{base_url}/auth/login", login_data)
    
    if response and response.status_code == 200:
        data = response.json()
        nurse_token = data.get('token')
        user = data.get('user', {})
        
        print(f"✅ Nurse login successful")
        print(f"Role: {user.get('role')}")
        
        headers = {'Authorization': f'Bearer {nurse_token}', 'Content-Type': 'application/json'}
        
        # Test nurse shift clock-in
        print("\n2. Testing Nurse Shift Clock-In")
        clock_in_data = {
            "shift_type": "morning"
        }
        
        response = test_endpoint('POST', f"{base_url}/nurse/shifts/clock-in", clock_in_data, headers)
        
        if response and response.status_code == 200:
            print("✅ Clock-in successful")
            
            # Test get current shift
            print("\n3. Testing Get Current Shift")
            response = test_endpoint('GET', f"{base_url}/nurse/current-shift", None, headers)
            
            if response and response.status_code == 200:
                print("✅ Get current shift successful")
                
                # Test clock-out
                print("\n4. Testing Nurse Shift Clock-Out")
                response = test_endpoint('POST', f"{base_url}/nurse/shifts/clock-out", None, headers)
                
                if response and response.status_code == 200:
                    print("✅ Clock-out successful")
                else:
                    print("❌ Clock-out failed")
            else:
                print("❌ Get current shift failed")
        else:
            print("❌ Clock-in failed")
    
    elif response and response.status_code == 401:
        print("❌ Nurse login failed - user doesn't exist or wrong credentials")
        
        # Try to create nurse user first
        print("\n1b. Creating Nurse User")
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
            # Now try the login again
            main()
        elif response and response.status_code == 400:
            print("ℹ️ Nurse user already exists, but login failed - check credentials")
        else:
            print("❌ Failed to create nurse user")
    
    else:
        print("❌ Nurse login failed with unexpected error")

if __name__ == "__main__":
    main()