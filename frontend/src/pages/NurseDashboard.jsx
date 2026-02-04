import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import { nurseAPI, vitalsAPI, patientAPI, notificationsAPI } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Progress } from '@/components/ui/progress';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from '@/components/ui/alert';
import { toast } from 'sonner';
import { formatDateTime, calculateAge } from '@/lib/utils';
import { 
  Activity, Pill, AlertTriangle, ClipboardList, CheckCircle2,
  Clock, Heart, Thermometer, User, Plus, Check, X, Bell,
  LogIn, LogOut, Users, ChevronRight, MoreVertical,
  Stethoscope, FileText, AlertCircle, Timer, Shield,
  Droplets, Wind, Gauge, ThermometerSun, Ban, RefreshCw,
  ChevronDown, Eye, ArrowRight, Calendar
} from 'lucide-react';

// Priority color mapping
const priorityColors = {
  stat: 'bg-red-500 text-white',
  urgent: 'bg-orange-500 text-white',
  high: 'bg-amber-500 text-white',
  routine: 'bg-blue-500 text-white',
  low: 'bg-slate-400 text-white'
};

const priorityBorderColors = {
  stat: 'border-l-red-500',
  urgent: 'border-l-orange-500',
  high: 'border-l-amber-500',
  routine: 'border-l-blue-500',
  low: 'border-l-slate-400'
};

// MAR status colors
const marStatusColors = {
  scheduled: 'bg-slate-100 text-slate-700',
  given: 'bg-emerald-100 text-emerald-700',
  held: 'bg-amber-100 text-amber-700',
  refused: 'bg-red-100 text-red-700',
  not_given: 'bg-gray-100 text-gray-700',
  self_administered: 'bg-blue-100 text-blue-700'
};

