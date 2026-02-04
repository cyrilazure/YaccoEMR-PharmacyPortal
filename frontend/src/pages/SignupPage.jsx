import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { signupAPI, regionAPI } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Checkbox } from '@/components/ui/checkbox';
import { 
  Select, SelectContent, SelectItem, 
  SelectTrigger, SelectValue 
} from '@/components/ui/select';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import { 
  Building2, User, Mail, Phone, MapPin, FileText,
  CheckCircle, Clock, Loader2, Activity, Shield,
  ArrowRight, Globe, Lock, AlertCircle
} from 'lucide-react';

// Ghana Regions
const GHANA_REGIONS = [
  { id: "greater-accra", name: "Greater Accra Region" },
  { id: "ashanti", name: "Ashanti Region" },
  { id: "eastern", name: "Eastern Region" },
  { id: "western", name: "Western Region" },
  { id: "central", name: "Central Region" },
  { id: "northern", name: "Northern Region" },
  { id: "volta", name: "Volta Region" },
  { id: "upper-east", name: "Upper East Region" },
  { id: "upper-west", name: "Upper West Region" },
  { id: "bono", name: "Bono Region" },
  { id: "bono-east", name: "Bono East Region" },
  { id: "ahafo", name: "Ahafo Region" },
  { id: "western-north", name: "Western North Region" },
  { id: "oti", name: "Oti Region" },
  { id: "north-east", name: "North East Region" },
  { id: "savannah", name: "Savannah Region" },
];

