# Yacco EMR - Product Requirements Document

## Project Overview
**Name:** Yacco EMR - Electronic Medical Records System  
**Version:** 1.3.0  
**Created:** February 3, 2026  
**Last Updated:** February 6, 2026

## Problem Statement
Build a comprehensive Electronic Medical Records (EMR) system similar to Epic EMR with core clinical modules, multi-role support, scheduling, AI-assisted documentation, and healthcare interoperability (FHIR). Extended with Ghana-specific features including NHIS integration, regional pharmacy network, Ghana FDA drug verification, and Paystack payment processing.

## User Personas
1. **Physicians** - Primary clinical users who document patient encounters, place orders, review results
2. **Nurses** - Execute orders, administer medications, document care, monitor patients (MAR workflow)
3. **Schedulers** - Manage appointments, patient registration, capacity
4. **Administrators** - Oversee system, manage users, view analytics, monitor system health
5. **Pharmacists** - Manage e-prescriptions, dispense medications, verify FDA registration
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

### E-Prescription Routing (NEW - February 6, 2026)
- [x] E-prescription routing from Patient Chart to external pharmacies
- [x] Pharmacy selection with search from Ghana Pharmacy Network (133 pharmacies)
- [x] Prescription status tracking: sent → accepted/rejected → filled
- [x] Prescription tracking by RX number with timeline
- [x] Pharmacy accept/reject/fill workflow
- [x] Patient Chart "Pharmacy" tab with active prescriptions and routing status
- [x] API endpoints: `/api/prescriptions/{id}/send-to-pharmacy`, `/api/prescriptions/tracking/{rx}`

### Ghana FDA Integration (NEW - February 6, 2026)
- [x] Drug registration database with 29 FDA-registered drugs (MOCKED - seed data)
- [x] Drug verification by trade name or registration number
- [x] Drug schedules: OTC, POM (Prescription Only), CD (Controlled Drug)
- [x] Drug categories: Human Medicine, Herbal, Veterinary, etc.
- [x] Manufacturer database with product counts
- [x] Safety alerts (mock data for demonstration)
- [x] API endpoints: `/api/fda/drugs/*`, `/api/fda/verify`, `/api/fda/schedules`

### Ghana Pharmacy Network (February 6, 2026)
- [x] Comprehensive national pharmacy database (133 pharmacies across all 16 regions)
- [x] Pharmacy types: GHS, Private Hospital, Retail, Wholesale, Chain, Mission, Quasi-Government
- [x] Major chains: Ernest Chemist (17 locations), mPharma (7 locations), Kinapharma (5 locations)
- [x] Search and filter by region, city, ownership type
- [x] Filter by NHIS accreditation (129 pharmacies), 24-hour service (26), delivery available (26)
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

### E-Prescription Routing (NEW)
```
POST /api/prescriptions/{id}/send-to-pharmacy - Route prescription to external pharmacy
GET  /api/prescriptions/tracking/{rx_number}  - Track prescription by RX number
GET  /api/prescriptions/patient/{id}/routed   - Get patient's routed prescriptions
GET  /api/prescriptions/routing/{id}/status   - Get routing status
PUT  /api/prescriptions/routing/{id}/accept   - Pharmacy accepts prescription
PUT  /api/prescriptions/routing/{id}/reject   - Pharmacy rejects prescription
PUT  /api/prescriptions/routing/{id}/fill     - Pharmacy marks as filled
```

### Ghana FDA Integration (NEW)
```
GET  /api/fda/drugs                      - List all registered drugs (29)
GET  /api/fda/drugs/search?q={query}     - Search drugs by name
GET  /api/fda/drugs/{registration_number} - Get drug details
POST /api/fda/verify                     - Verify drug registration
GET  /api/fda/schedules                  - Get drug schedules (OTC, POM, CD)
GET  /api/fda/categories                 - Get drug categories
GET  /api/fda/stats                      - Get registration statistics
GET  /api/fda/manufacturers              - List manufacturers
GET  /api/fda/alerts                     - Get safety alerts
```

### Pharmacy Network
```
GET  /api/pharmacy-network/pharmacies     - List all pharmacies (paginated)
GET  /api/pharmacy-network/pharmacies/search?q=<query> - Search pharmacies
GET  /api/pharmacy-network/pharmacies/{id} - Get pharmacy details
GET  /api/pharmacy-network/regions        - List all 16 Ghana regions
GET  /api/pharmacy-network/chains         - Get pharmacy chains
GET  /api/pharmacy-network/stats          - Get network statistics
```

### Billing & Finance
```
POST /api/billing/invoices               - Create invoice
PUT  /api/billing/invoices/{id}/reverse  - Reverse invoice
POST /api/billing/paystack/initialize    - Initialize Paystack payment
GET  /api/finance/bank-accounts          - Manage hospital bank accounts
```

## Prioritized Backlog

### P0 (Critical)
- [ ] Complete Ambulance Portal UI (fleet management, dispatch, reports)
- [ ] NHIS Pharmacy Claims Integration

### P1 (High Priority)
- [ ] Real Ghana FDA API integration (replace mock data)
- [ ] Notifications for prescription updates
- [ ] Lab results integration

### P2 (Medium Priority)
- [ ] Integration with other payment gateways (Flutterwave, Hubtel)
- [ ] Supply chain inventory for pharmacies

### P3 (Future)
- [ ] National e-Pharmacy platform integration
- [ ] Mobile apps

## Test Credentials
- **Super Admin**: ygtnetworks@gmail.com / test123
- **Hospital IT Admin**: it_admin@yacco.health / test123
- **Biller**: billing@yacco.health / test123
- **Bed Manager**: bed_manager@yacco.health / test123
- **Radiologist**: radiologist@yacco.health / test123
- **Radiology Staff**: radiology_staff@yacco.health / test123
- **Nurse**: test_nurse@yacco.health / test123

## Mocked/Simulated APIs
- **Ghana FDA API**: Using seed data in `fda_module.py` (29 registered drugs) - NOT actual Ghana FDA API
- **Paystack**: Using test keys for payment processing

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
