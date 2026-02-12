import { useState, useEffect } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter, DialogClose } from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { 
  Heart, Link2, Shield, Building2, Users, Stethoscope, 
  LogIn, LogOut, Settings, BarChart3, MapPin, Phone,
  Mail, Plus, Search, Edit, Trash2, Activity, Pill,
  ClipboardList, FileText, Globe, Check, X, Menu,
  ChevronRight, ArrowRight, Hospital, Store
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Ghana Regions Data
const GHANA_REGIONS = [
  { id: "greater-accra", name: "Greater Accra", capital: "Accra" },
  { id: "ashanti", name: "Ashanti", capital: "Kumasi" },
  { id: "central", name: "Central", capital: "Cape Coast" },
  { id: "eastern", name: "Eastern", capital: "Koforidua" },
  { id: "western", name: "Western", capital: "Sekondi-Takoradi" },
  { id: "western-north", name: "Western North", capital: "Sefwi Wiawso" },
  { id: "volta", name: "Volta", capital: "Ho" },
  { id: "oti", name: "Oti", capital: "Dambai" },
  { id: "northern", name: "Northern", capital: "Tamale" },
  { id: "savannah", name: "Savannah", capital: "Damongo" },
  { id: "north-east", name: "North East", capital: "Nalerigu" },
  { id: "upper-east", name: "Upper East", capital: "Bolgatanga" },
  { id: "upper-west", name: "Upper West", capital: "Wa" },
  { id: "bono", name: "Bono", capital: "Sunyani" },
  { id: "bono-east", name: "Bono East", capital: "Techiman" },
  { id: "ahafo", name: "Ahafo", capital: "Goaso" },
];

const USER_ROLES = [
  { value: "it_admin", label: "IT Admin" },
  { value: "facility_admin", label: "Facility Admin" },
  { value: "physician", label: "Physician" },
  { value: "nurse", label: "Nurse" },
  { value: "pharmacist", label: "Pharmacist" },
  { value: "dispenser", label: "Dispenser" },
  { value: "scheduler", label: "Scheduler" },
];

const FACILITY_TYPES = [
  { value: "teaching_hospital", label: "Teaching Hospital" },
  { value: "regional_hospital", label: "Regional Hospital" },
  { value: "district_hospital", label: "District Hospital" },
  { value: "clinic", label: "Clinic" },
  { value: "chps_compound", label: "CHPS Compound" },
  { value: "pharmacy", label: "Pharmacy" },
];

// Auth Context
const useAuth = () => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("yacco_token"));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      const savedToken = localStorage.getItem("yacco_token");
      if (savedToken) {
        try {
          const response = await axios.get(`${API}/auth/me`, {
            headers: { Authorization: `Bearer ${savedToken}` }
          });
          setUser(response.data);
          setToken(savedToken);
        } catch (e) {
          localStorage.removeItem("yacco_token");
          setToken(null);
          setUser(null);
        }
      }
      setLoading(false);
    };
    checkAuth();
  }, []);

  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, { email, password });
    localStorage.setItem("yacco_token", response.data.token);
    setToken(response.data.token);
    setUser(response.data.user);
    return response.data;
  };

  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch (e) {
      console.error("Logout error:", e);
    }
    localStorage.removeItem("yacco_token");
    setToken(null);
    setUser(null);
  };

  return { user, token, loading, login, logout };
};

