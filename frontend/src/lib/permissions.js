/**
 * RBAC (Role-Based Access Control) Configuration
 * Defines what each role CAN DO and CANNOT DO
 * This is the single source of truth for permissions
 */

// All available permissions in the system
export const PERMISSIONS = {
  // Platform Level
  MANAGE_HOSPITALS: 'manage_hospitals',
  CREATE_HOSPITALS: 'create_hospitals',
  DELETE_HOSPITALS: 'delete_hospitals',
  CREATE_HOSPITAL_IT_ADMIN: 'create_hospital_it_admin',
  VIEW_ALL_HOSPITALS: 'view_all_hospitals',
  
  // Hospital Level - Staff Management
  CREATE_STAFF: 'create_staff',
  MANAGE_STAFF: 'manage_staff',
  DEACTIVATE_STAFF: 'deactivate_staff',
  RESET_PASSWORDS: 'reset_passwords',
  
  // Hospital Level - Administration
  MANAGE_DEPARTMENTS: 'manage_departments',
  MANAGE_UNITS: 'manage_units',
  MANAGE_LOCATIONS: 'manage_locations',
  MANAGE_HOSPITAL_SETTINGS: 'manage_hospital_settings',
  ASSIGN_STAFF_TO_DEPARTMENTS: 'assign_staff_to_departments',
  
  // Patient Management
  VIEW_PATIENTS: 'view_patients',
  ADD_PATIENTS: 'add_patients',
  EDIT_PATIENTS: 'edit_patients',
  GENERATE_MRN: 'generate_mrn',
  VIEW_PATIENT_RECORDS: 'view_patient_records',
  
  // Clinical
  CREATE_CLINICAL_NOTES: 'create_clinical_notes',
  CREATE_ORDERS: 'create_orders',
  VIEW_ASSIGNED_PATIENTS: 'view_assigned_patients',
  REQUEST_EXTERNAL_RECORDS: 'request_external_records',
  VIEW_SHARED_RECORDS: 'view_shared_records',
  
  // Scheduling
  MANAGE_APPOINTMENTS: 'manage_appointments',
  VIEW_PROVIDER_AVAILABILITY: 'view_provider_availability',
  ASSIGN_PATIENTS_TO_DEPARTMENTS: 'assign_patients_to_departments',
  
  // Billing
  VIEW_BILLING: 'view_billing',
  CREATE_INVOICES: 'create_invoices',
  MANAGE_INSURANCE_CLAIMS: 'manage_insurance_claims',
  NHIS_LOOKUP: 'nhis_lookup',
  
  // Analytics & Audit
  VIEW_ANALYTICS: 'view_analytics',
  VIEW_AUDIT_LOGS: 'view_audit_logs',
  
  // Telehealth
  USE_TELEHEALTH: 'use_telehealth',
  
  // Notifications
  VIEW_NOTIFICATIONS: 'view_notifications',
};

