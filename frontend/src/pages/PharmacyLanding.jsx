import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog, DialogContent, DialogDescription,
  DialogHeader, DialogTitle, DialogFooter
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import {
  Select, SelectContent, SelectItem,
  SelectTrigger, SelectValue
} from '@/components/ui/select';
import { toast } from 'sonner';
import {
  Pill, Search, MapPin, Building2, Clock, Phone, Mail,
  LogIn, UserPlus, ChevronRight, Shield, Loader2,
  Hospital, Store, Truck, CheckCircle, Globe, FileText
} from 'lucide-react';
import api from '@/lib/api';

const API_BASE = process.env.REACT_APP_BACKEND_URL || '';

// Ghana Regions with descriptions
const GHANA_REGIONS = [
  { name: 'Greater Accra', capital: 'Accra', description: 'Capital region' },
  { name: 'Ashanti', capital: 'Kumasi', description: 'Second largest region' },
  { name: 'Central', capital: 'Cape Coast', description: 'Historic coastal region' },
  { name: 'Eastern', capital: 'Koforidua', description: 'Agricultural hub' },
  { name: 'Western', capital: 'Sekondi-Takoradi', description: 'Oil & Gas region' },
  { name: 'Western North', capital: 'Sefwi Wiawso', description: 'Cocoa producing region' },
  { name: 'Volta', capital: 'Ho', description: 'Tourism hub' },
  { name: 'Oti', capital: 'Dambai', description: 'Newest region' },
  { name: 'Northern', capital: 'Tamale', description: 'Largest by area' },
  { name: 'Savannah', capital: 'Damongo', description: 'Wildlife region' },
  { name: 'North East', capital: 'Nalerigu', description: 'Northern region' },
  { name: 'Upper East', capital: 'Bolgatanga', description: 'Border region' },
  { name: 'Upper West', capital: 'Wa', description: 'Northwest Ghana' },
  { name: 'Bono', capital: 'Sunyani', description: 'Clean city region' },
  { name: 'Bono East', capital: 'Techiman', description: 'Market hub' },
  { name: 'Ahafo', capital: 'Goaso', description: 'Forest region' },
];

// Pharmacy API
const pharmacyAPI = {
  getRegions: () => api.get('/pharmacy-portal/public/regions'),
  searchPharmacies: (params) => api.get('/pharmacy-portal/public/pharmacies', { params }),
  getPharmacy: (id) => api.get(`/pharmacy-portal/public/pharmacies/${id}`),
  register: (data) => api.post('/pharmacy-portal/register', data),
  login: (data) => api.post('/pharmacy-portal/auth/login', data),
};

