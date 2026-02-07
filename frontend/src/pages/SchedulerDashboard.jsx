import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/lib/auth';
import { appointmentsAPI, patientAPI, usersAPI } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
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
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import { formatTime, getStatusColor, calculateAge, formatDate } from '@/lib/utils';
import { 
  Calendar, Plus, Clock, User, ChevronLeft, ChevronRight, 
  UserPlus, CheckCircle, XCircle, Users, CalendarDays, Eye,
  Phone, Mail, MapPin, Shield, AlertCircle, LogIn, LogOut, Search
} from 'lucide-react';

export default function SchedulerDashboard() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [appointments, setAppointments] = useState([]);
  const [patients, setPatients] = useState([]);
  const [providers, setProviders] = useState([]);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [patientDialogOpen, setPatientDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  
  const [newAppointment, setNewAppointment] = useState({
    patient_id: '', provider_id: '', appointment_type: 'follow_up',
    date: '', start_time: '', end_time: '', reason: '', notes: ''
  });
  
  const [newPatient, setNewPatient] = useState({
    first_name: '', last_name: '', date_of_birth: '', gender: 'male',
    email: '', phone: '', insurance_provider: '', insurance_id: ''
  });

  const fetchData = useCallback(async () => {
    try {
      const [apptsRes, patientsRes, usersRes] = await Promise.all([
        appointmentsAPI.getAll({ date: selectedDate }),
        patientAPI.getAll(),
        usersAPI.getAll()
      ]);
      
      setAppointments(apptsRes.data);
      setPatients(patientsRes.data);
      setProviders(usersRes.data.filter(u => u.role === 'physician'));
    } catch (err) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [selectedDate]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCreateAppointment = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await appointmentsAPI.create(newAppointment);
      toast.success('Appointment scheduled');
      setDialogOpen(false);
      setNewAppointment({
        patient_id: '', provider_id: '', appointment_type: 'follow_up',
        date: '', start_time: '', end_time: '', reason: '', notes: ''
      });
      fetchData();
    } catch (err) {
      toast.error('Failed to schedule appointment');
    } finally {
      setSaving(false);
    }
  };

  const handleCreatePatient = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await patientAPI.create(newPatient);
      toast.success('Patient registered');
      setPatientDialogOpen(false);
      setNewPatient({
        first_name: '', last_name: '', date_of_birth: '', gender: 'male',
        email: '', phone: '', insurance_provider: '', insurance_id: ''
      });
      fetchData();
    } catch (err) {
      toast.error('Failed to register patient');
    } finally {
      setSaving(false);
    }
  };

  const handleStatusChange = async (apptId, newStatus) => {
    try {
      await appointmentsAPI.updateStatus(apptId, newStatus);
      toast.success('Status updated');
      fetchData();
    } catch (err) {
      toast.error('Failed to update status');
    }
  };

  const changeDate = (days) => {
    const date = new Date(selectedDate);
    date.setDate(date.getDate() + days);
    setSelectedDate(date.toISOString().split('T')[0]);
  };

  const getPatientName = (patientId) => {
    const patient = patients.find(p => p.id === patientId);
    return patient ? patient.first_name + ' ' + patient.last_name : 'Unknown';
  };

  const getProviderName = (providerId) => {
    const provider = providers.find(p => p.id === providerId);
    return provider ? 'Dr. ' + provider.first_name + ' ' + provider.last_name : 'Unknown';
  };

  // Time slots for the calendar view
  const timeSlots = ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00'];
  
  const stats = {
    scheduled: appointments.filter(a => a.status === 'scheduled').length,
    checkedIn: appointments.filter(a => a.status === 'checked_in').length,
    completed: appointments.filter(a => a.status === 'completed').length,
    cancelled: appointments.filter(a => a.status === 'cancelled').length
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="scheduler-dashboard">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900" style={{ fontFamily: 'Manrope' }}>
            Scheduling Center
          </h1>
          <p className="text-slate-500 mt-1">
            Welcome, {user?.first_name} • Manage appointments and patient registration
          </p>
        </div>
        <div className="flex gap-2">
          <Dialog open={patientDialogOpen} onOpenChange={setPatientDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" className="gap-2">
                <UserPlus className="w-4 h-4" /> Register Patient
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Register New Patient</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleCreatePatient} className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>First Name *</Label>
                    <Input value={newPatient.first_name} onChange={(e) => setNewPatient({ ...newPatient, first_name: e.target.value })} required />
                  </div>
                  <div className="space-y-2">
                    <Label>Last Name *</Label>
                    <Input value={newPatient.last_name} onChange={(e) => setNewPatient({ ...newPatient, last_name: e.target.value })} required />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Date of Birth *</Label>
                    <Input type="date" value={newPatient.date_of_birth} onChange={(e) => setNewPatient({ ...newPatient, date_of_birth: e.target.value })} required />
                  </div>
                  <div className="space-y-2">
                    <Label>Gender *</Label>
                    <Select value={newPatient.gender} onValueChange={(v) => setNewPatient({ ...newPatient, gender: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="male">Male</SelectItem>
                        <SelectItem value="female">Female</SelectItem>
                        <SelectItem value="other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Phone</Label>
                    <Input value={newPatient.phone} onChange={(e) => setNewPatient({ ...newPatient, phone: e.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label>Email</Label>
                    <Input type="email" value={newPatient.email} onChange={(e) => setNewPatient({ ...newPatient, email: e.target.value })} />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Insurance Provider</Label>
                    <Input value={newPatient.insurance_provider} onChange={(e) => setNewPatient({ ...newPatient, insurance_provider: e.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label>Insurance ID</Label>
                    <Input value={newPatient.insurance_id} onChange={(e) => setNewPatient({ ...newPatient, insurance_id: e.target.value })} />
                  </div>
                </div>
                <Button type="submit" className="w-full" disabled={saving}>
                  {saving ? 'Registering...' : 'Register Patient'}
                </Button>
              </form>
            </DialogContent>
          </Dialog>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2 bg-sky-600 hover:bg-sky-700">
                <Plus className="w-4 h-4" /> New Appointment
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Schedule Appointment</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleCreateAppointment} className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label>Patient *</Label>
                  <Select value={newAppointment.patient_id} onValueChange={(v) => setNewAppointment({ ...newAppointment, patient_id: v })}>
                    <SelectTrigger><SelectValue placeholder="Select patient" /></SelectTrigger>
                    <SelectContent>
                      {patients.map((p) => (
                        <SelectItem key={p.id} value={p.id}>{p.first_name} {p.last_name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Provider *</Label>
                  <Select value={newAppointment.provider_id} onValueChange={(v) => setNewAppointment({ ...newAppointment, provider_id: v })}>
                    <SelectTrigger><SelectValue placeholder="Select provider" /></SelectTrigger>
                    <SelectContent>
                      {providers.map((p) => (
                        <SelectItem key={p.id} value={p.id}>Dr. {p.first_name} {p.last_name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Type</Label>
                  <Select value={newAppointment.appointment_type} onValueChange={(v) => setNewAppointment({ ...newAppointment, appointment_type: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="new_patient">New Patient</SelectItem>
                      <SelectItem value="follow_up">Follow Up</SelectItem>
                      <SelectItem value="procedure">Procedure</SelectItem>
                      <SelectItem value="consultation">Consultation</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div className="space-y-2">
                    <Label>Date *</Label>
                    <Input type="date" value={newAppointment.date} onChange={(e) => setNewAppointment({ ...newAppointment, date: e.target.value })} required />
                  </div>
                  <div className="space-y-2">
                    <Label>Start *</Label>
                    <Input type="time" value={newAppointment.start_time} onChange={(e) => setNewAppointment({ ...newAppointment, start_time: e.target.value })} required />
                  </div>
                  <div className="space-y-2">
                    <Label>End *</Label>
                    <Input type="time" value={newAppointment.end_time} onChange={(e) => setNewAppointment({ ...newAppointment, end_time: e.target.value })} required />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Reason</Label>
                  <Input value={newAppointment.reason} onChange={(e) => setNewAppointment({ ...newAppointment, reason: e.target.value })} />
                </div>
                <Button type="submit" className="w-full" disabled={saving}>
                  {saving ? 'Scheduling...' : 'Schedule Appointment'}
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-amber-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Scheduled</p>
                <p className="text-2xl font-bold text-slate-900">{stats.scheduled}</p>
              </div>
              <Calendar className="w-8 h-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Checked In</p>
                <p className="text-2xl font-bold text-slate-900">{stats.checkedIn}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-emerald-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Completed</p>
                <p className="text-2xl font-bold text-slate-900">{stats.completed}</p>
              </div>
              <CheckCircle className="w-8 h-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-slate-400">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Cancelled/No Show</p>
                <p className="text-2xl font-bold text-slate-900">{stats.cancelled}</p>
              </div>
              <XCircle className="w-8 h-8 text-slate-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Date Navigation and Schedule */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="icon" onClick={() => changeDate(-1)}>
                <ChevronLeft className="w-5 h-5" />
              </Button>
              <div className="flex items-center gap-2">
                <CalendarDays className="w-5 h-5 text-sky-600" />
                <span className="text-lg font-semibold">
                  {new Date(selectedDate).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
                </span>
              </div>
              <Button variant="ghost" size="icon" onClick={() => changeDate(1)}>
                <ChevronRight className="w-5 h-5" />
              </Button>
            </div>
            <Input 
              type="date" 
              value={selectedDate} 
              onChange={(e) => setSelectedDate(e.target.value)}
              className="w-40"
            />
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
            </div>
          ) : appointments.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              <Calendar className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium">No appointments scheduled</p>
              <p className="text-sm">Click "New Appointment" to schedule one</p>
            </div>
          ) : (
            <ScrollArea className="h-[400px]">
              <div className="space-y-3">
                {appointments.map((appt) => (
                  <div 
                    key={appt.id} 
                    className="flex items-center justify-between p-4 rounded-lg border border-slate-200 hover:border-sky-200 transition-colors"
                  >
                    <div className="flex gap-4">
                      <div className="text-center min-w-[80px]">
                        <p className="text-lg font-bold text-sky-600">{formatTime(appt.start_time)}</p>
                        <p className="text-xs text-slate-400">to {formatTime(appt.end_time)}</p>
                      </div>
                      <div>
                        <p className="font-medium text-slate-900">{getPatientName(appt.patient_id)}</p>
                        <p className="text-sm text-slate-500">{getProviderName(appt.provider_id)}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge variant="outline" className="text-xs capitalize">{appt.appointment_type.replace('_', ' ')}</Badge>
                          {appt.reason && <span className="text-xs text-slate-500">{appt.reason}</span>}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge className={getStatusColor(appt.status)}>{appt.status.replace('_', ' ')}</Badge>
                      <Select onValueChange={(v) => handleStatusChange(appt.id, v)}>
                        <SelectTrigger className="w-[120px] h-8 text-sm">
                          <SelectValue placeholder="Update" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="scheduled">Scheduled</SelectItem>
                          <SelectItem value="checked_in">Check In</SelectItem>
                          <SelectItem value="in_progress">In Progress</SelectItem>
                          <SelectItem value="completed">Complete</SelectItem>
                          <SelectItem value="cancelled">Cancel</SelectItem>
                          <SelectItem value="no_show">No Show</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>

      {/* Patient List Quick View */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="w-5 h-5" /> Recent Patients
          </CardTitle>
          <CardDescription>Quick access to patient records</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {patients.slice(0, 10).map((patient) => (
              <div 
                key={patient.id}
                className="p-3 rounded-lg border border-slate-200 hover:border-sky-200 cursor-pointer transition-colors"
              >
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-sky-100 text-sky-700 flex items-center justify-center text-sm font-semibold">
                    {patient.first_name?.[0]}{patient.last_name?.[0]}
                  </div>
                  <div className="overflow-hidden">
                    <p className="font-medium text-sm text-slate-900 truncate">{patient.first_name} {patient.last_name}</p>
                    <p className="text-xs text-slate-500">{patient.mrn}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
