import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "@/lib/auth";
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

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="patients" element={<Patients />} />
            <Route path="patients/:id" element={<PatientChart />} />
            <Route path="appointments" element={<Appointments />} />
            <Route path="orders" element={<Orders />} />
            <Route path="analytics" element={<Analytics />} />
          </Route>
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
    </AuthProvider>
  );
}

export default App;