// Landing Page
const LandingPage = () => {
  const navigate = useNavigate();
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-emerald-50/30 to-teal-50/40">
      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-white/80 border-b border-slate-200/60">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-lg shadow-emerald-500/25">
              <Heart className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-800 tracking-tight">Yacco Health</h1>
              <p className="text-xs text-slate-500">Ghana Healthcare Network</p>
            </div>
          </div>
          <nav className="hidden md:flex items-center gap-8">
            <a href="#portals" className="text-sm font-medium text-slate-600 hover:text-emerald-600 transition-colors">Portals</a>
            <a href="#regions" className="text-sm font-medium text-slate-600 hover:text-emerald-600 transition-colors">Regions</a>
            <a href="#help" className="text-sm font-medium text-slate-600 hover:text-emerald-600 transition-colors">Help</a>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative py-20 px-6">
        <div className="max-w-6xl mx-auto text-center">
          <Badge variant="outline" className="mb-6 px-4 py-1.5 text-emerald-700 border-emerald-200 bg-emerald-50">
            <Shield className="w-3.5 h-3.5 mr-2" />
            Ghana Health Service Certified
          </Badge>
          <h2 className="text-5xl md:text-6xl font-bold mb-6">
            <span className="bg-gradient-to-r from-emerald-600 via-teal-500 to-cyan-500 bg-clip-text text-transparent">
              Ghana's Integrated
            </span>
            <br />
            <span className="text-slate-800">Healthcare Platform</span>
          </h2>
          <p className="text-xl text-slate-600 max-w-2xl mx-auto mb-12">
            Connecting hospitals and pharmacies across all 16 administrative regions. 
            Choose your portal below to get started.
          </p>
        </div>
      </section>

      {/* Portal Cards */}
      <section id="portals" className="px-6 pb-20">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-8">
          {/* EMR Portal Card */}
          <Card className="group relative overflow-hidden border-2 border-emerald-100 hover:border-emerald-300 transition-all duration-300 hover:shadow-2xl hover:shadow-emerald-500/10">
            <div className="absolute inset-x-0 top-0 h-1.5 bg-gradient-to-r from-emerald-400 to-teal-500" />
            <CardHeader className="pt-8 pb-4">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center mb-4 shadow-lg shadow-emerald-500/30 group-hover:scale-110 transition-transform">
                <Heart className="w-8 h-8 text-white" />
              </div>
              <CardTitle className="text-2xl text-slate-800">Yacco EMR</CardTitle>
              <CardDescription className="text-base">Electronic Medical Records for Hospitals</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-start gap-3">
                  <Shield className="w-5 h-5 text-emerald-500 mt-0.5" />
                  <div>
                    <p className="font-medium text-slate-700 text-sm">Secure & Compliant</p>
                    <p className="text-xs text-slate-500">HIPAA-aligned security with full audit trails</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Building2 className="w-5 h-5 text-emerald-500 mt-0.5" />
                  <div>
                    <p className="font-medium text-slate-700 text-sm">Multi-Facility</p>
                    <p className="text-xs text-slate-500">Regional Hospitals to CHPS Compounds</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Users className="w-5 h-5 text-emerald-500 mt-0.5" />
                  <div>
                    <p className="font-medium text-slate-700 text-sm">Role-Based Access</p>
                    <p className="text-xs text-slate-500">Physicians, Nurses, Schedulers, Admins</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Stethoscope className="w-5 h-5 text-emerald-500 mt-0.5" />
                  <div>
                    <p className="font-medium text-slate-700 text-sm">Clinical Tools</p>
                    <p className="text-xs text-slate-500">AI documentation, FHIR, Telehealth</p>
                  </div>
                </div>
              </div>
              <Button className="w-full h-12 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white shadow-lg shadow-emerald-500/25" data-testid="enter-emr-portal-btn">
                <LogIn className="w-4 h-4 mr-2" />
                Enter EMR Portal
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
              <p className="text-center text-xs text-slate-500">Hospitals, Clinics & Healthcare Facilities</p>
            </CardContent>
          </Card>

          {/* Pharmacy Portal Card */}
          <Card className="group relative overflow-hidden border-2 border-blue-100 hover:border-blue-300 transition-all duration-300 hover:shadow-2xl hover:shadow-blue-500/10">
            <div className="absolute inset-x-0 top-0 h-1.5 bg-gradient-to-r from-blue-500 to-indigo-500" />
            <CardHeader className="pt-8 pb-4">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center mb-4 shadow-lg shadow-blue-500/30 group-hover:scale-110 transition-transform">
                <Link2 className="w-8 h-8 text-white" />
              </div>
              <CardTitle className="text-2xl text-slate-800">Yacco Pharm</CardTitle>
              <CardDescription className="text-base">National Pharmacy Network Portal</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-start gap-3">
                  <FileText className="w-5 h-5 text-blue-500 mt-0.5" />
                  <div>
                    <p className="font-medium text-slate-700 text-sm">e-Prescription</p>
                    <p className="text-xs text-slate-500">Receive prescriptions from hospitals</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <ClipboardList className="w-5 h-5 text-blue-500 mt-0.5" />
                  <div>
                    <p className="font-medium text-slate-700 text-sm">NHIS Claims</p>
                    <p className="text-xs text-slate-500">Direct insurance claim processing</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Pill className="w-5 h-5 text-blue-500 mt-0.5" />
                  <div>
                    <p className="font-medium text-slate-700 text-sm">Inventory</p>
                    <p className="text-xs text-slate-500">Stock tracking & expiry alerts</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <Globe className="w-5 h-5 text-blue-500 mt-0.5" />
                  <div>
                    <p className="font-medium text-slate-700 text-sm">Nationwide</p>
                    <p className="text-xs text-slate-500">Connect across all 16 regions</p>
                  </div>
                </div>
              </div>
              <Button className="w-full h-12 bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white shadow-lg shadow-blue-500/25" data-testid="pharmacy-portal-btn">
                <Store className="w-4 h-4 mr-2" />
                Pharmacy Portal
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
              <p className="text-center text-xs text-slate-500">Pharmacy Owners, Pharmacists, Dispensers</p>
              <button className="w-full flex items-center justify-center gap-2 text-blue-600 hover:text-blue-700 text-sm font-medium" data-testid="register-pharmacy-btn">
                <Link2 className="w-4 h-4" />
                Register Your Pharmacy
                <ChevronRight className="w-4 h-4" />
              </button>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 px-6 bg-white/60 border-y border-slate-200/60">
        <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8">
          <div className="text-center">
            <p className="text-4xl font-bold text-emerald-600 mb-1">16</p>
            <p className="text-slate-600 text-sm">Regions Covered</p>
          </div>
          <div className="text-center">
            <p className="text-4xl font-bold text-emerald-600 mb-1">200+</p>
            <p className="text-slate-600 text-sm">Health Facilities</p>
          </div>
          <div className="text-center">
            <p className="text-4xl font-bold text-emerald-600 mb-1">133+</p>
            <p className="text-slate-600 text-sm">Registered Pharmacies</p>
          </div>
          <div className="text-center">
            <p className="text-4xl font-bold text-emerald-600 mb-1">24/7</p>
            <p className="text-slate-600 text-sm">Emergency Services</p>
          </div>
        </div>
      </section>

      {/* Regions Section */}
      <section id="regions" className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <Badge variant="outline" className="mb-4 px-3 py-1 text-slate-600 border-slate-300">
              16 Administrative Regions
            </Badge>
            <h3 className="text-3xl font-bold text-slate-800 mb-3">Nationwide Coverage</h3>
            <p className="text-slate-600">Healthcare connectivity across all regions of Ghana</p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {GHANA_REGIONS.map((region) => (
              <Card key={region.id} className="p-4 hover:shadow-md transition-shadow border-slate-200 hover:border-emerald-300">
                <div className="flex items-center gap-3">
                  <MapPin className="w-5 h-5 text-emerald-500" />
                  <div>
                    <p className="font-semibold text-slate-800 text-sm">{region.name}</p>
                    <p className="text-xs text-slate-500">{region.capital}</p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Help Section */}
      <section id="help" className="py-16 px-6 bg-slate-800 text-white">
        <div className="max-w-4xl mx-auto text-center">
          <h3 className="text-2xl font-bold mb-4">Need Help?</h3>
          <p className="text-slate-300 mb-8">Contact your local health facility administrator or reach out to our support team</p>
          <div className="flex flex-wrap justify-center gap-6">
            <div className="flex items-center gap-2 text-slate-300">
              <Phone className="w-5 h-5" />
              <span>+233 30 123 4567</span>
            </div>
            <div className="flex items-center gap-2 text-slate-300">
              <Mail className="w-5 h-5" />
              <span>support@yacco.health</span>
            </div>
          </div>
          <Separator className="my-8 bg-slate-700" />
          <p className="text-slate-400 text-sm mb-4">Platform Administrators:</p>
          <Button 
            variant="outline" 
            className="border-slate-600 text-slate-300 hover:bg-slate-700 hover:text-white"
            onClick={() => navigate('/it-admin')}
            data-testid="platform-admin-access-btn"
          >
            <Settings className="w-4 h-4 mr-2" />
            Platform Admin Access
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 bg-slate-900 text-slate-400 text-center text-sm">
        <p>© 2026 Yacco Health. Ghana Healthcare Network. All rights reserved.</p>
      </footer>
    </div>
  );
};

// IT Admin Login Page
const ITAdminLogin = ({ onLogin }) => {
  const [email, setEmail] = useState("admin@yacco.health");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [seeding, setSeeding] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await onLogin(email, password);
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed. Please check your credentials.");
    }
    setLoading(false);
  };

  const handleSeedData = async () => {
    setSeeding(true);
    try {
      await axios.post(`${API}/seed`);
      setError("");
      alert("Demo data created! You can now login with admin@yacco.health / admin123");
    } catch (err) {
      console.error("Seed error:", err);
    }
    setSeeding(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-6">
      <Card className="w-full max-w-md border-slate-700 bg-slate-800/50 backdrop-blur-sm">
        <CardHeader className="text-center pb-2">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-orange-500 to-red-600 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-orange-500/30">
            <Settings className="w-8 h-8 text-white" />
          </div>
          <CardTitle className="text-2xl text-white">IT Admin Portal</CardTitle>
          <CardDescription className="text-slate-400">Yacco Health Platform Administration</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-slate-300">Email</Label>
              <Input 
                id="email" 
                type="email" 
                value={email} 
                onChange={(e) => setEmail(e.target.value)}
                className="bg-slate-700/50 border-slate-600 text-white placeholder:text-slate-500"
                placeholder="admin@yacco.health"
                data-testid="login-email-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password" className="text-slate-300">Password</Label>
              <Input 
                id="password" 
                type="password" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)}
                className="bg-slate-700/50 border-slate-600 text-white placeholder:text-slate-500"
                placeholder="••••••••"
                data-testid="login-password-input"
              />
            </div>
            {error && (
              <p className="text-red-400 text-sm" data-testid="login-error">{error}</p>
            )}
            <Button 
              type="submit" 
              className="w-full bg-gradient-to-r from-orange-500 to-red-600 hover:from-orange-600 hover:to-red-700 text-white"
              disabled={loading}
              data-testid="login-submit-btn"
            >
              {loading ? "Signing in..." : "Sign In"}
            </Button>
          </form>
          <Separator className="my-6 bg-slate-700" />
          <Button 
            variant="outline" 
            className="w-full border-slate-600 text-slate-300 hover:bg-slate-700"
            onClick={handleSeedData}
            disabled={seeding}
            data-testid="seed-data-btn"
          >
            {seeding ? "Creating demo data..." : "Initialize Demo Data"}
          </Button>
          <p className="text-xs text-slate-500 text-center mt-2">
            Creates admin account and sample facilities
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

