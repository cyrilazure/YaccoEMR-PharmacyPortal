import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import { nurseAPI, patientAPI } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle, 
  DialogTrigger, 
  DialogFooter 
} from '@/components/ui/dialog';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { toast } from 'sonner';
import { 
  Activity, Pill, ClipboardList, CheckCircle2, Clock, 
  Heart, User, Plus, Check, Bell, LogIn, LogOut, 
  Users, Stethoscope, AlertCircle, Timer, Shield, 
  Droplets, Gauge, RefreshCw, Eye, Search, Hash, Calendar, IdCard,
  FileText, Send, Edit, Save, FileCheck
} from 'lucide-react';

const priorityColors = { 
  stat: 'bg-red-500 text-white', 
  urgent: 'bg-orange-500 text-white', 
  high: 'bg-amber-500 text-white', 
  routine: 'bg-blue-500 text-white', 
  low: 'bg-slate-400 text-white' 
};

const marStatusColors = { 
  scheduled: 'bg-slate-100 text-slate-700', 
  given: 'bg-emerald-100 text-emerald-700', 
  held: 'bg-amber-100 text-amber-700', 
  refused: 'bg-red-100 text-red-700' 
};

function getAcuityColor(level) {
  if (level >= 4) return 'bg-red-100 text-red-700';
  if (level >= 3) return 'bg-amber-100 text-amber-700';
  return 'bg-emerald-100 text-emerald-700';
}

function formatTime(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
}

// Stat Card Component
function StatCard({ label, value, icon: Icon, color }) {
  return (
    <Card className={`border-l-4 border-l-${color}-500`}>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-500 uppercase">{label}</p>
            <p className="text-2xl font-bold text-slate-900">{value}</p>
          </div>
          <Icon className={`w-8 h-8 text-${color}-500`} />
        </div>
      </CardContent>
    </Card>
  );
}

// Patient Card Component
function PatientCard({ item, onVitals, onView }) {
  return (
    <div 
      className="p-3 rounded-lg border border-slate-200 hover:border-sky-200 hover:bg-sky-50/50 cursor-pointer"
      onClick={onView}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center">
            <User className="w-5 h-5 text-slate-500" />
          </div>
          <div>
            <p className="font-medium text-slate-900">
              {item.patient.first_name} {item.patient.last_name}
            </p>
            <p className="text-xs text-slate-500">MRN: {item.patient.mrn}</p>
          </div>
        </div>
        <Badge className={getAcuityColor(item.acuity_level)}>
          Acuity {item.acuity_level}
        </Badge>
      </div>
      <div className="flex items-center gap-4 mt-3 text-xs">
        {item.latest_vitals ? (
          <>
            <span className="flex items-center gap-1 text-slate-600">
              <Heart className="w-3 h-3" />
              {item.latest_vitals.heart_rate || '--'}
            </span>
            <span className="flex items-center gap-1 text-slate-600">
              <Gauge className="w-3 h-3" />
              {item.latest_vitals.blood_pressure_systolic || '--'}/{item.latest_vitals.blood_pressure_diastolic || '--'}
            </span>
            <span className="flex items-center gap-1 text-slate-600">
              <Droplets className="w-3 h-3" />
              {item.latest_vitals.oxygen_saturation || '--'}%
            </span>
          </>
        ) : (
          <span className="text-amber-600 flex items-center gap-1">
            <Activity className="w-3 h-3" />No vitals
          </span>
        )}
      </div>
      <div className="flex items-center gap-2 mt-3">
        <Button 
          size="sm" 
          variant="outline" 
          className="h-7 text-xs flex-1"
          onClick={(e) => { e.stopPropagation(); onVitals(); }}
        >
          <Heart className="w-3 h-3 mr-1" />Vitals
        </Button>
        <Button 
          size="sm" 
          variant="outline" 
          className="h-7 text-xs flex-1"
          onClick={(e) => { e.stopPropagation(); onView(); }}
        >
          <Eye className="w-3 h-3 mr-1" />Chart
        </Button>
      </div>
    </div>
  );
}

