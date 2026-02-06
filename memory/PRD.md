# Yacco EMR - Product Requirements Document

## Project Overview
**Name:** Yacco EMR - Electronic Medical Records System  
**Version:** 1.4.0  
**Created:** February 3, 2026  
**Last Updated:** February 6, 2026

## Problem Statement
Build a comprehensive Electronic Medical Records (EMR) system similar to Epic EMR with core clinical modules, multi-role support, scheduling, AI-assisted documentation, and healthcare interoperability (FHIR). Extended with Ghana-specific features including NHIS integration, regional pharmacy network, Ghana FDA drug verification, ambulance fleet management, and Paystack payment processing.

## User Personas
1. **Physicians** - Primary clinical users who document patient encounters, place orders, review results
2. **Nurses** - Execute orders, administer medications, document care, monitor patients (MAR workflow)
3. **Schedulers** - Manage appointments, patient registration, capacity
4. **Administrators** - Oversee system, manage users, view analytics, monitor system health
5. **Pharmacists** - Manage e-prescriptions, dispense medications, verify FDA registration, manage NHIS claims
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

### NHIS Pharmacy Claims Integration (NEW - February 6, 2026)
- [x] NHIS member verification (MOCKED - sample data)
- [x] Ghana NHIS drug tariff database (30+ drugs with approved prices)
- [x] Pharmacy claim creation with drug selection
- [x] Claim status workflow: draft → submitted → approved/rejected → paid
- [x] Claims dashboard with financial summaries
- [x] Drug tariff search and coverage status
- [x] NHIS Claims Portal UI at `/nhis-claims`
- [x] API endpoints: `/api/nhis/verify-member`, `/api/nhis/tariff`, `/api/nhis/claims/*`

### Supply Chain & Inventory Module (NEW - February 6, 2026)
- [x] Inventory item catalog management
- [x] Stock batch tracking with expiry dates
- [x] Stock receiving workflow
- [x] Stock movement history
- [x] Purchase order management
- [x] Supplier database with Ghana pharmaceutical suppliers
- [x] Low stock and expiring items alerts
- [x] Stock valuation reports
- [x] Supply Chain Portal UI at `/supply-chain`
- [x] API endpoints: `/api/supply-chain/inventory`, `/api/supply-chain/stock/*`, `/api/supply-chain/suppliers`

### Notifications Module (NEW - February 6, 2026)
- [x] Real-time notification creation
- [x] Notification types: prescription updates, alerts, messages
- [x] Unread count tracking
- [x] Mark as read functionality
- [x] Broadcast notifications for admin
- [x] API endpoints: `/api/notifications`, `/api/notifications/unread-count`

### Ambulance Portal (UPDATED - February 6, 2026)
- [x] Fleet management with vehicle registration
- [x] Ambulance request workflow
- [x] Dispatch management
- [x] Trip status tracking (requested → approved → dispatched → completed)
- [x] Dashboard with fleet and request statistics
- [x] Ambulance Portal UI at `/ambulance`
- [x] API endpoints: `/api/ambulance/vehicles`, `/api/ambulance/requests`, `/api/ambulance/dashboard`

### E-Prescription Routing (February 6, 2026)
- [x] E-prescription routing from Patient Chart to external pharmacies
- [x] Pharmacy selection with search from Ghana Pharmacy Network (133 pharmacies)
- [x] Prescription status tracking: sent → accepted/rejected → filled
- [x] Prescription tracking by RX number with timeline
- [x] Pharmacy accept/reject/fill workflow
- [x] Patient Chart "Pharmacy" tab with active prescriptions and routing status
- [x] API endpoints: `/api/prescriptions/{id}/send-to-pharmacy`, `/api/prescriptions/tracking/{rx}`

### Ghana FDA Integration (February 6, 2026)
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

### NHIS Claims (NEW)
```
POST /api/nhis/verify-member           - Verify NHIS membership
GET  /api/nhis/member/{id}             - Get member details
GET  /api/nhis/tariff                  - Get drug tariff list
POST /api/nhis/claims/pharmacy         - Create pharmacy claim
GET  /api/nhis/claims                  - List claims
POST /api/nhis/claims/{id}/submit      - Submit claim to NHIS
PUT  /api/nhis/claims/{id}/status      - Update claim status
GET  /api/nhis/dashboard               - Get NHIS dashboard
```

