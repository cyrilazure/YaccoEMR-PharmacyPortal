# Yacco EMR - Product Requirements Document

## Project Overview
**Name:** Yacco EMR - Electronic Medical Records System  
**Version:** 1.2.0  
**Created:** February 3, 2026  
**Last Updated:** February 6, 2026

## Problem Statement
Build a comprehensive Electronic Medical Records (EMR) system similar to Epic EMR with core clinical modules, multi-role support, scheduling, AI-assisted documentation, and healthcare interoperability (FHIR). Extended with Ghana-specific features including NHIS integration, regional pharmacy network, and Paystack payment processing.

## User Personas
1. **Physicians** - Primary clinical users who document patient encounters, place orders, review results
2. **Nurses** - Execute orders, administer medications, document care, monitor patients (MAR workflow)
3. **Schedulers** - Manage appointments, patient registration, capacity
4. **Administrators** - Oversee system, manage users, view analytics, monitor system health
5. **Pharmacists** - Manage e-prescriptions, dispense medications
6. **Billers** - Create invoices, process payments, manage claims

## Tech Stack
- **Frontend:** React 19, Tailwind CSS, shadcn/ui components, Recharts
- **Backend:** FastAPI (Python)
- **Database:** MongoDB
- **AI:** OpenAI GPT-5.2 via Emergent LLM Key
- **Auth:** JWT-based authentication
- **Interoperability:** FHIR R4 API
- **Payments:** Paystack (with Subaccounts for hospital settlements)

## What's Been Implemented

### Ghana Pharmacy Network (NEW - February 6, 2026)
- [x] Comprehensive national pharmacy database (133 pharmacies across all 16 regions)
- [x] Pharmacy types: GHS, Private Hospital, Retail, Wholesale, Chain, Mission, Quasi-Government
- [x] Major chains: Ernest Chemist (17 locations), mPharma (7 locations), Kinapharma (5 locations)
- [x] Search and filter by region, city, ownership type
- [x] Filter by NHIS accreditation (129 pharmacies), 24-hour service (26), delivery available (26)
- [x] Pharmacy details view with contact info, operating hours, parent facility
- [x] Pharmacy Directory UI at `/pharmacy-directory`
- [x] API endpoints: `/api/pharmacy-network/*`

### Billing & Finance Module
- [x] GHS (₵) currency localization
- [x] Invoice creation, reversal, and voiding
- [x] Payment method changes with audit trail
- [x] Paystack integration with Subaccounts (direct settlement to hospital bank accounts)
- [x] Payment verification step for manual payments (Cash, Bank Transfer)
- [x] Bank transfer routing info display (domestic and international)
- [x] Finance Settings for hospital IT admin (bank accounts, mobile money)

### Bed Management Module
- [x] Ward creation (custom and auto-generated naming)
- [x] Bed creation and bulk creation
- [x] Patient admission, transfer, and discharge workflows
- [x] Census dashboard

### Radiology Module
- [x] Imaging order creation from patient chart
- [x] Radiology queue for staff
- [x] RBAC for radiologist vs radiology_staff

### e-Prescribing Module
- [x] Drug database with search
- [x] Prescription creation with drug-drug interaction checking
- [x] Pharmacy portal for dispensing

### Ambulance Module (Scaffolded)
- [x] Backend API for fleet management
- [x] Backend API for dispatch requests
- [ ] Frontend UI (basic scaffolding only)

### Core EMR Features
- [x] JWT authentication with 2FA support
- [x] Multi-tenant architecture (16 Ghana regions)
- [x] Role-based access control (15+ roles)
- [x] Patient management
- [x] Clinical documentation (SOAP notes)
- [x] Vitals, problems, medications, allergies
- [x] Lab and imaging orders
- [x] Appointment scheduling
- [x] AI-assisted documentation
- [x] FHIR R4 API
- [x] Telehealth video sessions
- [x] Audit logging

## Key API Endpoints

### Pharmacy Network (NEW)
```
GET  /api/pharmacy-network/pharmacies     - List all pharmacies (paginated)
GET  /api/pharmacy-network/pharmacies/search?q=<query> - Search pharmacies
GET  /api/pharmacy-network/pharmacies/{id} - Get pharmacy details
GET  /api/pharmacy-network/regions        - List all 16 Ghana regions
GET  /api/pharmacy-network/regions/{region}/pharmacies - Get pharmacies by region
GET  /api/pharmacy-network/ownership-types - Get ownership type options
GET  /api/pharmacy-network/chains         - Get pharmacy chains
GET  /api/pharmacy-network/stats          - Get network statistics
GET  /api/pharmacy-network/nearby         - Find nearby pharmacies
```

### Billing & Finance
```
POST /api/billing/invoices               - Create invoice
PUT  /api/billing/invoices/{id}/reverse  - Reverse invoice
PUT  /api/billing/invoices/{id}/change-payment-method - Change payment type
POST /api/billing/paystack/initialize    - Initialize Paystack payment
GET  /api/finance/bank-accounts          - Manage hospital bank accounts
```

### Bed Management
```
GET  /api/beds/census                    - Get bed census
POST /api/beds/wards/create              - Create ward
POST /api/beds/admissions/create         - Admit patient
POST /api/beds/admissions/{id}/transfer  - Transfer patient
POST /api/beds/admissions/{id}/discharge - Discharge patient
```

## Prioritized Backlog

### P0 (Critical)
- [ ] Complete Ambulance Portal UI (fleet management, dispatch, reports)
- [ ] NHIS Pharmacy Claims Integration

### P1 (High Priority)
- [ ] E-prescription routing to external pharmacies
- [ ] Prescription status tracking for physicians
- [ ] Notifications for prescription updates

### P2 (Medium Priority)
- [ ] Integration with other payment gateways (Flutterwave, Hubtel)
- [ ] Supply chain inventory for pharmacies

### P3 (Future)
- [ ] National e-Pharmacy platform integration
- [ ] FDA APIs integration
- [ ] Mobile apps

## Test Credentials
- **Super Admin**: ygtnetworks@gmail.com / test123
- **Hospital IT Admin**: it_admin@yacco.health / test123
- **Biller**: billing@yacco.health / test123
- **Bed Manager**: bed_manager@yacco.health / test123
- **Radiologist**: radiologist@yacco.health / test123
- **Radiology Staff**: radiology_staff@yacco.health / test123
- **Nurse**: test_nurse@yacco.health / test123

## Environment Variables
```
# Backend (.env)
MONGO_URL=mongodb://localhost:27017
DB_NAME=test_database
JWT_SECRET=<secret>
EMERGENT_LLM_KEY=<key>
PAYSTACK_SECRET_KEY=<key>

# Frontend (.env)
REACT_APP_BACKEND_URL=<url>
```
