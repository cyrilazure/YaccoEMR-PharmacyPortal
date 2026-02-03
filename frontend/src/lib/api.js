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

export default api;