### Supply Chain (NEW)
```
GET  /api/supply-chain/inventory       - List inventory items
POST /api/supply-chain/inventory       - Add inventory item
POST /api/supply-chain/stock/receive   - Receive stock
GET  /api/supply-chain/stock/batches   - Get stock batches
GET  /api/supply-chain/suppliers       - List suppliers
POST /api/supply-chain/suppliers/seed  - Seed Ghana suppliers
GET  /api/supply-chain/dashboard       - Get inventory dashboard
GET  /api/supply-chain/reports/expiring - Expiring items report
```

### Notifications (NEW)
```
GET  /api/notifications                - Get user notifications
GET  /api/notifications/unread-count   - Get unread count
POST /api/notifications                - Create notification
PUT  /api/notifications/{id}/read      - Mark as read
PUT  /api/notifications/mark-all-read  - Mark all as read
POST /api/notifications/broadcast      - Broadcast to users
```

### Ambulance
```
GET  /api/ambulance/vehicles           - List fleet
POST /api/ambulance/vehicles           - Register vehicle
GET  /api/ambulance/requests           - List requests
POST /api/ambulance/requests           - Create request
PUT  /api/ambulance/requests/{id}/approve - Approve request
POST /api/ambulance/requests/{id}/dispatch - Dispatch ambulance
PUT  /api/ambulance/requests/{id}/update-status - Update trip status
GET  /api/ambulance/dashboard          - Get operations dashboard
```

### E-Prescription Routing
```
POST /api/prescriptions/{id}/send-to-pharmacy - Route prescription to external pharmacy
GET  /api/prescriptions/tracking/{rx_number}  - Track prescription by RX number
GET  /api/prescriptions/patient/{id}/routed   - Get patient's routed prescriptions
GET  /api/prescriptions/routing/{id}/status   - Get routing status
PUT  /api/prescriptions/routing/{id}/accept   - Pharmacy accepts prescription
PUT  /api/prescriptions/routing/{id}/reject   - Pharmacy rejects prescription
PUT  /api/prescriptions/routing/{id}/fill     - Pharmacy marks as filled
```

### Ghana FDA Integration
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
- [x] ~~Complete Ambulance Portal UI~~ ✅ DONE
- [x] ~~NHIS Pharmacy Claims Integration~~ ✅ DONE
- [x] ~~Supply Chain Inventory Module~~ ✅ DONE

### P1 (High Priority)
- [ ] Real Ghana FDA API integration (replace mock data)
- [ ] Real NHIS API integration (replace mock data)
- [x] ~~Notifications for prescription updates~~ ✅ DONE
- [ ] Lab results integration

### P2 (Medium Priority)
- [ ] Integration with other payment gateways (Flutterwave, Hubtel)
- [ ] Email notifications (Resend integration ready)

### P3 (Future)
- [ ] National e-Pharmacy platform integration
- [ ] Mobile apps
- [ ] Refactor PatientChart.jsx (>1700 lines)

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
- **NHIS Member Database**: Using sample data in `nhis_claims_module.py` - NOT actual NHIS API
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

## Code Architecture
```
/app/
├── backend/
│   ├── server.py                   # Main FastAPI app
│   ├── nhis_claims_module.py       # NHIS pharmacy claims
│   ├── supply_chain_module.py      # Inventory management
│   ├── notifications_module.py     # Real-time notifications
│   ├── ambulance_module.py         # Emergency transport
│   ├── pharmacy_network_module.py  # National pharmacy database
│   ├── fda_module.py               # Ghana FDA drug registry (mock)
│   ├── prescription_module.py      # E-prescription routing
│   ├── billing_module.py           # Billing & finance
│   ├── bed_management_module.py    # Ward management
│   ├── radiology_module.py         # Imaging module
│   └── ...
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── NHISClaimsPortal.jsx    # NHIS claims UI
│       │   ├── SupplyChainPortal.jsx   # Inventory UI
│       │   ├── AmbulancePortal.jsx     # Emergency transport UI
│       │   ├── PharmacyDirectory.jsx   # Pharmacy search
│       │   ├── PatientChart.jsx        # Patient chart with Pharmacy tab
│       │   └── ...
│       └── lib/
│           └── api.js                  # API client
└── memory/
    └── PRD.md                          # This file
```