// Task Card Component
function TaskCard({ task, onComplete, isOverdue }) {
  const borderClass = isOverdue ? 'border-red-200 bg-red-50 border-l-red-500' : 'border-slate-200 border-l-blue-500';
  return (
    <div className={`p-3 rounded-lg border border-l-4 ${borderClass}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <Badge className={priorityColors[task.priority] || priorityColors.routine}>
              {task.priority?.toUpperCase()}
            </Badge>
            <span className="text-sm font-medium">
              {task.task_type?.replace('_', ' ').toUpperCase()}
            </span>
          </div>
          <p className="text-sm text-slate-600 mt-1">{task.description}</p>
          <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
            <span className="flex items-center gap-1">
              <User className="w-3 h-3" />{task.patient_name}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />Due: {formatTime(task.due_time)}
            </span>
          </div>
        </div>
        <Button size="sm" variant="outline" className="h-8" onClick={onComplete}>
          <Check className="w-4 h-4 mr-1" />Done
        </Button>
      </div>
    </div>
  );
}

// Medication Card Component
function MedCard({ entry, onAction, isOverdue }) {
  const borderClass = isOverdue ? 'border-red-200 bg-red-50' : 'border-slate-200';
  return (
    <div className={`p-3 rounded-lg border ${borderClass}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="font-medium text-slate-900">{entry.medication_name}</p>
          <div className="flex items-center gap-3 mt-1 text-sm text-slate-600">
            <span>{entry.dosage}</span>
            <span className="text-slate-400">•</span>
            <span>{entry.route}</span>
          </div>
          <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />{formatTime(entry.scheduled_time)}
            </span>
            <Badge className={marStatusColors[entry.status] || marStatusColors.scheduled}>
              {entry.status?.toUpperCase()}
            </Badge>
          </div>
        </div>
        <Button size="sm" onClick={onAction} className="bg-blue-600 hover:bg-blue-700">
          <Pill className="w-4 h-4 mr-1" />Admin
        </Button>
      </div>
    </div>
  );
}

export default function NurseDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [myPatients, setMyPatients] = useState([]);
  const [tasks, setTasks] = useState({ overdue: [], upcoming_30min: [] });
  const [medicationsDue, setMedicationsDue] = useState({ overdue: [], upcoming: [] });
  const [activeShift, setActiveShift] = useState(null);
  const [currentShiftType, setCurrentShiftType] = useState('');
  
  const [clockInOpen, setClockInOpen] = useState(false);
  const [clockOutOpen, setClockOutOpen] = useState(false);
  const [vitalsOpen, setVitalsOpen] = useState(false);
  const [taskOpen, setTaskOpen] = useState(false);
  const [marOpen, setMarOpen] = useState(false);
  
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [selectedMAR, setSelectedMAR] = useState(null);
  
  const [shiftType, setShiftType] = useState('morning');
  const [handoffNotes, setHandoffNotes] = useState('');
  const [vitals, setVitals] = useState({ 
    bp_sys: '', bp_dia: '', hr: '', rr: '', 
    temp: '', spo2: '', pain: '', notes: '' 
  });
  const [newTask, setNewTask] = useState({ 
    patient_id: '', task_type: 'vitals_due', 
    description: '', priority: 'routine' 
  });
  const [marAction, setMarAction] = useState({ 
    status: 'given', notes: '', held_reason: '' 
  });
  
  // Patient search state
  const [patientSearch, setPatientSearch] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);

  // Shift Reports state
  const [reports, setReports] = useState([]);
  const [reportOpen, setReportOpen] = useState(false);
  const [viewReportOpen, setViewReportOpen] = useState(false);
  const [selectedReport, setSelectedReport] = useState(null);
  const [newReport, setNewReport] = useState({
    title: '',
    content: '',
    patient_summary: '',
    critical_events: '',
    pending_items: '',
    recommendations: ''
  });
  
  // Assigned Patient Medications state
  const [assignedMeds, setAssignedMeds] = useState({ patients: [], total_medications: 0 });
  const [medsLoading, setMedsLoading] = useState(false);

  const isNurse = user?.role === 'nurse';

  // Patient search handler
  const handlePatientSearch = async () => {
    if (!patientSearch.trim()) return;
    
    setSearching(true);
    try {
      const res = await patientAPI.getAll({ search: patientSearch });
      setSearchResults(res.data || []);
    } catch (err) {
      toast.error('Search failed');
    } finally {
      setSearching(false);
    }
  };

  // Fetch shift reports
  const fetchReports = async () => {
    try {
      const res = await nurseAPI.getMyReports();
      setReports(res.data.reports || []);
    } catch (err) {
      console.error('Failed to fetch reports:', err);
    }
  };

  // Fetch all assigned patient medications
  const fetchAssignedMeds = async () => {
    setMedsLoading(true);
    try {
      const res = await nurseAPI.getAllAssignedMedications();
      setAssignedMeds(res.data);
    } catch (err) {
      console.error('Failed to fetch medications:', err);
    } finally {
      setMedsLoading(false);
    }
  };

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [statsRes, patientsRes, shiftRes, tasksRes, medsRes] = await Promise.all([
        nurseAPI.getDashboardStats(),
        nurseAPI.getMyPatients({ include_vitals: true }),
        nurseAPI.getCurrentShift(),
        nurseAPI.getDueTasks(),
        nurseAPI.getMedicationsDue(60)
      ]);
      setStats(statsRes.data);
      setMyPatients(patientsRes.data.patients || []);
      setCurrentShiftType(shiftRes.data.current_time_shift);
      setActiveShift(shiftRes.data.active_shift);
      setTasks(tasksRes.data);
      setMedicationsDue(medsRes.data);
      
      // Also fetch reports
      fetchReports();
    } catch (err) {
      console.error('Dashboard fetch error:', err);
      // Only show session expired for actual auth errors (401 Unauthorized)
      if (err.response?.status === 401) {
        toast.error('Session expired. Please login again.');
      }
      // 403 is often just access denied, not session expired
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 120000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleClockIn = async () => {
    try {
      await nurseAPI.clockIn({ shift_type: shiftType });
      toast.success('Clocked in successfully');
      setClockInOpen(false);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to clock in');
    }
  };

  const handleClockOut = async () => {
    try {
      await nurseAPI.clockOut(handoffNotes);
      toast.success('Clocked out successfully');
      setClockOutOpen(false);
      setHandoffNotes('');
      fetchData();
    } catch {
      toast.error('Failed to clock out');
    }
  };

  const handleRecordVitals = async (e) => {
    e.preventDefault();
    if (!selectedPatient) return;
    try {
      const data = { patient_id: selectedPatient.patient.id };
      if (vitals.bp_sys) data.blood_pressure_systolic = parseInt(vitals.bp_sys);
      if (vitals.bp_dia) data.blood_pressure_diastolic = parseInt(vitals.bp_dia);
      if (vitals.hr) data.heart_rate = parseInt(vitals.hr);
      if (vitals.rr) data.respiratory_rate = parseInt(vitals.rr);
      if (vitals.temp) data.temperature = parseFloat(vitals.temp);
      if (vitals.spo2) data.oxygen_saturation = parseInt(vitals.spo2);
      if (vitals.pain) data.pain_level = parseInt(vitals.pain);
      if (vitals.notes) data.notes = vitals.notes;
      await nurseAPI.quickRecordVitals(data);
      toast.success('Vitals recorded');
      setVitalsOpen(false);
      setVitals({ bp_sys: '', bp_dia: '', hr: '', rr: '', temp: '', spo2: '', pain: '', notes: '' });
      fetchData();
    } catch {
      toast.error('Failed to record vitals');
    }
  };

  const handleCompleteTask = async (taskId) => {
    try {
      await nurseAPI.completeTask(taskId);
      toast.success('Task completed');
      fetchData();
    } catch {
      toast.error('Failed to complete task');
    }
  };

  const handleCreateTask = async (e) => {
    e.preventDefault();
    try {
      await nurseAPI.createTask(newTask);
      toast.success('Task created');
      setTaskOpen(false);
      setNewTask({ patient_id: '', task_type: 'vitals_due', description: '', priority: 'routine' });
      fetchData();
    } catch {
      toast.error('Failed to create task');
    }
  };

  const handleMARAction = async () => {
    if (!selectedMAR) return;
    try {
      await nurseAPI.administerMedication({
        mar_entry_id: selectedMAR.id,
        status: marAction.status,
        notes: marAction.notes,
        held_reason: marAction.status === 'held' ? marAction.held_reason : null
      });
      toast.success('Medication updated');
      setMarOpen(false);
      setSelectedMAR(null);
      setMarAction({ status: 'given', notes: '', held_reason: '' });
      fetchData();
    } catch {
      toast.error('Failed to update medication');
    }
  };

  // Create shift report
  const handleCreateReport = async (e) => {
    e.preventDefault();
    if (!activeShift) {
      toast.error('Must be clocked in to create a report');
      return;
    }
    try {
      await nurseAPI.createReport({
        shift_id: activeShift.id,
        report_type: 'end_of_shift',
        title: newReport.title || `Shift Report - ${new Date().toLocaleDateString()}`,
        content: newReport.content,
        patient_summary: newReport.patient_summary,
        critical_events: newReport.critical_events,
        pending_items: newReport.pending_items,
        recommendations: newReport.recommendations
      });
      toast.success('Report created');
      setReportOpen(false);
      setNewReport({ title: '', content: '', patient_summary: '', critical_events: '', pending_items: '', recommendations: '' });
      fetchReports();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create report');
    }
  };

  // Submit report for supervisor review
  const handleSubmitReport = async (reportId) => {
    try {
      await nurseAPI.submitReport(reportId);
      toast.success('Report submitted for review');
      fetchReports();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to submit report');
    }
  };

  const getShiftProgress = () => {
    if (!activeShift) return 0;
    const elapsed = (new Date() - new Date(activeShift.clock_in_time)) / (1000 * 60 * 60);
    const duration = activeShift.shift_type?.includes('12') ? 12 : 8;
    return Math.min(100, (elapsed / duration) * 100);
  };

  if (loading && !stats) {
    return (
      <div className="space-y-6 p-6">
        <Skeleton className="h-20 w-full" />
        <div className="grid grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-24" />)}
        </div>
      </div>
    );
  }

  const statItems = [
    { label: 'My Patients', value: stats?.patient_count || 0, icon: Users, color: 'emerald' },
    { label: 'STAT Tasks', value: stats?.stat_tasks || 0, icon: AlertCircle, color: 'red' },
    { label: 'Urgent Tasks', value: stats?.urgent_tasks || 0, icon: Timer, color: 'orange' },
    { label: 'Meds Due', value: stats?.medications_due || 0, icon: Pill, color: 'blue' },
    { label: 'Vitals Due', value: stats?.vitals_due || 0, icon: Heart, color: 'amber' },
    { label: 'Notifications', value: stats?.unread_notifications || 0, icon: Bell, color: 'purple' },
  ];

  return (
    <div className="space-y-6" data-testid="nurse-dashboard">
      {/* Role Alert */}
      {!isNurse && (
        <Alert className="border-amber-200 bg-amber-50">
          <Shield className="h-4 w-4 text-amber-600" />
          <AlertTitle className="text-amber-800">Viewing as {user?.role}</AlertTitle>
          <AlertDescription className="text-amber-700">
            Some features may have different access levels.
          </AlertDescription>
        </Alert>
      )}

      {/* Header */}
      <div className="flex items-center justify-between bg-white rounded-xl p-4 shadow-sm border">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-sky-500 to-sky-600 flex items-center justify-center shadow-lg">
            <Stethoscope className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Nursing Workstation</h1>
            <p className="text-slate-500">Welcome, {user?.first_name}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {activeShift ? (
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="flex items-center gap-2 text-emerald-600">
                  <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="font-medium">On Shift</span>
                </div>
                <p className="text-sm text-slate-500">
                  {activeShift.shift_type?.toUpperCase()} • Started {formatTime(activeShift.clock_in_time)}
                </p>
                <Progress value={getShiftProgress()} className="h-1.5 w-32 mt-1" />
              </div>
              <Dialog open={clockOutOpen} onOpenChange={setClockOutOpen}>
                <DialogTrigger asChild>
                  <Button variant="outline" className="gap-2 border-red-200 text-red-600 hover:bg-red-50">
                    <LogOut className="w-4 h-4" />Clock Out
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Clock Out</DialogTitle>
                    <DialogDescription>End your shift and provide handoff notes</DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 mt-4">
                    <div className="bg-slate-50 p-3 rounded-lg text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-500">Patients:</span>
                        <span>{stats?.patient_count || 0}</span>
                      </div>
                      <div className="flex justify-between mt-1">
                        <span className="text-slate-500">Pending tasks:</span>
                        <span>{stats?.pending_tasks || 0}</span>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Handoff Notes</Label>
                      <Textarea 
                        placeholder="Critical info for incoming shift..." 
                        value={handoffNotes} 
                        onChange={(e) => setHandoffNotes(e.target.value)} 
                        rows={4} 
                      />
                    </div>
                  </div>
                  <DialogFooter className="mt-4">
                    <Button variant="outline" onClick={() => setClockOutOpen(false)}>Cancel</Button>
                    <Button onClick={handleClockOut} className="bg-red-600 hover:bg-red-700">Clock Out</Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>
          ) : (
            <Dialog open={clockInOpen} onOpenChange={setClockInOpen}>
              <DialogTrigger asChild>
                <Button className="gap-2 bg-emerald-600 hover:bg-emerald-700">
                  <LogIn className="w-4 h-4" />Clock In
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Clock In to Shift</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 mt-4">
                  <div className="space-y-2">
                    <Label>Shift Type</Label>
                    <Select value={shiftType} onValueChange={setShiftType}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="morning">Morning (7AM - 3PM)</SelectItem>
                        <SelectItem value="evening">Evening (3PM - 11PM)</SelectItem>
                        <SelectItem value="night">Night (11PM - 7AM)</SelectItem>
                        <SelectItem value="day_12">12-Hour Day</SelectItem>
                        <SelectItem value="night_12">12-Hour Night</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="p-3 bg-blue-50 rounded-lg text-sm text-blue-700">
                    Current Time Shift: {currentShiftType?.toUpperCase()}
                  </div>
                </div>
                <DialogFooter className="mt-4">
                  <Button variant="outline" onClick={() => setClockInOpen(false)}>Cancel</Button>
                  <Button onClick={handleClockIn} className="bg-emerald-600 hover:bg-emerald-700">Clock In</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          )}
          <Button variant="outline" size="icon" onClick={fetchData}>
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Patient Search Section */}
      <Card className="border-sky-100 bg-gradient-to-r from-sky-50 to-white">
        <CardContent className="py-4">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sky-700">
              <Search className="w-5 h-5" />
              <span className="font-medium">Patient Lookup</span>
            </div>
            <div className="flex-1 flex items-center gap-2 max-w-xl">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <Input
                  placeholder="Search by MRN, First Name, Last Name, or Date of Birth..."
                  value={patientSearch}
                  onChange={(e) => setPatientSearch(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handlePatientSearch()}
                  className="pl-9"
                />
              </div>
              <Button onClick={handlePatientSearch} disabled={searching}>
                {searching ? 'Searching...' : 'Search'}
              </Button>
            </div>
          </div>
          
          {/* Search Results */}
          {searchResults.length > 0 && (
            <div className="mt-4 space-y-2">
              <p className="text-sm text-gray-500">{searchResults.length} patient(s) found</p>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {searchResults.slice(0, 6).map((patient) => (
                  <div 
                    key={patient.id}
                    className="flex items-center justify-between p-3 bg-white rounded-lg border hover:border-sky-300 cursor-pointer"
                    onClick={() => navigate(`/patients/${patient.id}`)}
                  >
                    <div>
                      <p className="font-medium">{patient.first_name} {patient.last_name}</p>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        {patient.mrn ? (
                          <Badge className="bg-emerald-100 text-emerald-700 font-mono text-xs">{patient.mrn}</Badge>
                        ) : (
                          <Badge variant="outline" className="text-orange-600 text-xs">No MRN</Badge>
                        )}
                        <span>{patient.date_of_birth ? new Date(patient.date_of_birth).toLocaleDateString() : ''}</span>
                      </div>
                    </div>
                    <Button size="sm" variant="outline">
                      <Eye className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
        {statItems.map((stat) => (
          <StatCard key={stat.label} {...stat} />
        ))}
      </div>

      {/* Access Info */}
      {isNurse && (
        <Alert className="border-sky-200 bg-sky-50">
          <Shield className="h-4 w-4 text-sky-600" />
          <AlertTitle className="text-sky-800">Nursing Access (Read-Only for Orders)</AlertTitle>
          <AlertDescription className="text-sky-700">
            You can: Record vitals, administer medications (MAR), create shift reports. 
            <span className="font-medium"> Read-only: </span> Medications, Lab orders, Imaging orders (contact physician for prescriptions).
          </AlertDescription>
        </Alert>
      )}

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Patient Panel */}
        <Card className="lg:col-span-1">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Users className="w-5 h-5 text-emerald-500" />My Patients
              </CardTitle>
              <Badge variant="secondary">{myPatients.length}</Badge>
            </div>
            <CardDescription>Assigned patients for your shift</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[450px] pr-4">
              {myPatients.length === 0 ? (
                <div className="text-center py-12 text-slate-500">
                  <Users className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                  <p>No patients assigned</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {myPatients.map((item) => (
                    <PatientCard
                      key={item.patient.id}
                      item={item}
                      onVitals={() => { setSelectedPatient(item); setVitalsOpen(true); }}
                      onView={() => navigate(`/patients/${item.patient.id}`)}
                    />
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Tasks & MAR Panel */}
        <Card className="lg:col-span-2">
          <Tabs defaultValue="tasks">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <TabsList>
                  <TabsTrigger value="tasks" className="gap-2">
                    <ClipboardList className="w-4 h-4" />Tasks
                    {(tasks.overdue?.length > 0 || tasks.upcoming_30min?.length > 0) && (
                      <Badge variant="destructive" className="ml-1 h-5 w-5 p-0 flex items-center justify-center text-xs">
                        {(tasks.overdue?.length || 0) + (tasks.upcoming_30min?.length || 0)}
                      </Badge>
                    )}
                  </TabsTrigger>
                  <TabsTrigger value="medications" className="gap-2">
                    <Pill className="w-4 h-4" />Meds Due
                    {medicationsDue.overdue?.length > 0 && (
                      <Badge variant="destructive" className="ml-1 h-5 w-5 p-0 flex items-center justify-center text-xs">
                        {medicationsDue.overdue.length}
                      </Badge>
                    )}
                  </TabsTrigger>
                </TabsList>
                <Dialog open={taskOpen} onOpenChange={setTaskOpen}>
                  <DialogTrigger asChild>
                    <Button size="sm" variant="outline" className="gap-1">
                      <Plus className="w-4 h-4" />Add Task
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader><DialogTitle>Create New Task</DialogTitle></DialogHeader>
                    <form onSubmit={handleCreateTask} className="space-y-4 mt-4">
                      <div className="space-y-2">
                        <Label>Patient</Label>
                        <Select 
                          value={newTask.patient_id} 
                          onValueChange={(v) => setNewTask({ ...newTask, patient_id: v })}
                        >
                          <SelectTrigger><SelectValue placeholder="Select patient" /></SelectTrigger>
                          <SelectContent>
                            {myPatients.map((p) => (
                              <SelectItem key={p.patient.id} value={p.patient.id}>
                                {p.patient.first_name} {p.patient.last_name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Task Type</Label>
                          <Select 
                            value={newTask.task_type} 
                            onValueChange={(v) => setNewTask({ ...newTask, task_type: v })}
                          >
                            <SelectTrigger><SelectValue /></SelectTrigger>
                            <SelectContent>
                              <SelectItem value="vitals_due">Vitals Due</SelectItem>
                              <SelectItem value="medication_due">Medication Due</SelectItem>
                              <SelectItem value="wound_care">Wound Care</SelectItem>
                              <SelectItem value="iv_check">IV Check</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <Label>Priority</Label>
                          <Select 
                            value={newTask.priority} 
                            onValueChange={(v) => setNewTask({ ...newTask, priority: v })}
                          >
                            <SelectTrigger><SelectValue /></SelectTrigger>
                            <SelectContent>
                              <SelectItem value="stat">STAT</SelectItem>
                              <SelectItem value="urgent">Urgent</SelectItem>
                              <SelectItem value="routine">Routine</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label>Description</Label>
                        <Textarea 
                          placeholder="Task details..." 
                          value={newTask.description} 
                          onChange={(e) => setNewTask({ ...newTask, description: e.target.value })} 
                          required 
                        />
                      </div>
                      <DialogFooter><Button type="submit">Create Task</Button></DialogFooter>
                    </form>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent>
              <TabsContent value="tasks" className="mt-0">
                <ScrollArea className="h-[400px] pr-4">
                  {tasks.overdue?.length > 0 && (
                    <div className="mb-4">
                      <h4 className="text-sm font-medium text-red-600 mb-2 flex items-center gap-2">
                        <AlertCircle className="w-4 h-4" />Overdue ({tasks.overdue.length})
                      </h4>
                      <div className="space-y-2">
                        {tasks.overdue.map((t) => (
                          <TaskCard 
                            key={t.id} 
                            task={t} 
                            onComplete={() => handleCompleteTask(t.id)} 
                            isOverdue 
                          />
                        ))}
                      </div>
                    </div>
                  )}
                  {tasks.upcoming_30min?.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-amber-600 mb-2 flex items-center gap-2">
                        <Clock className="w-4 h-4" />Due Soon ({tasks.upcoming_30min.length})
                      </h4>
                      <div className="space-y-2">
                        {tasks.upcoming_30min.map((t) => (
                          <TaskCard 
                            key={t.id} 
                            task={t} 
                            onComplete={() => handleCompleteTask(t.id)} 
                          />
                        ))}
                      </div>
                    </div>
                  )}
                  {!tasks.overdue?.length && !tasks.upcoming_30min?.length && (
                    <div className="text-center py-12 text-slate-500">
                      <CheckCircle2 className="w-12 h-12 mx-auto mb-3 text-emerald-300" />
                      <p className="font-medium text-emerald-600">All caught up!</p>
                    </div>
                  )}
                </ScrollArea>
              </TabsContent>
              <TabsContent value="medications" className="mt-0">
                <ScrollArea className="h-[400px] pr-4">
                  {medicationsDue.overdue?.length > 0 && (
                    <div className="mb-4">
                      <h4 className="text-sm font-medium text-red-600 mb-2 flex items-center gap-2">
                        <AlertCircle className="w-4 h-4" />Overdue ({medicationsDue.overdue.length})
                      </h4>
                      <div className="space-y-2">
                        {medicationsDue.overdue.map((e) => (
                          <MedCard 
                            key={e.id} 
                            entry={e} 
                            onAction={() => { setSelectedMAR(e); setMarOpen(true); }} 
                            isOverdue 
                          />
                        ))}
                      </div>
                    </div>
                  )}
                  {medicationsDue.upcoming?.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-blue-600 mb-2 flex items-center gap-2">
                        <Clock className="w-4 h-4" />Upcoming ({medicationsDue.upcoming.length})
                      </h4>
                      <div className="space-y-2">
                        {medicationsDue.upcoming.map((e) => (
                          <MedCard 
                            key={e.id} 
                            entry={e} 
                            onAction={() => { setSelectedMAR(e); setMarOpen(true); }} 
                          />
                        ))}
                      </div>
                    </div>
                  )}
                  {!medicationsDue.overdue?.length && !medicationsDue.upcoming?.length && (
                    <div className="text-center py-12 text-slate-500">
                      <Pill className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                      <p>No medications due</p>
                    </div>
                  )}
                </ScrollArea>
              </TabsContent>
            </CardContent>
          </Tabs>
        </Card>
      </div>

      {/* Vitals Dialog */}
      <Dialog open={vitalsOpen} onOpenChange={setVitalsOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Heart className="w-5 h-5 text-red-500" />Record Vitals
            </DialogTitle>
            <DialogDescription>
              {selectedPatient && `${selectedPatient.patient.first_name} ${selectedPatient.patient.last_name}`}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleRecordVitals} className="space-y-4 mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Systolic BP</Label>
                <Input 
                  type="number" 
                  placeholder="120" 
                  value={vitals.bp_sys} 
                  onChange={(e) => setVitals({ ...vitals, bp_sys: e.target.value })} 
                />
              </div>
              <div className="space-y-2">
                <Label>Diastolic BP</Label>
                <Input 
                  type="number" 
                  placeholder="80" 
                  value={vitals.bp_dia} 
                  onChange={(e) => setVitals({ ...vitals, bp_dia: e.target.value })} 
                />
              </div>
              <div className="space-y-2">
                <Label>Heart Rate</Label>
                <Input 
                  type="number" 
                  placeholder="72" 
                  value={vitals.hr} 
                  onChange={(e) => setVitals({ ...vitals, hr: e.target.value })} 
                />
              </div>
              <div className="space-y-2">
                <Label>Temperature (°F)</Label>
                <Input 
                  type="number" 
                  step="0.1" 
                  placeholder="98.6" 
                  value={vitals.temp} 
                  onChange={(e) => setVitals({ ...vitals, temp: e.target.value })} 
                />
              </div>
              <div className="space-y-2">
                <Label>SpO2 (%)</Label>
                <Input 
                  type="number" 
                  placeholder="98" 
                  value={vitals.spo2} 
                  onChange={(e) => setVitals({ ...vitals, spo2: e.target.value })} 
                />
              </div>
              <div className="space-y-2">
                <Label>Resp Rate</Label>
                <Input 
                  type="number" 
                  placeholder="16" 
                  value={vitals.rr} 
                  onChange={(e) => setVitals({ ...vitals, rr: e.target.value })} 
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Pain Level (0-10)</Label>
              <Input 
                type="number" 
                min="0" 
                max="10" 
                placeholder="0" 
                value={vitals.pain} 
                onChange={(e) => setVitals({ ...vitals, pain: e.target.value })} 
              />
            </div>
            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea 
                placeholder="Additional observations..." 
                value={vitals.notes} 
                onChange={(e) => setVitals({ ...vitals, notes: e.target.value })} 
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setVitalsOpen(false)}>Cancel</Button>
              <Button type="submit" className="bg-sky-600 hover:bg-sky-700">Save Vitals</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* MAR Dialog */}
      <Dialog open={marOpen} onOpenChange={setMarOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Pill className="w-5 h-5 text-blue-500" />Medication Administration
            </DialogTitle>
            <DialogDescription>{selectedMAR?.medication_name}</DialogDescription>
          </DialogHeader>
          {selectedMAR && (
            <div className="space-y-4 mt-4">
              <div className="bg-slate-50 p-3 rounded-lg space-y-1 text-sm">
                <p><span className="text-slate-500">Dosage:</span> {selectedMAR.dosage}</p>
                <p><span className="text-slate-500">Route:</span> {selectedMAR.route}</p>
                <p><span className="text-slate-500">Scheduled:</span> {formatTime(selectedMAR.scheduled_time)}</p>
              </div>
              <div className="space-y-2">
                <Label>Action</Label>
                <Select 
                  value={marAction.status} 
                  onValueChange={(v) => setMarAction({ ...marAction, status: v })}
                >
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="given">Given</SelectItem>
                    <SelectItem value="held">Held</SelectItem>
                    <SelectItem value="refused">Refused</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {marAction.status === 'held' && (
                <div className="space-y-2">
                  <Label>Held Reason</Label>
                  <Select 
                    value={marAction.held_reason} 
                    onValueChange={(v) => setMarAction({ ...marAction, held_reason: v })}
                  >
                    <SelectTrigger><SelectValue placeholder="Select reason" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="NPO">NPO</SelectItem>
                      <SelectItem value="vital_signs">Abnormal Vital Signs</SelectItem>
                      <SelectItem value="physician_order">Physician Order</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}
              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea 
                  placeholder="Additional notes..." 
                  value={marAction.notes} 
                  onChange={(e) => setMarAction({ ...marAction, notes: e.target.value })} 
                />
              </div>
            </div>
          )}
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setMarOpen(false)}>Cancel</Button>
            <Button onClick={handleMARAction} className="bg-blue-600 hover:bg-blue-700">Confirm</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Shift Reports Section */}
      <Card className="mt-6">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-lg">
              <FileText className="w-5 h-5 text-purple-500" />
              Shift Reports
            </CardTitle>
            <Dialog open={reportOpen} onOpenChange={setReportOpen}>
              <DialogTrigger asChild>
                <Button size="sm" className="gap-2 bg-purple-600 hover:bg-purple-700" disabled={!activeShift}>
                  <Plus className="w-4 h-4" />
                  New Report
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2">
                    <FileText className="w-5 h-5 text-purple-500" />
                    Create Shift Report
                  </DialogTitle>
                  <DialogDescription>
                    Document your shift activities and observations
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleCreateReport} className="space-y-4 mt-4">
                  <div className="space-y-2">
                    <Label>Report Title</Label>
                    <Input 
                      placeholder={`Shift Report - ${new Date().toLocaleDateString()}`}
                      value={newReport.title}
                      onChange={(e) => setNewReport({ ...newReport, title: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Report Content *</Label>
                    <Textarea 
                      placeholder="Overall summary of your shift..." 
                      value={newReport.content}
                      onChange={(e) => setNewReport({ ...newReport, content: e.target.value })}
                      rows={4}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Patient Summary</Label>
                    <Textarea 
                      placeholder="Summary of patient conditions and care provided..."
                      value={newReport.patient_summary}
                      onChange={(e) => setNewReport({ ...newReport, patient_summary: e.target.value })}
                      rows={3}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Critical Events</Label>
                      <Textarea 
                        placeholder="Any critical events or concerns..."
                        value={newReport.critical_events}
                        onChange={(e) => setNewReport({ ...newReport, critical_events: e.target.value })}
                        rows={3}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Pending Items</Label>
                      <Textarea 
                        placeholder="Tasks or items to hand off..."
                        value={newReport.pending_items}
                        onChange={(e) => setNewReport({ ...newReport, pending_items: e.target.value })}
                        rows={3}
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Recommendations</Label>
                    <Textarea 
                      placeholder="Any recommendations for next shift..."
                      value={newReport.recommendations}
                      onChange={(e) => setNewReport({ ...newReport, recommendations: e.target.value })}
                      rows={2}
                    />
                  </div>
                  <DialogFooter>
                    <Button type="button" variant="outline" onClick={() => setReportOpen(false)}>Cancel</Button>
                    <Button type="submit" className="bg-purple-600 hover:bg-purple-700">Save Report</Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </div>
          <CardDescription>
            {!activeShift && <span className="text-amber-600">Clock in to create reports</span>}
            {activeShift && 'Create and manage your shift reports'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[250px]">
            {reports.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                <FileText className="w-10 h-10 mx-auto mb-3 text-slate-300" />
                <p>No reports yet</p>
              </div>
            ) : (
              <div className="space-y-3">
                {reports.map((report) => (
                  <div 
                    key={report.id} 
                    className={`p-3 rounded-lg border ${
                      report.status === 'draft' ? 'border-slate-200' :
                      report.status === 'submitted' ? 'border-amber-200 bg-amber-50' :
                      'border-emerald-200 bg-emerald-50'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <p className="font-medium">{report.title}</p>
                          <Badge className={
                            report.status === 'draft' ? 'bg-slate-100 text-slate-700' :
                            report.status === 'submitted' ? 'bg-amber-100 text-amber-700' :
                            'bg-emerald-100 text-emerald-700'
                          }>
                            {report.status?.toUpperCase()}
                          </Badge>
                        </div>
                        <p className="text-xs text-slate-500 mt-1">
                          {report.shift_type?.toUpperCase()} • {new Date(report.created_at).toLocaleString()}
                        </p>
                        <p className="text-sm text-slate-600 mt-2 line-clamp-2">{report.content}</p>
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
                          <Eye className="w-4 h-4" />
                        </Button>
                        {report.status === 'draft' && (
                          <Button 
                            size="sm"
                            onClick={() => handleSubmitReport(report.id)}
                            className="bg-amber-500 hover:bg-amber-600"
                          >
                            <Send className="w-4 h-4 mr-1" />
                            Submit
                          </Button>
                        )}
                      </div>
                    </div>
                    
                    {report.status === 'reviewed' && report.review_notes && (
                      <div className="mt-3 p-2 bg-emerald-100 rounded text-sm">
                        <p className="font-medium text-emerald-800">Supervisor Review:</p>
                        <p className="text-emerald-700">{report.review_notes}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>

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
                    <p className="text-sm text-gray-500">{selectedReport.shift_type?.toUpperCase()} Shift</p>
                  </div>
                  <Badge className={
                    selectedReport.status === 'draft' ? 'bg-slate-100 text-slate-700' :
                    selectedReport.status === 'submitted' ? 'bg-amber-100 text-amber-700' :
                    'bg-emerald-100 text-emerald-700'
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
                  <div className="p-2 bg-red-50 rounded">
                    <Label className="text-xs text-red-600">Critical Events</Label>
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
                
                <div className="text-sm text-gray-500">
                  Created: {new Date(selectedReport.created_at).toLocaleString()}
                </div>
                
                {selectedReport.review_notes && (
                  <Alert className="bg-emerald-50 border-emerald-200">
                    <FileCheck className="h-4 w-4 text-emerald-600" />
                    <AlertTitle className="text-emerald-800">Supervisor Review</AlertTitle>
                    <AlertDescription className="text-emerald-700">
                      {selectedReport.review_notes}
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            </ScrollArea>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setViewReportOpen(false)}>Close</Button>
            {selectedReport?.status === 'draft' && (
              <Button 
                onClick={() => {
                  handleSubmitReport(selectedReport.id);
                  setViewReportOpen(false);
                }}
                className="bg-amber-500 hover:bg-amber-600"
              >
                <Send className="w-4 h-4 mr-2" />
                Submit for Review
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
