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

### PatientChart Refactoring (February 6, 2026)
- [x] Created reusable components in `/components/patient-chart/`:
  - `LabsTab.jsx` - Lab orders and results with enhanced integration
  - `VitalsTab.jsx` - Vitals recording with status indicators
  - `ProblemsTab.jsx` - Problem list management
  - `MedicationsTab.jsx` - Medication management
- [x] Reduced main PatientChart.jsx complexity
- [x] Added lab results summary cards with abnormal flagging
- [x] Added trending indicators (High/Low) for lab values

### Real-Time Stock Alerts (February 6, 2026)
- [x] New API endpoint: `/api/supply-chain/alerts` - Get current stock alerts
- [x] New API endpoint: `/api/supply-chain/alerts/send-notifications` - Send notifications to pharmacists
- [x] Alerts track: Low stock, Out of stock, Expiring items (30/90 days)
- [x] Notifications created for pharmacy staff with priority levels
- [x] Stock alerts visible in Pharmacy Portal Inventory tab

### Consolidated Pharmacy Portal (UPDATED - February 6, 2026)
- [x] **Dispensing Tab**: Prescription verification, approval, and dispensing workflow
- [x] **Inventory Tab**: Stock management with Supply Chain integration
  - Add inventory items, receive stock, track batches
  - Low stock and expiring alerts
  - Ghana pharmaceutical suppliers database
- [x] **NHIS Claims Tab**: Integrated NHIS pharmacy claims
  - Member verification (MOCKED)
  - Drug tariff search
  - Claim creation and submission workflow
- [x] **Directory Tab**: National pharmacy network search
  - 133 pharmacies across 16 regions
  - Filter by region, NHIS accreditation, 24-hour service
- Accessible to: `pharmacist`, `pharmacy_tech`, `hospital_admin`

### Ambulance Portal - Role Access Updated (February 6, 2026)
- [x] Moved from IT Admin to clinical roles
- [x] Now accessible to: `nurse`, `nursing_supervisor`, `floor_supervisor`, `hospital_admin`
- [x] Removed from: `super_admin`, `hospital_it_admin`
- [x] Fleet management, request workflow, dispatch tracking