// Role definitions with their permissions
export const ROLE_PERMISSIONS = {
  // ========== PLATFORM LEVEL ==========
  super_admin: {
    name: 'Product Owner / Super Admin',
    level: 'platform',
    canDo: [
      PERMISSIONS.MANAGE_HOSPITALS,
      PERMISSIONS.CREATE_HOSPITALS,
      PERMISSIONS.DELETE_HOSPITALS,
      PERMISSIONS.CREATE_HOSPITAL_IT_ADMIN,
      PERMISSIONS.VIEW_ALL_HOSPITALS,
      PERMISSIONS.CREATE_STAFF, // Can create any staff for any hospital
    ],
    cannotDo: [
      PERMISSIONS.VIEW_PATIENTS,
      PERMISSIONS.VIEW_PATIENT_RECORDS,
      PERMISSIONS.VIEW_BILLING,
      PERMISSIONS.MANAGE_APPOINTMENTS,
      PERMISSIONS.VIEW_AUDIT_LOGS,
      PERMISSIONS.VIEW_ANALYTICS,
      PERMISSIONS.CREATE_CLINICAL_NOTES,
      PERMISSIONS.CREATE_ORDERS,
    ],
    defaultRoute: '/platform/super-admin',
    allowedRoutes: ['/platform/super-admin', '/platform-admin', '/po-portal'],
  },

  // ========== HOSPITAL LEVEL ==========
  hospital_admin: {
    name: 'Hospital Administrator',
    level: 'hospital',
    canDo: [
      PERMISSIONS.MANAGE_DEPARTMENTS,
      PERMISSIONS.MANAGE_UNITS,
      PERMISSIONS.MANAGE_LOCATIONS,
      PERMISSIONS.MANAGE_HOSPITAL_SETTINGS,
      PERMISSIONS.ASSIGN_STAFF_TO_DEPARTMENTS,
      PERMISSIONS.VIEW_PATIENTS,
      PERMISSIONS.ADD_PATIENTS,
      PERMISSIONS.GENERATE_MRN,
      PERMISSIONS.VIEW_PATIENT_RECORDS,
      PERMISSIONS.VIEW_NOTIFICATIONS,
    ],
    cannotDo: [
      PERMISSIONS.CREATE_STAFF,
      PERMISSIONS.MANAGE_STAFF,
      PERMISSIONS.VIEW_AUDIT_LOGS,
      PERMISSIONS.VIEW_ANALYTICS,
      PERMISSIONS.MANAGE_HOSPITALS,
      PERMISSIONS.DELETE_HOSPITALS,
    ],
    defaultRoute: '/admin-dashboard',
    allowedRoutes: ['/admin-dashboard', '/hospital-settings', '/patients', '/department'],
  },

  hospital_it_admin: {
    name: 'Hospital IT Administrator',
    level: 'hospital',
    canDo: [
      PERMISSIONS.CREATE_STAFF,
      PERMISSIONS.MANAGE_STAFF,
      PERMISSIONS.DEACTIVATE_STAFF,
      PERMISSIONS.RESET_PASSWORDS,
      PERMISSIONS.ASSIGN_STAFF_TO_DEPARTMENTS,
    ],
    cannotDo: [
      PERMISSIONS.VIEW_PATIENTS,
      PERMISSIONS.ADD_PATIENTS,
      PERMISSIONS.VIEW_PATIENT_RECORDS,
      PERMISSIONS.CREATE_CLINICAL_NOTES,
      PERMISSIONS.MANAGE_APPOINTMENTS,
      PERMISSIONS.VIEW_BILLING,
      PERMISSIONS.VIEW_AUDIT_LOGS,
      PERMISSIONS.VIEW_ANALYTICS,
      PERMISSIONS.MANAGE_HOSPITALS,
    ],
    defaultRoute: '/it-admin',
    allowedRoutes: ['/it-admin'],
  },

  // ========== FACILITY LEVEL ==========
  facility_admin: {
    name: 'Facility Administrator',
    level: 'facility',
    canDo: [
      PERMISSIONS.ASSIGN_STAFF_TO_DEPARTMENTS,
      PERMISSIONS.VIEW_NOTIFICATIONS,
    ],
    cannotDo: [
      PERMISSIONS.CREATE_STAFF,
      PERMISSIONS.VIEW_PATIENTS,
      PERMISSIONS.VIEW_PATIENT_RECORDS,
      PERMISSIONS.MANAGE_HOSPITAL_SETTINGS,
      PERMISSIONS.VIEW_AUDIT_LOGS,
      PERMISSIONS.VIEW_ANALYTICS,
    ],
    defaultRoute: '/facility-admin',
    allowedRoutes: ['/facility-admin'],
  },

  // ========== CLINICAL LEVEL ==========
  physician: {
    name: 'Physician',
    level: 'clinical',
    canDo: [
      PERMISSIONS.VIEW_ASSIGNED_PATIENTS,
      PERMISSIONS.VIEW_PATIENTS,
      PERMISSIONS.ADD_PATIENTS,
      PERMISSIONS.GENERATE_MRN,
      PERMISSIONS.VIEW_PATIENT_RECORDS,
      PERMISSIONS.CREATE_CLINICAL_NOTES,
      PERMISSIONS.CREATE_ORDERS,
      PERMISSIONS.REQUEST_EXTERNAL_RECORDS,
      PERMISSIONS.VIEW_SHARED_RECORDS,
      PERMISSIONS.VIEW_ANALYTICS,
      PERMISSIONS.USE_TELEHEALTH,
      PERMISSIONS.VIEW_NOTIFICATIONS,
    ],
    cannotDo: [
      PERMISSIONS.CREATE_STAFF,
      PERMISSIONS.MANAGE_STAFF,
      PERMISSIONS.VIEW_BILLING,
      PERMISSIONS.MANAGE_HOSPITALS,
      PERMISSIONS.MANAGE_HOSPITAL_SETTINGS,
    ],
    defaultRoute: '/dashboard',
    allowedRoutes: ['/dashboard', '/patients', '/appointments', '/orders', '/telehealth', '/analytics', '/records-sharing'],
  },

  nurse: {
    name: 'Nurse',
    level: 'clinical',
    canDo: [
      PERMISSIONS.VIEW_ASSIGNED_PATIENTS,
      PERMISSIONS.VIEW_PATIENTS,
      PERMISSIONS.VIEW_PATIENT_RECORDS,
      PERMISSIONS.MANAGE_APPOINTMENTS,
      PERMISSIONS.VIEW_NOTIFICATIONS,
    ],
    cannotDo: [
      PERMISSIONS.CREATE_STAFF,
      PERMISSIONS.REQUEST_EXTERNAL_RECORDS,
      PERMISSIONS.VIEW_BILLING,
      PERMISSIONS.VIEW_ANALYTICS,
      PERMISSIONS.MANAGE_HOSPITALS,
    ],
    defaultRoute: '/nurse-station',
    allowedRoutes: ['/nurse-station', '/patients', '/appointments', '/scheduling'],
  },

  // ========== OPERATIONAL LEVEL ==========
  scheduler: {
    name: 'Scheduler',
    level: 'operational',
    canDo: [
      PERMISSIONS.VIEW_PATIENTS,
      PERMISSIONS.MANAGE_APPOINTMENTS,
      PERMISSIONS.VIEW_PROVIDER_AVAILABILITY,
      PERMISSIONS.ASSIGN_PATIENTS_TO_DEPARTMENTS,
    ],
    cannotDo: [
      PERMISSIONS.CREATE_STAFF,
      PERMISSIONS.VIEW_PATIENT_RECORDS,
      PERMISSIONS.CREATE_CLINICAL_NOTES,
      PERMISSIONS.VIEW_BILLING,
      PERMISSIONS.VIEW_ANALYTICS,
    ],
    defaultRoute: '/scheduling',
    allowedRoutes: ['/scheduling', '/patients', '/appointments'],
  },

  biller: {
    name: 'Billing Staff',
    level: 'operational',
    canDo: [
      PERMISSIONS.VIEW_PATIENTS,
      PERMISSIONS.ADD_PATIENTS,
      PERMISSIONS.VIEW_BILLING,
      PERMISSIONS.CREATE_INVOICES,
      PERMISSIONS.MANAGE_INSURANCE_CLAIMS,
      PERMISSIONS.NHIS_LOOKUP,
    ],
    cannotDo: [
      PERMISSIONS.CREATE_STAFF,
      PERMISSIONS.VIEW_PATIENT_RECORDS,
      PERMISSIONS.CREATE_CLINICAL_NOTES,
      PERMISSIONS.CREATE_ORDERS,
      PERMISSIONS.VIEW_ANALYTICS,
    ],
    defaultRoute: '/billing',
    allowedRoutes: ['/billing', '/patients'],
  },

  records_officer: {
    name: 'Records Officer',
    level: 'operational',
    canDo: [
      PERMISSIONS.VIEW_PATIENTS,
      PERMISSIONS.ADD_PATIENTS,
      PERMISSIONS.GENERATE_MRN,
    ],
    cannotDo: [
      PERMISSIONS.CREATE_STAFF,
      PERMISSIONS.VIEW_PATIENT_RECORDS,
      PERMISSIONS.CREATE_CLINICAL_NOTES,
      PERMISSIONS.VIEW_BILLING,
      PERMISSIONS.VIEW_ANALYTICS,
    ],
    defaultRoute: '/department',
    allowedRoutes: ['/department', '/patients'],
  },

  department_staff: {
    name: 'Department Staff',
    level: 'operational',
    canDo: [
      PERMISSIONS.VIEW_PATIENTS,
      PERMISSIONS.ADD_PATIENTS,
    ],
    cannotDo: [
      PERMISSIONS.CREATE_STAFF,
      PERMISSIONS.VIEW_PATIENT_RECORDS,
      PERMISSIONS.CREATE_CLINICAL_NOTES,
      PERMISSIONS.VIEW_BILLING,
      PERMISSIONS.VIEW_ANALYTICS,
    ],
    defaultRoute: '/department',
    allowedRoutes: ['/department', '/patients'],
  },
};

