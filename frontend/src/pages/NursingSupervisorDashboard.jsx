import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import { nursingSupervisorAPI, patientAPI } from '@/lib/api';
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
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { toast } from 'sonner';
import { 
  Users, UserPlus, ClipboardList, FileText, 
  Clock, CheckCircle, AlertCircle, RefreshCw,
  Eye, UserCheck, Activity, Stethoscope, 
  Calendar, ChevronRight, Search, Plus,
  FileCheck, Send, Star
} from 'lucide-react';

// Stat Card Component
function StatCard({ label, value, icon: Icon, color = 'blue' }) {
  const colors = {
    blue: 'from-blue-500 to-blue-600',
    emerald: 'from-emerald-500 to-emerald-600',
    amber: 'from-amber-500 to-amber-600',
    purple: 'from-purple-500 to-purple-600',
    red: 'from-red-500 to-red-600',
    slate: 'from-slate-500 to-slate-600'
  };
  
  return (
    <Card className="relative overflow-hidden">
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-500">{label}</p>
            <p className="text-2xl font-bold">{value}</p>
          </div>
          <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colors[color]} flex items-center justify-center`}>
            <Icon className="w-6 h-6 text-white" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default function NursingSupervisorDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);
  const [nurses, setNurses] = useState([]);
  const [reports, setReports] = useState([]);
  const [currentShifts, setCurrentShifts] = useState([]);
  const [unassignedPatients, setUnassignedPatients] = useState([]);
  
  // Dialogs
  const [assignPatientOpen, setAssignPatientOpen] = useState(false);
  const [assignTaskOpen, setAssignTaskOpen] = useState(false);
  const [viewReportOpen, setViewReportOpen] = useState(false);
  const [reviewReportOpen, setReviewReportOpen] = useState(false);
  const [viewNurseOpen, setViewNurseOpen] = useState(false);
  
  // Selected items
  const [selectedNurse, setSelectedNurse] = useState(null);
  const [selectedReport, setSelectedReport] = useState(null);
  const [selectedPatient, setSelectedPatient] = useState(null);
  
  // Form states
  const [assignmentForm, setAssignmentForm] = useState({
    patient_id: '',
    nurse_id: '',
    room_bed: '',
    acuity_level: 2,
    notes: ''
  });
  const [taskForm, setTaskForm] = useState({
    patient_id: '',
    nurse_id: '',
    task_type: 'vitals_due',
    description: '',
    priority: 'routine'
  });
  const [reviewNotes, setReviewNotes] = useState('');
  
  const [saving, setSaving] = useState(false);
  const [nurseWorkload, setNurseWorkload] = useState(null);

  // Access check
  useEffect(() => {
    const allowedRoles = ['nursing_supervisor', 'floor_supervisor', 'hospital_admin', 'super_admin', 'admin'];
    if (user && !allowedRoles.includes(user.role)) {
      toast.error('Access denied: Supervisor role required');
      navigate('/');
    }
  }, [user, navigate]);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [dashRes, nursesRes, reportsRes, shiftsRes, unassignedRes] = await Promise.all([
        nursingSupervisorAPI.getDashboard(),
        nursingSupervisorAPI.listNurses({ on_shift_only: false }),
        nursingSupervisorAPI.listReports({ status: 'submitted', limit: 20 }),
        nursingSupervisorAPI.getCurrentShifts(),
        nursingSupervisorAPI.getUnassignedPatients()
      ]);
      
      setDashboard(dashRes.data);
      setNurses(nursesRes.data.nurses || []);
      setReports(reportsRes.data.reports || []);
      setCurrentShifts(shiftsRes.data.active_shifts || []);
      setUnassignedPatients(unassignedRes.data.patients || []);
    } catch (err) {
      console.error('Dashboard fetch error:', err);
      toast.error('Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleAssignPatient = async () => {
    if (!assignmentForm.patient_id || !assignmentForm.nurse_id) {
      toast.error('Please select both patient and nurse');
      return;
    }
    
    setSaving(true);
    try {
      await nursingSupervisorAPI.assignPatient(assignmentForm);
      toast.success('Patient assigned successfully');
      setAssignPatientOpen(false);
      setAssignmentForm({ patient_id: '', nurse_id: '', room_bed: '', acuity_level: 2, notes: '' });
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to assign patient');
    } finally {
      setSaving(false);
    }
  };

  const handleAssignTask = async () => {
    if (!taskForm.patient_id || !taskForm.nurse_id || !taskForm.description) {
      toast.error('Please fill all required fields');
      return;
    }
    
    setSaving(true);
    try {
      await nursingSupervisorAPI.assignTask(taskForm);
      toast.success('Task assigned successfully');
      setAssignTaskOpen(false);
      setTaskForm({ patient_id: '', nurse_id: '', task_type: 'vitals_due', description: '', priority: 'routine' });
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to assign task');
    } finally {
      setSaving(false);
    }
  };

  const handleReviewReport = async () => {
    if (!selectedReport || !reviewNotes.trim()) {
      toast.error('Please add review notes');
      return;
    }
    
    setSaving(true);
    try {
      await nursingSupervisorAPI.reviewReport(selectedReport.id, reviewNotes);
      toast.success('Report reviewed');
      setReviewReportOpen(false);
      setSelectedReport(null);
      setReviewNotes('');
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to review report');
    } finally {
      setSaving(false);
    }
  };

  const handleViewNurseWorkload = async (nurse) => {
    setSelectedNurse(nurse);
    setViewNurseOpen(true);
    try {
      const res = await nursingSupervisorAPI.getNurseWorkload(nurse.id);
      setNurseWorkload(res.data);
    } catch (err) {
      toast.error('Failed to load workload');
    }
  };

  if (loading && !dashboard) {
    return (
      <div className="space-y-6 p-6">
        <Skeleton className="h-20 w-full" />
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-24" />)}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6" data-testid="nursing-supervisor-dashboard">
      {/* Header */}
      <div className="flex items-center justify-between bg-white rounded-xl p-4 shadow-sm border">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center shadow-lg">
            <Users className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Nursing Supervisor</h1>
            <p className="text-slate-500">Floor Management & Oversight</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <Button onClick={() => setAssignPatientOpen(true)} className="bg-emerald-600 hover:bg-emerald-700">
            <UserPlus className="w-4 h-4 mr-2" />
            Assign Patient
          </Button>
          <Button onClick={() => setAssignTaskOpen(true)} variant="outline">
            <Plus className="w-4 h-4 mr-2" />
            Assign Task
          </Button>
          <Button variant="outline" size="icon" onClick={fetchData}>
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
        <StatCard label="Nurses on Shift" value={dashboard?.nurses_on_shift || 0} icon={Users} color="emerald" />
        <StatCard label="Total Nurses" value={dashboard?.total_nurses || 0} icon={Stethoscope} color="blue" />
        <StatCard label="Active Assignments" value={dashboard?.active_assignments || 0} icon={UserCheck} color="purple" />
        <StatCard label="Total Patients" value={dashboard?.total_patients || 0} icon={Activity} color="slate" />
        <StatCard label="Reports to Review" value={dashboard?.pending_reports_for_review || 0} icon={FileText} color="amber" />
        <StatCard label="Today's Reports" value={dashboard?.today_reports || 0} icon={FileCheck} color="emerald" />
      </div>

      {/* Tabs */}
      <Tabs defaultValue="nurses" className="w-full">
        <TabsList className="grid w-full grid-cols-4 max-w-xl">
          <TabsTrigger value="nurses">Nurses</TabsTrigger>
          <TabsTrigger value="shifts">Current Shifts</TabsTrigger>
          <TabsTrigger value="reports">
            Reports
            {dashboard?.pending_reports_for_review > 0 && (
              <Badge className="ml-2 bg-amber-500">{dashboard.pending_reports_for_review}</Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="unassigned">Unassigned</TabsTrigger>
        </TabsList>

        {/* Nurses Tab */}
        <TabsContent value="nurses" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Nursing Staff</CardTitle>
              <CardDescription>View all nurses and their current workload</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="rounded-lg border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Nurse</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Shift</TableHead>
                      <TableHead>Patients</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {nurses.map((nurse) => (
                      <TableRow key={nurse.id}>
                        <TableCell>
                          <div>
                            <p className="font-medium">{nurse.first_name} {nurse.last_name}</p>
                            <p className="text-sm text-gray-500">{nurse.email}</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          {nurse.active_shift ? (
                            <Badge className="bg-emerald-100 text-emerald-700">On Shift</Badge>
                          ) : (
                            <Badge variant="outline">Off Duty</Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          {nurse.active_shift ? (
                            <span className="text-sm">{nurse.active_shift.shift_type?.toUpperCase()}</span>
                          ) : '-'}
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary">{nurse.patient_count || 0}</Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button 
                            size="sm" 
                            variant="outline"
                            onClick={() => handleViewNurseWorkload(nurse)}
                          >
                            <Eye className="w-4 h-4 mr-1" />
                            View
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                    {nurses.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center py-12 text-gray-500">
                          No nurses found
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Current Shifts Tab */}
        <TabsContent value="shifts" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Active Shifts</CardTitle>
              <CardDescription>Currently clocked-in nursing staff</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {currentShifts.map((shift) => (
                  <Card key={shift.id} className="border-l-4 border-l-emerald-500">
                    <CardContent className="pt-4">
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="font-medium">{shift.nurse_name}</p>
                          <Badge className="mt-1">{shift.shift_type?.toUpperCase()}</Badge>
                        </div>
                        <Badge variant="secondary">{shift.patient_count || 0} patients</Badge>
                      </div>
                      <div className="mt-3 text-sm text-gray-500">
                        <div className="flex items-center gap-2">
                          <Clock className="w-3 h-3" />
                          Started: {new Date(shift.clock_in_time).toLocaleTimeString()}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
                {currentShifts.length === 0 && (
                  <div className="col-span-full text-center py-12 text-gray-500">
                    No active shifts
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Reports Tab */}
        <TabsContent value="reports" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Shift Reports (Read-Only)</CardTitle>
              <CardDescription>Review submitted reports from nursing staff</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[500px]">
                <div className="space-y-4">
                  {reports.map((report) => (
                    <Card key={report.id} className={report.status === 'submitted' ? 'border-amber-200 bg-amber-50' : ''}>
                      <CardContent className="pt-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <p className="font-medium">{report.title}</p>
                              <Badge className={
                                report.status === 'submitted' ? 'bg-amber-100 text-amber-700' :
                                report.status === 'reviewed' ? 'bg-emerald-100 text-emerald-700' :
                                'bg-gray-100 text-gray-700'
                              }>
                                {report.status?.toUpperCase()}
                              </Badge>
                            </div>
                            <p className="text-sm text-gray-600 mt-1">{report.nurse_name}</p>
                            <p className="text-xs text-gray-400 mt-1">
                              {report.shift_type?.toUpperCase()} • {new Date(report.created_at).toLocaleString()}
                            </p>
                            <p className="text-sm mt-2 line-clamp-2">{report.content}</p>
                          </div>
                          <div className="flex gap-2 ml-4">
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => {
                                setSelectedReport(report);
                                setViewReportOpen(true);
                              }}
                            >
                              <Eye className="w-4 h-4 mr-1" />
                              View
                            </Button>
                            {report.status === 'submitted' && (
                              <Button 
                                size="sm"
                                onClick={() => {
                                  setSelectedReport(report);
                                  setReviewReportOpen(true);
                                }}
                              >
                                <CheckCircle className="w-4 h-4 mr-1" />
                                Review
                              </Button>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                  {reports.length === 0 && (
                    <div className="text-center py-12 text-gray-500">
                      No reports to review
                    </div>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Unassigned Patients Tab */}
        <TabsContent value="unassigned" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Unassigned Patients</CardTitle>
              <CardDescription>Patients without a nurse assignment</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {unassignedPatients.map((patient) => (
                  <Card key={patient.id} className="border-l-4 border-l-amber-500">
                    <CardContent className="pt-4">
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="font-medium">{patient.first_name} {patient.last_name}</p>
                          <p className="text-sm text-gray-500">MRN: {patient.mrn || 'N/A'}</p>
                        </div>
                        <Button 
                          size="sm"
                          onClick={() => {
                            setAssignmentForm({ ...assignmentForm, patient_id: patient.id });
                            setSelectedPatient(patient);
                            setAssignPatientOpen(true);
                          }}
                        >
                          <UserPlus className="w-4 h-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
                {unassignedPatients.length === 0 && (
                  <div className="col-span-full text-center py-12 text-gray-500">
                    All patients are assigned
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Assign Patient Dialog */}
      <Dialog open={assignPatientOpen} onOpenChange={setAssignPatientOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Assign Patient to Nurse</DialogTitle>
            <DialogDescription>
              {selectedPatient 
                ? `Assign ${selectedPatient.first_name} ${selectedPatient.last_name} to a nurse`
                : 'Select a patient and nurse for assignment'
              }
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {!selectedPatient && (
              <div className="space-y-2">
                <Label>Patient</Label>
                <Select 
                  value={assignmentForm.patient_id} 
                  onValueChange={(v) => setAssignmentForm({...assignmentForm, patient_id: v})}
                >
                  <SelectTrigger><SelectValue placeholder="Select patient" /></SelectTrigger>
                  <SelectContent>
                    {unassignedPatients.map((p) => (
                      <SelectItem key={p.id} value={p.id}>
                        {p.first_name} {p.last_name} ({p.mrn || 'No MRN'})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            
            <div className="space-y-2">
              <Label>Assign to Nurse</Label>
              <Select 
                value={assignmentForm.nurse_id} 
                onValueChange={(v) => setAssignmentForm({...assignmentForm, nurse_id: v})}
              >
                <SelectTrigger><SelectValue placeholder="Select nurse" /></SelectTrigger>
                <SelectContent>
                  {nurses.filter(n => n.active_shift).map((n) => (
                    <SelectItem key={n.id} value={n.id}>
                      {n.first_name} {n.last_name} ({n.patient_count || 0} patients)
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Room/Bed</Label>
                <Input 
                  placeholder="e.g., 301-A"
                  value={assignmentForm.room_bed}
                  onChange={(e) => setAssignmentForm({...assignmentForm, room_bed: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <Label>Acuity Level (1-5)</Label>
                <Select 
                  value={String(assignmentForm.acuity_level)} 
                  onValueChange={(v) => setAssignmentForm({...assignmentForm, acuity_level: parseInt(v)})}
                >
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">1 - Stable</SelectItem>
                    <SelectItem value="2">2 - Low Risk</SelectItem>
                    <SelectItem value="3">3 - Moderate</SelectItem>
                    <SelectItem value="4">4 - High Risk</SelectItem>
                    <SelectItem value="5">5 - Critical</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea 
                placeholder="Assignment notes..."
                value={assignmentForm.notes}
                onChange={(e) => setAssignmentForm({...assignmentForm, notes: e.target.value})}
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setAssignPatientOpen(false);
              setSelectedPatient(null);
              setAssignmentForm({ patient_id: '', nurse_id: '', room_bed: '', acuity_level: 2, notes: '' });
            }}>
              Cancel
            </Button>
            <Button onClick={handleAssignPatient} disabled={saving}>
              {saving ? 'Assigning...' : 'Assign Patient'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Assign Task Dialog */}
      <Dialog open={assignTaskOpen} onOpenChange={setAssignTaskOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Assign Task to Nurse</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Patient</Label>
              <Select 
                value={taskForm.patient_id} 
                onValueChange={(v) => setTaskForm({...taskForm, patient_id: v})}
              >
                <SelectTrigger><SelectValue placeholder="Select patient" /></SelectTrigger>
                <SelectContent>
                  {unassignedPatients.map((p) => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.first_name} {p.last_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Assign to Nurse</Label>
              <Select 
                value={taskForm.nurse_id} 
                onValueChange={(v) => setTaskForm({...taskForm, nurse_id: v})}
              >
                <SelectTrigger><SelectValue placeholder="Select nurse" /></SelectTrigger>
                <SelectContent>
                  {nurses.filter(n => n.active_shift).map((n) => (
                    <SelectItem key={n.id} value={n.id}>
                      {n.first_name} {n.last_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Task Type</Label>
                <Select 
                  value={taskForm.task_type} 
                  onValueChange={(v) => setTaskForm({...taskForm, task_type: v})}
                >
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="vitals_due">Vitals Check</SelectItem>
                    <SelectItem value="medication_admin">Medication Admin</SelectItem>
                    <SelectItem value="wound_care">Wound Care</SelectItem>
                    <SelectItem value="lab_draw">Lab Draw</SelectItem>
                    <SelectItem value="assessment">Assessment</SelectItem>
                    <SelectItem value="discharge_prep">Discharge Prep</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Priority</Label>
                <Select 
                  value={taskForm.priority} 
                  onValueChange={(v) => setTaskForm({...taskForm, priority: v})}
                >
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="stat">STAT</SelectItem>
                    <SelectItem value="urgent">Urgent</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="routine">Routine</SelectItem>
                    <SelectItem value="low">Low</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div className="space-y-2">
              <Label>Description *</Label>
              <Textarea 
                placeholder="Task description..."
                value={taskForm.description}
                onChange={(e) => setTaskForm({...taskForm, description: e.target.value})}
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setAssignTaskOpen(false)}>Cancel</Button>
            <Button onClick={handleAssignTask} disabled={saving}>
              {saving ? 'Assigning...' : 'Assign Task'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* View Report Dialog */}
      <Dialog open={viewReportOpen} onOpenChange={setViewReportOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Shift Report</DialogTitle>
          </DialogHeader>
          
          {selectedReport && (
            <ScrollArea className="max-h-[60vh]">
              <div className="space-y-4 py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-lg">{selectedReport.title}</h3>
                    <p className="text-sm text-gray-500">{selectedReport.nurse_name} • {selectedReport.shift_type?.toUpperCase()}</p>
                  </div>
                  <Badge className={
                    selectedReport.status === 'submitted' ? 'bg-amber-100 text-amber-700' :
                    selectedReport.status === 'reviewed' ? 'bg-emerald-100 text-emerald-700' :
                    'bg-gray-100 text-gray-700'
                  }>
                    {selectedReport.status?.toUpperCase()}
                  </Badge>
                </div>
                
                <Separator />
                
                <div>
                  <Label className="text-xs text-gray-500">Report Content</Label>
                  <p className="mt-1 whitespace-pre-wrap">{selectedReport.content}</p>
                </div>
                
                {selectedReport.patient_summary && (
                  <div>
                    <Label className="text-xs text-gray-500">Patient Summary</Label>
                    <p className="mt-1 whitespace-pre-wrap">{selectedReport.patient_summary}</p>
                  </div>
                )}
                
                {selectedReport.critical_events && (
                  <div>
                    <Label className="text-xs text-gray-500">Critical Events</Label>
                    <p className="mt-1 whitespace-pre-wrap text-red-700">{selectedReport.critical_events}</p>
                  </div>
                )}
                
                {selectedReport.pending_items && (
                  <div>
                    <Label className="text-xs text-gray-500">Pending Items</Label>
                    <p className="mt-1 whitespace-pre-wrap">{selectedReport.pending_items}</p>
                  </div>
                )}
                
                {selectedReport.recommendations && (
                  <div>
                    <Label className="text-xs text-gray-500">Recommendations</Label>
                    <p className="mt-1 whitespace-pre-wrap">{selectedReport.recommendations}</p>
                  </div>
                )}
                
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span>Patients: {selectedReport.patient_count}</span>
                  <span>Submitted: {new Date(selectedReport.created_at).toLocaleString()}</span>
                </div>
                
                {selectedReport.review_notes && (
                  <Alert className="bg-emerald-50 border-emerald-200">
                    <CheckCircle className="h-4 w-4 text-emerald-600" />
                    <AlertTitle className="text-emerald-800">Supervisor Review</AlertTitle>
                    <AlertDescription className="text-emerald-700">
                      <p className="mt-1">{selectedReport.review_notes}</p>
                      <p className="text-xs mt-2">Reviewed by {selectedReport.reviewed_by_name} on {new Date(selectedReport.reviewed_at).toLocaleString()}</p>
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            </ScrollArea>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setViewReportOpen(false)}>Close</Button>
            {selectedReport?.status === 'submitted' && (
              <Button onClick={() => {
                setViewReportOpen(false);
                setReviewReportOpen(true);
              }}>
                <CheckCircle className="w-4 h-4 mr-2" />
                Review Report
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Review Report Dialog */}
      <Dialog open={reviewReportOpen} onOpenChange={setReviewReportOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Review Report</DialogTitle>
            <DialogDescription>
              Add your review notes for this shift report
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {selectedReport && (
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="font-medium">{selectedReport.title}</p>
                <p className="text-sm text-gray-500">{selectedReport.nurse_name}</p>
              </div>
            )}
            
            <div className="space-y-2">
              <Label>Review Notes *</Label>
              <Textarea 
                placeholder="Add your review comments, feedback, or follow-up items..."
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                rows={4}
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setReviewReportOpen(false);
              setReviewNotes('');
            }}>
              Cancel
            </Button>
            <Button onClick={handleReviewReport} disabled={saving || !reviewNotes.trim()}>
              {saving ? 'Submitting...' : 'Mark as Reviewed'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* View Nurse Workload Dialog */}
      <Dialog open={viewNurseOpen} onOpenChange={setViewNurseOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Nurse Workload</DialogTitle>
          </DialogHeader>
          
          {nurseWorkload && (
            <div className="space-y-4 py-4">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center text-white font-bold">
                  {nurseWorkload.nurse?.first_name?.[0]}{nurseWorkload.nurse?.last_name?.[0]}
                </div>
                <div>
                  <p className="font-semibold">{nurseWorkload.nurse?.first_name} {nurseWorkload.nurse?.last_name}</p>
                  <p className="text-sm text-gray-500">{nurseWorkload.nurse?.email}</p>
                </div>
              </div>
              
              <Separator />
              
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-emerald-50 rounded-lg text-center">
                  <p className="text-2xl font-bold text-emerald-700">{nurseWorkload.patient_count}</p>
                  <p className="text-xs text-emerald-600">Assigned Patients</p>
                </div>
                <div className="p-3 bg-amber-50 rounded-lg text-center">
                  <p className="text-2xl font-bold text-amber-700">{nurseWorkload.pending_tasks}</p>
                  <p className="text-xs text-amber-600">Pending Tasks</p>
                </div>
                <div className="p-3 bg-red-50 rounded-lg text-center">
                  <p className="text-2xl font-bold text-red-700">{nurseWorkload.overdue_tasks}</p>
                  <p className="text-xs text-red-600">Overdue Tasks</p>
                </div>
                <div className="p-3 bg-blue-50 rounded-lg text-center">
                  <p className="text-2xl font-bold text-blue-700">
                    {nurseWorkload.active_shift ? 'Yes' : 'No'}
                  </p>
                  <p className="text-xs text-blue-600">On Shift</p>
                </div>
              </div>
              
              {nurseWorkload.active_shift && (
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm font-medium">Current Shift</p>
                  <p className="text-sm text-gray-600">
                    {nurseWorkload.active_shift.shift_type?.toUpperCase()} • 
                    Started {new Date(nurseWorkload.active_shift.clock_in_time).toLocaleTimeString()}
                  </p>
                </div>
              )}
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setViewNurseOpen(false);
              setNurseWorkload(null);
            }}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
