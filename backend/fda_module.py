"""
Ghana Food and Drugs Authority (FDA) Integration Module
Provides drug verification, registration lookup, and regulatory compliance
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from enum import Enum

fda_router = APIRouter(prefix="/api/fda", tags=["Ghana FDA"])


# ============== Enums ==============

class DrugSchedule(str, Enum):
    OTC = "otc"  # Over the counter
    POM = "pom"  # Prescription Only Medicine
    CD = "cd"    # Controlled Drug
    POM_A = "pom_a"  # Pharmacy Only Medicine


class RegistrationStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    WITHDRAWN = "withdrawn"
    PENDING = "pending"


class DrugCategory(str, Enum):
    HUMAN_MEDICINE = "human_medicine"
    VETERINARY = "veterinary"
    HERBAL = "herbal"
    COSMETIC = "cosmetic"
    MEDICAL_DEVICE = "medical_device"
    FOOD_SUPPLEMENT = "food_supplement"


# ============== Pydantic Models ==============

class FDADrugRegistration(BaseModel):
    registration_number: str
    trade_name: str
    generic_name: str
    manufacturer: str
    country_of_origin: str
    dosage_form: str
    strength: str
    pack_size: str
    schedule: DrugSchedule
    category: DrugCategory
    status: RegistrationStatus
    registration_date: str
    expiry_date: str
    active_ingredients: List[str]
    indications: List[str]
    contraindications: List[str]
    side_effects: List[str]
    storage_conditions: str
    local_representative: Optional[str] = None


class DrugVerificationRequest(BaseModel):
    registration_number: Optional[str] = None
    trade_name: Optional[str] = None
    batch_number: Optional[str] = None


class DrugVerificationResponse(BaseModel):
    verified: bool
    registration_number: str
    trade_name: str
    manufacturer: str
    status: RegistrationStatus
    message: str


# ============== Ghana FDA Registered Drugs Database ==============
# This is a comprehensive seed database. In production, this would connect to Ghana FDA API.

FDA_REGISTERED_DRUGS = [
    # ============== ANTIMALARIALS ==============
    {
        "registration_number": "FDA/dD-22-3456",
        "trade_name": "Coartem",
        "generic_name": "Artemether-Lumefantrine",
        "manufacturer": "Novartis Pharma AG",
        "country_of_origin": "Switzerland",
        "dosage_form": "Tablet",
        "strength": "20mg/120mg",
        "pack_size": "24 tablets",
        "schedule": DrugSchedule.POM,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2022-01-15",
        "expiry_date": "2027-01-14",
        "active_ingredients": ["Artemether", "Lumefantrine"],
        "indications": ["Treatment of uncomplicated P. falciparum malaria"],
        "contraindications": ["First trimester pregnancy", "Severe hepatic impairment"],
        "side_effects": ["Headache", "Dizziness", "Nausea", "Abdominal pain"],
        "storage_conditions": "Store below 30°C"
    },
    {
        "registration_number": "FDA/dD-21-1234",
        "trade_name": "Artesunate Injection",
        "generic_name": "Artesunate",
        "manufacturer": "Guilin Pharmaceutical",
        "country_of_origin": "China",
        "dosage_form": "Injection",
        "strength": "60mg/vial",
        "pack_size": "1 vial",
        "schedule": DrugSchedule.POM,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2021-06-20",
        "expiry_date": "2026-06-19",
        "active_ingredients": ["Artesunate"],
        "indications": ["Severe malaria", "Complicated P. falciparum malaria"],
        "contraindications": ["Known hypersensitivity to artemisinin derivatives"],
        "side_effects": ["Reticulocytopenia", "Neutropenia", "Hepatotoxicity"],
        "storage_conditions": "Store below 25°C, protect from light"
    },
    {
        "registration_number": "FDA/dD-23-5678",
        "trade_name": "Lonart DS",
        "generic_name": "Artemether-Lumefantrine",
        "manufacturer": "Bliss GVS Pharma Ltd",
        "country_of_origin": "India",
        "dosage_form": "Tablet",
        "strength": "80mg/480mg",
        "pack_size": "6 tablets",
        "schedule": DrugSchedule.POM,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2023-03-10",
        "expiry_date": "2028-03-09",
        "active_ingredients": ["Artemether", "Lumefantrine"],
        "indications": ["Uncomplicated malaria in adults"],
        "contraindications": ["Pregnancy first trimester", "QT prolongation"],
        "side_effects": ["Palpitations", "Cough", "Arthralgia"],
        "storage_conditions": "Store below 30°C"
    },
    
    # ============== ANTIBIOTICS ==============
    {
        "registration_number": "FDA/dD-20-9012",
        "trade_name": "Amoxil",
        "generic_name": "Amoxicillin",
        "manufacturer": "GlaxoSmithKline",
        "country_of_origin": "United Kingdom",
        "dosage_form": "Capsule",
        "strength": "500mg",
        "pack_size": "21 capsules",
        "schedule": DrugSchedule.POM,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2020-08-15",
        "expiry_date": "2025-08-14",
        "active_ingredients": ["Amoxicillin trihydrate"],
        "indications": ["Respiratory tract infections", "UTI", "Skin infections"],
        "contraindications": ["Penicillin hypersensitivity", "History of amoxicillin-associated jaundice"],
        "side_effects": ["Diarrhea", "Nausea", "Skin rash", "Vomiting"],
        "storage_conditions": "Store below 25°C"
    },
    {
        "registration_number": "FDA/dD-21-3456",
        "trade_name": "Augmentin",
        "generic_name": "Amoxicillin-Clavulanic Acid",
        "manufacturer": "GlaxoSmithKline",
        "country_of_origin": "United Kingdom",
        "dosage_form": "Tablet",
        "strength": "625mg",
        "pack_size": "14 tablets",
        "schedule": DrugSchedule.POM,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2021-02-28",
        "expiry_date": "2026-02-27",
        "active_ingredients": ["Amoxicillin trihydrate", "Clavulanic acid"],
        "indications": ["Lower respiratory tract infections", "Otitis media", "Sinusitis"],
        "contraindications": ["Penicillin allergy", "Previous hepatic dysfunction with augmentin"],
        "side_effects": ["Diarrhea", "Candidiasis", "Nausea"],
        "storage_conditions": "Store below 25°C"
    },
    {
        "registration_number": "FDA/dD-22-7890",
        "trade_name": "Cipro",
        "generic_name": "Ciprofloxacin",
        "manufacturer": "Bayer AG",
        "country_of_origin": "Germany",
        "dosage_form": "Tablet",
        "strength": "500mg",
        "pack_size": "10 tablets",
        "schedule": DrugSchedule.POM,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2022-05-12",
        "expiry_date": "2027-05-11",
        "active_ingredients": ["Ciprofloxacin hydrochloride"],
        "indications": ["UTI", "Respiratory infections", "GI infections", "Typhoid fever"],
        "contraindications": ["Tendon disorders", "Myasthenia gravis", "Children under 18"],
        "side_effects": ["Nausea", "Diarrhea", "Dizziness", "Tendinitis"],
        "storage_conditions": "Store below 30°C, protect from light"
    },
    {
        "registration_number": "FDA/dD-23-1234",
        "trade_name": "Zithromax",
        "generic_name": "Azithromycin",
        "manufacturer": "Pfizer Inc",
        "country_of_origin": "USA",
        "dosage_form": "Tablet",
        "strength": "500mg",
        "pack_size": "3 tablets",
        "schedule": DrugSchedule.POM,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2023-01-20",
        "expiry_date": "2028-01-19",
        "active_ingredients": ["Azithromycin dihydrate"],
        "indications": ["Community-acquired pneumonia", "Pharyngitis", "Skin infections"],
        "contraindications": ["Hypersensitivity to macrolides", "History of cholestatic jaundice"],
        "side_effects": ["Diarrhea", "Nausea", "Abdominal pain", "QT prolongation"],
        "storage_conditions": "Store below 30°C"
    },
    {
        "registration_number": "FDA/dD-20-5678",
        "trade_name": "Flagyl",
        "generic_name": "Metronidazole",
        "manufacturer": "Sanofi-Aventis",
        "country_of_origin": "France",
        "dosage_form": "Tablet",
        "strength": "400mg",
        "pack_size": "14 tablets",
        "schedule": DrugSchedule.POM,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2020-11-05",
        "expiry_date": "2025-11-04",
        "active_ingredients": ["Metronidazole"],
        "indications": ["Amoebiasis", "Giardiasis", "Anaerobic infections", "H. pylori"],
        "contraindications": ["First trimester pregnancy", "Alcohol consumption"],
        "side_effects": ["Metallic taste", "Nausea", "Headache", "Peripheral neuropathy"],
        "storage_conditions": "Store below 25°C, protect from light"
    },
    
    # ============== CARDIOVASCULAR ==============
    {
        "registration_number": "FDA/dD-21-9012",
        "trade_name": "Norvasc",
        "generic_name": "Amlodipine",
        "manufacturer": "Pfizer Inc",
        "country_of_origin": "USA",
        "dosage_form": "Tablet",
        "strength": "5mg",
        "pack_size": "30 tablets",
        "schedule": DrugSchedule.POM,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2021-04-18",
        "expiry_date": "2026-04-17",
        "active_ingredients": ["Amlodipine besylate"],
        "indications": ["Hypertension", "Angina pectoris"],
        "contraindications": ["Cardiogenic shock", "Severe aortic stenosis"],
        "side_effects": ["Peripheral edema", "Flushing", "Palpitations"],
        "storage_conditions": "Store below 30°C"
    },
    {
        "registration_number": "FDA/dD-22-3457",
        "trade_name": "Lipitor",
        "generic_name": "Atorvastatin",
        "manufacturer": "Pfizer Inc",
        "country_of_origin": "USA",
        "dosage_form": "Tablet",
        "strength": "20mg",
        "pack_size": "30 tablets",
        "schedule": DrugSchedule.POM,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2022-02-14",
        "expiry_date": "2027-02-13",
        "active_ingredients": ["Atorvastatin calcium"],
        "indications": ["Hypercholesterolemia", "Prevention of cardiovascular events"],
        "contraindications": ["Active liver disease", "Pregnancy", "Breastfeeding"],
        "side_effects": ["Myalgia", "Elevated liver enzymes", "Headache"],
        "storage_conditions": "Store below 30°C"
    },
    {
        "registration_number": "FDA/dD-20-1235",
        "trade_name": "Zestril",
        "generic_name": "Lisinopril",
        "manufacturer": "AstraZeneca",
        "country_of_origin": "United Kingdom",
        "dosage_form": "Tablet",
        "strength": "10mg",
        "pack_size": "28 tablets",
        "schedule": DrugSchedule.POM,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2020-09-22",
        "expiry_date": "2025-09-21",
        "active_ingredients": ["Lisinopril dihydrate"],
        "indications": ["Hypertension", "Heart failure", "Diabetic nephropathy"],
        "contraindications": ["Angioedema history", "Pregnancy", "Bilateral renal artery stenosis"],
        "side_effects": ["Dry cough", "Dizziness", "Hypotension", "Hyperkalemia"],
        "storage_conditions": "Store below 30°C, protect from moisture"
    },
    {
        "registration_number": "FDA/dD-23-5679",
        "trade_name": "Cozaar",
        "generic_name": "Losartan",
        "manufacturer": "Merck & Co",
        "country_of_origin": "USA",
        "dosage_form": "Tablet",
        "strength": "50mg",
        "pack_size": "28 tablets",
        "schedule": DrugSchedule.POM,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2023-06-30",
        "expiry_date": "2028-06-29",
        "active_ingredients": ["Losartan potassium"],
        "indications": ["Hypertension", "Diabetic nephropathy", "Stroke prevention"],
        "contraindications": ["Pregnancy", "Severe hepatic impairment"],
        "side_effects": ["Dizziness", "Upper respiratory infection", "Hyperkalemia"],
        "storage_conditions": "Store below 30°C"
    },
    {
        "registration_number": "FDA/dD-21-7891",
        "trade_name": "Lasix",
        "generic_name": "Furosemide",
        "manufacturer": "Sanofi-Aventis",
        "country_of_origin": "France",
        "dosage_form": "Tablet",
        "strength": "40mg",
        "pack_size": "30 tablets",
        "schedule": DrugSchedule.POM,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2021-08-10",
        "expiry_date": "2026-08-09",
        "active_ingredients": ["Furosemide"],
        "indications": ["Edema", "Heart failure", "Hypertension"],
        "contraindications": ["Anuria", "Hepatic coma", "Severe hypokalemia"],
        "side_effects": ["Hypokalemia", "Dehydration", "Ototoxicity", "Hyperuricemia"],
        "storage_conditions": "Store below 25°C, protect from light"
    },
    
    # ============== DIABETES ==============
    {
        "registration_number": "FDA/dD-22-9013",
        "trade_name": "Glucophage",
        "generic_name": "Metformin",
        "manufacturer": "Merck Serono",
        "country_of_origin": "France",
        "dosage_form": "Tablet",
        "strength": "500mg",
        "pack_size": "60 tablets",
        "schedule": DrugSchedule.POM,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2022-07-25",
        "expiry_date": "2027-07-24",
        "active_ingredients": ["Metformin hydrochloride"],
        "indications": ["Type 2 diabetes mellitus"],
        "contraindications": ["Renal impairment", "Metabolic acidosis", "Alcoholism"],
        "side_effects": ["GI upset", "Metallic taste", "Lactic acidosis (rare)"],
        "storage_conditions": "Store below 30°C"
    },
    {
        "registration_number": "FDA/dD-23-1235",
        "trade_name": "Januvia",
        "generic_name": "Sitagliptin",
        "manufacturer": "Merck & Co",
        "country_of_origin": "USA",
        "dosage_form": "Tablet",
        "strength": "100mg",
        "pack_size": "28 tablets",
        "schedule": DrugSchedule.POM,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2023-04-05",
        "expiry_date": "2028-04-04",
        "active_ingredients": ["Sitagliptin phosphate"],
        "indications": ["Type 2 diabetes mellitus"],
        "contraindications": ["Type 1 diabetes", "Diabetic ketoacidosis"],
        "side_effects": ["Headache", "Upper respiratory infection", "Pancreatitis (rare)"],
        "storage_conditions": "Store below 30°C"
    },
    {
        "registration_number": "FDA/dD-20-3457",
        "trade_name": "Lantus",
        "generic_name": "Insulin Glargine",
        "manufacturer": "Sanofi-Aventis",
        "country_of_origin": "France",
        "dosage_form": "Injection",
        "strength": "100 units/mL",
        "pack_size": "5 x 3mL cartridges",
        "schedule": DrugSchedule.POM,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2020-12-01",
        "expiry_date": "2025-11-30",
        "active_ingredients": ["Insulin glargine"],
        "indications": ["Diabetes mellitus requiring insulin therapy"],
        "contraindications": ["Hypoglycemia", "Hypersensitivity to insulin glargine"],
        "side_effects": ["Hypoglycemia", "Injection site reactions", "Weight gain"],
        "storage_conditions": "Store at 2-8°C before first use, then below 30°C"
    },
    
    # ============== ANALGESICS & ANTI-INFLAMMATORIES ==============
    {
        "registration_number": "FDA/dD-19-7892",
        "trade_name": "Panadol",
        "generic_name": "Paracetamol",
        "manufacturer": "GlaxoSmithKline",
        "country_of_origin": "United Kingdom",
        "dosage_form": "Tablet",
        "strength": "500mg",
        "pack_size": "96 tablets",
        "schedule": DrugSchedule.OTC,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2019-05-10",
        "expiry_date": "2024-05-09",
        "active_ingredients": ["Paracetamol"],
        "indications": ["Fever", "Mild to moderate pain"],
        "contraindications": ["Severe hepatic impairment"],
        "side_effects": ["Rare allergic reactions", "Hepatotoxicity in overdose"],
        "storage_conditions": "Store below 30°C"
    },
    {
        "registration_number": "FDA/dD-21-5679",
        "trade_name": "Brufen",
        "generic_name": "Ibuprofen",
        "manufacturer": "Abbott Laboratories",
        "country_of_origin": "USA",
        "dosage_form": "Tablet",
        "strength": "400mg",
        "pack_size": "30 tablets",
        "schedule": DrugSchedule.POM_A,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2021-10-15",
        "expiry_date": "2026-10-14",
        "active_ingredients": ["Ibuprofen"],
        "indications": ["Pain", "Inflammation", "Fever", "Arthritis"],
        "contraindications": ["Active GI bleeding", "Severe renal impairment", "Third trimester pregnancy"],
        "side_effects": ["GI upset", "Dizziness", "Fluid retention"],
        "storage_conditions": "Store below 25°C"
    },
    {
        "registration_number": "FDA/dD-22-1236",
        "trade_name": "Voltaren",
        "generic_name": "Diclofenac",
        "manufacturer": "Novartis Pharma AG",
        "country_of_origin": "Switzerland",
        "dosage_form": "Tablet",
        "strength": "50mg",
        "pack_size": "20 tablets",
        "schedule": DrugSchedule.POM,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2022-03-08",
        "expiry_date": "2027-03-07",
        "active_ingredients": ["Diclofenac sodium"],
        "indications": ["Inflammatory conditions", "Pain", "Dysmenorrhea"],
        "contraindications": ["GI ulceration", "Severe heart failure", "Third trimester pregnancy"],
        "side_effects": ["GI disturbances", "Headache", "Cardiovascular events"],
        "storage_conditions": "Store below 30°C"
    },
    {
        "registration_number": "FDA/dD-CD-20-0001",
        "trade_name": "Tramacet",
        "generic_name": "Tramadol-Paracetamol",
        "manufacturer": "Janssen Pharmaceuticals",
        "country_of_origin": "Belgium",
        "dosage_form": "Tablet",
        "strength": "37.5mg/325mg",
        "pack_size": "20 tablets",
        "schedule": DrugSchedule.CD,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2020-06-20",
        "expiry_date": "2025-06-19",
        "active_ingredients": ["Tramadol hydrochloride", "Paracetamol"],
        "indications": ["Moderate to severe pain"],
        "contraindications": ["MAO inhibitors", "Epilepsy", "Opioid dependence"],
        "side_effects": ["Dizziness", "Nausea", "Constipation", "Seizures (rare)"],
        "storage_conditions": "Store below 30°C"
    },
    
    # ============== RESPIRATORY ==============
    {
        "registration_number": "FDA/dD-21-3458",
        "trade_name": "Ventolin",
        "generic_name": "Salbutamol",
        "manufacturer": "GlaxoSmithKline",
        "country_of_origin": "United Kingdom",
        "dosage_form": "Inhaler",
        "strength": "100mcg/puff",
        "pack_size": "200 doses",
        "schedule": DrugSchedule.POM,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2021-07-22",
        "expiry_date": "2026-07-21",
        "active_ingredients": ["Salbutamol sulfate"],
        "indications": ["Asthma", "COPD", "Bronchospasm"],
        "contraindications": ["Hypersensitivity to salbutamol"],
        "side_effects": ["Tremor", "Palpitations", "Headache"],
        "storage_conditions": "Store below 30°C, protect from direct sunlight"
    },
    {
        "registration_number": "FDA/dD-23-7893",
        "trade_name": "Seretide",
        "generic_name": "Fluticasone-Salmeterol",
        "manufacturer": "GlaxoSmithKline",
        "country_of_origin": "United Kingdom",
        "dosage_form": "Inhaler",
        "strength": "250mcg/50mcg",
        "pack_size": "60 doses",
        "schedule": DrugSchedule.POM,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2023-02-28",
        "expiry_date": "2028-02-27",
        "active_ingredients": ["Fluticasone propionate", "Salmeterol xinafoate"],
        "indications": ["Asthma maintenance", "COPD"],
        "contraindications": ["Primary treatment of acute asthma"],
        "side_effects": ["Oral candidiasis", "Hoarseness", "Headache"],
        "storage_conditions": "Store below 30°C"
    },
    
    # ============== GI MEDICATIONS ==============
    {
        "registration_number": "FDA/dD-22-5680",
        "trade_name": "Nexium",
        "generic_name": "Esomeprazole",
        "manufacturer": "AstraZeneca",
        "country_of_origin": "United Kingdom",
        "dosage_form": "Capsule",
        "strength": "40mg",
        "pack_size": "28 capsules",
        "schedule": DrugSchedule.POM,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2022-09-15",
        "expiry_date": "2027-09-14",
        "active_ingredients": ["Esomeprazole magnesium"],
        "indications": ["GERD", "Peptic ulcer", "H. pylori eradication"],
        "contraindications": ["Hypersensitivity to PPIs"],
        "side_effects": ["Headache", "Diarrhea", "Nausea"],
        "storage_conditions": "Store below 30°C"
    },
    {
        "registration_number": "FDA/dD-20-9014",
        "trade_name": "Losec",
        "generic_name": "Omeprazole",
        "manufacturer": "AstraZeneca",
        "country_of_origin": "United Kingdom",
        "dosage_form": "Capsule",
        "strength": "20mg",
        "pack_size": "14 capsules",
        "schedule": DrugSchedule.POM,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2020-04-10",
        "expiry_date": "2025-04-09",
        "active_ingredients": ["Omeprazole"],
        "indications": ["Peptic ulcer", "GERD", "Zollinger-Ellison syndrome"],
        "contraindications": ["Hypersensitivity to omeprazole"],
        "side_effects": ["Headache", "Abdominal pain", "Constipation"],
        "storage_conditions": "Store below 25°C, protect from moisture"
    },
    
    # ============== CNS MEDICATIONS ==============
    {
        "registration_number": "FDA/dD-CD-21-0002",
        "trade_name": "Valium",
        "generic_name": "Diazepam",
        "manufacturer": "Roche",
        "country_of_origin": "Switzerland",
        "dosage_form": "Tablet",
        "strength": "5mg",
        "pack_size": "30 tablets",
        "schedule": DrugSchedule.CD,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2021-03-15",
        "expiry_date": "2026-03-14",
        "active_ingredients": ["Diazepam"],
        "indications": ["Anxiety", "Muscle spasms", "Seizures", "Alcohol withdrawal"],
        "contraindications": ["Myasthenia gravis", "Severe respiratory depression", "Sleep apnea"],
        "side_effects": ["Drowsiness", "Ataxia", "Dependence"],
        "storage_conditions": "Store below 30°C"
    },
    {
        "registration_number": "FDA/dD-23-9015",
        "trade_name": "Zoloft",
        "generic_name": "Sertraline",
        "manufacturer": "Pfizer Inc",
        "country_of_origin": "USA",
        "dosage_form": "Tablet",
        "strength": "50mg",
        "pack_size": "30 tablets",
        "schedule": DrugSchedule.POM,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2023-08-20",
        "expiry_date": "2028-08-19",
        "active_ingredients": ["Sertraline hydrochloride"],
        "indications": ["Major depression", "Panic disorder", "OCD", "PTSD"],
        "contraindications": ["MAO inhibitors", "Pimozide use"],
        "side_effects": ["Nausea", "Diarrhea", "Insomnia", "Sexual dysfunction"],
        "storage_conditions": "Store below 30°C"
    },
    
    # ============== HERBAL MEDICINES (Ghana Local) ==============
    {
        "registration_number": "FDA/hD-22-0001",
        "trade_name": "Adutwumwaa Bitters",
        "generic_name": "Herbal Bitter",
        "manufacturer": "Adutwumwaa Herbal Industries",
        "country_of_origin": "Ghana",
        "dosage_form": "Liquid",
        "strength": "200mL",
        "pack_size": "1 bottle",
        "schedule": DrugSchedule.OTC,
        "category": DrugCategory.HERBAL,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2022-01-05",
        "expiry_date": "2027-01-04",
        "active_ingredients": ["Aloe vera", "Ginger", "Neem", "Moringa"],
        "indications": ["General wellness", "Digestive support"],
        "contraindications": ["Pregnancy", "Known hypersensitivity"],
        "side_effects": ["Mild GI upset"],
        "storage_conditions": "Store in cool, dry place"
    },
    {
        "registration_number": "FDA/hD-21-0002",
        "trade_name": "Cryptolepis Tea",
        "generic_name": "Cryptolepis sanguinolenta",
        "manufacturer": "Centre for Plant Medicine Research",
        "country_of_origin": "Ghana",
        "dosage_form": "Tea bag",
        "strength": "2g/bag",
        "pack_size": "25 bags",
        "schedule": DrugSchedule.OTC,
        "category": DrugCategory.HERBAL,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2021-06-15",
        "expiry_date": "2026-06-14",
        "active_ingredients": ["Cryptolepis sanguinolenta extract"],
        "indications": ["Traditional antimalarial", "Fever management"],
        "contraindications": ["Pregnancy", "Children under 5"],
        "side_effects": ["None reported"],
        "storage_conditions": "Store in cool, dry place"
    },
    
    # ============== VACCINES ==============
    {
        "registration_number": "FDA/vD-23-0001",
        "trade_name": "Comirnaty",
        "generic_name": "COVID-19 mRNA Vaccine",
        "manufacturer": "Pfizer-BioNTech",
        "country_of_origin": "USA/Germany",
        "dosage_form": "Injection",
        "strength": "30mcg/0.3mL",
        "pack_size": "6 doses/vial",
        "schedule": DrugSchedule.POM,
        "category": DrugCategory.HUMAN_MEDICINE,
        "status": RegistrationStatus.ACTIVE,
        "registration_date": "2023-01-01",
        "expiry_date": "2028-01-01",
        "active_ingredients": ["BNT162b2 mRNA"],
        "indications": ["Prevention of COVID-19"],
        "contraindications": ["Severe allergic reaction to previous dose"],
        "side_effects": ["Injection site pain", "Fatigue", "Headache", "Myalgia"],
        "storage_conditions": "Store at -90°C to -60°C (ultra-cold)"
    },
]


def create_fda_endpoints(db, get_current_user):
    """Create FDA API endpoints"""
    
    @fda_router.get("/drugs")
    async def list_registered_drugs(
        query: Optional[str] = Query(None, description="Search by name"),
        category: Optional[str] = Query(None, description="Filter by category"),
        schedule: Optional[str] = Query(None, description="Filter by schedule"),
        status: Optional[str] = Query(None, description="Filter by status"),
        manufacturer: Optional[str] = Query(None, description="Filter by manufacturer"),
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0)
    ):
        """List all FDA registered drugs with filtering"""
        filtered = FDA_REGISTERED_DRUGS.copy()
        
        if query:
            query_lower = query.lower()
            filtered = [d for d in filtered if 
                query_lower in d["trade_name"].lower() or 
                query_lower in d["generic_name"].lower() or
                any(query_lower in ing.lower() for ing in d["active_ingredients"])]
        
        if category:
            filtered = [d for d in filtered if d["category"].value == category]
        
        if schedule:
            filtered = [d for d in filtered if d["schedule"].value == schedule]
        
        if status:
            filtered = [d for d in filtered if d["status"].value == status]
        
        if manufacturer:
            filtered = [d for d in filtered if manufacturer.lower() in d["manufacturer"].lower()]
        
        # Convert enums to values
        result = []
        for d in filtered[offset:offset + limit]:
            drug_dict = {**d}
            drug_dict["schedule"] = drug_dict["schedule"].value
            drug_dict["category"] = drug_dict["category"].value
            drug_dict["status"] = drug_dict["status"].value
            result.append(drug_dict)
        
        return {
            "drugs": result,
            "total": len(filtered),
            "limit": limit,
            "offset": offset
        }
    
    @fda_router.get("/drugs/search")
    async def search_drugs(
        q: str = Query(..., min_length=2, description="Search query"),
        limit: int = Query(20, ge=1, le=100)
    ):
        """Search FDA registered drugs by name or active ingredient"""
        q_lower = q.lower()
        results = []
        
        for d in FDA_REGISTERED_DRUGS:
            if (q_lower in d["trade_name"].lower() or 
                q_lower in d["generic_name"].lower() or
                any(q_lower in ing.lower() for ing in d["active_ingredients"])):
                
                drug_dict = {**d}
                drug_dict["schedule"] = drug_dict["schedule"].value
                drug_dict["category"] = drug_dict["category"].value
                drug_dict["status"] = drug_dict["status"].value
                results.append(drug_dict)
                
                if len(results) >= limit:
                    break
        
        return {"drugs": results, "total": len(results), "query": q}
    
    @fda_router.get("/drugs/{registration_number}")
    async def get_drug_details(registration_number: str):
        """Get detailed information about a registered drug"""
        for d in FDA_REGISTERED_DRUGS:
            if d["registration_number"] == registration_number:
                drug_dict = {**d}
                drug_dict["schedule"] = drug_dict["schedule"].value
                drug_dict["category"] = drug_dict["category"].value
                drug_dict["status"] = drug_dict["status"].value
                return drug_dict
        
        raise HTTPException(status_code=404, detail="Drug not found in FDA registry")
    
    @fda_router.post("/verify")
    async def verify_drug(request: DrugVerificationRequest):
        """Verify if a drug is registered with Ghana FDA"""
        if request.registration_number:
            for d in FDA_REGISTERED_DRUGS:
                if d["registration_number"] == request.registration_number:
                    return {
                        "verified": d["status"] == RegistrationStatus.ACTIVE,
                        "registration_number": d["registration_number"],
                        "trade_name": d["trade_name"],
                        "manufacturer": d["manufacturer"],
                        "status": d["status"].value,
                        "message": "Drug is registered and active" if d["status"] == RegistrationStatus.ACTIVE else f"Drug registration is {d['status'].value}"
                    }
            return {
                "verified": False,
                "registration_number": request.registration_number,
                "trade_name": "",
                "manufacturer": "",
                "status": "not_found",
                "message": "Drug not found in FDA registry"
            }
        
        if request.trade_name:
            for d in FDA_REGISTERED_DRUGS:
                if request.trade_name.lower() in d["trade_name"].lower():
                    return {
                        "verified": d["status"] == RegistrationStatus.ACTIVE,
                        "registration_number": d["registration_number"],
                        "trade_name": d["trade_name"],
                        "manufacturer": d["manufacturer"],
                        "status": d["status"].value,
                        "message": "Drug is registered and active" if d["status"] == RegistrationStatus.ACTIVE else f"Drug registration is {d['status'].value}"
                    }
        
        return {
            "verified": False,
            "registration_number": "",
            "trade_name": request.trade_name or "",
            "manufacturer": "",
            "status": "not_found",
            "message": "Drug not found in FDA registry"
        }
    
    @fda_router.get("/schedules")
    async def get_drug_schedules():
        """Get list of drug schedules and their meanings"""
        return {
            "schedules": [
                {"id": DrugSchedule.OTC.value, "name": "Over The Counter (OTC)", "description": "Available without prescription"},
                {"id": DrugSchedule.POM_A.value, "name": "Pharmacy Only Medicine", "description": "Available from pharmacy without prescription"},
                {"id": DrugSchedule.POM.value, "name": "Prescription Only Medicine (POM)", "description": "Requires valid prescription"},
                {"id": DrugSchedule.CD.value, "name": "Controlled Drug", "description": "Strictly controlled, requires special prescription"}
            ]
        }
    
    @fda_router.get("/categories")
    async def get_drug_categories():
        """Get list of drug categories"""
        return {
            "categories": [
                {"id": DrugCategory.HUMAN_MEDICINE.value, "name": "Human Medicine"},
                {"id": DrugCategory.VETERINARY.value, "name": "Veterinary Medicine"},
                {"id": DrugCategory.HERBAL.value, "name": "Herbal Medicine"},
                {"id": DrugCategory.COSMETIC.value, "name": "Cosmetic"},
                {"id": DrugCategory.MEDICAL_DEVICE.value, "name": "Medical Device"},
                {"id": DrugCategory.FOOD_SUPPLEMENT.value, "name": "Food Supplement"}
            ]
        }
    
    @fda_router.get("/stats")
    async def get_fda_stats():
        """Get statistics about registered drugs"""
        stats = {
            "total_registered": len(FDA_REGISTERED_DRUGS),
            "by_schedule": {},
            "by_category": {},
            "by_status": {},
            "by_country": {},
            "controlled_drugs": 0,
            "active_registrations": 0
        }
        
        for d in FDA_REGISTERED_DRUGS:
            # By schedule
            schedule = d["schedule"].value
            stats["by_schedule"][schedule] = stats["by_schedule"].get(schedule, 0) + 1
            
            # By category
            category = d["category"].value
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
            
            # By status
            status = d["status"].value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # By country
            country = d["country_of_origin"]
            stats["by_country"][country] = stats["by_country"].get(country, 0) + 1
            
            # Controlled drugs
            if d["schedule"] == DrugSchedule.CD:
                stats["controlled_drugs"] += 1
            
            # Active
            if d["status"] == RegistrationStatus.ACTIVE:
                stats["active_registrations"] += 1
        
        return stats
    
    @fda_router.get("/manufacturers")
    async def get_manufacturers():
        """Get list of all manufacturers"""
        manufacturers = {}
        for d in FDA_REGISTERED_DRUGS:
            mfr = d["manufacturer"]
            if mfr not in manufacturers:
                manufacturers[mfr] = {
                    "name": mfr,
                    "country": d["country_of_origin"],
                    "product_count": 0
                }
            manufacturers[mfr]["product_count"] += 1
        
        return {"manufacturers": list(manufacturers.values())}
    
    @fda_router.get("/alerts")
    async def get_safety_alerts():
        """Get drug safety alerts (mock data for demonstration)"""
        return {
            "alerts": [
                {
                    "id": "ALERT-2023-001",
                    "type": "recall",
                    "severity": "high",
                    "drug": "Sample Drug Batch XYZ",
                    "reason": "Contamination detected",
                    "date": "2023-12-01",
                    "action_required": "Return to pharmacy"
                },
                {
                    "id": "ALERT-2023-002",
                    "type": "warning",
                    "severity": "medium",
                    "drug": "Various ACE Inhibitors",
                    "reason": "Updated contraindication for pregnancy",
                    "date": "2023-11-15",
                    "action_required": "Review patient medication history"
                }
            ],
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    return fda_router
