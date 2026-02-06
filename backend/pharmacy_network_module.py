"""
Ghana National Pharmacy Network Module
Comprehensive database of pharmacies across Ghana including:
- GHS (Ghana Health Service) Hospital Pharmacies
- Private Hospital Pharmacies
- Retail/Community Pharmacies
- Wholesale/Distribution Pharmacies
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from enum import Enum

pharmacy_network_router = APIRouter(prefix="/api/pharmacy-network", tags=["Pharmacy Network"])


# ============== Enums ==============

class OwnershipType(str, Enum):
    GHS = "ghs"  # Ghana Health Service (Government)
    PRIVATE_HOSPITAL = "private_hospital"
    RETAIL = "retail"  # Community/Retail Pharmacies
    WHOLESALE = "wholesale"
    CHAIN = "chain"  # Pharmacy Chains (Ernest Chemist, mPharma, etc.)
    MISSION = "mission"  # Mission/Religious Hospital Pharmacies
    QUASI_GOVERNMENT = "quasi_government"  # SSNIT, Military, Police, etc.


class PharmacyStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class PharmacyTier(str, Enum):
    TIER_1 = "tier_1"  # 24/7 service, full stock
    TIER_2 = "tier_2"  # Standard hours, good stock
    TIER_3 = "tier_3"  # Limited hours/stock


class Region(str, Enum):
    GREATER_ACCRA = "Greater Accra"
    ASHANTI = "Ashanti"
    WESTERN = "Western"
    CENTRAL = "Central"
    EASTERN = "Eastern"
    VOLTA = "Volta"
    NORTHERN = "Northern"
    UPPER_EAST = "Upper East"
    UPPER_WEST = "Upper West"
    BONO = "Bono"
    BONO_EAST = "Bono East"
    AHAFO = "Ahafo"
    WESTERN_NORTH = "Western North"
    OTI = "Oti"
    SAVANNAH = "Savannah"
    NORTH_EAST = "North East"


# ============== Pydantic Models ==============

class PharmacyBase(BaseModel):
    name: str
    ownership_type: OwnershipType
    region: Region
    city: str
    address: str
    phone: str
    email: Optional[str] = None
    operating_hours: Optional[str] = None
    tier: PharmacyTier = PharmacyTier.TIER_2
    has_nhis: bool = True  # NHIS accredited
    has_delivery: bool = False
    has_24hr_service: bool = False
    coordinates: Optional[dict] = None  # {lat: float, lng: float}
    license_number: Optional[str] = None
    parent_facility: Optional[str] = None  # For hospital pharmacies


class PharmacyCreate(PharmacyBase):
    pass


class PharmacyResponse(PharmacyBase):
    id: str
    status: PharmacyStatus
    created_at: str
    prescription_count: int = 0
    rating: float = 0.0


class PharmacySearchParams(BaseModel):
    query: Optional[str] = None
    region: Optional[Region] = None
    city: Optional[str] = None
    ownership_type: Optional[OwnershipType] = None
    has_nhis: Optional[bool] = None
    has_24hr_service: Optional[bool] = None
    has_delivery: Optional[bool] = None


# ============== Comprehensive Ghana Pharmacy Database ==============

SEED_PHARMACIES = [
    # ==========================================
    # GREATER ACCRA REGION
    # ==========================================
    
    # --- GHS Hospital Pharmacies (Greater Accra) ---
    {
        "id": "GHS-GA-001",
        "name": "Korle Bu Teaching Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Guggisberg Avenue, Korle Bu",
        "phone": "0302-665401",
        "operating_hours": "24 Hours",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_24hr_service": True,
        "parent_facility": "Korle Bu Teaching Hospital",
        "license_number": "GHS/PHARM/001"
    },
    {
        "id": "GHS-GA-002",
        "name": "Ridge Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Castle Road, Ridge",
        "phone": "0302-228315",
        "operating_hours": "24 Hours",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_24hr_service": True,
        "parent_facility": "Greater Accra Regional Hospital (Ridge)",
        "license_number": "GHS/PHARM/002"
    },
    {
        "id": "GHS-GA-003",
        "name": "La General Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "La, Accra",
        "phone": "0302-774430",
        "operating_hours": "Mon-Fri 8AM-5PM, Sat 8AM-1PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "La General Hospital",
        "license_number": "GHS/PHARM/003"
    },
    {
        "id": "GHS-GA-004",
        "name": "Tema General Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.GREATER_ACCRA,
        "city": "Tema",
        "address": "Community 1, Tema",
        "phone": "0303-202721",
        "operating_hours": "24 Hours",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_24hr_service": True,
        "parent_facility": "Tema General Hospital",
        "license_number": "GHS/PHARM/004"
    },
    {
        "id": "GHS-GA-005",
        "name": "Achimota Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Achimota",
        "phone": "0302-401234",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Achimota Hospital",
        "license_number": "GHS/PHARM/005"
    },
    {
        "id": "GHS-GA-006",
        "name": "Mamprobi Polyclinic Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Mamprobi, Accra",
        "phone": "0302-228790",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_3,
        "has_nhis": True,
        "parent_facility": "Mamprobi Polyclinic",
        "license_number": "GHS/PHARM/006"
    },
    {
        "id": "GHS-GA-007",
        "name": "Kaneshie Polyclinic Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Kaneshie, Accra",
        "phone": "0302-223456",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Kaneshie Polyclinic",
        "license_number": "GHS/PHARM/007"
    },
    {
        "id": "GHS-GA-008",
        "name": "Dansoman Polyclinic Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Dansoman, Accra",
        "phone": "0302-310234",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Dansoman Polyclinic",
        "license_number": "GHS/PHARM/008"
    },
    {
        "id": "GHS-GA-009",
        "name": "Ashaiman Polyclinic Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.GREATER_ACCRA,
        "city": "Ashaiman",
        "address": "Ashaiman Township",
        "phone": "0303-300456",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Ashaiman Polyclinic",
        "license_number": "GHS/PHARM/009"
    },
    {
        "id": "GHS-GA-010",
        "name": "Madina Polyclinic Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Madina, Accra",
        "phone": "0302-520890",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Madina Polyclinic",
        "license_number": "GHS/PHARM/010"
    },
    
    # --- Quasi-Government Hospital Pharmacies (Greater Accra) ---
    {
        "id": "QG-GA-001",
        "name": "37 Military Hospital Pharmacy",
        "ownership_type": OwnershipType.QUASI_GOVERNMENT,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Liberation Road, Accra",
        "phone": "0302-777021",
        "operating_hours": "24 Hours",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_24hr_service": True,
        "parent_facility": "37 Military Hospital",
        "license_number": "MOD/PHARM/001"
    },
    {
        "id": "QG-GA-002",
        "name": "Police Hospital Pharmacy",
        "ownership_type": OwnershipType.QUASI_GOVERNMENT,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Cantonments, Accra",
        "phone": "0302-776481",
        "operating_hours": "24 Hours",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_24hr_service": True,
        "parent_facility": "Police Hospital",
        "license_number": "GPS/PHARM/001"
    },
    {
        "id": "QG-GA-003",
        "name": "SSNIT Hospital Pharmacy",
        "ownership_type": OwnershipType.QUASI_GOVERNMENT,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Ring Road East, Accra",
        "phone": "0302-783567",
        "operating_hours": "Mon-Fri 8AM-6PM, Sat 8AM-2PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "SSNIT Hospital",
        "license_number": "SSNIT/PHARM/001"
    },
    {
        "id": "QG-GA-004",
        "name": "University of Ghana Hospital Pharmacy",
        "ownership_type": OwnershipType.QUASI_GOVERNMENT,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Legon, Accra",
        "phone": "0302-500381",
        "operating_hours": "Mon-Fri 8AM-8PM, Sat 8AM-4PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "parent_facility": "University of Ghana Hospital",
        "license_number": "UG/PHARM/001"
    },
    
    # --- Private Hospital Pharmacies (Greater Accra) ---
    {
        "id": "PVT-GA-001",
        "name": "Nyaho Medical Centre Pharmacy - Airport",
        "ownership_type": OwnershipType.PRIVATE_HOSPITAL,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Airport Residential Area, Accra",
        "phone": "0302-784625",
        "email": "pharmacy@nyahomedical.com",
        "operating_hours": "24 Hours",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_24hr_service": True,
        "has_delivery": True,
        "parent_facility": "Nyaho Medical Centre",
        "license_number": "PVT/PHARM/GA/001"
    },
    {
        "id": "PVT-GA-002",
        "name": "Nyaho Medical Centre Pharmacy - Tema",
        "ownership_type": OwnershipType.PRIVATE_HOSPITAL,
        "region": Region.GREATER_ACCRA,
        "city": "Tema",
        "address": "Community 2, Tema",
        "phone": "0303-212345",
        "email": "tema@nyahomedical.com",
        "operating_hours": "Mon-Sat 8AM-8PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_delivery": True,
        "parent_facility": "Nyaho Medical Centre Tema",
        "license_number": "PVT/PHARM/GA/002"
    },
    {
        "id": "PVT-GA-003",
        "name": "The Trust Hospital Pharmacy",
        "ownership_type": OwnershipType.PRIVATE_HOSPITAL,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Osu, Accra",
        "phone": "0302-761974",
        "email": "pharmacy@thetrusthospital.com",
        "operating_hours": "24 Hours",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_24hr_service": True,
        "parent_facility": "The Trust Hospital",
        "license_number": "PVT/PHARM/GA/003"
    },
    {
        "id": "PVT-GA-004",
        "name": "Lister Hospital Pharmacy",
        "ownership_type": OwnershipType.PRIVATE_HOSPITAL,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Airport Road, Accra",
        "phone": "0302-781239",
        "email": "pharmacy@listerhospital.com.gh",
        "operating_hours": "24 Hours",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_24hr_service": True,
        "parent_facility": "Lister Hospital",
        "license_number": "PVT/PHARM/GA/004"
    },
    {
        "id": "PVT-GA-005",
        "name": "Holy Trinity Medical Centre Pharmacy",
        "ownership_type": OwnershipType.PRIVATE_HOSPITAL,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "North Ridge, Accra",
        "phone": "0302-226172",
        "operating_hours": "Mon-Sat 8AM-8PM, Sun 10AM-4PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Holy Trinity Medical Centre",
        "license_number": "PVT/PHARM/GA/005"
    },
    {
        "id": "PVT-GA-006",
        "name": "Gicel Hospital Pharmacy",
        "ownership_type": OwnershipType.PRIVATE_HOSPITAL,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Haatso, Accra",
        "phone": "0302-546789",
        "operating_hours": "Mon-Sat 8AM-8PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Gicel Hospital",
        "license_number": "PVT/PHARM/GA/006"
    },
    {
        "id": "PVT-GA-007",
        "name": "Akai House Clinic Pharmacy",
        "ownership_type": OwnershipType.PRIVATE_HOSPITAL,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Airport Residential Area",
        "phone": "0302-773150",
        "operating_hours": "24 Hours",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_24hr_service": True,
        "parent_facility": "Akai House Clinic",
        "license_number": "PVT/PHARM/GA/007"
    },
    {
        "id": "PVT-GA-008",
        "name": "Tema Women's Hospital Pharmacy",
        "ownership_type": OwnershipType.PRIVATE_HOSPITAL,
        "region": Region.GREATER_ACCRA,
        "city": "Tema",
        "address": "Community 8, Tema",
        "phone": "0303-206789",
        "operating_hours": "24 Hours",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_24hr_service": True,
        "parent_facility": "Tema Women's Hospital",
        "license_number": "PVT/PHARM/GA/008"
    },
    
    # --- Ernest Chemist Chain (Greater Accra) ---
    {
        "id": "EC-GA-001",
        "name": "Ernest Chemist - Accra Mall",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Accra Mall, Tetteh Quarshie Interchange",
        "phone": "0302-818290",
        "email": "accramall@ernestchemist.com",
        "operating_hours": "Mon-Sat 9AM-9PM, Sun 11AM-7PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_delivery": True,
        "license_number": "EC/PHARM/001"
    },
    {
        "id": "EC-GA-002",
        "name": "Ernest Chemist - Osu Oxford Street",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Oxford Street, Osu",
        "phone": "0302-785643",
        "email": "osu@ernestchemist.com",
        "operating_hours": "Mon-Sat 8AM-9PM, Sun 10AM-6PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_delivery": True,
        "license_number": "EC/PHARM/002"
    },
    {
        "id": "EC-GA-003",
        "name": "Ernest Chemist - Ring Road Central",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Ring Road Central",
        "phone": "0302-234567",
        "email": "ringroad@ernestchemist.com",
        "operating_hours": "24 Hours",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_24hr_service": True,
        "has_delivery": True,
        "license_number": "EC/PHARM/003"
    },
    {
        "id": "EC-GA-004",
        "name": "Ernest Chemist - East Legon",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "American House, East Legon",
        "phone": "0302-517890",
        "email": "eastlegon@ernestchemist.com",
        "operating_hours": "Mon-Sat 8AM-10PM, Sun 9AM-8PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_delivery": True,
        "license_number": "EC/PHARM/004"
    },
    {
        "id": "EC-GA-005",
        "name": "Ernest Chemist - Spintex",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Spintex Road",
        "phone": "0302-812345",
        "email": "spintex@ernestchemist.com",
        "operating_hours": "Mon-Sat 8AM-9PM, Sun 10AM-6PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_delivery": True,
        "license_number": "EC/PHARM/005"
    },
    {
        "id": "EC-GA-006",
        "name": "Ernest Chemist - Tema Community 1",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.GREATER_ACCRA,
        "city": "Tema",
        "address": "Community 1, Tema",
        "phone": "0303-203456",
        "email": "tema@ernestchemist.com",
        "operating_hours": "Mon-Sat 8AM-9PM, Sun 10AM-6PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_delivery": True,
        "license_number": "EC/PHARM/006"
    },
    {
        "id": "EC-GA-007",
        "name": "Ernest Chemist - Dansoman",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Dansoman High Street",
        "phone": "0302-313456",
        "email": "dansoman@ernestchemist.com",
        "operating_hours": "Mon-Sat 8AM-9PM, Sun 10AM-6PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "has_delivery": True,
        "license_number": "EC/PHARM/007"
    },
    {
        "id": "EC-GA-008",
        "name": "Ernest Chemist - Madina",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Madina Market Road",
        "phone": "0302-526789",
        "email": "madina@ernestchemist.com",
        "operating_hours": "Mon-Sat 8AM-9PM, Sun 10AM-6PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "has_delivery": True,
        "license_number": "EC/PHARM/008"
    },
    {
        "id": "EC-GA-009",
        "name": "Ernest Chemist - Lapaz",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Lapaz, Accra",
        "phone": "0302-419876",
        "operating_hours": "Mon-Sat 8AM-9PM, Sun 10AM-6PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "license_number": "EC/PHARM/009"
    },
    {
        "id": "EC-GA-010",
        "name": "Ernest Chemist - Achimota Mall",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Achimota Mall",
        "phone": "0302-405678",
        "email": "achimotamall@ernestchemist.com",
        "operating_hours": "Mon-Sat 9AM-9PM, Sun 11AM-7PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_delivery": True,
        "license_number": "EC/PHARM/010"
    },
    
    # --- mPharma Chain (Greater Accra) ---
    {
        "id": "MP-GA-001",
        "name": "mPharma - Airport Residential",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Airport Residential Area",
        "phone": "0302-785000",
        "email": "airport@mpharma.com",
        "operating_hours": "Mon-Sat 8AM-9PM, Sun 10AM-6PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_delivery": True,
        "license_number": "MP/PHARM/001"
    },
    {
        "id": "MP-GA-002",
        "name": "mPharma - Osu",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Osu, Oxford Street",
        "phone": "0302-786111",
        "email": "osu@mpharma.com",
        "operating_hours": "Mon-Sat 8AM-9PM, Sun 10AM-6PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_delivery": True,
        "license_number": "MP/PHARM/002"
    },
    {
        "id": "MP-GA-003",
        "name": "mPharma - Dzorwulu",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Dzorwulu, Accra",
        "phone": "0302-787222",
        "email": "dzorwulu@mpharma.com",
        "operating_hours": "Mon-Sat 8AM-8PM, Sun 10AM-5PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_delivery": True,
        "license_number": "MP/PHARM/003"
    },
    {
        "id": "MP-GA-004",
        "name": "mPharma - Spintex",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Spintex Road, Accra",
        "phone": "0302-788333",
        "email": "spintex@mpharma.com",
        "operating_hours": "Mon-Sat 8AM-8PM, Sun 10AM-5PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_delivery": True,
        "license_number": "MP/PHARM/004"
    },
    {
        "id": "MP-GA-005",
        "name": "mPharma - Tema",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.GREATER_ACCRA,
        "city": "Tema",
        "address": "Community 11, Tema",
        "phone": "0303-209444",
        "email": "tema@mpharma.com",
        "operating_hours": "Mon-Sat 8AM-8PM, Sun 10AM-5PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_delivery": True,
        "license_number": "MP/PHARM/005"
    },
    
    # --- Kinapharma Chain (Greater Accra) ---
    {
        "id": "KP-GA-001",
        "name": "Kinapharma - Spintex",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Spintex Road",
        "phone": "0302-815000",
        "email": "spintex@kinapharma.com",
        "operating_hours": "Mon-Sat 8AM-9PM, Sun 10AM-6PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_delivery": True,
        "license_number": "KP/PHARM/001"
    },
    {
        "id": "KP-GA-002",
        "name": "Kinapharma - Achimota",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Achimota, Accra",
        "phone": "0302-407890",
        "email": "achimota@kinapharma.com",
        "operating_hours": "Mon-Sat 8AM-8PM, Sun 10AM-5PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_delivery": True,
        "license_number": "KP/PHARM/002"
    },
    {
        "id": "KP-GA-003",
        "name": "Kinapharma - Circle",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Kwame Nkrumah Circle",
        "phone": "0302-251234",
        "email": "circle@kinapharma.com",
        "operating_hours": "Mon-Sat 8AM-8PM, Sun 10AM-5PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "license_number": "KP/PHARM/003"
    },
    {
        "id": "KP-GA-004",
        "name": "Kinapharma - Tema Community 25",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.GREATER_ACCRA,
        "city": "Tema",
        "address": "Community 25, Tema",
        "phone": "0303-305678",
        "email": "tema25@kinapharma.com",
        "operating_hours": "Mon-Sat 8AM-8PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "license_number": "KP/PHARM/004"
    },
    
    # --- Other Retail Pharmacies (Greater Accra) ---
    {
        "id": "RT-GA-001",
        "name": "Starcare Pharmacy - Tema",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.GREATER_ACCRA,
        "city": "Tema",
        "address": "Community 1, Tema",
        "phone": "0303-204567",
        "operating_hours": "Mon-Sat 8AM-9PM, Sun 10AM-6PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "license_number": "RT/PHARM/GA/001"
    },
    {
        "id": "RT-GA-002",
        "name": "Tobinco Pharmacy - Madina",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Madina Market",
        "phone": "0302-529012",
        "operating_hours": "Mon-Sat 7AM-9PM, Sun 9AM-6PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "license_number": "RT/PHARM/GA/002"
    },
    {
        "id": "RT-GA-003",
        "name": "Letap Pharmaceuticals - Kaneshie",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Kaneshie Market Road",
        "phone": "0302-224567",
        "operating_hours": "Mon-Sat 7AM-8PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "license_number": "RT/PHARM/GA/003"
    },
    {
        "id": "RT-GA-004",
        "name": "Care Pharmacy - East Legon",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "East Legon, Accra",
        "phone": "0302-518901",
        "operating_hours": "Mon-Sat 8AM-9PM, Sun 10AM-6PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "has_delivery": True,
        "license_number": "RT/PHARM/GA/004"
    },
    {
        "id": "RT-GA-005",
        "name": "Entrance Pharmacy - Ridge",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Ridge Hospital Area",
        "phone": "0302-228567",
        "operating_hours": "Mon-Sat 8AM-8PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "license_number": "RT/PHARM/GA/005"
    },
    {
        "id": "RT-GA-006",
        "name": "HealthPlus Pharmacy - Osu",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Osu, Accra",
        "phone": "0302-763456",
        "operating_hours": "Mon-Sat 8AM-10PM, Sun 10AM-6PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_delivery": True,
        "license_number": "RT/PHARM/GA/006"
    },
    {
        "id": "RT-GA-007",
        "name": "Lapaz Pharmacy",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Lapaz Station",
        "phone": "0302-419234",
        "operating_hours": "Mon-Sat 7AM-9PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "license_number": "RT/PHARM/GA/007"
    },
    {
        "id": "RT-GA-008",
        "name": "Kasoa Pharmacy",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.GREATER_ACCRA,
        "city": "Kasoa",
        "address": "Kasoa New Market",
        "phone": "0302-890123",
        "operating_hours": "Mon-Sat 7AM-8PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "license_number": "RT/PHARM/GA/008"
    },
    {
        "id": "RT-GA-009",
        "name": "Ashaiman Central Pharmacy",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.GREATER_ACCRA,
        "city": "Ashaiman",
        "address": "Ashaiman Market",
        "phone": "0303-301234",
        "operating_hours": "Mon-Sat 7AM-9PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "license_number": "RT/PHARM/GA/009"
    },
    {
        "id": "RT-GA-010",
        "name": "Nungua Pharmacy",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Nungua, Accra",
        "phone": "0302-716789",
        "operating_hours": "Mon-Sat 7AM-8PM",
        "tier": PharmacyTier.TIER_3,
        "has_nhis": True,
        "license_number": "RT/PHARM/GA/010"
    },
    
    # ==========================================
    # ASHANTI REGION
    # ==========================================
    
    # --- GHS Hospital Pharmacies (Ashanti) ---
    {
        "id": "GHS-AS-001",
        "name": "Komfo Anokye Teaching Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.ASHANTI,
        "city": "Kumasi",
        "address": "Bantama, Kumasi",
        "phone": "0322-022301",
        "operating_hours": "24 Hours",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_24hr_service": True,
        "parent_facility": "Komfo Anokye Teaching Hospital",
        "license_number": "GHS/PHARM/AS/001"
    },
    {
        "id": "GHS-AS-002",
        "name": "Okomfo Anokye Hospital Annex Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.ASHANTI,
        "city": "Kumasi",
        "address": "Adum, Kumasi",
        "phone": "0322-024567",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "KATH Annex",
        "license_number": "GHS/PHARM/AS/002"
    },
    {
        "id": "GHS-AS-003",
        "name": "Manhyia District Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.ASHANTI,
        "city": "Kumasi",
        "address": "Manhyia, Kumasi",
        "phone": "0322-028901",
        "operating_hours": "Mon-Fri 8AM-5PM, Sat 8AM-1PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Manhyia District Hospital",
        "license_number": "GHS/PHARM/AS/003"
    },
    {
        "id": "GHS-AS-004",
        "name": "Tafo Government Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.ASHANTI,
        "city": "Kumasi",
        "address": "Tafo, Kumasi",
        "phone": "0322-031234",
        "operating_hours": "24 Hours",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_24hr_service": True,
        "parent_facility": "Tafo Government Hospital",
        "license_number": "GHS/PHARM/AS/004"
    },
    {
        "id": "GHS-AS-005",
        "name": "Ejisu Government Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.ASHANTI,
        "city": "Ejisu",
        "address": "Ejisu Township",
        "phone": "0322-041234",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Ejisu Government Hospital",
        "license_number": "GHS/PHARM/AS/005"
    },
    {
        "id": "GHS-AS-006",
        "name": "Obuasi Government Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.ASHANTI,
        "city": "Obuasi",
        "address": "Obuasi Township",
        "phone": "0322-445678",
        "operating_hours": "24 Hours",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_24hr_service": True,
        "parent_facility": "Obuasi Government Hospital",
        "license_number": "GHS/PHARM/AS/006"
    },
    {
        "id": "GHS-AS-007",
        "name": "Mampong Government Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.ASHANTI,
        "city": "Mampong",
        "address": "Mampong Township",
        "phone": "0322-508901",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Mampong Government Hospital",
        "license_number": "GHS/PHARM/AS/007"
    },
    
    # --- Private Hospital Pharmacies (Ashanti) ---
    {
        "id": "PVT-AS-001",
        "name": "Kumasi South Hospital Pharmacy",
        "ownership_type": OwnershipType.PRIVATE_HOSPITAL,
        "region": Region.ASHANTI,
        "city": "Kumasi",
        "address": "Atonsu, Kumasi",
        "phone": "0322-039876",
        "operating_hours": "24 Hours",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_24hr_service": True,
        "parent_facility": "Kumasi South Hospital",
        "license_number": "PVT/PHARM/AS/001"
    },
    {
        "id": "PVT-AS-002",
        "name": "Ahodwo Specialist Hospital Pharmacy",
        "ownership_type": OwnershipType.PRIVATE_HOSPITAL,
        "region": Region.ASHANTI,
        "city": "Kumasi",
        "address": "Ahodwo, Kumasi",
        "phone": "0322-036789",
        "operating_hours": "Mon-Sat 8AM-8PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "parent_facility": "Ahodwo Specialist Hospital",
        "license_number": "PVT/PHARM/AS/002"
    },
    {
        "id": "PVT-AS-003",
        "name": "Angel Hospital Pharmacy",
        "ownership_type": OwnershipType.PRIVATE_HOSPITAL,
        "region": Region.ASHANTI,
        "city": "Kumasi",
        "address": "Santasi, Kumasi",
        "phone": "0322-034567",
        "operating_hours": "24 Hours",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_24hr_service": True,
        "parent_facility": "Angel Hospital",
        "license_number": "PVT/PHARM/AS/003"
    },
    
    # --- Chain Pharmacies (Ashanti) ---
    {
        "id": "EC-AS-001",
        "name": "Ernest Chemist - Adum",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.ASHANTI,
        "city": "Kumasi",
        "address": "Adum, Kumasi",
        "phone": "0322-026789",
        "email": "adum@ernestchemist.com",
        "operating_hours": "Mon-Sat 8AM-9PM, Sun 10AM-6PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_delivery": True,
        "license_number": "EC/PHARM/AS/001"
    },
    {
        "id": "EC-AS-002",
        "name": "Ernest Chemist - Bantama",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.ASHANTI,
        "city": "Kumasi",
        "address": "Bantama High Street",
        "phone": "0322-023456",
        "email": "bantama@ernestchemist.com",
        "operating_hours": "Mon-Sat 8AM-9PM, Sun 10AM-6PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_delivery": True,
        "license_number": "EC/PHARM/AS/002"
    },
    {
        "id": "EC-AS-003",
        "name": "Ernest Chemist - Asafo",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.ASHANTI,
        "city": "Kumasi",
        "address": "Asafo Market Area",
        "phone": "0322-045678",
        "email": "asafo@ernestchemist.com",
        "operating_hours": "Mon-Sat 8AM-9PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "license_number": "EC/PHARM/AS/003"
    },
    {
        "id": "MP-AS-001",
        "name": "mPharma - KNUST",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.ASHANTI,
        "city": "Kumasi",
        "address": "KNUST Campus, Kumasi",
        "phone": "0322-060123",
        "email": "knust@mpharma.com",
        "operating_hours": "Mon-Sat 8AM-8PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_delivery": True,
        "license_number": "MP/PHARM/AS/001"
    },
    {
        "id": "MP-AS-002",
        "name": "mPharma - Ahodwo",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.ASHANTI,
        "city": "Kumasi",
        "address": "Ahodwo, Kumasi",
        "phone": "0322-037890",
        "email": "ahodwo@mpharma.com",
        "operating_hours": "Mon-Sat 8AM-8PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_delivery": True,
        "license_number": "MP/PHARM/AS/002"
    },
    {
        "id": "KP-AS-001",
        "name": "Kinapharma - Bantama",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.ASHANTI,
        "city": "Kumasi",
        "address": "Bantama High Street",
        "phone": "0322-025678",
        "email": "bantama@kinapharma.com",
        "operating_hours": "Mon-Sat 8AM-8PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "license_number": "KP/PHARM/AS/001"
    },
    
    # --- Retail Pharmacies (Ashanti) ---
    {
        "id": "RT-AS-001",
        "name": "Tobinco Pharmacy - Asafo",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.ASHANTI,
        "city": "Kumasi",
        "address": "Asafo Market",
        "phone": "0322-048901",
        "operating_hours": "Mon-Sat 7AM-9PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "license_number": "RT/PHARM/AS/001"
    },
    {
        "id": "RT-AS-002",
        "name": "Kejetia Pharmacy",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.ASHANTI,
        "city": "Kumasi",
        "address": "Kejetia Market",
        "phone": "0322-021234",
        "operating_hours": "Mon-Sat 7AM-8PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "license_number": "RT/PHARM/AS/002"
    },
    {
        "id": "RT-AS-003",
        "name": "Suame Pharmacy",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.ASHANTI,
        "city": "Kumasi",
        "address": "Suame Magazine",
        "phone": "0322-054567",
        "operating_hours": "Mon-Sat 7AM-8PM",
        "tier": PharmacyTier.TIER_3,
        "has_nhis": True,
        "license_number": "RT/PHARM/AS/003"
    },
    {
        "id": "RT-AS-004",
        "name": "Obuasi Central Pharmacy",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.ASHANTI,
        "city": "Obuasi",
        "address": "Obuasi Town Center",
        "phone": "0322-447890",
        "operating_hours": "Mon-Sat 7AM-9PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "license_number": "RT/PHARM/AS/004"
    },
    
    # ==========================================
    # WESTERN REGION
    # ==========================================
    
    # --- GHS Hospital Pharmacies (Western) ---
    {
        "id": "GHS-WR-001",
        "name": "Effia Nkwanta Regional Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.WESTERN,
        "city": "Takoradi",
        "address": "Effia Nkwanta, Takoradi",
        "phone": "0312-022345",
        "operating_hours": "24 Hours",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_24hr_service": True,
        "parent_facility": "Effia Nkwanta Regional Hospital",
        "license_number": "GHS/PHARM/WR/001"
    },
    {
        "id": "GHS-WR-002",
        "name": "Takoradi Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.WESTERN,
        "city": "Takoradi",
        "address": "Takoradi Central",
        "phone": "0312-024567",
        "operating_hours": "Mon-Fri 8AM-5PM, Sat 8AM-1PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Takoradi Hospital",
        "license_number": "GHS/PHARM/WR/002"
    },
    {
        "id": "GHS-WR-003",
        "name": "Tarkwa Government Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.WESTERN,
        "city": "Tarkwa",
        "address": "Tarkwa Township",
        "phone": "0312-320123",
        "operating_hours": "24 Hours",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_24hr_service": True,
        "parent_facility": "Tarkwa Government Hospital",
        "license_number": "GHS/PHARM/WR/003"
    },
    {
        "id": "GHS-WR-004",
        "name": "Axim Government Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.WESTERN,
        "city": "Axim",
        "address": "Axim Township",
        "phone": "0312-420234",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Axim Government Hospital",
        "license_number": "GHS/PHARM/WR/004"
    },
    
    # --- Chain & Retail Pharmacies (Western) ---
    {
        "id": "EC-WR-001",
        "name": "Ernest Chemist - Takoradi Market Circle",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.WESTERN,
        "city": "Takoradi",
        "address": "Market Circle, Takoradi",
        "phone": "0312-023456",
        "email": "takoradi@ernestchemist.com",
        "operating_hours": "Mon-Sat 8AM-9PM, Sun 10AM-6PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_delivery": True,
        "license_number": "EC/PHARM/WR/001"
    },
    {
        "id": "RT-WR-001",
        "name": "Harbour Pharmacy - Takoradi",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.WESTERN,
        "city": "Takoradi",
        "address": "Harbour Area, Takoradi",
        "phone": "0312-028901",
        "operating_hours": "Mon-Sat 8AM-8PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "license_number": "RT/PHARM/WR/001"
    },
    {
        "id": "RT-WR-002",
        "name": "Sekondi Pharmacy",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.WESTERN,
        "city": "Sekondi",
        "address": "Sekondi Township",
        "phone": "0312-045678",
        "operating_hours": "Mon-Sat 8AM-7PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "license_number": "RT/PHARM/WR/002"
    },
    {
        "id": "RT-WR-003",
        "name": "Tarkwa Central Pharmacy",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.WESTERN,
        "city": "Tarkwa",
        "address": "Tarkwa Main Street",
        "phone": "0312-322345",
        "operating_hours": "Mon-Sat 7AM-9PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "license_number": "RT/PHARM/WR/003"
    },
    
    # ==========================================
    # CENTRAL REGION
    # ==========================================
    
    # --- GHS Hospital Pharmacies (Central) ---
    {
        "id": "GHS-CR-001",
        "name": "Cape Coast Teaching Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.CENTRAL,
        "city": "Cape Coast",
        "address": "University Post, Cape Coast",
        "phone": "0332-132567",
        "operating_hours": "24 Hours",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_24hr_service": True,
        "parent_facility": "Cape Coast Teaching Hospital",
        "license_number": "GHS/PHARM/CR/001"
    },
    {
        "id": "GHS-CR-002",
        "name": "Metropolitan Hospital Pharmacy - Cape Coast",
        "ownership_type": OwnershipType.GHS,
        "region": Region.CENTRAL,
        "city": "Cape Coast",
        "address": "Kotokuraba, Cape Coast",
        "phone": "0332-134567",
        "operating_hours": "Mon-Fri 8AM-5PM, Sat 8AM-1PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Cape Coast Metropolitan Hospital",
        "license_number": "GHS/PHARM/CR/002"
    },
    {
        "id": "GHS-CR-003",
        "name": "Winneba Municipal Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.CENTRAL,
        "city": "Winneba",
        "address": "Winneba Township",
        "phone": "0332-322456",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Winneba Municipal Hospital",
        "license_number": "GHS/PHARM/CR/003"
    },
    {
        "id": "GHS-CR-004",
        "name": "Saltpond Government Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.CENTRAL,
        "city": "Saltpond",
        "address": "Saltpond Township",
        "phone": "0332-420123",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Saltpond Government Hospital",
        "license_number": "GHS/PHARM/CR/004"
    },
    
    # --- Retail Pharmacies (Central) ---
    {
        "id": "RT-CR-001",
        "name": "Coastline Pharmacy - Cape Coast",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.CENTRAL,
        "city": "Cape Coast",
        "address": "Commercial Area, Cape Coast",
        "phone": "0332-136789",
        "operating_hours": "Mon-Sat 8AM-8PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "license_number": "RT/PHARM/CR/001"
    },
    {
        "id": "RT-CR-002",
        "name": "UCC Pharmacy",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.CENTRAL,
        "city": "Cape Coast",
        "address": "UCC Campus, Cape Coast",
        "phone": "0332-138901",
        "operating_hours": "Mon-Sat 8AM-7PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "license_number": "RT/PHARM/CR/002"
    },
    
    # ==========================================
    # EASTERN REGION
    # ==========================================
    
    # --- GHS Hospital Pharmacies (Eastern) ---
    {
        "id": "GHS-ER-001",
        "name": "Eastern Regional Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.EASTERN,
        "city": "Koforidua",
        "address": "Koforidua Central",
        "phone": "0342-022345",
        "operating_hours": "24 Hours",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_24hr_service": True,
        "parent_facility": "Eastern Regional Hospital",
        "license_number": "GHS/PHARM/ER/001"
    },
    {
        "id": "GHS-ER-002",
        "name": "Koforidua Government Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.EASTERN,
        "city": "Koforidua",
        "address": "Koforidua Township",
        "phone": "0342-024567",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Koforidua Government Hospital",
        "license_number": "GHS/PHARM/ER/002"
    },
    {
        "id": "GHS-ER-003",
        "name": "Nsawam Government Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.EASTERN,
        "city": "Nsawam",
        "address": "Nsawam Township",
        "phone": "0342-320456",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Nsawam Government Hospital",
        "license_number": "GHS/PHARM/ER/003"
    },
    {
        "id": "GHS-ER-004",
        "name": "Akropong Government Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.EASTERN,
        "city": "Akropong",
        "address": "Akropong Akuapem",
        "phone": "0342-420789",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Akropong Government Hospital",
        "license_number": "GHS/PHARM/ER/004"
    },
    
    # --- Retail Pharmacies (Eastern) ---
    {
        "id": "RT-ER-001",
        "name": "Koforidua Central Pharmacy",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.EASTERN,
        "city": "Koforidua",
        "address": "Koforidua Market Area",
        "phone": "0342-026789",
        "operating_hours": "Mon-Sat 7AM-9PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "license_number": "RT/PHARM/ER/001"
    },
    {
        "id": "EC-ER-001",
        "name": "Ernest Chemist - Koforidua",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.EASTERN,
        "city": "Koforidua",
        "address": "Koforidua Town",
        "phone": "0342-028901",
        "email": "koforidua@ernestchemist.com",
        "operating_hours": "Mon-Sat 8AM-8PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_delivery": True,
        "license_number": "EC/PHARM/ER/001"
    },
    
    # ==========================================
    # VOLTA REGION
    # ==========================================
    
    # --- GHS Hospital Pharmacies (Volta) ---
    {
        "id": "GHS-VR-001",
        "name": "Ho Teaching Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.VOLTA,
        "city": "Ho",
        "address": "Ho Municipal",
        "phone": "0362-026789",
        "operating_hours": "24 Hours",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_24hr_service": True,
        "parent_facility": "Ho Teaching Hospital",
        "license_number": "GHS/PHARM/VR/001"
    },
    {
        "id": "GHS-VR-002",
        "name": "Ho Municipal Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.VOLTA,
        "city": "Ho",
        "address": "Ho Township",
        "phone": "0362-028901",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Ho Municipal Hospital",
        "license_number": "GHS/PHARM/VR/002"
    },
    {
        "id": "GHS-VR-003",
        "name": "Keta Municipal Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.VOLTA,
        "city": "Keta",
        "address": "Keta Township",
        "phone": "0362-320456",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Keta Municipal Hospital",
        "license_number": "GHS/PHARM/VR/003"
    },
    {
        "id": "GHS-VR-004",
        "name": "Hohoe Municipal Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.VOLTA,
        "city": "Hohoe",
        "address": "Hohoe Township",
        "phone": "0362-420123",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Hohoe Municipal Hospital",
        "license_number": "GHS/PHARM/VR/004"
    },
    
    # --- Retail Pharmacies (Volta) ---
    {
        "id": "RT-VR-001",
        "name": "Ho Central Pharmacy",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.VOLTA,
        "city": "Ho",
        "address": "Ho Market Area",
        "phone": "0362-031234",
        "operating_hours": "Mon-Sat 7AM-8PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "license_number": "RT/PHARM/VR/001"
    },
    
    # ==========================================
    # NORTHERN REGION
    # ==========================================
    
    # --- GHS Hospital Pharmacies (Northern) ---
    {
        "id": "GHS-NR-001",
        "name": "Tamale Teaching Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.NORTHERN,
        "city": "Tamale",
        "address": "Tamale Central",
        "phone": "0372-022567",
        "operating_hours": "24 Hours",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_24hr_service": True,
        "parent_facility": "Tamale Teaching Hospital",
        "license_number": "GHS/PHARM/NR/001"
    },
    {
        "id": "GHS-NR-002",
        "name": "Tamale Central Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.NORTHERN,
        "city": "Tamale",
        "address": "Tamale Hospital Road",
        "phone": "0372-024789",
        "operating_hours": "Mon-Fri 8AM-5PM, Sat 8AM-1PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Tamale Central Hospital",
        "license_number": "GHS/PHARM/NR/002"
    },
    {
        "id": "GHS-NR-003",
        "name": "West Hospital Pharmacy - Tamale",
        "ownership_type": OwnershipType.GHS,
        "region": Region.NORTHERN,
        "city": "Tamale",
        "address": "West Hospital, Tamale",
        "phone": "0372-026901",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Tamale West Hospital",
        "license_number": "GHS/PHARM/NR/003"
    },
    {
        "id": "GHS-NR-004",
        "name": "Yendi Municipal Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.NORTHERN,
        "city": "Yendi",
        "address": "Yendi Township",
        "phone": "0372-320234",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Yendi Municipal Hospital",
        "license_number": "GHS/PHARM/NR/004"
    },
    
    # --- Retail Pharmacies (Northern) ---
    {
        "id": "RT-NR-001",
        "name": "Tamale Central Pharmacy",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.NORTHERN,
        "city": "Tamale",
        "address": "Tamale Main Market",
        "phone": "0372-028567",
        "operating_hours": "Mon-Sat 7AM-9PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "license_number": "RT/PHARM/NR/001"
    },
    {
        "id": "RT-NR-002",
        "name": "Northern Star Pharmacy",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.NORTHERN,
        "city": "Tamale",
        "address": "Tamale Market Area",
        "phone": "0372-031234",
        "operating_hours": "Mon-Sat 7AM-8PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "license_number": "RT/PHARM/NR/002"
    },
    {
        "id": "EC-NR-001",
        "name": "Ernest Chemist - Tamale",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.NORTHERN,
        "city": "Tamale",
        "address": "Tamale Central",
        "phone": "0372-033456",
        "email": "tamale@ernestchemist.com",
        "operating_hours": "Mon-Sat 8AM-8PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "license_number": "EC/PHARM/NR/001"
    },
    
    # ==========================================
    # UPPER EAST REGION
    # ==========================================
    
    # --- GHS Hospital Pharmacies (Upper East) ---
    {
        "id": "GHS-UE-001",
        "name": "Upper East Regional Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.UPPER_EAST,
        "city": "Bolgatanga",
        "address": "Bolgatanga Central",
        "phone": "0382-022456",
        "operating_hours": "24 Hours",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_24hr_service": True,
        "parent_facility": "Upper East Regional Hospital",
        "license_number": "GHS/PHARM/UE/001"
    },
    {
        "id": "GHS-UE-002",
        "name": "Bawku Presbyterian Hospital Pharmacy",
        "ownership_type": OwnershipType.MISSION,
        "region": Region.UPPER_EAST,
        "city": "Bawku",
        "address": "Bawku Township",
        "phone": "0382-320678",
        "operating_hours": "Mon-Sat 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Bawku Presbyterian Hospital",
        "license_number": "GHS/PHARM/UE/002"
    },
    {
        "id": "GHS-UE-003",
        "name": "Navrongo War Memorial Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.UPPER_EAST,
        "city": "Navrongo",
        "address": "Navrongo Township",
        "phone": "0382-420234",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Navrongo War Memorial Hospital",
        "license_number": "GHS/PHARM/UE/003"
    },
    
    # --- Retail Pharmacies (Upper East) ---
    {
        "id": "RT-UE-001",
        "name": "Bolgatanga Pharmacy",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.UPPER_EAST,
        "city": "Bolgatanga",
        "address": "Bolgatanga Market",
        "phone": "0382-024567",
        "operating_hours": "Mon-Sat 7AM-7PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "license_number": "RT/PHARM/UE/001"
    },
    
    # ==========================================
    # UPPER WEST REGION
    # ==========================================
    
    # --- GHS Hospital Pharmacies (Upper West) ---
    {
        "id": "GHS-UW-001",
        "name": "Upper West Regional Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.UPPER_WEST,
        "city": "Wa",
        "address": "Wa Central",
        "phone": "0392-022567",
        "operating_hours": "24 Hours",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_24hr_service": True,
        "parent_facility": "Upper West Regional Hospital",
        "license_number": "GHS/PHARM/UW/001"
    },
    {
        "id": "GHS-UW-002",
        "name": "Wa Municipal Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.UPPER_WEST,
        "city": "Wa",
        "address": "Wa Township",
        "phone": "0392-024789",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Wa Municipal Hospital",
        "license_number": "GHS/PHARM/UW/002"
    },
    {
        "id": "GHS-UW-003",
        "name": "Jirapa District Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.UPPER_WEST,
        "city": "Jirapa",
        "address": "Jirapa Township",
        "phone": "0392-320456",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Jirapa District Hospital",
        "license_number": "GHS/PHARM/UW/003"
    },
    
    # --- Retail Pharmacies (Upper West) ---
    {
        "id": "RT-UW-001",
        "name": "Wa Central Pharmacy",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.UPPER_WEST,
        "city": "Wa",
        "address": "Wa Market",
        "phone": "0392-026789",
        "operating_hours": "Mon-Sat 7AM-7PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "license_number": "RT/PHARM/UW/001"
    },
    
    # ==========================================
    # BONO REGION
    # ==========================================
    
    # --- GHS Hospital Pharmacies (Bono) ---
    {
        "id": "GHS-BR-001",
        "name": "Sunyani Regional Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.BONO,
        "city": "Sunyani",
        "address": "Sunyani Central",
        "phone": "0352-022567",
        "operating_hours": "24 Hours",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_24hr_service": True,
        "parent_facility": "Sunyani Regional Hospital",
        "license_number": "GHS/PHARM/BR/001"
    },
    {
        "id": "GHS-BR-002",
        "name": "Sunyani Municipal Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.BONO,
        "city": "Sunyani",
        "address": "Sunyani Township",
        "phone": "0352-024789",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Sunyani Municipal Hospital",
        "license_number": "GHS/PHARM/BR/002"
    },
    {
        "id": "GHS-BR-003",
        "name": "Berekum Holy Family Hospital Pharmacy",
        "ownership_type": OwnershipType.MISSION,
        "region": Region.BONO,
        "city": "Berekum",
        "address": "Berekum Township",
        "phone": "0352-320234",
        "operating_hours": "Mon-Sat 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Berekum Holy Family Hospital",
        "license_number": "GHS/PHARM/BR/003"
    },
    
    # --- Retail Pharmacies (Bono) ---
    {
        "id": "RT-BR-001",
        "name": "Sunyani Central Pharmacy",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.BONO,
        "city": "Sunyani",
        "address": "Sunyani Market",
        "phone": "0352-026789",
        "operating_hours": "Mon-Sat 7AM-8PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "license_number": "RT/PHARM/BR/001"
    },
    {
        "id": "EC-BR-001",
        "name": "Ernest Chemist - Sunyani",
        "ownership_type": OwnershipType.CHAIN,
        "region": Region.BONO,
        "city": "Sunyani",
        "address": "Sunyani Central",
        "phone": "0352-028901",
        "email": "sunyani@ernestchemist.com",
        "operating_hours": "Mon-Sat 8AM-8PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "license_number": "EC/PHARM/BR/001"
    },
    
    # ==========================================
    # BONO EAST REGION
    # ==========================================
    
    {
        "id": "GHS-BE-001",
        "name": "Techiman Holy Family Hospital Pharmacy",
        "ownership_type": OwnershipType.MISSION,
        "region": Region.BONO_EAST,
        "city": "Techiman",
        "address": "Techiman Township",
        "phone": "0352-522345",
        "operating_hours": "24 Hours",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": True,
        "has_24hr_service": True,
        "parent_facility": "Techiman Holy Family Hospital",
        "license_number": "GHS/PHARM/BE/001"
    },
    {
        "id": "GHS-BE-002",
        "name": "Techiman Municipal Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.BONO_EAST,
        "city": "Techiman",
        "address": "Techiman Central",
        "phone": "0352-524567",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Techiman Municipal Hospital",
        "license_number": "GHS/PHARM/BE/002"
    },
    {
        "id": "RT-BE-001",
        "name": "Techiman Market Pharmacy",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.BONO_EAST,
        "city": "Techiman",
        "address": "Techiman Market",
        "phone": "0352-526789",
        "operating_hours": "Mon-Sat 7AM-9PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "license_number": "RT/PHARM/BE/001"
    },
    
    # ==========================================
    # AHAFO REGION
    # ==========================================
    
    {
        "id": "GHS-AH-001",
        "name": "Goaso Municipal Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.AHAFO,
        "city": "Goaso",
        "address": "Goaso Township",
        "phone": "0352-720234",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Goaso Municipal Hospital",
        "license_number": "GHS/PHARM/AH/001"
    },
    {
        "id": "RT-AH-001",
        "name": "Goaso Central Pharmacy",
        "ownership_type": OwnershipType.RETAIL,
        "region": Region.AHAFO,
        "city": "Goaso",
        "address": "Goaso Market",
        "phone": "0352-722456",
        "operating_hours": "Mon-Sat 7AM-7PM",
        "tier": PharmacyTier.TIER_3,
        "has_nhis": True,
        "license_number": "RT/PHARM/AH/001"
    },
    
    # ==========================================
    # WESTERN NORTH REGION
    # ==========================================
    
    {
        "id": "GHS-WN-001",
        "name": "Sefwi Wiawso Government Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.WESTERN_NORTH,
        "city": "Sefwi Wiawso",
        "address": "Sefwi Wiawso Township",
        "phone": "0312-620345",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Sefwi Wiawso Government Hospital",
        "license_number": "GHS/PHARM/WN/001"
    },
    {
        "id": "GHS-WN-002",
        "name": "Bibiani Government Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.WESTERN_NORTH,
        "city": "Bibiani",
        "address": "Bibiani Township",
        "phone": "0312-622567",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Bibiani Government Hospital",
        "license_number": "GHS/PHARM/WN/002"
    },
    
    # ==========================================
    # OTI REGION
    # ==========================================
    
    {
        "id": "GHS-OT-001",
        "name": "Dambai Government Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.OTI,
        "city": "Dambai",
        "address": "Dambai Township",
        "phone": "0362-720234",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Dambai Government Hospital",
        "license_number": "GHS/PHARM/OT/001"
    },
    {
        "id": "GHS-OT-002",
        "name": "Jasikan Government Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.OTI,
        "city": "Jasikan",
        "address": "Jasikan Township",
        "phone": "0362-722456",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Jasikan Government Hospital",
        "license_number": "GHS/PHARM/OT/002"
    },
    
    # ==========================================
    # SAVANNAH REGION
    # ==========================================
    
    {
        "id": "GHS-SV-001",
        "name": "Damongo District Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.SAVANNAH,
        "city": "Damongo",
        "address": "Damongo Township",
        "phone": "0372-720345",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Damongo District Hospital",
        "license_number": "GHS/PHARM/SV/001"
    },
    {
        "id": "GHS-SV-002",
        "name": "Bole District Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.SAVANNAH,
        "city": "Bole",
        "address": "Bole Township",
        "phone": "0372-722567",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Bole District Hospital",
        "license_number": "GHS/PHARM/SV/002"
    },
    
    # ==========================================
    # NORTH EAST REGION
    # ==========================================
    
    {
        "id": "GHS-NE-001",
        "name": "Nalerigu Baptist Medical Centre Pharmacy",
        "ownership_type": OwnershipType.MISSION,
        "region": Region.NORTH_EAST,
        "city": "Nalerigu",
        "address": "Nalerigu Township",
        "phone": "0372-820234",
        "operating_hours": "Mon-Sat 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Nalerigu Baptist Medical Centre",
        "license_number": "GHS/PHARM/NE/001"
    },
    {
        "id": "GHS-NE-002",
        "name": "Gambaga Government Hospital Pharmacy",
        "ownership_type": OwnershipType.GHS,
        "region": Region.NORTH_EAST,
        "city": "Gambaga",
        "address": "Gambaga Township",
        "phone": "0372-822456",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_2,
        "has_nhis": True,
        "parent_facility": "Gambaga Government Hospital",
        "license_number": "GHS/PHARM/NE/002"
    },
    
    # ==========================================
    # WHOLESALE / DISTRIBUTION (National)
    # ==========================================
    
    {
        "id": "WS-001",
        "name": "Ernest Chemist Wholesale - Head Office",
        "ownership_type": OwnershipType.WHOLESALE,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Ring Road, Accra",
        "phone": "0302-999000",
        "email": "wholesale@ernestchemist.com",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": False,
        "license_number": "WS/PHARM/001"
    },
    {
        "id": "WS-002",
        "name": "Kinapharma Limited - Distribution",
        "ownership_type": OwnershipType.WHOLESALE,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "North Industrial Area",
        "phone": "0302-228800",
        "email": "distribution@kinapharma.com",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": False,
        "license_number": "WS/PHARM/002"
    },
    {
        "id": "WS-003",
        "name": "Tobinco Pharmaceuticals - Warehouse",
        "ownership_type": OwnershipType.WHOLESALE,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Tema Industrial Area",
        "phone": "0303-204500",
        "email": "warehouse@tobinco.com",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": False,
        "license_number": "WS/PHARM/003"
    },
    {
        "id": "WS-004",
        "name": "Letap Pharmaceuticals - Distribution Centre",
        "ownership_type": OwnershipType.WHOLESALE,
        "region": Region.GREATER_ACCRA,
        "city": "Accra",
        "address": "Spintex Road, Accra",
        "phone": "0302-815500",
        "email": "distribution@letap.com",
        "operating_hours": "Mon-Fri 8AM-5PM",
        "tier": PharmacyTier.TIER_1,
        "has_nhis": False,
        "license_number": "WS/PHARM/004"
    },
]


def create_pharmacy_network_endpoints(db, get_current_user):
    """Create pharmacy network API endpoints with database injection"""
    
    @pharmacy_network_router.get("/pharmacies")
    async def list_all_pharmacies(
        region: Optional[str] = Query(None, description="Filter by region"),
        city: Optional[str] = Query(None, description="Filter by city"),
        ownership_type: Optional[str] = Query(None, description="Filter by ownership type"),
        has_nhis: Optional[bool] = Query(None, description="Filter by NHIS accreditation"),
        has_24hr_service: Optional[bool] = Query(None, description="Filter by 24-hour service"),
        has_delivery: Optional[bool] = Query(None, description="Filter by delivery service"),
        tier: Optional[str] = Query(None, description="Filter by tier"),
        limit: int = Query(100, ge=1, le=500),
        offset: int = Query(0, ge=0)
    ):
        """List all pharmacies in the national database with filtering"""
        filtered = SEED_PHARMACIES.copy()
        
        if region:
            filtered = [p for p in filtered if p.get("region") and p["region"].value == region]
        if city:
            filtered = [p for p in filtered if city.lower() in p.get("city", "").lower()]
        if ownership_type:
            filtered = [p for p in filtered if p.get("ownership_type") and p["ownership_type"].value == ownership_type]
        if has_nhis is not None:
            filtered = [p for p in filtered if p.get("has_nhis") == has_nhis]
        if has_24hr_service is not None:
            filtered = [p for p in filtered if p.get("has_24hr_service") == has_24hr_service]
        if has_delivery is not None:
            filtered = [p for p in filtered if p.get("has_delivery") == has_delivery]
        if tier:
            filtered = [p for p in filtered if p.get("tier") and p["tier"].value == tier]
        
        # Convert enums to values for JSON response
        result = []
        for p in filtered[offset:offset + limit]:
            pharmacy_dict = {**p}
            if "ownership_type" in pharmacy_dict and hasattr(pharmacy_dict["ownership_type"], "value"):
                pharmacy_dict["ownership_type"] = pharmacy_dict["ownership_type"].value
            if "region" in pharmacy_dict and hasattr(pharmacy_dict["region"], "value"):
                pharmacy_dict["region"] = pharmacy_dict["region"].value
            if "tier" in pharmacy_dict and hasattr(pharmacy_dict["tier"], "value"):
                pharmacy_dict["tier"] = pharmacy_dict["tier"].value
            pharmacy_dict["status"] = "active"
            result.append(pharmacy_dict)
        
        return {
            "pharmacies": result,
            "total": len(filtered),
            "limit": limit,
            "offset": offset
        }
    
    @pharmacy_network_router.get("/pharmacies/search")
    async def search_pharmacies(
        q: str = Query(..., min_length=2, description="Search query"),
        region: Optional[str] = Query(None, description="Filter by region"),
        limit: int = Query(20, ge=1, le=100)
    ):
        """Search pharmacies by name, city, or address"""
        q_lower = q.lower()
        results = []
        
        for p in SEED_PHARMACIES:
            # Search in name, city, address
            if (q_lower in p.get("name", "").lower() or
                q_lower in p.get("city", "").lower() or
                q_lower in p.get("address", "").lower()):
                
                # Apply region filter if provided
                if region and p.get("region"):
                    if p["region"].value != region:
                        continue
                
                pharmacy_dict = {**p}
                if "ownership_type" in pharmacy_dict and hasattr(pharmacy_dict["ownership_type"], "value"):
                    pharmacy_dict["ownership_type"] = pharmacy_dict["ownership_type"].value
                if "region" in pharmacy_dict and hasattr(pharmacy_dict["region"], "value"):
                    pharmacy_dict["region"] = pharmacy_dict["region"].value
                if "tier" in pharmacy_dict and hasattr(pharmacy_dict["tier"], "value"):
                    pharmacy_dict["tier"] = pharmacy_dict["tier"].value
                pharmacy_dict["status"] = "active"
                results.append(pharmacy_dict)
                
                if len(results) >= limit:
                    break
        
        return {"pharmacies": results, "total": len(results), "query": q}
    
    @pharmacy_network_router.get("/pharmacies/{pharmacy_id}")
    async def get_pharmacy_details(pharmacy_id: str):
        """Get details of a specific pharmacy"""
        for p in SEED_PHARMACIES:
            if p.get("id") == pharmacy_id:
                pharmacy_dict = {**p}
                if "ownership_type" in pharmacy_dict and hasattr(pharmacy_dict["ownership_type"], "value"):
                    pharmacy_dict["ownership_type"] = pharmacy_dict["ownership_type"].value
                if "region" in pharmacy_dict and hasattr(pharmacy_dict["region"], "value"):
                    pharmacy_dict["region"] = pharmacy_dict["region"].value
                if "tier" in pharmacy_dict and hasattr(pharmacy_dict["tier"], "value"):
                    pharmacy_dict["tier"] = pharmacy_dict["tier"].value
                pharmacy_dict["status"] = "active"
                return pharmacy_dict
        
        raise HTTPException(status_code=404, detail="Pharmacy not found")
    
    @pharmacy_network_router.get("/regions")
    async def get_regions():
        """Get list of all Ghana regions"""
        return {
            "regions": [
                {"id": r.name, "name": r.value}
                for r in Region
            ]
        }
    
    @pharmacy_network_router.get("/regions/{region}/pharmacies")
    async def get_pharmacies_by_region(
        region: str,
        ownership_type: Optional[str] = None,
        limit: int = Query(50, ge=1, le=200)
    ):
        """Get all pharmacies in a specific region"""
        results = []
        
        for p in SEED_PHARMACIES:
            if p.get("region") and p["region"].value == region:
                if ownership_type and p.get("ownership_type"):
                    if p["ownership_type"].value != ownership_type:
                        continue
                
                pharmacy_dict = {**p}
                if "ownership_type" in pharmacy_dict and hasattr(pharmacy_dict["ownership_type"], "value"):
                    pharmacy_dict["ownership_type"] = pharmacy_dict["ownership_type"].value
                if "region" in pharmacy_dict and hasattr(pharmacy_dict["region"], "value"):
                    pharmacy_dict["region"] = pharmacy_dict["region"].value
                if "tier" in pharmacy_dict and hasattr(pharmacy_dict["tier"], "value"):
                    pharmacy_dict["tier"] = pharmacy_dict["tier"].value
                pharmacy_dict["status"] = "active"
                results.append(pharmacy_dict)
                
                if len(results) >= limit:
                    break
        
        return {"pharmacies": results, "total": len(results), "region": region}
    
    @pharmacy_network_router.get("/ownership-types")
    async def get_ownership_types():
        """Get list of pharmacy ownership types"""
        return {
            "ownership_types": [
                {"id": ot.value, "name": ot.name.replace("_", " ").title(), "description": _get_ownership_description(ot)}
                for ot in OwnershipType
            ]
        }
    
    @pharmacy_network_router.get("/stats")
    async def get_pharmacy_stats():
        """Get statistics about the pharmacy network"""
        stats = {
            "total_pharmacies": len(SEED_PHARMACIES),
            "by_region": {},
            "by_ownership": {},
            "nhis_accredited": 0,
            "24hr_service": 0,
            "with_delivery": 0
        }
        
        for p in SEED_PHARMACIES:
            # By region
            region = p.get("region")
            if region:
                region_name = region.value if hasattr(region, "value") else region
                stats["by_region"][region_name] = stats["by_region"].get(region_name, 0) + 1
            
            # By ownership
            ownership = p.get("ownership_type")
            if ownership:
                ownership_name = ownership.value if hasattr(ownership, "value") else ownership
                stats["by_ownership"][ownership_name] = stats["by_ownership"].get(ownership_name, 0) + 1
            
            # Services
            if p.get("has_nhis"):
                stats["nhis_accredited"] += 1
            if p.get("has_24hr_service"):
                stats["24hr_service"] += 1
            if p.get("has_delivery"):
                stats["with_delivery"] += 1
        
        return stats
    
    @pharmacy_network_router.get("/nearby")
    async def find_nearby_pharmacies(
        region: str = Query(..., description="Region to search in"),
        city: Optional[str] = Query(None, description="City to search in"),
        has_24hr_service: Optional[bool] = Query(None, description="Only show 24-hour pharmacies"),
        limit: int = Query(10, ge=1, le=50)
    ):
        """Find pharmacies near a location (simplified - by region/city)"""
        results = []
        
        for p in SEED_PHARMACIES:
            if p.get("region") and p["region"].value == region:
                if city and city.lower() not in p.get("city", "").lower():
                    continue
                if has_24hr_service is not None and p.get("has_24hr_service") != has_24hr_service:
                    continue
                
                pharmacy_dict = {**p}
                if "ownership_type" in pharmacy_dict and hasattr(pharmacy_dict["ownership_type"], "value"):
                    pharmacy_dict["ownership_type"] = pharmacy_dict["ownership_type"].value
                if "region" in pharmacy_dict and hasattr(pharmacy_dict["region"], "value"):
                    pharmacy_dict["region"] = pharmacy_dict["region"].value
                if "tier" in pharmacy_dict and hasattr(pharmacy_dict["tier"], "value"):
                    pharmacy_dict["tier"] = pharmacy_dict["tier"].value
                pharmacy_dict["status"] = "active"
                results.append(pharmacy_dict)
                
                if len(results) >= limit:
                    break
        
        return {"pharmacies": results, "total": len(results)}
    
    @pharmacy_network_router.get("/chains")
    async def get_pharmacy_chains():
        """Get list of major pharmacy chains in Ghana"""
        chains = {}
        
        for p in SEED_PHARMACIES:
            if p.get("ownership_type") == OwnershipType.CHAIN:
                # Extract chain name from pharmacy name
                name = p.get("name", "")
                chain_name = name.split(" - ")[0] if " - " in name else name
                
                if chain_name not in chains:
                    chains[chain_name] = {
                        "name": chain_name,
                        "locations": [],
                        "count": 0
                    }
                
                chains[chain_name]["locations"].append({
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "city": p.get("city"),
                    "region": p.get("region").value if hasattr(p.get("region"), "value") else p.get("region")
                })
                chains[chain_name]["count"] += 1
        
        return {"chains": list(chains.values())}
    
    return pharmacy_network_router


def _get_ownership_description(ownership_type: OwnershipType) -> str:
    """Get description for ownership type"""
    descriptions = {
        OwnershipType.GHS: "Ghana Health Service government hospitals and clinics",
        OwnershipType.PRIVATE_HOSPITAL: "Private hospital pharmacies",
        OwnershipType.RETAIL: "Community and retail pharmacies",
        OwnershipType.WHOLESALE: "Pharmaceutical wholesale and distribution",
        OwnershipType.CHAIN: "National pharmacy chains (Ernest Chemist, mPharma, etc.)",
        OwnershipType.MISSION: "Mission and religious hospital pharmacies",
        OwnershipType.QUASI_GOVERNMENT: "SSNIT, Military, Police, and University hospitals"
    }
    return descriptions.get(ownership_type, "")
