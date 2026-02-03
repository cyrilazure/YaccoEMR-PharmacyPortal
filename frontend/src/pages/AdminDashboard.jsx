import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/lib/auth';
import { usersAPI, patientAPI, ordersAPI, appointmentsAPI, dashboardAPI } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { toast } from 'sonner';
import { formatDateTime, getRoleDisplayName } from '@/lib/utils';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';
import { 
  Users, UserPlus, Settings, Shield, Activity, 
  TrendingUp, BarChart3, Clock, Database, Server
} from 'lucide-react';

export default function AdminDashboard() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState(null);
  const [patients, setPatients] = useState([]);
  const [orders, setOrders] = useState([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  
  const [newUser, setNewUser] = useState({
    email: '', password: '', first_name: '', last_name: '',
    role: 'nurse', department: '', specialty: ''
  });

  const fetchData = useCallback(async () => {
    try {
      const [usersRes, statsRes, patientsRes, ordersRes] = await Promise.all([
        usersAPI.getAll(),
        dashboardAPI.getStats(),
        patientAPI.getAll(),
        ordersAPI.getAll({})
      ]);
      
      setUsers(usersRes.data);
      setStats(statsRes.data);
      setPatients(patientsRes.data);
      setOrders(ordersRes.data);
    } catch (err) {
      console.error('Admin dashboard fetch error:', err);
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
      // Using register endpoint
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newUser)
      });
      
      if (response.ok) {
        toast.success('User created successfully');
        setDialogOpen(false);
        setNewUser({
          email: '', password: '', first_name: '', last_name: '',
          role: 'nurse', department: '', specialty: ''
        });
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

  // Calculate stats
  const usersByRole = [
    { name: 'Physicians', value: users.filter(u => u.role === 'physician').length, color: '#3b82f6' },
    { name: 'Nurses', value: users.filter(u => u.role === 'nurse').length, color: '#10b981' },
    { name: 'Schedulers', value: users.filter(u => u.role === 'scheduler').length, color: '#f59e0b' },
    { name: 'Admins', value: users.filter(u => u.role === 'admin').length, color: '#8b5cf6' },
  ];

  const orderStats = [
    { name: 'Pending', value: orders.filter(o => o.status === 'pending').length },
    { name: 'In Progress', value: orders.filter(o => o.status === 'in_progress').length },
    { name: 'Completed', value: orders.filter(o => o.status === 'completed').length },
  ];

  // Mock system health
  const systemHealth = [
    { name: 'API Server', status: 'healthy', uptime: '99.9%' },
    { name: 'Database', status: 'healthy', uptime: '99.8%' },
    { name: 'FHIR Server', status: 'healthy', uptime: '99.9%' },
  ];

  return (
    <div className="space-y-6 animate-fade-in" data-testid="admin-dashboard">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900" style={{ fontFamily: 'Manrope' }}>
            Administration Center
          </h1>
          <p className="text-slate-500 mt-1">
            Welcome, {user?.first_name} • System management and oversight
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2 bg-sky-600 hover:bg-sky-700">
              <UserPlus className="w-4 h-4" /> Add User
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New User</DialogTitle>
              <DialogDescription>Add a new staff member to the system</DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreateUser} className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>First Name *</Label>
                  <Input value={newUser.first_name} onChange={(e) => setNewUser({ ...newUser, first_name: e.target.value })} required />
                </div>
                <div className="space-y-2">
                  <Label>Last Name *</Label>
                  <Input value={newUser.last_name} onChange={(e) => setNewUser({ ...newUser, last_name: e.target.value })} required />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Email *</Label>
                <Input type="email" value={newUser.email} onChange={(e) => setNewUser({ ...newUser, email: e.target.value })} required />
              </div>
              <div className="space-y-2">
                <Label>Password *</Label>
                <Input type="password" value={newUser.password} onChange={(e) => setNewUser({ ...newUser, password: e.target.value })} required />
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
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Department</Label>
                  <Input value={newUser.department} onChange={(e) => setNewUser({ ...newUser, department: e.target.value })} />
                </div>
                <div className="space-y-2">
                  <Label>Specialty</Label>
                  <Input value={newUser.specialty} onChange={(e) => setNewUser({ ...newUser, specialty: e.target.value })} />
                </div>
              </div>
              <Button type="submit" className="w-full" disabled={saving}>
                {saving ? 'Creating...' : 'Create User'}
              </Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Users</p>
                <p className="text-2xl font-bold text-slate-900">{users.length}</p>
              </div>
              <Users className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-emerald-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Patients</p>
                <p className="text-2xl font-bold text-slate-900">{patients.length}</p>
              </div>
              <Activity className="w-8 h-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-amber-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Orders</p>
                <p className="text-2xl font-bold text-slate-900">{orders.length}</p>
              </div>
              <BarChart3 className="w-8 h-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">System Status</p>
                <p className="text-2xl font-bold text-emerald-600">Healthy</p>
              </div>
              <Server className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="users">
        <TabsList>
          <TabsTrigger value="users">User Management</TabsTrigger>
          <TabsTrigger value="analytics">System Analytics</TabsTrigger>
          <TabsTrigger value="system">System Health</TabsTrigger>
        </TabsList>

        {/* Users Tab */}
        <TabsContent value="users" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Staff Directory</CardTitle>
              <CardDescription>{users.length} registered users</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-3">
                  <Skeleton className="h-16 w-full" />
                  <Skeleton className="h-16 w-full" />
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Department</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Joined</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map((u) => (
                      <TableRow key={u.id}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-full bg-sky-100 text-sky-700 flex items-center justify-center text-sm font-semibold">
                              {u.first_name?.[0]}{u.last_name?.[0]}
                            </div>
                            <span className="font-medium">{u.first_name} {u.last_name}</span>
                          </div>
                        </TableCell>
                        <TableCell className="text-slate-600">{u.email}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className="capitalize">{getRoleDisplayName(u.role)}</Badge>
                        </TableCell>
                        <TableCell className="text-slate-600">{u.department || '-'}</TableCell>
                        <TableCell>
                          <Badge className={u.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'}>
                            {u.is_active ? 'Active' : 'Inactive'}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-slate-500 text-sm">
                          {formatDateTime(u.created_at)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Users by Role</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={usersByRole}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {usersByRole.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex justify-center gap-4 mt-4">
                  {usersByRole.map((item) => (
                    <div key={item.name} className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                      <span className="text-sm text-slate-600">{item.name}: {item.value}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Order Pipeline</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={orderStats}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 12 }} />
                    <YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* System Health Tab */}
        <TabsContent value="system" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Server className="w-5 h-5" /> System Services
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {systemHealth.map((service) => (
                    <div key={service.name} className="flex items-center justify-between p-4 rounded-lg border border-slate-200">
                      <div className="flex items-center gap-3">
                        <div className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse" />
                        <div>
                          <p className="font-medium text-slate-900">{service.name}</p>
                          <p className="text-sm text-slate-500">Uptime: {service.uptime}</p>
                        </div>
                      </div>
                      <Badge className="bg-emerald-100 text-emerald-700 capitalize">{service.status}</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="w-5 h-5" /> Database Statistics
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 rounded-lg bg-slate-50">
                    <span className="text-slate-600">Total Patients</span>
                    <span className="font-bold text-slate-900">{patients.length}</span>
                  </div>
                  <div className="flex items-center justify-between p-4 rounded-lg bg-slate-50">
                    <span className="text-slate-600">Total Orders</span>
                    <span className="font-bold text-slate-900">{orders.length}</span>
                  </div>
                  <div className="flex items-center justify-between p-4 rounded-lg bg-slate-50">
                    <span className="text-slate-600">Total Users</span>
                    <span className="font-bold text-slate-900">{users.length}</span>
                  </div>
                  <div className="flex items-center justify-between p-4 rounded-lg bg-slate-50">
                    <span className="text-slate-600">FHIR Resources</span>
                    <span className="font-bold text-slate-900">7 types</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* FHIR Endpoints Info */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-sky-600" /> FHIR R4 API Endpoints
              </CardTitle>
              <CardDescription>Interoperability endpoints for healthcare data exchange</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {['Patient', 'Observation', 'Condition', 'MedicationRequest', 'AllergyIntolerance', 'ServiceRequest', 'Appointment'].map((resource) => (
                  <div key={resource} className="p-3 rounded-lg border border-slate-200">
                    <p className="font-medium text-slate-900">{resource}</p>
                    <p className="text-xs text-slate-500 font-mono">/api/fhir/{resource}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
