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
  Building2, Users, Settings, Plus, Mail, Phone, MapPin,
  UserPlus, Send, Copy, CheckCircle2, XCircle, Clock,
  Shield, Edit, Trash2, RefreshCw, Key, Activity
} from 'lucide-react';

export default function HospitalSettings() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('organization');
  
  // Data
  const [organization, setOrganization] = useState(null);
  const [staff, setStaff] = useState([]);
  const [invitations, setInvitations] = useState([]);
  
  // Dialogs
  const [editOrgDialogOpen, setEditOrgDialogOpen] = useState(false);
  const [createStaffDialogOpen, setCreateStaffDialogOpen] = useState(false);
  const [inviteStaffDialogOpen, setInviteStaffDialogOpen] = useState(false);
  const [credentialsDialogOpen, setCredentialsDialogOpen] = useState(false);
  
  // Form states
  const [orgUpdate, setOrgUpdate] = useState({});
  const [newStaff, setNewStaff] = useState({
    email: '',
    first_name: '',
    last_name: '',
    role: 'physician',
    department: '',
    specialty: '',
    phone: '',
    license_number: ''
  });
  const [newCredentials, setNewCredentials] = useState({ email: '', password: '' });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [orgRes, staffRes, invitesRes] = await Promise.all([
        organizationAPI.getMyOrganization(),
        organizationAPI.listStaff(),
        organizationAPI.listInvitations()
      ]);
      setOrganization(orgRes.data.organization);
      setOrgUpdate(orgRes.data.organization);
      setStaff(staffRes.data.staff || []);
      setInvitations(invitesRes.data.invitations || []);
    } catch (err) {
      toast.error('Failed to load organization data');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateOrganization = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await organizationAPI.updateMyOrganization({
        name: orgUpdate.name,
        address_line1: orgUpdate.address_line1,
        address_line2: orgUpdate.address_line2,
        city: orgUpdate.city,
        state: orgUpdate.state,
        zip_code: orgUpdate.zip_code,
        phone: orgUpdate.phone,
        fax: orgUpdate.fax,
        email: orgUpdate.email,
        website: orgUpdate.website
      });
      toast.success('Organization updated');
      setEditOrgDialogOpen(false);
      fetchData();
    } catch (err) {
      toast.error('Failed to update organization');
    } finally {
      setSaving(false);
    }
  };

  const handleCreateStaff = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await organizationAPI.createStaff(newStaff);
      toast.success('Staff account created');
      
      // Show credentials
      setNewCredentials({
        email: res.data.email,
        password: res.data.temp_password
      });
      setCredentialsDialogOpen(true);
      
      setCreateStaffDialogOpen(false);
      setNewStaff({
        email: '', first_name: '', last_name: '', role: 'physician',
        department: '', specialty: '', phone: '', license_number: ''
      });
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create staff account');
    } finally {
      setSaving(false);
    }
  };

  const handleInviteStaff = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await organizationAPI.inviteStaff(newStaff);
      toast.success('Invitation sent');
      
      // Copy invitation link
      const inviteLink = `${window.location.origin}${res.data.invitation_link}`;
      navigator.clipboard.writeText(inviteLink);
      toast.info('Invitation link copied to clipboard');
      
      setInviteStaffDialogOpen(false);
      setNewStaff({
        email: '', first_name: '', last_name: '', role: 'physician',
        department: '', specialty: '', phone: '', license_number: ''
      });
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to send invitation');
    } finally {
      setSaving(false);
    }
  };

  const handleDeactivateStaff = async (userId) => {
    try {
      await organizationAPI.deactivateStaff(userId);
      toast.success('Staff member deactivated');
      fetchData();
    } catch (err) {
      toast.error('Failed to deactivate staff');
    }
  };

  const handleActivateStaff = async (userId) => {
    try {
      await organizationAPI.activateStaff(userId);
      toast.success('Staff member activated');
      fetchData();
    } catch (err) {
      toast.error('Failed to activate staff');
    }
  };

  const handleCancelInvitation = async (invitationId) => {
    try {
      await organizationAPI.cancelInvitation(invitationId);
      toast.success('Invitation cancelled');
      fetchData();
    } catch (err) {
      toast.error('Failed to cancel invitation');
    }
  };

  const copyCredentials = () => {
    navigator.clipboard.writeText(`Email: ${newCredentials.email}\nPassword: ${newCredentials.password}`);
    toast.success('Credentials copied to clipboard');
  };

  const getRoleBadge = (role) => {
    const styles = {
      hospital_admin: { className: 'bg-purple-100 text-purple-700', label: 'Admin' },
      physician: { className: 'bg-sky-100 text-sky-700', label: 'Physician' },
      nurse: { className: 'bg-green-100 text-green-700', label: 'Nurse' },
      scheduler: { className: 'bg-amber-100 text-amber-700', label: 'Scheduler' }
    };
    const style = styles[role] || { className: 'bg-slate-100 text-slate-700', label: role };
    return <Badge className={style.className}>{style.label}</Badge>;
  };

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

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-48" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="hospital-settings">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Manrope' }}>
            Hospital Settings
          </h1>
          <p className="text-slate-500 mt-1">Manage your organization and staff</p>
        </div>
        <Button variant="outline" onClick={fetchData} className="gap-2">
          <RefreshCw className="w-4 h-4" /> Refresh
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="organization">Organization</TabsTrigger>
          <TabsTrigger value="staff">Staff Management</TabsTrigger>
          <TabsTrigger value="invitations">Invitations</TabsTrigger>
        </TabsList>

        {/* Organization Tab */}
        <TabsContent value="organization" className="mt-6 space-y-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Building2 className="w-5 h-5" /> {organization?.name}
                </CardTitle>
                <CardDescription>{organization?.organization_type?.replace('_', ' ')}</CardDescription>
              </div>
              <Dialog open={editOrgDialogOpen} onOpenChange={setEditOrgDialogOpen}>
                <DialogTrigger asChild>
                  <Button variant="outline" className="gap-2">
                    <Edit className="w-4 h-4" /> Edit
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-lg">
                  <DialogHeader>
                    <DialogTitle>Edit Organization</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleUpdateOrganization} className="space-y-4 mt-4">
                    <div className="space-y-2">
                      <Label>Organization Name</Label>
                      <Input value={orgUpdate.name || ''} onChange={(e) => setOrgUpdate({...orgUpdate, name: e.target.value})} />
                    </div>
                    <div className="space-y-2">
                      <Label>Address</Label>
                      <Input value={orgUpdate.address_line1 || ''} onChange={(e) => setOrgUpdate({...orgUpdate, address_line1: e.target.value})} />
                    </div>
                    <div className="grid grid-cols-3 gap-2">
                      <Input placeholder="City" value={orgUpdate.city || ''} onChange={(e) => setOrgUpdate({...orgUpdate, city: e.target.value})} />
                      <Input placeholder="State" value={orgUpdate.state || ''} onChange={(e) => setOrgUpdate({...orgUpdate, state: e.target.value})} />
                      <Input placeholder="ZIP" value={orgUpdate.zip_code || ''} onChange={(e) => setOrgUpdate({...orgUpdate, zip_code: e.target.value})} />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Phone</Label>
                        <Input value={orgUpdate.phone || ''} onChange={(e) => setOrgUpdate({...orgUpdate, phone: e.target.value})} />
                      </div>
                      <div className="space-y-2">
                        <Label>Email</Label>
                        <Input type="email" value={orgUpdate.email || ''} onChange={(e) => setOrgUpdate({...orgUpdate, email: e.target.value})} />
                      </div>
                    </div>
                    <Button type="submit" className="w-full" disabled={saving}>
                      {saving ? 'Saving...' : 'Save Changes'}
                    </Button>
                  </form>
                </DialogContent>
              </Dialog>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="flex items-start gap-3">
                    <MapPin className="w-5 h-5 text-slate-400 mt-1" />
                    <div>
                      <p className="font-medium">Address</p>
                      <p className="text-slate-600">
                        {organization?.address_line1}<br />
                        {organization?.address_line2 && <>{organization.address_line2}<br /></>}
                        {organization?.city}, {organization?.state} {organization?.zip_code}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <Phone className="w-5 h-5 text-slate-400 mt-1" />
                    <div>
                      <p className="font-medium">Phone</p>
                      <p className="text-slate-600">{organization?.phone}</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <Mail className="w-5 h-5 text-slate-400 mt-1" />
                    <div>
                      <p className="font-medium">Email</p>
                      <p className="text-slate-600">{organization?.email}</p>
                    </div>
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="p-4 bg-slate-50 rounded-lg">
                    <p className="text-sm text-slate-500 mb-2">License Number</p>
                    <p className="font-mono font-medium">{organization?.license_number}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <Card>
                      <CardContent className="pt-4 text-center">
                        <Users className="w-8 h-8 mx-auto mb-2 text-sky-500" />
                        <p className="text-2xl font-bold">{organization?.total_users || 0}</p>
                        <p className="text-sm text-slate-500">/ {organization?.max_users} users</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="pt-4 text-center">
                        <Activity className="w-8 h-8 mx-auto mb-2 text-emerald-500" />
                        <p className="text-2xl font-bold">{organization?.total_patients || 0}</p>
                        <p className="text-sm text-slate-500">/ {organization?.max_patients} patients</p>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Staff Management Tab */}
        <TabsContent value="staff" className="mt-6 space-y-6">
          <div className="flex justify-end gap-2">
            <Dialog open={inviteStaffDialogOpen} onOpenChange={setInviteStaffDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="gap-2">
                  <Send className="w-4 h-4" /> Send Invitation
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Invite Staff Member</DialogTitle>
                  <DialogDescription>Send an email invitation to join your organization</DialogDescription>
                </DialogHeader>
                <form onSubmit={handleInviteStaff} className="space-y-4 mt-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>First Name *</Label>
                      <Input required value={newStaff.first_name} onChange={(e) => setNewStaff({...newStaff, first_name: e.target.value})} />
                    </div>
                    <div className="space-y-2">
                      <Label>Last Name *</Label>
                      <Input required value={newStaff.last_name} onChange={(e) => setNewStaff({...newStaff, last_name: e.target.value})} />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Email *</Label>
                    <Input type="email" required value={newStaff.email} onChange={(e) => setNewStaff({...newStaff, email: e.target.value})} />
                  </div>
                  <div className="space-y-2">
                    <Label>Role *</Label>
                    <Select value={newStaff.role} onValueChange={(v) => setNewStaff({...newStaff, role: v})}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="physician">Physician</SelectItem>
                        <SelectItem value="nurse">Nurse</SelectItem>
                        <SelectItem value="scheduler">Scheduler</SelectItem>
                        <SelectItem value="hospital_admin">Hospital Admin</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Department</Label>
                      <Input value={newStaff.department} onChange={(e) => setNewStaff({...newStaff, department: e.target.value})} />
                    </div>
                    <div className="space-y-2">
                      <Label>Specialty</Label>
                      <Input value={newStaff.specialty} onChange={(e) => setNewStaff({...newStaff, specialty: e.target.value})} />
                    </div>
                  </div>
                  <Button type="submit" className="w-full" disabled={saving}>
                    {saving ? 'Sending...' : 'Send Invitation'}
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
            <Dialog open={createStaffDialogOpen} onOpenChange={setCreateStaffDialogOpen}>
              <DialogTrigger asChild>
                <Button className="gap-2 bg-sky-600 hover:bg-sky-700" data-testid="create-staff-btn">
                  <UserPlus className="w-4 h-4" /> Create Account
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Create Staff Account</DialogTitle>
                  <DialogDescription>Create account with temporary password</DialogDescription>
                </DialogHeader>
                <form onSubmit={handleCreateStaff} className="space-y-4 mt-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>First Name *</Label>
                      <Input required value={newStaff.first_name} onChange={(e) => setNewStaff({...newStaff, first_name: e.target.value})} />
                    </div>
                    <div className="space-y-2">
                      <Label>Last Name *</Label>
                      <Input required value={newStaff.last_name} onChange={(e) => setNewStaff({...newStaff, last_name: e.target.value})} />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Email *</Label>
                    <Input type="email" required value={newStaff.email} onChange={(e) => setNewStaff({...newStaff, email: e.target.value})} />
                  </div>
                  <div className="space-y-2">
                    <Label>Role *</Label>
                    <Select value={newStaff.role} onValueChange={(v) => setNewStaff({...newStaff, role: v})}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="physician">Physician</SelectItem>
                        <SelectItem value="nurse">Nurse</SelectItem>
                        <SelectItem value="scheduler">Scheduler</SelectItem>
                        <SelectItem value="hospital_admin">Hospital Admin</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Department</Label>
                      <Input value={newStaff.department} onChange={(e) => setNewStaff({...newStaff, department: e.target.value})} />
                    </div>
                    <div className="space-y-2">
                      <Label>Phone</Label>
                      <Input value={newStaff.phone} onChange={(e) => setNewStaff({...newStaff, phone: e.target.value})} />
                    </div>
                  </div>
                  <Button type="submit" className="w-full" disabled={saving}>
                    {saving ? 'Creating...' : 'Create Account'}
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5" /> Staff Members ({staff.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                {staff.length === 0 ? (
                  <p className="text-center text-slate-500 py-8">No staff members yet</p>
                ) : (
                  <div className="space-y-2">
                    {staff.map((member) => (
                      <Card key={member.id} className="hover:border-sky-200 transition-colors">
                        <CardContent className="p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                              <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center">
                                <span className="text-lg font-medium text-slate-600">
                                  {member.first_name?.[0]}{member.last_name?.[0]}
                                </span>
                              </div>
                              <div>
                                <div className="flex items-center gap-2">
                                  <p className="font-medium">{member.first_name} {member.last_name}</p>
                                  {getRoleBadge(member.role)}
                                  {!member.is_active && <Badge variant="destructive">Inactive</Badge>}
                                </div>
                                <p className="text-sm text-slate-500">{member.email}</p>
                                {member.department && (
                                  <p className="text-sm text-slate-400">{member.department}</p>
                                )}
                              </div>
                            </div>
                            <div className="flex gap-2">
                              {member.id !== user?.id && (
                                member.is_active ? (
                                  <Button size="sm" variant="outline" className="text-red-600" onClick={() => handleDeactivateStaff(member.id)}>
                                    Deactivate
                                  </Button>
                                ) : (
                                  <Button size="sm" variant="outline" className="text-green-600" onClick={() => handleActivateStaff(member.id)}>
                                    Activate
                                  </Button>
                                )
                              )}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Invitations Tab */}
        <TabsContent value="invitations" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Mail className="w-5 h-5" /> Pending Invitations
              </CardTitle>
            </CardHeader>
            <CardContent>
              {invitations.filter(i => i.status === 'pending').length === 0 ? (
                <p className="text-center text-slate-500 py-8">No pending invitations</p>
              ) : (
                <div className="space-y-2">
                  {invitations.filter(i => i.status === 'pending').map((invite) => (
                    <Card key={invite.id}>
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium">{invite.first_name} {invite.last_name}</p>
                            <p className="text-sm text-slate-500">{invite.email}</p>
                            <div className="flex items-center gap-2 mt-1">
                              {getRoleBadge(invite.role)}
                              <span className="text-sm text-slate-400">
                                Expires: {formatDateTime(invite.expires_at)}
                              </span>
                            </div>
                          </div>
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                navigator.clipboard.writeText(`${window.location.origin}/accept-invitation?token=${invite.invitation_token}`);
                                toast.success('Link copied');
                              }}
                            >
                              <Copy className="w-4 h-4 mr-1" /> Copy Link
                            </Button>
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => handleCancelInvitation(invite.id)}
                            >
                              Cancel
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Credentials Dialog */}
      <Dialog open={credentialsDialogOpen} onOpenChange={setCredentialsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Key className="w-5 h-5" /> Staff Credentials Created
            </DialogTitle>
            <DialogDescription>Share these credentials securely with the staff member</DialogDescription>
          </DialogHeader>
          <div className="mt-4 p-4 bg-slate-50 rounded-lg space-y-2">
            <div>
              <Label className="text-slate-500">Email</Label>
              <p className="font-mono font-medium">{newCredentials.email}</p>
            </div>
            <div>
              <Label className="text-slate-500">Temporary Password</Label>
              <p className="font-mono font-medium text-lg">{newCredentials.password}</p>
            </div>
          </div>
          <Button onClick={copyCredentials} className="w-full gap-2">
            <Copy className="w-4 h-4" /> Copy Credentials
          </Button>
          <p className="text-sm text-amber-600 text-center">
            ⚠️ This password will only be shown once. Please save it securely.
          </p>
        </DialogContent>
      </Dialog>
    </div>
  );
}
