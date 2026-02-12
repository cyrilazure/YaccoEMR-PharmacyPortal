import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/lib/auth';
import { adminAPI, usersAPI, organizationAPI, auditAPI } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Checkbox } from '@/components/ui/checkbox';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Dialog, DialogContent, DialogDescription, 
  DialogHeader, DialogTitle, DialogTrigger, DialogFooter 
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
import { toast } from 'sonner';
import { formatDateTime, getRoleDisplayName } from '@/lib/utils';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { 
  Users, UserPlus, Settings, Shield, Activity, TrendingUp, 
  BarChart3, Clock, Database, Server, Search, MoreVertical,
  UserCog, FileText, CheckCircle2, XCircle, Eye, Lock, Unlock,
  RefreshCw, Share2, AlertTriangle, ChevronRight, Building2
} from 'lucide-react';

const ROLE_COLORS = {
  physician: '#3b82f6',
  nurse: '#10b981',
  scheduler: '#f59e0b',
  admin: '#8b5cf6',
  hospital_admin: '#ec4899',
  lab_tech: '#06b6d4'
};

export default function AdminDashboard() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Data
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [permissionGroups, setPermissionGroups] = useState([]);
  const [availablePermissions, setAvailablePermissions] = useState([]);
  const [sharingPolicies, setSharingPolicies] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  
  // Filters
  const [userSearch, setUserSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  
  // Dialogs
  const [createUserOpen, setCreateUserOpen] = useState(false);
  const [editUserOpen, setEditUserOpen] = useState(false);
  const [createGroupOpen, setCreateGroupOpen] = useState(false);
  const [bulkActionOpen, setBulkActionOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedUsers, setSelectedUsers] = useState([]);
  
  // Forms
  const [newUser, setNewUser] = useState({
    email: '', password: '', first_name: '', last_name: '',
    role: 'nurse', department: '', specialty: ''
  });
  const [newGroup, setNewGroup] = useState({
    name: '', description: '', permissions: []
  });
  const [userRoleUpdate, setUserRoleUpdate] = useState({
    role: '', permissions_groups: [], custom_permissions: []
  });
  const [bulkAction, setBulkAction] = useState({ action: '', reason: '' });
  const [saving, setSaving] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [statsRes, usersRes, groupsRes, permsRes, policiesRes] = await Promise.all([
        adminAPI.getDashboardStats(),
        adminAPI.getUsers({ limit: 100 }),
        adminAPI.getPermissionGroups(),
        adminAPI.getAvailablePermissions(),
        adminAPI.getSharingPolicies({ direction: 'incoming' })
      ]);
      
      setStats(statsRes.data);
      setUsers(usersRes.data.users || []);
      setPermissionGroups(groupsRes.data.groups || []);
      setAvailablePermissions(permsRes.data.permissions || []);
      setSharingPolicies(policiesRes.data.policies || []);
    } catch (err) {
      console.error('Admin dashboard fetch error:', err);
      toast.error('Failed to load admin data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newUser)
      });
      
      if (response.ok) {
        toast.success('User created successfully');
        setCreateUserOpen(false);
        setNewUser({ email: '', password: '', first_name: '', last_name: '', role: 'nurse', department: '', specialty: '' });
        fetchData();
      } else {
        const data = await response.json();
        toast.error(data.detail || 'Failed to create user');
      }
    } catch (err) {
      toast.error('Failed to create user');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateUserRole = async () => {
    if (!selectedUser) return;
    setSaving(true);
    try {
      await adminAPI.updateUserRole(selectedUser.id, {
        user_id: selectedUser.id,
        role: userRoleUpdate.role || selectedUser.role,
        permissions_groups: userRoleUpdate.permissions_groups,
        custom_permissions: userRoleUpdate.custom_permissions
      });
      toast.success('User role updated');
      setEditUserOpen(false);
      setSelectedUser(null);
      fetchData();
    } catch (err) {
      toast.error('Failed to update user role');
    } finally {
      setSaving(false);
    }
  };

  const handleBulkAction = async () => {
    if (selectedUsers.length === 0) return;
    setSaving(true);
    try {
      const result = await adminAPI.bulkUserAction({
        user_ids: selectedUsers,
        action: bulkAction.action,
        reason: bulkAction.reason
      });
      toast.success(`Action completed: ${result.data.success} successful, ${result.data.failed} failed`);
      setBulkActionOpen(false);
      setSelectedUsers([]);
      setBulkAction({ action: '', reason: '' });
      fetchData();
    } catch (err) {
      toast.error('Bulk action failed');
    } finally {
      setSaving(false);
    }
  };

  const handleCreateGroup = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await adminAPI.createPermissionGroup(newGroup);
      toast.success('Permission group created');
      setCreateGroupOpen(false);
      setNewGroup({ name: '', description: '', permissions: [] });
      fetchData();
    } catch (err) {
      toast.error('Failed to create permission group');
    } finally {
      setSaving(false);
    }
  };

  const handleApproveSharingPolicy = async (policyId) => {
    try {
      await adminAPI.approveSharingPolicy(policyId, {
        approved_data_types: ['patient_records', 'lab_results'],
        duration_days: 365
      });
      toast.success('Sharing policy approved');
      fetchData();
    } catch (err) {
      toast.error('Failed to approve policy');
    }
  };

  const handleDenySharingPolicy = async (policyId) => {
    try {
      await adminAPI.denySharingPolicy(policyId, 'Policy not compliant with organizational requirements');
      toast.success('Sharing policy denied');
      fetchData();
    } catch (err) {
      toast.error('Failed to deny policy');
    }
  };

  // Filter users
  const filteredUsers = users.filter(u => {
    const matchesSearch = !userSearch || 
      u.first_name?.toLowerCase().includes(userSearch.toLowerCase()) ||
      u.last_name?.toLowerCase().includes(userSearch.toLowerCase()) ||
      u.email?.toLowerCase().includes(userSearch.toLowerCase());
    const matchesRole = roleFilter === 'all' || u.role === roleFilter;
    const matchesStatus = statusFilter === 'all' || 
      (statusFilter === 'active' && u.is_active) || 
      (statusFilter === 'inactive' && !u.is_active);
    return matchesSearch && matchesRole && matchesStatus;
  });

  // Role distribution for chart
  const roleDistData = stats?.role_distribution ? 
    Object.entries(stats.role_distribution).map(([role, count]) => ({
      name: getRoleDisplayName(role),
      value: count,
      color: ROLE_COLORS[role] || '#6b7280'
    })) : [];

  if (user?.role !== 'hospital_admin' && user?.role !== 'super_admin') {
    return (
      <div className="flex items-center justify-center h-96">
        <Card className="w-96 text-center">
          <CardContent className="pt-8">
            <Shield className="w-16 h-16 mx-auto mb-4 text-red-500" />
            <h2 className="text-xl font-bold mb-2">Access Denied</h2>
            <p className="text-slate-500">Hospital Admin access required</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (loading && !stats) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-32" />)}
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="admin-dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center shadow-lg">
            <Shield className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Hospital Administration</h1>
            <p className="text-slate-500">Manage users, roles, and policies</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="icon" onClick={fetchData}>
            <RefreshCw className="w-4 h-4" />
          </Button>
          <Dialog open={createUserOpen} onOpenChange={setCreateUserOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2 bg-purple-600 hover:bg-purple-700">
                <UserPlus className="w-4 h-4" />Add User
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create New User</DialogTitle>
                <DialogDescription>Add a new staff member to your organization</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleCreateUser} className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>First Name *</Label>
                    <Input 
                      value={newUser.first_name} 
                      onChange={(e) => setNewUser({ ...newUser, first_name: e.target.value })} 
                      required 
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Last Name *</Label>
                    <Input 
                      value={newUser.last_name} 
                      onChange={(e) => setNewUser({ ...newUser, last_name: e.target.value })} 
                      required 
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Email *</Label>
                  <Input 
                    type="email" 
                    value={newUser.email} 
                    onChange={(e) => setNewUser({ ...newUser, email: e.target.value })} 
                    required 
                  />
                </div>
                <div className="space-y-2">
                  <Label>Password *</Label>
                  <Input 
                    type="password" 
                    value={newUser.password} 
                    onChange={(e) => setNewUser({ ...newUser, password: e.target.value })} 
                    required 
                  />
                </div>
                <div className="space-y-2">
                  <Label>Role *</Label>
                  <Select value={newUser.role} onValueChange={(v) => setNewUser({ ...newUser, role: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="physician">Physician</SelectItem>
                      <SelectItem value="nurse">Nurse</SelectItem>
                      <SelectItem value="scheduler">Scheduler</SelectItem>
                      <SelectItem value="admin">Administrator</SelectItem>
                      <SelectItem value="lab_tech">Lab Technician</SelectItem>
                      <SelectItem value="billing">Billing Staff</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Department</Label>
                    <Input 
                      value={newUser.department} 
                      onChange={(e) => setNewUser({ ...newUser, department: e.target.value })} 
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Specialty</Label>
                    <Input 
                      value={newUser.specialty} 
                      onChange={(e) => setNewUser({ ...newUser, specialty: e.target.value })} 
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button type="submit" disabled={saving}>
                    {saving ? 'Creating...' : 'Create User'}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Users</p>
                <p className="text-2xl font-bold text-slate-900">{stats?.users?.total || 0}</p>
                <p className="text-xs text-emerald-600">{stats?.users?.active || 0} active</p>
              </div>
              <Users className="w-10 h-10 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-emerald-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Patients</p>
                <p className="text-2xl font-bold text-slate-900">{stats?.patients?.total || 0}</p>
              </div>
              <Activity className="w-10 h-10 text-emerald-500" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-amber-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Activity (24h)</p>
                <p className="text-2xl font-bold text-slate-900">{stats?.activity_24h || 0}</p>
              </div>
              <BarChart3 className="w-10 h-10 text-amber-500" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Pending Policies</p>
                <p className="text-2xl font-bold text-slate-900">{stats?.pending_sharing_requests || 0}</p>
              </div>
              <Share2 className="w-10 h-10 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="users">User Management</TabsTrigger>
          <TabsTrigger value="roles">Roles & Groups</TabsTrigger>
          <TabsTrigger value="policies">Sharing Policies</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>User Distribution by Role</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={roleDistData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                        label={({ name, value }) => `${name}: ${value}`}
                      >
                        {roleDistData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button 
                  variant="outline" 
                  className="w-full justify-start gap-2"
                  onClick={() => setCreateUserOpen(true)}
                >
                  <UserPlus className="w-4 h-4" />Add New User
                </Button>
                <Button 
                  variant="outline" 
                  className="w-full justify-start gap-2"
                  onClick={() => setCreateGroupOpen(true)}
                >
                  <UserCog className="w-4 h-4" />Create Permission Group
                </Button>
                <Button 
                  variant="outline" 
                  className="w-full justify-start gap-2"
                  onClick={() => setActiveTab('policies')}
                >
                  <Share2 className="w-4 h-4" />Review Sharing Policies
                  {(stats?.pending_sharing_requests || 0) > 0 && (
                    <Badge variant="destructive" className="ml-auto">{stats.pending_sharing_requests}</Badge>
                  )}
                </Button>
                <Button 
                  variant="outline" 
                  className="w-full justify-start gap-2"
                  onClick={() => window.location.href = '/audit-logs'}
                >
                  <FileText className="w-4 h-4" />View Audit Logs
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Locked Accounts Alert */}
          {(stats?.users?.locked || 0) > 0 && (
            <Alert className="border-red-200 bg-red-50">
              <Lock className="h-4 w-4 text-red-600" />
              <AlertTitle className="text-red-800">Locked Accounts</AlertTitle>
              <AlertDescription className="text-red-700">
                {stats.users.locked} user account(s) are currently locked. 
                <Button variant="link" className="p-0 h-auto text-red-700" onClick={() => setActiveTab('users')}>
                  Review and unlock
                </Button>
              </AlertDescription>
            </Alert>
          )}
        </TabsContent>

        {/* Users Tab */}
        <TabsContent value="users" className="space-y-4">
          {/* Filters */}
          <div className="flex items-center gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="Search users..."
                className="pl-10"
                value={userSearch}
                onChange={(e) => setUserSearch(e.target.value)}
              />
            </div>
            <Select value={roleFilter} onValueChange={setRoleFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Filter by role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Roles</SelectItem>
                <SelectItem value="physician">Physicians</SelectItem>
                <SelectItem value="nurse">Nurses</SelectItem>
                <SelectItem value="scheduler">Schedulers</SelectItem>
                <SelectItem value="admin">Admins</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
              </SelectContent>
            </Select>
            {selectedUsers.length > 0 && (
              <Button 
                variant="outline" 
                className="gap-2"
                onClick={() => setBulkActionOpen(true)}
              >
                Bulk Action ({selectedUsers.length})
              </Button>
            )}
          </div>

          {/* Users Table */}
          <Card>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <Checkbox
                      checked={selectedUsers.length === filteredUsers.length && filteredUsers.length > 0}
                      onCheckedChange={(checked) => {
                        setSelectedUsers(checked ? filteredUsers.map(u => u.id) : []);
                      }}
                    />
                  </TableHead>
                  <TableHead>User</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Department</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Active</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredUsers.map((u) => (
                  <TableRow key={u.id}>
                    <TableCell>
                      <Checkbox
                        checked={selectedUsers.includes(u.id)}
                        onCheckedChange={(checked) => {
                          setSelectedUsers(prev => 
                            checked ? [...prev, u.id] : prev.filter(id => id !== u.id)
                          );
                        }}
                      />
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">{u.first_name} {u.last_name}</p>
                        <p className="text-sm text-slate-500">{u.email}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge style={{ backgroundColor: ROLE_COLORS[u.role] || '#6b7280' }} className="text-white">
                        {getRoleDisplayName(u.role)}
                      </Badge>
                    </TableCell>
                    <TableCell>{u.department || '-'}</TableCell>
                    <TableCell>
                      {u.is_active ? (
                        <Badge className="bg-emerald-100 text-emerald-700">Active</Badge>
                      ) : (
                        <Badge className="bg-red-100 text-red-700">Inactive</Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-sm text-slate-500">
                      {u.last_login ? formatDateTime(u.last_login) : 'Never'}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => {
                          setSelectedUser(u);
                          setUserRoleUpdate({
                            role: u.role,
                            permissions_groups: u.permission_groups || [],
                            custom_permissions: u.custom_permissions || []
                          });
                          setEditUserOpen(true);
                        }}
                      >
                        <UserCog className="w-4 h-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>

        {/* Roles & Groups Tab */}
        <TabsContent value="roles" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Permission Groups</h3>
            <Dialog open={createGroupOpen} onOpenChange={setCreateGroupOpen}>
              <DialogTrigger asChild>
                <Button className="gap-2">
                  <UserCog className="w-4 h-4" />Create Group
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Create Permission Group</DialogTitle>
                  <DialogDescription>Define a reusable set of permissions</DialogDescription>
                </DialogHeader>
                <form onSubmit={handleCreateGroup} className="space-y-4 mt-4">
                  <div className="space-y-2">
                    <Label>Group Name *</Label>
                    <Input
                      value={newGroup.name}
                      onChange={(e) => setNewGroup({ ...newGroup, name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Description</Label>
                    <Textarea
                      value={newGroup.description}
                      onChange={(e) => setNewGroup({ ...newGroup, description: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Permissions</Label>
                    <ScrollArea className="h-48 border rounded-lg p-3">
                      <div className="grid grid-cols-2 gap-2">
                        {availablePermissions.map((p) => (
                          <div key={p.key} className="flex items-center gap-2">
                            <Checkbox
                              checked={newGroup.permissions.includes(p.key)}
                              onCheckedChange={(checked) => {
                                setNewGroup(prev => ({
                                  ...prev,
                                  permissions: checked
                                    ? [...prev.permissions, p.key]
                                    : prev.permissions.filter(k => k !== p.key)
                                }));
                              }}
                            />
                            <span className="text-sm">{p.description}</span>
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  </div>
                  <DialogFooter>
                    <Button type="submit" disabled={saving}>
                      {saving ? 'Creating...' : 'Create Group'}
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {permissionGroups.map((group) => (
              <Card key={group.id}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">{group.name}</CardTitle>
                    {group.is_system && (
                      <Badge variant="secondary">System</Badge>
                    )}
                  </div>
                  <CardDescription>{group.description || 'No description'}</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-slate-500 mb-2">
                    {group.permissions?.length || 0} permissions
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {(group.permissions || []).slice(0, 5).map((p) => (
                      <Badge key={p} variant="outline" className="text-xs">{p}</Badge>
                    ))}
                    {(group.permissions?.length || 0) > 5 && (
                      <Badge variant="outline" className="text-xs">+{group.permissions.length - 5} more</Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Sharing Policies Tab */}
        <TabsContent value="policies" className="space-y-4">
          <Alert className="border-blue-200 bg-blue-50">
            <Share2 className="h-4 w-4 text-blue-600" />
            <AlertTitle className="text-blue-800">Record Sharing Policies</AlertTitle>
            <AlertDescription className="text-blue-700">
              Review and approve requests from other organizations to access patient records.
            </AlertDescription>
          </Alert>

          <Card>
            <CardHeader>
              <CardTitle>Incoming Policy Requests</CardTitle>
            </CardHeader>
            <CardContent>
              {sharingPolicies.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <Share2 className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                  <p>No pending sharing policy requests</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {sharingPolicies.map((policy) => (
                    <div key={policy.id} className="p-4 border rounded-lg">
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <Building2 className="w-4 h-4 text-slate-500" />
                            <span className="font-medium">{policy.requesting_organization_name}</span>
                            <Badge className={
                              policy.status === 'pending' ? 'bg-amber-100 text-amber-700' :
                              policy.status === 'approved' ? 'bg-emerald-100 text-emerald-700' :
                              'bg-red-100 text-red-700'
                            }>
                              {policy.status}
                            </Badge>
                          </div>
                          <p className="text-sm text-slate-500 mt-1">{policy.justification}</p>
                          <div className="flex items-center gap-4 mt-2 text-xs text-slate-400">
                            <span>Type: {policy.policy_type}</span>
                            <span>Duration: {policy.duration_days} days</span>
                            <span>Requested: {formatDateTime(policy.requested_at)}</span>
                          </div>
                        </div>
                        {policy.status === 'pending' && (
                          <div className="flex items-center gap-2">
                            <Button 
                              size="sm" 
                              className="bg-emerald-600 hover:bg-emerald-700"
                              onClick={() => handleApproveSharingPolicy(policy.id)}
                            >
                              <CheckCircle2 className="w-4 h-4 mr-1" />Approve
                            </Button>
                            <Button 
                              size="sm" 
                              variant="destructive"
                              onClick={() => handleDenySharingPolicy(policy.id)}
                            >
                              <XCircle className="w-4 h-4 mr-1" />Deny
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Edit User Dialog */}
      <Dialog open={editUserOpen} onOpenChange={setEditUserOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit User Role</DialogTitle>
            <DialogDescription>
              {selectedUser && `${selectedUser.first_name} ${selectedUser.last_name}`}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label>Role</Label>
              <Select 
                value={userRoleUpdate.role} 
                onValueChange={(v) => setUserRoleUpdate({ ...userRoleUpdate, role: v })}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="physician">Physician</SelectItem>
                  <SelectItem value="nurse">Nurse</SelectItem>
                  <SelectItem value="scheduler">Scheduler</SelectItem>
                  <SelectItem value="admin">Administrator</SelectItem>
                  <SelectItem value="lab_tech">Lab Technician</SelectItem>
                  <SelectItem value="billing">Billing Staff</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Permission Groups</Label>
              <div className="border rounded-lg p-3 space-y-2">
                {permissionGroups.map((g) => (
                  <div key={g.id} className="flex items-center gap-2">
                    <Checkbox
                      checked={userRoleUpdate.permissions_groups.includes(g.id)}
                      onCheckedChange={(checked) => {
                        setUserRoleUpdate(prev => ({
                          ...prev,
                          permissions_groups: checked
                            ? [...prev.permissions_groups, g.id]
                            : prev.permissions_groups.filter(id => id !== g.id)
                        }));
                      }}
                    />
                    <span className="text-sm">{g.name}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setEditUserOpen(false)}>Cancel</Button>
            <Button onClick={handleUpdateUserRole} disabled={saving}>
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Bulk Action Dialog */}
      <Dialog open={bulkActionOpen} onOpenChange={setBulkActionOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Bulk User Action</DialogTitle>
            <DialogDescription>
              Apply action to {selectedUsers.length} selected user(s)
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label>Action</Label>
              <Select 
                value={bulkAction.action} 
                onValueChange={(v) => setBulkAction({ ...bulkAction, action: v })}
              >
                <SelectTrigger><SelectValue placeholder="Select action" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="activate">Activate Users</SelectItem>
                  <SelectItem value="deactivate">Deactivate Users</SelectItem>
                  <SelectItem value="unlock">Unlock Accounts</SelectItem>
                  <SelectItem value="force_logout">Force Logout</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Reason (optional)</Label>
              <Textarea
                value={bulkAction.reason}
                onChange={(e) => setBulkAction({ ...bulkAction, reason: e.target.value })}
                placeholder="Reason for this action..."
              />
            </div>
          </div>
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setBulkActionOpen(false)}>Cancel</Button>
            <Button onClick={handleBulkAction} disabled={saving || !bulkAction.action}>
              {saving ? 'Processing...' : 'Apply Action'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
