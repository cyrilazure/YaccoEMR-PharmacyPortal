import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import { regionAPI } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import { 
  Activity, MapPin, Building2, Users, LogIn, UserPlus,
  Heart, Shield, Phone, Mail, Globe, ChevronRight,
  Stethoscope, FileText, Calendar, Smartphone, Lock,
  CheckCircle, Star, ArrowRight, Clock, HelpCircle,
  Loader2, Hospital, Landmark, Menu, X
} from 'lucide-react';

// Ghana's 16 Administrative Regions
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

export default function EMRLandingPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [regions, setRegions] = useState(GHANA_REGIONS);
  const [selectedRegion, setSelectedRegion] = useState(null);
  const [loading, setLoading] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [regionHospitalCounts, setRegionHospitalCounts] = useState({});

  // Redirect if already logged in
  useEffect(() => {
    if (user) {
      const redirects = {
        'super_admin': '/platform-admin',
        'hospital_admin': '/admin-dashboard',
        'hospital_it_admin': '/admin-dashboard',
        'physician': '/dashboard',
        'nurse': '/nurse-station',
        'scheduler': '/scheduling',
        'biller': '/billing'
      };
      navigate(redirects[user.role] || '/dashboard');
    }
  }, [user, navigate]);

  // Load region hospital counts
  useEffect(() => {
    const fetchRegionData = async () => {
      try {
        const response = await regionAPI.getRegions();
        const regionsData = response.data.regions || [];
        const counts = {};
        regionsData.forEach(r => {
          counts[r.id] = r.hospital_count || 0;
        });
        setRegionHospitalCounts(counts);
      } catch (err) {
        console.log('Could not load region data');
      }
    };
    fetchRegionData();
  }, []);

  const handleRegionSelect = (region) => {
    setSelectedRegion(region);
    // Store in localStorage for routing
    localStorage.setItem('selected_region', JSON.stringify(region));
  };

  const handleProceedToLogin = () => {
    if (selectedRegion) {
      navigate('/login', { state: { region: selectedRegion } });
    } else {
      navigate('/login');
    }
  };

  const handleProceedToSignup = () => {
    navigate('/signup');
  };

  const features = [
    {
      icon: Shield,
      title: 'Secure & Compliant',
      description: 'HIPAA-aligned security with full audit trails and data encryption'
    },
    {
      icon: Hospital,
      title: 'Multi-Facility Support',
      description: 'Manage multiple health facilities from District Hospitals to CHPS Compounds'
    },
    {
      icon: Users,
      title: 'Role-Based Access',
      description: 'Tailored portals for Physicians, Nurses, Schedulers, and Administrators'
    },
    {
      icon: Globe,
      title: 'Nationwide Coverage',
      description: 'Connected across all 16 administrative regions of Ghana'
    }
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* ============ HEADER NAVIGATION ============ */}
      <header className="sticky top-0 z-50 bg-white border-b border-gray-100 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-lg shadow-emerald-200">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <div>
                <span className="text-xl font-bold text-gray-900 tracking-tight">
                  Yacco EMR
                </span>
                <span className="hidden sm:block text-xs text-gray-500">Ghana Healthcare Network</span>
              </div>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-sm font-medium text-gray-600 hover:text-emerald-600 transition-colors">
                Features
              </a>
              <a href="#regions" className="text-sm font-medium text-gray-600 hover:text-emerald-600 transition-colors">
                Regions
              </a>
              <a href="#help" className="text-sm font-medium text-gray-600 hover:text-emerald-600 transition-colors">
                Help
              </a>
              <Button 
                variant="ghost" 
                className="text-sm font-medium text-gray-600 hover:text-emerald-600"
                onClick={() => navigate('/login')}
              >
                Access Records
              </Button>
              <Button 
                className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg shadow-emerald-200"
                onClick={() => navigate('/login')}
              >
                <LogIn className="w-4 h-4 mr-2" />
                Provider Login
              </Button>
            </nav>

            {/* Mobile Menu Toggle */}
            <button 
              className="md:hidden p-2"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>

          {/* Mobile Navigation */}
          {mobileMenuOpen && (
            <div className="md:hidden py-4 border-t border-gray-100">
              <nav className="flex flex-col gap-4">
                <a href="#features" className="text-sm font-medium text-gray-600 hover:text-emerald-600">
                  Features
                </a>
                <a href="#regions" className="text-sm font-medium text-gray-600 hover:text-emerald-600">
                  Regions
                </a>
                <a href="#help" className="text-sm font-medium text-gray-600 hover:text-emerald-600">
                  Help
                </a>
                <Button 
                  variant="outline"
                  className="w-full justify-center"
                  onClick={() => navigate('/login')}
                >
                  Access Records
                </Button>
                <Button 
                  className="w-full bg-emerald-600 hover:bg-emerald-700"
                  onClick={() => navigate('/login')}
                >
                  <LogIn className="w-4 h-4 mr-2" />
                  Provider Login
                </Button>
              </nav>
            </div>
          )}
        </div>
      </header>

      {/* ============ HERO SECTION ============ */}
      <section className="relative py-20 overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 bg-gradient-to-br from-emerald-50 via-white to-teal-50" />
        <div className="absolute inset-0 opacity-30">
          <div className="absolute top-20 left-10 w-72 h-72 bg-emerald-200 rounded-full blur-3xl" />
          <div className="absolute bottom-10 right-10 w-96 h-96 bg-teal-200 rounded-full blur-3xl" />
        </div>
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            <Badge className="mb-4 bg-emerald-100 text-emerald-700 border-emerald-200">
              🇬🇭 Ghana Health Service Certified
            </Badge>
            
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 mb-6 leading-tight">
              Connect to Your
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-600 to-teal-600">
                {' '}Healthcare Provider
              </span>
            </h1>
            
            <p className="text-lg sm:text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              Log in or sign up to access your medical records with your healthcare provider in Ghana. 
              Secure, connected, and designed for Ghana's healthcare system.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button 
                size="lg"
                className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-xl shadow-emerald-200 text-lg px-8"
                onClick={handleProceedToLogin}
              >
                <LogIn className="w-5 h-5 mr-2" />
                Log In
              </Button>
              <Button 
                size="lg"
                variant="outline"
                className="border-2 border-emerald-600 text-emerald-700 hover:bg-emerald-50 text-lg px-8"
                onClick={handleProceedToSignup}
              >
                <UserPlus className="w-5 h-5 mr-2" />
                Sign Up
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* ============ EMR CENTRAL CARD ============ */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-center">
            <Card className="w-full max-w-md border-2 border-emerald-100 shadow-2xl shadow-emerald-100/50">
              <CardHeader className="text-center pb-2">
                <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-lg shadow-emerald-200">
                  <Heart className="w-10 h-10 text-white" />
                </div>
                <CardTitle className="text-2xl font-bold text-gray-900">EMR Central</CardTitle>
                <CardDescription className="text-gray-500">
                  Your gateway to Ghana's healthcare network
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 pt-4">
                <Button 
                  className="w-full h-14 bg-emerald-600 hover:bg-emerald-700 text-lg shadow-lg"
                  onClick={handleProceedToLogin}
                >
                  <LogIn className="w-5 h-5 mr-3" />
                  Log In
                  <span className="ml-auto text-emerald-200 text-sm">Patients, Clinicians, Admins</span>
                </Button>
                <Button 
                  variant="outline"
                  className="w-full h-14 border-2 text-lg hover:bg-emerald-50"
                  onClick={handleProceedToSignup}
                >
                  <UserPlus className="w-5 h-5 mr-3" />
                  Sign Up
                  <span className="ml-auto text-gray-400 text-sm">Patients, Providers, Facilities</span>
                </Button>
              </CardContent>
              <CardFooter className="flex flex-col gap-2 pt-4 border-t">
                <p className="text-xs text-gray-400 text-center">
                  Secure access to your health records across Ghana's healthcare network
                </p>
                <div className="flex items-center justify-center gap-4 text-xs text-gray-500">
                  <span className="flex items-center gap-1">
                    <Shield className="w-3 h-3" /> Encrypted
                  </span>
                  <span className="flex items-center gap-1">
                    <Lock className="w-3 h-3" /> HIPAA Compliant
                  </span>
                </div>
              </CardFooter>
            </Card>
          </div>
        </div>
      </section>

      {/* ============ FEATURES SECTION ============ */}
      <section id="features" className="py-20 bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              Built for Ghana's Healthcare
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              A modern EMR platform designed to connect health facilities across all regions of Ghana
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, idx) => (
              <Card key={idx} className="border-0 shadow-lg hover:shadow-xl transition-shadow bg-white">
                <CardContent className="pt-8 pb-6 text-center">
                  <div className="w-14 h-14 mx-auto mb-4 rounded-xl bg-emerald-100 flex items-center justify-center">
                    <feature.icon className="w-7 h-7 text-emerald-600" />
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2">{feature.title}</h3>
                  <p className="text-sm text-gray-500">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* ============ GHANA REGIONS SELECTION ============ */}
      <section id="regions" className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <Badge className="mb-4 bg-teal-100 text-teal-700 border-teal-200">
              <MapPin className="w-3 h-3 mr-1" />
              16 Administrative Regions
            </Badge>
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              Select Your Region
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Choose the region where your health facility is located to find your healthcare provider
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {regions.map((region) => (
              <button
                key={region.id}
                onClick={() => handleRegionSelect(region)}
                className={`p-4 rounded-xl border-2 text-left transition-all hover:shadow-lg
                  ${selectedRegion?.id === region.id 
                    ? 'border-emerald-500 bg-emerald-50 shadow-lg shadow-emerald-100' 
                    : 'border-gray-100 bg-white hover:border-emerald-200 hover:bg-emerald-50/50'
                  }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className={`font-semibold ${selectedRegion?.id === region.id ? 'text-emerald-700' : 'text-gray-900'}`}>
                      {region.name}
                    </h3>
                    <p className="text-xs text-gray-500 mt-1">Capital: {region.capital}</p>
                  </div>
                  {selectedRegion?.id === region.id && (
                    <CheckCircle className="w-5 h-5 text-emerald-600" />
                  )}
                </div>
                <div className="flex items-center gap-1 mt-2 text-xs text-gray-400">
                  <Building2 className="w-3 h-3" />
                  <span>{regionHospitalCounts[region.id] || 0} facilities</span>
                </div>
              </button>
            ))}
          </div>

          {selectedRegion && (
            <div className="mt-8 text-center">
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-100 rounded-full text-emerald-700 mb-4">
                <CheckCircle className="w-4 h-4" />
                <span className="font-medium">Selected: {selectedRegion.name} Region</span>
              </div>
              <div className="flex justify-center gap-4">
                <Button 
                  size="lg"
                  className="bg-emerald-600 hover:bg-emerald-700"
                  onClick={handleProceedToLogin}
                >
                  Find My Provider
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* ============ FACILITY TYPES ============ */}
      <section className="py-16 bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-4">
              Supported Health Facilities
            </h2>
            <p className="text-gray-600">
              Connecting all levels of Ghana's healthcare system
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { name: 'Teaching Hospital', icon: Hospital, desc: 'University-affiliated medical centers' },
              { name: 'Regional Hospital', icon: Building2, desc: 'Regional healthcare hubs' },
              { name: 'District Hospital', icon: Landmark, desc: 'District-level care facilities' },
              { name: 'CHPS Compound', icon: Heart, desc: 'Community health posts' },
            ].map((facility, idx) => (
              <Card key={idx} className="border border-gray-100 hover:border-emerald-200 transition-colors">
                <CardContent className="pt-6 text-center">
                  <div className="w-12 h-12 mx-auto mb-3 rounded-lg bg-teal-100 flex items-center justify-center">
                    <facility.icon className="w-6 h-6 text-teal-600" />
                  </div>
                  <h3 className="font-semibold text-gray-900">{facility.name}</h3>
                  <p className="text-xs text-gray-500 mt-1">{facility.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* ============ HELP SECTION ============ */}
      <section id="help" className="py-16 bg-emerald-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <HelpCircle className="w-12 h-12 mx-auto mb-4 text-emerald-600" />
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Need Help?</h2>
          <p className="text-gray-600 mb-6">
            Contact your local health facility administrator or reach out to our support team
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button variant="outline" className="gap-2">
              <Phone className="w-4 h-4" />
              +233 30 123 4567
            </Button>
            <Button variant="outline" className="gap-2">
              <Mail className="w-4 h-4" />
              support@yacco-emr.gh
            </Button>
          </div>
        </div>
      </section>

      {/* ============ FOOTER ============ */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            {/* Brand */}
            <div className="md:col-span-2">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-emerald-500 flex items-center justify-center">
                  <Activity className="w-5 h-5" />
                </div>
                <span className="text-xl font-bold">Yacco EMR</span>
              </div>
              <p className="text-gray-400 text-sm max-w-md">
                Ghana's integrated electronic medical records system, connecting healthcare 
                providers across all 16 administrative regions for better patient care.
              </p>
              <div className="flex items-center gap-2 mt-4">
                <Badge className="bg-emerald-900 text-emerald-300 border-emerald-700">
                  <Globe className="w-3 h-3 mr-1" />
                  Ghana Health Service Certified
                </Badge>
              </div>
            </div>

            {/* Quick Links */}
            <div>
              <h4 className="font-semibold mb-4">Quick Links</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><Link to="/login" className="hover:text-white transition-colors">Provider Login</Link></li>
                <li><Link to="/signup" className="hover:text-white transition-colors">Register Facility</Link></li>
                <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
                <li><a href="#regions" className="hover:text-white transition-colors">Find by Region</a></li>
              </ul>
            </div>

            {/* Legal */}
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">About</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Contact Support</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Privacy Policy</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Terms of Use</a></li>
              </ul>
            </div>
          </div>

          <Separator className="my-8 bg-gray-800" />

          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-sm text-gray-500">
              © 2025 Yacco EMR. All rights reserved.
            </p>
            <div className="flex items-center gap-4">
              <span className="text-xs text-gray-500">Coming Soon:</span>
              <div className="flex gap-2">
                <Badge variant="outline" className="text-gray-400 border-gray-700">
                  <Smartphone className="w-3 h-3 mr-1" />
                  iOS
                </Badge>
                <Badge variant="outline" className="text-gray-400 border-gray-700">
                  <Smartphone className="w-3 h-3 mr-1" />
                  Android
                </Badge>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
