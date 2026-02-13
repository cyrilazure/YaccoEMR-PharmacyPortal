# Yacco EMR - Product Requirements Document

## Project Overview
Yacco Health is a comprehensive Electronic Medical Records (EMR) and Pharmacy Portal for Ghana's healthcare network. It connects hospitals and pharmacies across all 16 administrative regions.

## Current Status: Active Development
Last Updated: February 13, 2026

---

## Core Features

### Authentication & Access Control
- **Multi-step Login Flow**: Region → Hospital → Location → Credentials
- **Role-Based Access Control**: Super Admin, IT Admin, Hospital Admin, Physician, Nurse, Nursing Supervisor, Floor Supervisor, Pharmacist, Biller, Scheduler, Receptionist, Bed Manager
- **OTP Verification**: **TEMPORARILY DISABLED** (can be re-enabled via `OTP_ENABLED=true` in `.env`)
- **JWT Token Authentication**
- **Patient Chart Access Control**: RBAC enforced for patient documentation access
- **Confidentiality Notice**: HIPAA-style privacy notice displayed on chart access

### Healthcare Interoperability
- **HL7 v2.x ADT Messaging**: Admission, Discharge, Transfer events
- **FHIR R4 Support**: Patient, Observation, Encounter resources
- **DICOM/PACS Integration**: Medical imaging storage and retrieval
- **Google Cloud Healthcare API Integration**: Connected to `my-second-project-36094`

### Clinical Documentation (NEW - Phase 1 Complete)
- **Nursing Documentation**:
  - Assessment, Vitals Summary, Progress Notes, Care Plans
  - Shift Reports, Intake/Output, Pain Assessment
  - Fall Risk, Skin Assessment, Wound Care
  - Patient Education, Discharge Instructions
  - Sign/Lock documentation (immutable once signed)
  
- **Physician Documentation**:
  - History & Physical (H&P)
  - Progress Notes, Consultations
  - Procedure Notes, Operative Notes
  - Discharge Summaries, Order Notes, Addendums
  - SOAP note format with all standard fields
  - Sign/Lock documentation (immutable once signed)

- **Cross-Role Visibility**:
  - Physicians: Full view of nursing documentation (read-only)
  - Nurses: Full view of physician documentation (read-only)
  - Supervisors: Unit overview with all documentation access
  
- **Audit Logging**:
  - All chart access events logged (view, create, edit, sign)
  - Access denial logging for security monitoring
  - Immutable audit trail for compliance

### Clinical Features
- Patient Registration & Management
- Electronic Medical Records
- Lab Results & Radiology
- e-Prescribing
- NHIS Claims Integration
- Telehealth Video Consultations
- Voice Dictation

### Administrative Features
- Staff Account Management
- Bed Management
- Ambulance Dispatch
- Supply Chain & Inventory
- Billing & Finance

---

## Recent Changes (February 13, 2026)

### Completed - Phase 1: Clinical Documentation & RBAC
1. ✅ **Clinical Documentation Module**: `/app/backend/clinical_documentation_module.py`
   - Full CRUD for Nursing Documentation with 12 document types
   - Full CRUD for Physician Documentation with 8 document types (SOAP format)
   - Patient Assignment management for access control
   - Comprehensive audit logging

2. ✅ **Patient Chart UI Enhancement**: `/app/frontend/src/pages/PatientChart.jsx`
   - New "Nursing" and "Physician" tabs in tabbed interface
   - Role-based "Add Documentation" buttons
   - Read-only indicators for cross-role access
   - Full documentation forms with all clinical fields

3. ✅ **Confidentiality Notice Modal**:
   - HIPAA-style privacy notice on chart access
   - Patient name/MRN displayed
   - Acknowledgment required before proceeding
   - Session-based persistence

4. ✅ **Frontend API Integration**: `/app/frontend/src/lib/api.js`
   - `clinicalDocsAPI` object with all endpoints
   - Nursing/Physician doc CRUD operations
   - Audit log retrieval for admins

5. ✅ **Testing Complete**: 100% pass rate
   - 12 backend tests passed
   - All frontend flows validated
   - RBAC correctly enforced

---

## Completed (February 12, 2026)
3. ✅ **HL7 ADT Portal**: New frontend page created at `/app/frontend/src/pages/HL7ADTPortal.jsx`
   - Accessible by: IT Admin, Nursing Supervisor, Physician, Nurse, Floor Supervisor
   - Features: ADT Events, HL7 Messages, Bed Census views
4. ✅ **User Credentials Seeded**: All hospital staff from user's list added to database
5. ✅ **JWT Secret Aligned**: Fixed mismatch between `security/__init__.py` and `region_module.py`

### Pending
- Patient Referral Enhancement (already exists, may need additional features)
- Full verification of Healthcare Integrations

---

## Test Credentials

### Super Admin
- Email: `ygtnetworks@gmail.com`
- Password: `test123`

### Greater Accra - Korle Bu Teaching Hospital
- **IT Admin**: `cyrilfiifi@gmail.com` / `FrwLSe6qEpaEytRV`
- **Physician**: `testdemo@test.com` / `tBwt43K3fhQ7h4_O`
- **Nurse Supervisor**: `nursing_supervisor@yacco.health` / `saY_m0srjzMJbIkw`
- **Pharmacist**: `pharmacist@yacco.health` / `T1bJaq5U5iuv5Op4`

