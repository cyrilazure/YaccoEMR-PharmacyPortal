import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/lib/auth";
import { Toaster } from "@/components/ui/sonner";

// Pages
import LoginPage from "@/pages/Login";
import RegionHospitalLogin from "@/pages/RegionHospitalLogin";
import EMRLandingPage from "@/pages/EMRLandingPage";
import PlatformOwnerPortal from "@/pages/PlatformOwnerPortal";
import ForgotPassword from "@/pages/ForgotPassword";
import ResetPassword from "@/pages/ResetPassword";
import Layout from "@/pages/Layout";
import Dashboard from "@/pages/Dashboard";
import Patients from "@/pages/Patients";
import PatientChart from "@/pages/PatientChart";
import Appointments from "@/pages/Appointments";
import Orders from "@/pages/Orders";
import Analytics from "@/pages/Analytics";
import NurseDashboard from "@/pages/NurseDashboard";
import SchedulerDashboard from "@/pages/SchedulerDashboard";
import AdminDashboard from "@/pages/AdminDashboard";
import TelehealthPage from "@/pages/TelehealthPage";
import SuperAdminDashboard from "@/pages/SuperAdminDashboard";
import SuperAdminLogin from "@/pages/SuperAdminLogin";
import POLogin from "@/pages/POLogin";
import HospitalSettings from "@/pages/HospitalSettings";
import HospitalRegistration from "@/pages/HospitalRegistration";
import BillingPage from "@/pages/BillingPage";
import RecordsSharing from "@/pages/RecordsSharing";
import SecuritySettings from "@/pages/SecuritySettings";
import AuditLogs from "@/pages/AuditLogs";

// New Pages
import SignupPage from "@/pages/SignupPage";
import HospitalAdminPortal from "@/pages/HospitalAdminPortal";
import HospitalMainDashboard from "@/pages/HospitalMainDashboard";
import HospitalSuperAdminIT from "@/pages/HospitalSuperAdminIT";
import DepartmentUnitPortal from "@/pages/DepartmentUnitPortal";

// Role-based redirect component
function RoleBasedRedirect() {
  const { user } = useAuth();
  
  if (!user) return <Navigate to="/login" replace />;
  
  switch (user.role) {
    case 'super_admin':
      return <Navigate to="/platform-admin" replace />;
    case 'hospital_admin':
      return <Navigate to="/admin-dashboard" replace />;
    case 'hospital_it_admin':
      return <Navigate to="/it-admin" replace />;
    case 'physician':
      return <Navigate to="/dashboard" replace />;
    case 'nurse':
      return <Navigate to="/nurse-station" replace />;
    case 'scheduler':
      return <Navigate to="/scheduling" replace />;
    case 'admin':
      return <Navigate to="/admin" replace />;
    case 'biller':
      return <Navigate to="/billing" replace />;
    default:
      return <Navigate to="/dashboard" replace />;
  }
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* ========== PUBLIC ROUTES ========== */}
          
          {/* Landing Page - Main Entry Point */}
          <Route path="/" element={<EMRLandingPage />} />
          
          {/* Ghana Region-Based Login */}
          <Route path="/login" element={<RegionHospitalLogin />} />
          
          {/* Platform Owner (Super Admin) Login */}
          <Route path="/po-login" element={<POLogin />} />
          <Route path="/admin-login" element={<POLogin />} />
          <Route path="/platform/admin" element={<POLogin />} />
          
          {/* Public Signup */}
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/signup/provider" element={<SignupPage />} />
          
          {/* Legacy/Direct Login (for backward compatibility) */}
          <Route path="/direct-login" element={<LoginPage />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/register-hospital" element={<HospitalRegistration />} />
          
          {/* Hidden Super Admin Portal - Only owner knows this URL */}
          <Route path="/yacco-owner-admin" element={<SuperAdminLogin />} />
          
          {/* ========== PROTECTED ROUTES ========== */}
          <Route element={<Layout />}>
            <Route path="home" element={<RoleBasedRedirect />} />
            
            {/* Platform Owner (Super Admin) Portal */}
            <Route path="platform-admin" element={<PlatformOwnerPortal />} />
            <Route path="po-portal" element={<PlatformOwnerPortal />} />
            
            {/* Legacy Super Admin Dashboard */}
            <Route path="super-admin" element={<SuperAdminDashboard />} />
            
            {/* ========== HOSPITAL-SPECIFIC ROUTES ========== */}
            
            {/* Hospital Main Dashboard */}
            <Route path="hospital/:hospitalId/dashboard" element={<HospitalMainDashboard />} />
            
            {/* Hospital Admin Portal */}
            <Route path="hospital/:hospitalId/admin" element={<HospitalAdminPortal />} />
            
            {/* Hospital Super Admin IT Portal - Staff Management Only */}
            <Route path="hospital/:hospitalId/super-admin" element={<HospitalSuperAdminIT />} />
            <Route path="hospital/:hospitalId/it-admin" element={<HospitalSuperAdminIT />} />
            
            {/* Hospital Role-Specific Portals */}
            <Route path="hospital/:hospitalId/physician" element={<Dashboard />} />
            <Route path="hospital/:hospitalId/nurse" element={<NurseDashboard />} />
            <Route path="hospital/:hospitalId/scheduler" element={<SchedulerDashboard />} />
            <Route path="hospital/:hospitalId/billing" element={<BillingPage />} />
            <Route path="hospital/:hospitalId/department/:deptId" element={<Dashboard />} />
            
            {/* Hospital Shared Pages */}
            <Route path="hospital/:hospitalId/patients" element={<Patients />} />
            <Route path="hospital/:hospitalId/patients/:id" element={<PatientChart />} />
            <Route path="hospital/:hospitalId/appointments" element={<Appointments />} />
            <Route path="hospital/:hospitalId/orders" element={<Orders />} />
            
            {/* ========== LEGACY ROUTES (without hospitalId) ========== */}
            
            {/* Hospital Admin Settings */}
            <Route path="hospital-settings" element={<HospitalSettings />} />
            <Route path="admin-dashboard" element={<HospitalAdminPortal />} />
            
            {/* IT Admin Dashboard (without hospitalId) */}
            <Route path="it-admin" element={<HospitalSuperAdminIT />} />
            
            {/* Physician Dashboard */}
            <Route path="dashboard" element={<Dashboard />} />
            
            {/* Nurse Dashboard */}
            <Route path="nurse-station" element={<NurseDashboard />} />
            
            {/* Scheduler Dashboard */}
            <Route path="scheduling" element={<SchedulerDashboard />} />
            
            {/* Admin Dashboard */}
            <Route path="admin" element={<AdminDashboard />} />
            
            {/* Shared Pages */}
            <Route path="patients" element={<Patients />} />
            <Route path="patients/:id" element={<PatientChart />} />
            <Route path="appointments" element={<Appointments />} />
            <Route path="orders" element={<Orders />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="telehealth" element={<TelehealthPage />} />
            <Route path="telehealth/:sessionId" element={<TelehealthPage />} />
            <Route path="billing" element={<BillingPage />} />
            <Route path="records-sharing" element={<RecordsSharing />} />
            
            {/* Security & Audit */}
            <Route path="security" element={<SecuritySettings />} />
            <Route path="audit-logs" element={<AuditLogs />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </AuthProvider>
  );
}

export default App;
