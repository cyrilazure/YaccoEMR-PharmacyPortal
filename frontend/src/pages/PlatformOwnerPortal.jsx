import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import { regionAPI, adminAPI, organizationAPI } from '@/lib/api';
import { hasPermission, PERMISSIONS } from '@/lib/permissions';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Dialog, DialogContent, DialogDescription, 
  DialogHeader, DialogTitle, DialogFooter,
  DialogTrigger
} from '@/components/ui/dialog';
import { 
  Select, SelectContent, SelectItem, 
  SelectTrigger, SelectValue 
} from '@/components/ui/select';
import { 
  Table, TableBody, TableCell, 
  TableHead, TableHeader, TableRow 
} from '@/components/ui/table';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import { 
  Building2, MapPin, Users, Plus, LogIn, Search, 
  RefreshCw, Globe, Settings, Shield, Activity,
  ChevronRight, ExternalLink, Eye, Copy, Check,
  AlertCircle, CheckCircle, Clock, Loader2,
  Hospital, UserCog, BarChart3, Trash2, AlertTriangle,
  Ban, Power, XCircle, Pill, Store, FileText
} from 'lucide-react';
import api from '@/lib/api';

// Ghana Regions for dropdown
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

export default function PlatformOwnerPortal() {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  // All hooks MUST be declared before any conditional returns (React rules of hooks)
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Data
  const [overview, setOverview] = useState(null);
  const [hospitals, setHospitals] = useState([]);
  const [pendingHospitals, setPendingHospitals] = useState([]);
  const [approvedOrganizations, setApprovedOrganizations] = useState([]);
  const [regions, setRegions] = useState([]);
  
  // Filters
  const [selectedRegion, setSelectedRegion] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Dialogs
  const [createHospitalOpen, setCreateHospitalOpen] = useState(false);
  const [loginAsOpen, setLoginAsOpen] = useState(false);
  const [selectedHospital, setSelectedHospital] = useState(null);
  const [copiedPassword, setCopiedPassword] = useState(null);
  
  // Staff creation dialog
  const [createStaffOpen, setCreateStaffOpen] = useState(false);
  const [staffHospital, setStaffHospital] = useState(null);
  const [hospitalDepartments, setHospitalDepartments] = useState([]);
  const [newStaff, setNewStaff] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    role: 'physician',
    department_id: '',
    employee_id: ''
  });
  const [createdStaff, setCreatedStaff] = useState(null);
  
  // Hospital deletion dialog
  const [deleteHospitalOpen, setDeleteHospitalOpen] = useState(false);
  const [hospitalToDelete, setHospitalToDelete] = useState(null);
  const [deleteConfirmation, setDeleteConfirmation] = useState('');
  const [deleting, setDeleting] = useState(false);
  
  // Hospital status management
  const [statusChangeOpen, setStatusChangeOpen] = useState(false);
  const [hospitalToChangeStatus, setHospitalToChangeStatus] = useState(null);
  
  // Pharmacy approval management
  const [pendingPharmacies, setPendingPharmacies] = useState([]);
  const [approvedPharmacies, setApprovedPharmacies] = useState([]);
  const [pharmacyLoading, setPharmacyLoading] = useState(false);
  const [selectedPharmacyDetails, setSelectedPharmacyDetails] = useState(null);
  const [pharmacyDetailsOpen, setPharmacyDetailsOpen] = useState(false);
  const [approvalNotes, setApprovalNotes] = useState('');
  
  // Forms
  const [newHospital, setNewHospital] = useState({
    name: '',
    region_id: '',
    address: '',
    city: '',
    phone: '',
    email: '',
    license_number: '',
    ghana_health_service_id: '',
    admin_first_name: '',
    admin_last_name: '',
    admin_email: '',
    admin_phone: ''
  });
  const [createdHospital, setCreatedHospital] = useState(null);
  const [saving, setSaving] = useState(false);

  const isSuperAdmin = user?.role === 'super_admin';

  const fetchData = useCallback(async () => {
    if (!isSuperAdmin) return;
    try {
      setLoading(true);
      const [overviewRes, regionsRes, hospitalsRes, pendingOrgsRes, allOrgsRes] = await Promise.all([
        regionAPI.getPlatformOverview(),
        regionAPI.getRegions(),
        regionAPI.getHospitalAdmins(selectedRegion === 'all' ? null : selectedRegion),
        organizationAPI.getPending().catch(() => ({ data: { organizations: [] } })),
        organizationAPI.getOrganizations().catch(() => ({ data: { organizations: [] } }))
      ]);
      
      setOverview(overviewRes.data);
      setRegions(regionsRes.data.regions || []);
      setHospitals(hospitalsRes.data.hospitals || []);
      
      // Get pending and approved organizations from registration workflow
      const allOrgs = allOrgsRes.data.organizations || allOrgsRes.data || [];
      setPendingHospitals(allOrgs.filter(o => o.status === 'pending'));
      setApprovedOrganizations(allOrgs.filter(o => o.status === 'active' || o.status === 'approved'));
    } catch (err) {
      console.error('Error fetching data:', err);
      toast.error('Failed to load platform data');
    } finally {
      setLoading(false);
    }
  }, [selectedRegion, isSuperAdmin]);

  // Fetch pharmacies data
  const fetchPharmacies = useCallback(async () => {
    if (!isSuperAdmin) return;
    try {
      setPharmacyLoading(true);
      const [pendingRes, allRes] = await Promise.all([
        api.get('/pharmacy-portal/admin/pharmacies/pending'),
        api.get('/pharmacy-portal/public/pharmacies', { params: { limit: 100 } })
      ]);
      setPendingPharmacies(pendingRes.data.pharmacies || []);
      setApprovedPharmacies(allRes.data.pharmacies?.filter(p => p.status === 'approved') || []);
    } catch (err) {
      console.error('Error fetching pharmacies:', err);
    } finally {
      setPharmacyLoading(false);
    }
  }, [isSuperAdmin]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (activeTab === 'pharmacies') {
      fetchPharmacies();
    }
  }, [activeTab, fetchPharmacies]);

  // Check if user is super admin (after all hooks are declared)
  if (!isSuperAdmin) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Alert variant="destructive" className="max-w-md">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Access Denied</AlertTitle>
          <AlertDescription>
            You must be a Platform Owner (Super Admin) to access this page.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const handleCreateHospital = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const response = await regionAPI.createHospital(newHospital);
      setCreatedHospital(response.data);
      toast.success('Hospital created successfully!');
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create hospital');
    } finally {
      setSaving(false);
    }
  };

  const handleLoginAsHospital = async (hospital) => {
    try {
      setSaving(true);
      const response = await regionAPI.loginAsHospital(hospital.hospital.id);
      
      // Store the impersonation token
      localStorage.setItem('yacco_token', response.data.token);
      localStorage.setItem('yacco_user', JSON.stringify(response.data.user));
      localStorage.setItem('yacco_hospital', JSON.stringify(response.data.hospital));
      localStorage.setItem('yacco_impersonation', JSON.stringify(response.data.impersonation));
      
      toast.success(`Now logged in as ${response.data.hospital.name}`);
      
      // Redirect to admin dashboard
      window.location.href = response.data.redirect_to;
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to login as hospital');
    } finally {
      setSaving(false);
    }
  };

  // Helper to extract error message from API response
  const getErrorMessage = (err, defaultMsg) => {
    const detail = err.response?.data?.detail;
    if (typeof detail === 'string') {
      return detail;
    } else if (Array.isArray(detail)) {
      // Extract field names from validation errors
      const fields = detail.map(e => e.loc?.[e.loc.length - 1] || 'field').join(', ');
      return `Validation error: ${fields}`;
    }
    return defaultMsg;
  };

  // Approve pending hospital registration
  const handleApproveHospital = async (hospitalId) => {
    try {
      setSaving(true);
      await organizationAPI.approve(hospitalId, {});
      toast.success('Hospital approved successfully!');
      fetchData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to approve hospital'));
    } finally {
      setSaving(false);
    }
  };

  // Reject pending hospital registration
  const handleRejectHospital = async (hospitalId) => {
    try {
      setSaving(true);
      await organizationAPI.reject(hospitalId, { reason: 'Rejected by Platform Owner' });
      toast.success('Hospital registration rejected');
      fetchData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to reject hospital'));
    } finally {
      setSaving(false);
    }
  };

  // Create hospital staff
  const handleCreateStaff = async (e) => {
    e.preventDefault();
    if (!staffHospital) {
      toast.error('Please select a hospital first');
      return;
    }
    
    setSaving(true);
    try {
      const response = await regionAPI.createHospitalStaff(staffHospital.hospital.id, newStaff);
      setCreatedStaff(response.data);
      toast.success('Staff account created successfully!');
      setNewStaff({
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        role: 'physician',
        department_id: '',
        employee_id: ''
      });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create staff account');
    } finally {
      setSaving(false);
    }
  };

  const openStaffDialog = async (hospital) => {
    setStaffHospital(hospital);
    setCreatedStaff(null);
    setHospitalDepartments([]);
    setCreateStaffOpen(true);
    
    // Fetch departments for the selected hospital
    try {
      const response = await regionAPI.getHospitalDepartments(hospital.hospital.id);
      setHospitalDepartments(response.data.departments || []);
    } catch (err) {
      console.error('Failed to fetch hospital departments:', err);
      // If endpoint doesn't exist, don't show error - departments are optional
    }
  };

  // Pharmacy Approval/Rejection Handlers
  const handleApprovePharmacy = async (pharmacyId) => {
    try {
      await api.put(`/pharmacy-portal/admin/pharmacies/${pharmacyId}/approve`, {
        status: 'approved',
        notes: approvalNotes || 'Approved by Platform Admin'
      });
      toast.success('Pharmacy approved successfully');
      setPharmacyDetailsOpen(false);
      setApprovalNotes('');
      fetchPharmacies();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to approve pharmacy');
    }
  };

  const handleRejectPharmacy = async (pharmacyId) => {
    if (!approvalNotes) {
      toast.error('Please provide a reason for rejection');
      return;
    }
    try {
      await api.put(`/pharmacy-portal/admin/pharmacies/${pharmacyId}/approve`, {
        status: 'rejected',
        notes: approvalNotes
      });
      toast.success('Pharmacy registration rejected');
      setPharmacyDetailsOpen(false);
      setApprovalNotes('');
      fetchPharmacies();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to reject pharmacy');
    }
  };

  const openPharmacyDetails = (pharmacy) => {
    setSelectedPharmacyDetails(pharmacy);
    setApprovalNotes('');
    setPharmacyDetailsOpen(true);
  };

  // Hospital Deletion (Soft Delete with Safeguards)
  const handleDeleteHospital = async () => {
    if (!hospitalToDelete) return;
    
    // Verify confirmation text matches hospital name
    if (deleteConfirmation !== hospitalToDelete.hospital.name) {
      toast.error('Please type the hospital name exactly to confirm deletion');
      return;
    }
    
    setDeleting(true);
    try {
      await regionAPI.deleteHospital(hospitalToDelete.hospital.id);
      toast.success(`Hospital "${hospitalToDelete.hospital.name}" has been deactivated`);
      setDeleteHospitalOpen(false);
      setHospitalToDelete(null);
      setDeleteConfirmation('');
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete hospital');
    } finally {
      setDeleting(false);
    }
  };

  // Hospital Status Change (Activate/Suspend/Deactivate)
  const handleChangeHospitalStatus = async (status) => {
    if (!hospitalToChangeStatus) return;
    
    try {
      setSaving(true);
      await regionAPI.updateHospitalStatus(hospitalToChangeStatus.hospital.id, { status });
      toast.success(`Hospital status changed to ${status}`);
      setStatusChangeOpen(false);
      setHospitalToChangeStatus(null);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to change hospital status');
    } finally {
      setSaving(false);
    }
  };

  const copyToClipboard = async (text, id) => {
    await navigator.clipboard.writeText(text);
    setCopiedPassword(id);
    setTimeout(() => setCopiedPassword(null), 2000);
    toast.success('Copied to clipboard!');
  };

  const filteredHospitals = hospitals.filter(h => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      h.hospital.name.toLowerCase().includes(query) ||
      h.hospital.city?.toLowerCase().includes(query) ||
      h.admin?.email?.toLowerCase().includes(query)
    );
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white">
        <div className="container mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <div className="w-12 h-12 rounded-xl bg-white/20 flex items-center justify-center">
                  <Shield className="w-7 h-7" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold">Platform Owner Portal</h1>
                  <p className="text-emerald-100">Ghana Healthcare Network Administration</p>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <Badge variant="secondary" className="bg-white/20 text-white border-0">
                {user?.email}
              </Badge>
              <Button 
                variant="outline" 
                className="border-white/30 text-white hover:bg-white/20"
                onClick={fetchData}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 py-8">
        {/* Overview Cards */}
        {overview && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">Total Hospitals</p>
                    <p className="text-3xl font-bold text-emerald-600">{overview.totals?.hospitals || 0}</p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center">
                    <Hospital className="w-6 h-6 text-emerald-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">Total Users</p>
                    <p className="text-3xl font-bold text-blue-600">{overview.totals?.users || 0}</p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
                    <Users className="w-6 h-6 text-blue-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">Total Locations</p>
                    <p className="text-3xl font-bold text-purple-600">{overview.totals?.locations || 0}</p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-purple-100 flex items-center justify-center">
                    <MapPin className="w-6 h-6 text-purple-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">Active Regions</p>
                    <p className="text-3xl font-bold text-orange-600">
                      {overview.regions?.filter(r => r.hospital_count > 0).length || 0}/16
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-full bg-orange-100 flex items-center justify-center">
                    <Globe className="w-6 h-6 text-orange-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Main Content */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-6">
            <TabsTrigger value="overview" className="gap-2">
              <BarChart3 className="w-4 h-4" /> Overview
            </TabsTrigger>
            <TabsTrigger value="hospitals" className="gap-2">
              <Hospital className="w-4 h-4" /> Hospitals
            </TabsTrigger>
            <TabsTrigger value="pharmacies" className="gap-2">
              <Store className="w-4 h-4" /> Pharmacies
              {pendingPharmacies.length > 0 && (
                <Badge className="ml-1 bg-red-500 text-white text-xs">{pendingPharmacies.length}</Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="staff" className="gap-2">
              <UserCog className="w-4 h-4" /> Staff
            </TabsTrigger>
            <TabsTrigger value="regions" className="gap-2">
              <Globe className="w-4 h-4" /> Regions
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Hospitals by Region */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MapPin className="w-5 h-5 text-emerald-600" />
                    Hospitals by Region
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[400px]">
                    <div className="space-y-3">
                      {overview?.regions?.filter(r => r.hospital_count > 0).map((region) => (
                        <div key={region.id} className="flex items-center justify-between p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors">
                          <div>
                            <p className="font-medium">{region.name}</p>
                            <p className="text-sm text-gray-500">Capital: {region.capital}</p>
                          </div>
                          <div className="text-right">
                            <Badge variant="secondary">{region.hospital_count} hospitals</Badge>
                            <p className="text-xs text-gray-400 mt-1">{region.user_count || 0} users</p>
                          </div>
                        </div>
                      ))}
                      {overview?.regions?.filter(r => r.hospital_count === 0).length > 0 && (
                        <div className="pt-4 border-t">
                          <p className="text-sm text-gray-500 mb-2">Regions without hospitals:</p>
                          <div className="flex flex-wrap gap-2">
                            {overview?.regions?.filter(r => r.hospital_count === 0).map((region) => (
                              <Badge key={region.id} variant="outline" className="text-xs">
                                {region.name}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>

              {/* Role Distribution */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="w-5 h-5 text-blue-600" />
                    Staff Distribution
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {overview?.role_distribution && Object.entries(overview.role_distribution).map(([role, count]) => (
                      <div key={role} className="flex items-center gap-4">
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-sm font-medium capitalize">{role.replace('_', ' ')}</span>
                            <span className="text-sm text-gray-500">{count}</span>
                          </div>
                          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-emerald-500 rounded-full transition-all"
                              style={{ width: `${(count / (overview.totals?.users || 1)) * 100}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Hospitals Tab */}
          <TabsContent value="hospitals">
            <div className="space-y-6">
              {/* Pending Hospital Approvals Section */}
              <Card className="border-amber-200 bg-amber-50/30">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2 text-amber-800">
                        <Clock className="w-5 h-5" />
                        Pending Hospital Approvals ({pendingHospitals.length})
                      </CardTitle>
                      <CardDescription>Review and approve hospital registrations</CardDescription>
                    </div>
                    <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
                      <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                      Refresh
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {loading ? (
                    <div className="flex items-center justify-center py-12">
                      <Loader2 className="w-8 h-8 animate-spin text-amber-600" />
                    </div>
                  ) : pendingHospitals.length === 0 ? (
                    <div className="text-center py-12 text-slate-500">
                      <CheckCircle className="w-16 h-16 mx-auto mb-4 text-emerald-400" />
                      <p className="font-medium">All caught up!</p>
                      <p className="text-sm">No pending hospital registrations to review</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {pendingHospitals.map((hospital) => (
                        <div key={hospital.id} className="p-4 bg-white rounded-lg border border-amber-200 hover:border-amber-300 transition-colors">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
                                  <Hospital className="w-5 h-5 text-amber-600" />
                                </div>
                                <div>
                                  <h4 className="font-semibold text-slate-900">{hospital.name}</h4>
                                  <p className="text-sm text-slate-500">
                                    License: {hospital.license_number || '-'}
                                  </p>
                                </div>
                              </div>
                              <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                                <div>
                                  <p className="text-slate-400">Type</p>
                                  <p className="font-medium">{hospital.organization_type || hospital.type || 'Hospital'}</p>
                                </div>
                                <div>
                                  <p className="text-slate-400">Region</p>
                                  <p className="font-medium">{hospital.state || hospital.region || '-'}</p>
                                </div>
                                <div>
                                  <p className="text-slate-400">City</p>
                                  <p className="font-medium">{hospital.city || '-'}</p>
                                </div>
                                <div>
                                  <p className="text-slate-400">Contact</p>
                                  <p className="font-medium text-xs">{hospital.email || hospital.admin_email || '-'}</p>
                                </div>
                              </div>
                              <p className="mt-2 text-xs text-slate-400">
                                Registered: {hospital.created_at ? new Date(hospital.created_at).toLocaleDateString() : '-'}
                              </p>
                            </div>
                            <div className="flex gap-2 ml-4">
                              <Button 
                                size="sm" 
                                className="bg-emerald-600 hover:bg-emerald-700"
                                onClick={() => handleApproveHospital(hospital.id)}
                                disabled={saving}
                              >
                                <CheckCircle className="w-4 h-4 mr-1" /> Approve
                              </Button>
                              <Button 
                                size="sm" 
                                variant="destructive"
                                onClick={() => handleRejectHospital(hospital.id)}
                                disabled={saving}
                              >
                                <XCircle className="w-4 h-4 mr-1" /> Reject
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Approved Hospitals Section */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <CheckCircle className="w-5 h-5 text-emerald-600" />
                        Approved Hospitals ({hospitals.length})
                      </CardTitle>
                      <CardDescription>Create and manage hospital accounts</CardDescription>
                    </div>
                    <Dialog open={createHospitalOpen} onOpenChange={setCreateHospitalOpen}>
                      <DialogTrigger asChild>
                        <Button className="bg-emerald-600 hover:bg-emerald-700">
                          <Plus className="w-4 h-4 mr-2" />
                          Add Hospital
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                        <DialogHeader>
                          <DialogTitle>Create New Hospital</DialogTitle>
                          <DialogDescription>
                            Register a new hospital in the Ghana Healthcare Network
                          </DialogDescription>
                        </DialogHeader>
                        
                        {createdHospital ? (
                          <div className="space-y-4">
                            <Alert className="bg-emerald-50 border-emerald-200">
                              <CheckCircle className="h-4 w-4 text-emerald-600" />
                              <AlertTitle className="text-emerald-800">Hospital Created Successfully!</AlertTitle>
                              <AlertDescription className="text-emerald-700">
                                Save the admin credentials below - the password cannot be retrieved later.
                              </AlertDescription>
                            </Alert>
                            
                            <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                              <h4 className="font-semibold">Hospital Details</h4>
                              <p><strong>Name:</strong> {createdHospital.hospital?.name}</p>
                              <p><strong>ID:</strong> {createdHospital.hospital?.id}</p>
                            </div>
                            
                            <div className="bg-blue-50 rounded-lg p-4 space-y-3">
                              <h4 className="font-semibold text-blue-800">Admin Credentials</h4>
                              <div className="flex items-center justify-between">
                                <div>
                                  <p><strong>Email:</strong> {createdHospital.admin?.email}</p>
                                  <p><strong>Password:</strong> {createdHospital.admin?.temp_password}</p>
                                </div>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => copyToClipboard(
                                    `Email: ${createdHospital.admin?.email}\nPassword: ${createdHospital.admin?.temp_password}`,
                                    'new'
                                  )}
                                >
                                  {copiedPassword === 'new' ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                                </Button>
                              </div>
                            </div>
                            
                            <DialogFooter>
                              <Button onClick={() => {
                                setCreatedHospital(null);
                                setCreateHospitalOpen(false);
                                setNewHospital({
                                  name: '', region_id: '', address: '', city: '', phone: '', email: '',
                                  license_number: '', ghana_health_service_id: '',
                                  admin_first_name: '', admin_last_name: '', admin_email: '', admin_phone: ''
                                });
                              }}>
                                Done
                              </Button>
                            </DialogFooter>
                          </div>
                        ) : (
                          <form onSubmit={handleCreateHospital} className="space-y-6">
                            <div className="grid grid-cols-2 gap-4">
                              <div className="col-span-2">
                                <Label>Hospital Name *</Label>
                                <Input
                                  value={newHospital.name}
                                  onChange={(e) => setNewHospital({...newHospital, name: e.target.value})}
                                  placeholder="e.g., Accra Regional Hospital"
                                  required
                                />
                              </div>
                              
                              <div>
                                <Label>Region *</Label>
                                <Select
                                  value={newHospital.region_id}
                                  onValueChange={(v) => setNewHospital({...newHospital, region_id: v})}
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
                                  value={newHospital.city}
                                  onChange={(e) => setNewHospital({...newHospital, city: e.target.value})}
                                  placeholder="e.g., Accra"
                                  required
                                />
                              </div>
                              
                              <div className="col-span-2">
                                <Label>Address *</Label>
                                <Input
                                  value={newHospital.address}
                                  onChange={(e) => setNewHospital({...newHospital, address: e.target.value})}
                                  placeholder="Street address"
                                  required
                                />
                              </div>
                              
                              <div>
                                <Label>Phone</Label>
                                <Input
                                  value={newHospital.phone}
                                  onChange={(e) => setNewHospital({...newHospital, phone: e.target.value})}
                                  placeholder="+233-XXX-XXXXXX"
                                />
                              </div>
                              
                              <div>
                                <Label>Email</Label>
                                <Input
                                  type="email"
                                  value={newHospital.email}
                                  onChange={(e) => setNewHospital({...newHospital, email: e.target.value})}
                                  placeholder="hospital@domain.com"
                                />
                              </div>
                              
                              <div>
                                <Label>License Number *</Label>
                                <Input
                                  value={newHospital.license_number}
                                  onChange={(e) => setNewHospital({...newHospital, license_number: e.target.value})}
                                  placeholder="HFR-XXXX-XXXX"
                                  required
                                />
                              </div>
                              
                              <div>
                                <Label>GHS ID</Label>
                                <Input
                                  value={newHospital.ghana_health_service_id}
                                  onChange={(e) => setNewHospital({...newHospital, ghana_health_service_id: e.target.value})}
                                  placeholder="Ghana Health Service ID"
                                />
                              </div>
                            </div>
                            
                            <Separator />
                            
                            <div>
                              <h4 className="font-medium mb-4">Hospital Administrator</h4>
                              <div className="grid grid-cols-2 gap-4">
                                <div>
                                  <Label>First Name *</Label>
                                  <Input
                                    value={newHospital.admin_first_name}
                                    onChange={(e) => setNewHospital({...newHospital, admin_first_name: e.target.value})}
                                    required
                                  />
                                </div>
                                <div>
                                  <Label>Last Name *</Label>
                                  <Input
                                    value={newHospital.admin_last_name}
                                    onChange={(e) => setNewHospital({...newHospital, admin_last_name: e.target.value})}
                                    required
                                  />
                                </div>
                                <div>
                                  <Label>Admin Email *</Label>
                                  <Input
                                    type="email"
                                    value={newHospital.admin_email}
                                    onChange={(e) => setNewHospital({...newHospital, admin_email: e.target.value})}
                                    placeholder="admin@hospital.gov.gh"
                                    required
                                  />
                                </div>
                                <div>
                                  <Label>Admin Phone *</Label>
                                  <Input
                                    value={newHospital.admin_phone}
                                    onChange={(e) => setNewHospital({...newHospital, admin_phone: e.target.value})}
                                    placeholder="+233-XXX-XXXXXX"
                                    required
                                  />
                                </div>
                              </div>
                            </div>
                            
                            <DialogFooter>
                              <Button type="button" variant="outline" onClick={() => setCreateHospitalOpen(false)}>
                                Cancel
                              </Button>
                              <Button type="submit" className="bg-emerald-600 hover:bg-emerald-700" disabled={saving}>
                                {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Plus className="w-4 h-4 mr-2" />}
                                Create Hospital
                              </Button>
                            </DialogFooter>
                          </form>
                        )}
                      </DialogContent>
                    </Dialog>
                  </div>
                </CardHeader>
                
                <CardContent>
                  {/* Filters */}
                  <div className="flex items-center gap-4 mb-6">
                    <div className="relative flex-1 max-w-sm">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <Input
                        placeholder="Search hospitals..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-9"
                      />
                    </div>
                    <Select value={selectedRegion} onValueChange={setSelectedRegion}>
                      <SelectTrigger className="w-[200px]">
                        <SelectValue placeholder="Filter by region" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Regions</SelectItem>
                        {GHANA_REGIONS.map((r) => (
                          <SelectItem key={r.id} value={r.id}>{r.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Hospitals Table */}
                  {loading ? (
                    <div className="flex justify-center py-12">
                      <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
                    </div>
                  ) : (
                    <div className="rounded-lg border">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Hospital</TableHead>
                            <TableHead>Region</TableHead>
                            <TableHead>Admin</TableHead>
                            <TableHead className="text-center">Locations</TableHead>
                            <TableHead className="text-center">Users</TableHead>
                            <TableHead className="text-right">Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {filteredHospitals.map((item) => (
                            <TableRow key={item.hospital.id}>
                              <TableCell>
                                <div>
                                  <p className="font-medium">{item.hospital.name}</p>
                                  <p className="text-sm text-gray-500">{item.hospital.city}</p>
                                </div>
                              </TableCell>
                              <TableCell>
                                <Badge variant="outline">
                                  {GHANA_REGIONS.find(r => r.id === item.hospital.region_id)?.name?.replace(' Region', '') || item.hospital.region_id}
                                </Badge>
                              </TableCell>
                              <TableCell>
                                {item.admin ? (
                                  <div>
                                    <p className="text-sm">{item.admin.name}</p>
                                    <p className="text-xs text-gray-500">{item.admin.email}</p>
                                  </div>
                                ) : (
                                  <span className="text-gray-400">No admin</span>
                                )}
                              </TableCell>
                              <TableCell className="text-center">
                                <Badge variant="secondary">{item.hospital.location_count}</Badge>
                              </TableCell>
                              <TableCell className="text-center">
                                <Badge variant="secondary">{item.hospital.user_count}</Badge>
                              </TableCell>
                              <TableCell className="text-right">
                                <div className="flex items-center justify-end gap-2">
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => handleLoginAsHospital(item)}
                                    disabled={saving}
                                  >
                                    <LogIn className="w-4 h-4 mr-1" />
                                    Login As
                                  </Button>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => {
                                      setHospitalToChangeStatus(item);
                                      setStatusChangeOpen(true);
                                    }}
                                  >
                                    <Power className="w-4 h-4" />
                                  </Button>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                    onClick={() => {
                                      setHospitalToDelete(item);
                                      setDeleteConfirmation('');
                                      setDeleteHospitalOpen(true);
                                    }}
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </Button>
                                </div>
                              </TableCell>
                            </TableRow>
                          ))}
                          {filteredHospitals.length === 0 && (
                            <TableRow>
                              <TableCell colSpan={6} className="text-center py-12 text-gray-500">
                                No hospitals found
                              </TableCell>
                            </TableRow>
                          )}
                        </TableBody>
                      </Table>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Staff Tab - Create Staff for Any Hospital */}
          <TabsContent value="staff">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <UserCog className="w-5 h-5 text-emerald-600" />
                      Hospital Staff Management
                    </CardTitle>
                    <CardDescription>Create staff accounts for any hospital in the platform</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Alert className="mb-6 border-blue-200 bg-blue-50">
                  <Shield className="h-4 w-4 text-blue-600" />
                  <AlertDescription className="text-blue-700">
                    As Platform Owner, you can create staff accounts for any hospital. 
                    Select a hospital first, then fill in the staff details.
                  </AlertDescription>
                </Alert>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Select Hospital */}
                  <Card className="border-2 border-dashed">
                    <CardHeader>
                      <CardTitle className="text-lg">1. Select Hospital</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ScrollArea className="h-[400px]">
                        <div className="space-y-2">
                          {hospitals.map((item) => (
                            <div
                              key={item.hospital.id}
                              onClick={() => setStaffHospital(item)}
                              className={`p-4 rounded-lg border cursor-pointer transition-all ${
                                staffHospital?.hospital.id === item.hospital.id
                                  ? 'border-emerald-500 bg-emerald-50'
                                  : 'border-gray-200 hover:border-emerald-300 hover:bg-gray-50'
                              }`}
                            >
                              <div className="flex items-center justify-between">
                                <div>
                                  <p className="font-medium">{item.hospital.name}</p>
                                  <p className="text-sm text-gray-500">{item.hospital.city}</p>
                                </div>
                                {staffHospital?.hospital.id === item.hospital.id && (
                                  <CheckCircle className="w-5 h-5 text-emerald-600" />
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </ScrollArea>
                    </CardContent>
                  </Card>

                  {/* Create Staff Form */}
                  <Card className={`border-2 ${staffHospital ? 'border-emerald-200' : 'border-dashed opacity-50'}`}>
                    <CardHeader>
                      <CardTitle className="text-lg">2. Create Staff Account</CardTitle>
                      {staffHospital && (
                        <Badge className="w-fit bg-emerald-100 text-emerald-700">
                          {staffHospital.hospital.name}
                        </Badge>
                      )}
                    </CardHeader>
                    <CardContent>
                      {createdStaff ? (
                        <div className="space-y-4">
                          <Alert className="border-emerald-200 bg-emerald-50">
                            <CheckCircle className="h-4 w-4 text-emerald-600" />
                            <AlertTitle className="text-emerald-800">Staff Created Successfully!</AlertTitle>
                          </Alert>
                          <div className="p-4 bg-gray-50 rounded-lg space-y-3">
                            <div>
                              <Label className="text-xs text-gray-500">Name</Label>
                              <p className="font-medium">{createdStaff.user?.first_name} {createdStaff.user?.last_name}</p>
                            </div>
                            <div>
                              <Label className="text-xs text-gray-500">Email</Label>
                              <p>{createdStaff.user?.email}</p>
                            </div>
                            <div>
                              <Label className="text-xs text-gray-500">Role</Label>
                              <Badge variant="outline" className="capitalize">{createdStaff.user?.role}</Badge>
                            </div>
                            <Separator />
                            <div>
                              <Label className="text-xs text-gray-500">Temporary Password</Label>
                              <div className="flex items-center gap-2 mt-1">
                                <code className="px-3 py-2 bg-white border rounded text-sm font-mono">
                                  {createdStaff.temp_password}
                                </code>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => copyToClipboard(createdStaff.temp_password, 'staff-pass')}
                                >
                                  {copiedPassword === 'staff-pass' ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                                </Button>
                              </div>
                            </div>
                          </div>
                          <Button
                            className="w-full"
                            variant="outline"
                            onClick={() => setCreatedStaff(null)}
                          >
                            Create Another Staff
                          </Button>
                        </div>
                      ) : (
                        <form onSubmit={handleCreateStaff} className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <Label>First Name *</Label>
                              <Input
                                value={newStaff.first_name}
                                onChange={(e) => setNewStaff({...newStaff, first_name: e.target.value})}
                                placeholder="First name"
                                required
                                disabled={!staffHospital}
                              />
                            </div>
                            <div>
                              <Label>Last Name *</Label>
                              <Input
                                value={newStaff.last_name}
                                onChange={(e) => setNewStaff({...newStaff, last_name: e.target.value})}
                                placeholder="Last name"
                                required
                                disabled={!staffHospital}
                              />
                            </div>
                          </div>
                          <div>
                            <Label>Email *</Label>
                            <Input
                              type="email"
                              value={newStaff.email}
                              onChange={(e) => setNewStaff({...newStaff, email: e.target.value})}
                              placeholder="staff@hospital.gov.gh"
                              required
                              disabled={!staffHospital}
                            />
                          </div>
                          <div>
                            <Label>Phone</Label>
                            <Input
                              value={newStaff.phone}
                              onChange={(e) => setNewStaff({...newStaff, phone: e.target.value})}
                              placeholder="+233-XXX-XXXXXX"
                              disabled={!staffHospital}
                            />
                          </div>
                          <div>
                            <Label>Role *</Label>
                            <Select
                              value={newStaff.role}
                              onValueChange={(v) => setNewStaff({...newStaff, role: v})}
                              disabled={!staffHospital}
                            >
                              <SelectTrigger>
                                <SelectValue placeholder="Select role" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="hospital_admin">Hospital Admin</SelectItem>
                                <SelectItem value="hospital_it_admin">Hospital IT Admin</SelectItem>
                                <SelectItem value="facility_admin">Facility Admin</SelectItem>
                                <SelectItem value="physician">Physician</SelectItem>
                                <SelectItem value="nurse">Nurse</SelectItem>
                                <SelectItem value="scheduler">Scheduler</SelectItem>
                                <SelectItem value="biller">Billing Staff</SelectItem>
                                <SelectItem value="records_officer">Records Officer</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                          <div>
                            <Label>Department</Label>
                            <Select
                              value={newStaff.department_id}
                              onValueChange={(v) => setNewStaff({...newStaff, department_id: v})}
                              disabled={!staffHospital}
                            >
                              <SelectTrigger>
                                <SelectValue placeholder={hospitalDepartments.length === 0 ? "No departments available" : "Select department"} />
                              </SelectTrigger>
                              <SelectContent>
                                {hospitalDepartments.map(dept => (
                                  <SelectItem key={dept.id} value={dept.id}>{dept.name}</SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                            {hospitalDepartments.length === 0 && staffHospital && (
                              <p className="text-xs text-amber-600 mt-1">No departments configured. Add departments via Hospital Admin portal.</p>
                            )}
                          </div>
                          <div>
                            <Label>Employee ID (Optional)</Label>
                            <Input
                              value={newStaff.employee_id}
                              onChange={(e) => setNewStaff({...newStaff, employee_id: e.target.value})}
                              placeholder="EMP-XXXX"
                              disabled={!staffHospital}
                            />
                          </div>
                          <Button
                            type="submit"
                            className="w-full bg-emerald-600 hover:bg-emerald-700"
                            disabled={!staffHospital || saving}
                          >
                            {saving ? (
                              <Loader2 className="w-4 h-4 animate-spin mr-2" />
                            ) : (
                              <Plus className="w-4 h-4 mr-2" />
                            )}
                            Create Staff Account
                          </Button>
                        </form>
                      )}
                    </CardContent>
                  </Card>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Regions Tab */}
          <TabsContent value="regions">
            <Card>
              <CardHeader>
                <CardTitle>Ghana Regions Overview</CardTitle>
                <CardDescription>All 16 administrative regions of Ghana</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {regions.map((region) => (
                    <Card key={region.id} className={region.hospital_count > 0 ? 'border-emerald-200 bg-emerald-50/50' : ''}>
                      <CardContent className="pt-4">
                        <div className="flex items-start justify-between">
                          <div>
                            <h4 className="font-medium">{region.name}</h4>
                            <p className="text-sm text-gray-500">Capital: {region.capital}</p>
                            <p className="text-xs text-gray-400">Code: {region.code}</p>
                          </div>
                          {region.hospital_count > 0 ? (
                            <Badge className="bg-emerald-600">{region.hospital_count}</Badge>
                          ) : (
                            <Badge variant="outline" className="text-gray-400">0</Badge>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Pharmacies Tab - Pharmacy Approval Workflow */}
          <TabsContent value="pharmacies">
            <div className="space-y-6">
              {/* Pending Approvals Section */}
              <Card className="border-amber-200 bg-amber-50/30">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2 text-amber-800">
                        <Clock className="w-5 h-5" />
                        Pending Pharmacy Approvals ({pendingPharmacies.length})
                      </CardTitle>
                      <CardDescription>Review and approve pharmacy registrations</CardDescription>
                    </div>
                    <Button variant="outline" size="sm" onClick={fetchPharmacies} disabled={pharmacyLoading}>
                      <RefreshCw className={`w-4 h-4 mr-2 ${pharmacyLoading ? 'animate-spin' : ''}`} />
                      Refresh
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {pharmacyLoading ? (
                    <div className="flex items-center justify-center py-12">
                      <Loader2 className="w-8 h-8 animate-spin text-amber-600" />
                    </div>
                  ) : pendingPharmacies.length === 0 ? (
                    <div className="text-center py-12 text-slate-500">
                      <CheckCircle className="w-16 h-16 mx-auto mb-4 text-emerald-400" />
                      <p className="font-medium">All caught up!</p>
                      <p className="text-sm">No pending pharmacy registrations to review</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {pendingPharmacies.map((pharmacy) => (
                        <div key={pharmacy.id} className="p-4 bg-white rounded-lg border border-amber-200 hover:border-amber-300 transition-colors">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
                                  <Store className="w-5 h-5 text-amber-600" />
                                </div>
                                <div>
                                  <h4 className="font-semibold text-slate-900">{pharmacy.name}</h4>
                                  <p className="text-sm text-slate-500">
                                    License: {pharmacy.license_number}
                                  </p>
                                </div>
                              </div>
                              <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                                <div>
                                  <p className="text-slate-400">Region</p>
                                  <p className="font-medium">{pharmacy.region}</p>
                                </div>
                                <div>
                                  <p className="text-slate-400">District</p>
                                  <p className="font-medium">{pharmacy.district || '-'}</p>
                                </div>
                                <div>
                                  <p className="text-slate-400">Town</p>
                                  <p className="font-medium">{pharmacy.town || '-'}</p>
                                </div>
                                <div>
                                  <p className="text-slate-400">NHIS</p>
                                  <Badge className={pharmacy.has_nhis_accreditation ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'}>
                                    {pharmacy.has_nhis_accreditation ? 'Accredited' : 'Not Accredited'}
                                  </Badge>
                                </div>
                              </div>
                              <p className="mt-2 text-xs text-slate-400">
                                Registered: {new Date(pharmacy.created_at).toLocaleDateString()}
                              </p>
                            </div>
                            <div className="flex gap-2 ml-4">
                              <Button variant="outline" size="sm" onClick={() => openPharmacyDetails(pharmacy)}>
                                <Eye className="w-4 h-4 mr-1" /> Review
                              </Button>
                              <Button 
                                size="sm" 
                                className="bg-emerald-600 hover:bg-emerald-700"
                                onClick={() => handleApprovePharmacy(pharmacy.id)}
                              >
                                <CheckCircle className="w-4 h-4 mr-1" /> Approve
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Approved Pharmacies Section */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-emerald-600" />
                    Approved Pharmacies ({approvedPharmacies.length})
                  </CardTitle>
                  <CardDescription>Pharmacies currently active in the network</CardDescription>
                </CardHeader>
                <CardContent>
                  {approvedPharmacies.length === 0 ? (
                    <div className="text-center py-8 text-slate-500">
                      <Store className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                      <p>No approved pharmacies yet</p>
                    </div>
                  ) : (
                    <ScrollArea className="h-[400px]">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Pharmacy Name</TableHead>
                            <TableHead>License #</TableHead>
                            <TableHead>Region</TableHead>
                            <TableHead>District</TableHead>
                            <TableHead>NHIS</TableHead>
                            <TableHead>Status</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {approvedPharmacies.map((pharmacy) => (
                            <TableRow key={pharmacy.id}>
                              <TableCell className="font-medium">{pharmacy.name}</TableCell>
                              <TableCell className="font-mono text-sm">{pharmacy.license_number}</TableCell>
                              <TableCell>{pharmacy.region}</TableCell>
                              <TableCell>{pharmacy.district || '-'}</TableCell>
                              <TableCell>
                                {pharmacy.has_nhis_accreditation ? (
                                  <Badge className="bg-green-100 text-green-700">Yes</Badge>
                                ) : (
                                  <Badge variant="outline">No</Badge>
                                )}
                              </TableCell>
                              <TableCell>
                                <Badge className="bg-emerald-100 text-emerald-700">Active</Badge>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </ScrollArea>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* Pharmacy Details Dialog */}
      <Dialog open={pharmacyDetailsOpen} onOpenChange={setPharmacyDetailsOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Store className="w-5 h-5 text-blue-600" />
              Pharmacy Registration Details
            </DialogTitle>
            <DialogDescription>
              Review the pharmacy registration details before approval
            </DialogDescription>
          </DialogHeader>
          
          {selectedPharmacyDetails && (
            <div className="space-y-4">
              {/* Basic Info */}
              <div className="p-4 bg-slate-50 rounded-lg">
                <h4 className="font-semibold text-slate-800 mb-3">Basic Information</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-slate-400">Pharmacy Name</p>
                    <p className="font-medium">{selectedPharmacyDetails.name}</p>
                  </div>
                  <div>
                    <p className="text-slate-400">License Number</p>
                    <p className="font-medium font-mono">{selectedPharmacyDetails.license_number}</p>
                  </div>
                  <div>
                    <p className="text-slate-400">Ownership Type</p>
                    <p className="font-medium">{selectedPharmacyDetails.ownership_type?.replace(/_/g, ' ') || '-'}</p>
                  </div>
                  <div>
                    <p className="text-slate-400">Registration Date</p>
                    <p className="font-medium">{new Date(selectedPharmacyDetails.created_at).toLocaleDateString()}</p>
                  </div>
                </div>
              </div>

              {/* Location */}
              <div className="p-4 bg-slate-50 rounded-lg">
                <h4 className="font-semibold text-slate-800 mb-3">Location</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-slate-400">Region</p>
                    <p className="font-medium">{selectedPharmacyDetails.region}</p>
                  </div>
                  <div>
                    <p className="text-slate-400">District</p>
                    <p className="font-medium">{selectedPharmacyDetails.district || '-'}</p>
                  </div>
                  <div>
                    <p className="text-slate-400">Town</p>
                    <p className="font-medium">{selectedPharmacyDetails.town || '-'}</p>
                  </div>
                  <div>
                    <p className="text-slate-400">Address</p>
                    <p className="font-medium">{selectedPharmacyDetails.address || '-'}</p>
                  </div>
                </div>
              </div>

              {/* Contact */}
              <div className="p-4 bg-slate-50 rounded-lg">
                <h4 className="font-semibold text-slate-800 mb-3">Contact Information</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-slate-400">Phone</p>
                    <p className="font-medium">{selectedPharmacyDetails.phone || '-'}</p>
                  </div>
                  <div>
                    <p className="text-slate-400">Email</p>
                    <p className="font-medium">{selectedPharmacyDetails.email || '-'}</p>
                  </div>
                </div>
              </div>

              {/* Accreditation */}
              <div className="p-4 bg-slate-50 rounded-lg">
                <h4 className="font-semibold text-slate-800 mb-3">Accreditation & Services</h4>
                <div className="flex gap-4">
                  <Badge className={selectedPharmacyDetails.has_nhis_accreditation ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'}>
                    {selectedPharmacyDetails.has_nhis_accreditation ? '✓ NHIS Accredited' : '✗ No NHIS'}
                  </Badge>
                  <Badge className={selectedPharmacyDetails.has_24hr_service ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-500'}>
                    {selectedPharmacyDetails.has_24hr_service ? '✓ 24hr Service' : '✗ Not 24hr'}
                  </Badge>
                </div>
              </div>

              {/* Approval Notes */}
              <div className="space-y-2">
                <Label>Admin Notes (optional for approval, required for rejection)</Label>
                <Input
                  placeholder="Add notes about this approval/rejection..."
                  value={approvalNotes}
                  onChange={(e) => setApprovalNotes(e.target.value)}
                />
              </div>
            </div>
          )}

          <DialogFooter className="flex gap-2">
            <Button variant="outline" onClick={() => setPharmacyDetailsOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => selectedPharmacyDetails && handleRejectPharmacy(selectedPharmacyDetails.id)}
            >
              <XCircle className="w-4 h-4 mr-1" /> Reject
            </Button>
            <Button
              className="bg-emerald-600 hover:bg-emerald-700"
              onClick={() => selectedPharmacyDetails && handleApprovePharmacy(selectedPharmacyDetails.id)}
            >
              <CheckCircle className="w-4 h-4 mr-1" /> Approve
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Hospital Dialog */}
      <Dialog open={deleteHospitalOpen} onOpenChange={setDeleteHospitalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="w-5 h-5" />
              Delete Hospital
            </DialogTitle>
            <DialogDescription>
              This action will deactivate the hospital and all associated users. This cannot be easily undone.
            </DialogDescription>
          </DialogHeader>
          
          {hospitalToDelete && (
            <div className="space-y-4">
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Warning</AlertTitle>
                <AlertDescription>
                  You are about to delete <strong>{hospitalToDelete.hospital.name}</strong>.
                  This will affect:
                  <ul className="list-disc list-inside mt-2">
                    <li>{hospitalToDelete.hospital.user_count || 0} staff accounts</li>
                    <li>{hospitalToDelete.hospital.location_count || 0} locations</li>
                    <li>All associated patient records</li>
                  </ul>
                </AlertDescription>
              </Alert>
              
              <div>
                <Label>Type hospital name to confirm:</Label>
                <p className="text-sm text-gray-500 mb-2">
                  Type: <code className="bg-gray-100 px-2 py-1 rounded">{hospitalToDelete.hospital.name}</code>
                </p>
                <Input
                  value={deleteConfirmation}
                  onChange={(e) => setDeleteConfirmation(e.target.value)}
                  placeholder="Enter hospital name"
                  className={deleteConfirmation === hospitalToDelete.hospital.name ? 'border-red-500' : ''}
                />
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteHospitalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteHospital}
              disabled={deleting || deleteConfirmation !== hospitalToDelete?.hospital.name}
            >
              {deleting ? (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              ) : (
                <Trash2 className="w-4 h-4 mr-2" />
              )}
              Delete Hospital
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Hospital Status Change Dialog */}
      <Dialog open={statusChangeOpen} onOpenChange={setStatusChangeOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Power className="w-5 h-5" />
              Change Hospital Status
            </DialogTitle>
            <DialogDescription>
              Update the status of {hospitalToChangeStatus?.hospital.name}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="grid gap-3">
              <Button
                variant="outline"
                className="justify-start gap-3 h-auto py-3"
                onClick={() => handleChangeHospitalStatus('active')}
              >
                <CheckCircle className="w-5 h-5 text-emerald-600" />
                <div className="text-left">
                  <p className="font-medium">Active</p>
                  <p className="text-xs text-gray-500">Hospital is fully operational</p>
                </div>
              </Button>
              
              <Button
                variant="outline"
                className="justify-start gap-3 h-auto py-3"
                onClick={() => handleChangeHospitalStatus('suspended')}
              >
                <Ban className="w-5 h-5 text-orange-600" />
                <div className="text-left">
                  <p className="font-medium">Suspended</p>
                  <p className="text-xs text-gray-500">Temporarily disable all access</p>
                </div>
              </Button>
              
              <Button
                variant="outline"
                className="justify-start gap-3 h-auto py-3"
                onClick={() => handleChangeHospitalStatus('inactive')}
              >
                <XCircle className="w-5 h-5 text-gray-600" />
                <div className="text-left">
                  <p className="font-medium">Inactive</p>
                  <p className="text-xs text-gray-500">Hospital not in use</p>
                </div>
              </Button>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setStatusChangeOpen(false)}>
              Cancel
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
