import { useState, useEffect } from 'react';
import { appointmentsAPI, patientAPI, usersAPI } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
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
import { formatDate, formatTime, getStatusColor } from '@/lib/utils';
import { Calendar, Plus, Clock, User, ChevronLeft, ChevronRight, Check } from 'lucide-react';

export default function Appointments() {
  const [appointments, setAppointments] = useState([]);
  const [patients, setPatients] = useState([]);
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  
  const [newAppointment, setNewAppointment] = useState({
    patient_id: '', provider_id: '', appointment_type: 'follow_up',
    date: '', start_time: '', end_time: '', reason: '', notes: ''
  });

  useEffect(() => {
    fetchData();
  }, [selectedDate]);

  const fetchData = async () => {
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
      toast.error('Failed to load appointments');
    } finally {
      setLoading(false);
    }
  };

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
      toast.error('Failed to create appointment');
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
    return patient ? `${patient.first_name} ${patient.last_name}` : 'Unknown';
  };

  const getProviderName = (providerId) => {
    const provider = providers.find(p => p.id === providerId);
    return provider ? `Dr. ${provider.first_name} ${provider.last_name}` : 'Unknown';
  };

  // Group appointments by time slots
  const timeSlots = ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00'];

  return (
    <div className="space-y-6 animate-fade-in" data-testid="appointments-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900" style={{ fontFamily: 'Manrope' }}>
            Appointments
          </h1>
          <p className="text-slate-500 mt-1">Schedule and manage patient appointments</p>
        </div>
        
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="gap-2 bg-sky-600 hover:bg-sky-700" data-testid="schedule-appointment-btn">
              <Plus className="w-4 h-4" /> Schedule Appointment
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle style={{ fontFamily: 'Manrope' }}>Schedule New Appointment</DialogTitle>
              <DialogDescription>
                Book a new appointment for a patient
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreateAppointment} className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label>Patient *</Label>
                <Select 
                  value={newAppointment.patient_id} 
                  onValueChange={(v) => setNewAppointment({ ...newAppointment, patient_id: v })}
                >
                  <SelectTrigger data-testid="appt-patient">
                    <SelectValue placeholder="Select patient" />
                  </SelectTrigger>
                  <SelectContent>
                    {patients.map((p) => (
                      <SelectItem key={p.id} value={p.id}>
                        {p.first_name} {p.last_name} ({p.mrn})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Provider *</Label>
                <Select 
                  value={newAppointment.provider_id} 
                  onValueChange={(v) => setNewAppointment({ ...newAppointment, provider_id: v })}
                >
                  <SelectTrigger data-testid="appt-provider">
                    <SelectValue placeholder="Select provider" />
                  </SelectTrigger>
                  <SelectContent>
                    {providers.map((p) => (
                      <SelectItem key={p.id} value={p.id}>
                        Dr. {p.first_name} {p.last_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Appointment Type *</Label>
                <Select 
                  value={newAppointment.appointment_type} 
                  onValueChange={(v) => setNewAppointment({ ...newAppointment, appointment_type: v })}
                >
                  <SelectTrigger data-testid="appt-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="new_patient">New Patient</SelectItem>
                    <SelectItem value="follow_up">Follow Up</SelectItem>
                    <SelectItem value="procedure">Procedure</SelectItem>
                    <SelectItem value="consultation">Consultation</SelectItem>
                    <SelectItem value="urgent">Urgent Visit</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-2">
                  <Label>Date *</Label>
                  <Input 
                    type="date" 
                    value={newAppointment.date} 
                    onChange={(e) => setNewAppointment({ ...newAppointment, date: e.target.value })}
                    required
                    data-testid="appt-date"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Start Time *</Label>
                  <Input 
                    type="time" 
                    value={newAppointment.start_time} 
                    onChange={(e) => setNewAppointment({ ...newAppointment, start_time: e.target.value })}
                    required
                    data-testid="appt-start-time"
                  />
                </div>
                <div className="space-y-2">
                  <Label>End Time *</Label>
                  <Input 
                    type="time" 
                    value={newAppointment.end_time} 
                    onChange={(e) => setNewAppointment({ ...newAppointment, end_time: e.target.value })}
                    required
                    data-testid="appt-end-time"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Reason for Visit</Label>
                <Input 
                  value={newAppointment.reason} 
                  onChange={(e) => setNewAppointment({ ...newAppointment, reason: e.target.value })}
                  placeholder="Brief reason for appointment"
                  data-testid="appt-reason"
                />
              </div>
              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea 
                  value={newAppointment.notes} 
                  onChange={(e) => setNewAppointment({ ...newAppointment, notes: e.target.value })}
                  placeholder="Additional notes..."
                  data-testid="appt-notes"
                />
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t">
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={saving} data-testid="save-appointment-btn">
                  {saving ? 'Scheduling...' : 'Schedule'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Date Navigation */}
      <Card>
        <CardContent className="py-4">
          <div className="flex items-center justify-between">
            <Button variant="ghost" size="icon" onClick={() => changeDate(-1)} data-testid="prev-day">
              <ChevronLeft className="w-5 h-5" />
            </Button>
            <div className="flex items-center gap-4">
              <Calendar className="w-5 h-5 text-sky-600" />
              <div className="text-center">
                <p className="text-lg font-semibold text-slate-900" style={{ fontFamily: 'Manrope' }}>
                  {new Date(selectedDate).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
                </p>
                <p className="text-sm text-slate-500">{appointments.length} appointments scheduled</p>
              </div>
              <Input 
                type="date" 
                value={selectedDate} 
                onChange={(e) => setSelectedDate(e.target.value)}
                className="w-40"
                data-testid="date-picker"
              />
            </div>
            <Button variant="ghost" size="icon" onClick={() => changeDate(1)} data-testid="next-day">
              <ChevronRight className="w-5 h-5" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Appointments List */}
      <Card>
        <CardHeader>
          <CardTitle style={{ fontFamily: 'Manrope' }}>Schedule</CardTitle>
          <CardDescription>Click on an appointment to manage its status</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4].map(i => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </div>
          ) : appointments.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              <Calendar className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg font-medium">No appointments for this day</p>
              <p className="text-sm">Schedule a new appointment to get started</p>
            </div>
          ) : (
            <div className="space-y-3">
              {appointments.map((appt) => (
                <div 
                  key={appt.id} 
                  className="p-4 rounded-lg border border-slate-200 hover:border-sky-200 hover:shadow-sm transition-all"
                  data-testid={`appointment-card-${appt.id}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex gap-4">
                      <div className="w-16 text-center">
                        <p className="text-lg font-bold text-sky-600">{formatTime(appt.start_time)}</p>
                        <p className="text-xs text-slate-400">to {formatTime(appt.end_time)}</p>
                      </div>
                      <div>
                        <p className="font-medium text-slate-900">{getPatientName(appt.patient_id)}</p>
                        <p className="text-sm text-slate-500">{getProviderName(appt.provider_id)}</p>
                        <div className="flex items-center gap-2 mt-2">
                          <Badge variant="outline" className="capitalize">{appt.appointment_type.replace('_', ' ')}</Badge>
                          {appt.reason && <span className="text-sm text-slate-600">{appt.reason}</span>}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className={getStatusColor(appt.status)}>{appt.status.replace('_', ' ')}</Badge>
                      <Select onValueChange={(v) => handleStatusChange(appt.id, v)}>
                        <SelectTrigger className="w-[130px]" data-testid={`status-select-${appt.id}`}>
                          <SelectValue placeholder="Update" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="scheduled">Scheduled</SelectItem>
                          <SelectItem value="checked_in">Checked In</SelectItem>
                          <SelectItem value="in_progress">In Progress</SelectItem>
                          <SelectItem value="completed">Completed</SelectItem>
                          <SelectItem value="cancelled">Cancelled</SelectItem>
                          <SelectItem value="no_show">No Show</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
