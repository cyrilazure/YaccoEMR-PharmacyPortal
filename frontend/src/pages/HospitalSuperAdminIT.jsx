import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import { hospitalITAdminAPI, hospitalAdminAPI } from '@/lib/api';
import { getErrorMessage } from '@/lib/utils';
import api from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Dialog, DialogContent, DialogDescription, 
  DialogHeader, DialogTitle, DialogFooter 
} from '@/components/ui/dialog';
import { 
  Select, SelectContent, SelectItem, 
  SelectTrigger, SelectValue 
} from '@/components/ui/select';
import { 
  Table, TableBody, TableCell, 
  TableHead, TableHeader, TableRow 
} from '@/components/ui/table';
import { 
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuTrigger, DropdownMenuSeparator
} from '@/components/ui/dropdown-menu';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import { 
  Users, UserPlus, Key, Shield, Settings, RefreshCw,
  Search, MoreVertical, CheckCircle, XCircle, AlertCircle,
  Loader2, Copy, Check, Lock, Unlock, UserCog, Building2,
  MapPin, FolderTree, Activity, Ban, Eye, EyeOff, Trash2, Plus, Landmark, CreditCard, Edit
} from 'lucide-react';

// Staff roles available for IT Admin to assign
const STAFF_ROLES = [
  { value: 'physician', label: 'Physician', description: 'Medical doctor' },
  { value: 'nurse', label: 'Nurse', description: 'Nursing staff' },
  { value: 'nursing_supervisor', label: 'Nursing Supervisor', description: 'Floor/unit supervisor' },
  { value: 'floor_supervisor', label: 'Floor Supervisor', description: 'Floor management' },
  { value: 'scheduler', label: 'Scheduler', description: 'Appointment management' },
  { value: 'biller', label: 'Biller', description: 'Billing & finance' },
  { value: 'hospital_admin', label: 'Hospital Admin', description: 'Department management' },
  { value: 'receptionist', label: 'Receptionist', description: 'Front desk' },
  { value: 'lab_tech', label: 'Lab Technician', description: 'Laboratory' },
  { value: 'pharmacist', label: 'Pharmacist', description: 'Pharmacy' },
];

