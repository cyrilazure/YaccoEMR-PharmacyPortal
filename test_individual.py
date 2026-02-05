#!/usr/bin/env python3

import requests
import json
import jwt

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
    base_url = "https://careflow-183.preview.emergentagent.com/api"
    
    print("🧪 Testing Yacco EMR Backend - Review Request")
    print("=" * 60)
    
    # Test 1: Super Admin Login
    print("\n1. Testing Super Admin Login")
    login_data = {
        "email": "ygtnetworks@gmail.com",
        "password": "test123"
    }
    
    response = test_endpoint('POST', f"{base_url}/auth/login", login_data)
    
    if response and response.status_code == 200:
        data = response.json()
        token = data.get('token')
        user = data.get('user', {})
        
        print(f"✅ Login successful")
        print(f"Role: {user.get('role')}")
        
        # Verify JWT token
        if token:
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
                print(f"JWT Role: {payload.get('role')}")
            except Exception as e:
                print(f"JWT decode error: {e}")
        
        # Test 2: Patient Creation with MRN and Payment
        print("\n2. Testing Patient Creation with MRN and Payment")
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        
        patient_data = {
            "first_name": "Test",
            "last_name": "Patient",
            "date_of_birth": "1990-01-15",
            "gender": "male",
            "mrn": "MRN-CUSTOM-001",
            "payment_type": "insurance",
            "insurance_provider": "NHIS",
            "insurance_id": "NHIS-12345678",
            "adt_notification": True
        }
        
        response = test_endpoint('POST', f"{base_url}/patients", patient_data, headers)
        
        if response and response.status_code == 200:
            print("✅ Patient creation with MRN successful")
        else:
            print("❌ Patient creation with MRN failed")
        
        # Test 3: Patient Creation with Cash Payment
        print("\n3. Testing Patient Creation with Cash Payment")
        
        cash_patient_data = {
            "first_name": "Cash",
            "last_name": "Patient",
            "date_of_birth": "1985-06-20",
            "gender": "female",
            "payment_type": "cash",
            "adt_notification": True
        }
        
        response = test_endpoint('POST', f"{base_url}/patients", cash_patient_data, headers)
        
        if response and response.status_code == 200:
            print("✅ Cash patient creation successful")
        else:
            print("❌ Cash patient creation failed")
        
        # Test 4: Check if nurse endpoints exist
        print("\n4. Testing Nurse Endpoints Availability")
        
        # Try to access nurse endpoints (should fail without proper auth)
        response = test_endpoint('GET', f"{base_url}/nurse/current-shift", None, headers)
        
        if response:
            if response.status_code == 404:
                print("❌ Nurse endpoints not found - nurse module may not be implemented")
            elif response.status_code == 401 or response.status_code == 403:
                print("✅ Nurse endpoints exist but require proper nurse authentication")
            else:
                print(f"ℹ️ Nurse endpoint response: {response.status_code}")
        
    else:
        print("❌ Super Admin login failed")

if __name__ == "__main__":
    main()