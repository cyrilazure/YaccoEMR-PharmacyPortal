import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import { hospitalDashboardAPI, departmentAPI } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { toast } from 'sonner';
import {
  Building2, MapPin, Users, Loader2, RefreshCw,
  AlertCircle, CheckCircle, Shield, Clock, Search,
  Layers, UserCheck, ChevronRight, Activity
} from 'lucide-react';

export default function FacilityAdminPortal() {
  const { hospitalId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const effectiveHospitalId = hospitalId || user?.organization_id;

  // State
  const [loading, setLoading] = useState(true);
  const [facility, setFacility] = useState(null);
  const [departments, setDepartments] = useState([]);
  const [staff, setStaff] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('overview');

  // Assignment dialog
  const [assignDialogOpen, setAssignDialogOpen] = useState(false);
  const [selectedStaff, setSelectedStaff] = useState(null);
  const [selectedDepartment, setSelectedDepartment] = useState('');
  const [saving, setSaving] = useState(false);

  // Access control
  const allowedRoles = ['facility_admin', 'hospital_admin', 'super_admin'];
  const hasAccess = allowedRoles.includes(user?.role);

  // Fetch data
  const fetchData = useCallback(async () => {
    if (!effectiveHospitalId || !hasAccess) return;

    try {
      setLoading(true);
      const [dashboardRes, deptRes] = await Promise.all([
        hospitalDashboardAPI.getDashboard(effectiveHospitalId),
        departmentAPI.getAll()
      ]);

      setFacility(dashboardRes.data);
      setDepartments(deptRes.data || []);
      
      // Extract staff from dashboard
      if (dashboardRes.data?.staff) {
        setStaff(dashboardRes.data.staff);
      }
    } catch (err) {
      console.error('Error fetching facility data:', err);
      toast.error('Failed to load facility data');
    } finally {
      setLoading(false);
    }
  }, [effectiveHospitalId, hasAccess]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Filter staff by search
  const filteredStaff = staff.filter(s =>
    `${s.first_name} ${s.last_name}`.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.role?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Assign staff to department (facility-level operation)
  const handleAssignStaff = async () => {
    if (!selectedStaff || !selectedDepartment) {
      toast.error('Please select a department');
      return;
    }

    try {
      setSaving(true);
      await departmentAPI.assignStaff(selectedDepartment, selectedStaff.id);
      toast.success(`${selectedStaff.first_name} assigned to department`);
      setAssignDialogOpen(false);
      setSelectedStaff(null);
      setSelectedDepartment('');
      fetchData();
    } catch (err) {
      toast.error('Failed to assign staff');
    } finally {
      setSaving(false);
    }
  };

  // Access denied view
  if (!hasAccess) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Alert variant="destructive" className="max-w-md">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Access Denied</AlertTitle>
          <AlertDescription>
            You must be a Facility Administrator to access this portal.
            Contact your Hospital IT Administrator for access.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  if (loading) {
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
            Facility Administrator Portal
          </h1>
          <p className="text-gray-500 mt-1 flex items-center gap-2">
            <MapPin className="w-4 h-4" />
            {facility?.hospital?.name || 'Health Facility'}
            {facility?.location && (
              <Badge variant="outline">{facility.location.name}</Badge>
            )}
          </p>
        </div>
        <Button onClick={fetchData} variant="outline">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Access Notice */}
      <Alert className="border-blue-200 bg-blue-50">
        <Shield className="h-4 w-4 text-blue-600" />
        <AlertTitle className="text-blue-800">Facility Administrator Access</AlertTitle>
        <AlertDescription className="text-blue-700">
          You can view facility information and assign staff to departments. 
          For staff account creation, contact the Hospital IT Administrator.
          Patient medical records are not accessible from this portal.
        </AlertDescription>
      </Alert>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview" className="gap-2">
            <Activity className="w-4 h-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="departments" className="gap-2">
            <Layers className="w-4 h-4" />
            Departments
          </TabsTrigger>
          <TabsTrigger value="staff" className="gap-2">
            <Users className="w-4 h-4" />
            Staff Assignments
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="mt-6">
          <div className="grid md:grid-cols-3 gap-6">
            {/* Facility Info */}
            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle>Facility Information</CardTitle>
                <CardDescription>Basic facility details</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-xs text-gray-500">Facility Name</Label>
                    <p className="font-medium">{facility?.hospital?.name || '-'}</p>
                  </div>
                  <div>
                    <Label className="text-xs text-gray-500">Location</Label>
                    <p className="font-medium">{facility?.hospital?.city || '-'}</p>
                  </div>
                  <div>
                    <Label className="text-xs text-gray-500">Region</Label>
                    <p className="font-medium capitalize">
                      {facility?.hospital?.region_id?.replace('-', ' ') || '-'}
                    </p>
                  </div>
                  <div>
                    <Label className="text-xs text-gray-500">Status</Label>
                    <Badge className="bg-emerald-100 text-emerald-700">Active</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Quick Stats */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Stats</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-600">Departments</span>
                  <Badge variant="secondary">{departments.length}</Badge>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-600">Staff Members</span>
                  <Badge variant="secondary">{staff.length}</Badge>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-600">Locations</span>
                  <Badge variant="secondary">{facility?.stats?.locations || 1}</Badge>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Departments Tab */}
        <TabsContent value="departments" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Departments & Units</CardTitle>
              <CardDescription>View facility departments</CardDescription>
            </CardHeader>
            <CardContent>
              {departments.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <Layers className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No departments configured</p>
                  <p className="text-sm">Contact Hospital Admin to create departments</p>
                </div>
              ) : (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {departments.map((dept) => (
                    <Card key={dept.id} className="border">
                      <CardContent className="pt-4">
                        <div className="flex items-start justify-between">
                          <div>
                            <h4 className="font-medium">{dept.name}</h4>
                            <p className="text-xs text-gray-500 capitalize">
                              {dept.type?.replace('_', ' ')}
                            </p>
                          </div>
                          <Badge variant="outline">
                            {dept.staff_count || 0} staff
                          </Badge>
                        </div>
                        {dept.description && (
                          <p className="text-xs text-gray-400 mt-2">{dept.description}</p>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Staff Assignments Tab */}
        <TabsContent value="staff" className="mt-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Staff Department Assignments</CardTitle>
                  <CardDescription>
                    Assign staff members to departments. New accounts are created by IT Admin.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {/* Search */}
              <div className="flex items-center gap-4 mb-6">
                <div className="relative flex-1 max-w-sm">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <Input
                    placeholder="Search staff..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9"
                  />
                </div>
              </div>

              {/* Staff Table */}
              {filteredStaff.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No staff members found</p>
                </div>
              ) : (
                <div className="rounded-lg border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Name</TableHead>
                        <TableHead>Role</TableHead>
                        <TableHead>Department</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredStaff.map((member) => (
                        <TableRow key={member.id}>
                          <TableCell className="font-medium">
                            {member.first_name} {member.last_name}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className="capitalize">
                              {member.role?.replace('_', ' ')}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {member.department_name || (
                              <span className="text-gray-400">Not assigned</span>
                            )}
                          </TableCell>
                          <TableCell>
                            {member.is_active !== false ? (
                              <Badge className="bg-emerald-100 text-emerald-700">Active</Badge>
                            ) : (
                              <Badge variant="secondary">Inactive</Badge>
                            )}
                          </TableCell>
                          <TableCell className="text-right">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setSelectedStaff(member);
                                setAssignDialogOpen(true);
                              }}
                            >
                              <UserCheck className="w-4 h-4 mr-1" />
                              Assign Dept
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
      </Tabs>

      {/* Assign Department Dialog */}
      <Dialog open={assignDialogOpen} onOpenChange={setAssignDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Assign to Department</DialogTitle>
            <DialogDescription>
              Select a department for {selectedStaff?.first_name} {selectedStaff?.last_name}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div>
              <Label>Department</Label>
              <Select value={selectedDepartment} onValueChange={setSelectedDepartment}>
                <SelectTrigger>
                  <SelectValue placeholder="Select department" />
                </SelectTrigger>
                <SelectContent>
                  {departments.map((dept) => (
                    <SelectItem key={dept.id} value={dept.id}>
                      {dept.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setAssignDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleAssignStaff} disabled={saving}>
              {saving ? (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              ) : (
                <CheckCircle className="w-4 h-4 mr-2" />
              )}
              Assign
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
