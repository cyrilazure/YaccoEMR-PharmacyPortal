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

// Auth APIs
export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (userData) => api.post('/auth/register', userData),
  getMe: () => api.get('/auth/me'),
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

export default api;
