import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { organizationAPI } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';
import { Building2, ArrowLeft, CheckCircle2, ArrowRight } from 'lucide-react';

export default function HospitalRegistration() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  
  const [formData, setFormData] = useState({
    // Organization info
    name: '',
    organization_type: 'hospital',
    address_line1: '',
    address_line2: '',
    city: '',
    state: '',
    zip_code: '',
    country: 'USA',
    phone: '',
    fax: '',
    email: '',
    website: '',
    license_number: '',
    tax_id: '',
    npi_number: '',
    // Admin contact
    admin_first_name: '',
    admin_last_name: '',
    admin_email: '',
    admin_phone: '',
    admin_title: 'Administrator'
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await organizationAPI.register(formData);
      setSubmitted(true);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to submit registration');
    } finally {
      setLoading(false);
    }
  };

  const updateField = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const canProceed = () => {
    if (step === 1) {
      return formData.name && formData.address_line1 && formData.city && 
             formData.state && formData.zip_code && formData.phone && formData.email;
    }
    if (step === 2) {
      return formData.license_number;
    }
    if (step === 3) {
      return formData.admin_first_name && formData.admin_last_name && 
             formData.admin_email && formData.admin_phone;
    }
    return false;
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-sky-50 to-indigo-100 flex items-center justify-center p-4">
        <Card className="w-full max-w-lg text-center">
          <CardContent className="pt-12 pb-8">
            <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6">
              <CheckCircle2 className="w-10 h-10 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold mb-2">Registration Submitted!</h2>
            <p className="text-slate-500 mb-6">
              Thank you for registering your organization with Yacco EMR. 
              Your application is now pending review.
            </p>
            <p className="text-sm text-slate-600 mb-8">
              You will receive an email at <strong>{formData.admin_email}</strong> once your 
              registration has been approved. This typically takes 1-2 business days.
            </p>
            <Button onClick={() => navigate('/login')} className="w-full">
              Return to Login
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 to-indigo-100 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <Link to="/login" className="inline-flex items-center text-sky-600 hover:text-sky-700 mb-4">
            <ArrowLeft className="w-4 h-4 mr-1" /> Back to Login
          </Link>
          <div className="flex items-center justify-center gap-3 mb-2">
            <div className="w-12 h-12 rounded-xl bg-sky-600 flex items-center justify-center">
              <Building2 className="w-7 h-7 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-slate-900" style={{ fontFamily: 'Manrope' }}>
              Yacco EMR
            </h1>
          </div>
          <p className="text-slate-500">Hospital Registration</p>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-center mb-8">
          {[1, 2, 3].map((s) => (
            <div key={s} className="flex items-center">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                s <= step ? 'bg-sky-600 text-white' : 'bg-slate-200 text-slate-500'
              }`}>
                {s}
              </div>
              {s < 3 && (
                <div className={`w-16 h-1 ${s < step ? 'bg-sky-600' : 'bg-slate-200'}`} />
              )}
            </div>
          ))}
        </div>

        <Card>
          <CardHeader>
            <CardTitle>
              {step === 1 && 'Organization Information'}
              {step === 2 && 'Registration Details'}
              {step === 3 && 'Administrator Contact'}
            </CardTitle>
            <CardDescription>
              {step === 1 && 'Enter your hospital or healthcare organization details'}
              {step === 2 && 'Provide your license and registration information'}
              {step === 3 && 'Enter the primary administrator contact information'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit}>
              {/* Step 1: Organization Info */}
              {step === 1 && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2 col-span-2">
                      <Label>Organization Name *</Label>
                      <Input 
                        required 
                        value={formData.name} 
                        onChange={(e) => updateField('name', e.target.value)}
                        placeholder="e.g., City General Hospital"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Organization Type</Label>
                      <Select value={formData.organization_type} onValueChange={(v) => updateField('organization_type', v)}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="hospital">Hospital</SelectItem>
                          <SelectItem value="clinic">Clinic</SelectItem>
                          <SelectItem value="medical_center">Medical Center</SelectItem>
                          <SelectItem value="urgent_care">Urgent Care</SelectItem>
                          <SelectItem value="specialty_center">Specialty Center</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Street Address *</Label>
                    <Input 
                      required
                      value={formData.address_line1} 
                      onChange={(e) => updateField('address_line1', e.target.value)}
                      placeholder="123 Medical Center Drive"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Address Line 2</Label>
                    <Input 
                      value={formData.address_line2} 
                      onChange={(e) => updateField('address_line2', e.target.value)}
                      placeholder="Suite, Building, Floor (optional)"
                    />
                  </div>
                  
                  <div className="grid grid-cols-6 gap-4">
                    <div className="space-y-2 col-span-3">
                      <Label>City *</Label>
                      <Input required value={formData.city} onChange={(e) => updateField('city', e.target.value)} />
                    </div>
                    <div className="space-y-2 col-span-1">
                      <Label>State *</Label>
                      <Input required value={formData.state} onChange={(e) => updateField('state', e.target.value)} placeholder="CA" />
                    </div>
                    <div className="space-y-2 col-span-2">
                      <Label>ZIP Code *</Label>
                      <Input required value={formData.zip_code} onChange={(e) => updateField('zip_code', e.target.value)} />
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Phone *</Label>
                      <Input required value={formData.phone} onChange={(e) => updateField('phone', e.target.value)} placeholder="(555) 123-4567" />
                    </div>
                    <div className="space-y-2">
                      <Label>Email *</Label>
                      <Input type="email" required value={formData.email} onChange={(e) => updateField('email', e.target.value)} placeholder="info@hospital.com" />
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Website</Label>
                    <Input value={formData.website} onChange={(e) => updateField('website', e.target.value)} placeholder="https://www.hospital.com" />
                  </div>
                </div>
              )}

              {/* Step 2: Registration Details */}
              {step === 2 && (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>License Number *</Label>
                    <Input 
                      required 
                      value={formData.license_number} 
                      onChange={(e) => updateField('license_number', e.target.value)}
                      placeholder="State healthcare license number"
                    />
                    <p className="text-sm text-slate-500">Your state-issued healthcare facility license number</p>
                  </div>
                  
                  <div className="space-y-2">
                    <Label>NPI Number</Label>
                    <Input 
                      value={formData.npi_number} 
                      onChange={(e) => updateField('npi_number', e.target.value)}
                      placeholder="10-digit NPI"
                    />
                    <p className="text-sm text-slate-500">National Provider Identifier (if applicable)</p>
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Tax ID / EIN</Label>
                    <Input 
                      value={formData.tax_id} 
                      onChange={(e) => updateField('tax_id', e.target.value)}
                      placeholder="XX-XXXXXXX"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Fax Number</Label>
                    <Input 
                      value={formData.fax} 
                      onChange={(e) => updateField('fax', e.target.value)}
                      placeholder="(555) 123-4568"
                    />
                  </div>
                </div>
              )}

              {/* Step 3: Admin Contact */}
              {step === 3 && (
                <div className="space-y-4">
                  <p className="text-sm text-slate-600 mb-4">
                    This person will be the primary administrator for your organization and will 
                    receive login credentials upon approval.
                  </p>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>First Name *</Label>
                      <Input required value={formData.admin_first_name} onChange={(e) => updateField('admin_first_name', e.target.value)} />
                    </div>
                    <div className="space-y-2">
                      <Label>Last Name *</Label>
                      <Input required value={formData.admin_last_name} onChange={(e) => updateField('admin_last_name', e.target.value)} />
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Title</Label>
                    <Input value={formData.admin_title} onChange={(e) => updateField('admin_title', e.target.value)} placeholder="e.g., IT Director, Administrator" />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Email *</Label>
                    <Input type="email" required value={formData.admin_email} onChange={(e) => updateField('admin_email', e.target.value)} />
                    <p className="text-sm text-slate-500">Login credentials will be sent to this email</p>
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Phone *</Label>
                    <Input required value={formData.admin_phone} onChange={(e) => updateField('admin_phone', e.target.value)} />
                  </div>
                </div>
              )}

              {/* Navigation Buttons */}
              <div className="flex justify-between mt-8">
                {step > 1 ? (
                  <Button type="button" variant="outline" onClick={() => setStep(step - 1)}>
                    <ArrowLeft className="w-4 h-4 mr-2" /> Previous
                  </Button>
                ) : (
                  <div />
                )}
                
                {step < 3 ? (
                  <Button type="button" onClick={() => setStep(step + 1)} disabled={!canProceed()}>
                    Next <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                ) : (
                  <Button type="submit" disabled={!canProceed() || loading}>
                    {loading ? 'Submitting...' : 'Submit Registration'}
                  </Button>
                )}
              </div>
            </form>
          </CardContent>
        </Card>

        <p className="text-center text-sm text-slate-500 mt-6">
          Already registered? <Link to="/login" className="text-sky-600 hover:underline">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