export default function SignupPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  
  const [activeTab, setActiveTab] = useState('hospital');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(null);
  
  // Hospital registration form
  const [hospitalForm, setHospitalForm] = useState({
    hospital_name: '',
    region_id: '',
    address: '',
    city: '',
    phone: '',
    hospital_email: '',
    website: '',
    license_number: '',
    ghana_health_service_id: '',
    admin_first_name: '',
    admin_last_name: '',
    admin_email: '',
    admin_phone: '',
    admin_title: 'Hospital Administrator',
    accept_terms: false
  });
  
  // Provider registration form
  const inviteCode = searchParams.get('code');
  const [providerForm, setProviderForm] = useState({
    invite_code: inviteCode || '',
    email: '',
    first_name: '',
    last_name: '',
    phone: '',
    specialty: '',
    license_number: '',
    password: '',
    confirm_password: '',
    accept_terms: false
  });

  useEffect(() => {
    if (inviteCode) {
      setActiveTab('provider');
      setProviderForm(prev => ({ ...prev, invite_code: inviteCode }));
    }
  }, [inviteCode]);

  const handleHospitalSubmit = async (e) => {
    e.preventDefault();
    
    if (!hospitalForm.accept_terms) {
      toast.error('Please accept the terms and conditions');
      return;
    }
    
    setLoading(true);
    try {
      const response = await signupAPI.registerHospital(hospitalForm);
      setSuccess({
        type: 'hospital',
        registrationId: response.data.registration_id,
        email: hospitalForm.admin_email,
        message: response.data.message
      });
      toast.success('Registration submitted successfully!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const handleProviderSubmit = async (e) => {
    e.preventDefault();
    
    if (!providerForm.accept_terms) {
      toast.error('Please accept the terms and conditions');
      return;
    }
    
    if (providerForm.password !== providerForm.confirm_password) {
      toast.error('Passwords do not match');
      return;
    }
    
    setLoading(true);
    try {
      const response = await signupAPI.registerProvider(providerForm);
      toast.success('Account created! You can now login.');
      navigate('/login');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  // Success screen
  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-teal-50 flex items-center justify-center p-8">
        <Card className="max-w-lg w-full border-0 shadow-xl">
          <CardHeader className="text-center pb-2">
            <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-8 h-8 text-emerald-600" />
            </div>
            <CardTitle className="text-2xl text-emerald-700">Registration Submitted!</CardTitle>
            <CardDescription>Your registration is being processed</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert className="bg-blue-50 border-blue-200">
              <Mail className="h-4 w-4 text-blue-600" />
              <AlertTitle className="text-blue-800">Check Your Email</AlertTitle>
              <AlertDescription className="text-blue-700">
                A verification link has been sent to <strong>{success.email}</strong>
              </AlertDescription>
            </Alert>
            
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-semibold mb-2">Next Steps:</h4>
              <ol className="space-y-2 text-sm text-gray-600">
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center text-xs font-bold flex-shrink-0">1</span>
                  <span>Verify your email (within 48 hours)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center text-xs font-bold flex-shrink-0">2</span>
                  <span>Wait for platform approval (1-2 business days)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center text-xs font-bold flex-shrink-0">3</span>
                  <span>Receive login credentials via email</span>
                </li>
              </ol>
            </div>
            
            <div className="text-center text-sm text-gray-500">
              Registration ID: <code className="bg-gray-100 px-2 py-1 rounded">{success.registrationId}</code>
            </div>
          </CardContent>
          <CardFooter className="flex flex-col gap-3">
            <Button 
              variant="outline" 
              className="w-full"
              onClick={() => navigate(`/signup/status?id=${success.registrationId}`)}
            >
              <Clock className="w-4 h-4 mr-2" />
              Check Status
            </Button>
            <Link to="/login" className="text-emerald-600 hover:underline text-sm">
              Already have an account? Login
            </Link>
          </CardFooter>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex">
      {/* Left Side - Branding */}
      <div className="hidden lg:flex lg:w-2/5 relative overflow-hidden bg-gradient-to-br from-emerald-600 via-emerald-700 to-teal-700">
        <div className="absolute inset-0">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(255,255,255,0.1),transparent_50%)]" />
        </div>
        
        <div className="relative z-10 flex flex-col justify-between p-12 text-white">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-xl bg-white/20 flex items-center justify-center">
                <Activity className="w-7 h-7" />
              </div>
              <div>
                <span className="text-2xl font-bold">Yacco EMR</span>
                <p className="text-emerald-200 text-sm">Ghana Healthcare Network</p>
              </div>
            </div>
          </div>
          
          <div className="space-y-6">
            <h1 className="text-3xl font-bold leading-tight">
              Join Ghana's Leading<br />Healthcare Platform
            </h1>
            <p className="text-emerald-100 max-w-md">
              Register your hospital or healthcare facility to access comprehensive 
              EMR services across all 16 regions of Ghana.
            </p>
            
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center">
                  <Shield className="w-5 h-5" />
                </div>
                <div>
                  <div className="font-semibold">HIPAA Compliant</div>
                  <div className="text-sm text-emerald-200">Secure patient data protection</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center">
                  <Globe className="w-5 h-5" />
                </div>
                <div>
                  <div className="font-semibold">Multi-Location Support</div>
                  <div className="text-sm text-emerald-200">Manage all your branches</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center">
                  <Lock className="w-5 h-5" />
                </div>
                <div>
                  <div className="font-semibold">Role-Based Access</div>
                  <div className="text-sm text-emerald-200">Secure staff management</div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="text-sm text-emerald-200">
            © 2025 Yacco EMR. Ghana Health Service Certified.
          </div>
        </div>
      </div>

      {/* Right Side - Forms */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-2xl mx-auto p-8">
          {/* Mobile Header */}
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-xl bg-emerald-600 flex items-center justify-center">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <span className="text-xl font-bold">Yacco EMR</span>
              <p className="text-gray-500 text-sm">Registration</p>
            </div>
          </div>

          <div className="mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Create Account</h2>
            <p className="text-gray-500">Register your hospital or join as a provider</p>
          </div>

          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid grid-cols-2 mb-6">
              <TabsTrigger value="hospital" className="gap-2">
                <Building2 className="w-4 h-4" />
                Hospital Registration
              </TabsTrigger>
              <TabsTrigger value="provider" className="gap-2">
                <User className="w-4 h-4" />
                Provider (Invite)
              </TabsTrigger>
            </TabsList>

            {/* Hospital Registration */}
            <TabsContent value="hospital">
              <form onSubmit={handleHospitalSubmit} className="space-y-6">
                {/* Hospital Information */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Building2 className="w-5 h-5 text-emerald-600" />
                      Hospital Information
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="grid grid-cols-2 gap-4">
                    <div className="col-span-2">
                      <Label>Hospital Name *</Label>
                      <Input
                        value={hospitalForm.hospital_name}
                        onChange={(e) => setHospitalForm({...hospitalForm, hospital_name: e.target.value})}
                        placeholder="e.g., Accra Regional Hospital"
                        required
                      />
                    </div>
                    <div>
                      <Label>Region *</Label>
                      <Select
                        value={hospitalForm.region_id}
                        onValueChange={(v) => setHospitalForm({...hospitalForm, region_id: v})}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select region" />
                        </SelectTrigger>
                        <SelectContent>
                          {GHANA_REGIONS.map((r) => (
                            <SelectItem key={r.id} value={r.id}>{r.name}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>City *</Label>
                      <Input
                        value={hospitalForm.city}
                        onChange={(e) => setHospitalForm({...hospitalForm, city: e.target.value})}
                        placeholder="e.g., Accra"
                        required
                      />
                    </div>
                    <div className="col-span-2">
                      <Label>Address *</Label>
                      <Input
                        value={hospitalForm.address}
                        onChange={(e) => setHospitalForm({...hospitalForm, address: e.target.value})}
                        placeholder="Street address"
                        required
                      />
                    </div>
                    <div>
                      <Label>Phone *</Label>
                      <Input
                        value={hospitalForm.phone}
                        onChange={(e) => setHospitalForm({...hospitalForm, phone: e.target.value})}
                        placeholder="+233-XXX-XXXXXX"
                        required
                      />
                    </div>
                    <div>
                      <Label>Email *</Label>
                      <Input
                        type="email"
                        value={hospitalForm.hospital_email}
                        onChange={(e) => setHospitalForm({...hospitalForm, hospital_email: e.target.value})}
                        placeholder="info@hospital.gov.gh"
                        required
                      />
                    </div>
                    <div>
                      <Label>License Number *</Label>
                      <Input
                        value={hospitalForm.license_number}
                        onChange={(e) => setHospitalForm({...hospitalForm, license_number: e.target.value})}
                        placeholder="GHS-XXX-XXXX"
                        required
                      />
                    </div>
                    <div>
                      <Label>GHS ID (Optional)</Label>
                      <Input
                        value={hospitalForm.ghana_health_service_id}
                        onChange={(e) => setHospitalForm({...hospitalForm, ghana_health_service_id: e.target.value})}
                        placeholder="Ghana Health Service ID"
                      />
                    </div>
                  </CardContent>
                </Card>

                {/* Admin Information */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <User className="w-5 h-5 text-emerald-600" />
                      Administrator Contact
                    </CardTitle>
                    <CardDescription>This person will manage your hospital account</CardDescription>
                  </CardHeader>
                  <CardContent className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>First Name *</Label>
                      <Input
                        value={hospitalForm.admin_first_name}
                        onChange={(e) => setHospitalForm({...hospitalForm, admin_first_name: e.target.value})}
                        required
                      />
                    </div>
                    <div>
                      <Label>Last Name *</Label>
                      <Input
                        value={hospitalForm.admin_last_name}
                        onChange={(e) => setHospitalForm({...hospitalForm, admin_last_name: e.target.value})}
                        required
                      />
                    </div>
                    <div>
                      <Label>Admin Email *</Label>
                      <Input
                        type="email"
                        value={hospitalForm.admin_email}
                        onChange={(e) => setHospitalForm({...hospitalForm, admin_email: e.target.value})}
                        placeholder="admin@hospital.gov.gh"
                        required
                      />
                    </div>
                    <div>
                      <Label>Admin Phone *</Label>
                      <Input
                        value={hospitalForm.admin_phone}
                        onChange={(e) => setHospitalForm({...hospitalForm, admin_phone: e.target.value})}
                        placeholder="+233-XXX-XXXXXX"
                        required
                      />
                    </div>
                  </CardContent>
                </Card>

                {/* Terms */}
                <div className="flex items-start gap-3">
                  <Checkbox
                    id="hospital-terms"
                    checked={hospitalForm.accept_terms}
                    onCheckedChange={(checked) => setHospitalForm({...hospitalForm, accept_terms: checked})}
                  />
                  <Label htmlFor="hospital-terms" className="text-sm text-gray-600 leading-relaxed">
                    I agree to the <a href="#" className="text-emerald-600 hover:underline">Terms of Service</a> and{' '}
                    <a href="#" className="text-emerald-600 hover:underline">Privacy Policy</a>. I confirm that I am 
                    authorized to register this hospital.
                  </Label>
                </div>

                <Button 
                  type="submit" 
                  className="w-full h-12 bg-emerald-600 hover:bg-emerald-700"
                  disabled={loading}
                >
                  {loading ? (
                    <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Submitting...</>
                  ) : (
                    <><Building2 className="w-4 h-4 mr-2" /> Register Hospital</>
                  )}
                </Button>
              </form>
            </TabsContent>

            {/* Provider Registration */}
            <TabsContent value="provider">
              <form onSubmit={handleProviderSubmit} className="space-y-6">
                <Alert className="bg-blue-50 border-blue-200">
                  <AlertCircle className="h-4 w-4 text-blue-600" />
                  <AlertTitle className="text-blue-800">Invite Required</AlertTitle>
                  <AlertDescription className="text-blue-700">
                    Provider registration requires an invite code from your hospital administrator.
                  </AlertDescription>
                </Alert>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Provider Registration</CardTitle>
                  </CardHeader>
                  <CardContent className="grid grid-cols-2 gap-4">
                    <div className="col-span-2">
                      <Label>Invite Code *</Label>
                      <Input
                        value={providerForm.invite_code}
                        onChange={(e) => setProviderForm({...providerForm, invite_code: e.target.value})}
                        placeholder="Enter your invite code"
                        required
                      />
                    </div>
                    <div>
                      <Label>First Name *</Label>
                      <Input
                        value={providerForm.first_name}
                        onChange={(e) => setProviderForm({...providerForm, first_name: e.target.value})}
                        required
                      />
                    </div>
                    <div>
                      <Label>Last Name *</Label>
                      <Input
                        value={providerForm.last_name}
                        onChange={(e) => setProviderForm({...providerForm, last_name: e.target.value})}
                        required
                      />
                    </div>
                    <div>
                      <Label>Email *</Label>
                      <Input
                        type="email"
                        value={providerForm.email}
                        onChange={(e) => setProviderForm({...providerForm, email: e.target.value})}
                        required
                      />
                    </div>
                    <div>
                      <Label>Phone *</Label>
                      <Input
                        value={providerForm.phone}
                        onChange={(e) => setProviderForm({...providerForm, phone: e.target.value})}
                        required
                      />
                    </div>
                    <div>
                      <Label>Specialty</Label>
                      <Input
                        value={providerForm.specialty}
                        onChange={(e) => setProviderForm({...providerForm, specialty: e.target.value})}
                        placeholder="e.g., Cardiology"
                      />
                    </div>
                    <div>
                      <Label>License Number</Label>
                      <Input
                        value={providerForm.license_number}
                        onChange={(e) => setProviderForm({...providerForm, license_number: e.target.value})}
                      />
                    </div>
                    <div>
                      <Label>Password *</Label>
                      <Input
                        type="password"
                        value={providerForm.password}
                        onChange={(e) => setProviderForm({...providerForm, password: e.target.value})}
                        required
                        minLength={8}
                      />
                    </div>
                    <div>
                      <Label>Confirm Password *</Label>
                      <Input
                        type="password"
                        value={providerForm.confirm_password}
                        onChange={(e) => setProviderForm({...providerForm, confirm_password: e.target.value})}
                        required
                      />
                    </div>
                  </CardContent>
                </Card>

                <div className="flex items-start gap-3">
                  <Checkbox
                    id="provider-terms"
                    checked={providerForm.accept_terms}
                    onCheckedChange={(checked) => setProviderForm({...providerForm, accept_terms: checked})}
                  />
                  <Label htmlFor="provider-terms" className="text-sm text-gray-600">
                    I agree to the Terms of Service and Privacy Policy.
                  </Label>
                </div>

                <Button 
                  type="submit" 
                  className="w-full h-12 bg-emerald-600 hover:bg-emerald-700"
                  disabled={loading}
                >
                  {loading ? (
                    <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Creating Account...</>
                  ) : (
                    <><User className="w-4 h-4 mr-2" /> Create Account</>
                  )}
                </Button>
              </form>
            </TabsContent>
          </Tabs>

          <div className="mt-6 text-center">
            <p className="text-gray-500">
              Already have an account?{' '}
              <Link to="/login" className="text-emerald-600 hover:underline font-medium">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