// Region Card Component
function RegionCard({ region, count, onClick, selected }) {
  return (
    <Card 
      className={`cursor-pointer transition-all hover:shadow-lg hover:border-blue-300 ${
        selected ? 'ring-2 ring-blue-500 bg-blue-50' : ''
      }`}
      onClick={onClick}
      data-testid={`region-card-${region.name.toLowerCase().replace(/ /g, '-')}`}
    >
      <CardContent className="pt-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-slate-800">{region.name}</h3>
            <p className="text-xs text-slate-500">{region.capital}</p>
          </div>
          <Badge variant="secondary" className="bg-blue-100 text-blue-700">
            {count} pharmacies
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}

// Pharmacy Card Component
function PharmacyCard({ pharmacy, onClick }) {
  return (
    <Card 
      className="cursor-pointer hover:shadow-lg transition-all hover:border-green-300"
      onClick={onClick}
      data-testid={`pharmacy-card-${pharmacy.id}`}
    >
      <CardContent className="pt-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="font-semibold text-slate-800">{pharmacy.name}</h3>
            <div className="flex items-center gap-2 mt-1 text-sm text-slate-500">
              <MapPin className="w-3 h-3" />
              <span>{pharmacy.city || pharmacy.town}, {pharmacy.region}</span>
            </div>
            {pharmacy.phone && (
              <div className="flex items-center gap-2 mt-1 text-sm text-slate-500">
                <Phone className="w-3 h-3" />
                <span>{pharmacy.phone}</span>
              </div>
            )}
          </div>
          <div className="text-right">
            <Badge className={`${
              pharmacy.ownership_type === 'ghs' ? 'bg-green-100 text-green-700' :
              pharmacy.ownership_type === 'retail' ? 'bg-blue-100 text-blue-700' :
              pharmacy.ownership_type === 'chain' ? 'bg-purple-100 text-purple-700' :
              'bg-gray-100 text-gray-700'
            }`}>
              {pharmacy.ownership_type?.replace(/_/g, ' ').toUpperCase() || 'PHARMACY'}
            </Badge>
            <div className="flex gap-1 mt-2 justify-end">
              {pharmacy.has_nhis && (
                <Badge variant="outline" className="text-xs text-green-600">NHIS</Badge>
              )}
              {pharmacy.has_24hr_service && (
                <Badge variant="outline" className="text-xs text-blue-600">24/7</Badge>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Login Dialog Component
function LoginDialog({ open, onOpenChange, onSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await pharmacyAPI.login({ email, password });
      localStorage.setItem('pharmacy_token', response.data.token);
      localStorage.setItem('pharmacy_user', JSON.stringify(response.data.user));
      localStorage.setItem('pharmacy_info', JSON.stringify(response.data.pharmacy));
      toast.success(`Welcome back, ${response.data.user.first_name}!`);
      onSuccess(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <LogIn className="w-5 h-5 text-blue-600" />
            Pharmacy Login
          </DialogTitle>
          <DialogDescription>
            Sign in to access your pharmacy dashboard
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleLogin} className="space-y-4">
          <div className="space-y-2">
            <Label>Email</Label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="pharmacy@example.com"
              required
            />
          </div>
          <div className="space-y-2">
            <Label>Password</Label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <LogIn className="w-4 h-4 mr-2" />}
            Sign In
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// Registration Dialog Component
function RegistrationDialog({ open, onOpenChange, onSuccess }) {
  const [formData, setFormData] = useState({
    pharmacy_name: '',
    license_number: '',
    region: '',
    district: '',
    town: '',
    address: '',
    gps_address: '',
    phone: '',
    email: '',
    superintendent_pharmacist_name: '',
    superintendent_license_number: '',
    ownership_type: 'retail',
    operating_hours: 'Mon-Sat 8AM-8PM',
    password: '',
    confirm_password: '',
    has_nhis_accreditation: false,
  });
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1);

  const updateField = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.password !== formData.confirm_password) {
      toast.error('Passwords do not match');
      return;
    }
    
    setLoading(true);
    try {
      const response = await pharmacyAPI.register(formData);
      toast.success('Registration submitted! Awaiting approval.');
      onSuccess(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-green-600" />
            Pharmacy Registration
          </DialogTitle>
          <DialogDescription>
            Register your pharmacy to join the national pharmacy network
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit}>
          {/* Step Indicators */}
          <div className="flex items-center justify-center gap-4 mb-6">
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step === s ? 'bg-blue-600 text-white' :
                  step > s ? 'bg-green-500 text-white' :
                  'bg-gray-200 text-gray-500'
                }`}
              >
                {step > s ? <CheckCircle className="w-4 h-4" /> : s}
              </div>
            ))}
          </div>

          {/* Step 1: Basic Info */}
          {step === 1 && (
            <div className="space-y-4">
              <h3 className="font-semibold text-slate-700">Basic Information</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Pharmacy Name *</Label>
                  <Input
                    value={formData.pharmacy_name}
                    onChange={(e) => updateField('pharmacy_name', e.target.value)}
                    placeholder="ABC Pharmacy"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>License Number *</Label>
                  <Input
                    value={formData.license_number}
                    onChange={(e) => updateField('license_number', e.target.value)}
                    placeholder="PCGH/001234"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Region *</Label>
                  <Select value={formData.region} onValueChange={(v) => updateField('region', v)}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select region" />
                    </SelectTrigger>
                    <SelectContent>
                      {GHANA_REGIONS.map((r) => (
                        <SelectItem key={r.name} value={r.name}>{r.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>District *</Label>
                  <Input
                    value={formData.district}
                    onChange={(e) => updateField('district', e.target.value)}
                    placeholder="Accra Metropolitan"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Town/City *</Label>
                  <Input
                    value={formData.town}
                    onChange={(e) => updateField('town', e.target.value)}
                    placeholder="Accra"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Ownership Type</Label>
                  <Select value={formData.ownership_type} onValueChange={(v) => updateField('ownership_type', v)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="retail">Retail/Community</SelectItem>
                      <SelectItem value="private_hospital">Hospital Pharmacy</SelectItem>
                      <SelectItem value="chain">Pharmacy Chain</SelectItem>
                      <SelectItem value="wholesale">Wholesale</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <Button type="button" onClick={() => setStep(2)} className="w-full">
                Next <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          )}

          {/* Step 2: Contact & Location */}
          {step === 2 && (
            <div className="space-y-4">
              <h3 className="font-semibold text-slate-700">Contact & Location</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2 space-y-2">
                  <Label>Address *</Label>
                  <Input
                    value={formData.address}
                    onChange={(e) => updateField('address', e.target.value)}
                    placeholder="123 Main Street"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>GPS Address</Label>
                  <Input
                    value={formData.gps_address}
                    onChange={(e) => updateField('gps_address', e.target.value)}
                    placeholder="GA-123-4567"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Operating Hours</Label>
                  <Input
                    value={formData.operating_hours}
                    onChange={(e) => updateField('operating_hours', e.target.value)}
                    placeholder="Mon-Sat 8AM-8PM"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Phone *</Label>
                  <Input
                    value={formData.phone}
                    onChange={(e) => updateField('phone', e.target.value)}
                    placeholder="+233 XX XXX XXXX"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Email *</Label>
                  <Input
                    type="email"
                    value={formData.email}
                    onChange={(e) => updateField('email', e.target.value)}
                    placeholder="pharmacy@example.com"
                    required
                  />
                </div>
                <div className="col-span-2">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.has_nhis_accreditation}
                      onChange={(e) => updateField('has_nhis_accreditation', e.target.checked)}
                      className="rounded"
                    />
                    <span>NHIS Accredited Pharmacy</span>
                  </label>
                </div>
              </div>
              <div className="flex gap-4">
                <Button type="button" variant="outline" onClick={() => setStep(1)} className="flex-1">
                  Back
                </Button>
                <Button type="button" onClick={() => setStep(3)} className="flex-1">
                  Next <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>
          )}

          {/* Step 3: Superintendent & Credentials */}
          {step === 3 && (
            <div className="space-y-4">
              <h3 className="font-semibold text-slate-700">Superintendent Pharmacist & Login</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Superintendent Pharmacist Name *</Label>
                  <Input
                    value={formData.superintendent_pharmacist_name}
                    onChange={(e) => updateField('superintendent_pharmacist_name', e.target.value)}
                    placeholder="Dr. John Doe"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Superintendent License # *</Label>
                  <Input
                    value={formData.superintendent_license_number}
                    onChange={(e) => updateField('superintendent_license_number', e.target.value)}
                    placeholder="PSGH/12345"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Password *</Label>
                  <Input
                    type="password"
                    value={formData.password}
                    onChange={(e) => updateField('password', e.target.value)}
                    placeholder="••••••••"
                    required
                    minLength={6}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Confirm Password *</Label>
                  <Input
                    type="password"
                    value={formData.confirm_password}
                    onChange={(e) => updateField('confirm_password', e.target.value)}
                    placeholder="••••••••"
                    required
                  />
                </div>
              </div>
              <div className="bg-blue-50 p-4 rounded-lg text-sm text-blue-700">
                <Shield className="w-4 h-4 inline mr-2" />
                Your registration will be reviewed by our team. You will receive an email once approved.
              </div>
              <div className="flex gap-4">
                <Button type="button" variant="outline" onClick={() => setStep(2)} className="flex-1">
                  Back
                </Button>
                <Button type="submit" disabled={loading} className="flex-1 bg-green-600 hover:bg-green-700">
                  {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <UserPlus className="w-4 h-4 mr-2" />}
                  Submit Registration
                </Button>
              </div>
            </div>
          )}
        </form>
      </DialogContent>
    </Dialog>
  );
}

// Main Pharmacy Landing Page Component
export default function PharmacyLanding() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [regionsData, setRegionsData] = useState([]);
  const [selectedRegion, setSelectedRegion] = useState(null);
  const [pharmacies, setPharmacies] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [showLogin, setShowLogin] = useState(false);
  const [showRegister, setShowRegister] = useState(false);
  const [totalPharmacies, setTotalPharmacies] = useState(0);

  // Fetch regions with pharmacy counts
  useEffect(() => {
    const fetchRegions = async () => {
      try {
        const response = await pharmacyAPI.getRegions();
        setRegionsData(response.data.regions || []);
        setTotalPharmacies(response.data.total_pharmacies || 0);
      } catch (error) {
        console.error('Failed to fetch regions:', error);
        // Use static data as fallback
        setRegionsData(GHANA_REGIONS.map(r => ({ ...r, region: r.name, pharmacy_count: 0 })));
      } finally {
        setLoading(false);
      }
    };
    fetchRegions();
  }, []);

  // Fetch pharmacies when region selected or search
  useEffect(() => {
    const fetchPharmacies = async () => {
      setLoading(true);
      try {
        const params = {};
        if (selectedRegion) params.region = selectedRegion;
        if (searchQuery) params.search = searchQuery;
        
        const response = await pharmacyAPI.searchPharmacies(params);
        setPharmacies(response.data.pharmacies || []);
      } catch (error) {
        console.error('Failed to fetch pharmacies:', error);
      } finally {
        setLoading(false);
      }
    };
    
    if (selectedRegion || searchQuery) {
      fetchPharmacies();
    } else {
      setPharmacies([]);
    }
  }, [selectedRegion, searchQuery]);

  // Handle successful login
  const handleLoginSuccess = (data) => {
    setShowLogin(false);
    navigate('/pharmacy/dashboard');
  };

  // Handle successful registration
  const handleRegisterSuccess = (data) => {
    setShowRegister(false);
    toast.info('Registration submitted. Please wait for approval before logging in.');
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-50 to-white" data-testid="pharmacy-landing">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-emerald-600 to-emerald-700 rounded-xl flex items-center justify-center">
                <Pill className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-800">Yacco Pharm</h1>
                <p className="text-xs text-slate-500">Ghana National Pharmacy Network</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="outline" onClick={() => setShowLogin(true)}>
                <LogIn className="w-4 h-4 mr-2" />
                Pharmacy Login
              </Button>
              <Button className="bg-emerald-600 hover:bg-emerald-700" onClick={() => setShowRegister(true)}>
                <UserPlus className="w-4 h-4 mr-2" />
                Register Pharmacy
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-12 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <h2 className="text-4xl font-bold text-slate-900 mb-4">
            Connect to Pharmacy Services
          </h2>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto mb-8">
            Access licensed pharmacies across Ghana for medication dispensing and supply coordination.
            Find pharmacies by region, check availability, and connect with healthcare providers.
          </p>
          
          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto mb-8">
            <Card>
              <CardContent className="pt-6">
                <div className="text-3xl font-bold text-blue-600">{totalPharmacies}+</div>
                <div className="text-sm text-slate-500">Registered Pharmacies</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-3xl font-bold text-green-600">16</div>
                <div className="text-sm text-slate-500">Regions Covered</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-3xl font-bold text-purple-600">24/7</div>
                <div className="text-sm text-slate-500">Emergency Services</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-3xl font-bold text-orange-600">NHIS</div>
                <div className="text-sm text-slate-500">Insurance Supported</div>
              </CardContent>
            </Card>
          </div>

          {/* Search Bar */}
          <div className="max-w-2xl mx-auto">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search pharmacies by name, location, or license number..."
                className="pl-12 h-14 text-lg rounded-xl shadow-lg"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <section className="py-8 px-4">
        <div className="max-w-7xl mx-auto">
          <Tabs defaultValue="regions" className="w-full">
            <TabsList className="grid w-full max-w-md mx-auto grid-cols-2 mb-8">
              <TabsTrigger value="regions" className="gap-2">
                <Globe className="w-4 h-4" /> Browse by Region
              </TabsTrigger>
              <TabsTrigger value="results" className="gap-2">
                <Store className="w-4 h-4" /> Search Results
              </TabsTrigger>
            </TabsList>

            {/* Regions Tab */}
            <TabsContent value="regions">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {GHANA_REGIONS.map((region) => {
                  const regionData = regionsData.find(r => r.region === region.name);
                  return (
                    <RegionCard
                      key={region.name}
                      region={region}
                      count={regionData?.pharmacy_count || 0}
                      selected={selectedRegion === region.name}
                      onClick={() => setSelectedRegion(
                        selectedRegion === region.name ? null : region.name
                      )}
                    />
                  );
                })}
              </div>
            </TabsContent>

            {/* Results Tab */}
            <TabsContent value="results">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
                </div>
              ) : pharmacies.length === 0 ? (
                <div className="text-center py-12 text-slate-500">
                  <Store className="w-16 h-16 mx-auto mb-4 text-slate-300" />
                  <p>Select a region or search to view pharmacies</p>
                </div>
              ) : (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {pharmacies.map((pharmacy) => (
                    <PharmacyCard
                      key={pharmacy.id}
                      pharmacy={pharmacy}
                      onClick={() => navigate(`/pharmacy/${pharmacy.id}`)}
                    />
                  ))}
                </div>
              )}
            </TabsContent>
          </Tabs>

          {/* Selected Region Pharmacies */}
          {selectedRegion && pharmacies.length > 0 && (
            <div className="mt-8">
              <h3 className="text-xl font-semibold text-slate-800 mb-4">
                Pharmacies in {selectedRegion} ({pharmacies.length})
              </h3>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {pharmacies.map((pharmacy) => (
                  <PharmacyCard
                    key={pharmacy.id}
                    pharmacy={pharmacy}
                    onClick={() => navigate(`/pharmacy/${pharmacy.id}`)}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Features Section */}
      <section className="py-12 px-4 bg-slate-50">
        <div className="max-w-7xl mx-auto">
          <h3 className="text-2xl font-bold text-center text-slate-800 mb-8">
            Pharmacy Portal Features
          </h3>
          <div className="grid md:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-blue-600" />
                  e-Prescription Receiving
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-slate-600 text-sm">
                  Receive electronic prescriptions directly from physicians and hospitals.
                  Streamline your dispensing workflow.
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="w-5 h-5 text-green-600" />
                  NHIS Claims Processing
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-slate-600 text-sm">
                  Submit insurance claims directly through the platform.
                  Support for NHIS and private insurers.
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Truck className="w-5 h-5 text-purple-600" />
                  Inventory Management
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-slate-600 text-sm">
                  Track stock levels, manage expiry dates, and automate reorder alerts.
                  Never run out of essential medications.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 bg-slate-800 text-white">
        <div className="max-w-7xl mx-auto text-center">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Pill className="w-6 h-6" />
            <span className="font-semibold">Ghana Pharmacy Network</span>
          </div>
          <p className="text-slate-400 text-sm">
            Part of the National Healthcare Information System
          </p>
          <p className="text-slate-500 text-xs mt-2">
            © 2026 Ministry of Health, Ghana. All rights reserved.
          </p>
        </div>
      </footer>

      {/* Dialogs */}
      <LoginDialog
        open={showLogin}
        onOpenChange={setShowLogin}
        onSuccess={handleLoginSuccess}
      />
      <RegistrationDialog
        open={showRegister}
        onOpenChange={setShowRegister}
        onSuccess={handleRegisterSuccess}
      />
    </div>
  );
}