### Greater Accra - Ashaiman Polyclinic
- **IT Admin**: `ashaiman@itadmin.com` / `ZXHoe0HxwupLPzvv`
- **Physician ICU**: `physicianicu@pysicianicu.com` / `q4EqVHzNEiobz6NC`
- **Nurse Supervisor**: `nursesupervisor@nursesupervisor.com` / `CbboeUs7oxiI2gaX`

### Northern Region - Tamale Teaching Hospital
- **IT Admin**: `itadmin@yacco.reginal.com` / `ixYbFGkLYSLHqqJA`
- **Physician**: `physician22@yaccoregional.com` / `KS-znfVr6KJTQ_GP`

### Eastern Region - Eastern Regional Health Center
- **IT Admin**: `eastern@itadmin.com` / `pBE12jXrkwi3M-8a`
- **Physician**: `physicianicu@physician.com` / `-VR8OvTy3vB1RDnr`

---

## API Endpoints

### Authentication
- `POST /api/regions/auth/login` - Staff login (Region-based)
- `POST /api/v1/auth/super-admin-login` - Super admin login

### Google Healthcare API
- `GET /api/google-healthcare/config` - Get configuration
- `GET /api/google-healthcare/status` - Connection status
- `POST /api/google-healthcare/datasets/create` - Create dataset (IT Admin)
- `POST /api/google-healthcare/fhir-store/create` - Create FHIR store
- `POST /api/google-healthcare/fhir/patients` - Create FHIR Patient
- `GET /api/google-healthcare/fhir/patients` - Search patients
- `POST /api/google-healthcare/hl7v2/messages/ingest` - Ingest HL7v2 message
- `GET /api/google-healthcare/hl7v2/messages` - List messages
- `POST /api/google-healthcare/dicom/instances/store` - Store DICOM
- `GET /api/google-healthcare/dicom/instances` - Search DICOM

### HL7 v2 ADT
- `POST /api/hl7/adt/admit` - Patient admission
- `POST /api/hl7/adt/transfer` - Patient transfer
- `POST /api/hl7/adt/discharge` - Patient discharge
- `GET /api/hl7/adt/events` - List ADT events
- `GET /api/hl7/messages` - List HL7 messages

### Clinical Documentation (NEW)
- `GET /api/clinical-docs/doc-types/nursing` - Get nursing documentation types
- `GET /api/clinical-docs/doc-types/physician` - Get physician documentation types
- `GET /api/clinical-docs/nursing/{patient_id}` - Get nursing docs for patient
- `POST /api/clinical-docs/nursing` - Create nursing documentation
- `PUT /api/clinical-docs/nursing/{doc_id}` - Update nursing documentation
- `POST /api/clinical-docs/nursing/{doc_id}/sign` - Sign nursing documentation
- `GET /api/clinical-docs/physician/{patient_id}` - Get physician docs for patient
- `POST /api/clinical-docs/physician` - Create physician documentation
- `PUT /api/clinical-docs/physician/{doc_id}` - Update physician documentation
- `POST /api/clinical-docs/physician/{doc_id}/sign` - Sign physician documentation
- `GET /api/clinical-docs/assignments/{patient_id}` - Get patient assignments
- `POST /api/clinical-docs/assignments` - Create patient assignment
- `DELETE /api/clinical-docs/assignments/{id}` - End patient assignment
- `GET /api/clinical-docs/audit-logs/{patient_id}` - Get patient audit logs
- `GET /api/clinical-docs/audit-logs` - Get all audit logs (admin)
- `GET /api/clinical-docs/audit-logs/suspicious` - Get suspicious activity alerts

### Patient Referrals
- `GET /api/referrals/` - List referrals
- `POST /api/referrals/` - Create referral
- `GET /api/referrals/{id}` - Get referral details

---

## Environment Configuration

### Backend (.env)
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
CORS_ORIGINS="*"
OTP_ENABLED=false
GOOGLE_HEALTHCARE_CREDENTIALS=/app/backend/google_healthcare_credentials.json
GOOGLE_CLOUD_PROJECT=my-second-project-36094
```

### Frontend (.env)
```
REACT_APP_BACKEND_URL=https://emr-supervisor-dash.preview.emergentagent.com
WDS_SOCKET_PORT=443
```

---

## Architecture

```
/app/
├── backend/                  # FastAPI backend
│   ├── security/             # Authentication & authorization
│   ├── hl7_module.py         # HL7 v2 ADT module
│   ├── google_healthcare_module.py  # Google Healthcare API
│   ├── referral_module.py    # Patient referrals
│   ├── region_module.py      # Region-based login
│   └── server.py             # Main application
├── frontend/                 # React frontend
│   └── src/
│       ├── pages/
│       │   ├── HL7ADTPortal.jsx     # HL7/ADT dashboard
│       │   ├── PatientReferralPage.jsx
│       │   └── Layout.jsx           # Navigation
│       └── components/ui/    # Shadcn UI components
```

---

## Future Enhancements

1. **Google Healthcare API** - Full FHIR resource management
2. **HL7 Message Routing** - Automated message routing between facilities
3. **DICOM Viewer** - Web-based DICOM image viewer
4. **Interoperability Dashboard** - Real-time message monitoring
5. **OTP Re-enablement** - Make OTP configurable per hospital/role
