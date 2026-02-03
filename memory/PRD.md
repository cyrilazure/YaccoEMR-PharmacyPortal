# Yacco EMR - Product Requirements Document

## Project Overview
**Name:** Yacco EMR - Electronic Medical Records System  
**Version:** 1.0.0 MVP  
**Created:** February 3, 2026  
**Last Updated:** February 3, 2026

## Problem Statement
Build a comprehensive Electronic Medical Records (EMR) system similar to Epic EMR with core clinical modules, multi-role support, scheduling, and AI-assisted documentation.

## User Personas
1. **Physicians** - Primary clinical users who document patient encounters, place orders, review results
2. **Nurses** - Execute orders, administer medications, document care, monitor patients
3. **Schedulers** - Manage appointments, patient registration, capacity
4. **Administrators** - Oversee system, manage users, view analytics

## Core Requirements (Static)
- JWT-based authentication with role-based access
- Patient management (registration, search, demographics)
- Clinical documentation (notes, vitals, problems, medications, allergies)
- Orders management (lab, imaging, medication orders)
- Appointment scheduling
- AI-assisted documentation using GPT-5.2
- Analytics dashboard

## Tech Stack
- **Frontend:** React 19, Tailwind CSS, shadcn/ui components
- **Backend:** FastAPI (Python)
- **Database:** MongoDB
- **AI:** OpenAI GPT-5.2 via Emergent LLM Key
- **Auth:** JWT-based authentication

## What's Been Implemented (MVP)

### Backend (server.py)
- [x] JWT authentication (register, login, /auth/me)
- [x] User management with roles (physician, nurse, scheduler, admin)
- [x] Patient CRUD operations with search
- [x] Vitals recording and retrieval
- [x] Problems/diagnoses management
- [x] Medications management
- [x] Allergies management
- [x] Clinical notes with SOAP format
- [x] Orders management (lab, imaging, medication)
- [x] Appointments scheduling with status updates
- [x] Dashboard statistics endpoint
- [x] AI-assisted note generation endpoint

### Frontend Pages
- [x] Login page with registration (Login.jsx)
- [x] Main layout with sidebar navigation (Layout.jsx)
- [x] Dashboard with stats and recent data (Dashboard.jsx)
- [x] Patients list with search and registration (Patients.jsx)
- [x] Patient chart with tabs (PatientChart.jsx)
  - Overview, Vitals, Problems, Meds, Notes, Orders
- [x] Appointments scheduling (Appointments.jsx)
- [x] Orders management with filtering (Orders.jsx)
- [x] Analytics with charts (Analytics.jsx)

### Design
- Clean medical/healthcare light theme
- Manrope + Inter fonts
- Sky blue accent color
- Responsive sidebar navigation

## Testing Results
- Backend: 100% pass rate
- Frontend: 95% pass rate
- All core workflows functional

## Prioritized Backlog

### P0 (Critical - Not Yet Implemented)
- [ ] Password reset functionality
- [ ] Session management (token refresh)

### P1 (High Priority)
- [ ] E-prescribing integration
- [ ] Lab result integration
- [ ] Imaging viewer (DICOM)
- [ ] MyChart patient portal
- [ ] Telehealth video visits

### P2 (Medium Priority)
- [ ] Billing/Revenue Cycle integration
- [ ] Care coordination tools
- [ ] Population health features
- [ ] Audit logging for HIPAA
- [ ] Role permission management

### P3 (Future)
- [ ] Mobile apps (Haiku/Canto equivalents)
- [ ] Interoperability (FHIR, HL7)
- [ ] Clinical decision support
- [ ] Drug interaction checking
- [ ] Report builder

## Next Tasks
1. Implement password reset flow
2. Add token refresh for long sessions
3. Build MyChart patient portal
4. Integrate real lab result feeds
5. Add HIPAA audit logging

## API Endpoints
```
POST /api/auth/register - Register new user
POST /api/auth/login - Login user
GET  /api/auth/me - Get current user

GET  /api/patients - List/search patients
POST /api/patients - Create patient
GET  /api/patients/{id} - Get patient
PUT  /api/patients/{id} - Update patient

POST /api/vitals - Record vitals
GET  /api/vitals/{patient_id} - Get patient vitals

POST /api/problems - Add problem
GET  /api/problems/{patient_id} - Get patient problems
PUT  /api/problems/{id} - Update problem

POST /api/medications - Add medication
GET  /api/medications/{patient_id} - Get patient meds
PUT  /api/medications/{id} - Update medication

POST /api/allergies - Add allergy
GET  /api/allergies/{patient_id} - Get allergies

POST /api/notes - Create clinical note
GET  /api/notes/{patient_id} - Get patient notes
PUT  /api/notes/{id} - Update note
POST /api/notes/{id}/sign - Sign note

POST /api/orders - Place order
GET  /api/orders - List orders
PUT  /api/orders/{id}/status - Update status
PUT  /api/orders/{id}/result - Add result

POST /api/appointments - Schedule appointment
GET  /api/appointments - List appointments
PUT  /api/appointments/{id}/status - Update status

GET  /api/dashboard/stats - Dashboard statistics
POST /api/ai/generate-note - AI-assisted note generation
```

## Environment Variables
```
# Backend (.env)
MONGO_URL=mongodb://localhost:27017
DB_NAME=test_database
JWT_SECRET=<secret>
EMERGENT_LLM_KEY=<key>

# Frontend (.env)
REACT_APP_BACKEND_URL=<url>
```