// IT Admin Dashboard
const ITAdminDashboard = ({ user, token, onLogout }) => {
  const [activeTab, setActiveTab] = useState("overview");
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [facilities, setFacilities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  // User dialog state
  const [userDialogOpen, setUserDialogOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [userForm, setUserForm] = useState({ name: "", email: "", password: "", role: "", region_id: "", phone: "", is_active: true });

  // Facility dialog state
  const [facilityDialogOpen, setFacilityDialogOpen] = useState(false);
  const [editingFacility, setEditingFacility] = useState(null);
  const [facilityForm, setFacilityForm] = useState({ name: "", facility_type: "", region_id: "", address: "", phone: "", email: "", is_active: true, nhis_registered: false });

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsRes, usersRes, facilitiesRes] = await Promise.all([
        axios.get(`${API}/stats`, { headers }),
        axios.get(`${API}/users`, { headers }),
        axios.get(`${API}/facilities`, { headers })
      ]);
      setStats(statsRes.data);
      setUsers(usersRes.data);
      setFacilities(facilitiesRes.data);
    } catch (err) {
      console.error("Fetch error:", err);
    }
    setLoading(false);
  };

  // User CRUD
  const handleSaveUser = async () => {
    try {
      if (editingUser) {
        await axios.put(`${API}/users/${editingUser.id}`, userForm, { headers });
      } else {
        await axios.post(`${API}/users`, userForm, { headers });
      }
      setUserDialogOpen(false);
      setEditingUser(null);
      setUserForm({ name: "", email: "", password: "", role: "", region_id: "", phone: "", is_active: true });
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to save user");
    }
  };

  const handleEditUser = (u) => {
    setEditingUser(u);
    setUserForm({ ...u, password: "" });
    setUserDialogOpen(true);
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm("Are you sure you want to delete this user?")) return;
    try {
      await axios.delete(`${API}/users/${userId}`, { headers });
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to delete user");
    }
  };

  // Facility CRUD
  const handleSaveFacility = async () => {
    try {
      if (editingFacility) {
        await axios.put(`${API}/facilities/${editingFacility.id}`, facilityForm, { headers });
      } else {
        await axios.post(`${API}/facilities`, facilityForm, { headers });
      }
      setFacilityDialogOpen(false);
      setEditingFacility(null);
      setFacilityForm({ name: "", facility_type: "", region_id: "", address: "", phone: "", email: "", is_active: true, nhis_registered: false });
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to save facility");
    }
  };

  const handleEditFacility = (f) => {
    setEditingFacility(f);
    setFacilityForm({ ...f });
    setFacilityDialogOpen(true);
  };

  const handleDeleteFacility = async (facilityId) => {
    if (!window.confirm("Are you sure you want to delete this facility?")) return;
    try {
      await axios.delete(`${API}/facilities/${facilityId}`, { headers });
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to delete facility");
    }
  };

  const getRegionName = (id) => GHANA_REGIONS.find(r => r.id === id)?.name || id;
  const getRoleLabel = (value) => USER_ROLES.find(r => r.value === value)?.label || value;
  const getFacilityTypeLabel = (value) => FACILITY_TYPES.find(t => t.value === value)?.label || value;

  const filteredUsers = users.filter(u => 
    u.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.email?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredFacilities = facilities.filter(f =>
    f.name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-slate-800 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-red-600 flex items-center justify-center">
              <Settings className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">IT Admin Portal</h1>
              <p className="text-xs text-slate-400">Yacco Health Platform</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right hidden md:block">
              <p className="text-sm text-white font-medium">{user?.name}</p>
              <p className="text-xs text-slate-400">{user?.email}</p>
            </div>
            <Button 
              variant="outline" 
              size="sm"
              className="border-slate-600 text-slate-300 hover:bg-slate-700"
              onClick={onLogout}
              data-testid="logout-btn"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="bg-slate-800 border border-slate-700">
            <TabsTrigger value="overview" className="data-[state=active]:bg-orange-500 data-[state=active]:text-white" data-testid="tab-overview">
              <BarChart3 className="w-4 h-4 mr-2" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="users" className="data-[state=active]:bg-orange-500 data-[state=active]:text-white" data-testid="tab-users">
              <Users className="w-4 h-4 mr-2" />
              Users
            </TabsTrigger>
            <TabsTrigger value="facilities" className="data-[state=active]:bg-orange-500 data-[state=active]:text-white" data-testid="tab-facilities">
              <Building2 className="w-4 h-4 mr-2" />
              Facilities
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <Card className="bg-slate-800 border-slate-700">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-slate-400 text-sm">Total Users</p>
                      <p className="text-3xl font-bold text-white">{stats?.total_users || 0}</p>
                    </div>
                    <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center">
                      <Users className="w-6 h-6 text-blue-400" />
                    </div>
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-slate-800 border-slate-700">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-slate-400 text-sm">Active Users</p>
                      <p className="text-3xl font-bold text-white">{stats?.active_users || 0}</p>
                    </div>
                    <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center">
                      <Activity className="w-6 h-6 text-emerald-400" />
                    </div>
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-slate-800 border-slate-700">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-slate-400 text-sm">Facilities</p>
                      <p className="text-3xl font-bold text-white">{stats?.total_facilities || 0}</p>
                    </div>
                    <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center">
                      <Hospital className="w-6 h-6 text-purple-400" />
                    </div>
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-slate-800 border-slate-700">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-slate-400 text-sm">Pharmacies</p>
                      <p className="text-3xl font-bold text-white">{stats?.total_pharmacies || 0}</p>
                    </div>
                    <div className="w-12 h-12 rounded-xl bg-orange-500/20 flex items-center justify-center">
                      <Pill className="w-6 h-6 text-orange-400" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Recent Activity */}
            <Card className="bg-slate-800 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-4">
                <Button onClick={() => { setActiveTab("users"); setUserDialogOpen(true); }} className="bg-blue-600 hover:bg-blue-700" data-testid="quick-add-user-btn">
                  <Plus className="w-4 h-4 mr-2" />
                  Add User
                </Button>
                <Button onClick={() => { setActiveTab("facilities"); setFacilityDialogOpen(true); }} className="bg-purple-600 hover:bg-purple-700" data-testid="quick-add-facility-btn">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Facility
                </Button>
                <Button variant="outline" onClick={fetchData} className="border-slate-600 text-slate-300 hover:bg-slate-700" data-testid="refresh-data-btn">
                  <Activity className="w-4 h-4 mr-2" />
                  Refresh Data
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Users Tab */}
          <TabsContent value="users" className="space-y-4">
            <div className="flex flex-col md:flex-row gap-4 justify-between">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input 
                  placeholder="Search users..." 
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 bg-slate-800 border-slate-700 text-white placeholder:text-slate-500"
                  data-testid="search-users-input"
                />
              </div>
              <Dialog open={userDialogOpen} onOpenChange={setUserDialogOpen}>
                <DialogTrigger asChild>
                  <Button 
                    className="bg-orange-500 hover:bg-orange-600"
                    onClick={() => { setEditingUser(null); setUserForm({ name: "", email: "", password: "", role: "", region_id: "", phone: "", is_active: true }); }}
                    data-testid="add-user-btn"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Add User
                  </Button>
                </DialogTrigger>
                <DialogContent className="bg-slate-800 border-slate-700 text-white">
                  <DialogHeader>
                    <DialogTitle>{editingUser ? "Edit User" : "Add New User"}</DialogTitle>
                    <DialogDescription className="text-slate-400">
                      {editingUser ? "Update user information" : "Create a new user account"}
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label className="text-slate-300">Name</Label>
                        <Input 
                          value={userForm.name} 
                          onChange={(e) => setUserForm({...userForm, name: e.target.value})}
                          className="bg-slate-700 border-slate-600 text-white"
                          data-testid="user-form-name"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label className="text-slate-300">Email</Label>
                        <Input 
                          type="email"
                          value={userForm.email} 
                          onChange={(e) => setUserForm({...userForm, email: e.target.value})}
                          className="bg-slate-700 border-slate-600 text-white"
                          data-testid="user-form-email"
                        />
                      </div>
                    </div>
                    {!editingUser && (
                      <div className="space-y-2">
                        <Label className="text-slate-300">Password</Label>
                        <Input 
                          type="password"
                          value={userForm.password} 
                          onChange={(e) => setUserForm({...userForm, password: e.target.value})}
                          className="bg-slate-700 border-slate-600 text-white"
                          data-testid="user-form-password"
                        />
                      </div>
                    )}
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label className="text-slate-300">Role</Label>
                        <Select value={userForm.role} onValueChange={(v) => setUserForm({...userForm, role: v})}>
                          <SelectTrigger className="bg-slate-700 border-slate-600 text-white" data-testid="user-form-role">
                            <SelectValue placeholder="Select role" />
                          </SelectTrigger>
                          <SelectContent className="bg-slate-800 border-slate-700">
                            {USER_ROLES.map(role => (
                              <SelectItem key={role.value} value={role.value} className="text-white hover:bg-slate-700">{role.label}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label className="text-slate-300">Region</Label>
                        <Select value={userForm.region_id} onValueChange={(v) => setUserForm({...userForm, region_id: v})}>
                          <SelectTrigger className="bg-slate-700 border-slate-600 text-white" data-testid="user-form-region">
                            <SelectValue placeholder="Select region" />
                          </SelectTrigger>
                          <SelectContent className="bg-slate-800 border-slate-700">
                            {GHANA_REGIONS.map(region => (
                              <SelectItem key={region.id} value={region.id} className="text-white hover:bg-slate-700">{region.name}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-slate-300">Phone</Label>
                      <Input 
                        value={userForm.phone} 
                        onChange={(e) => setUserForm({...userForm, phone: e.target.value})}
                        className="bg-slate-700 border-slate-600 text-white"
                        placeholder="+233..."
                        data-testid="user-form-phone"
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <Label className="text-slate-300">Active Status</Label>
                      <Switch 
                        checked={userForm.is_active} 
                        onCheckedChange={(v) => setUserForm({...userForm, is_active: v})}
                        data-testid="user-form-active"
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <DialogClose asChild>
                      <Button variant="outline" className="border-slate-600 text-slate-300 hover:bg-slate-700">Cancel</Button>
                    </DialogClose>
                    <Button onClick={handleSaveUser} className="bg-orange-500 hover:bg-orange-600" data-testid="user-form-submit">
                      {editingUser ? "Update" : "Create"}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>

            <Card className="bg-slate-800 border-slate-700">
              <ScrollArea className="h-[500px]">
                <table className="w-full">
                  <thead className="bg-slate-900/50 sticky top-0">
                    <tr>
                      <th className="text-left p-4 text-slate-400 text-sm font-medium">User</th>
                      <th className="text-left p-4 text-slate-400 text-sm font-medium">Role</th>
                      <th className="text-left p-4 text-slate-400 text-sm font-medium">Region</th>
                      <th className="text-left p-4 text-slate-400 text-sm font-medium">Status</th>
                      <th className="text-right p-4 text-slate-400 text-sm font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredUsers.map((u) => (
                      <tr key={u.id} className="border-t border-slate-700 hover:bg-slate-700/50" data-testid={`user-row-${u.id}`}>
                        <td className="p-4">
                          <div>
                            <p className="text-white font-medium">{u.name}</p>
                            <p className="text-slate-400 text-sm">{u.email}</p>
                          </div>
                        </td>
                        <td className="p-4">
                          <Badge variant="outline" className="text-slate-300 border-slate-600">
                            {getRoleLabel(u.role)}
                          </Badge>
                        </td>
                        <td className="p-4 text-slate-300">{getRegionName(u.region_id) || "-"}</td>
                        <td className="p-4">
                          {u.is_active ? (
                            <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30">Active</Badge>
                          ) : (
                            <Badge className="bg-red-500/20 text-red-400 border-red-500/30">Inactive</Badge>
                          )}
                        </td>
                        <td className="p-4 text-right">
                          <div className="flex justify-end gap-2">
                            <Button size="sm" variant="outline" onClick={() => handleEditUser(u)} className="border-slate-600 text-slate-300 hover:bg-slate-700" data-testid={`edit-user-${u.id}`}>
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button size="sm" variant="outline" onClick={() => handleDeleteUser(u.id)} className="border-red-600 text-red-400 hover:bg-red-500/20" data-testid={`delete-user-${u.id}`}>
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </ScrollArea>
            </Card>
          </TabsContent>

          {/* Facilities Tab */}
          <TabsContent value="facilities" className="space-y-4">
            <div className="flex flex-col md:flex-row gap-4 justify-between">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input 
                  placeholder="Search facilities..." 
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 bg-slate-800 border-slate-700 text-white placeholder:text-slate-500"
                  data-testid="search-facilities-input"
                />
              </div>
              <Dialog open={facilityDialogOpen} onOpenChange={setFacilityDialogOpen}>
                <DialogTrigger asChild>
                  <Button 
                    className="bg-orange-500 hover:bg-orange-600"
                    onClick={() => { setEditingFacility(null); setFacilityForm({ name: "", facility_type: "", region_id: "", address: "", phone: "", email: "", is_active: true, nhis_registered: false }); }}
                    data-testid="add-facility-btn"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Add Facility
                  </Button>
                </DialogTrigger>
                <DialogContent className="bg-slate-800 border-slate-700 text-white max-w-lg">
                  <DialogHeader>
                    <DialogTitle>{editingFacility ? "Edit Facility" : "Add New Facility"}</DialogTitle>
                    <DialogDescription className="text-slate-400">
                      {editingFacility ? "Update facility information" : "Register a new healthcare facility"}
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label className="text-slate-300">Facility Name</Label>
                      <Input 
                        value={facilityForm.name} 
                        onChange={(e) => setFacilityForm({...facilityForm, name: e.target.value})}
                        className="bg-slate-700 border-slate-600 text-white"
                        data-testid="facility-form-name"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label className="text-slate-300">Type</Label>
                        <Select value={facilityForm.facility_type} onValueChange={(v) => setFacilityForm({...facilityForm, facility_type: v})}>
                          <SelectTrigger className="bg-slate-700 border-slate-600 text-white" data-testid="facility-form-type">
                            <SelectValue placeholder="Select type" />
                          </SelectTrigger>
                          <SelectContent className="bg-slate-800 border-slate-700">
                            {FACILITY_TYPES.map(type => (
                              <SelectItem key={type.value} value={type.value} className="text-white hover:bg-slate-700">{type.label}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label className="text-slate-300">Region</Label>
                        <Select value={facilityForm.region_id} onValueChange={(v) => setFacilityForm({...facilityForm, region_id: v})}>
                          <SelectTrigger className="bg-slate-700 border-slate-600 text-white" data-testid="facility-form-region">
                            <SelectValue placeholder="Select region" />
                          </SelectTrigger>
                          <SelectContent className="bg-slate-800 border-slate-700">
                            {GHANA_REGIONS.map(region => (
                              <SelectItem key={region.id} value={region.id} className="text-white hover:bg-slate-700">{region.name}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label className="text-slate-300">Address</Label>
                      <Input 
                        value={facilityForm.address} 
                        onChange={(e) => setFacilityForm({...facilityForm, address: e.target.value})}
                        className="bg-slate-700 border-slate-600 text-white"
                        data-testid="facility-form-address"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label className="text-slate-300">Phone</Label>
                        <Input 
                          value={facilityForm.phone} 
                          onChange={(e) => setFacilityForm({...facilityForm, phone: e.target.value})}
                          className="bg-slate-700 border-slate-600 text-white"
                          placeholder="+233..."
                          data-testid="facility-form-phone"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label className="text-slate-300">Email</Label>
                        <Input 
                          type="email"
                          value={facilityForm.email} 
                          onChange={(e) => setFacilityForm({...facilityForm, email: e.target.value})}
                          className="bg-slate-700 border-slate-600 text-white"
                          data-testid="facility-form-email"
                        />
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <Label className="text-slate-300">Active Status</Label>
                      <Switch 
                        checked={facilityForm.is_active} 
                        onCheckedChange={(v) => setFacilityForm({...facilityForm, is_active: v})}
                        data-testid="facility-form-active"
                      />
                    </div>
                    <div className="flex items-center justify-between">
                      <Label className="text-slate-300">NHIS Registered</Label>
                      <Switch 
                        checked={facilityForm.nhis_registered} 
                        onCheckedChange={(v) => setFacilityForm({...facilityForm, nhis_registered: v})}
                        data-testid="facility-form-nhis"
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <DialogClose asChild>
                      <Button variant="outline" className="border-slate-600 text-slate-300 hover:bg-slate-700">Cancel</Button>
                    </DialogClose>
                    <Button onClick={handleSaveFacility} className="bg-orange-500 hover:bg-orange-600" data-testid="facility-form-submit">
                      {editingFacility ? "Update" : "Create"}
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>

            <Card className="bg-slate-800 border-slate-700">
              <ScrollArea className="h-[500px]">
                <table className="w-full">
                  <thead className="bg-slate-900/50 sticky top-0">
                    <tr>
                      <th className="text-left p-4 text-slate-400 text-sm font-medium">Facility</th>
                      <th className="text-left p-4 text-slate-400 text-sm font-medium">Type</th>
                      <th className="text-left p-4 text-slate-400 text-sm font-medium">Region</th>
                      <th className="text-left p-4 text-slate-400 text-sm font-medium">NHIS</th>
                      <th className="text-left p-4 text-slate-400 text-sm font-medium">Status</th>
                      <th className="text-right p-4 text-slate-400 text-sm font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredFacilities.map((f) => (
                      <tr key={f.id} className="border-t border-slate-700 hover:bg-slate-700/50" data-testid={`facility-row-${f.id}`}>
                        <td className="p-4">
                          <div>
                            <p className="text-white font-medium">{f.name}</p>
                            <p className="text-slate-400 text-sm">{f.address || "-"}</p>
                          </div>
                        </td>
                        <td className="p-4">
                          <Badge variant="outline" className="text-slate-300 border-slate-600">
                            {getFacilityTypeLabel(f.facility_type)}
                          </Badge>
                        </td>
                        <td className="p-4 text-slate-300">{getRegionName(f.region_id)}</td>
                        <td className="p-4">
                          {f.nhis_registered ? (
                            <Check className="w-5 h-5 text-emerald-400" />
                          ) : (
                            <X className="w-5 h-5 text-slate-500" />
                          )}
                        </td>
                        <td className="p-4">
                          {f.is_active ? (
                            <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30">Active</Badge>
                          ) : (
                            <Badge className="bg-red-500/20 text-red-400 border-red-500/30">Inactive</Badge>
                          )}
                        </td>
                        <td className="p-4 text-right">
                          <div className="flex justify-end gap-2">
                            <Button size="sm" variant="outline" onClick={() => handleEditFacility(f)} className="border-slate-600 text-slate-300 hover:bg-slate-700" data-testid={`edit-facility-${f.id}`}>
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button size="sm" variant="outline" onClick={() => handleDeleteFacility(f.id)} className="border-red-600 text-red-400 hover:bg-red-500/20" data-testid={`delete-facility-${f.id}`}>
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </ScrollArea>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

// IT Admin Page Wrapper
const ITAdminPage = () => {
  const { user, token, loading, login, logout } = useAuth();
  const navigate = useNavigate();

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  if (!user || user.role !== "it_admin") {
    return <ITAdminLogin onLogin={login} />;
  }

  return <ITAdminDashboard user={user} token={token} onLogout={logout} />;
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/it-admin" element={<ITAdminPage />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
