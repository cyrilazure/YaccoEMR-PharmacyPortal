import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('yacco_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('yacco_token');
      localStorage.removeItem('yacco_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Authentication APIs
export const authAPI = {
  register: (userData) => api.post('/auth/register', userData),
  login: (email, password, totpCode = null) => api.post('/auth/login', { email, password, totp_code: totpCode }),
  loginEnhanced: (credentials) => api.post('/auth/login/enhanced', credentials),
  getMe: () => api.get('/auth/me'),
  refreshToken: (refreshToken) => api.post('/auth/refresh', { refresh_token: refreshToken }),
  logout: () => api.post('/auth/logout'),
  logoutAll: () => api.post('/auth/logout/all'),
  validateToken: () => api.post('/auth/validate'),
  changePassword: (currentPassword, newPassword) => api.post('/auth/password/change', { 
    current_password: currentPassword, 
    new_password: newPassword 
  }),
  getSessions: () => api.get('/auth/sessions'),
  revokeSession: (sessionId) => api.delete(`/auth/sessions/${sessionId}`),
  checkPermission: (permission) => api.get(`/auth/permissions/check/${permission}`),
  getPermissionGroups: () => api.get('/auth/groups'),
};

// Patient APIs
export const patientAPI = {
  getAll: (search) => api.get('/patients', { params: { search } }),
  getById: (id) => api.get(`/patients/${id}`),
  create: (data) => api.post('/patients', data),
  update: (id, data) => api.put(`/patients/${id}`, data),
};

// Vitals APIs
export const vitalsAPI = {
  getByPatient: (patientId) => api.get(`/vitals/${patientId}`),
  create: (data) => api.post('/vitals', data),
};

// Problems APIs
export const problemsAPI = {
  getByPatient: (patientId) => api.get(`/problems/${patientId}`),
  create: (data) => api.post('/problems', data),
  update: (id, data) => api.put(`/problems/${id}`, data),
};

// Medications APIs
export const medicationsAPI = {
  getByPatient: (patientId) => api.get(`/medications/${patientId}`),
  create: (data) => api.post('/medications', data),
  update: (id, data) => api.put(`/medications/${id}`, data),
};

// Allergies APIs
export const allergiesAPI = {
  getByPatient: (patientId) => api.get(`/allergies/${patientId}`),
  create: (data) => api.post('/allergies', data),
};

// Clinical Notes APIs
export const notesAPI = {
  getByPatient: (patientId) => api.get(`/notes/${patientId}`),
  create: (data) => api.post('/notes', data),
  update: (id, data) => api.put(`/notes/${id}`, data),
  sign: (id) => api.post(`/notes/${id}/sign`),
};

// Orders APIs
export const ordersAPI = {
  getAll: (params) => api.get('/orders', { params }),
  create: (data) => api.post('/orders', data),
  updateStatus: (id, status) => api.put(`/orders/${id}/status`, null, { params: { status } }),
  addResult: (id, result) => api.put(`/orders/${id}/result`, null, { params: { result } }),
};

// Appointments APIs
export const appointmentsAPI = {
  getAll: (params) => api.get('/appointments', { params }),
  create: (data) => api.post('/appointments', data),
  updateStatus: (id, status) => api.put(`/appointments/${id}/status`, null, { params: { status } }),
};

// Users APIs
export const usersAPI = {
  getAll: () => api.get('/users'),
  getById: (id) => api.get(`/users/${id}`),
};

// Dashboard APIs
export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
};

// AI APIs
export const aiAPI = {
  generateNote: (data) => api.post('/ai/generate-note', data),
};

// Lab APIs
export const labAPI = {
  // Orders
  createOrder: (data) => api.post('/lab/orders', data),
  getPatientOrders: (patientId) => api.get(`/lab/orders/${patientId}`),
  getAllOrders: (params) => api.get('/lab/orders', { params }),
  updateOrderStatus: (orderId, status) => api.put(`/lab/orders/${orderId}/status`, null, { params: { status } }),
  // Results
  simulateResults: (orderId, scenario = 'normal') => api.post(`/lab/results/simulate/${orderId}`, null, { params: { scenario } }),
  getPatientResults: (patientId, panelCode) => api.get(`/lab/results/${patientId}`, { params: { panel_code: panelCode } }),
  getResultByOrder: (orderId) => api.get(`/lab/results/order/${orderId}`),
  // Panels & Definitions
  getPanels: () => api.get('/lab/panels'),
  getTestDefinitions: (category) => api.get('/lab/test-definitions', { params: { category } }),
  // HL7 ORU
  receiveHL7ORU: (message) => api.post('/lab/hl7/oru', message),
};

// Telehealth APIs
export const telehealthAPI = {
  // Configuration
  getConfig: () => api.get('/telehealth/config'),
  // Sessions
  createSession: (data) => api.post('/telehealth/sessions', data),
  getSessions: (params) => api.get('/telehealth/sessions', { params }),
  getSession: (sessionId) => api.get(`/telehealth/sessions/${sessionId}`),
  joinSession: (sessionId, data) => api.post(`/telehealth/sessions/${sessionId}/join`, data),
  startSession: (sessionId) => api.post(`/telehealth/sessions/${sessionId}/start`),
  endSession: (sessionId, notes) => api.post(`/telehealth/sessions/${sessionId}/end`, null, { params: { notes } }),
  updateStatus: (sessionId, status) => api.put(`/telehealth/sessions/${sessionId}/status`, null, { params: { status } }),
  getParticipants: (sessionId) => api.get(`/telehealth/sessions/${sessionId}/participants`),
  createFromAppointment: (appointmentId) => api.post(`/telehealth/sessions/from-appointment/${appointmentId}`),
  getUpcoming: () => api.get('/telehealth/upcoming'),
  // Dyte (when enabled)
  createDyteMeeting: (sessionId) => api.post('/telehealth/dyte/create-meeting', null, { params: { session_id: sessionId } }),
  getDyteStatus: () => api.get('/telehealth/dyte/status'),
};

// Organization/Multi-tenant APIs
export const organizationAPI = {
  // Self-service registration (public)
  register: (data) => api.post('/organizations/register', data),
  
  // Super Admin endpoints
  listAll: (params) => api.get('/organizations', { params }),
  getPending: () => api.get('/organizations/pending'),
  approve: (orgId, data) => api.post(`/organizations/${orgId}/approve`, data),
  reject: (orgId, data) => api.post(`/organizations/${orgId}/reject`, data),
  suspend: (orgId, reason) => api.post(`/organizations/${orgId}/suspend`, null, { params: { reason } }),
  reactivate: (orgId) => api.post(`/organizations/${orgId}/reactivate`),
  createByAdmin: (data, autoApprove = true) => api.post('/organizations/create-by-admin', data, { params: { auto_approve: autoApprove } }),
  getPlatformStats: () => api.get('/organizations/stats/platform'),
  
  // Hospital Admin endpoints
  getMyOrganization: () => api.get('/organizations/my-organization'),
  updateMyOrganization: (data) => api.put('/organizations/my-organization', data),
  getOrganization: (orgId) => api.get(`/organizations/${orgId}`),
  
  // Staff management
  listStaff: (params) => api.get('/organizations/staff', { params }),
  createStaff: (data) => api.post('/organizations/staff/create', data),
  inviteStaff: (data) => api.post('/organizations/staff/invite', data),
  acceptInvitation: (data) => api.post('/organizations/staff/accept-invitation', data),
  listInvitations: (params) => api.get('/organizations/staff/invitations', { params }),
  cancelInvitation: (invitationId) => api.delete(`/organizations/staff/invitations/${invitationId}`),
  deactivateStaff: (userId) => api.put(`/organizations/staff/${userId}/deactivate`),
  activateStaff: (userId) => api.put(`/organizations/staff/${userId}/activate`),
  updateStaffRole: (userId, newRole) => api.put(`/organizations/staff/${userId}/role`, null, { params: { new_role: newRole } }),
};

// Password Reset APIs
export const passwordAPI = {
  requestReset: (email) => api.post('/auth/password-reset/request', null, { params: { email } }),
  confirmReset: (token, newPassword) => api.post('/auth/password-reset/confirm', null, { params: { token, new_password: newPassword } }),
  changePassword: (currentPassword, newPassword) => api.post('/auth/change-password', null, { params: { current_password: currentPassword, new_password: newPassword } }),
};

// Pharmacy APIs
export const pharmacyAPI = {
  // Drug database
  getDrugs: (params) => api.get('/pharmacy/drugs', { params }),
  getDrugCategories: () => api.get('/pharmacy/drugs/categories'),
  getFrequencies: () => api.get('/pharmacy/frequencies'),
  
  // Pharmacy registration & auth
  register: (data) => api.post('/pharmacy/register', data),
  login: (data) => api.post('/pharmacy/login', data),
  
  // Pharmacy management (Super Admin)
  getPendingPharmacies: () => api.get('/pharmacy/pending'),
  approvePharmacy: (pharmacyId) => api.post(`/pharmacy/${pharmacyId}/approve`),
  
  // Public pharmacy search
  getAllPharmacies: (params) => api.get('/pharmacy/all', { params }),
  searchByMedication: (params) => api.get('/pharmacy/search/by-medication', { params }),
  
  // Inventory management
  addToInventory: (pharmacyId, data) => api.post('/pharmacy/inventory', data, { params: { pharmacy_id: pharmacyId } }),
  getInventory: (pharmacyId, search) => api.get(`/pharmacy/inventory/${pharmacyId}`, { params: { search } }),
  updateInventoryItem: (inventoryId, quantity, unitPrice) => api.put(`/pharmacy/inventory/${inventoryId}`, null, { params: { quantity, unit_price: unitPrice } }),
  deleteInventoryItem: (inventoryId) => api.delete(`/pharmacy/inventory/${inventoryId}`),
  
  // Prescriptions
  createPrescription: (data) => api.post('/pharmacy/prescriptions', data),
  getPatientPrescriptions: (patientId) => api.get(`/pharmacy/prescriptions/patient/${patientId}`),
  getPharmacyPrescriptions: (pharmacyId, status) => api.get(`/pharmacy/prescriptions/pharmacy/${pharmacyId}`, { params: { status } }),
  updatePrescriptionStatus: (prescriptionId, status) => api.put(`/pharmacy/prescriptions/${prescriptionId}/status`, null, { params: { status } }),
};

// Billing APIs
export const billingAPI = {
  // Service codes
  getServiceCodes: (category) => api.get('/billing/service-codes', { params: { category } }),
  
  // Invoices
  createInvoice: (data) => api.post('/billing/invoices', data),
  getInvoices: (params) => api.get('/billing/invoices', { params }),
  getInvoice: (invoiceId) => api.get(`/billing/invoices/${invoiceId}`),
  sendInvoice: (invoiceId) => api.put(`/billing/invoices/${invoiceId}/send`),
  cancelInvoice: (invoiceId) => api.delete(`/billing/invoices/${invoiceId}`),
  
  // Payments
  recordPayment: (data) => api.post('/billing/payments', data),
  getInvoicePayments: (invoiceId) => api.get(`/billing/payments/invoice/${invoiceId}`),
  
  // Paystack
  initializePaystack: (invoiceId, email) => api.post('/billing/paystack/initialize', null, { params: { invoice_id: invoiceId, email } }),
  verifyPaystack: (reference) => api.get(`/billing/paystack/verify/${reference}`),
  getPaystackConfig: () => api.get('/billing/paystack/config'),
  
  // Insurance Claims
  createClaim: (data) => api.post('/billing/claims', data),
  getClaims: (params) => api.get('/billing/claims', { params }),
  getClaim: (claimId) => api.get(`/billing/claims/${claimId}`),
  submitClaim: (claimId) => api.post(`/billing/claims/${claimId}/submit`),
  
  // Stats
  getStats: () => api.get('/billing/stats'),
};

// Reports APIs
export const reportsAPI = {
  // Report types
  getReportTypes: () => api.get('/reports/types/list'),
  
  // Generate reports
  generate: (data) => api.post('/reports/generate', data),
  generateAI: (data) => api.post('/reports/generate/ai', data),
  
  // CRUD
  getPatientReports: (patientId) => api.get(`/reports/patient/${patientId}`),
  getReport: (reportId) => api.get(`/reports/${reportId}`),
  updateReport: (reportId, content, title) => api.put(`/reports/${reportId}`, null, { params: { content, title } }),
  deleteReport: (reportId) => api.delete(`/reports/${reportId}`),
  
  // Export
  exportPDF: (reportId) => api.get(`/reports/${reportId}/pdf`),
};

// Imaging APIs
export const imagingAPI = {
  // Studies
  createStudy: (data) => api.post('/imaging/studies', data),
  getStudies: (params) => api.get('/imaging/studies', { params }),
  getStudy: (studyId) => api.get(`/imaging/studies/${studyId}`),
  getPatientStudies: (patientId) => api.get(`/imaging/studies/patient/${patientId}`),
  
  // Images
  uploadImage: (studyId, formData) => api.post(`/imaging/studies/${studyId}/upload`, formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  getStudyImages: (studyId) => api.get(`/imaging/studies/${studyId}/images`),
  getImageData: (imageId) => api.get(`/imaging/images/${imageId}/data`),
  
  // Interpretation
  addInterpretation: (studyId, data) => api.post(`/imaging/studies/${studyId}/interpret`, data),
  
  // Demo
  createSampleStudies: (patientId, patientName) => api.post('/imaging/demo/create-samples', null, { params: { patient_id: patientId, patient_name: patientName } }),
  
  // Modalities
  getModalities: () => api.get('/imaging/modalities'),
};

// Clinical Decision Support APIs
export const cdsAPI = {
  checkInteractions: (medications, newMedication) => api.post('/cds/check-interactions', { medications, new_medication: newMedication }),
  checkAllergy: (patientAllergies, medication) => api.post('/cds/check-allergy', { patient_allergies: patientAllergies, medication }),
  comprehensiveCheck: (patientId, newMedication) => api.post('/cds/comprehensive-check', null, { params: { patient_id: patientId, new_medication: newMedication } }),
  getDrugClasses: () => api.get('/cds/drug-classes'),
  getCommonAllergies: () => api.get('/cds/common-allergies'),
};

// Records Sharing / Health Information Exchange APIs
export const recordsSharingAPI = {
  // Physician search
  searchPhysicians: (params) => api.get('/records-sharing/physicians/search', { params }),
  getPhysicianProfile: (physicianId) => api.get(`/records-sharing/physicians/${physicianId}`),
  
  // Records requests
  createRequest: (data) => api.post('/records-sharing/requests', data),
  uploadConsentForm: (requestId, formData) => api.post(`/records-sharing/requests/${requestId}/consent-form`, formData, { headers: { 'Content-Type': 'multipart/form-data' } }),
  getIncomingRequests: (status) => api.get('/records-sharing/requests/incoming', { params: { status } }),
  getOutgoingRequests: (status) => api.get('/records-sharing/requests/outgoing', { params: { status } }),
  getRequestDetails: (requestId) => api.get(`/records-sharing/requests/${requestId}`),
  respondToRequest: (requestId, data) => api.post(`/records-sharing/requests/${requestId}/respond`, data),
  cancelRequest: (requestId) => api.post(`/records-sharing/requests/${requestId}/cancel`),
  
  // Shared records access
  getSharedRecords: (patientId) => api.get(`/records-sharing/shared-records/${patientId}`),
  getMyAccessGrants: () => api.get('/records-sharing/my-access-grants'),
  
  // Notifications
  getNotifications: (unreadOnly) => api.get('/records-sharing/notifications', { params: { unread_only: unreadOnly } }),
  markNotificationRead: (notificationId) => api.put(`/records-sharing/notifications/${notificationId}/read`),
  markAllNotificationsRead: () => api.put('/records-sharing/notifications/read-all'),
  
  // Statistics
  getStats: () => api.get('/records-sharing/stats'),
};

// RBAC (Role-Based Access Control) APIs
export const rbacAPI = {
  getMyPermissions: () => api.get('/rbac/permissions/my'),
  checkPermission: (permission) => api.get(`/rbac/permissions/check/${permission}`),
  checkBulkPermissions: (permissions) => api.post('/rbac/permissions/check-bulk', permissions),
  getAllRoles: () => api.get('/rbac/roles'),
  getRoleDetails: (role) => api.get(`/rbac/roles/${role}`),
  getAllPermissions: () => api.get('/rbac/permissions/all'),
  getPermissionMatrix: () => api.get('/rbac/matrix'),
};

// Two-Factor Authentication APIs
export const twoFactorAPI = {
  getStatus: () => api.get('/2fa/status'),
  setup: () => api.post('/2fa/setup'),
  verify: (code) => api.post('/2fa/verify', { code }),
  disable: (code) => api.post('/2fa/disable', { code }),
  validate: (code) => api.post('/2fa/validate', { code }),
  regenerateBackupCodes: (code) => api.post('/2fa/backup-codes/regenerate', { code }),
  useBackupCode: (backupCode) => api.post('/2fa/backup-codes/use', { backup_code: backupCode }),
  getBackupCodesCount: () => api.get('/2fa/backup-codes/count'),
};

// Enhanced Audit APIs
export const auditAPI = {
  getLogs: (params) => api.get('/audit/logs', { params }),
  getLogsCount: (params) => api.get('/audit/logs/count', { params }),
  getPatientLogs: (patientId, limit) => api.get(`/audit/logs/patient/${patientId}`, { params: { limit } }),
  getUserLogs: (userId, limit) => api.get(`/audit/logs/user/${userId}`, { params: { limit } }),
  getStats: (days) => api.get('/audit/stats', { params: { days } }),
  getSecurityStats: (days) => api.get('/audit/stats/security', { params: { days } }),
  exportLogs: (params) => api.get('/audit/export', { params }),
  getAlerts: (hours) => api.get('/audit/alerts', { params: { hours } }),
  getActions: () => api.get('/audit/actions'),
  getResourceTypes: () => api.get('/audit/resource-types'),
};

// Nurse Portal APIs
export const nurseAPI = {
  // Dashboard
  getDashboardStats: () => api.get('/nurse/dashboard/stats'),
  
  // Shifts
  getShifts: () => api.get('/nurse/shifts'),
  getCurrentShift: () => api.get('/nurse/current-shift'),
  clockIn: (data) => api.post('/nurse/shifts/clock-in', data),
  clockOut: (handoffNotes) => api.post('/nurse/shifts/clock-out', null, { params: { handoff_notes: handoffNotes } }),
  getHandoffNotes: (departmentId) => api.get('/nurse/shifts/handoff-notes', { params: { department_id: departmentId } }),
  
  // Patient Assignments
  getMyPatients: (params) => api.get('/nurse/my-patients', { params }),
  assignPatient: (data) => api.post('/nurse/assign-patient', data),
  unassignPatient: (patientId, nurseId) => api.delete(`/nurse/unassign-patient/${patientId}`, { params: { nurse_id: nurseId } }),
  getPatientLoad: (departmentId) => api.get('/nurse/patient-load', { params: { department_id: departmentId } }),
  
  // Tasks
  getTasks: (params) => api.get('/nurse/tasks', { params }),
  getDueTasks: () => api.get('/nurse/tasks/due'),
  createTask: (data) => api.post('/nurse/tasks', data),
  completeTask: (taskId, notes) => api.post(`/nurse/tasks/${taskId}/complete`, null, { params: { completion_notes: notes } }),
  deferTask: (taskId, newDueTime, reason) => api.post(`/nurse/tasks/${taskId}/defer`, null, { params: { new_due_time: newDueTime, reason } }),
  getTaskTypes: () => api.get('/nurse/task-types'),
  getTaskPriorities: () => api.get('/nurse/task-priorities'),
  
  // Medication Administration Record (MAR)
  getMAR: (patientId, date) => api.get(`/nurse/mar/${patientId}`, { params: { date } }),
  administerMedication: (data) => api.post('/nurse/mar/administer', data),
  getMedicationsDue: (windowMinutes) => api.get('/nurse/mar/due', { params: { window_minutes: windowMinutes } }),
  generateMARSchedule: (patientId, date) => api.post('/nurse/mar/generate-schedule', null, { params: { patient_id: patientId, date } }),
  
  // Quick Actions
  quickRecordVitals: (data) => api.post('/nurse/quick-vitals', null, { params: data }),
  
  // Permissions
  getPermissions: () => api.get('/nurse/permissions'),
  checkPermission: (permission) => api.get(`/nurse/permissions/check/${permission}`),
  
  // Shift Reports
  createReport: (data) => api.post('/nurse/reports', data),
  getMyReports: (params) => api.get('/nurse/reports', { params }),
  getReport: (reportId) => api.get(`/nurse/reports/${reportId}`),
  updateReport: (reportId, data) => api.put(`/nurse/reports/${reportId}`, null, { params: data }),
  submitReport: (reportId) => api.post(`/nurse/reports/${reportId}/submit`),
  
  // Patient Medications
  getPatientMedications: (patientId) => api.get(`/nurse/patient-medications/${patientId}`),
  getAllAssignedMedications: () => api.get('/nurse/all-assigned-medications'),
};

// Nursing Supervisor APIs
export const nursingSupervisorAPI = {
  // Dashboard
  getDashboard: () => api.get('/nursing-supervisor/dashboard'),
  
  // Nurses
  listNurses: (params) => api.get('/nursing-supervisor/nurses', { params }),
  getNurseWorkload: (nurseId) => api.get(`/nursing-supervisor/nurses/${nurseId}/workload`),
  
  // Patient Assignments
  assignPatient: (data) => api.post('/nursing-supervisor/assign-patient', data),
  unassignPatient: (assignmentId) => api.delete(`/nursing-supervisor/unassign-patient/${assignmentId}`),
  getUnassignedPatients: () => api.get('/nursing-supervisor/unassigned-patients'),
  
  // Task Assignments
  assignTask: (data) => api.post('/nursing-supervisor/assign-task', data),
  
  // Reports (Read-Only)
  listReports: (params) => api.get('/nursing-supervisor/reports', { params }),
  getReport: (reportId) => api.get(`/nursing-supervisor/reports/${reportId}`),
  reviewReport: (reportId, reviewNotes) => api.post(`/nursing-supervisor/reports/${reportId}/review`, { review_notes: reviewNotes }),
  
  // Shifts
  getCurrentShifts: () => api.get('/nursing-supervisor/shifts/current'),
  getShiftHistory: (params) => api.get('/nursing-supervisor/shifts/history', { params }),
  
  // Force Clock-Out
  forceClockOut: (nurseId, reason) => api.post(`/nursing-supervisor/force-clock-out/${nurseId}`, null, { params: { reason } }),
  
  // Handoff Notes
  getHandoffNotes: (params) => api.get('/nursing-supervisor/handoff-notes', { params }),
};

// Admin Portal APIs
export const adminAPI = {
  // Dashboard
  getDashboardStats: () => api.get('/admin/dashboard/stats'),
  
  // Permission Groups
  getPermissionGroups: () => api.get('/admin/permission-groups'),
  createPermissionGroup: (data) => api.post('/admin/permission-groups', data),
  updatePermissionGroup: (groupId, data) => api.put(`/admin/permission-groups/${groupId}`, data),
  deletePermissionGroup: (groupId) => api.delete(`/admin/permission-groups/${groupId}`),
  getAvailablePermissions: () => api.get('/admin/available-permissions'),
  
  // User Management
  getUsers: (params) => api.get('/admin/users', { params }),
  updateUserRole: (userId, data) => api.put(`/admin/users/${userId}/role`, data),
  bulkUserAction: (data) => api.post('/admin/users/bulk-action', data),
  getUserActivity: (userId, days) => api.get(`/admin/users/${userId}/activity`, { params: { days } }),
  
  // Sharing Policies
  getSharingPolicies: (params) => api.get('/admin/sharing-policies', { params }),
  approveSharingPolicy: (policyId, data) => api.post(`/admin/sharing-policies/${policyId}/approve`, data),
  denySharingPolicy: (policyId, reason) => api.post(`/admin/sharing-policies/${policyId}/deny`, null, { params: { reason } }),
  requestSharingPolicy: (params) => api.post('/admin/sharing-policies/request', null, { params }),
  
  // Security Policies (Super Admin)
  getSecurityPolicies: (policyType) => api.get('/admin/security-policies', { params: { policy_type: policyType } }),
  createSecurityPolicy: (data) => api.post('/admin/security-policies', data),
  toggleSecurityPolicy: (policyType, isActive) => api.put(`/admin/security-policies/${policyType}/toggle`, null, { params: { is_active: isActive } }),
  
  // System-Wide (Super Admin)
  getSystemAuditLogs: (params) => api.get('/admin/system/audit-logs', { params }),
  getSecurityAlerts: (hours) => api.get('/admin/system/security-alerts', { params: { hours } }),
  getSystemHealth: () => api.get('/admin/system/health'),
  getPlatformStats: () => api.get('/admin/system/stats'),
};

// Region & Hospital Discovery APIs (Ghana)
export const regionAPI = {
  // Public Discovery (no auth required)
  getRegions: () => api.get('/regions/'),
  getRegion: (regionId) => api.get(`/regions/${regionId}`),
  getHospitalsByRegion: (regionId, search, city) => api.get(`/regions/${regionId}/hospitals`, { 
    params: { search, city } 
  }),
  getHospitalDetails: (hospitalId) => api.get(`/regions/hospitals/${hospitalId}`),
  getHospitalLocations: (hospitalId) => api.get(`/regions/hospitals/${hospitalId}/locations`),
  
  // Location-Aware Authentication
  locationLogin: (email, password, hospitalId, locationId, totpCode) => api.post('/regions/auth/login', {
    email,
    password,
    hospital_id: hospitalId,
    location_id: locationId,
    totp_code: totpCode
  }),
  getRedirectUrl: () => api.get('/regions/auth/redirect-url'),
  
  // Super Admin - Region Management
  createRegion: (data) => api.post('/regions/admin/regions', data),
  updateRegion: (regionId, data) => api.put(`/regions/admin/regions/${regionId}`, data),
  deleteRegion: (regionId) => api.delete(`/regions/admin/regions/${regionId}`),
  
  // Super Admin - Hospital Management
  createHospital: (data) => api.post('/regions/admin/hospitals', data),
  assignHospitalToRegion: (hospitalId, regionId) => api.put(`/regions/admin/hospitals/${hospitalId}/region`, null, { 
    params: { region_id: regionId } 
  }),
  getAllHospitals: (regionId, status) => api.get('/regions/admin/hospitals/all', { 
    params: { region_id: regionId, status } 
  }),
  getPlatformOverview: () => api.get('/regions/admin/overview'),
  
  // Super Admin - Hospital Access (Login As)
  loginAsHospital: (hospitalId) => api.post(`/regions/admin/login-as-hospital/${hospitalId}`),
  getHospitalAdmins: (regionId) => api.get('/regions/admin/hospital-admins', { params: { region_id: regionId } }),
  
  // Super Admin - Create Staff for any Hospital
  createHospitalStaff: (hospitalId, data) => api.post(`/regions/admin/hospitals/${hospitalId}/staff`, data),
  
  // Super Admin - Get Hospital Departments
  getHospitalDepartments: (hospitalId) => api.get(`/hospital/${hospitalId}/admin/departments`),
  
  // Super Admin - Seed Departments for Existing Hospital
  seedHospitalDepartments: (hospitalId) => api.post(`/regions/admin/hospitals/${hospitalId}/seed-departments`),
  
  // Super Admin - Hospital Management (Delete/Status Change)
  deleteHospital: (hospitalId) => api.delete(`/regions/admin/hospitals/${hospitalId}`),
  updateHospitalStatus: (hospitalId, data) => api.put(`/regions/admin/hospitals/${hospitalId}/status`, data),
  
  // Hospital Admin - Location Management
  addLocation: (hospitalId, data) => api.post(`/regions/hospitals/${hospitalId}/locations`, data),
  updateLocation: (hospitalId, locationId, data) => api.put(`/regions/hospitals/${hospitalId}/locations/${locationId}`, data),
  deactivateLocation: (hospitalId, locationId) => api.delete(`/regions/hospitals/${hospitalId}/locations/${locationId}`),
  
  // Hospital Admin - Staff Management
  createStaffWithLocation: (hospitalId, data) => api.post(`/regions/hospitals/${hospitalId}/staff`, data),
  assignStaffToLocation: (userId, locationId) => api.put(`/regions/staff/${userId}/location`, null, { 
    params: { location_id: locationId } 
  }),
};

// Hospital Admin APIs
export const hospitalAdminAPI = {
  // Dashboard
  getDashboard: (hospitalId) => api.get(`/hospital/${hospitalId}/admin/dashboard`),
  
  // User Management
  listUsers: (hospitalId, params) => api.get(`/hospital/${hospitalId}/admin/users`, { params }),
  createUser: (hospitalId, data) => api.post(`/hospital/${hospitalId}/admin/users`, data),
  getUser: (hospitalId, userId) => api.get(`/hospital/${hospitalId}/admin/users/${userId}`),
  updateUser: (hospitalId, userId, data) => api.put(`/hospital/${hospitalId}/admin/users/${userId}`, data),
  deactivateUser: (hospitalId, userId) => api.delete(`/hospital/${hospitalId}/admin/users/${userId}`),
  reactivateUser: (hospitalId, userId) => api.post(`/hospital/${hospitalId}/admin/users/${userId}/reactivate`),
  resetPassword: (hospitalId, userId) => api.post(`/hospital/${hospitalId}/admin/users/${userId}/reset-password`),
  configureMFA: (hospitalId, userId, requireMfa) => api.post(`/hospital/${hospitalId}/admin/users/${userId}/mfa`, { require_mfa: requireMfa }),
  
  // Department Management
  listDepartments: (hospitalId) => api.get(`/hospital/${hospitalId}/admin/departments`),
  createDepartment: (hospitalId, data) => api.post(`/hospital/${hospitalId}/admin/departments`, data),
  updateDepartment: (hospitalId, deptId, data) => api.put(`/hospital/${hospitalId}/admin/departments/${deptId}`, data),
  deactivateDepartment: (hospitalId, deptId) => api.delete(`/hospital/${hospitalId}/admin/departments/${deptId}`),
  
  // Unit Management
  listUnits: (hospitalId, deptId) => api.get(`/hospital/${hospitalId}/admin/units`, { params: { department_id: deptId } }),
  createUnit: (hospitalId, data) => api.post(`/hospital/${hospitalId}/admin/units`, data),
  
  // Audit Logs
  getAuditLogs: (hospitalId, params) => api.get(`/hospital/${hospitalId}/admin/audit-logs`, { params }),
  
  // Settings
  getSettings: (hospitalId) => api.get(`/hospital/${hospitalId}/admin/settings`),
  updateSettings: (hospitalId, data) => api.put(`/hospital/${hospitalId}/admin/settings`, data),
};

// Hospital Dashboard APIs
export const hospitalDashboardAPI = {
  getDashboard: (hospitalId, locationId) => api.get(`/hospital/${hospitalId}/dashboard`, { params: { location_id: locationId } }),
  getLocations: (hospitalId) => api.get(`/hospital/${hospitalId}/locations`),
  
  // Role-Specific Portals
  getPhysicianPortal: (hospitalId) => api.get(`/hospital/${hospitalId}/physician`),
  getNursePortal: (hospitalId) => api.get(`/hospital/${hospitalId}/nurse`),
  getSchedulerPortal: (hospitalId) => api.get(`/hospital/${hospitalId}/scheduler`),
  getBillingPortal: (hospitalId) => api.get(`/hospital/${hospitalId}/billing`),
  getDepartmentPortal: (hospitalId, deptId) => api.get(`/hospital/${hospitalId}/department/${deptId}`),
};

// Signup APIs
export const signupAPI = {
  // Public
  registerHospital: (data) => api.post('/signup/hospital', data),
  verifyEmail: (token) => api.post('/signup/verify-email', { token }),
  checkStatus: (registrationId) => api.get(`/signup/status/${registrationId}`),
  registerProvider: (data) => api.post('/signup/provider', data),
  resendVerification: (email) => api.post('/signup/resend-verification', null, { params: { email } }),
  
  // Admin
  listPendingRegistrations: (status) => api.get('/signup/admin/pending', { params: { status } }),
  approveRegistration: (registrationId, decision) => api.post(`/signup/admin/approve/${registrationId}`, decision),
  createProviderInvite: (hospitalId, email, role, departmentId) => api.post('/signup/admin/invite-provider', null, {
    params: { hospital_id: hospitalId, email, role, department_id: departmentId }
  }),
};

// Hospital IT Admin APIs (Super Admin IT)
export const hospitalITAdminAPI = {
  // Dashboard
  getDashboard: (hospitalId) => api.get(`/hospital/${hospitalId}/super-admin/dashboard`),
  
  // Staff Management
  listStaff: (hospitalId, params) => api.get(`/hospital/${hospitalId}/super-admin/staff`, { params }),
  createStaff: (hospitalId, data) => api.post(`/hospital/${hospitalId}/super-admin/staff`, data),
  bulkCreateStaff: (hospitalId, staffList) => api.post(`/hospital/${hospitalId}/super-admin/staff/bulk`, { staff_list: staffList }),
  getStaff: (hospitalId, staffId) => api.get(`/hospital/${hospitalId}/super-admin/staff/${staffId}`),
  updateStaff: (hospitalId, staffId, data) => api.put(`/hospital/${hospitalId}/super-admin/staff/${staffId}`, data),
  deleteStaff: (hospitalId, staffId) => api.delete(`/hospital/${hospitalId}/super-admin/staff/${staffId}`),
  
  // Account Status
  activateStaff: (hospitalId, staffId) => api.post(`/hospital/${hospitalId}/super-admin/staff/${staffId}/activate`),
  deactivateStaff: (hospitalId, staffId, reason) => api.post(`/hospital/${hospitalId}/super-admin/staff/${staffId}/deactivate`, null, { params: { reason } }),
  suspendStaff: (hospitalId, staffId, reason) => api.post(`/hospital/${hospitalId}/super-admin/staff/${staffId}/suspend`, null, { params: { reason } }),
  
  // Credentials
  resetPassword: (hospitalId, staffId) => api.post(`/hospital/${hospitalId}/super-admin/staff/${staffId}/reset-password`),
  unlockAccount: (hospitalId, staffId) => api.post(`/hospital/${hospitalId}/super-admin/staff/${staffId}/unlock`),
  
  // Assignments
  changeRole: (hospitalId, staffId, newRole) => api.put(`/hospital/${hospitalId}/super-admin/staff/${staffId}/role`, null, { params: { new_role: newRole } }),
  assignDepartment: (hospitalId, staffId, departmentId) => api.put(`/hospital/${hospitalId}/super-admin/staff/${staffId}/department`, null, { params: { department_id: departmentId } }),
  assignLocation: (hospitalId, staffId, locationId) => api.put(`/hospital/${hospitalId}/super-admin/staff/${staffId}/location`, null, { params: { location_id: locationId } }),
  
  // Activity Log
  getActivityLog: (hospitalId, params) => api.get(`/hospital/${hospitalId}/super-admin/activity-log`, { params }),
  
  // Department Management
  listDepartments: (hospitalId) => api.get(`/hospital/${hospitalId}/super-admin/departments`),
  seedDepartments: (hospitalId) => api.post(`/hospital/${hospitalId}/super-admin/departments/seed`),
  createDepartment: (hospitalId, code, name, description) => api.post(`/hospital/${hospitalId}/super-admin/departments`, null, { params: { code, name, description } }),
};

// Department Portal API
export const departmentAPI = {
  // Get all departments
  getAll: (params) => api.get('/departments', { params }),
  
  // Get department by ID
  getById: (departmentId) => api.get(`/departments/${departmentId}`),
  
  // Get department types
  getTypes: () => api.get('/departments/types'),
  
  // Get department hierarchy
  getHierarchy: () => api.get('/departments/hierarchy'),
  
  // Get department stats
  getStats: () => api.get('/departments/stats'),
  
  // Create department (admin only)
  create: (data) => api.post('/departments', data),
  
  // Update department (admin only)
  update: (departmentId, data) => api.put(`/departments/${departmentId}`, data),
  
  // Delete department (admin only)
  delete: (departmentId) => api.delete(`/departments/${departmentId}`),
  
  // Get department staff
  getStaff: (departmentId) => api.get(`/departments/${departmentId}/staff`),
  
  // Assign staff to department
  assignStaff: (departmentId, staffId) => api.post(`/departments/${departmentId}/assign-staff`, { staff_id: staffId }),
  
  // Get department patients
  getPatients: (departmentId, params) => api.get(`/departments/${departmentId}/patients`, { params }),
};

export default api;