/**
 * Check if a role has a specific permission
 */
export const hasPermission = (role, permission) => {
  const roleConfig = ROLE_PERMISSIONS[role];
  if (!roleConfig) return false;
  return roleConfig.canDo.includes(permission);
};

/**
 * Check if a permission is explicitly denied for a role
 */
export const isDenied = (role, permission) => {
  const roleConfig = ROLE_PERMISSIONS[role];
  if (!roleConfig) return true;
  return roleConfig.cannotDo.includes(permission);
};

/**
 * Get default route for a role
 */
export const getDefaultRoute = (role) => {
  const roleConfig = ROLE_PERMISSIONS[role];
  return roleConfig?.defaultRoute || '/dashboard';
};

/**
 * Check if a route is allowed for a role
 */
export const isRouteAllowed = (role, route) => {
  const roleConfig = ROLE_PERMISSIONS[role];
  if (!roleConfig) return false;
  
  // Check if exact match or starts with allowed route
  return roleConfig.allowedRoutes.some(
    allowed => route === allowed || route.startsWith(allowed + '/')
  );
};

/**
 * Get role display name
 */
export const getRoleName = (role) => {
  return ROLE_PERMISSIONS[role]?.name || role;
};

/**
 * Get all permissions for a role
 */
export const getRolePermissions = (role) => {
  return ROLE_PERMISSIONS[role] || null;
};

export default {
  PERMISSIONS,
  ROLE_PERMISSIONS,
  hasPermission,
  isDenied,
  getDefaultRoute,
  isRouteAllowed,
  getRoleName,
  getRolePermissions,
};
