import React, { useState, useEffect } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import { regionAPI } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { 
  Activity, 
  MapPin, 
  Building2, 
  Search, 
  ChevronRight, 
  ChevronLeft,
  Phone,
  Mail,
  Clock,
  Stethoscope,
  Shield,
  Users,
  LogIn,
  Smartphone,
  AlertCircle,
  CheckCircle,
  Loader2,
  Globe
} from 'lucide-react';

// Role to portal mapping
const ROLE_REDIRECTS = {
  'super_admin': '/platform/super-admin',
  'hospital_admin': '/admin-dashboard',
  'hospital_it_admin': '/it-admin',
  'facility_admin': '/facility-admin',
  'admin': '/admin-dashboard',
  'physician': '/dashboard',
  'nurse': '/nurse-station',
  'biller': '/billing',
  'scheduler': '/scheduling'
};

// Steps in the discovery flow
const STEPS = {
  REGION: 1,
  HOSPITAL: 2,
  LOCATION: 3,
  LOGIN: 4
};

export default function RegionHospitalLogin() {
  const { 
    user, 
    login: authLogin,
    requiresOTP,
    requiresPhone,
    otpPhoneMasked,
    cancelOTP,
    // Region-specific methods
    regionLogin,
    submitPhoneForRegion,
    completeRegionOTPLogin
  } = useAuth();
  const navigate = useNavigate();
  
  // Step state
  const [currentStep, setCurrentStep] = useState(STEPS.REGION);
  
  // Data states
  const [regions, setRegions] = useState([]);
  const [hospitals, setHospitals] = useState([]);
  const [locations, setLocations] = useState([]);
  
  // Selection states
  const [selectedRegion, setSelectedRegion] = useState(null);
  const [selectedHospital, setSelectedHospital] = useState(null);
  const [selectedLocation, setSelectedLocation] = useState(null);
  
  // UI states
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [totpCode, setTotpCode] = useState('');
  const [show2FADialog, setShow2FADialog] = useState(false);
  const [pendingLogin, setPendingLogin] = useState(null);
  
  // OTP states
  const [phoneNumber, setPhoneNumber] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [resending, setResending] = useState(false);

  // Load regions on mount
  useEffect(() => {
    loadRegions();
  }, []);

  // Redirect if already logged in
  if (user) {
    return <Navigate to={ROLE_REDIRECTS[user.role] || '/dashboard'} replace />;
  }

  const loadRegions = async () => {
    try {
      setLoading(true);
      const response = await regionAPI.getRegions();
      setRegions(response.data.regions || []);
    } catch (error) {
      toast.error('Failed to load regions');
      console.error('Error loading regions:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadHospitalsByRegion = async (regionId) => {
    try {
      setLoading(true);
      const response = await regionAPI.getHospitalsByRegion(regionId, searchQuery);
      setHospitals(response.data.hospitals || []);
    } catch (error) {
      toast.error('Failed to load hospitals');
      console.error('Error loading hospitals:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadLocations = async (hospitalId) => {
    try {
      setLoading(true);
      const response = await regionAPI.getHospitalLocations(hospitalId);
      setLocations(response.data.locations || []);
    } catch (error) {
      toast.error('Failed to load locations');
      console.error('Error loading locations:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRegionSelect = (region) => {
    setSelectedRegion(region);
    setSelectedHospital(null);
    setSelectedLocation(null);
    loadHospitalsByRegion(region.id);
    setCurrentStep(STEPS.HOSPITAL);
  };

  const handleHospitalSelect = async (hospital) => {
    setSelectedHospital(hospital);
    setSelectedLocation(null);
    
    if (hospital.has_multiple_locations || hospital.location_count > 1) {
      await loadLocations(hospital.id);
      setCurrentStep(STEPS.LOCATION);
    } else {
      // Single location - proceed to login
      if (hospital.location_count === 1) {
        const response = await regionAPI.getHospitalLocations(hospital.id);
        const singleLocation = response.data.locations?.[0];
        setSelectedLocation(singleLocation || null);
      }
      setCurrentStep(STEPS.LOGIN);
    }
  };

  const handleLocationSelect = (location) => {
    setSelectedLocation(location);
    setCurrentStep(STEPS.LOGIN);
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    
    if (!selectedHospital) {
      toast.error('Please select a hospital first');
      return;
    }
    
    setLoading(true);
    try {
      // Use new OTP flow
      const response = await regionAPI.locationLoginInit(
        loginForm.email,
        loginForm.password,
        selectedHospital.id,
        selectedLocation?.id || null
      );
      
      if (response.data.phone_required) {
        // Phone number is required - auth context will handle the dialog
        toast.info('Please enter your phone number for verification');
      } else if (response.data.otp_required) {
        // OTP is required - auth context will handle the dialog
        toast.success('OTP sent to your phone');
      }
      
    } catch (error) {
      if (error.response?.data?.detail === '2FA_REQUIRED') {
        setPendingLogin({ email: loginForm.email, password: loginForm.password });
        setShow2FADialog(true);
        toast.info('Please enter your 2FA code');
      } else {
        toast.error(error.response?.data?.detail || 'Login failed');
      }
    } finally {
      setLoading(false);
    }
  };

  const handlePhoneSubmit = async (e) => {
    e.preventDefault();
    if (phoneNumber.length < 9) {
      toast.error('Please enter a valid phone number');
      return;
    }
    
    setLoading(true);
    try {
      await submitPhoneNumber(phoneNumber);
      toast.success('OTP sent to your phone');
    } catch (err) {
      const detail = err.response?.data?.detail;
      const errorMessage = typeof detail === 'string' ? detail : 'Failed to send OTP';
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleOTPSubmit = async (e) => {
    e.preventDefault();
    if (otpCode.length !== 6) {
      toast.error('Please enter a valid 6-digit OTP');
      return;
    }
    
    setLoading(true);
    try {
      const userData = await completeOTPLogin(otpCode);
      toast.success('Welcome back!');
      const redirectPath = ROLE_REDIRECTS[userData.role] || '/dashboard';
      navigate(redirectPath);
    } catch (err) {
      const detail = err.response?.data?.detail;
      const errorMessage = typeof detail === 'string' ? detail : (err.message || 'Invalid OTP');
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleResendOTP = async () => {
    setResending(true);
    try {
      await resendOTP();
      toast.success('OTP resent successfully');
    } catch (err) {
      toast.error('Failed to resend OTP');
    } finally {
      setResending(false);
    }
  };

  const handleCancelOTP = () => {
    cancelOTP();
    setOtpCode('');
    setPhoneNumber('');
  };

  const handle2FASubmit = async (e) => {
    e.preventDefault();
    
    if (!pendingLogin) return;
    
    setLoading(true);
    try {
      const response = await regionAPI.locationLogin(
        pendingLogin.email,
        pendingLogin.password,
        selectedHospital.id,
        selectedLocation?.id || null,
        totpCode
      );
      
      const { token, user: userData, hospital, location } = response.data;
      
      localStorage.setItem('yacco_token', token);
      localStorage.setItem('yacco_user', JSON.stringify(userData));
      localStorage.setItem('yacco_hospital', JSON.stringify(hospital));
      if (location) {
        localStorage.setItem('yacco_location', JSON.stringify(location));
      }
      
      toast.success(`Welcome to ${hospital.name}!`);
      
      const redirectPath = ROLE_REDIRECTS[userData.role] || '/dashboard';
      window.location.href = redirectPath;
      
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Invalid 2FA code');
    } finally {
      setLoading(false);
      setShow2FADialog(false);
      setPendingLogin(null);
      setTotpCode('');
    }
  };

  const goBack = () => {
    if (currentStep === STEPS.HOSPITAL) {
      setCurrentStep(STEPS.REGION);
      setSelectedRegion(null);
      setHospitals([]);
    } else if (currentStep === STEPS.LOCATION) {
      setCurrentStep(STEPS.HOSPITAL);
      setSelectedHospital(null);
      setLocations([]);
    } else if (currentStep === STEPS.LOGIN) {
      if (selectedHospital?.has_multiple_locations) {
        setCurrentStep(STEPS.LOCATION);
      } else {
        setCurrentStep(STEPS.HOSPITAL);
        setSelectedHospital(null);
      }
    }
  };

  const filteredHospitals = hospitals.filter(h => 
    !searchQuery || 
    h.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    h.city?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen flex" data-testid="region-login-page">
      {/* Left Side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
        <div 
          className="absolute inset-0 bg-cover bg-center"
          style={{ 
            backgroundImage: 'url(https://images.unsplash.com/photo-1538108149393-fbbd81895907?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzZ8MHwxfHNlYXJjaHwxfHxhZnJpY2FuJTIwaG9zcGl0YWwlMjBoZWFsdGhjYXJlfGVufDB8fHx8MTcwMDA3Njk2OHww&ixlib=rb-4.1.0&q=85)'
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-br from-emerald-900/90 via-emerald-800/85 to-teal-900/80" />
        <div className="relative z-10 flex flex-col justify-between p-12 text-white">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-12 h-12 rounded-xl bg-emerald-500 flex items-center justify-center">
                <Activity className="w-7 h-7" />
              </div>
              <span className="text-3xl font-bold tracking-tight">Yacco EMR</span>
            </div>
            <p className="text-emerald-200 text-lg">Ghana Healthcare Network</p>
          </div>
          
          <div className="space-y-8">
            <div>
              <h1 className="text-4xl font-bold mb-4 leading-tight">
                Connecting Ghana's<br />Healthcare System
              </h1>
              <p className="text-emerald-100 text-lg max-w-md">
                Access your hospital's electronic medical records from any location across Ghana's 16 regions.
              </p>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-3 bg-white/10 rounded-lg p-3">
                <MapPin className="w-5 h-5 text-emerald-300" />
                <div>
                  <div className="font-semibold">16 Regions</div>
                  <div className="text-sm text-emerald-200">Nationwide Coverage</div>
                </div>
              </div>
              <div className="flex items-center gap-3 bg-white/10 rounded-lg p-3">
                <Building2 className="w-5 h-5 text-emerald-300" />
                <div>
                  <div className="font-semibold">Multi-Location</div>
                  <div className="text-sm text-emerald-200">Hospital Branches</div>
                </div>
              </div>
              <div className="flex items-center gap-3 bg-white/10 rounded-lg p-3">
                <Shield className="w-5 h-5 text-emerald-300" />
                <div>
                  <div className="font-semibold">Secure Access</div>
                  <div className="text-sm text-emerald-200">Data Isolation</div>
                </div>
              </div>
              <div className="flex items-center gap-3 bg-white/10 rounded-lg p-3">
                <Users className="w-5 h-5 text-emerald-300" />
                <div>
                  <div className="font-semibold">Role-Based</div>
                  <div className="text-sm text-emerald-200">Personalized Portals</div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="text-sm text-emerald-200">
            <p>© 2025 Yacco EMR. All rights reserved.</p>
            <p className="flex items-center gap-1 mt-1">
              <Globe className="w-4 h-4" /> Ghana Health Service Certified
            </p>
          </div>
        </div>
      </div>

      {/* Right Side - Discovery Flow */}
      <div className="flex-1 flex items-center justify-center p-8 bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="w-full max-w-lg">
          {/* Progress Indicator */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-2">
              {[
                { step: STEPS.REGION, label: 'Region' },
                { step: STEPS.HOSPITAL, label: 'Hospital' },
                { step: STEPS.LOCATION, label: 'Location' },
                { step: STEPS.LOGIN, label: 'Login' }
              ].map((s, idx) => (
                <React.Fragment key={s.step}>
                  <div className="flex flex-col items-center">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium transition-all
                      ${currentStep >= s.step 
                        ? 'bg-emerald-600 text-white' 
                        : 'bg-gray-200 text-gray-500'}`}
                    >
                      {currentStep > s.step ? <CheckCircle className="w-5 h-5" /> : idx + 1}
                    </div>
                    <span className={`text-xs mt-1 ${currentStep >= s.step ? 'text-emerald-600 font-medium' : 'text-gray-400'}`}>
                      {s.label}
                    </span>
                  </div>
                  {idx < 3 && (
                    <div className={`flex-1 h-1 mx-2 rounded ${currentStep > s.step ? 'bg-emerald-600' : 'bg-gray-200'}`} />
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* Step 1: Region Selection */}
          {currentStep === STEPS.REGION && (
            <Card className="border-0 shadow-xl">
              <CardHeader className="space-y-1 pb-4">
                <CardTitle className="text-2xl flex items-center gap-2">
                  <MapPin className="w-6 h-6 text-emerald-600" />
                  Select Your Region
                </CardTitle>
                <CardDescription>
                  Choose the region where your hospital is located
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {loading ? (
                  <div className="flex justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
                  </div>
                ) : (
                  <div className="grid grid-cols-2 gap-3 max-h-96 overflow-y-auto pr-2">
                    {regions.map((region) => (
                      <button
                        key={region.id}
                        onClick={() => handleRegionSelect(region)}
                        className="p-4 border rounded-lg text-left hover:border-emerald-500 hover:bg-emerald-50 transition-all group"
                      >
                        <div className="font-medium group-hover:text-emerald-700">{region.name}</div>
                        <div className="text-sm text-gray-500 flex items-center gap-1 mt-1">
                          <Building2 className="w-3 h-3" />
                          {region.hospital_count || 0} hospitals
                        </div>
                        <div className="text-xs text-gray-400 mt-1">Capital: {region.capital}</div>
                      </button>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Step 2: Hospital Selection */}
          {currentStep === STEPS.HOSPITAL && (
            <Card className="border-0 shadow-xl">
              <CardHeader className="space-y-1 pb-4">
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={goBack}
                  className="w-fit -ml-2 mb-2"
                >
                  <ChevronLeft className="w-4 h-4 mr-1" /> Back to Regions
                </Button>
                <CardTitle className="text-2xl flex items-center gap-2">
                  <Building2 className="w-6 h-6 text-emerald-600" />
                  Select Hospital
                </CardTitle>
                <CardDescription>
                  Hospitals in <span className="font-medium text-emerald-600">{selectedRegion?.name}</span>
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <Input
                    placeholder="Search hospitals..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9"
                  />
                </div>
                
                {loading ? (
                  <div className="flex justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
                  </div>
                ) : filteredHospitals.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <Building2 className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                    <p>No hospitals found in this region</p>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-80 overflow-y-auto pr-2">
                    {filteredHospitals.map((hospital) => (
                      <button
                        key={hospital.id}
                        onClick={() => handleHospitalSelect(hospital)}
                        className="w-full p-4 border rounded-lg text-left hover:border-emerald-500 hover:bg-emerald-50 transition-all group"
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <div className="font-medium group-hover:text-emerald-700">{hospital.name}</div>
                            <div className="text-sm text-gray-500 flex items-center gap-1 mt-1">
                              <MapPin className="w-3 h-3" />
                              {hospital.city}
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {hospital.has_multiple_locations && (
                              <Badge variant="secondary" className="text-xs">
                                {hospital.location_count} locations
                              </Badge>
                            )}
                            <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-emerald-600" />
                          </div>
                        </div>
                        {hospital.phone && (
                          <div className="text-xs text-gray-400 flex items-center gap-1 mt-2">
                            <Phone className="w-3 h-3" /> {hospital.phone}
                          </div>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Step 3: Location Selection (if multiple locations) */}
          {currentStep === STEPS.LOCATION && (
            <Card className="border-0 shadow-xl">
              <CardHeader className="space-y-1 pb-4">
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={goBack}
                  className="w-fit -ml-2 mb-2"
                >
                  <ChevronLeft className="w-4 h-4 mr-1" /> Back to Hospitals
                </Button>
                <CardTitle className="text-2xl flex items-center gap-2">
                  <MapPin className="w-6 h-6 text-emerald-600" />
                  Select Location
                </CardTitle>
                <CardDescription>
                  Choose your work location at <span className="font-medium text-emerald-600">{selectedHospital?.name}</span>
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {loading ? (
                  <div className="flex justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
                  </div>
                ) : (
                  <div className="space-y-3 max-h-80 overflow-y-auto pr-2">
                    {locations.map((location) => (
                      <button
                        key={location.id}
                        onClick={() => handleLocationSelect(location)}
                        className="w-full p-4 border rounded-lg text-left hover:border-emerald-500 hover:bg-emerald-50 transition-all group"
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <div className="font-medium group-hover:text-emerald-700">{location.name}</div>
                            <div className="text-sm text-gray-500 mt-1">{location.address}</div>
                            <div className="flex items-center gap-3 mt-2">
                              <Badge variant="outline" className="text-xs">
                                {location.location_type?.replace('_', ' ')}
                              </Badge>
                              {location.is_24_hour && (
                                <Badge className="bg-emerald-100 text-emerald-700 text-xs">24 Hour</Badge>
                              )}
                              {location.has_emergency && (
                                <Badge className="bg-red-100 text-red-700 text-xs">Emergency</Badge>
                              )}
                            </div>
                          </div>
                          <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-emerald-600" />
                        </div>
                        {location.operating_hours && (
                          <div className="text-xs text-gray-400 flex items-center gap-1 mt-2">
                            <Clock className="w-3 h-3" /> {location.operating_hours}
                          </div>
                        )}
                      </button>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Step 4: Login */}
          {currentStep === STEPS.LOGIN && (
            <Card className="border-0 shadow-xl">
              <CardHeader className="space-y-1 pb-4">
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={goBack}
                  className="w-fit -ml-2 mb-2"
                >
                  <ChevronLeft className="w-4 h-4 mr-1" /> Back
                </Button>
                <CardTitle className="text-2xl flex items-center gap-2">
                  <LogIn className="w-6 h-6 text-emerald-600" />
                  Sign In
                </CardTitle>
                <CardDescription>
                  Login to <span className="font-medium text-emerald-600">{selectedHospital?.name}</span>
                  {selectedLocation && (
                    <span className="block text-xs mt-1">
                      Location: {selectedLocation.name}
                    </span>
                  )}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleLogin} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="you@hospital.gh"
                      value={loginForm.email}
                      onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <Input
                      id="password"
                      type="password"
                      placeholder="••••••••"
                      value={loginForm.password}
                      onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                      required
                    />
                  </div>
                  <Button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-700" disabled={loading}>
                    {loading ? (
                      <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Signing in...</>
                    ) : (
                      <><LogIn className="w-4 h-4 mr-2" /> Sign In</>
                    )}
                  </Button>
                </form>
              </CardContent>
              <CardFooter className="flex flex-col gap-2 text-center text-sm text-gray-500">
                <p>Forgot your password? Contact your hospital administrator.</p>
              </CardFooter>
            </Card>
          )}

          {/* Context Info */}
          {(selectedRegion || selectedHospital) && currentStep !== STEPS.REGION && (
            <div className="mt-4 p-3 bg-emerald-50 rounded-lg border border-emerald-200">
              <div className="flex items-center gap-2 text-sm text-emerald-700">
                <CheckCircle className="w-4 h-4" />
                <span>
                  {selectedRegion?.name}
                  {selectedHospital && ` → ${selectedHospital.name}`}
                  {selectedLocation && ` → ${selectedLocation.name}`}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 2FA Dialog */}
      <Dialog open={show2FADialog} onOpenChange={setShow2FADialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Smartphone className="w-5 h-5 text-emerald-600" />
              Two-Factor Authentication
            </DialogTitle>
            <DialogDescription>
              Enter the 6-digit code from your authenticator app
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handle2FASubmit} className="space-y-4">
            <Input
              placeholder="000000"
              value={totpCode}
              onChange={(e) => setTotpCode(e.target.value)}
              className="text-center text-2xl tracking-widest"
              maxLength={6}
              autoFocus
            />
            <div className="flex gap-2">
              <Button 
                type="button" 
                variant="outline" 
                className="flex-1"
                onClick={() => {
                  setShow2FADialog(false);
                  setPendingLogin(null);
                  setTotpCode('');
                }}
              >
                Cancel
              </Button>
              <Button 
                type="submit" 
                className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                disabled={loading || totpCode.length < 6}
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Verify'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Phone Number Dialog for OTP */}
      <Dialog open={requiresPhone} onOpenChange={() => {}}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Phone className="w-5 h-5 text-emerald-600" />
              Phone Verification Required
            </DialogTitle>
            <DialogDescription>
              Enter your phone number to receive a one-time verification code
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handlePhoneSubmit} className="space-y-4">
            <div>
              <Label htmlFor="phone">Phone Number</Label>
              <Input
                id="phone"
                type="tel"
                placeholder="0241234567"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                className="mt-1"
              />
              <p className="text-xs text-slate-500 mt-1">
                Enter your Ghana mobile number (e.g., 0241234567)
              </p>
            </div>
            
            <div className="flex gap-2">
              <Button type="button" variant="outline" onClick={handleCancelOTP} className="flex-1">
                Cancel
              </Button>
              <Button type="submit" disabled={loading} className="flex-1 bg-emerald-600 hover:bg-emerald-700">
                {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                Send OTP
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* OTP Verification Dialog */}
      <Dialog open={requiresOTP && !requiresPhone} onOpenChange={() => {}}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-emerald-600" />
              Enter Verification Code
            </DialogTitle>
            <DialogDescription>
              We sent a 6-digit code to {otpPhoneMasked}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleOTPSubmit} className="space-y-4">
            <div>
              <Label htmlFor="otp">Verification Code</Label>
              <Input
                id="otp"
                type="text"
                placeholder="123456"
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                className="mt-1 text-center text-2xl tracking-widest"
                maxLength={6}
              />
            </div>
            
            <div className="flex gap-2">
              <Button type="button" variant="outline" onClick={handleCancelOTP} className="flex-1">
                Cancel
              </Button>
              <Button type="submit" disabled={loading || otpCode.length !== 6} className="flex-1 bg-emerald-600 hover:bg-emerald-700">
                {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                Verify
              </Button>
            </div>
            
            <div className="text-center">
              <Button
                type="button"
                variant="link"
                onClick={handleResendOTP}
                disabled={resending}
                className="text-sm"
              >
                {resending ? 'Resending...' : "Didn't receive code? Resend"}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