### Navigation Cleanup (February 6, 2026)
- [x] Removed standalone "Pharmacy Directory", "NHIS Claims", "Supply Chain" from sidebar
- [x] These are now integrated tabs within "Pharmacy Portal"
- [x] Cleaner navigation for all roles

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
- [x] **Barcode Lookup** (NEW - February 6, 2026): `/api/fda/lookup/barcode?barcode=GTIN`
  - Returns drug info (name, generic, registration #, manufacturer, category) for known barcodes
  - Mock data includes: Paracetamol, Amoxicillin, Artemether, Metformin, Omeprazole
- [x] API endpoints: `/api/fda/drugs/*`, `/api/fda/verify`, `/api/fda/schedules`, `/api/fda/lookup/barcode`

### IT Admin User Permission Management (February 6, 2026)
- [x] **Module-level permissions** that IT Admin can grant/revoke per user
- [x] Available permissions:
  - `supply_chain:manage` - Full access to inventory, stock receiving, supplier management
  - `supply_chain:view` - View-only access to inventory
  - `billing:manage` - Full access to billing operations
  - `lab:manage` - Full access to laboratory operations
  - `radiology:manage` - Full access to radiology
  - `nhis:claims` - Submit and manage NHIS claims
- [x] API endpoints:
  - `GET /api/hospital/{id}/super-admin/staff/{staff_id}/permissions`
  - `POST /api/hospital/{id}/super-admin/staff/{staff_id}/permissions/grant`
  - `POST /api/hospital/{id}/super-admin/staff/{staff_id}/permissions/revoke`
- [x] UI: Staff dropdown menu → "Manage Permissions" → Toggle permissions dialog

### Barcode Scanning for Inventory (February 6, 2026)
- [x] React-zxing integration for camera-based barcode scanning
- [x] Add Item dialog includes barcode input field + "Scan" button
- [x] When barcode is scanned or entered:
  - Calls FDA lookup API to get drug info
  - Auto-populates: drug_name, drug_code, fda_registration, manufacturer, category
  - Shows toast notification with drug name or "not found" message
- [x] BarcodeScanner component with video preview and scan frame

### Two-Factor Authentication Improvements (February 6, 2026)
- [x] Fixed QR code URL encoding (special characters in email/issuer)
- [x] Improved 2FA setup dialog UI:
  - Clear instructions: "Open your authenticator app and SCAN this QR code"
  - Warning: "Do NOT copy the URL"
  - Recommended apps list (Google Authenticator, Microsoft Authenticator, Authy, 1Password)
  - Manual entry key with copy button and formatted display
  - Account and issuer info displayed

### Ghana Pharmacy Network (February 6, 2026)
- [x] Comprehensive national pharmacy database (133 pharmacies across all 16 regions)
- [x] Pharmacy types: GHS, Private Hospital, Retail, Wholesale, Chain, Mission, Quasi-Government
- [x] Major chains: Ernest Chemist (17 locations), mPharma (7 locations), Kinapharma (5 locations)
- [x] Search and filter by region, city, ownership type
- [x] Filter by NHIS accreditation (129 pharmacies), 24-hour service (26), delivery available (26)
- [x] Pharmacy Directory UI at `/pharmacy-directory`
- [x] API endpoints: `/api/pharmacy-network/*`

### Location-Based Pharmacy Routing for e-Prescriptions (February 6, 2026)
- [x] **Enhanced e-Prescription Dialog** with pharmacy selection:
  - Diagnosis/indication field (required)
  - Priority dropdown (Routine, Urgent, STAT)
  - Clinical notes textarea
  - Medication section with full details (name, route, dosage, frequency, duration, quantity, special instructions)
  - "Add Medication" to add multiple drugs to one prescription
  - **"Route to Pharmacy (Optional)"** section with embedded pharmacy search
- [x] **Enhanced "Send to Pharmacy" Dialog** with location-based filtering:
  - Priority ordering: Same hospital pharmacy → Same district → Same region → National
  - Region dropdown filter (all 16 Ghana regions)
  - Ownership type filter (Public, Private, Chain, Hospital-Based)
  - NHIS accreditation toggle filter
  - 24-hour service toggle filter
  - Search by pharmacy name, city, or address
  - Shows pharmacy count and "Load More" for pagination
  - Selected pharmacy confirmation with clear button
  - Additional routing notes for pharmacist
- [x] **Fallback Routing Rules**:
  - Hospital's own pharmacy shown as "Recommended" priority option
  - If no pharmacy selected, prescription stays in "pending_verification" status
- [x] **Audit Logging**: Tracks pharmacy selection, routing time, changes

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

### Billing Shifts & Financial Controls (February 7, 2026)
```
POST /api/billing-shifts/clock-in        - Start billing shift
POST /api/billing-shifts/clock-out       - End billing shift
GET  /api/billing-shifts/active          - Get active shift
GET  /api/billing-shifts/my-shifts       - Get shift history
GET  /api/billing-shifts/dashboard/biller - Biller shift-scoped dashboard
GET  /api/billing-shifts/dashboard/senior-biller - Senior biller department dashboard (NEW)
GET  /api/billing-shifts/dashboard/admin  - Admin full financial dashboard
GET  /api/billing-shifts/all-shifts      - All shifts (admin only)
POST /api/billing-shifts/shifts/{id}/reconcile - Reconcile shift
POST /api/billing-shifts/shifts/{id}/flag - Flag shift discrepancy
GET  /api/billing-shifts/audit-logs      - Billing audit logs
```

**Features Implemented:**
- [x] **Shift Clock-In/Out**: Billers clock in to track shift-specific collections
- [x] **Shift-Scoped KPIs**: Invoices generated, payments received, cash/MoMo/card/insurance breakdown
- [x] **Admin Financial Dashboard**: Daily/Weekly/Monthly revenue, payment mode distribution
- [x] **Revenue Trend Charts**: Area chart for weekly revenue, Pie chart for payment distribution, Bar chart for daily transactions (Feb 7)
- [x] **Outstanding Balances (Persistent)**: Unpaid invoices, pending insurance - NOT reset with shifts
- [x] **Shift Reconciliation UI**: Admins can reconcile shifts with actual cash verification
- [x] **Shift Flagging**: Flag shifts with discrepancies for investigation
- [x] **Billing Audit Logs**: Track invoice creation, payments, shift events
- [x] **Print Receipt with Hospital Logo**: Generate receipts with hospital name, address, logo (Feb 7)
- [x] **Senior Biller Dashboard**: Department-wide view for senior billers showing all active shifts (Feb 7)
- [x] **Audit & Compliance UI**: Searchable/filterable audit log with timeline view and summary stats (Feb 7)

**Data Visibility Rules:**
| Role | Own Shift | All Shifts | Daily/Weekly/Monthly | Outstanding |
|------|-----------|------------|---------------------|-------------|
| Biller | ✅ | ❌ | ❌ | ✅ |
| Senior Biller | ✅ | ✅ (dept) | ❌ | ✅ |
| Hospital Admin | ✅ | ✅ | ✅ | ✅ |
| Finance Manager | ✅ | ✅ | ✅ | ✅ |

### Nurse Supervisor Portal Enhancements (February 7, 2026)
- [x] **Bed Management Tab**: Integrated bed census display in Nursing Supervisor Dashboard
  - Shows Total Beds, Available, Occupied, Reserved, Occupancy %
  - Ward Census with individual ward details and occupancy bars
  - Quick access to Full Bed Management page
- [x] **Nurse Assignment Fix**: Nurse list now populates correctly in "Assign Patient to Nurse" dialog
  - Shows all nurses with on-shift indicators (green = on shift, gray = off duty)
  - Grouped by on-shift and available nurses
- [x] **Ambulance Request Patient Search**: Enhanced Request Ambulance dialog
  - Toggle between "Search Existing Patient" and "Manual Entry (New Patient)"
  - Patient search by name or MRN
  - Auto-populates patient info when selected
- [x] **Ambulance Vehicle Registration**: Nursing Supervisors can now register ambulance vehicles
  - Added `nursing_supervisor` to allowed_roles in ambulance_module.py
  - No more "Access denied" error for vehicle registration
- [x] **Clock In/Out for Supervisors**: Supervisors can now clock in/out their own shifts (Feb 7)
- [x] **Scrollable Dialogs**: Clock-out and Force Clock-out dialogs now scroll properly (Feb 7)

### Hospital Info Enhancements (February 7, 2026)
- [x] `/api/hospital/info` endpoint now returns `logo_url` field
- [x] Print Receipt displays hospital logo if available
- [x] Receipt shows hospital name, address, contact info dynamically

## Prioritized Backlog

### P0 (Critical)
- [x] ~~Complete Ambulance Portal UI~~ ✅ DONE
- [x] ~~NHIS Pharmacy Claims Integration~~ ✅ DONE
- [x] ~~Supply Chain Inventory Module~~ ✅ DONE
- [x] ~~Nurse Supervisor Portal Enhancements~~ ✅ DONE (Feb 7, 2026)
- [x] ~~Billing Shift-Based Financial Controls~~ ✅ DONE (Feb 7, 2026)
- [x] ~~Senior Biller Dashboard & Reconciliation UI~~ ✅ DONE (Feb 7, 2026)
- [x] ~~Hospital Logo on Receipts~~ ✅ DONE (Feb 7, 2026)

### P1 (High Priority)
- [ ] Real Ghana FDA API integration (replace mock data)
- [ ] Real NHIS API integration (replace mock data)
- [ ] Complete PatientChart refactoring (remaining tabs: Overview, Notes, Orders, Imaging, Pharmacy)
- [x] ~~Notifications for prescription updates~~ ✅ DONE
- [x] ~~Stock alerts for pharmacists~~ ✅ DONE
- [x] ~~Advanced Admin Dashboard Widgets (graphs/charts for revenue trends)~~ ✅ DONE (Feb 7, 2026)
- [x] ~~Audit & Compliance Logging UI (view detailed audit logs for financial actions)~~ ✅ DONE (Feb 7, 2026)

### P2 (Medium Priority)
- [ ] Integration with other payment gateways (Flutterwave, Hubtel)
- [ ] Email notifications (Resend integration ready)
- [ ] Real-time notifications via Resend
- [ ] Component refactoring (BillingPage.jsx, NursingSupervisorDashboard.jsx)

### P3 (Future)
- [ ] National e-Pharmacy platform integration
- [ ] Mobile apps

## Test Credentials
- **Super Admin**: ygtnetworks@gmail.com / test123
- **Hospital IT Admin**: it_admin@yacco.health / test123
- **Nursing Supervisor**: nursing_supervisor@yacco.health / test123
- **Biller**: biller@yacco.health / test123
- **Bed Manager**: bed_manager@yacco.health / test123
- **Radiologist**: radiologist@yacco.health / test123
- **Radiology Staff**: radiology_staff@yacco.health / test123
- **Nurse**: test_nurse@yacco.health / test123
- **Pharmacist**: pharmacist@yacco.health / test123

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
