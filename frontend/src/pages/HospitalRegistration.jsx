import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Dialog, DialogContent, DialogDescription,
  DialogHeader, DialogTitle, DialogFooter
} from '@/components/ui/dialog';
import {
  Select, SelectContent, SelectItem,
  SelectTrigger, SelectValue
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { 
  Hospital, Building2, MapPin, Phone, Mail, 
  FileText, User, Shield, CheckCircle, Clock,
  Loader2, ArrowRight, Activity, Globe, UserPlus,
  LogIn, ChevronRight, Stethoscope, Heart
} from 'lucide-react';
import api from '@/lib/api';

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

const ORGANIZATION_TYPES = [
  { value: "hospital", label: "Hospital" },
  { value: "clinic", label: "Clinic" },
  { value: "medical_center", label: "Medical Center" },
  { value: "urgent_care", label: "Urgent Care Center" },
  { value: "specialty_center", label: "Specialty Center" },
];

export default function HospitalRegistration() {
  const navigate = useNavigate();
  const [showRegister, setShowRegister] = useState(false);
  const [loading, setLoading] = useState(false);
  const [registrationSuccess, setRegistrationSuccess] = useState(false);
  
  const [formData, setFormData] = useState({
    // Organization Info
    name: '',
    organization_type: 'hospital',
    license_number: '',
    npi_number: '',
    tax_id: '',
    // Address
    address_line1: '',
    address_line2: '',
    city: '',
    state: '',
    zip_code: '',
    country: 'Ghana',
    // Contact
    phone: '',
    fax: '',
    email: '',
    website: '',
    // Admin Contact
    admin_first_name: '',
    admin_last_name: '',
    admin_email: '',
    admin_phone: '',
    admin_title: 'Hospital Administrator',
  });

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await api.post('/organizations/register', formData);
      setRegistrationSuccess(true);
      toast.success('Registration submitted successfully!');
    } catch (error) {
      // Handle error - detail can be a string or array of validation errors
      const errorDetail = error.response?.data?.detail;
      let errorMessage = 'Registration failed. Please try again.';
      
      if (typeof errorDetail === 'string') {
        errorMessage = errorDetail;
      } else if (Array.isArray(errorDetail)) {
        // Extract field names from validation errors
        const missingFields = errorDetail.map(err => {
          const field = err.loc?.[err.loc.length - 1] || 'Unknown';
          return field.replace(/_/g, ' ');
        });
        errorMessage = `Please fill in required fields: ${missingFields.slice(0, 3).join(', ')}${missingFields.length > 3 ? '...' : ''}`;
      }
      
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      organization_type: 'hospital',
      license_number: '',
      npi_number: '',
      tax_id: '',
      address_line1: '',
      address_line2: '',
      city: '',
      state: '',
      zip_code: '',
      country: 'Ghana',
      phone: '',
      fax: '',
      email: '',
      website: '',
      admin_first_name: '',
      admin_last_name: '',
      admin_email: '',
      admin_phone: '',
      admin_title: 'Hospital Administrator',
    });
    setRegistrationSuccess(false);
    setShowRegister(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-50 to-white" data-testid="hospital-registration">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-emerald-600 to-emerald-700 rounded-xl flex items-center justify-center">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-emerald-700">Yacco EMR</h1>
                <p className="text-xs text-slate-500">Hospital Registration Portal</p>
              </div>
            </Link>
            <div className="flex items-center gap-3">
              <Button variant="outline" onClick={() => navigate('/login')}>
                <LogIn className="w-4 h-4 mr-2" />
                Staff Login
              </Button>
              <Button className="bg-emerald-600 hover:bg-emerald-700" onClick={() => setShowRegister(true)}>
                <UserPlus className="w-4 h-4 mr-2" />
                Register Hospital
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-16 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <Badge className="bg-emerald-100 text-emerald-700 mb-4">
              <Hospital className="w-3 h-3 mr-1" /> Ghana Healthcare Network
            </Badge>
            <h1 className="text-4xl sm:text-5xl font-bold mb-4">
              <span className="text-emerald-700">Join Ghana's</span>
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-emerald-600 to-blue-600">
                Digital Healthcare Network
              </span>
            </h1>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Register your hospital or healthcare facility to access Yacco EMR - 
              Ghana's integrated electronic medical records system.
            </p>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto mb-12">
            <Card>
              <CardContent className="pt-6 text-center">
                <div className="text-3xl font-bold text-emerald-600">200+</div>
                <div className="text-sm text-slate-500">Registered Hospitals</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6 text-center">
                <div className="text-3xl font-bold text-emerald-600">16</div>
                <div className="text-sm text-slate-500">Regions Covered</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6 text-center">
                <div className="text-3xl font-bold text-emerald-600">50K+</div>
                <div className="text-sm text-slate-500">Healthcare Workers</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6 text-center">
                <div className="text-3xl font-bold text-emerald-600">NHIS</div>
                <div className="text-sm text-slate-500">Integrated</div>
              </CardContent>
            </Card>
          </div>

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            <Card className="border-emerald-200 hover:border-emerald-300 transition-colors">
              <CardHeader>
                <div className="w-12 h-12 rounded-lg bg-emerald-100 flex items-center justify-center mb-2">
                  <FileText className="w-6 h-6 text-emerald-600" />
                </div>
                <CardTitle className="text-lg">Electronic Medical Records</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-slate-600 text-sm">
                  Comprehensive patient records, clinical documentation, and medical history management.
                </p>
              </CardContent>
            </Card>

            <Card className="border-emerald-200 hover:border-emerald-300 transition-colors">
              <CardHeader>
                <div className="w-12 h-12 rounded-lg bg-emerald-100 flex items-center justify-center mb-2">
                  <Stethoscope className="w-6 h-6 text-emerald-600" />
                </div>
                <CardTitle className="text-lg">Clinical Modules</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-slate-600 text-sm">
                  Laboratory, Radiology, Pharmacy, Nursing, and specialized department modules.
                </p>
              </CardContent>
            </Card>

            <Card className="border-emerald-200 hover:border-emerald-300 transition-colors">
              <CardHeader>
                <div className="w-12 h-12 rounded-lg bg-emerald-100 flex items-center justify-center mb-2">
                  <Shield className="w-6 h-6 text-emerald-600" />
                </div>
                <CardTitle className="text-lg">NHIS Integration</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-slate-600 text-sm">
                  Seamless integration with National Health Insurance Scheme for claims processing.
                </p>
              </CardContent>
            </Card>
          </div>

          {/* CTA */}
          <div className="text-center mt-12">
            <Button 
              size="lg" 
              className="bg-emerald-600 hover:bg-emerald-700 text-lg px-8"
              onClick={() => setShowRegister(true)}
            >
              <Hospital className="w-5 h-5 mr-2" />
              Register Your Hospital
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
            <p className="text-sm text-slate-500 mt-4">
              Registration is free. Approval typically takes 1-3 business days.
            </p>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-16 px-4 bg-white">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold text-center mb-12">How to Join</h2>
          <div className="grid md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto mb-4 text-xl font-bold">1</div>
              <h3 className="font-semibold mb-2">Register</h3>
              <p className="text-sm text-slate-600">Submit your hospital information and license details</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto mb-4 text-xl font-bold">2</div>
              <h3 className="font-semibold mb-2">Review</h3>
              <p className="text-sm text-slate-600">Our team verifies your credentials and documentation</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto mb-4 text-xl font-bold">3</div>
              <h3 className="font-semibold mb-2">Approval</h3>
              <p className="text-sm text-slate-600">Receive admin credentials upon approval</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto mb-4 text-xl font-bold">4</div>
              <h3 className="font-semibold mb-2">Go Live</h3>
              <p className="text-sm text-slate-600">Start using Yacco EMR for your hospital</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-white py-8 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-600 flex items-center justify-center">
              <Activity className="w-5 h-5" />
            </div>
            <span className="text-xl font-bold">Yacco Health</span>
          </div>
          <p className="text-slate-400 text-sm">
            Ghana's Integrated Healthcare Platform
          </p>
          <div className="flex justify-center gap-4 mt-4 text-sm text-slate-400">
            <Link to="/" className="hover:text-white">Home</Link>
            <Link to="/pharmacy" className="hover:text-white">Pharmacy Network</Link>
            <Link to="/login" className="hover:text-white">Staff Login</Link>
          </div>
        </div>
      </footer>

      {/* Registration Dialog */}
      <Dialog open={showRegister} onOpenChange={setShowRegister}>
        <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Hospital className="w-5 h-5 text-emerald-600" />
              {registrationSuccess ? 'Registration Submitted' : 'Hospital Registration'}
            </DialogTitle>
            <DialogDescription>
              {registrationSuccess 
                ? 'Your registration has been submitted for review.'
                : 'Fill in your hospital details to join the Yacco EMR network.'
              }
            </DialogDescription>
          </DialogHeader>

          {registrationSuccess ? (
            <div className="py-8 text-center">
              <div className="w-20 h-20 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-6">
                <CheckCircle className="w-10 h-10 text-emerald-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Registration Submitted!</h3>
              <p className="text-slate-600 mb-6">
                Your hospital registration is pending review by our team.<br />
                You will receive an email at <strong>{formData.admin_email}</strong> once approved.
              </p>
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-left mb-6">
                <div className="flex items-start gap-3">
                  <Clock className="w-5 h-5 text-amber-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-amber-800">What happens next?</p>
                    <ul className="text-sm text-amber-700 mt-1 space-y-1">
                      <li>• Our team will verify your hospital credentials</li>
                      <li>• Approval typically takes 1-3 business days</li>
                      <li>• You'll receive admin login credentials via email</li>
                    </ul>
                  </div>
                </div>
              </div>
              <Button onClick={resetForm} className="bg-emerald-600 hover:bg-emerald-700">
                Close
              </Button>
            </div>
          ) : (
            <form onSubmit={handleRegister} className="space-y-6">
              {/* Organization Information */}
              <div className="space-y-4">
                <h3 className="font-semibold flex items-center gap-2">
                  <Building2 className="w-4 h-4 text-emerald-600" />
                  Organization Information
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2">
                    <Label>Hospital/Facility Name *</Label>
                    <Input
                      value={formData.name}
                      onChange={(e) => handleInputChange('name', e.target.value)}
                      placeholder="e.g., Korle Bu Teaching Hospital"
                      required
                    />
                  </div>
                  <div>
                    <Label>Facility Type *</Label>
                    <Select 
                      value={formData.organization_type} 
                      onValueChange={(v) => handleInputChange('organization_type', v)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {ORGANIZATION_TYPES.map(type => (
                          <SelectItem key={type.value} value={type.value}>{type.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>License Number *</Label>
                    <Input
                      value={formData.license_number}
                      onChange={(e) => handleInputChange('license_number', e.target.value)}
                      placeholder="Health facility license"
                      required
                    />
                  </div>
                  <div>
                    <Label>NPI Number</Label>
                    <Input
                      value={formData.npi_number}
                      onChange={(e) => handleInputChange('npi_number', e.target.value)}
                      placeholder="Optional"
                    />
                  </div>
                  <div>
                    <Label>Tax ID</Label>
                    <Input
                      value={formData.tax_id}
                      onChange={(e) => handleInputChange('tax_id', e.target.value)}
                      placeholder="Optional"
                    />
                  </div>
                </div>
              </div>

              {/* Address */}
              <div className="space-y-4">
                <h3 className="font-semibold flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-emerald-600" />
                  Location
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2">
                    <Label>Address Line 1 *</Label>
                    <Input
                      value={formData.address_line1}
                      onChange={(e) => handleInputChange('address_line1', e.target.value)}
                      placeholder="Street address"
                      required
                    />
                  </div>
                  <div className="col-span-2">
                    <Label>Address Line 2</Label>
                    <Input
                      value={formData.address_line2}
                      onChange={(e) => handleInputChange('address_line2', e.target.value)}
                      placeholder="Building, Suite, etc."
                    />
                  </div>
                  <div>
                    <Label>City/Town *</Label>
                    <Input
                      value={formData.city}
                      onChange={(e) => handleInputChange('city', e.target.value)}
                      placeholder="e.g., Accra"
                      required
                    />
                  </div>
                  <div>
                    <Label>Region *</Label>
                    <Select 
                      value={formData.state} 
                      onValueChange={(v) => handleInputChange('state', v)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select region" />
                      </SelectTrigger>
                      <SelectContent>
                        {GHANA_REGIONS.map(region => (
                          <SelectItem key={region.id} value={region.name}>{region.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Postal Code</Label>
                    <Input
                      value={formData.zip_code}
                      onChange={(e) => handleInputChange('zip_code', e.target.value)}
                      placeholder="e.g., GA-123"
                    />
                  </div>
                </div>
              </div>

              {/* Contact */}
              <div className="space-y-4">
                <h3 className="font-semibold flex items-center gap-2">
                  <Phone className="w-4 h-4 text-emerald-600" />
                  Contact Information
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Phone Number *</Label>
                    <Input
                      value={formData.phone}
                      onChange={(e) => handleInputChange('phone', e.target.value)}
                      placeholder="e.g., 030-2123456"
                      required
                    />
                  </div>
                  <div>
                    <Label>Fax Number</Label>
                    <Input
                      value={formData.fax}
                      onChange={(e) => handleInputChange('fax', e.target.value)}
                      placeholder="Optional"
                    />
                  </div>
                  <div>
                    <Label>Email Address *</Label>
                    <Input
                      type="email"
                      value={formData.email}
                      onChange={(e) => handleInputChange('email', e.target.value)}
                      placeholder="hospital@example.com"
                      required
                    />
                  </div>
                  <div>
                    <Label>Website</Label>
                    <Input
                      value={formData.website}
                      onChange={(e) => handleInputChange('website', e.target.value)}
                      placeholder="https://..."
                    />
                  </div>
                </div>
              </div>

              {/* Admin Contact */}
              <div className="space-y-4">
                <h3 className="font-semibold flex items-center gap-2">
                  <User className="w-4 h-4 text-emerald-600" />
                  Administrator Contact
                </h3>
                <p className="text-sm text-slate-500">
                  This person will receive the admin login credentials upon approval.
                </p>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>First Name *</Label>
                    <Input
                      value={formData.admin_first_name}
                      onChange={(e) => handleInputChange('admin_first_name', e.target.value)}
                      placeholder="First name"
                      required
                    />
                  </div>
                  <div>
                    <Label>Last Name *</Label>
                    <Input
                      value={formData.admin_last_name}
                      onChange={(e) => handleInputChange('admin_last_name', e.target.value)}
                      placeholder="Last name"
                      required
                    />
                  </div>
                  <div>
                    <Label>Admin Email *</Label>
                    <Input
                      type="email"
                      value={formData.admin_email}
                      onChange={(e) => handleInputChange('admin_email', e.target.value)}
                      placeholder="admin@hospital.com"
                      required
                    />
                  </div>
                  <div>
                    <Label>Admin Phone *</Label>
                    <Input
                      value={formData.admin_phone}
                      onChange={(e) => handleInputChange('admin_phone', e.target.value)}
                      placeholder="e.g., 024-1234567"
                      required
                    />
                  </div>
                  <div className="col-span-2">
                    <Label>Job Title</Label>
                    <Input
                      value={formData.admin_title}
                      onChange={(e) => handleInputChange('admin_title', e.target.value)}
                      placeholder="e.g., Hospital Administrator"
                    />
                  </div>
                </div>
              </div>

              <DialogFooter className="gap-2">
                <Button type="button" variant="outline" onClick={() => setShowRegister(false)}>
                  Cancel
                </Button>
                <Button type="submit" className="bg-emerald-600 hover:bg-emerald-700" disabled={loading}>
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Submitting...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Submit Registration
                    </>
                  )}
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
