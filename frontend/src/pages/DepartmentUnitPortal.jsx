import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import { patientAPI, departmentAPI } from '@/lib/api';
import { getErrorMessage } from '@/lib/utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import {
  Users, UserPlus, Search, Building2, MapPin, Loader2,
  AlertCircle, Phone, Mail, Calendar, CheckCircle,
  ClipboardList, Clock, RefreshCw, FileText, Eye,
  User, Hash, IdCard, Shield, Activity
} from 'lucide-react';

// Ghana-specific ID types
const GHANA_ID_TYPES = [
  { value: 'nhis', label: 'NHIS ID', description: 'National Health Insurance Scheme' },
  { value: 'ghana_card', label: 'Ghana Card', description: 'National Identification Number' },
  { value: 'passport', label: 'Passport', description: 'Ghana Passport Number' },
  { value: 'voter_id', label: 'Voter ID', description: 'Electoral Commission ID' },
  { value: 'drivers_license', label: "Driver's License", description: 'DVLA License Number' },
];

export default function DepartmentUnitPortal() {
  const { hospitalId, deptId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  // Department context
  const [department, setDepartment] = useState(null);
  const [departments, setDepartments] = useState([]);
  const [selectedDepartment, setSelectedDepartment] = useState(deptId || null);
  
  // Patient data
  const [patients, setPatients] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  
  // Loading states
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  // Dialogs
  const [addPatientOpen, setAddPatientOpen] = useState(false);
  const [viewPatientOpen, setViewPatientOpen] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState(null);
  
  // New patient form
  const [newPatient, setNewPatient] = useState({
    first_name: '',
    last_name: '',
    middle_name: '',
    date_of_birth: '',
    gender: 'male',
    phone: '',
    email: '',
    address: '',
    city: '',
    region: '',
    // Ghana-specific fields
    nhis_id: '',
    ghana_card_number: '',
    id_type: 'nhis',
    id_number: '',
    emergency_contact_name: '',
    emergency_contact_phone: '',
    emergency_contact_relationship: ''
  });

  // Access control
  const effectiveHospitalId = hospitalId || user?.organization_id;
  const allowedRoles = ['physician', 'nurse', 'admin', 'hospital_admin', 'records_officer', 'department_staff', 'scheduler'];
  const canAddPatient = allowedRoles.includes(user?.role);
  const canViewPatient = allowedRoles.includes(user?.role);

  // Fetch departments on load
  useEffect(() => {
    const fetchDepartments = async () => {
      try {
        const response = await departmentAPI.getAll();
        setDepartments(response.data || []);
        
        // If deptId is provided, fetch that department
        if (deptId) {
          const deptRes = await departmentAPI.getById(deptId);
          setDepartment(deptRes.data);
        }
      } catch (err) {
        console.error('Error fetching departments:', err);
      }
    };
    fetchDepartments();
  }, [deptId]);

  // Fetch patients for selected department
  const fetchPatients = useCallback(async () => {
    if (!selectedDepartment && !user?.department_id) return;
    
    try {
      setLoading(true);
      const response = await patientAPI.getAll({
        department_id: selectedDepartment || user?.department_id
      });
      setPatients(response.data || []);
    } catch (err) {
      console.error('Error fetching patients:', err);
      toast.error('Failed to load patients');
    } finally {
      setLoading(false);
    }
  }, [selectedDepartment, user?.department_id]);

  useEffect(() => {
    fetchPatients();
  }, [fetchPatients]);

  // Search patients
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    
    try {
      setSearching(true);
      const response = await patientAPI.getAll({ search: searchQuery });
      setSearchResults(response.data || []);
    } catch (err) {
      toast.error('Search failed');
    } finally {
      setSearching(false);
    }
  };

  // Add new patient
  const handleAddPatient = async (e) => {
    e.preventDefault();
    
    if (!newPatient.first_name || !newPatient.last_name) {
      toast.error('First name and last name are required');
      return;
    }
    
    try {
      setSaving(true);
      
      const patientData = {
        ...newPatient,
        department_id: selectedDepartment || user?.department_id,
        organization_id: effectiveHospitalId
      };
      
      const response = await patientAPI.create(patientData);
      
      toast.success('Patient registered successfully');
      setAddPatientOpen(false);
      setNewPatient({
        first_name: '',
        last_name: '',
        middle_name: '',
        date_of_birth: '',
        gender: 'male',
        phone: '',
        email: '',
        address: '',
        city: '',
        region: '',
        nhis_id: '',
        ghana_card_number: '',
        id_type: 'nhis',
        id_number: '',
        emergency_contact_name: '',
        emergency_contact_phone: '',
        emergency_contact_relationship: ''
      });
      fetchPatients();
    } catch (err) {
      console.error('Error adding patient:', err);
      toast.error(err.response?.data?.detail || 'Failed to register patient');
    } finally {
      setSaving(false);
    }
  };

  // View patient details (non-clinical only)
  const handleViewPatient = (patient) => {
    setSelectedPatient(patient);
    setViewPatientOpen(true);
  };

  const formatDate = (date) => {
    if (!date) return '-';
    return new Date(date).toLocaleDateString('en-GH', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const calculateAge = (dob) => {
    if (!dob) return '-';
    const today = new Date();
    const birth = new Date(dob);
    let age = today.getFullYear() - birth.getFullYear();
    const m = today.getMonth() - birth.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
    return age;
  };

  if (loading && patients.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Building2 className="w-6 h-6 text-emerald-600" />
            Department / Unit Portal
          </h1>
          <p className="text-gray-500 mt-1">
            Manage patient registrations for your department
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Select
            value={selectedDepartment || 'all'}
            onValueChange={(v) => setSelectedDepartment(v === 'all' ? null : v)}
          >
            <SelectTrigger className="w-[250px]">
              <SelectValue placeholder="Select Department" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Departments</SelectItem>
              {departments.map((dept) => (
                <SelectItem key={dept.id} value={dept.id}>
                  {dept.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button onClick={fetchPatients} variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Access Notice */}
      <Alert className="border-amber-200 bg-amber-50">
        <Shield className="h-4 w-4 text-amber-600" />
        <AlertTitle className="text-amber-800">Department Access Level</AlertTitle>
        <AlertDescription className="text-amber-700">
          This portal provides access to patient demographics and administrative data only.
          Clinical notes, diagnoses, orders, and prescriptions are not accessible here.
        </AlertDescription>
      </Alert>

      {/* Main Content */}
      <Tabs defaultValue="patients" className="space-y-4">
        <TabsList>
          <TabsTrigger value="patients" className="gap-2">
            <Users className="w-4 h-4" />
            Department Patients
          </TabsTrigger>
          <TabsTrigger value="search" className="gap-2">
            <Search className="w-4 h-4" />
            Search Patient
          </TabsTrigger>
          <TabsTrigger value="register" className="gap-2">
            <UserPlus className="w-4 h-4" />
            Register New
          </TabsTrigger>
        </TabsList>

        {/* Department Patients Tab */}
        <TabsContent value="patients">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Department Patient List</CardTitle>
                  <CardDescription>
                    Patients registered in {department?.name || 'your department'}
                  </CardDescription>
                </div>
                <Badge variant="outline" className="text-emerald-600">
                  {patients.length} Patients
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              {patients.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No patients registered in this department</p>
                  <Button 
                    className="mt-4" 
                    onClick={() => setAddPatientOpen(true)}
                    disabled={!canAddPatient}
                  >
                    <UserPlus className="w-4 h-4 mr-2" />
                    Register First Patient
                  </Button>
                </div>
              ) : (
                <div className="rounded-lg border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Patient Name</TableHead>
                        <TableHead>NHIS ID</TableHead>
                        <TableHead>Date of Birth</TableHead>
                        <TableHead>Age</TableHead>
                        <TableHead>Gender</TableHead>
                        <TableHead>Phone</TableHead>
                        <TableHead>Registration Date</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {patients.map((patient) => (
                        <TableRow key={patient.id}>
                          <TableCell className="font-medium">
                            {patient.first_name} {patient.middle_name || ''} {patient.last_name}
                          </TableCell>
                          <TableCell>
                            {patient.nhis_id || patient.insurance_id || '-'}
                          </TableCell>
                          <TableCell>{formatDate(patient.date_of_birth)}</TableCell>
                          <TableCell>{calculateAge(patient.date_of_birth)}</TableCell>
                          <TableCell className="capitalize">{patient.gender}</TableCell>
                          <TableCell>{patient.phone || '-'}</TableCell>
                          <TableCell>{formatDate(patient.created_at)}</TableCell>
                          <TableCell className="text-right">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleViewPatient(patient)}
                              disabled={!canViewPatient}
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Search Tab */}
        <TabsContent value="search">
          <Card>
            <CardHeader>
              <CardTitle>Search Existing Patient</CardTitle>
              <CardDescription>
                Search for patients by name, NHIS ID, Ghana Card, or phone number
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <Input
                    placeholder="Search by name, NHIS ID, Ghana Card, phone..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    className="pl-9"
                  />
                </div>
                <Button onClick={handleSearch} disabled={searching}>
                  {searching ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    'Search'
                  )}
                </Button>
              </div>

              {searchResults.length > 0 && (
                <div className="rounded-lg border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Patient Name</TableHead>
                        <TableHead>NHIS ID</TableHead>
                        <TableHead>Date of Birth</TableHead>
                        <TableHead>Phone</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {searchResults.map((patient) => (
                        <TableRow key={patient.id}>
                          <TableCell className="font-medium">
                            {patient.first_name} {patient.last_name}
                          </TableCell>
                          <TableCell>{patient.nhis_id || '-'}</TableCell>
                          <TableCell>{formatDate(patient.date_of_birth)}</TableCell>
                          <TableCell>{patient.phone || '-'}</TableCell>
                          <TableCell className="text-right">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleViewPatient(patient)}
                            >
                              <Eye className="w-4 h-4 mr-1" />
                              View
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}

              {searchQuery && searchResults.length === 0 && !searching && (
                <div className="text-center py-8 text-gray-500">
                  <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No patients found matching "{searchQuery}"</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Register New Patient Tab */}
        <TabsContent value="register">
          <Card>
            <CardHeader>
              <CardTitle>Register New Patient</CardTitle>
              <CardDescription>
                Add a new patient to the department. Ghana-specific identification supported.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!canAddPatient ? (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Access Denied</AlertTitle>
                  <AlertDescription>
                    You do not have permission to register new patients.
                  </AlertDescription>
                </Alert>
              ) : (
                <form onSubmit={handleAddPatient} className="space-y-6">
                  {/* Personal Information */}
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-4">Personal Information</h3>
                    <div className="grid md:grid-cols-3 gap-4">
                      <div>
                        <Label htmlFor="first_name">First Name *</Label>
                        <Input
                          id="first_name"
                          value={newPatient.first_name}
                          onChange={(e) => setNewPatient({ ...newPatient, first_name: e.target.value })}
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="middle_name">Middle Name</Label>
                        <Input
                          id="middle_name"
                          value={newPatient.middle_name}
                          onChange={(e) => setNewPatient({ ...newPatient, middle_name: e.target.value })}
                        />
                      </div>
                      <div>
                        <Label htmlFor="last_name">Last Name *</Label>
                        <Input
                          id="last_name"
                          value={newPatient.last_name}
                          onChange={(e) => setNewPatient({ ...newPatient, last_name: e.target.value })}
                          required
                        />
                      </div>
                      <div>
                        <Label htmlFor="date_of_birth">Date of Birth</Label>
                        <Input
                          id="date_of_birth"
                          type="date"
                          value={newPatient.date_of_birth}
                          onChange={(e) => setNewPatient({ ...newPatient, date_of_birth: e.target.value })}
                        />
                      </div>
                      <div>
                        <Label htmlFor="gender">Gender</Label>
                        <Select
                          value={newPatient.gender}
                          onValueChange={(v) => setNewPatient({ ...newPatient, gender: v })}
                        >
                          <SelectTrigger>
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

                  <Separator />

                  {/* Ghana Identification */}
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-4">Ghana Identification</h3>
                    <div className="grid md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="nhis_id">NHIS ID</Label>
                        <Input
                          id="nhis_id"
                          placeholder="National Health Insurance ID"
                          value={newPatient.nhis_id}
                          onChange={(e) => setNewPatient({ ...newPatient, nhis_id: e.target.value })}
                        />
                      </div>
                      <div>
                        <Label htmlFor="ghana_card_number">Ghana Card Number</Label>
                        <Input
                          id="ghana_card_number"
                          placeholder="GHA-XXXXXXXXX-X"
                          value={newPatient.ghana_card_number}
                          onChange={(e) => setNewPatient({ ...newPatient, ghana_card_number: e.target.value })}
                        />
                      </div>
                      <div>
                        <Label htmlFor="id_type">Alternative ID Type</Label>
                        <Select
                          value={newPatient.id_type}
                          onValueChange={(v) => setNewPatient({ ...newPatient, id_type: v })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {GHANA_ID_TYPES.map((type) => (
                              <SelectItem key={type.value} value={type.value}>
                                {type.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label htmlFor="id_number">ID Number</Label>
                        <Input
                          id="id_number"
                          value={newPatient.id_number}
                          onChange={(e) => setNewPatient({ ...newPatient, id_number: e.target.value })}
                        />
                      </div>
                    </div>
                  </div>

                  <Separator />

                  {/* Contact Information */}
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-4">Contact Information</h3>
                    <div className="grid md:grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="phone">Phone Number</Label>
                        <Input
                          id="phone"
                          placeholder="+233 XX XXX XXXX"
                          value={newPatient.phone}
                          onChange={(e) => setNewPatient({ ...newPatient, phone: e.target.value })}
                        />
                      </div>
                      <div>
                        <Label htmlFor="email">Email (Optional)</Label>
                        <Input
                          id="email"
                          type="email"
                          value={newPatient.email}
                          onChange={(e) => setNewPatient({ ...newPatient, email: e.target.value })}
                        />
                      </div>
                      <div className="md:col-span-2">
                        <Label htmlFor="address">Address</Label>
                        <Input
                          id="address"
                          placeholder="Street address"
                          value={newPatient.address}
                          onChange={(e) => setNewPatient({ ...newPatient, address: e.target.value })}
                        />
                      </div>
                      <div>
                        <Label htmlFor="city">City / Town</Label>
                        <Input
                          id="city"
                          value={newPatient.city}
                          onChange={(e) => setNewPatient({ ...newPatient, city: e.target.value })}
                        />
                      </div>
                      <div>
                        <Label htmlFor="region">Region</Label>
                        <Select
                          value={newPatient.region}
                          onValueChange={(v) => setNewPatient({ ...newPatient, region: v })}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select Region" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="greater-accra">Greater Accra</SelectItem>
                            <SelectItem value="ashanti">Ashanti</SelectItem>
                            <SelectItem value="central">Central</SelectItem>
                            <SelectItem value="eastern">Eastern</SelectItem>
                            <SelectItem value="western">Western</SelectItem>
                            <SelectItem value="western-north">Western North</SelectItem>
                            <SelectItem value="volta">Volta</SelectItem>
                            <SelectItem value="oti">Oti</SelectItem>
                            <SelectItem value="northern">Northern</SelectItem>
                            <SelectItem value="savannah">Savannah</SelectItem>
                            <SelectItem value="north-east">North East</SelectItem>
                            <SelectItem value="upper-east">Upper East</SelectItem>
                            <SelectItem value="upper-west">Upper West</SelectItem>
                            <SelectItem value="bono">Bono</SelectItem>
                            <SelectItem value="bono-east">Bono East</SelectItem>
                            <SelectItem value="ahafo">Ahafo</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </div>

                  <Separator />

                  {/* Emergency Contact */}
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-4">Emergency Contact</h3>
                    <div className="grid md:grid-cols-3 gap-4">
                      <div>
                        <Label htmlFor="emergency_contact_name">Contact Name</Label>
                        <Input
                          id="emergency_contact_name"
                          value={newPatient.emergency_contact_name}
                          onChange={(e) => setNewPatient({ ...newPatient, emergency_contact_name: e.target.value })}
                        />
                      </div>
                      <div>
                        <Label htmlFor="emergency_contact_phone">Contact Phone</Label>
                        <Input
                          id="emergency_contact_phone"
                          value={newPatient.emergency_contact_phone}
                          onChange={(e) => setNewPatient({ ...newPatient, emergency_contact_phone: e.target.value })}
                        />
                      </div>
                      <div>
                        <Label htmlFor="emergency_contact_relationship">Relationship</Label>
                        <Select
                          value={newPatient.emergency_contact_relationship}
                          onValueChange={(v) => setNewPatient({ ...newPatient, emergency_contact_relationship: v })}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="spouse">Spouse</SelectItem>
                            <SelectItem value="parent">Parent</SelectItem>
                            <SelectItem value="child">Child</SelectItem>
                            <SelectItem value="sibling">Sibling</SelectItem>
                            <SelectItem value="relative">Other Relative</SelectItem>
                            <SelectItem value="friend">Friend</SelectItem>
                            <SelectItem value="other">Other</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-end gap-3 pt-4">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setNewPatient({
                        first_name: '', last_name: '', middle_name: '',
                        date_of_birth: '', gender: 'male', phone: '', email: '',
                        address: '', city: '', region: '', nhis_id: '',
                        ghana_card_number: '', id_type: 'nhis', id_number: '',
                        emergency_contact_name: '', emergency_contact_phone: '',
                        emergency_contact_relationship: ''
                      })}
                    >
                      Clear Form
                    </Button>
                    <Button type="submit" disabled={saving} className="bg-emerald-600 hover:bg-emerald-700">
                      {saving ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Registering...
                        </>
                      ) : (
                        <>
                          <UserPlus className="w-4 h-4 mr-2" />
                          Register Patient
                        </>
                      )}
                    </Button>
                  </div>
                </form>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* View Patient Details Dialog (Non-Clinical Only) */}
      <Dialog open={viewPatientOpen} onOpenChange={setViewPatientOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <User className="w-5 h-5 text-emerald-600" />
              Patient Information
            </DialogTitle>
            <DialogDescription>
              Demographic and administrative details only. Clinical records not accessible.
            </DialogDescription>
          </DialogHeader>
          
          {selectedPatient && (
            <div className="space-y-6">
              {/* Basic Info */}
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <Label className="text-xs text-gray-500">Full Name</Label>
                  <p className="font-medium">
                    {selectedPatient.first_name} {selectedPatient.middle_name || ''} {selectedPatient.last_name}
                  </p>
                </div>
                <div className="space-y-1">
                  <Label className="text-xs text-gray-500">Date of Birth / Age</Label>
                  <p className="font-medium">
                    {formatDate(selectedPatient.date_of_birth)} ({calculateAge(selectedPatient.date_of_birth)} years)
                  </p>
                </div>
                <div className="space-y-1">
                  <Label className="text-xs text-gray-500">Gender</Label>
                  <p className="font-medium capitalize">{selectedPatient.gender}</p>
                </div>
                <div className="space-y-1">
                  <Label className="text-xs text-gray-500">MRN</Label>
                  <p className="font-medium">{selectedPatient.mrn || selectedPatient.id}</p>
                </div>
              </div>

              <Separator />

              {/* Ghana IDs */}
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <Label className="text-xs text-gray-500 flex items-center gap-1">
                    <IdCard className="w-3 h-3" />
                    NHIS ID
                  </Label>
                  <p className="font-medium">{selectedPatient.nhis_id || selectedPatient.insurance_id || '-'}</p>
                </div>
                <div className="space-y-1">
                  <Label className="text-xs text-gray-500 flex items-center gap-1">
                    <IdCard className="w-3 h-3" />
                    Ghana Card
                  </Label>
                  <p className="font-medium">{selectedPatient.ghana_card_number || '-'}</p>
                </div>
              </div>

              <Separator />

              {/* Contact */}
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <Label className="text-xs text-gray-500 flex items-center gap-1">
                    <Phone className="w-3 h-3" />
                    Phone
                  </Label>
                  <p className="font-medium">{selectedPatient.phone || '-'}</p>
                </div>
                <div className="space-y-1">
                  <Label className="text-xs text-gray-500 flex items-center gap-1">
                    <Mail className="w-3 h-3" />
                    Email
                  </Label>
                  <p className="font-medium">{selectedPatient.email || '-'}</p>
                </div>
                <div className="md:col-span-2 space-y-1">
                  <Label className="text-xs text-gray-500 flex items-center gap-1">
                    <MapPin className="w-3 h-3" />
                    Address
                  </Label>
                  <p className="font-medium">
                    {selectedPatient.address || '-'}
                    {selectedPatient.city && `, ${selectedPatient.city}`}
                    {selectedPatient.region && `, ${selectedPatient.region}`}
                  </p>
                </div>
              </div>

              {/* Notice */}
              <Alert className="border-blue-200 bg-blue-50">
                <Shield className="h-4 w-4 text-blue-600" />
                <AlertDescription className="text-blue-700 text-sm">
                  Clinical records, diagnoses, orders, and prescriptions are not accessible from this portal.
                  Contact a clinician for medical information.
                </AlertDescription>
              </Alert>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setViewPatientOpen(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
