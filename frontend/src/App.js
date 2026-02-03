import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/lib/auth";
import { Toaster } from "@/components/ui/sonner";

// Pages
import LoginPage from "@/pages/Login";
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

// Role-based redirect component
function RoleBasedRedirect() {
  const { user } = useAuth();
  
  if (!user) return <Navigate to="/login" replace />;
  
  switch (user.role) {
    case 'super_admin':
      return <Navigate to="/platform-admin" replace />;
    case 'hospital_admin':
      return <Navigate to="/hospital-settings" replace />;
    case 'physician':
      return <Navigate to="/dashboard" replace />;
    case 'nurse':
      return <Navigate to="/nurse-station" replace />;
    case 'scheduler':
      return <Navigate to="/scheduling" replace />;
    case 'admin':
      return <Navigate to="/admin" replace />;
    default:
      return <Navigate to="/dashboard" replace />;
  }
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Customer-Facing Portal (Hospitals & Staff) */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/register-hospital" element={<HospitalRegistration />} />
          
          {/* Hidden Super Admin Portal - Only owner knows this URL */}
          <Route path="/yacco-owner-admin" element={<SuperAdminLogin />} />
          
          {/* Protected Routes */}
          <Route path="/" element={<Layout />}>
            <Route index element={<RoleBasedRedirect />} />
            {/* Super Admin Dashboard */}
            <Route path="platform-admin" element={<SuperAdminDashboard />} />
            {/* Hospital Admin Settings */}
            <Route path="hospital-settings" element={<HospitalSettings />} />
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
          </Route>
          <Route path="*" element={<RoleBasedRedirect />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </AuthProvider>
  );
}

export default App;
