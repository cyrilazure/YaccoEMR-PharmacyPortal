import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import { hospitalAdminAPI, regionAPI, patientAPI } from '@/lib/api';
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
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import { 
  Users, Building2, MapPin, Plus, Search, RefreshCw,
  Settings, Shield, Activity, UserPlus, Key, Lock,
  CheckCircle, XCircle, AlertCircle, Loader2,
  LayoutDashboard, FileText, Clock, Copy, Check,
  UserCog, FolderTree, Mail, Phone, IdCard, Eye, Hash
} from 'lucide-react';

const STAFF_ROLES = [
  { value: 'physician', label: 'Physician' },
  { value: 'nurse', label: 'Nurse' },
  { value: 'scheduler', label: 'Scheduler' },
  { value: 'biller', label: 'Biller' },
  { value: 'hospital_admin', label: 'Hospital Admin' },
  { value: 'receptionist', label: 'Receptionist' },
  { value: 'lab_tech', label: 'Lab Technician' },
  { value: 'pharmacist', label: 'Pharmacist' },
];

export default function HospitalAdminPortal() {
  const { hospitalId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  
  // Get hospitalId from URL or user's organization
  const effectiveHospitalId = hospitalId || user?.organization_id;
  
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Data
  const [dashboard, setDashboard] = useState(null);
  const [users, setUsers] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [locations, setLocations] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [patients, setPatients] = useState([]);
  
  // Filters
  const [userSearch, setUserSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [patientSearch, setPatientSearch] = useState('');
  
  // Dialogs
  const [createUserOpen, setCreateUserOpen] = useState(false);
  const [createDeptOpen, setCreateDeptOpen] = useState(false);
  const [resetPasswordOpen, setResetPasswordOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [createdCredentials, setCreatedCredentials] = useState(null);
  const [createMRNOpen, setCreateMRNOpen] = useState(false);
  const [viewPatientOpen, setViewPatientOpen] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState(null);
  
  // Forms
  const [newUser, setNewUser] = useState({
    email: '',
    first_name: '',
    last_name: '',
    role: 'physician',
    department_id: '',
    location_id: '',
    phone: '',
    specialty: ''
  });
  const [newDept, setNewDept] = useState({
    name: '',
    code: '',
    department_type: 'clinical',
    description: ''
  });
  const [saving, setSaving] = useState(false);
  const [copiedPassword, setCopiedPassword] = useState(false);

  // Check access
  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    
    // Super admin can access any hospital
    if (user.role === 'super_admin') return;
    
    // Hospital admin can only access their own hospital
    if (user.role !== 'hospital_admin' && user.role !== 'admin') {
      toast.error('Access denied');
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
      const [dashboardRes, usersRes, deptsRes] = await Promise.all([
        hospitalAdminAPI.getDashboard(effectiveHospitalId),
        hospitalAdminAPI.listUsers(effectiveHospitalId, {}),
        hospitalAdminAPI.listDepartments(effectiveHospitalId)
      ]);
      
      setDashboard(dashboardRes.data);
      setUsers(usersRes.data.users || []);
      setDepartments(deptsRes.data.departments || []);
      
      // Load locations
      try {
        const locRes = await regionAPI.getHospitalLocations(effectiveHospitalId);
        setLocations(locRes.data.locations || []);
      } catch (e) {
        console.log('No locations found');
      }
    } catch (err) {
      console.error('Error fetching data:', err);
      toast.error('Failed to load hospital data');
    } finally {
      setLoading(false);
    }
  }, [effectiveHospitalId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const response = await hospitalAdminAPI.createUser(effectiveHospitalId, newUser);
      setCreatedCredentials({
        email: response.data.user.email,
        tempPassword: response.data.credentials.temp_password
      });
      toast.success('User created successfully!');
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create user');
    } finally {
      setSaving(false);
    }
  };

  const handleCreateDepartment = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await hospitalAdminAPI.createDepartment(effectiveHospitalId, newDept);
      toast.success('Department created!');
      setCreateDeptOpen(false);
      setNewDept({ name: '', code: '', department_type: 'clinical', description: '' });
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create department');
    } finally {
      setSaving(false);
    }
  };

  const handleResetPassword = async () => {
    if (!selectedUser) return;
    setSaving(true);
    try {
      const response = await hospitalAdminAPI.resetPassword(effectiveHospitalId, selectedUser.id);
      setCreatedCredentials({
        email: selectedUser.email,
        tempPassword: response.data.temp_password
      });
      toast.success('Password reset!');
      setResetPasswordOpen(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to reset password');
    } finally {
      setSaving(false);
    }
  };

  const handleDeactivateUser = async (userId) => {
    if (!confirm('Are you sure you want to deactivate this user?')) return;
    try {
      await hospitalAdminAPI.deactivateUser(effectiveHospitalId, userId);
      toast.success('User deactivated');
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to deactivate user');
    }
  };

  const handleReactivateUser = async (userId) => {
    try {
      await hospitalAdminAPI.reactivateUser(effectiveHospitalId, userId);
      toast.success('User reactivated');
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to reactivate user');
    }
  };

  const copyToClipboard = async (text) => {
    await navigator.clipboard.writeText(text);
    setCopiedPassword(true);
    setTimeout(() => setCopiedPassword(false), 2000);
  };

  const filteredUsers = users.filter(u => {
    if (roleFilter !== 'all' && u.role !== roleFilter) return false;
    if (!userSearch) return true;
    const query = userSearch.toLowerCase();
    return (
      u.email?.toLowerCase().includes(query) ||
      u.first_name?.toLowerCase().includes(query) ||
      u.last_name?.toLowerCase().includes(query)
    );
  });

  if (loading) {
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
            <Settings className="w-6 h-6 text-emerald-600" />
            Hospital Administration
          </h1>
          <p className="text-gray-500">{dashboard?.hospital?.name}</p>
        </div>
        <Button onClick={fetchData} variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total Staff</p>
                <p className="text-2xl font-bold">{dashboard?.stats?.total_users || 0}</p>
              </div>
              <Users className="w-8 h-8 text-emerald-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Departments</p>
                <p className="text-2xl font-bold">{dashboard?.stats?.total_departments || 0}</p>
              </div>
              <FolderTree className="w-8 h-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Locations</p>
                <p className="text-2xl font-bold">{dashboard?.stats?.total_locations || 0}</p>
              </div>
              <MapPin className="w-8 h-8 text-purple-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Pending</p>
                <p className="text-2xl font-bold">{dashboard?.stats?.pending_users || 0}</p>
              </div>
              <Clock className="w-8 h-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview" className="gap-2">
            <LayoutDashboard className="w-4 h-4" /> Overview
          </TabsTrigger>
          <TabsTrigger value="patients" className="gap-2">
            <Users className="w-4 h-4" /> Patient Records
          </TabsTrigger>
          <TabsTrigger value="users" className="gap-2">
            <UserCog className="w-4 h-4" /> Staff Directory
          </TabsTrigger>
          <TabsTrigger value="departments" className="gap-2">
            <FolderTree className="w-4 h-4" /> Departments
          </TabsTrigger>
          <TabsTrigger value="audit" className="gap-2">
            <FileText className="w-4 h-4" /> Audit Logs
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Role Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Staff by Role</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {dashboard?.role_distribution && Object.entries(dashboard.role_distribution).map(([role, count]) => (
                    <div key={role} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <span className="capitalize">{role.replace('_', ' ')}</span>
                      <Badge>{count}</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Departments */}
            <Card>
              <CardHeader>
                <CardTitle>Departments</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {departments.slice(0, 5).map((dept) => (
                    <div key={dept.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <div>
                        <p className="font-medium">{dept.name}</p>
                        <p className="text-xs text-gray-500">{dept.code}</p>
                      </div>
                      <Badge variant="secondary">{dept.user_count || 0} staff</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Users Tab */}
        <TabsContent value="users" className="mt-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Staff Directory</CardTitle>
                  <CardDescription>View hospital staff members. Contact IT Admin for new accounts.</CardDescription>
                </div>
                <Alert className="max-w-md">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription className="text-xs">
                    User creation is managed by the IT Administrator. Contact your Hospital IT Admin to add new staff.
                  </AlertDescription>
                </Alert>
              </div>
            </CardHeader>
            <CardContent>
              {/* Filters */}
              <div className="flex items-center gap-4 mb-4">
                <div className="relative flex-1 max-w-sm">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <Input
                    placeholder="Search staff..."
                    value={userSearch}
                    onChange={(e) => setUserSearch(e.target.value)}
                    className="pl-9"
                  />
                </div>
                <Select value={roleFilter} onValueChange={setRoleFilter}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder="Filter by role" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Roles</SelectItem>
                    {STAFF_ROLES.map(r => (
                      <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Users Table - Read Only */}
              <div className="rounded-lg border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Department</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredUsers.map((u) => (
                      <TableRow key={u.id}>
                        <TableCell className="font-medium">
                          {u.first_name} {u.last_name}
                        </TableCell>
                        <TableCell>{u.email}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className="capitalize">
                            {u.role?.replace('_', ' ')}
                          </Badge>
                        </TableCell>
                        <TableCell>{u.department_name || '-'}</TableCell>
                        <TableCell>
                          {u.is_active ? (
                            <Badge className="bg-emerald-100 text-emerald-700">Active</Badge>
                          ) : (
                            <Badge variant="secondary">Inactive</Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Departments Tab */}
        <TabsContent value="departments" className="mt-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Department Management</CardTitle>
                  <CardDescription>Organize hospital departments</CardDescription>
                </div>
                <Button onClick={() => setCreateDeptOpen(true)} className="bg-emerald-600 hover:bg-emerald-700">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Department
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {departments.map((dept) => (
                  <Card key={dept.id} className="border">
                    <CardContent className="pt-4">
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className="font-semibold">{dept.name}</h4>
                          <p className="text-sm text-gray-500">{dept.code}</p>
                          <Badge variant="outline" className="mt-2 capitalize">
                            {dept.department_type}
                          </Badge>
                        </div>
                        <Badge>{dept.user_count || 0} staff</Badge>
                      </div>
                      {dept.description && (
                        <p className="text-sm text-gray-500 mt-2">{dept.description}</p>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Audit Tab */}
        <TabsContent value="audit" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Audit Logs</CardTitle>
              <CardDescription>Track administrative actions</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                <div className="space-y-3">
                  {dashboard?.recent_activity?.map((log, idx) => (
                    <div key={idx} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                      <Activity className="w-4 h-4 text-gray-400 mt-1" />
                      <div className="flex-1">
                        <p className="text-sm">
                          <span className="font-medium">{log.user_email}</span>
                          {' - '}
                          <span className="capitalize">{log.action?.replace('_', ' ')}</span>
                        </p>
                        <p className="text-xs text-gray-500">{new Date(log.timestamp).toLocaleString()}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Create User Dialog */}
      <Dialog open={createUserOpen} onOpenChange={(open) => {
        setCreateUserOpen(open);
        if (!open) {
          setCreatedCredentials(null);
          setNewUser({
            email: '', first_name: '', last_name: '', role: 'physician',
            department_id: '', location_id: '', phone: '', specialty: ''
          });
        }
      }}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Add Staff Member</DialogTitle>
            <DialogDescription>Create a new staff account</DialogDescription>
          </DialogHeader>
          
          {createdCredentials ? (
            <div className="space-y-4">
              <Alert className="bg-emerald-50 border-emerald-200">
                <CheckCircle className="h-4 w-4 text-emerald-600" />
                <AlertTitle className="text-emerald-800">Staff Created!</AlertTitle>
                <AlertDescription className="text-emerald-700">
                  Save these credentials - the password cannot be retrieved later.
                </AlertDescription>
              </Alert>
              
              <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">Email</p>
                    <p className="font-medium">{createdCredentials.email}</p>
                  </div>
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">Temporary Password</p>
                    <p className="font-mono font-medium">{createdCredentials.tempPassword}</p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => copyToClipboard(createdCredentials.tempPassword)}
                  >
                    {copiedPassword ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  </Button>
                </div>
              </div>
              
              <DialogFooter>
                <Button onClick={() => {
                  setCreateUserOpen(false);
                  setCreatedCredentials(null);
                }}>Done</Button>
              </DialogFooter>
            </div>
          ) : (
            <form onSubmit={handleCreateUser} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>First Name *</Label>
                  <Input
                    value={newUser.first_name}
                    onChange={(e) => setNewUser({...newUser, first_name: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label>Last Name *</Label>
                  <Input
                    value={newUser.last_name}
                    onChange={(e) => setNewUser({...newUser, last_name: e.target.value})}
                    required
                  />
                </div>
                <div className="col-span-2">
                  <Label>Email *</Label>
                  <Input
                    type="email"
                    value={newUser.email}
                    onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label>Role *</Label>
                  <Select
                    value={newUser.role}
                    onValueChange={(v) => setNewUser({...newUser, role: v})}
                  >
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
                  <Label>Department</Label>
                  <Select
                    value={newUser.department_id}
                    onValueChange={(v) => setNewUser({...newUser, department_id: v})}
                  >
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
                  <Select
                    value={newUser.location_id}
                    onValueChange={(v) => setNewUser({...newUser, location_id: v})}
                  >
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
                <div>
                  <Label>Phone</Label>
                  <Input
                    value={newUser.phone}
                    onChange={(e) => setNewUser({...newUser, phone: e.target.value})}
                  />
                </div>
              </div>
              
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setCreateUserOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" className="bg-emerald-600 hover:bg-emerald-700" disabled={saving}>
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Create Staff'}
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>

      {/* Create Department Dialog */}
      <Dialog open={createDeptOpen} onOpenChange={setCreateDeptOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Department</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateDepartment} className="space-y-4">
            <div>
              <Label>Department Name *</Label>
              <Input
                value={newDept.name}
                onChange={(e) => setNewDept({...newDept, name: e.target.value})}
                placeholder="e.g., Cardiology"
                required
              />
            </div>
            <div>
              <Label>Code *</Label>
              <Input
                value={newDept.code}
                onChange={(e) => setNewDept({...newDept, code: e.target.value.toUpperCase()})}
                placeholder="e.g., CARD"
                required
              />
            </div>
            <div>
              <Label>Type</Label>
              <Select
                value={newDept.department_type}
                onValueChange={(v) => setNewDept({...newDept, department_type: v})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="clinical">Clinical</SelectItem>
                  <SelectItem value="administrative">Administrative</SelectItem>
                  <SelectItem value="support">Support</SelectItem>
                  <SelectItem value="diagnostic">Diagnostic</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Description</Label>
              <Input
                value={newDept.description}
                onChange={(e) => setNewDept({...newDept, description: e.target.value})}
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setCreateDeptOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" className="bg-emerald-600 hover:bg-emerald-700" disabled={saving}>
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Create'}
              </Button>
            </DialogFooter>
          </form>
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
              Generate a new temporary password for {selectedUser?.email}
            </DialogDescription>
          </DialogHeader>
          
          {createdCredentials ? (
            <div className="space-y-4">
              <Alert className="bg-emerald-50 border-emerald-200">
                <CheckCircle className="h-4 w-4 text-emerald-600" />
                <AlertTitle className="text-emerald-800">Password Reset!</AlertTitle>
              </Alert>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">New Password</p>
                    <p className="font-mono font-medium">{createdCredentials.tempPassword}</p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => copyToClipboard(createdCredentials.tempPassword)}
                  >
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
              <Button variant="outline" onClick={() => setResetPasswordOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleResetPassword} disabled={saving}>
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Reset Password'}
              </Button>
            </DialogFooter>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
