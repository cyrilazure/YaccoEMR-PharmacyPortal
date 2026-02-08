#!/usr/bin/env python
"""
Check IT Admin user role and permissions
"""

import requests
import json

def check_user_role():
    base_url = "https://unified-health-8.preview.emergentagent.com/api"
    
    # Login as IT Admin
    login_data = {
        "email": "kofiabedu2019@gmail.com",
        "password": "2I6ZRBkjVn2ZQg7O",
        "hospital_id": "e717ed11-7955-4884-8d6b-a529f918c34f",
        "location_id": "b61d7896-b4ef-436b-868e-94a60b55c64c"
    }
    
    response = requests.post(f"{base_url}/regions/auth/login", json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        print("Login successful!")
        print(f"User data: {json.dumps(data, indent=2)}")
        
        # Get user profile
        token = data.get('token')
        headers = {"Authorization": f"Bearer {token}"}
        
        profile_response = requests.get(f"{base_url}/regions/auth/me", headers=headers)
        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            print(f"\nUser profile: {json.dumps(profile_data, indent=2)}")
        else:
            print(f"Failed to get profile: {profile_response.status_code} - {profile_response.text}")
    else:
        print(f"Login failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    check_user_role()