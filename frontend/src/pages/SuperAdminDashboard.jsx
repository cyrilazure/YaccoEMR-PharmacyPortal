import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth';
import { organizationAPI } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
import { toast } from 'sonner';
import { formatDateTime } from '@/lib/utils';
import {
  Building2, Users, Activity, Clock, CheckCircle2, XCircle, PauseCircle,
  Plus, Search, Shield, Globe, Phone, Mail, FileText, RefreshCw,
  TrendingUp, AlertTriangle, Eye
} from 'lucide-react';

export default function SuperAdminDashboard() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Data
  const [stats, setStats] = useState(null);
  const [organizations, setOrganizations] = useState([]);
  const [pendingOrgs, setPendingOrgs] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  
  // Dialogs
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [approveDialogOpen, setApproveDialogOpen] = useState(false);
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedOrg, setSelectedOrg] = useState(null);
  
  // Form states
  const [newOrg, setNewOrg] = useState({
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
    admin_first_name: '',
    admin_last_name: '',
    admin_email: '',
    admin_phone: '',
    admin_title: 'Administrator'
  });
  const [approvalData, setApprovalData] = useState({
    subscription_plan: 'standard',
    max_users: 50,
    max_patients: 10000,
    notes: ''
  });
  const [rejectionReason, setRejectionReason] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsRes, orgsRes, pendingRes] = await Promise.all([
        organizationAPI.getPlatformStats(),
        organizationAPI.listAll(),
        organizationAPI.getPending()
      ]);
      setStats(statsRes.data);
      setOrganizations(orgsRes.data.organizations || []);
      setPendingOrgs(pendingRes.data.organizations || []);
    } catch (err) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateOrganization = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await organizationAPI.createByAdmin(newOrg, true);
      toast.success('Organization created successfully');
      setCreateDialogOpen(false);
      
      // Show credentials
      if (res.data.temp_password) {
        toast.info(
          `Admin credentials:\nEmail: ${res.data.admin_email}\nPassword: ${res.data.temp_password}`,
          { duration: 15000 }
        );
      }
      
      setNewOrg({
        name: '', organization_type: 'hospital', address_line1: '', address_line2: '',
        city: '', state: '', zip_code: '', country: 'USA', phone: '', fax: '',
        email: '', website: '', license_number: '', tax_id: '', npi_number: '',
        admin_first_name: '', admin_last_name: '', admin_email: '', admin_phone: '', admin_title: 'Administrator'
      });
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create organization');
    } finally {
      setSaving(false);
    }
  };

  const handleApprove = async () => {
    if (!selectedOrg) return;
    setSaving(true);
    try {
      const res = await organizationAPI.approve(selectedOrg.id, approvalData);
      toast.success('Organization approved');
      
      // Show credentials
      if (res.data.temp_password) {
        toast.info(
          `Admin credentials:\nEmail: ${res.data.admin_email}\nPassword: ${res.data.temp_password}`,
          { duration: 15000 }
        );
      }
      
      setApproveDialogOpen(false);
      setSelectedOrg(null);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to approve organization');
    } finally {
      setSaving(false);
    }
  };

  const handleReject = async () => {
    if (!selectedOrg || !rejectionReason) return;
    setSaving(true);
    try {
      await organizationAPI.reject(selectedOrg.id, { reason: rejectionReason });
      toast.success('Organization rejected');
      setRejectDialogOpen(false);
      setSelectedOrg(null);
      setRejectionReason('');
      fetchData();
    } catch (err) {
      toast.error('Failed to reject organization');
    } finally {
      setSaving(false);
    }
  };

  const handleSuspend = async (org) => {
    try {
      await organizationAPI.suspend(org.id, 'Suspended by admin');
      toast.success('Organization suspended');
      fetchData();
    } catch (err) {
      toast.error('Failed to suspend organization');
    }
  };

  const handleReactivate = async (org) => {
    try {
      await organizationAPI.reactivate(org.id);
      toast.success('Organization reactivated');
      fetchData();
    } catch (err) {
      toast.error('Failed to reactivate organization');
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      pending: { className: 'bg-amber-100 text-amber-700', icon: Clock },
      active: { className: 'bg-green-100 text-green-700', icon: CheckCircle2 },
      suspended: { className: 'bg-red-100 text-red-700', icon: PauseCircle },
      rejected: { className: 'bg-slate-100 text-slate-700', icon: XCircle }
    };
    const style = styles[status] || styles.pending;
    const Icon = style.icon;
    return (
      <Badge className={`${style.className} gap-1`}>
        <Icon className="w-3 h-3" /> {status}
      </Badge>
    );
  };

  const filteredOrgs = organizations.filter(org => {
    const matchesSearch = !searchQuery || 
      org.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      org.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      org.license_number?.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || org.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  if (user?.role !== 'super_admin') {
    return (
      <div className="flex items-center justify-center h-96">
        <Card className="w-96 text-center">
          <CardContent className="pt-8">
            <Shield className="w-16 h-16 mx-auto mb-4 text-red-500" />
            <h2 className="text-xl font-bold mb-2">Access Denied</h2>
            <p className="text-slate-500">Super Admin access required</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid grid-cols-4 gap-4">
          {[1,2,3,4].map(i => <Skeleton key={i} className="h-32" />)}
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="super-admin-dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Manrope' }}>
            Platform Administration
          </h1>
          <p className="text-slate-500 mt-1">Manage hospitals and organizations</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchData} className="gap-2">
            <RefreshCw className="w-4 h-4" /> Refresh
          </Button>
          <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2 bg-sky-600 hover:bg-sky-700" data-testid="create-org-btn">
                <Plus className="w-4 h-4" /> Add Organization
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create New Organization</DialogTitle>
                <DialogDescription>Add a new hospital or healthcare organization to the platform</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleCreateOrganization} className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Organization Name *</Label>
                    <Input required value={newOrg.name} onChange={(e) => setNewOrg({...newOrg, name: e.target.value})} />
                  </div>
                  <div className="space-y-2">
                    <Label>Type</Label>
                    <Select value={newOrg.organization_type} onValueChange={(v) => setNewOrg({...newOrg, organization_type: v})}>
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
                  <Label>Address Line 1 *</Label>
                  <Input required value={newOrg.address_line1} onChange={(e) => setNewOrg({...newOrg, address_line1: e.target.value})} />
                </div>
                <div className="space-y-2">
                  <Label>Address Line 2</Label>
                  <Input value={newOrg.address_line2} onChange={(e) => setNewOrg({...newOrg, address_line2: e.target.value})} />
                </div>
                
                <div className="grid grid-cols-4 gap-4">
                  <div className="space-y-2 col-span-2">
                    <Label>City *</Label>
                    <Input required value={newOrg.city} onChange={(e) => setNewOrg({...newOrg, city: e.target.value})} />
                  </div>
                  <div className="space-y-2">
                    <Label>State *</Label>
                    <Input required value={newOrg.state} onChange={(e) => setNewOrg({...newOrg, state: e.target.value})} />
                  </div>
                  <div className="space-y-2">
                    <Label>ZIP *</Label>
                    <Input required value={newOrg.zip_code} onChange={(e) => setNewOrg({...newOrg, zip_code: e.target.value})} />
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Phone *</Label>
                    <Input required value={newOrg.phone} onChange={(e) => setNewOrg({...newOrg, phone: e.target.value})} />
                  </div>
                  <div className="space-y-2">
                    <Label>Email *</Label>
                    <Input type="email" required value={newOrg.email} onChange={(e) => setNewOrg({...newOrg, email: e.target.value})} />
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>License Number *</Label>
                    <Input required value={newOrg.license_number} onChange={(e) => setNewOrg({...newOrg, license_number: e.target.value})} />
                  </div>
                  <div className="space-y-2">
                    <Label>NPI Number</Label>
                    <Input value={newOrg.npi_number} onChange={(e) => setNewOrg({...newOrg, npi_number: e.target.value})} />
                  </div>
                </div>
                
                <hr className="my-4" />
                <h4 className="font-medium">Admin Contact</h4>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>First Name *</Label>
                    <Input required value={newOrg.admin_first_name} onChange={(e) => setNewOrg({...newOrg, admin_first_name: e.target.value})} />
                  </div>
                  <div className="space-y-2">
                    <Label>Last Name *</Label>
                    <Input required value={newOrg.admin_last_name} onChange={(e) => setNewOrg({...newOrg, admin_last_name: e.target.value})} />
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Admin Email *</Label>
                    <Input type="email" required value={newOrg.admin_email} onChange={(e) => setNewOrg({...newOrg, admin_email: e.target.value})} />
                  </div>
                  <div className="space-y-2">
                    <Label>Admin Phone *</Label>
                    <Input required value={newOrg.admin_phone} onChange={(e) => setNewOrg({...newOrg, admin_phone: e.target.value})} />
                  </div>
                </div>
                
                <Button type="submit" className="w-full" disabled={saving}>
                  {saving ? 'Creating...' : 'Create Organization'}
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Organizations</p>
                <p className="text-3xl font-bold">{stats?.total_organizations || 0}</p>
              </div>
              <Building2 className="w-10 h-10 text-sky-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Active</p>
                <p className="text-3xl font-bold text-green-600">{stats?.active_organizations || 0}</p>
              </div>
              <CheckCircle2 className="w-10 h-10 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Pending Approval</p>
                <p className="text-3xl font-bold text-amber-600">{stats?.pending_organizations || 0}</p>
              </div>
              <Clock className="w-10 h-10 text-amber-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Users</p>
                <p className="text-3xl font-bold">{stats?.total_users || 0}</p>
              </div>
              <Users className="w-10 h-10 text-purple-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Patients</p>
                <p className="text-3xl font-bold">{stats?.total_patients || 0}</p>
              </div>
              <Activity className="w-10 h-10 text-rose-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pending Approvals Alert */}
      {pendingOrgs.length > 0 && (
        <Card className="border-l-4 border-l-amber-500">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-amber-700">
              <AlertTriangle className="w-5 h-5" /> Pending Approvals ({pendingOrgs.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {pendingOrgs.slice(0, 3).map((org) => (
                <div key={org.id} className="flex items-center justify-between p-3 bg-amber-50 rounded-lg">
                  <div>
                    <p className="font-medium">{org.name}</p>
                    <p className="text-sm text-slate-500">{org.city}, {org.state} • Applied {formatDateTime(org.created_at)}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => { setSelectedOrg(org); setViewDialogOpen(true); }}
                    >
                      <Eye className="w-4 h-4 mr-1" /> View
                    </Button>
                    <Button 
                      size="sm" 
                      className="bg-green-600 hover:bg-green-700"
                      onClick={() => { setSelectedOrg(org); setApproveDialogOpen(true); }}
                    >
                      Approve
                    </Button>
                    <Button 
                      size="sm" 
                      variant="destructive"
                      onClick={() => { setSelectedOrg(org); setRejectDialogOpen(true); }}
                    >
                      Reject
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Organizations List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Building2 className="w-5 h-5" /> All Organizations
            </CardTitle>
            <div className="flex gap-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  placeholder="Search organizations..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 w-64"
                />
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-36">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="suspended">Suspended</SelectItem>
                  <SelectItem value="rejected">Rejected</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[400px]">
            <div className="space-y-2">
              {filteredOrgs.length === 0 ? (
                <p className="text-center text-slate-500 py-8">No organizations found</p>
              ) : (
                filteredOrgs.map((org) => (
                  <Card key={org.id} className="hover:border-sky-200 transition-colors">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 rounded-full bg-sky-100 flex items-center justify-center">
                            <Building2 className="w-6 h-6 text-sky-600" />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <p className="font-medium">{org.name}</p>
                              {getStatusBadge(org.status)}
                            </div>
                            <p className="text-sm text-slate-500">
                              {org.city}, {org.state} • {org.organization_type?.replace('_', ' ')}
                            </p>
                            <div className="flex items-center gap-4 text-sm text-slate-400 mt-1">
                              <span className="flex items-center gap-1">
                                <Users className="w-3 h-3" /> {org.total_users || 0} users
                              </span>
                              <span className="flex items-center gap-1">
                                <Activity className="w-3 h-3" /> {org.total_patients || 0} patients
                              </span>
                              <span className="flex items-center gap-1">
                                <Mail className="w-3 h-3" /> {org.email}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => { setSelectedOrg(org); setViewDialogOpen(true); }}
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          {org.status === 'active' && (
                            <Button size="sm" variant="outline" className="text-red-600" onClick={() => handleSuspend(org)}>
                              Suspend
                            </Button>
                          )}
                          {org.status === 'suspended' && (
                            <Button size="sm" variant="outline" className="text-green-600" onClick={() => handleReactivate(org)}>
                              Reactivate
                            </Button>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Approve Dialog */}
      <Dialog open={approveDialogOpen} onOpenChange={setApproveDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Approve Organization</DialogTitle>
            <DialogDescription>Configure subscription and approve {selectedOrg?.name}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label>Subscription Plan</Label>
              <Select value={approvalData.subscription_plan} onValueChange={(v) => setApprovalData({...approvalData, subscription_plan: v})}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="starter">Starter (25 users, 2,500 patients)</SelectItem>
                  <SelectItem value="standard">Standard (50 users, 10,000 patients)</SelectItem>
                  <SelectItem value="professional">Professional (100 users, 25,000 patients)</SelectItem>
                  <SelectItem value="enterprise">Enterprise (Unlimited)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Max Users</Label>
                <Input type="number" value={approvalData.max_users} onChange={(e) => setApprovalData({...approvalData, max_users: parseInt(e.target.value)})} />
              </div>
              <div className="space-y-2">
                <Label>Max Patients</Label>
                <Input type="number" value={approvalData.max_patients} onChange={(e) => setApprovalData({...approvalData, max_patients: parseInt(e.target.value)})} />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea value={approvalData.notes} onChange={(e) => setApprovalData({...approvalData, notes: e.target.value})} placeholder="Internal notes..." />
            </div>
            <Button onClick={handleApprove} className="w-full bg-green-600 hover:bg-green-700" disabled={saving}>
              {saving ? 'Approving...' : 'Approve Organization'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Reject Dialog */}
      <Dialog open={rejectDialogOpen} onOpenChange={setRejectDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject Organization</DialogTitle>
            <DialogDescription>Provide a reason for rejecting {selectedOrg?.name}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label>Rejection Reason *</Label>
              <Textarea 
                value={rejectionReason} 
                onChange={(e) => setRejectionReason(e.target.value)} 
                placeholder="Explain why this organization is being rejected..."
                required
              />
            </div>
            <Button onClick={handleReject} className="w-full" variant="destructive" disabled={saving || !rejectionReason}>
              {saving ? 'Rejecting...' : 'Reject Organization'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* View Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{selectedOrg?.name}</DialogTitle>
            <DialogDescription>Organization Details</DialogDescription>
          </DialogHeader>
          {selectedOrg && (
            <div className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-500">Type</p>
                  <p className="font-medium">{selectedOrg.organization_type?.replace('_', ' ')}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Status</p>
                  {getStatusBadge(selectedOrg.status)}
                </div>
                <div>
                  <p className="text-sm text-slate-500">License Number</p>
                  <p className="font-medium">{selectedOrg.license_number}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">NPI</p>
                  <p className="font-medium">{selectedOrg.npi_number || 'N/A'}</p>
                </div>
              </div>
              <hr />
              <div>
                <p className="text-sm text-slate-500">Address</p>
                <p className="font-medium">
                  {selectedOrg.address_line1}<br />
                  {selectedOrg.address_line2 && <>{selectedOrg.address_line2}<br /></>}
                  {selectedOrg.city}, {selectedOrg.state} {selectedOrg.zip_code}
                </p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-500">Phone</p>
                  <p className="font-medium">{selectedOrg.phone}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Email</p>
                  <p className="font-medium">{selectedOrg.email}</p>
                </div>
              </div>
              <hr />
              <div>
                <p className="text-sm text-slate-500 mb-2">Admin Contact</p>
                <p className="font-medium">{selectedOrg.admin_first_name} {selectedOrg.admin_last_name}</p>
                <p className="text-sm text-slate-600">{selectedOrg.admin_email}</p>
                <p className="text-sm text-slate-600">{selectedOrg.admin_phone}</p>
              </div>
              <hr />
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-slate-500">Created</p>
                  <p>{formatDateTime(selectedOrg.created_at)}</p>
                </div>
                {selectedOrg.approved_at && (
                  <div>
                    <p className="text-slate-500">Approved</p>
                    <p>{formatDateTime(selectedOrg.approved_at)}</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