export default function NurseDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  // State
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [myPatients, setMyPatients] = useState([]);
  const [tasks, setTasks] = useState({ overdue: [], upcoming_30min: [] });
  const [medicationsDue, setMedicationsDue] = useState({ overdue: [], upcoming: [] });
  const [activeShift, setActiveShift] = useState(null);
  const [currentShiftType, setCurrentShiftType] = useState('');
  
  // Dialogs
  const [clockInDialogOpen, setClockInDialogOpen] = useState(false);
  const [clockOutDialogOpen, setClockOutDialogOpen] = useState(false);
  const [vitalsDialogOpen, setVitalsDialogOpen] = useState(false);
  const [marDialogOpen, setMarDialogOpen] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [selectedMAREntry, setSelectedMAREntry] = useState(null);
  const [taskDialogOpen, setTaskDialogOpen] = useState(false);
  
  // Form states
  const [shiftType, setShiftType] = useState('morning');
  const [handoffNotes, setHandoffNotes] = useState('');
  const [newVitals, setNewVitals] = useState({
    blood_pressure_systolic: '', blood_pressure_diastolic: '',
    heart_rate: '', respiratory_rate: '', temperature: '',
    oxygen_saturation: '', pain_level: '', notes: ''
  });
  const [marAction, setMarAction] = useState({
    status: 'given',
    notes: '',
    held_reason: '',
    refused_reason: ''
  });
  const [newTask, setNewTask] = useState({
    patient_id: '',
    task_type: 'vitals_due',
    description: '',
    priority: 'routine',
    due_time: ''
  });

  // Access restriction check
  const isNurse = user?.role === 'nurse';
  
  // Fetch all dashboard data
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      
      const [statsRes, patientsRes, currentShiftRes, dueTasksRes, medsDueRes] = await Promise.all([
        nurseAPI.getDashboardStats(),
        nurseAPI.getMyPatients({ include_vitals: true }),
        nurseAPI.getCurrentShift(),
        nurseAPI.getDueTasks(),
        nurseAPI.getMedicationsDue(60)
      ]);
      
      setStats(statsRes.data);
      setMyPatients(patientsRes.data.patients || []);
      setCurrentShiftType(currentShiftRes.data.current_time_shift);
      setActiveShift(currentShiftRes.data.active_shift);
      setTasks(dueTasksRes.data);
      setMedicationsDue(medsDueRes.data);
      
    } catch (err) {
      console.error('Dashboard fetch error:', err);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    // Auto-refresh every 2 minutes
    const interval = setInterval(fetchData, 120000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // Clock in handler
  const handleClockIn = async () => {
    try {
      await nurseAPI.clockIn({ shift_type: shiftType });
      toast.success('Successfully clocked in');
      setClockInDialogOpen(false);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to clock in');
    }
  };

  // Clock out handler
  const handleClockOut = async () => {
    try {
      await nurseAPI.clockOut(handoffNotes);
      toast.success('Successfully clocked out');
      setClockOutDialogOpen(false);
      setHandoffNotes('');
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to clock out');
    }
  };

  // Record vitals handler
  const handleRecordVitals = async (e) => {
    e.preventDefault();
    if (!selectedPatient) return;
    
    try {
      const data = {
        patient_id: selectedPatient.patient.id,
        ...Object.fromEntries(
          Object.entries(newVitals).filter(([_, v]) => v !== '')
        )
      };
      
      // Convert numeric fields
      ['blood_pressure_systolic', 'blood_pressure_diastolic', 'heart_rate', 
       'respiratory_rate', 'oxygen_saturation', 'pain_level'].forEach(key => {
        if (data[key]) data[key] = parseInt(data[key]);
      });
      if (data.temperature) data.temperature = parseFloat(data.temperature);
      
      await nurseAPI.quickRecordVitals(data);
      toast.success('Vitals recorded successfully');
      setVitalsDialogOpen(false);
      resetVitalsForm();
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to record vitals');
    }
  };

  // Complete task handler
  const handleCompleteTask = async (taskId) => {
    try {
      await nurseAPI.completeTask(taskId);
      toast.success('Task completed');
      fetchData();
    } catch (err) {
      toast.error('Failed to complete task');
    }
  };

  // MAR administration handler
  const handleMARAction = async () => {
    if (!selectedMAREntry) return;
    
    try {
      await nurseAPI.administerMedication({
        mar_entry_id: selectedMAREntry.id,
        status: marAction.status,
        notes: marAction.notes,
        held_reason: marAction.status === 'held' ? marAction.held_reason : null,
        refused_reason: marAction.status === 'refused' ? marAction.refused_reason : null
      });
      toast.success(`Medication marked as ${marAction.status}`);
      setMarDialogOpen(false);
      setSelectedMAREntry(null);
      setMarAction({ status: 'given', notes: '', held_reason: '', refused_reason: '' });
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update medication');
    }
  };

  // Create task handler
  const handleCreateTask = async (e) => {
    e.preventDefault();
    try {
      await nurseAPI.createTask(newTask);
      toast.success('Task created');
      setTaskDialogOpen(false);
      setNewTask({
        patient_id: '',
        task_type: 'vitals_due',
        description: '',
        priority: 'routine',
        due_time: ''
      });
      fetchData();
    } catch (err) {
      toast.error('Failed to create task');
    }
  };

  const resetVitalsForm = () => {
    setNewVitals({
      blood_pressure_systolic: '', blood_pressure_diastolic: '',
      heart_rate: '', respiratory_rate: '', temperature: '',
      oxygen_saturation: '', pain_level: '', notes: ''
    });
  };

  // Calculate shift progress
  const getShiftProgress = () => {
    if (!activeShift) return 0;
    const clockIn = new Date(activeShift.clock_in_time);
    const now = new Date();
    const elapsed = (now - clockIn) / (1000 * 60 * 60); // hours
    const duration = activeShift.shift_type?.includes('12') ? 12 : 8;
    return Math.min(100, (elapsed / duration) * 100);
  };

  // Format time for display
  const formatTime = (isoString) => {
    if (!isoString) return '';
    return new Date(isoString).toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  // Get acuity badge color
  const getAcuityColor = (level) => {
    if (level >= 4) return 'bg-red-100 text-red-700 border-red-200';
    if (level >= 3) return 'bg-amber-100 text-amber-700 border-amber-200';
    return 'bg-emerald-100 text-emerald-700 border-emerald-200';
  };

  if (loading && !stats) {
    return (
      <div className="space-y-6 animate-fade-in p-6">
        <Skeleton className="h-20 w-full" />
        <div className="grid grid-cols-4 gap-4">
          {[1,2,3,4].map(i => <Skeleton key={i} className="h-24" />)}
        </div>
        <div className="grid grid-cols-2 gap-6">
          <Skeleton className="h-96" />
          <Skeleton className="h-96" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="nurse-dashboard">
      {/* Access Restriction Banner for Non-Nurse */}
      {!isNurse && (
        <Alert className="border-amber-200 bg-amber-50">
          <Shield className="h-4 w-4 text-amber-600" />
          <AlertTitle className="text-amber-800">Viewing as {user?.role}</AlertTitle>
          <AlertDescription className="text-amber-700">
            Some nurse-specific features may have different access levels for your role.
          </AlertDescription>
        </Alert>
      )}

      {/* Header with Shift Info */}
      <div className="flex items-center justify-between bg-white rounded-xl p-4 shadow-sm border">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-sky-500 to-sky-600 flex items-center justify-center shadow-lg">
            <Stethoscope className="w-7 h-7 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Manrope' }}>
              Nursing Workstation
            </h1>
            <p className="text-slate-500">
              Welcome, {user?.first_name} • {new Date().toLocaleDateString('en-US', { 
                weekday: 'long', month: 'long', day: 'numeric' 
              })}
            </p>
          </div>
        </div>
        
        {/* Shift Controls */}
        <div className="flex items-center gap-3">
          {activeShift ? (
            <div className="flex items-center gap-4">
              <div className="text-right">
                <div className="flex items-center gap-2 text-emerald-600">
                  <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="font-medium">On Shift</span>
                </div>
                <p className="text-sm text-slate-500">
                  {activeShift.shift_type?.replace('_', ' ').toUpperCase()} • Started {formatTime(activeShift.clock_in_time)}
                </p>
                <div className="mt-1">
                  <Progress value={getShiftProgress()} className="h-1.5 w-32" />
                </div>
              </div>
              <Dialog open={clockOutDialogOpen} onOpenChange={setClockOutDialogOpen}>
                <DialogTrigger asChild>
                  <Button variant="outline" className="gap-2 border-red-200 text-red-600 hover:bg-red-50">
                    <LogOut className="w-4 h-4" />
                    Clock Out
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Clock Out</DialogTitle>
                    <DialogDescription>
                      End your shift and provide handoff notes for the incoming nurse
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 mt-4">
                    <div className="bg-slate-50 p-3 rounded-lg">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-500">Patients assigned:</span>
                        <span className="font-medium">{stats?.patient_count || 0}</span>
                      </div>
                      <div className="flex justify-between text-sm mt-1">
                        <span className="text-slate-500">Tasks pending:</span>
                        <span className="font-medium">{stats?.pending_tasks || 0}</span>
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
                    <Button variant="outline" onClick={() => setClockOutDialogOpen(false)}>
                      Cancel
                    </Button>
                    <Button onClick={handleClockOut} className="bg-red-600 hover:bg-red-700">
                      Clock Out
                    </Button>
                  </DialogFooter>
                </DialogContent>
              </Dialog>
            </div>
          ) : (
            <Dialog open={clockInDialogOpen} onOpenChange={setClockInDialogOpen}>
              <DialogTrigger asChild>
                <Button className="gap-2 bg-emerald-600 hover:bg-emerald-700">
                  <LogIn className="w-4 h-4" />
                  Clock In
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Clock In to Shift</DialogTitle>
                  <DialogDescription>
                    Start your nursing shift
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 mt-4">
                  <div className="space-y-2">
                    <Label>Shift Type</Label>
                    <Select value={shiftType} onValueChange={setShiftType}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="morning">Morning (7AM - 3PM)</SelectItem>
                        <SelectItem value="evening">Evening (3PM - 11PM)</SelectItem>
                        <SelectItem value="night">Night (11PM - 7AM)</SelectItem>
                        <SelectItem value="day_12">12-Hour Day (7AM - 7PM)</SelectItem>
                        <SelectItem value="night_12">12-Hour Night (7PM - 7AM)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="p-3 bg-blue-50 rounded-lg text-sm text-blue-700">
                    <p className="font-medium">Current Time Shift: {currentShiftType?.replace('_', ' ').toUpperCase()}</p>
                  </div>
                </div>
                <DialogFooter className="mt-4">
                  <Button variant="outline" onClick={() => setClockInDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button onClick={handleClockIn} className="bg-emerald-600 hover:bg-emerald-700">
                    Clock In
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          )}
          
          <Button variant="outline" size="icon" onClick={fetchData}>
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <Card className="border-l-4 border-l-emerald-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wide">My Patients</p>
                <p className="text-2xl font-bold text-slate-900">{stats?.patient_count || 0}</p>
              </div>
              <Users className="w-8 h-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="border-l-4 border-l-red-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wide">STAT Tasks</p>
                <p className="text-2xl font-bold text-slate-900">{stats?.stat_tasks || 0}</p>
              </div>
              <AlertCircle className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="border-l-4 border-l-orange-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wide">Urgent Tasks</p>
                <p className="text-2xl font-bold text-slate-900">{stats?.urgent_tasks || 0}</p>
              </div>
              <Timer className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wide">Meds Due</p>
                <p className="text-2xl font-bold text-slate-900">{stats?.medications_due || 0}</p>
              </div>
              <Pill className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="border-l-4 border-l-amber-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wide">Vitals Due</p>
                <p className="text-2xl font-bold text-slate-900">{stats?.vitals_due || 0}</p>
              </div>
              <Heart className="w-8 h-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wide">Notifications</p>
                <p className="text-2xl font-bold text-slate-900">{stats?.unread_notifications || 0}</p>
              </div>
              <Bell className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Access Restrictions Info */}
      {isNurse && (
        <Alert className="border-sky-200 bg-sky-50">
          <Shield className="h-4 w-4 text-sky-600" />
          <AlertTitle className="text-sky-800">Role-Based Access</AlertTitle>
          <AlertDescription className="text-sky-700">
            As a nurse, you can view and administer medications, record vitals, and update order status. 
            You cannot prescribe medications or create orders. Contact a physician for prescription needs.
          </AlertDescription>
        </Alert>
      )}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* My Patients Panel */}
        <Card className="lg:col-span-1">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Users className="w-5 h-5 text-emerald-500" />
                My Patients
              </CardTitle>
              <Badge variant="secondary">{myPatients.length}</Badge>
            </div>
            <CardDescription>Assigned patients for your shift</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[500px] pr-4">
              {myPatients.length === 0 ? (
                <div className="text-center py-12 text-slate-500">
                  <Users className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                  <p>No patients assigned</p>
                  <p className="text-sm">Clock in to receive patient assignments</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {myPatients.map((item) => (
                    <div
                      key={item.patient.id}
                      className="p-3 rounded-lg border border-slate-200 hover:border-sky-200 hover:bg-sky-50/50 transition-all cursor-pointer"
                      onClick={() => navigate(`/patients/${item.patient.id}`)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center">
                            <User className="w-5 h-5 text-slate-500" />
                          </div>
                          <div>
                            <p className="font-medium text-slate-900">
                              {item.patient.first_name} {item.patient.last_name}
                            </p>
                            <p className="text-xs text-slate-500">
                              MRN: {item.patient.mrn}
                            </p>
                          </div>
                        </div>
                        <Badge className={getAcuityColor(item.acuity_level)}>
                          Acuity {item.acuity_level}
                        </Badge>
                      </div>
                      
                      {/* Quick Stats */}
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
                            <AlertTriangle className="w-3 h-3" />
                            No vitals recorded
                          </span>
                        )}
                      </div>
                      
                      {/* Action Buttons */}
                      <div className="flex items-center gap-2 mt-3">
                        <Button 
                          size="sm" 
                          variant="outline" 
                          className="h-7 text-xs flex-1"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedPatient(item);
                            setVitalsDialogOpen(true);
                          }}
                        >
                          <Heart className="w-3 h-3 mr-1" />
                          Vitals
                        </Button>
                        <Button 
                          size="sm" 
                          variant="outline" 
                          className="h-7 text-xs flex-1"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/patients/${item.patient.id}?tab=medications`);
                          }}
                        >
                          <Pill className="w-3 h-3 mr-1" />
                          MAR
                        </Button>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button size="sm" variant="ghost" className="h-7 w-7 p-0" onClick={(e) => e.stopPropagation()}>
                              <MoreVertical className="w-4 h-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => navigate(`/patients/${item.patient.id}`)}>
                              <Eye className="w-4 h-4 mr-2" />
                              View Chart
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => {
                              setNewTask({ ...newTask, patient_id: item.patient.id });
                              setTaskDialogOpen(true);
                            }}>
                              <Plus className="w-4 h-4 mr-2" />
                              Add Task
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem className="text-slate-500">
                              <FileText className="w-4 h-4 mr-2" />
                              View Notes
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                      
                      {/* Task/Med Indicators */}
                      {(item.pending_tasks_count > 0 || item.active_medications_count > 0) && (
                        <div className="flex items-center gap-2 mt-2 pt-2 border-t border-slate-100">
                          {item.pending_tasks_count > 0 && (
                            <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">
                              {item.pending_tasks_count} tasks
                            </span>
                          )}
                          {item.active_medications_count > 0 && (
                            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                              {item.active_medications_count} active meds
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Tasks & MAR Panel */}
        <Card className="lg:col-span-2">
          <Tabs defaultValue="tasks" className="h-full">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <TabsList>
                  <TabsTrigger value="tasks" className="gap-2">
                    <ClipboardList className="w-4 h-4" />
                    Tasks
                    {(tasks.overdue?.length > 0 || tasks.upcoming_30min?.length > 0) && (
                      <Badge variant="destructive" className="ml-1 h-5 w-5 p-0 flex items-center justify-center text-xs">
                        {(tasks.overdue?.length || 0) + (tasks.upcoming_30min?.length || 0)}
                      </Badge>
                    )}
                  </TabsTrigger>
                  <TabsTrigger value="medications" className="gap-2">
                    <Pill className="w-4 h-4" />
                    Medications Due
                    {(medicationsDue.overdue?.length > 0) && (
                      <Badge variant="destructive" className="ml-1 h-5 w-5 p-0 flex items-center justify-center text-xs">
                        {medicationsDue.overdue?.length || 0}
                      </Badge>
                    )}
                  </TabsTrigger>
                </TabsList>
                <Dialog open={taskDialogOpen} onOpenChange={setTaskDialogOpen}>
                  <DialogTrigger asChild>
                    <Button size="sm" variant="outline" className="gap-1">
                      <Plus className="w-4 h-4" />
                      Add Task
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Create New Task</DialogTitle>
                    </DialogHeader>
                    <form onSubmit={handleCreateTask} className="space-y-4 mt-4">
                      <div className="space-y-2">
                        <Label>Patient</Label>
                        <Select 
                          value={newTask.patient_id} 
                          onValueChange={(v) => setNewTask({...newTask, patient_id: v})}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select patient" />
                          </SelectTrigger>
                          <SelectContent>
                            {myPatients.map(p => (
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
                            onValueChange={(v) => setNewTask({...newTask, task_type: v})}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="vitals_due">Vitals Due</SelectItem>
                              <SelectItem value="medication_due">Medication Due</SelectItem>
                              <SelectItem value="assessment_due">Assessment Due</SelectItem>
                              <SelectItem value="wound_care">Wound Care</SelectItem>
                              <SelectItem value="iv_check">IV Check</SelectItem>
                              <SelectItem value="pain_assessment">Pain Assessment</SelectItem>
                              <SelectItem value="intake_output">Intake/Output</SelectItem>
                              <SelectItem value="custom">Custom</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <Label>Priority</Label>
                          <Select 
                            value={newTask.priority} 
                            onValueChange={(v) => setNewTask({...newTask, priority: v})}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="stat">STAT (Immediate)</SelectItem>
                              <SelectItem value="urgent">Urgent (30 min)</SelectItem>
                              <SelectItem value="high">High (1 hour)</SelectItem>
                              <SelectItem value="routine">Routine</SelectItem>
                              <SelectItem value="low">Low</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label>Description</Label>
                        <Textarea
                          placeholder="Task details..."
                          value={newTask.description}
                          onChange={(e) => setNewTask({...newTask, description: e.target.value})}
                          required
                        />
                      </div>
                      <DialogFooter>
                        <Button type="submit">Create Task</Button>
                      </DialogFooter>
                    </form>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent>
              <TabsContent value="tasks" className="mt-0">
                <ScrollArea className="h-[450px] pr-4">
                  {/* Overdue Tasks */}
                  {tasks.overdue?.length > 0 && (
                    <div className="mb-4">
                      <h4 className="text-sm font-medium text-red-600 mb-2 flex items-center gap-2">
                        <AlertCircle className="w-4 h-4" />
                        Overdue ({tasks.overdue.length})
                      </h4>
                      <div className="space-y-2">
                        {tasks.overdue.map((task) => (
                          <TaskCard 
                            key={task.id} 
                            task={task} 
                            onComplete={() => handleCompleteTask(task.id)}
                            isOverdue 
                          />
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Upcoming Tasks */}
                  {tasks.upcoming_30min?.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-amber-600 mb-2 flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        Due Soon ({tasks.upcoming_30min.length})
                      </h4>
                      <div className="space-y-2">
                        {tasks.upcoming_30min.map((task) => (
                          <TaskCard 
                            key={task.id} 
                            task={task} 
                            onComplete={() => handleCompleteTask(task.id)}
                          />
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {(!tasks.overdue?.length && !tasks.upcoming_30min?.length) && (
                    <div className="text-center py-12 text-slate-500">
                      <CheckCircle2 className="w-12 h-12 mx-auto mb-3 text-emerald-300" />
                      <p className="font-medium text-emerald-600">All caught up!</p>
                      <p className="text-sm">No pending tasks</p>
                    </div>
                  )}
                </ScrollArea>
              </TabsContent>
              
              <TabsContent value="medications" className="mt-0">
                <ScrollArea className="h-[450px] pr-4">
                  {/* Overdue Medications */}
                  {medicationsDue.overdue?.length > 0 && (
                    <div className="mb-4">
                      <h4 className="text-sm font-medium text-red-600 mb-2 flex items-center gap-2">
                        <AlertCircle className="w-4 h-4" />
                        Overdue ({medicationsDue.overdue.length})
                      </h4>
                      <div className="space-y-2">
                        {medicationsDue.overdue.map((entry) => (
                          <MedicationCard 
                            key={entry.id} 
                            entry={entry}
                            isOverdue
                            onAction={() => {
                              setSelectedMAREntry(entry);
                              setMarDialogOpen(true);
                            }}
                          />
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {/* Upcoming Medications */}
                  {medicationsDue.upcoming?.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-blue-600 mb-2 flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        Upcoming ({medicationsDue.upcoming.length})
                      </h4>
                      <div className="space-y-2">
                        {medicationsDue.upcoming.map((entry) => (
                          <MedicationCard 
                            key={entry.id} 
                            entry={entry}
                            onAction={() => {
                              setSelectedMAREntry(entry);
                              setMarDialogOpen(true);
                            }}
                          />
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {(!medicationsDue.overdue?.length && !medicationsDue.upcoming?.length) && (
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

      {/* Vitals Recording Dialog */}
      <Dialog open={vitalsDialogOpen} onOpenChange={setVitalsDialogOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Heart className="w-5 h-5 text-red-500" />
              Record Vitals
            </DialogTitle>
            <DialogDescription>
              {selectedPatient && `${selectedPatient.patient.first_name} ${selectedPatient.patient.last_name}`}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleRecordVitals} className="space-y-4 mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="flex items-center gap-1">
                  <Gauge className="w-3 h-3" /> Systolic BP
                </Label>
                <Input 
                  type="number" 
                  placeholder="120"
                  value={newVitals.blood_pressure_systolic} 
                  onChange={(e) => setNewVitals({ ...newVitals, blood_pressure_systolic: e.target.value })} 
                />
              </div>
              <div className="space-y-2">
                <Label className="flex items-center gap-1">
                  <Gauge className="w-3 h-3" /> Diastolic BP
                </Label>
                <Input 
                  type="number" 
                  placeholder="80"
                  value={newVitals.blood_pressure_diastolic} 
                  onChange={(e) => setNewVitals({ ...newVitals, blood_pressure_diastolic: e.target.value })} 
                />
              </div>
              <div className="space-y-2">
                <Label className="flex items-center gap-1">
                  <Heart className="w-3 h-3" /> Heart Rate
                </Label>
                <Input 
                  type="number" 
                  placeholder="72"
                  value={newVitals.heart_rate} 
                  onChange={(e) => setNewVitals({ ...newVitals, heart_rate: e.target.value })} 
                />
              </div>
              <div className="space-y-2">
                <Label className="flex items-center gap-1">
                  <ThermometerSun className="w-3 h-3" /> Temperature (°F)
                </Label>
                <Input 
                  type="number" 
                  step="0.1"
                  placeholder="98.6"
                  value={newVitals.temperature} 
                  onChange={(e) => setNewVitals({ ...newVitals, temperature: e.target.value })} 
                />
              </div>
              <div className="space-y-2">
                <Label className="flex items-center gap-1">
                  <Droplets className="w-3 h-3" /> SpO2 (%)
                </Label>
                <Input 
                  type="number" 
                  placeholder="98"
                  value={newVitals.oxygen_saturation} 
                  onChange={(e) => setNewVitals({ ...newVitals, oxygen_saturation: e.target.value })} 
                />
              </div>
              <div className="space-y-2">
                <Label className="flex items-center gap-1">
                  <Wind className="w-3 h-3" /> Resp Rate
                </Label>
                <Input 
                  type="number" 
                  placeholder="16"
                  value={newVitals.respiratory_rate} 
                  onChange={(e) => setNewVitals({ ...newVitals, respiratory_rate: e.target.value })} 
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
                value={newVitals.pain_level} 
                onChange={(e) => setNewVitals({ ...newVitals, pain_level: e.target.value })} 
              />
            </div>
            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea
                placeholder="Additional observations..."
                value={newVitals.notes}
                onChange={(e) => setNewVitals({ ...newVitals, notes: e.target.value })}
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setVitalsDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" className="bg-sky-600 hover:bg-sky-700">
                Save Vitals
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* MAR Action Dialog */}
      <Dialog open={marDialogOpen} onOpenChange={setMarDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Pill className="w-5 h-5 text-blue-500" />
              Medication Administration
            </DialogTitle>
            <DialogDescription>
              {selectedMAREntry && selectedMAREntry.medication_name}
            </DialogDescription>
          </DialogHeader>
          {selectedMAREntry && (
            <div className="space-y-4 mt-4">
              <div className="bg-slate-50 p-3 rounded-lg space-y-1">
                <p><span className="text-slate-500">Dosage:</span> {selectedMAREntry.dosage}</p>
                <p><span className="text-slate-500">Route:</span> {selectedMAREntry.route}</p>
                <p><span className="text-slate-500">Scheduled:</span> {formatTime(selectedMAREntry.scheduled_time)}</p>
              </div>
              
              <div className="space-y-2">
                <Label>Action</Label>
                <Select value={marAction.status} onValueChange={(v) => setMarAction({...marAction, status: v})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="given">Given</SelectItem>
                    <SelectItem value="held">Held</SelectItem>
                    <SelectItem value="refused">Refused</SelectItem>
                    <SelectItem value="self_administered">Self-Administered</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              {marAction.status === 'held' && (
                <div className="space-y-2">
                  <Label>Held Reason</Label>
                  <Select value={marAction.held_reason} onValueChange={(v) => setMarAction({...marAction, held_reason: v})}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select reason" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="NPO">NPO (Nothing by Mouth)</SelectItem>
                      <SelectItem value="vital_signs">Abnormal Vital Signs</SelectItem>
                      <SelectItem value="lab_values">Abnormal Lab Values</SelectItem>
                      <SelectItem value="physician_order">Physician Order</SelectItem>
                      <SelectItem value="patient_sleeping">Patient Sleeping</SelectItem>
                      <SelectItem value="other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}
              
              {marAction.status === 'refused' && (
                <div className="space-y-2">
                  <Label>Refused Reason</Label>
                  <Textarea
                    placeholder="Document patient's reason for refusing..."
                    value={marAction.refused_reason}
                    onChange={(e) => setMarAction({...marAction, refused_reason: e.target.value})}
                  />
                </div>
              )}
              
              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea
                  placeholder="Additional notes..."
                  value={marAction.notes}
                  onChange={(e) => setMarAction({...marAction, notes: e.target.value})}
                />
              </div>
            </div>
          )}
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setMarDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleMARAction} className="bg-blue-600 hover:bg-blue-700">
              Confirm
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// Task Card Component
function TaskCard({ task, onComplete, isOverdue }) {
  return (
    <div className={`p-3 rounded-lg border ${isOverdue ? 'border-red-200 bg-red-50' : 'border-slate-200'} ${priorityBorderColors[task.priority]} border-l-4`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <Badge className={priorityColors[task.priority]} size="sm">
              {task.priority?.toUpperCase()}
            </Badge>
            <span className="text-sm font-medium text-slate-900">{task.task_type?.replace('_', ' ').toUpperCase()}</span>
          </div>
          <p className="text-sm text-slate-600 mt-1">{task.description}</p>
          <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
            <span className="flex items-center gap-1">
              <User className="w-3 h-3" />
              {task.patient_name}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              Due: {new Date(task.due_time).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>
        </div>
        <Button size="sm" variant="outline" className="h-8" onClick={onComplete}>
          <Check className="w-4 h-4 mr-1" />
          Done
        </Button>
      </div>
    </div>
  );
}

// Medication Card Component
function MedicationCard({ entry, isOverdue, onAction }) {
  return (
    <div className={`p-3 rounded-lg border ${isOverdue ? 'border-red-200 bg-red-50' : 'border-slate-200'}`}>
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
              <Clock className="w-3 h-3" />
              {new Date(entry.scheduled_time).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
            </span>
            <Badge className={marStatusColors[entry.status]}>
              {entry.status?.toUpperCase()}
            </Badge>
          </div>
        </div>
        <Button size="sm" onClick={onAction} className="bg-blue-600 hover:bg-blue-700">
          <Pill className="w-4 h-4 mr-1" />
          Admin
        </Button>
      </div>
    </div>
  );
}
