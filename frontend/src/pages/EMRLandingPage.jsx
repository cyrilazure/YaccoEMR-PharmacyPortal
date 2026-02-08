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
  Activity, MapPin, Building2, Users, LogIn,
  Heart, Shield, Phone, Mail, Globe, ChevronRight,
  Stethoscope, FileText, Calendar, Smartphone, Lock,
  CheckCircle, Star, ArrowRight, Clock, HelpCircle,
  Loader2, Hospital, Landmark, Menu, X, KeyRound, Pill, Store
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
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [regionHospitalCounts, setRegionHospitalCounts] = useState({});

  // Redirect if already logged in
  useEffect(() => {
    if (user) {
      const redirects = {
        'super_admin': '/platform/super-admin',
        'hospital_admin': '/admin-dashboard',
        'hospital_it_admin': '/it-admin',
        'facility_admin': '/facility-admin',
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

  const emrFeatures = [
    {
      icon: Shield,
      title: 'Secure & Compliant',
      description: 'HIPAA-aligned security with full audit trails'
    },
    {
      icon: Hospital,
      title: 'Multi-Facility',
      description: 'Regional Hospitals to CHPS Compounds'
    },
    {
      icon: Users,
      title: 'Role-Based Access',
      description: 'Physicians, Nurses, Schedulers, Admins'
    },
    {
      icon: Stethoscope,
      title: 'Clinical Tools',
      description: 'AI documentation, FHIR, Telehealth'
    }
  ];

  const pharmacyFeatures = [
    {
      icon: FileText,
      title: 'e-Prescription',
      description: 'Receive prescriptions from hospitals'
    },
    {
      icon: Shield,
      title: 'NHIS Claims',
      description: 'Direct insurance claim processing'
    },
    {
      icon: Store,
      title: 'Inventory',
      description: 'Stock tracking & expiry alerts'
    },
    {
      icon: Globe,
      title: 'Nationwide',
      description: 'Connect across all 16 regions'
    }
  ];

  return (
    <div className="min-h-screen bg-slate-50" data-testid="unified-landing-page">
      {/* ============ HEADER NAVIGATION ============ */}
      <header className="sticky top-0 z-50 bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-600 to-emerald-700 flex items-center justify-center shadow-lg">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <div>
                <span className="text-xl font-bold text-emerald-700 tracking-tight">
                  Yacco Health
                </span>
                <span className="hidden sm:block text-xs text-slate-500">Ghana Healthcare Network</span>
              </div>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-6">
              <a href="#portals" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">
                Portals
              </a>
              <a href="#regions" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">
                Regions
              </a>
              <a href="#help" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">
                Help
              </a>
            </nav>

            {/* Mobile Menu Toggle */}
            <button 
              className="md:hidden p-2"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              data-testid="mobile-menu-toggle"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>

          {/* Mobile Navigation */}
          {mobileMenuOpen && (
            <div className="md:hidden py-4 border-t border-slate-100">
              <nav className="flex flex-col gap-4">
                <a href="#portals" className="text-sm font-medium text-slate-600 hover:text-slate-900">
                  Portals
                </a>
                <a href="#regions" className="text-sm font-medium text-slate-600 hover:text-slate-900">
                  Regions
                </a>
                <a href="#help" className="text-sm font-medium text-slate-600 hover:text-slate-900">
                  Help
                </a>
              </nav>
            </div>
          )}
        </div>
      </header>

      {/* ============ HERO SECTION ============ */}
      <section className="relative py-16 md:py-24 overflow-hidden">
        {/* Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-slate-100 via-white to-slate-50" />
        <div className="absolute inset-0 opacity-30">
          <div className="absolute top-20 left-10 w-72 h-72 bg-emerald-100 rounded-full blur-3xl" />
          <div className="absolute bottom-10 right-10 w-96 h-96 bg-emerald-100 rounded-full blur-3xl" />
        </div>
        
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-12">
            <Badge className="mb-4 bg-slate-100 text-slate-700 border-slate-200">
              Ghana Health Service Certified
            </Badge>
            
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold mb-6 leading-tight">
              <span className="text-emerald-600">Ghana's Integrated</span>
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-emerald-600 to-blue-600">
                Healthcare Platform
              </span>
            </h1>
            
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Connecting hospitals and pharmacies across all 16 administrative regions. 
              Choose your portal below to get started.
            </p>
          </div>

          {/* ============ TWO PORTAL CARDS ============ */}
          <div id="portals" className="grid md:grid-cols-2 gap-6 lg:gap-8 max-w-5xl mx-auto">
            
            {/* Yacco EMR Portal Card */}
            <Card 
              className="relative overflow-hidden border-2 border-slate-200 hover:border-emerald-400 transition-all duration-300 hover:shadow-2xl group cursor-pointer"
              onClick={() => navigate('/login')}
              data-testid="emr-portal-card"
            >
              <div className="absolute top-0 left-0 right-0 h-2 bg-gradient-to-r from-emerald-500 to-teal-500" />
              <CardHeader className="pt-8 pb-4 text-center">
                <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-xl shadow-emerald-200/50 group-hover:scale-105 transition-transform">
                  <Heart className="w-10 h-10 text-white" />
                </div>
                <CardTitle className="text-2xl font-bold text-slate-900">Yacco EMR</CardTitle>
                <CardDescription className="text-slate-500 text-base">
                  Electronic Medical Records for Hospitals
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-2 pb-6">
                <div className="grid grid-cols-2 gap-3 mb-6">
                  {emrFeatures.map((feature, idx) => (
                    <div key={idx} className="flex items-start gap-2 p-2 rounded-lg bg-emerald-50/50">
                      <feature.icon className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs font-medium text-slate-700">{feature.title}</p>
                        <p className="text-xs text-slate-500">{feature.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
                <Button 
                  className="w-full h-12 bg-emerald-600 hover:bg-emerald-700 text-white text-base font-semibold shadow-lg shadow-emerald-200/50 group-hover:shadow-xl"
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate('/login');
                  }}
                  data-testid="emr-login-btn"
                >
                  <LogIn className="w-5 h-5 mr-2" />
                  Hospital Staff Login
                  <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                </Button>
                <p className="text-center text-xs text-slate-500 mt-3">
                  Physicians, Nurses, Schedulers, Administrators
                </p>
                <Button 
                  variant="link"
                  className="w-full mt-2 text-emerald-600 hover:text-emerald-700"
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate('/register-hospital');
                  }}
                  data-testid="register-hospital-btn"
                >
                  <Hospital className="w-4 h-4 mr-2" />
                  Register Your Hospital
                  <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </CardContent>
            </Card>

            {/* Yacco Pharm Portal Card */}
            <Card 
              className="relative overflow-hidden border-2 border-slate-200 hover:border-blue-400 transition-all duration-300 hover:shadow-2xl group cursor-pointer"
              onClick={() => navigate('/pharmacy')}
              data-testid="pharm-portal-card"
            >
              <div className="absolute top-0 left-0 right-0 h-2 bg-gradient-to-r from-blue-500 to-indigo-500" />
              <CardHeader className="pt-8 pb-4 text-center">
                <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-xl shadow-blue-200/50 group-hover:scale-105 transition-transform">
                  <Pill className="w-10 h-10 text-white" />
                </div>
                <CardTitle className="text-2xl font-bold text-slate-900">Yacco Pharm</CardTitle>
                <CardDescription className="text-slate-500 text-base">
                  National Pharmacy Network Portal
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-2 pb-6">
                <div className="grid grid-cols-2 gap-3 mb-6">
                  {pharmacyFeatures.map((feature, idx) => (
                    <div key={idx} className="flex items-start gap-2 p-2 rounded-lg bg-blue-50/50">
                      <feature.icon className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                      <div>
                        <p className="text-xs font-medium text-slate-700">{feature.title}</p>
                        <p className="text-xs text-slate-500">{feature.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
                <Button 
                  className="w-full h-12 bg-blue-600 hover:bg-blue-700 text-white text-base font-semibold shadow-lg shadow-blue-200/50 group-hover:shadow-xl"
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate('/pharmacy');
                  }}
                  data-testid="pharm-login-btn"
                >
                  <Store className="w-5 h-5 mr-2" />
                  Pharmacy Portal
                  <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                </Button>
                <p className="text-center text-xs text-slate-500 mt-3">
                  Pharmacy Owners, Pharmacists, Dispensers
                </p>
                <Button 
                  variant="link"
                  className="w-full mt-2 text-blue-600 hover:text-blue-700"
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate('/pharmacy');
                  }}
                  data-testid="register-pharmacy-btn"
                >
                  <Pill className="w-4 h-4 mr-2" />
                  Register Your Pharmacy
                  <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* ============ PLATFORM STATS ============ */}
      <section className="py-12 bg-white border-y border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-3xl font-bold text-emerald-600">16</div>
              <div className="text-sm text-slate-500 mt-1">Regions Covered</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-emerald-600">200+</div>
              <div className="text-sm text-slate-500 mt-1">Health Facilities</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-emerald-600">133+</div>
              <div className="text-sm text-slate-500 mt-1">Registered Pharmacies</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-emerald-600">24/7</div>
              <div className="text-sm text-slate-500 mt-1">Emergency Services</div>
            </div>
          </div>
        </div>
      </section>

      {/* ============ GHANA REGIONS ============ */}
      <section id="regions" className="py-16 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <Badge className="mb-4 bg-slate-100 text-slate-700 border-slate-200">
              <MapPin className="w-3 h-3 mr-1" />
              16 Administrative Regions
            </Badge>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 mb-3">
              Nationwide Coverage
            </h2>
            <p className="text-slate-600 max-w-xl mx-auto">
              Healthcare connectivity across all regions of Ghana
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
            {regions.map((region) => (
              <div
                key={region.id}
                className="p-3 rounded-lg border border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm transition-all text-center"
              >
                <h3 className="font-medium text-slate-800 text-sm">
                  {region.name}
                </h3>
                <p className="text-xs text-slate-500">{region.capital}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============ FACILITY TYPES ============ */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 mb-3">
              Supported Facilities
            </h2>
            <p className="text-slate-600">
              Connecting all levels of Ghana's healthcare system
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { name: 'Teaching Hospital', icon: Hospital, desc: 'University-affiliated centers', color: 'emerald' },
              { name: 'Regional Hospital', icon: Building2, desc: 'Regional healthcare hubs', color: 'blue' },
              { name: 'District Hospital', icon: Landmark, desc: 'District-level facilities', color: 'indigo' },
              { name: 'Pharmacies', icon: Pill, desc: 'Community & chain pharmacies', color: 'teal' },
            ].map((facility, idx) => (
              <Card key={idx} className="border border-slate-200 hover:border-slate-300 transition-colors">
                <CardContent className="pt-6 text-center">
                  <div className={`w-12 h-12 mx-auto mb-3 rounded-lg bg-${facility.color}-100 flex items-center justify-center`}>
                    <facility.icon className={`w-6 h-6 text-${facility.color}-600`} />
                  </div>
                  <h3 className="font-semibold text-slate-900">{facility.name}</h3>
                  <p className="text-xs text-slate-500 mt-1">{facility.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* ============ HELP SECTION ============ */}
      <section id="help" className="py-16 bg-gradient-to-br from-slate-100 to-slate-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <HelpCircle className="w-12 h-12 mx-auto mb-4 text-slate-600" />
          <h2 className="text-2xl font-bold text-slate-900 mb-4">Need Help?</h2>
          <p className="text-slate-600 mb-6">
            Contact your local health facility administrator or reach out to our support team
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button variant="outline" className="gap-2 bg-white">
              <Phone className="w-4 h-4" />
              +233 30 123 4567
            </Button>
            <Button variant="outline" className="gap-2 bg-white">
              <Mail className="w-4 h-4" />
              support@yacco.health
            </Button>
          </div>
          
          <div className="mt-8 p-4 bg-white rounded-lg border border-slate-200 max-w-md mx-auto">
            <p className="text-sm text-slate-600">
              <strong>Platform Administrators:</strong>
            </p>
            <Button
              variant="link"
              className="text-slate-600 hover:text-slate-900"
              onClick={() => navigate('/po-login')}
              data-testid="platform-admin-link"
            >
              <KeyRound className="w-4 h-4 mr-2" />
              Platform Admin Access
            </Button>
          </div>
        </div>
      </section>

      {/* ============ FOOTER ============ */}
      <footer className="bg-slate-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-8">
            {/* Brand */}
            <div className="md:col-span-2">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-emerald-600 flex items-center justify-center">
                  <Activity className="w-5 h-5" />
                </div>
                <span className="text-xl font-bold">Yacco Health</span>
              </div>
              <p className="text-slate-400 text-sm max-w-md">
                Ghana's integrated healthcare platform, connecting hospitals and pharmacies 
                across all 16 administrative regions for better patient care.
              </p>
              <div className="flex items-center gap-2 mt-4">
                <Badge className="bg-slate-800 text-slate-300 border-slate-700">
                  <Globe className="w-3 h-3 mr-1" />
                  Ghana Health Service Certified
                </Badge>
              </div>
            </div>

            {/* Portals */}
            <div>
              <h4 className="font-semibold mb-4">Portals</h4>
              <ul className="space-y-2 text-sm text-slate-400">
                <li>
                  <Link to="/login" className="hover:text-white transition-colors flex items-center gap-2">
                    <Heart className="w-3 h-3" /> Yacco EMR
                  </Link>
                </li>
                <li>
                  <Link to="/pharmacy" className="hover:text-white transition-colors flex items-center gap-2">
                    <Pill className="w-3 h-3" /> Yacco Pharm
                  </Link>
                </li>
              </ul>
            </div>

            {/* Legal */}
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <ul className="space-y-2 text-sm text-slate-400">
                <li><a href="#" className="hover:text-white transition-colors">About</a></li>
                <li><a href="#help" className="hover:text-white transition-colors">Contact Support</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Privacy Policy</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Terms of Use</a></li>
              </ul>
            </div>
          </div>

          <Separator className="my-8 bg-slate-800" />

          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-sm text-slate-500">
              © 2026 Yacco Health. All rights reserved.
            </p>
            <div className="flex items-center gap-4">
              <span className="text-xs text-slate-500">Coming Soon:</span>
              <div className="flex gap-2">
                <Badge variant="outline" className="text-slate-400 border-slate-700">
                  <Smartphone className="w-3 h-3 mr-1" />
                  iOS
                </Badge>
                <Badge variant="outline" className="text-slate-400 border-slate-700">
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
