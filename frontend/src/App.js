import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/lib/auth";
import { Toaster } from "@/components/ui/sonner";

// Pages
import LoginPage from "@/pages/Login";
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

// Role-based redirect component
function RoleBasedRedirect() {
  const { user } = useAuth();
  
  if (!user) return <Navigate to="/login" replace />;
  
  switch (user.role) {
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
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<Layout />}>
            <Route index element={<RoleBasedRedirect />} />
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
