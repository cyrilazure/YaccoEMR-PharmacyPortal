import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/lib/auth';
import { adminAPI, organizationAPI, pharmacyAdminAPI } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Switch } from '@/components/ui/switch';
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
import { formatDateTime } from '@/lib/utils';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';
import { 
  Building2, Shield, Activity, TrendingUp, Server, Database,
  AlertTriangle, Users, Settings, Lock, CheckCircle2, XCircle,
  RefreshCw, Eye, Search, Globe, FileText, Clock, Zap,
  ShieldCheck, ShieldAlert, AlertCircle, Play, Pause, Pill, Hospital
} from 'lucide-react';

const STATUS_COLORS = {
  active: '#10b981',
  pending: '#f59e0b',
  suspended: '#ef4444',
  inactive: '#6b7280'
};

export default function SuperAdminDashboard() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Data
  const [systemHealth, setSystemHealth] = useState(null);
  const [platformStats, setPlatformStats] = useState(null);
  const [securityPolicies, setSecurityPolicies] = useState([]);
  const [organizations, setOrganizations] = useState([]);
  const [pharmacies, setPharmacies] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [securityAlerts, setSecurityAlerts] = useState({ alerts: [], summary: {} });
  
  // Counts
  const [pendingHospitals, setPendingHospitals] = useState(0);
  const [pendingPharmacies, setPendingPharmacies] = useState(0);
  
  // Filters
  const [orgSearch, setOrgSearch] = useState('');
  const [pharmacySearch, setPharmacySearch] = useState('');
  const [auditFilter, setAuditFilter] = useState({ days: 7, org: 'all' });
  
  // Dialogs
  const [createOrgOpen, setCreateOrgOpen] = useState(false);
  const [editPolicyOpen, setEditPolicyOpen] = useState(false);
  const [selectedOrg, setSelectedOrg] = useState(null);
  const [selectedPolicy, setSelectedPolicy] = useState(null);
  
  // Forms
  const [newOrg, setNewOrg] = useState({
    name: '', type: 'hospital', contact_email: '', phone: '',
    address: '', city: '', state: '', zip_code: ''
  });
  const [policySettings, setPolicySettings] = useState({});
  const [saving, setSaving] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [healthRes, statsRes, policiesRes, orgsRes, alertsRes, pharmaciesRes] = await Promise.all([
        adminAPI.getSystemHealth(),
        adminAPI.getPlatformStats(),
        adminAPI.getSecurityPolicies(),
        organizationAPI.getOrganizations(),
        adminAPI.getSecurityAlerts(24),
        pharmacyAdminAPI.listAll()
      ]);
      
      setSystemHealth(healthRes.data);
      setPlatformStats(statsRes.data);
      setSecurityPolicies(policiesRes.data.policies || []);
      setOrganizations(orgsRes.data.organizations || []);
      setPharmacies(pharmaciesRes.data.pharmacies || []);
      setSecurityAlerts(alertsRes.data);
      
      // Count pending
      setPendingHospitals((orgsRes.data.organizations || []).filter(o => o.status === 'pending').length);
      setPendingPharmacies(pharmaciesRes.data.pending_count || 0);
    } catch (err) {
      console.error('Super admin dashboard fetch error:', err);
      toast.error('Failed to load system data');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchAuditLogs = useCallback(async () => {
    try {
      const params = {
        days: auditFilter.days,
        limit: 50
      };
      if (auditFilter.org !== 'all') {
        params.organization_id = auditFilter.org;
      }
      const res = await adminAPI.getSystemAuditLogs(params);
      setAuditLogs(res.data.logs || []);
    } catch (err) {
      console.error('Audit logs fetch error:', err);
    }
  }, [auditFilter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (activeTab === 'audit') {
      fetchAuditLogs();
    }
  }, [activeTab, fetchAuditLogs]);

  const handleCreateOrg = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await organizationAPI.register({
        ...newOrg,
        admin_email: newOrg.contact_email,
        admin_password: 'TempPassword123!',
        admin_first_name: 'Admin',
        admin_last_name: newOrg.name
      });
      toast.success('Organization created successfully');
      setCreateOrgOpen(false);
      setNewOrg({ name: '', type: 'hospital', contact_email: '', phone: '', address: '', city: '', state: '', zip_code: '' });
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create organization');
    } finally {
      setSaving(false);
    }
  };

  const handleOrgAction = async (orgId, action) => {
    try {
      if (action === 'approve') {
        await organizationAPI.approve(orgId);
        toast.success('Hospital approved');
      } else if (action === 'suspend') {
        await organizationAPI.suspend(orgId, 'Suspended by super admin');
        toast.success('Hospital suspended');
      } else if (action === 'reactivate') {
        await organizationAPI.reactivate(orgId);
        toast.success('Hospital reactivated');
      } else if (action === 'reject') {
        await organizationAPI.reject(orgId, { reason: 'Rejected by super admin' });
        toast.success('Hospital rejected');
      }
      fetchData();
    } catch (err) {
      toast.error('Action failed');
    }
  };

  const handlePharmacyAction = async (pharmacyId, action) => {
    try {
      if (action === 'approve') {
        await pharmacyAdminAPI.approve(pharmacyId, 'Approved by super admin');
        toast.success('Pharmacy approved');
      } else if (action === 'reject') {
        await pharmacyAdminAPI.reject(pharmacyId, 'Rejected by super admin');
        toast.success('Pharmacy rejected');
      } else if (action === 'suspend') {
        await pharmacyAdminAPI.suspend(pharmacyId, 'Suspended by super admin');
        toast.success('Pharmacy suspended');
      } else if (action === 'reactivate') {
        await pharmacyAdminAPI.reactivate(pharmacyId);
        toast.success('Pharmacy reactivated');
      }
      fetchData();
    } catch (err) {
      toast.error('Action failed');
    }
  };

  const handleTogglePolicy = async (policyType, isActive) => {
    try {
      await adminAPI.toggleSecurityPolicy(policyType, isActive);
      toast.success(`Policy ${isActive ? 'enabled' : 'disabled'}`);
      fetchData();
    } catch (err) {
      toast.error('Failed to update policy');
    }
  };

  const handleUpdatePolicy = async () => {
    if (!selectedPolicy) return;
    setSaving(true);
    try {
      await adminAPI.createSecurityPolicy({
        policy_type: selectedPolicy.policy_type,
        name: selectedPolicy.name,
        settings: policySettings
      });
      toast.success('Policy updated');
      setEditPolicyOpen(false);
      fetchData();
    } catch (err) {
      toast.error('Failed to update policy');
    } finally {
      setSaving(false);
    }
  };

  // Filter organizations
  const filteredOrgs = organizations.filter(o =>
    !orgSearch || o.name?.toLowerCase().includes(orgSearch.toLowerCase())
  );

  // Activity trend chart data
  const activityData = platformStats?.activity_trend || [];

  // Org status distribution
  const orgStatusData = platformStats?.organizations ? 
    Object.entries(platformStats.organizations).map(([status, count]) => ({
      name: status.charAt(0).toUpperCase() + status.slice(1),
      value: count,
      color: STATUS_COLORS[status] || '#6b7280'
    })) : [];

  if (user?.role !== 'super_admin') {
    return (
      <div className="flex items-center justify-center h-96">
        <Card className="w-96 text-center">
          <CardContent className="pt-8">
            <ShieldAlert className="w-16 h-16 mx-auto mb-4 text-red-500" />
            <h2 className="text-xl font-bold mb-2">Access Denied</h2>
            <p className="text-slate-500">Super Admin access required</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (loading && !systemHealth) {
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
    <div className="space-y-6 animate-fade-in" data-testid="super-admin-dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-red-500 to-red-600 flex items-center justify-center shadow-lg">
            <ShieldCheck className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Platform Administration</h1>
            <p className="text-slate-500">System-wide management and security</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Badge 
            className={systemHealth?.status === 'healthy' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}
          >
            System: {systemHealth?.status || 'Unknown'}
          </Badge>
          <Button variant="outline" size="icon" onClick={fetchData}>
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* System Health Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-emerald-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Organizations</p>
                <p className="text-2xl font-bold text-slate-900">{systemHealth?.stats?.total_organizations || 0}</p>
                <p className="text-xs text-emerald-600">{systemHealth?.stats?.active_organizations || 0} active</p>
              </div>
              <Building2 className="w-10 h-10 text-emerald-500" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Users</p>
                <p className="text-2xl font-bold text-slate-900">{systemHealth?.stats?.total_users || 0}</p>
              </div>
              <Users className="w-10 h-10 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Patients</p>
                <p className="text-2xl font-bold text-slate-900">{systemHealth?.stats?.total_patients || 0}</p>
              </div>
              <Activity className="w-10 h-10 text-purple-500" />
            </div>
          </CardContent>
        </Card>
        <Card className={`border-l-4 ${securityAlerts.total > 0 ? 'border-l-red-500' : 'border-l-emerald-500'}`}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Security Alerts (24h)</p>
                <p className="text-2xl font-bold text-slate-900">{securityAlerts.total || 0}</p>
              </div>
              <AlertTriangle className={`w-10 h-10 ${securityAlerts.total > 0 ? 'text-red-500' : 'text-emerald-500'}`} />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pending Approvals Alert */}
      {(pendingHospitals > 0 || pendingPharmacies > 0) && (
        <Alert className="border-amber-200 bg-amber-50">
          <AlertTriangle className="h-4 w-4 text-amber-600" />
          <AlertTitle className="text-amber-800">Pending Approvals</AlertTitle>
          <AlertDescription className="text-amber-700 flex items-center gap-4">
            {pendingHospitals > 0 && (
              <span className="flex items-center gap-1">
                <Hospital className="w-4 h-4" /> {pendingHospitals} Hospital(s)
              </span>
            )}
            {pendingPharmacies > 0 && (
              <span className="flex items-center gap-1">
                <Pill className="w-4 h-4" /> {pendingPharmacies} Pharmacy(s)
              </span>
            )}
          </AlertDescription>
        </Alert>
      )}

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="hospitals" className="gap-1">
            <Hospital className="w-4 h-4" /> Hospitals
            {pendingHospitals > 0 && <Badge className="ml-1 bg-amber-500 text-white text-xs">{pendingHospitals}</Badge>}
          </TabsTrigger>
          <TabsTrigger value="pharmacies" className="gap-1">
            <Pill className="w-4 h-4" /> Pharmacies
            {pendingPharmacies > 0 && <Badge className="ml-1 bg-amber-500 text-white text-xs">{pendingPharmacies}</Badge>}
          </TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
          <TabsTrigger value="audit">Audit</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* System Health */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Server className="w-5 h-5" />System Health
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {systemHealth?.checks?.map((check, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        {check.status === 'healthy' ? (
                          <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                        ) : (
                          <XCircle className="w-5 h-5 text-red-500" />
                        )}
                        <span className="font-medium">{check.component}</span>
                      </div>
                      <Badge className={check.status === 'healthy' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}>
                        {check.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Activity Trend */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />Activity Trend (7 days)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={activityData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Organization Distribution */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Organizations by Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={orgStatusData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={5}
                        dataKey="value"
                        label={({ name, value }) => `${name}: ${value}`}
                      >
                        {orgStatusData.map((entry, index) => (
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
                <CardTitle>Users by Role</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={platformStats?.users_by_role ? Object.entries(platformStats.users_by_role).map(([role, count]) => ({ role, count })) : []}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="role" tick={{ fontSize: 10 }} />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="count" fill="#8b5cf6" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Organizations Tab */}
        <TabsContent value="organizations" className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="Search organizations..."
                className="pl-10"
                value={orgSearch}
                onChange={(e) => setOrgSearch(e.target.value)}
              />
            </div>
            <Dialog open={createOrgOpen} onOpenChange={setCreateOrgOpen}>
              <DialogTrigger asChild>
                <Button className="gap-2 bg-red-600 hover:bg-red-700">
                  <Building2 className="w-4 h-4" />Create Organization
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-lg">
                <DialogHeader>
                  <DialogTitle>Create New Organization</DialogTitle>
                  <DialogDescription>Add a new hospital or clinic to the platform</DialogDescription>
                </DialogHeader>
                <form onSubmit={handleCreateOrg} className="space-y-4 mt-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2 col-span-2">
                      <Label>Organization Name *</Label>
                      <Input
                        value={newOrg.name}
                        onChange={(e) => setNewOrg({ ...newOrg, name: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Type *</Label>
                      <Select value={newOrg.type} onValueChange={(v) => setNewOrg({ ...newOrg, type: v })}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="hospital">Hospital</SelectItem>
                          <SelectItem value="clinic">Clinic</SelectItem>
                          <SelectItem value="practice">Private Practice</SelectItem>
                          <SelectItem value="lab">Laboratory</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Contact Email *</Label>
                      <Input
                        type="email"
                        value={newOrg.contact_email}
                        onChange={(e) => setNewOrg({ ...newOrg, contact_email: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Phone</Label>
                      <Input
                        value={newOrg.phone}
                        onChange={(e) => setNewOrg({ ...newOrg, phone: e.target.value })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>City</Label>
                      <Input
                        value={newOrg.city}
                        onChange={(e) => setNewOrg({ ...newOrg, city: e.target.value })}
                      />
                    </div>
                  </div>
                  <DialogFooter>
                    <Button type="submit" disabled={saving}>
                      {saving ? 'Creating...' : 'Create Organization'}
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          <Card>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Organization</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Users</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredOrgs.map((org) => (
                  <TableRow key={org.id}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{org.name}</p>
                        <p className="text-sm text-slate-500">{org.contact_email}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{org.type}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge style={{ backgroundColor: STATUS_COLORS[org.status] || '#6b7280' }} className="text-white">
                        {org.status}
                      </Badge>
                    </TableCell>
                    <TableCell>{org.user_count || 0}</TableCell>
                    <TableCell className="text-sm text-slate-500">
                      {org.created_at ? formatDateTime(org.created_at) : '-'}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        {org.status === 'pending' && (
                          <Button 
                            size="sm" 
                            className="bg-emerald-600 hover:bg-emerald-700"
                            onClick={() => handleOrgAction(org.id, 'approve')}
                          >
                            Approve
                          </Button>
                        )}
                        {org.status === 'active' && (
                          <Button 
                            size="sm" 
                            variant="destructive"
                            onClick={() => handleOrgAction(org.id, 'suspend')}
                          >
                            Suspend
                          </Button>
                        )}
                        {org.status === 'suspended' && (
                          <Button 
                            size="sm"
                            onClick={() => handleOrgAction(org.id, 'reactivate')}
                          >
                            Reactivate
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>

        {/* Security Policies Tab */}
        <TabsContent value="security" className="space-y-4">
          <Alert className="border-amber-200 bg-amber-50">
            <Shield className="h-4 w-4 text-amber-600" />
            <AlertTitle className="text-amber-800">Security Policies</AlertTitle>
            <AlertDescription className="text-amber-700">
              Configure platform-wide security settings. Changes apply to all organizations.
            </AlertDescription>
          </Alert>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {securityPolicies.map((policy) => (
              <Card key={policy.policy_type}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base flex items-center gap-2">
                      {policy.policy_type === 'password' && <Lock className="w-4 h-4" />}
                      {policy.policy_type === 'session' && <Clock className="w-4 h-4" />}
                      {policy.policy_type === 'mfa' && <ShieldCheck className="w-4 h-4" />}
                      {policy.policy_type === 'access' && <Globe className="w-4 h-4" />}
                      {policy.name}
                    </CardTitle>
                    <Switch
                      checked={policy.is_active}
                      onCheckedChange={(checked) => handleTogglePolicy(policy.policy_type, checked)}
                    />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    {policy.policy_type === 'password' && policy.settings && (
                      <>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Min Length:</span>
                          <span>{policy.settings.min_length}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Max Age (days):</span>
                          <span>{policy.settings.max_age_days}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Lockout After:</span>
                          <span>{policy.settings.lockout_attempts} attempts</span>
                        </div>
                      </>
                    )}
                    {policy.policy_type === 'session' && policy.settings && (
                      <>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Max Duration:</span>
                          <span>{policy.settings.max_session_duration_hours}h</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Idle Timeout:</span>
                          <span>{policy.settings.idle_timeout_minutes}m</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Max Concurrent:</span>
                          <span>{policy.settings.max_concurrent_sessions}</span>
                        </div>
                      </>
                    )}
                    {policy.policy_type === 'mfa' && policy.settings && (
                      <>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Required For:</span>
                          <span>{policy.settings.required_for_roles?.join(', ') || 'None'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Methods:</span>
                          <span>{policy.settings.allowed_methods?.join(', ')}</span>
                        </div>
                      </>
                    )}
                    {policy.policy_type === 'access' && policy.settings && (
                      <>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Working Hours Only:</span>
                          <span>{policy.settings.working_hours_only ? 'Yes' : 'No'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">VPN Required:</span>
                          <span>{policy.settings.require_vpn_for_admin ? 'Yes' : 'No'}</span>
                        </div>
                      </>
                    )}
                  </div>
                  <Button 
                    variant="outline" 
                    className="w-full mt-4"
                    onClick={() => {
                      setSelectedPolicy(policy);
                      setPolicySettings(policy.settings || {});
                      setEditPolicyOpen(true);
                    }}
                  >
                    Edit Settings
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Audit Tab */}
        <TabsContent value="audit" className="space-y-4">
          <div className="flex items-center gap-4">
            <Select 
              value={auditFilter.days.toString()} 
              onValueChange={(v) => setAuditFilter({ ...auditFilter, days: parseInt(v) })}
            >
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">Last 24 hours</SelectItem>
                <SelectItem value="7">Last 7 days</SelectItem>
                <SelectItem value="30">Last 30 days</SelectItem>
              </SelectContent>
            </Select>
            <Select 
              value={auditFilter.org} 
              onValueChange={(v) => setAuditFilter({ ...auditFilter, org: v })}
            >
              <SelectTrigger className="w-60">
                <SelectValue placeholder="Filter by organization" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Organizations</SelectItem>
                {organizations.map((org) => (
                  <SelectItem key={org.id} value={org.id}>{org.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={fetchAuditLogs}>
              <RefreshCw className="w-4 h-4 mr-2" />Refresh
            </Button>
          </div>

          {/* Security Alerts Summary */}
          {securityAlerts.total > 0 && (
            <Alert className="border-red-200 bg-red-50">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <AlertTitle className="text-red-800">Security Alerts</AlertTitle>
              <AlertDescription className="text-red-700">
                {securityAlerts.total} security-related events in the last 24 hours:
                {Object.entries(securityAlerts.summary || {}).map(([type, count]) => (
                  <Badge key={type} variant="destructive" className="ml-2">{type}: {count}</Badge>
                ))}
              </AlertDescription>
            </Alert>
          )}

          <Card>
            <CardHeader>
              <CardTitle>System Audit Logs</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px]">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Timestamp</TableHead>
                      <TableHead>User</TableHead>
                      <TableHead>Action</TableHead>
                      <TableHead>Resource</TableHead>
                      <TableHead>Organization</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {auditLogs.map((log) => (
                      <TableRow key={log.id}>
                        <TableCell className="text-sm">
                          {formatDateTime(log.timestamp)}
                        </TableCell>
                        <TableCell>
                          <div>
                            <p className="text-sm font-medium">{log.user_name || 'System'}</p>
                            <p className="text-xs text-slate-500">{log.user_role}</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{log.action}</Badge>
                        </TableCell>
                        <TableCell className="text-sm text-slate-500">
                          {log.resource_type}
                        </TableCell>
                        <TableCell className="text-sm text-slate-500">
                          {organizations.find(o => o.id === log.organization_id)?.name || '-'}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Edit Policy Dialog */}
      <Dialog open={editPolicyOpen} onOpenChange={setEditPolicyOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Edit {selectedPolicy?.name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            {selectedPolicy?.policy_type === 'password' && (
              <>
                <div className="space-y-2">
                  <Label>Minimum Password Length</Label>
                  <Input
                    type="number"
                    value={policySettings.min_length || 12}
                    onChange={(e) => setPolicySettings({ ...policySettings, min_length: parseInt(e.target.value) })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Password Expiration (days)</Label>
                  <Input
                    type="number"
                    value={policySettings.max_age_days || 90}
                    onChange={(e) => setPolicySettings({ ...policySettings, max_age_days: parseInt(e.target.value) })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Lockout After Failed Attempts</Label>
                  <Input
                    type="number"
                    value={policySettings.lockout_attempts || 5}
                    onChange={(e) => setPolicySettings({ ...policySettings, lockout_attempts: parseInt(e.target.value) })}
                  />
                </div>
              </>
            )}
            {selectedPolicy?.policy_type === 'session' && (
              <>
                <div className="space-y-2">
                  <Label>Max Session Duration (hours)</Label>
                  <Input
                    type="number"
                    value={policySettings.max_session_duration_hours || 12}
                    onChange={(e) => setPolicySettings({ ...policySettings, max_session_duration_hours: parseInt(e.target.value) })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Idle Timeout (minutes)</Label>
                  <Input
                    type="number"
                    value={policySettings.idle_timeout_minutes || 30}
                    onChange={(e) => setPolicySettings({ ...policySettings, idle_timeout_minutes: parseInt(e.target.value) })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Max Concurrent Sessions</Label>
                  <Input
                    type="number"
                    value={policySettings.max_concurrent_sessions || 3}
                    onChange={(e) => setPolicySettings({ ...policySettings, max_concurrent_sessions: parseInt(e.target.value) })}
                  />
                </div>
              </>
            )}
          </div>
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setEditPolicyOpen(false)}>Cancel</Button>
            <Button onClick={handleUpdatePolicy} disabled={saving}>
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
