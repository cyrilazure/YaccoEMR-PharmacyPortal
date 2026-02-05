import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { patientAPI } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Checkbox } from '@/components/ui/checkbox';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { toast } from 'sonner';
import { calculateAge, formatDate } from '@/lib/utils';
import { 
  Search, UserPlus, Users, ChevronRight, Phone, Mail, 
  Calendar, IdCard, FileText, Hash, CreditCard, Banknote, AlertCircle
} from 'lucide-react';

export default function Patients() {
  const navigate = useNavigate();
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [paymentType, setPaymentType] = useState('insurance'); // 'insurance' or 'cash'
  const [newPatient, setNewPatient] = useState({
    first_name: '', last_name: '', date_of_birth: '', gender: 'male',
    mrn: '', // Added MRN field
    email: '', phone: '', address: '',
    emergency_contact_name: '', emergency_contact_phone: '',
    insurance_provider: '', insurance_id: '', insurance_plan: '',
    payment_type: 'insurance', // 'insurance' or 'cash'
    adt_notification: true // ADT notification flag
  });

  useEffect(() => {
    fetchPatients();
  }, []);

  useEffect(() => {
    const delaySearch = setTimeout(() => {
      fetchPatients(searchTerm);
    }, 300);
    return () => clearTimeout(delaySearch);
  }, [searchTerm]);

  const fetchPatients = async (search = '') => {
    try {
      const res = await patientAPI.getAll(search);
      setPatients(res.data);
    } catch (err) {
      toast.error('Failed to load patients');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePatient = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await patientAPI.create(newPatient);
      toast.success('Patient created successfully');
      setDialogOpen(false);
      setNewPatient({
        first_name: '', last_name: '', date_of_birth: '', gender: 'male',
        email: '', phone: '', address: '',
        emergency_contact_name: '', emergency_contact_phone: '',
        insurance_provider: '', insurance_id: ''
      });
      fetchPatients();
      navigate(`/patients/${res.data.id}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create patient');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="patients-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900" style={{ fontFamily: 'Manrope' }}>
            Patients
          </h1>
          <p className="text-slate-500 mt-1">Manage patient records and information</p>
        </div>
        
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2 bg-sky-600 hover:bg-sky-700" data-testid="add-patient-btn">
              <UserPlus className="w-4 h-4" /> Add Patient
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle style={{ fontFamily: 'Manrope' }}>Register New Patient</DialogTitle>
              <DialogDescription>
                Enter the patient's demographic and contact information
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreatePatient} className="space-y-6 mt-4">
              {/* Personal Info */}
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900 flex items-center gap-2">
                  <Users className="w-4 h-4" /> Personal Information
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="first_name">First Name *</Label>
                    <Input 
                      id="first_name"
                      data-testid="patient-firstname"
                      value={newPatient.first_name}
                      onChange={(e) => setNewPatient({ ...newPatient, first_name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="last_name">Last Name *</Label>
                    <Input 
                      id="last_name"
                      data-testid="patient-lastname"
                      value={newPatient.last_name}
                      onChange={(e) => setNewPatient({ ...newPatient, last_name: e.target.value })}
                      required
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="dob">Date of Birth *</Label>
                    <Input 
                      id="dob"
                      data-testid="patient-dob"
                      type="date"
                      value={newPatient.date_of_birth}
                      onChange={(e) => setNewPatient({ ...newPatient, date_of_birth: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="gender">Gender *</Label>
                    <Select 
                      value={newPatient.gender} 
                      onValueChange={(value) => setNewPatient({ ...newPatient, gender: value })}
                    >
                      <SelectTrigger data-testid="patient-gender">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="male">Male</SelectItem>
                        <SelectItem value="female">Female</SelectItem>
                        <SelectItem value="other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              {/* Contact Info */}
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900 flex items-center gap-2">
                  <Phone className="w-4 h-4" /> Contact Information
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input 
                      id="email"
                      data-testid="patient-email"
                      type="email"
                      value={newPatient.email}
                      onChange={(e) => setNewPatient({ ...newPatient, email: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="phone">Phone</Label>
                    <Input 
                      id="phone"
                      data-testid="patient-phone"
                      value={newPatient.phone}
                      onChange={(e) => setNewPatient({ ...newPatient, phone: e.target.value })}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="address">Address</Label>
                  <Input 
                    id="address"
                    data-testid="patient-address"
                    value={newPatient.address}
                    onChange={(e) => setNewPatient({ ...newPatient, address: e.target.value })}
                  />
                </div>
              </div>

              {/* Emergency Contact */}
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900 flex items-center gap-2">
                  <Users className="w-4 h-4" /> Emergency Contact
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="emergency_name">Contact Name</Label>
                    <Input 
                      id="emergency_name"
                      data-testid="patient-emergency-name"
                      value={newPatient.emergency_contact_name}
                      onChange={(e) => setNewPatient({ ...newPatient, emergency_contact_name: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="emergency_phone">Contact Phone</Label>
                    <Input 
                      id="emergency_phone"
                      data-testid="patient-emergency-phone"
                      value={newPatient.emergency_contact_phone}
                      onChange={(e) => setNewPatient({ ...newPatient, emergency_contact_phone: e.target.value })}
                    />
                  </div>
                </div>
              </div>

              {/* Insurance Info */}
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900 flex items-center gap-2">
                  <IdCard className="w-4 h-4" /> Insurance Information
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="insurance_provider">Insurance Provider</Label>
                    <Input 
                      id="insurance_provider"
                      data-testid="patient-insurance-provider"
                      value={newPatient.insurance_provider}
                      onChange={(e) => setNewPatient({ ...newPatient, insurance_provider: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="insurance_id">Insurance ID</Label>
                    <Input 
                      id="insurance_id"
                      data-testid="patient-insurance-id"
                      value={newPatient.insurance_id}
                      onChange={(e) => setNewPatient({ ...newPatient, insurance_id: e.target.value })}
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t">
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={saving} data-testid="save-patient-btn">
                  {saving ? 'Creating...' : 'Create Patient'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <Input 
              placeholder="Search by name or MRN..."
              className="pl-10"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              data-testid="patient-search"
            />
          </div>
        </CardContent>
      </Card>

      {/* Patients Table */}
      <Card>
        <CardHeader>
          <CardTitle style={{ fontFamily: 'Manrope' }}>Patient Registry</CardTitle>
          <CardDescription>{patients.length} patients found</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3, 4, 5].map(i => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : patients.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              <Users className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium">No patients found</p>
              <p className="text-sm">Register your first patient to get started</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Patient</TableHead>
                  <TableHead>MRN</TableHead>
                  <TableHead>Age / Gender</TableHead>
                  <TableHead>Contact</TableHead>
                  <TableHead>Insurance</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {patients.map((patient) => (
                  <TableRow 
                    key={patient.id} 
                    className="cursor-pointer hover:bg-slate-50"
                    onClick={() => navigate(`/patients/${patient.id}`)}
                    data-testid={`patient-row-${patient.id}`}
                  >
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-sky-100 text-sky-700 flex items-center justify-center font-semibold">
                          {patient.first_name?.[0]}{patient.last_name?.[0]}
                        </div>
                        <div>
                          <p className="font-medium text-slate-900">
                            {patient.first_name} {patient.last_name}
                          </p>
                          <p className="text-xs text-slate-500">DOB: {formatDate(patient.date_of_birth)}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="font-mono">{patient.mrn}</Badge>
                    </TableCell>
                    <TableCell>
                      <span className="text-slate-900">{calculateAge(patient.date_of_birth)} yrs</span>
                      <span className="text-slate-400 mx-1">•</span>
                      <span className="text-slate-600 capitalize">{patient.gender}</span>
                    </TableCell>
                    <TableCell>
                      {patient.phone && (
                        <div className="flex items-center gap-1 text-sm text-slate-600">
                          <Phone className="w-3 h-3" /> {patient.phone}
                        </div>
                      )}
                      {patient.email && (
                        <div className="flex items-center gap-1 text-sm text-slate-500 truncate max-w-[180px]">
                          <Mail className="w-3 h-3" /> {patient.email}
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      {patient.insurance_provider ? (
                        <span className="text-sm text-slate-600">{patient.insurance_provider}</span>
                      ) : (
                        <span className="text-sm text-slate-400">Not provided</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Button variant="ghost" size="sm">
                        <ChevronRight className="w-4 h-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
