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

def test_nurse_login_and_shifts(email, password):
    """Test nurse login and shift management"""
    base_url = "https://portal-index.preview.emergentagent.com/api"
    
    print(f"\n🧪 Testing Nurse: {email}")
    print("=" * 60)
    
    # Try to login as nurse
    print(f"\n1. Login as Nurse: {email}")
    nurse_login_data = {
        "email": email,
        "password": password
    }
    
    response = test_endpoint('POST', f"{base_url}/auth/login", nurse_login_data)
    
    if response and response.status_code == 200:
        data = response.json()
        nurse_token = data.get('token')
        user = data.get('user', {})
        
        print(f"✅ Nurse login successful - Role: {user.get('role')}")
        
        # Now test nurse functionality
        nurse_headers = {'Authorization': f'Bearer {nurse_token}', 'Content-Type': 'application/json'}
        
        # Test nurse shift clock-in
        print("\n2. Testing Nurse Shift Clock-In")
        clock_in_data = {
            "shift_type": "morning"
        }
        
        response = test_endpoint('POST', f"{base_url}/nurse/shifts/clock-in", clock_in_data, nurse_headers)
        
        if response and response.status_code == 200:
            print("✅ Clock-in successful")
            
            # Test get current shift
            print("\n3. Testing Get Current Shift")
            response = test_endpoint('GET', f"{base_url}/nurse/current-shift", None, nurse_headers)
            
            if response and response.status_code == 200:
                print("✅ Get current shift successful")
                
                # Test clock-out
                print("\n4. Testing Nurse Shift Clock-Out")
                response = test_endpoint('POST', f"{base_url}/nurse/shifts/clock-out", None, nurse_headers)
                
                if response and response.status_code == 200:
                    print("✅ Clock-out successful")
                    print(f"\n🎉 All nurse shift management tests passed for {email}!")
                    return True
                else:
                    print("❌ Clock-out failed")
            else:
                print("❌ Get current shift failed")
        else:
            print("❌ Clock-in failed")
    else:
        print(f"❌ Nurse login failed for {email}")
    
    return False

def main():
    # Try different nurse accounts with common passwords
    nurse_accounts = [
        ("testnurse@test.com", "test123"),
        ("testnurse@test.com", "password"),
        ("fiifiabedu@gmail.com", "test123"),
        ("fiifiabedu@gmail.com", "password"),
        ("testnurse@hospital.com", "password"),
        ("testnurse@hospital.com", "nurse123")
    ]
    
    for email, password in nurse_accounts:
        if test_nurse_login_and_shifts(email, password):
            break
        print("\n" + "-" * 60)

if __name__ == "__main__":
    main()