#!/usr/bin/env python3
"""Script to fix ward/bed organization_id and re-seed for the correct hospital"""

import requests
import json
import os
from pymongo import MongoClient

# Get backend URL from .env
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=')[1]
            break

# Get MongoDB connection
with open('/app/backend/.env', 'r') as f:
    env_vars = {}
    for line in f:
        if '=' in line and not line.startswith('#'):
            key, value = line.strip().split('=', 1)
            env_vars[key] = value

mongo_url = env_vars.get('MONGO_URL')
db_name = env_vars.get('DB_NAME')

client = MongoClient(mongo_url)
db = client[db_name]

print(f"Backend URL: {BACKEND_URL}")
print(f"MongoDB: {db_name}")
print()

# Get the correct hospital ID and organization ID
response = requests.get(f"{BACKEND_URL}/api/regions/greater-accra/hospitals")
hospitals = response.json().get('hospitals', [])

if not hospitals:
    print("❌ No hospitals found!")
    exit(1)

hospital = hospitals[0]
hospital_id = hospital['id']
print(f"Hospital: {hospital['name']}")
print(f"Hospital ID: {hospital_id}")
print()

# Delete existing wards with null organization_id
result = db.wards.delete_many({"organization_id": None})
print(f"Deleted {result.deleted_count} wards with null organization_id")

# Delete existing beds with null organization_id
result = db.beds.delete_many({"organization_id": None})
print(f"Deleted {result.deleted_count} beds with null organization_id")

# Delete existing rooms with null organization_id
result = db.rooms.delete_many({"organization_id": None})
print(f"Deleted {result.deleted_count} rooms with null organization_id")

print()
print("Now logging in with bed_manager to seed wards...")

# Login as bed manager
login_response = requests.post(
    f"{BACKEND_URL}/api/auth/login",
    json={"email": "bed_manager@yacco.health", "password": "test123"}
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.text}")
    exit(1)

token = login_response.json()['token']
user = login_response.json()['user']
headers = {"Authorization": f"Bearer {token}"}

print(f"✅ Logged in as {user['email']}")
print(f"   Organization ID: {user.get('organization_id')}")
print()

# Seed default wards
seed_response = requests.post(
    f"{BACKEND_URL}/api/beds/wards/seed-defaults",
    headers=headers
)

if seed_response.status_code == 200:
    result = seed_response.json()
    print(f"✅ {result['message']}")
    print(f"   Created: {result.get('count', 0)} wards")
else:
    print(f"❌ Seed failed: {seed_response.text}")
    exit(1)

print()
print("Seeding beds for all wards...")

# Get all wards
wards_response = requests.get(f"{BACKEND_URL}/api/beds/wards", headers=headers)
wards = wards_response.json()['wards']

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
        print(f"  ✅ {ward_name}: {rooms_created} rooms, {beds_created} beds")
    else:
        print(f"  ❌ {ward_name}: Error - {bulk_response.text}")

print()
print(f"🏥 SEEDING COMPLETE")
print(f"Total rooms: {total_rooms_created}")
print(f"Total beds: {total_beds_created}")

# Final verification
census_response = requests.get(f"{BACKEND_URL}/api/beds/census", headers=headers)
census = census_response.json()
print()
print(f"📊 Final Census:")
print(f"Total beds: {census['summary']['total_beds']}")
print(f"Available: {census['summary']['available']}")