export default function HospitalSuperAdminIT() {
  const { hospitalId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const effectiveHospitalId = hospitalId || user?.organization_id;
  
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('staff');
  
  // Data
  const [dashboard, setDashboard] = useState(null);
  const [staff, setStaff] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [locations, setLocations] = useState([]);
  const [activityLog, setActivityLog] = useState([]);
  const [bankAccounts, setBankAccounts] = useState([]);
  const [mobileMoneyAccounts, setMobileMoneyAccounts] = useState([]);
  
  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [roleFilter, setRoleFilter] = useState('all');
  
  // Dialogs
  const [createStaffOpen, setCreateStaffOpen] = useState(false);
  const [viewStaffOpen, setViewStaffOpen] = useState(false);
  const [resetPasswordOpen, setResetPasswordOpen] = useState(false);
  const [assignmentOpen, setAssignmentOpen] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [addBankDialogOpen, setAddBankDialogOpen] = useState(false);
  const [editBankDialogOpen, setEditBankDialogOpen] = useState(false);
  const [addMoMoDialogOpen, setAddMoMoDialogOpen] = useState(false);
  const [permissionsDialogOpen, setPermissionsDialogOpen] = useState(false);
  const [selectedStaff, setSelectedStaff] = useState(null);
  const [selectedBankAccount, setSelectedBankAccount] = useState(null);
  const [createdCredentials, setCreatedCredentials] = useState(null);
  const [staffPermissions, setStaffPermissions] = useState(null);
  
  // Forms
  const [newStaff, setNewStaff] = useState({
    email: '',
    first_name: '',
    last_name: '',
    role: 'physician',
    department_id: '',
    location_id: '',
    phone: '',
    employee_id: ''
  });
  const [assignmentData, setAssignmentData] = useState({
    type: 'department',
    value: ''
  });
  const [bankForm, setBankForm] = useState({
    bank_name: '',
    account_name: '',
    account_number: '',
    branch: '',
    swift_code: '',
    account_type: 'current',
    currency: 'GHS',
    bank_code: '',
    enable_paystack_settlement: true,
    is_primary: false
  });
  const [momoForm, setMomoForm] = useState({
    provider: 'MTN',
    account_name: '',
    mobile_number: '',
    wallet_id: '',
    is_primary: false
  });
  const [saving, setSaving] = useState(false);
  const [copiedPassword, setCopiedPassword] = useState(false);

  // Access check
  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    
    // Allow super_admin, hospital_it_admin, or hospital_admin
    if (user.role === 'super_admin') return;
    
    if (!['hospital_it_admin', 'hospital_admin'].includes(user.role)) {
      toast.error('IT Admin access required');
      navigate('/');
      return;
    }
    
    if (effectiveHospitalId && user.organization_id !== effectiveHospitalId) {
      toast.error('Not authorized for this hospital');
      navigate('/');
    }
  }, [user, effectiveHospitalId, navigate]);

  const fetchData = useCallback(async () => {
    if (!effectiveHospitalId) return;
    
    try {
      setLoading(true);
      const [dashboardRes, staffRes] = await Promise.all([
        hospitalITAdminAPI.getDashboard(effectiveHospitalId),
        hospitalITAdminAPI.listStaff(effectiveHospitalId, {
          status: statusFilter === 'all' ? null : statusFilter,
          role: roleFilter === 'all' ? null : roleFilter,
          search: searchQuery || null
        })
      ]);
      
      setDashboard(dashboardRes.data);
      setStaff(staffRes.data.staff || []);
      setDepartments(dashboardRes.data.departments || []);
      setLocations(dashboardRes.data.locations || []);
      setActivityLog(dashboardRes.data.recent_it_actions || []);
    } catch (err) {
      console.error('Error fetching data:', err);
      toast.error('Failed to load IT Admin dashboard');
    } finally {
      setLoading(false);
    }
  }, [effectiveHospitalId, statusFilter, roleFilter, searchQuery]);

  useEffect(() => {
    fetchData();
    fetchFinanceData();
  }, [fetchData]);

  // Create Staff
  const handleCreateStaff = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const response = await hospitalITAdminAPI.createStaff(effectiveHospitalId, newStaff);
      setCreatedCredentials(response.data.credentials);
      toast.success('Staff account created!');
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create staff');
    } finally {
      setSaving(false);
    }
  };

  // Reset Password
  const handleResetPassword = async () => {
    if (!selectedStaff) return;
    setSaving(true);
    try {
      const response = await hospitalITAdminAPI.resetPassword(effectiveHospitalId, selectedStaff.id);
      setCreatedCredentials(response.data.credentials);
      toast.success('Password reset!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to reset password');
    } finally {
      setSaving(false);
    }
  };

  // Activate/Deactivate
  const handleActivate = async (staffId) => {
    try {
      await hospitalITAdminAPI.activateStaff(effectiveHospitalId, staffId);
      toast.success('Account activated');
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to activate');
    }
  };

  const handleDeactivate = async (staffId) => {
    if (!confirm('Are you sure you want to deactivate this account?')) return;
    try {
      await hospitalITAdminAPI.deactivateStaff(effectiveHospitalId, staffId, 'Admin action');
      toast.success('Account deactivated');
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to deactivate');
    }
  };

  const handleSuspend = async (staffId) => {
    const reason = prompt('Enter suspension reason:');
    if (!reason) return;
    try {
      await hospitalITAdminAPI.suspendStaff(effectiveHospitalId, staffId, reason);
      toast.success('Account suspended');
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to suspend');
    }
  };

  const handleUnlock = async (staffId) => {
    try {
      await hospitalITAdminAPI.unlockAccount(effectiveHospitalId, staffId);
      toast.success('Account unlocked');
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to unlock');
    }
  };

  // Delete User
  const handleDelete = async () => {
    if (!selectedStaff) return;
    setSaving(true);
    try {
      await hospitalITAdminAPI.deleteStaff(effectiveHospitalId, selectedStaff.id);
      toast.success('Account permanently deleted');
      setDeleteConfirmOpen(false);
      setSelectedStaff(null);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete account');
    } finally {
      setSaving(false);
    }
  };

  // Seed Departments
  const handleSeedDepartments = async () => {
    try {
      const response = await hospitalITAdminAPI.seedDepartments(effectiveHospitalId);
      toast.success(response.data.message);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to seed departments');
    }
  };

  // Assignments
  const handleAssignment = async () => {
    if (!selectedStaff || !assignmentData.value) return;
    setSaving(true);
    try {
      if (assignmentData.type === 'department') {
        await hospitalITAdminAPI.assignDepartment(effectiveHospitalId, selectedStaff.id, assignmentData.value);
      } else if (assignmentData.type === 'location') {
        await hospitalITAdminAPI.assignLocation(effectiveHospitalId, selectedStaff.id, assignmentData.value);
      } else if (assignmentData.type === 'role') {
        await hospitalITAdminAPI.changeRole(effectiveHospitalId, selectedStaff.id, assignmentData.value);
      }
      toast.success('Assignment updated');
      setAssignmentOpen(false);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update assignment');
    } finally {
      setSaving(false);
    }
  };

  const copyToClipboard = async (text) => {
    await navigator.clipboard.writeText(text);
    setCopiedPassword(true);
    setTimeout(() => setCopiedPassword(false), 2000);
    toast.success('Copied!');
  };

  const getStatusBadge = (staffMember) => {
    if (!staffMember.is_active && staffMember.status === 'suspended') {
      return <Badge variant="destructive">Suspended</Badge>;
    }
    if (!staffMember.is_active) {
      return <Badge variant="secondary">Inactive</Badge>;
    }
    return <Badge className="bg-emerald-100 text-emerald-700">Active</Badge>;
  };

  // Permission Management Handlers
  const handleOpenPermissions = async (staffMember) => {
    setSelectedStaff(staffMember);
    try {
      const res = await hospitalITAdminAPI.getStaffPermissions(effectiveHospitalId, staffMember.id);
      setStaffPermissions(res.data);
      setPermissionsDialogOpen(true);
    } catch (err) {
      toast.error('Failed to load permissions');
    }
  };

  const handleTogglePermission = async (permission, isGranted) => {
    if (!selectedStaff) return;
    try {
      if (isGranted) {
        await hospitalITAdminAPI.revokePermission(effectiveHospitalId, selectedStaff.id, permission);
        toast.success('Permission revoked');
      } else {
        await hospitalITAdminAPI.grantPermission(effectiveHospitalId, selectedStaff.id, permission);
        toast.success('Permission granted');
      }
      // Refresh permissions
      const res = await hospitalITAdminAPI.getStaffPermissions(effectiveHospitalId, selectedStaff.id);
      setStaffPermissions(res.data);
    } catch (err) {
      toast.error('Failed to update permission');
    }
  };

  // Finance Settings Handlers
  const fetchFinanceData = async () => {
    try {
      const [bankRes, momoRes] = await Promise.all([
        api.get('/finance/bank-accounts'),
        api.get('/finance/mobile-money-accounts')
      ]);
      setBankAccounts(bankRes.data.accounts || []);
      setMobileMoneyAccounts(momoRes.data.accounts || []);
    } catch (err) {
      console.error('Failed to load finance data:', err);
    }
  };

  const handleAddBankAccount = async (e) => {
    e.preventDefault();
    if (!bankForm.bank_name || !bankForm.account_number) {
      toast.error('Bank name and account number are required');
      return;
    }
    
    setSaving(true);
    try {
      await api.post('/finance/bank-accounts', bankForm);
      toast.success('Bank account added successfully');
      setAddBankDialogOpen(false);
      setBankForm({
        bank_name: '', account_name: '', account_number: '',
        branch: '', swift_code: '', account_type: 'current',
        currency: 'GHS', bank_code: '', enable_paystack_settlement: true, is_primary: false
      });
      fetchFinanceData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to add bank account'));
    } finally {
      setSaving(false);
    }
  };

  const handleAddMoMoAccount = async (e) => {
    e.preventDefault();
    if (!momoForm.account_name || !momoForm.mobile_number) {
      toast.error('Account name and mobile number are required');
      return;
    }
    
    setSaving(true);
    try {
      await api.post('/finance/mobile-money-accounts', momoForm);
      toast.success('Mobile money account added');
      setAddMoMoDialogOpen(false);
      setMomoForm({
        provider: 'MTN', account_name: '', mobile_number: '',
        wallet_id: '', is_primary: false
      });
      fetchFinanceData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to add mobile money account'));
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteBankAccount = async (accountId) => {
    if (!confirm('Are you sure you want to remove this bank account?')) return;
    
    try {
      await api.delete(`/finance/bank-accounts/${accountId}`);
      toast.success('Bank account removed');
      fetchFinanceData();
    } catch (err) {
      toast.error('Failed to remove account');
    }
  };

  const handleEditBankAccount = (account) => {
    setSelectedBankAccount(account);
    setBankForm({
      bank_name: account.bank_name,
      account_name: account.account_name,
      account_number: account.account_number,
      branch: account.branch || '',
      swift_code: account.swift_code || '',
      account_type: account.account_type,
      currency: account.currency,
      bank_code: account.bank_code || '',
      enable_paystack_settlement: account.enable_paystack_settlement !== false,
      is_primary: account.is_primary
    });
    setEditBankDialogOpen(true);
  };

  const handleUpdateBankAccount = async (e) => {
    e.preventDefault();
    if (!selectedBankAccount) return;
    
    setSaving(true);
    try {
      await api.put(`/finance/bank-accounts/${selectedBankAccount.id}`, bankForm);
      toast.success('Bank account updated');
      setEditBankDialogOpen(false);
      setSelectedBankAccount(null);
      setBankForm({
        bank_name: '', account_name: '', account_number: '',
        branch: '', swift_code: '', account_type: 'current',
        currency: 'GHS', bank_code: '', enable_paystack_settlement: true, is_primary: false
      });
      fetchFinanceData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to update bank account'));
    } finally {
      setSaving(false);
    }
  };

  const handleTogglePrimary = async (accountId, currentIsPrimary) => {
    if (currentIsPrimary) {
      toast.info('This is already the primary account');
      return;
    }
    
    try {
      // Update to make this primary (backend will unset others)
      const account = bankAccounts.find(a => a.id === accountId);
      await api.put(`/finance/bank-accounts/${accountId}`, {
        ...account,
        is_primary: true
      });
      toast.success('Primary account updated');
      fetchFinanceData();
    } catch (err) {
      toast.error('Failed to update primary account');
    }
  };

  if (loading && !dashboard) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Shield className="w-6 h-6 text-slate-700" />
            IT Administration
          </h1>
          <p className="text-gray-500">{dashboard?.hospital?.name} - Staff Account Management</p>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={fetchData} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button onClick={() => setCreateStaffOpen(true)} className="bg-slate-800 hover:bg-slate-900">
            <UserPlus className="w-4 h-4 mr-2" />
            Add Staff
          </Button>
        </div>
      </div>

      {/* IT Admin Notice */}
      <Alert className="bg-slate-50 border-slate-200">
        <Shield className="h-4 w-4 text-slate-600" />
        <AlertTitle className="text-slate-800">IT Administration Portal</AlertTitle>
        <AlertDescription className="text-slate-600">
          This portal is for staff account management only. Patient records, appointments, billing, and clinical features are not accessible here.
        </AlertDescription>
      </Alert>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total Staff</p>
                <p className="text-2xl font-bold">{dashboard?.staff_stats?.total || 0}</p>
              </div>
              <Users className="w-8 h-8 text-slate-300" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Active</p>
                <p className="text-2xl font-bold text-emerald-600">{dashboard?.staff_stats?.active || 0}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-emerald-200" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Inactive</p>
                <p className="text-2xl font-bold text-gray-600">{dashboard?.staff_stats?.inactive || 0}</p>
              </div>
              <XCircle className="w-8 h-8 text-gray-200" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Departments</p>
                <p className="text-2xl font-bold text-blue-600">{departments.length}</p>
              </div>
              <FolderTree className="w-8 h-8 text-blue-200" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="staff" className="gap-2">
            <Users className="w-4 h-4" /> Staff Accounts
          </TabsTrigger>
          <TabsTrigger value="assignments" className="gap-2">
            <FolderTree className="w-4 h-4" /> Departments & Locations
          </TabsTrigger>
          <TabsTrigger value="finance" className="gap-2">
            <Landmark className="w-4 h-4" /> Finance Settings
          </TabsTrigger>
          <TabsTrigger value="activity" className="gap-2">
            <Activity className="w-4 h-4" /> IT Activity Log
          </TabsTrigger>
        </TabsList>

        {/* Staff Tab */}
        <TabsContent value="staff" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Staff Account Management</CardTitle>
              <CardDescription>Create, manage, and control staff access</CardDescription>
            </CardHeader>
            <CardContent>
              {/* Filters */}
              <div className="flex flex-wrap items-center gap-4 mb-6">
                <div className="relative flex-1 min-w-[200px] max-w-sm">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <Input
                    placeholder="Search by name, email, ID..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9"
                  />
                </div>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-[140px]">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="inactive">Inactive</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={roleFilter} onValueChange={setRoleFilter}>
                  <SelectTrigger className="w-[160px]">
                    <SelectValue placeholder="Role" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Roles</SelectItem>
                    {STAFF_ROLES.map(r => (
                      <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Staff Table */}
              <div className="rounded-lg border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Staff Member</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Department</TableHead>
                      <TableHead>Location</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {staff.map((s) => (
                      <TableRow key={s.id}>
                        <TableCell>
                          <div>
                            <p className="font-medium">{s.first_name} {s.last_name}</p>
                            <p className="text-sm text-gray-500">{s.email}</p>
                            {s.employee_id && (
                              <p className="text-xs text-gray-400">ID: {s.employee_id}</p>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="capitalize">
                            {s.role?.replace('_', ' ')}
                          </Badge>
                        </TableCell>
                        <TableCell>{s.department_name || '-'}</TableCell>
                        <TableCell>{s.location_name || '-'}</TableCell>
                        <TableCell>{getStatusBadge(s)}</TableCell>
                        <TableCell className="text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm">
                                <MoreVertical className="w-4 h-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => {
                                setSelectedStaff(s);
                                setViewStaffOpen(true);
                              }}>
                                <Eye className="w-4 h-4 mr-2" /> View Details
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => {
                                setSelectedStaff(s);
                                setResetPasswordOpen(true);
                              }}>
                                <Key className="w-4 h-4 mr-2" /> Reset Password
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem onClick={() => {
                                setSelectedStaff(s);
                                setAssignmentData({ type: 'role', value: '' });
                                setAssignmentOpen(true);
                              }}>
                                <UserCog className="w-4 h-4 mr-2" /> Change Role
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => {
                                setSelectedStaff(s);
                                setAssignmentData({ type: 'department', value: '' });
                                setAssignmentOpen(true);
                              }}>
                                <FolderTree className="w-4 h-4 mr-2" /> Assign Department
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => {
                                setSelectedStaff(s);
                                setAssignmentData({ type: 'location', value: '' });
                                setAssignmentOpen(true);
                              }}>
                                <MapPin className="w-4 h-4 mr-2" /> Assign Location
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              {s.is_active ? (
                                <>
                                  <DropdownMenuItem 
                                    onClick={() => handleSuspend(s.id)}
                                    className="text-orange-600"
                                  >
                                    <Ban className="w-4 h-4 mr-2" /> Suspend
                                  </DropdownMenuItem>
                                  <DropdownMenuItem 
                                    onClick={() => handleDeactivate(s.id)}
                                    className="text-red-600"
                                  >
                                    <XCircle className="w-4 h-4 mr-2" /> Deactivate
                                  </DropdownMenuItem>
                                </>
                              ) : (
                                <DropdownMenuItem 
                                  onClick={() => handleActivate(s.id)}
                                  className="text-emerald-600"
                                >
                                  <CheckCircle className="w-4 h-4 mr-2" /> Activate
                                </DropdownMenuItem>
                              )}
                              <DropdownMenuItem onClick={() => handleUnlock(s.id)}>
                                <Unlock className="w-4 h-4 mr-2" /> Unlock Account
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem 
                                onClick={() => {
                                  setSelectedStaff(s);
                                  setDeleteConfirmOpen(true);
                                }}
                                className="text-red-600"
                              >
                                <Trash2 className="w-4 h-4 mr-2" /> Delete Account
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                    {staff.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center py-12 text-gray-500">
                          No staff accounts found
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Assignments Tab */}
        <TabsContent value="assignments" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Departments */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <FolderTree className="w-5 h-5 text-blue-600" />
                    Departments
                  </CardTitle>
                  {departments.length === 0 && (
                    <Button size="sm" onClick={handleSeedDepartments} variant="outline">
                      <Plus className="w-4 h-4 mr-2" />
                      Add Default Departments
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {departments.map((dept) => (
                    <div key={dept.id} className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                      <div>
                        <p className="font-medium">{dept.name}</p>
                        <p className="text-xs text-gray-500">{dept.code}</p>
                      </div>
                      <Badge variant="secondary">{dept.staff_count || 0} staff</Badge>
                    </div>
                  ))}
                  {departments.length === 0 && (
                    <div className="text-center py-8">
                      <p className="text-gray-500 mb-3">No departments configured</p>
                      <Button onClick={handleSeedDepartments} className="bg-blue-600 hover:bg-blue-700">
                        <Plus className="w-4 h-4 mr-2" />
                        Setup Default Departments
                      </Button>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Locations */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-purple-600" />
                  Locations
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {locations.map((loc) => (
                    <div key={loc.id} className="flex items-center justify-between p-3 rounded-lg bg-gray-50">
                      <div>
                        <p className="font-medium">{loc.name}</p>
                        <p className="text-xs text-gray-500 capitalize">{loc.location_type?.replace('_', ' ')}</p>
                      </div>
                      <Badge variant="secondary">{loc.staff_count || 0} staff</Badge>
                    </div>
                  ))}
                  {locations.length === 0 && (
                    <p className="text-center text-gray-500 py-8">No locations</p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Role Distribution */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Staff by Role</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {dashboard?.role_distribution && Object.entries(dashboard.role_distribution).map(([role, count]) => (
                    <div key={role} className="p-4 rounded-lg bg-gray-50 text-center">
                      <p className="text-2xl font-bold">{count}</p>
                      <p className="text-sm text-gray-500 capitalize">{role.replace('_', ' ')}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Activity Tab */}
        <TabsContent value="activity" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>IT Activity Log</CardTitle>
              <CardDescription>Account management actions (not patient audit logs)</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                <div className="space-y-3">
                  {activityLog.map((log, idx) => (
                    <div key={idx} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                      <Activity className="w-4 h-4 text-gray-400 mt-1" />
                      <div className="flex-1">
                        <p className="text-sm">
                          <span className="font-medium">{log.admin_email}</span>
                          {' - '}
                          <span className="capitalize">{log.action?.replace(/_/g, ' ')}</span>
                        </p>
                        {log.details && (
                          <p className="text-xs text-gray-500">
                            {log.details.email && `User: ${log.details.email}`}
                            {log.details.role && ` • Role: ${log.details.role}`}
                          </p>
                        )}
                        <p className="text-xs text-gray-400">{new Date(log.timestamp).toLocaleString()}</p>
                      </div>
                    </div>
                  ))}
                  {activityLog.length === 0 && (
                    <p className="text-center text-gray-500 py-12">No IT activity recorded</p>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Finance Settings Tab */}
        <TabsContent value="finance" className="mt-6">
          <div className="space-y-4">
            {/* Bank Accounts Section */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Building2 className="w-5 h-5 text-emerald-600" />
                    Bank Accounts
                  </CardTitle>
                  <CardDescription>Hospital bank accounts for receiving patient payments</CardDescription>
                </div>
                <Button onClick={() => setAddBankDialogOpen(true)} className="gap-2 bg-emerald-600 hover:bg-emerald-700">
                  <Plus className="w-4 h-4" /> Add Bank Account
                </Button>
              </CardHeader>
              <CardContent>
                {bankAccounts.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <Building2 className="w-12 h-12 mx-auto mb-4 opacity-30" />
                    <p className="mb-4">No bank accounts configured</p>
                    <Button onClick={() => setAddBankDialogOpen(true)} variant="outline" className="gap-2">
                      <Plus className="w-4 h-4" /> Add Your First Bank Account
                    </Button>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Bank Name</TableHead>
                        <TableHead>Account Name</TableHead>
                        <TableHead>Account Number</TableHead>
                        <TableHead>Branch</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {bankAccounts.map((account) => (
                        <TableRow key={account.id}>
                          <TableCell className="font-medium">{account.bank_name}</TableCell>
                          <TableCell>{account.account_name}</TableCell>
                          <TableCell className="font-mono text-sm">{account.account_number}</TableCell>
                          <TableCell className="text-sm text-gray-500">{account.branch || 'N/A'}</TableCell>
                          <TableCell className="capitalize text-sm">{account.account_type}</TableCell>
                          <TableCell>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleTogglePrimary(account.id, account.is_primary)}
                              className={account.is_primary ? 'border-emerald-300' : ''}
                            >
                              {account.is_primary ? (
                                <Badge className="bg-emerald-100 text-emerald-700 border-0">
                                  <CheckCircle className="w-3 h-3 mr-1" /> Primary
                                </Badge>
                              ) : (
                                <span className="text-xs text-gray-600">Set as Primary</span>
                              )}
                            </Button>
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex gap-1 justify-end">
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleEditBankAccount(account)}
                                className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                              >
                                <Edit className="w-4 h-4" />
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleDeleteBankAccount(account.id)}
                                className="text-red-600 hover:text-red-700 hover:bg-red-50"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>

            {/* Mobile Money Section */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="w-5 h-5 text-blue-600" />
                    Mobile Money Accounts
                  </CardTitle>
                  <CardDescription>MTN, Vodafone, AirtelTigo wallet accounts</CardDescription>
                </div>
                <Button onClick={() => setAddMoMoDialogOpen(true)} className="gap-2 bg-blue-600 hover:bg-blue-700">
                  <Plus className="w-4 h-4" /> Add Mobile Money
                </Button>
              </CardHeader>
              <CardContent>
                {mobileMoneyAccounts.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Activity className="w-10 h-10 mx-auto mb-3 opacity-30" />
                    <p>No mobile money accounts configured</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {mobileMoneyAccounts.map((account) => (
                      <Card key={account.id} className="border-blue-200">
                        <CardContent className="pt-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <Badge className="bg-blue-100 text-blue-700">{account.provider}</Badge>
                                {account.is_primary && (
                                  <Badge className="bg-emerald-100 text-emerald-700">Primary</Badge>
                                )}
                              </div>
                              <p className="font-medium">{account.account_name}</p>
                              <p className="text-sm text-gray-600 font-mono">{account.mobile_number}</p>
                              {account.wallet_id && (
                                <p className="text-xs text-gray-500 mt-1">Wallet: {account.wallet_id}</p>
                              )}
                            </div>
                            <Button size="sm" variant="ghost" className="text-red-600">
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Security Info */}
            <Alert className="border-amber-200 bg-amber-50">
              <Shield className="w-4 h-4 text-amber-600" />
              <AlertTitle className="text-amber-800">Financial Security Notice</AlertTitle>
              <AlertDescription className="text-amber-700">
                Bank account information is sensitive. Only Finance Officers, Hospital Admins, and IT Admins can access this section.
                All changes are logged in the audit trail.
              </AlertDescription>
            </Alert>
          </div>
        </TabsContent>
      </Tabs>

      {/* Create Staff Dialog */}
      <Dialog open={createStaffOpen} onOpenChange={(open) => {
        setCreateStaffOpen(open);
        if (!open) {
          setCreatedCredentials(null);
          setNewStaff({
            email: '', first_name: '', last_name: '', role: 'physician',
            department_id: '', location_id: '', phone: '', employee_id: ''
          });
        }
      }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Create Staff Account</DialogTitle>
            <DialogDescription>Add a new staff member to the system</DialogDescription>
          </DialogHeader>
          
          {createdCredentials ? (
            <div className="space-y-4">
              <Alert className="bg-emerald-50 border-emerald-200">
                <CheckCircle className="h-4 w-4 text-emerald-600" />
                <AlertTitle className="text-emerald-800">Account Created!</AlertTitle>
                <AlertDescription className="text-emerald-700">
                  Save these credentials - the password cannot be retrieved later.
                </AlertDescription>
              </Alert>
              
              <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                <div>
                  <p className="text-sm text-gray-500">Email</p>
                  <p className="font-medium">{createdCredentials.email}</p>
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">Temporary Password</p>
                    <p className="font-mono font-medium">{createdCredentials.temp_password}</p>
                  </div>
                  <Button variant="outline" size="sm" onClick={() => copyToClipboard(createdCredentials.temp_password)}>
                    {copiedPassword ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  </Button>
                </div>
              </div>
              
              <DialogFooter>
                <Button onClick={() => {
                  setCreateStaffOpen(false);
                  setCreatedCredentials(null);
                }}>Done</Button>
              </DialogFooter>
            </div>
          ) : (
            <form onSubmit={handleCreateStaff} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>First Name *</Label>
                  <Input
                    value={newStaff.first_name}
                    onChange={(e) => setNewStaff({...newStaff, first_name: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label>Last Name *</Label>
                  <Input
                    value={newStaff.last_name}
                    onChange={(e) => setNewStaff({...newStaff, last_name: e.target.value})}
                    required
                  />
                </div>
                <div className="col-span-2">
                  <Label>Email *</Label>
                  <Input
                    type="email"
                    value={newStaff.email}
                    onChange={(e) => setNewStaff({...newStaff, email: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label>Role *</Label>
                  <Select value={newStaff.role} onValueChange={(v) => setNewStaff({...newStaff, role: v})}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {STAFF_ROLES.map(r => (
                        <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Employee ID</Label>
                  <Input
                    value={newStaff.employee_id}
                    onChange={(e) => setNewStaff({...newStaff, employee_id: e.target.value})}
                    placeholder="Optional"
                  />
                </div>
                <div>
                  <Label>Department</Label>
                  <Select value={newStaff.department_id} onValueChange={(v) => setNewStaff({...newStaff, department_id: v})}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select department" />
                    </SelectTrigger>
                    <SelectContent>
                      {departments.map(d => (
                        <SelectItem key={d.id} value={d.id}>{d.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Location</Label>
                  <Select value={newStaff.location_id} onValueChange={(v) => setNewStaff({...newStaff, location_id: v})}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select location" />
                    </SelectTrigger>
                    <SelectContent>
                      {locations.map(l => (
                        <SelectItem key={l.id} value={l.id}>{l.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="col-span-2">
                  <Label>Phone</Label>
                  <Input
                    value={newStaff.phone}
                    onChange={(e) => setNewStaff({...newStaff, phone: e.target.value})}
                    placeholder="+233-XXX-XXXXXX"
                  />
                </div>
              </div>
              
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setCreateStaffOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" className="bg-slate-800 hover:bg-slate-900" disabled={saving}>
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Create Account'}
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>

      {/* Reset Password Dialog */}
      <Dialog open={resetPasswordOpen} onOpenChange={(open) => {
        setResetPasswordOpen(open);
        if (!open) setCreatedCredentials(null);
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reset Password</DialogTitle>
            <DialogDescription>
              Generate new password for {selectedStaff?.email}
            </DialogDescription>
          </DialogHeader>
          
          {createdCredentials ? (
            <div className="space-y-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">New Password</p>
                    <p className="font-mono font-medium">{createdCredentials.temp_password}</p>
                  </div>
                  <Button variant="outline" size="sm" onClick={() => copyToClipboard(createdCredentials.temp_password)}>
                    {copiedPassword ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  </Button>
                </div>
              </div>
              <DialogFooter>
                <Button onClick={() => {
                  setResetPasswordOpen(false);
                  setCreatedCredentials(null);
                }}>Done</Button>
              </DialogFooter>
            </div>
          ) : (
            <DialogFooter>
              <Button variant="outline" onClick={() => setResetPasswordOpen(false)}>Cancel</Button>
              <Button onClick={handleResetPassword} disabled={saving}>
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Reset Password'}
              </Button>
            </DialogFooter>
          )}
        </DialogContent>
      </Dialog>

      {/* View Staff Details Dialog */}
      <Dialog open={viewStaffOpen} onOpenChange={setViewStaffOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Eye className="w-5 h-5 text-blue-600" />
              Staff Details
            </DialogTitle>
          </DialogHeader>
          
          {selectedStaff && (
            <div className="space-y-4 py-4">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white text-xl font-bold">
                  {selectedStaff.first_name?.[0]}{selectedStaff.last_name?.[0]}
                </div>
                <div>
                  <h3 className="text-lg font-semibold">{selectedStaff.first_name} {selectedStaff.last_name}</h3>
                  <p className="text-gray-500">{selectedStaff.email}</p>
                </div>
              </div>
              
              <Separator />
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-xs text-gray-500">Role</Label>
                  <p className="font-medium capitalize">{selectedStaff.role?.replace('_', ' ')}</p>
                </div>
                <div>
                  <Label className="text-xs text-gray-500">Status</Label>
                  <div className="flex items-center gap-2">
                    {selectedStaff.is_active ? (
                      <Badge className="bg-emerald-100 text-emerald-700">Active</Badge>
                    ) : (
                      <Badge className="bg-red-100 text-red-700">Inactive</Badge>
                    )}
                  </div>
                </div>
                <div>
                  <Label className="text-xs text-gray-500">Department</Label>
                  <p className="font-medium">{selectedStaff.department_name || 'Not assigned'}</p>
                </div>
                <div>
                  <Label className="text-xs text-gray-500">Location</Label>
                  <p className="font-medium">{selectedStaff.location_name || 'Not assigned'}</p>
                </div>
                <div>
                  <Label className="text-xs text-gray-500">Phone</Label>
                  <p className="font-medium">{selectedStaff.phone || 'Not provided'}</p>
                </div>
                <div>
                  <Label className="text-xs text-gray-500">Employee ID</Label>
                  <p className="font-medium font-mono">{selectedStaff.employee_id || 'Not assigned'}</p>
                </div>
              </div>
              
              <Separator />
              
              <div>
                <Label className="text-xs text-gray-500">Account Created</Label>
                <p className="text-sm">{selectedStaff.created_at ? new Date(selectedStaff.created_at).toLocaleString() : 'Unknown'}</p>
              </div>
              
              {selectedStaff.is_locked && (
                <Alert className="border-red-200 bg-red-50">
                  <Lock className="h-4 w-4 text-red-600" />
                  <AlertTitle className="text-red-800">Account Locked</AlertTitle>
                  <AlertDescription className="text-red-600">
                    This account is locked due to multiple failed login attempts.
                  </AlertDescription>
                </Alert>
              )}
              
              {selectedStaff.is_temp_password && (
                <Alert className="border-amber-200 bg-amber-50">
                  <Key className="h-4 w-4 text-amber-600" />
                  <AlertTitle className="text-amber-800">Temporary Password</AlertTitle>
                  <AlertDescription className="text-amber-600">
                    User must change password on next login.
                  </AlertDescription>
                </Alert>
              )}
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setViewStaffOpen(false)}>Close</Button>
            <Button onClick={() => {
              setViewStaffOpen(false);
              setResetPasswordOpen(true);
            }}>
              <Key className="w-4 h-4 mr-2" />
              Reset Password
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Assignment Dialog */}
      <Dialog open={assignmentOpen} onOpenChange={setAssignmentOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {assignmentData.type === 'role' && 'Change Role'}
              {assignmentData.type === 'department' && 'Assign Department'}
              {assignmentData.type === 'location' && 'Assign Location'}
            </DialogTitle>
            <DialogDescription>
              Update assignment for {selectedStaff?.first_name} {selectedStaff?.last_name}
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4">
            {assignmentData.type === 'role' && (
              <Select value={assignmentData.value} onValueChange={(v) => setAssignmentData({...assignmentData, value: v})}>
                <SelectTrigger>
                  <SelectValue placeholder="Select new role" />
                </SelectTrigger>
                <SelectContent>
                  {STAFF_ROLES.map(r => (
                    <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            {assignmentData.type === 'department' && (
              <Select value={assignmentData.value} onValueChange={(v) => setAssignmentData({...assignmentData, value: v})}>
                <SelectTrigger>
                  <SelectValue placeholder="Select department" />
                </SelectTrigger>
                <SelectContent>
                  {departments.map(d => (
                    <SelectItem key={d.id} value={d.id}>{d.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            {assignmentData.type === 'location' && (
              <Select value={assignmentData.value} onValueChange={(v) => setAssignmentData({...assignmentData, value: v})}>
                <SelectTrigger>
                  <SelectValue placeholder="Select location" />
                </SelectTrigger>
                <SelectContent>
                  {locations.map(l => (
                    <SelectItem key={l.id} value={l.id}>{l.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setAssignmentOpen(false)}>Cancel</Button>
            <Button onClick={handleAssignment} disabled={saving || !assignmentData.value}>
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Save'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-red-600 flex items-center gap-2">
              <Trash2 className="w-5 h-5" />
              Delete User Account
            </DialogTitle>
            <DialogDescription>
              This action cannot be undone. The user account will be permanently deleted.
            </DialogDescription>
          </DialogHeader>
          
          {selectedStaff && (
            <div className="py-4">
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Warning</AlertTitle>
                <AlertDescription>
                  You are about to permanently delete the account for:
                  <div className="mt-2 font-medium">
                    <p>{selectedStaff.first_name} {selectedStaff.last_name}</p>
                    <p className="text-sm">{selectedStaff.email}</p>
                  </div>
                </AlertDescription>
              </Alert>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteConfirmOpen(false)}>
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              onClick={handleDelete} 
              disabled={saving}
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Delete Permanently'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Bank Account Dialog */}
      <Dialog open={addBankDialogOpen} onOpenChange={setAddBankDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Add Hospital Bank Account</DialogTitle>
            <DialogDescription>Configure bank account for receiving patient payments</DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleAddBankAccount} className="space-y-4 mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Bank Name *</Label>
                <Select 
                  value={bankForm.bank_name} 
                  onValueChange={(v) => {
                    const bankMap = {
                      'GCB Bank': '040',
                      'Ecobank Ghana': '050',
                      'Stanbic Bank': '030',
                      'Fidelity Bank': '070',
                      'GTBank Ghana': '080',
                      'Absa Bank Ghana': '090',
                      'Standard Chartered': '061',
                      'ADB Bank': '011',
                      'Zenith Bank': '012',
                      'Cal Bank': '013',
                      'Access Bank': '014',
                      'UBA Ghana': '016',
                      'Prudential Bank': '018'
                    };
                    setBankForm({...bankForm, bank_name: v, bank_code: bankMap[v] || ''});
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select bank" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="GCB Bank">GCB Bank</SelectItem>
                    <SelectItem value="Ecobank Ghana">Ecobank Ghana</SelectItem>
                    <SelectItem value="Absa Bank Ghana">Absa Bank Ghana</SelectItem>
                    <SelectItem value="Stanbic Bank">Stanbic Bank</SelectItem>
                    <SelectItem value="Fidelity Bank">Fidelity Bank</SelectItem>
                    <SelectItem value="GTBank Ghana">GTBank Ghana</SelectItem>
                    <SelectItem value="Standard Chartered">Standard Chartered</SelectItem>
                    <SelectItem value="Cal Bank">Cal Bank</SelectItem>
                    <SelectItem value="Access Bank">Access Bank</SelectItem>
                    <SelectItem value="Zenith Bank">Zenith Bank</SelectItem>
                    <SelectItem value="ADB Bank">ADB Bank</SelectItem>
                    <SelectItem value="Prudential Bank">Prudential Bank</SelectItem>
                    <SelectItem value="UBA Ghana">UBA Ghana</SelectItem>
                  </SelectContent>
                </Select>
                {bankForm.bank_code && (
                  <p className="text-xs text-gray-500">Bank Code: {bankForm.bank_code}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label>Account Name *</Label>
                <Input
                  value={bankForm.account_name}
                  onChange={(e) => setBankForm({...bankForm, account_name: e.target.value})}
                  placeholder="Hospital account name"
                  required
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Account Number *</Label>
                <Input
                  value={bankForm.account_number}
                  onChange={(e) => setBankForm({...bankForm, account_number: e.target.value})}
                  placeholder="Account number"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Branch</Label>
                <Input
                  value={bankForm.branch}
                  onChange={(e) => setBankForm({...bankForm, branch: e.target.value})}
                  placeholder="e.g., Accra Main"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Account Type</Label>
                <Select value={bankForm.account_type} onValueChange={(v) => setBankForm({...bankForm, account_type: v})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="current">Current Account</SelectItem>
                    <SelectItem value="savings">Savings Account</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Currency</Label>


      {/* Edit Bank Account Dialog */}
      <Dialog open={editBankDialogOpen} onOpenChange={setEditBankDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Edit Bank Account</DialogTitle>
            <DialogDescription>Update hospital bank account details</DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleUpdateBankAccount} className="space-y-4 mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Bank Name *</Label>
                <Select 
                  value={bankForm.bank_name} 
                  onValueChange={(v) => {
                    const bankMap = {
                      'GCB Bank': '040',
                      'Ecobank Ghana': '050',
                      'Stanbic Bank': '030',
                      'Fidelity Bank': '070',
                      'GTBank Ghana': '080',
                      'Absa Bank Ghana': '090',
                      'Standard Chartered': '061',
                      'ADB Bank': '011',
                      'Zenith Bank': '012',
                      'Cal Bank': '013',
                      'Access Bank': '014',
                      'UBA Ghana': '016',
                      'Prudential Bank': '018'
                    };
                    setBankForm({...bankForm, bank_name: v, bank_code: bankMap[v] || ''});
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select bank" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="GCB Bank">GCB Bank</SelectItem>
                    <SelectItem value="Ecobank Ghana">Ecobank Ghana</SelectItem>
                    <SelectItem value="Absa Bank Ghana">Absa Bank Ghana</SelectItem>
                    <SelectItem value="Stanbic Bank">Stanbic Bank</SelectItem>
                    <SelectItem value="Fidelity Bank">Fidelity Bank</SelectItem>
                    <SelectItem value="GTBank Ghana">GTBank Ghana</SelectItem>
                    <SelectItem value="Standard Chartered">Standard Chartered</SelectItem>
                    <SelectItem value="Cal Bank">Cal Bank</SelectItem>
                    <SelectItem value="Access Bank">Access Bank</SelectItem>
                    <SelectItem value="Zenith Bank">Zenith Bank</SelectItem>
                    <SelectItem value="ADB Bank">ADB Bank</SelectItem>
                    <SelectItem value="Prudential Bank">Prudential Bank</SelectItem>
                    <SelectItem value="UBA Ghana">UBA Ghana</SelectItem>
                  </SelectContent>
                </Select>
                {bankForm.bank_code && (
                  <p className="text-xs text-gray-500">Bank Code: {bankForm.bank_code}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label>Account Name *</Label>
                <Input
                  value={bankForm.account_name}
                  onChange={(e) => setBankForm({...bankForm, account_name: e.target.value})}
                  placeholder="Hospital account name"
                  required
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Account Number *</Label>
                <Input
                  value={bankForm.account_number}
                  onChange={(e) => setBankForm({...bankForm, account_number: e.target.value})}
                  placeholder="Account number"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Branch</Label>
                <Input
                  value={bankForm.branch}
                  onChange={(e) => setBankForm({...bankForm, branch: e.target.value})}
                  placeholder="e.g., Accra Main"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Account Type</Label>
                <Select value={bankForm.account_type} onValueChange={(v) => setBankForm({...bankForm, account_type: v})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="current">Current Account</SelectItem>
                    <SelectItem value="savings">Savings Account</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Currency</Label>
                <Select value={bankForm.currency} onValueChange={(v) => setBankForm({...bankForm, currency: v})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="GHS">GHS (Ghana Cedi)</SelectItem>
                    <SelectItem value="USD">USD (US Dollar)</SelectItem>
                    <SelectItem value="EUR">EUR (Euro)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div className="space-y-2">
              <Label>SWIFT Code (Optional)</Label>
              <Input
                value={bankForm.swift_code}
                onChange={(e) => setBankForm({...bankForm, swift_code: e.target.value})}
                placeholder="For international transfers"
              />
            </div>
            
            <div className="flex items-center gap-2 p-3 bg-emerald-50 rounded-lg">
              <input
                type="checkbox"
                id="edit-primary-bank"
                checked={bankForm.is_primary}
                onChange={(e) => setBankForm({...bankForm, is_primary: e.target.checked})}
                className="rounded"
              />
              <Label htmlFor="edit-primary-bank" className="text-emerald-700 font-medium cursor-pointer">
                <CheckCircle className="w-4 h-4 inline mr-1" />
                Set as primary account for receiving payments
              </Label>
            </div>
            
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setEditBankDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={saving} className="bg-blue-600 hover:bg-blue-700">
                {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                Update Bank Account
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

                <Select value={bankForm.currency} onValueChange={(v) => setBankForm({...bankForm, currency: v})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="GHS">GHS (Ghana Cedi)</SelectItem>
                    <SelectItem value="USD">USD (US Dollar)</SelectItem>
                    <SelectItem value="EUR">EUR (Euro)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div className="space-y-2">
              <Label>SWIFT Code (Optional)</Label>
              <Input
                value={bankForm.swift_code}
                onChange={(e) => setBankForm({...bankForm, swift_code: e.target.value})}
                placeholder="For international transfers"
              />
            </div>
            
            <Alert className="bg-blue-50 border-blue-200">
              <CreditCard className="w-4 h-4 text-blue-600" />
              <AlertTitle className="text-blue-800">Paystack Direct Settlement</AlertTitle>
              <AlertDescription className="text-blue-700 text-sm">
                When patients pay via Paystack (card payments), the money will be sent DIRECTLY to this bank account automatically. 
                No manual transfers needed. Settlement takes 1-2 business days.
              </AlertDescription>
            </Alert>
            
            <div className="flex items-center gap-2 p-3 bg-emerald-50 rounded-lg">
              <input
                type="checkbox"
                id="primary-bank"
                checked={bankForm.is_primary}
                onChange={(e) => setBankForm({...bankForm, is_primary: e.target.checked})}
                className="rounded"
              />
              <Label htmlFor="primary-bank" className="text-emerald-700 font-medium cursor-pointer">
                <CheckCircle className="w-4 h-4 inline mr-1" />
                Set as primary account for receiving payments
              </Label>
            </div>
            
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setAddBankDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={saving} className="bg-emerald-600 hover:bg-emerald-700">
                {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                Add Bank Account
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Add Mobile Money Dialog */}
      <Dialog open={addMoMoDialogOpen} onOpenChange={setAddMoMoDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Mobile Money Account</DialogTitle>
            <DialogDescription>Configure mobile money wallet for payments</DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleAddMoMoAccount} className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label>Provider *</Label>
              <Select value={momoForm.provider} onValueChange={(v) => setMomoForm({...momoForm, provider: v})}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="MTN">MTN Mobile Money</SelectItem>
                  <SelectItem value="Vodafone">Vodafone Cash</SelectItem>
                  <SelectItem value="AirtelTigo">AirtelTigo Money</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Account Name *</Label>
              <Input
                value={momoForm.account_name}
                onChange={(e) => setMomoForm({...momoForm, account_name: e.target.value})}
                placeholder="Hospital name on mobile money"
                required
              />
            </div>
            
            <div className="space-y-2">
              <Label>Mobile Number *</Label>
              <Input
                value={momoForm.mobile_number}
                onChange={(e) => setMomoForm({...momoForm, mobile_number: e.target.value})}
                placeholder="e.g., 0244123456"
                required
              />
            </div>
            
            <div className="space-y-2">
              <Label>Wallet ID (Optional)</Label>
              <Input
                value={momoForm.wallet_id}
                onChange={(e) => setMomoForm({...momoForm, wallet_id: e.target.value})}
                placeholder="Merchant/Wallet ID if applicable"
              />
            </div>
            
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="primary-momo"
                checked={momoForm.is_primary}
                onChange={(e) => setMomoForm({...momoForm, is_primary: e.target.checked})}
                className="rounded"
              />
              <Label htmlFor="primary-momo" className="cursor-pointer">Set as primary mobile money account</Label>
            </div>
            
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setAddMoMoDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={saving} className="bg-blue-600 hover:bg-blue-700">
                {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                Add Mobile Money
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
