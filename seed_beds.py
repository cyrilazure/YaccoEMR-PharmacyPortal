#!/usr/bin/env python3
"""Script to seed beds for all wards in the EMR system"""

import requests
import json
import os

# Get backend URL from .env
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1]
            break

print(f"Backend URL: {BACKEND_URL}")

# Login as super admin
login_response = requests.post(
    f"{BACKEND_URL}/api/auth/login",
    json={"email": "ygtnetworks@gmail.com", "password": "test123"}
)
token = login_response.json()['token']
headers = {"Authorization": f"Bearer {token}"}

# Get all wards
wards_response = requests.get(f"{BACKEND_URL}/api/beds/wards", headers=headers)
wards = wards_response.json()['wards']

print(f"\nFound {len(wards)} wards. Seeding beds...\n")

# Define bed configuration per ward type
ward_configs = {
    'emergency': {'rooms': 10, 'beds_per_room': 2, 'prefix': 'ER'},
    'general': {'rooms': 15, 'beds_per_room': 4, 'prefix': 'GW'},
    'icu': {'rooms': 8, 'beds_per_room': 1, 'prefix': 'ICU'},
    'ccu': {'rooms': 6, 'beds_per_room': 1, 'prefix': 'CCU'},
    'micu': {'rooms': 6, 'beds_per_room': 1, 'prefix': 'MICU'},
    'sicu': {'rooms': 6, 'beds_per_room': 1, 'prefix': 'SICU'},
    'nicu': {'rooms': 10, 'beds_per_room': 2, 'prefix': 'NICU'},
    'pediatric': {'rooms': 12, 'beds_per_room': 4, 'prefix': 'PED'},
    'maternity': {'rooms': 10, 'beds_per_room': 2, 'prefix': 'MAT'},
    'surgical': {'rooms': 12, 'beds_per_room': 4, 'prefix': 'SUR'},
    'orthopedic': {'rooms': 8, 'beds_per_room': 4, 'prefix': 'ORT'},
    'isolation': {'rooms': 6, 'beds_per_room': 1, 'prefix': 'ISO'},
    'private': {'rooms': 20, 'beds_per_room': 1, 'prefix': 'PVT'},
    'oncology': {'rooms': 8, 'beds_per_room': 4, 'prefix': 'ONC'},
    'psychiatric': {'rooms': 10, 'beds_per_room': 2, 'prefix': 'PSY'},
}

total_beds_created = 0
total_rooms_created = 0

for ward in wards:
    ward_id = ward['id']
    ward_type = ward['ward_type']
    ward_name = ward['name']
    
    # Get configuration for this ward type
    config = ward_configs.get(ward_type, {'rooms': 10, 'beds_per_room': 2, 'prefix': 'RM'})
    
    # Call bulk create endpoint
    bulk_response = requests.post(
        f"{BACKEND_URL}/api/beds/beds/bulk-create",
        headers=headers,
        params={
            'ward_id': ward_id,
            'room_prefix': config['prefix'],
            'beds_per_room': config['beds_per_room'],
            'num_rooms': config['rooms']
        }
    )
    
    if bulk_response.status_code == 200:
        result = bulk_response.json()
        rooms_created = result['rooms_created']
        beds_created = result['beds_created']
        total_rooms_created += rooms_created
        total_beds_created += beds_created
        print(f"✅ {ward_name}: Created {rooms_created} rooms and {beds_created} beds")
    else:
        print(f"❌ {ward_name}: Error {bulk_response.status_code} - {bulk_response.text}")

print(f"\n🏥 SEEDING COMPLETE")
print(f"Total rooms created: {total_rooms_created}")
print(f"Total beds created: {total_beds_created}")

# Verify with census endpoint
census_response = requests.get(f"{BACKEND_URL}/api/beds/census", headers=headers)
census = census_response.json()
print(f"\n📊 Ward Census:")
print(f"Total beds: {census['summary']['total_beds']}")
print(f"Available: {census['summary']['available']}")
print(f"Occupied: {census['summary']['occupied']}")
