import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/lib/auth";
import { Toaster } from "@/components/ui/sonner";

// Pages
import LoginPage from "@/pages/Login";
import RegionHospitalLogin from "@/pages/RegionHospitalLogin";
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
import HospitalSettings from "@/pages/HospitalSettings";
import HospitalRegistration from "@/pages/HospitalRegistration";
import BillingPage from "@/pages/BillingPage";
import RecordsSharing from "@/pages/RecordsSharing";
import SecuritySettings from "@/pages/SecuritySettings";
import AuditLogs from "@/pages/AuditLogs";

// Role-based redirect component
function RoleBasedRedirect() {
  const { user } = useAuth();
  
  if (!user) return <Navigate to="/login" replace />;
  
  switch (user.role) {
    case 'super_admin':
      return <Navigate to="/platform-admin" replace />;
    case 'hospital_admin':
      return <Navigate to="/admin-dashboard" replace />;
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
          {/* Ghana Region-Based Login - Main Entry Point */}
          <Route path="/login" element={<RegionHospitalLogin />} />
          
          {/* Legacy/Direct Login (for backward compatibility) */}
          <Route path="/direct-login" element={<LoginPage />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/register-hospital" element={<HospitalRegistration />} />
          
          {/* Hidden Super Admin Portal - Only owner knows this URL */}
          <Route path="/yacco-owner-admin" element={<SuperAdminLogin />} />
          
          {/* Protected Routes */}
          <Route path="/" element={<Layout />}>
            <Route index element={<RoleBasedRedirect />} />
            {/* Platform Owner (Super Admin) Portal */}
            <Route path="platform-admin" element={<PlatformOwnerPortal />} />
            <Route path="po-portal" element={<PlatformOwnerPortal />} />
            {/* Legacy Super Admin Dashboard */}
            <Route path="super-admin" element={<SuperAdminDashboard />} />
            {/* Hospital Admin Settings */}
            <Route path="hospital-settings" element={<HospitalSettings />} />
            <Route path="admin-dashboard" element={<AdminDashboard />} />
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
          <Route path="*" element={<RoleBasedRedirect />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </AuthProvider>
  );
}

export default App;
