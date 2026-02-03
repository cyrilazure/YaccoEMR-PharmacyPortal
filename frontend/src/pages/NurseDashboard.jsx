import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import { patientAPI, vitalsAPI, medicationsAPI, ordersAPI } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { toast } from 'sonner';
import { formatDateTime, calculateAge, getStatusColor } from '@/lib/utils';
import { 
  Activity, Pill, AlertTriangle, ClipboardList, CheckCircle2,
  Clock, Heart, Thermometer, User, Plus, Check
} from 'lucide-react';

export default function NurseDashboard() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [patients, setPatients] = useState([]);
  const [pendingMeds, setPendingMeds] = useState([]);
  const [pendingVitals, setPendingVitals] = useState([]);
  const [pendingOrders, setPendingOrders] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [vitalsDialogOpen, setVitalsDialogOpen] = useState(false);
  const [newVitals, setNewVitals] = useState({
    blood_pressure_systolic: '', blood_pressure_diastolic: '',
    heart_rate: '', respiratory_rate: '', temperature: '',
    oxygen_saturation: '', weight: '', height: '', notes: ''
  });

  const fetchData = useCallback(async () => {
    try {
      const [patientsRes, ordersRes] = await Promise.all([
        patientAPI.getAll(),
        ordersAPI.getAll({ status: 'pending' })
      ]);
      
      setPatients(patientsRes.data);
      setPendingOrders(ordersRes.data.filter(o => o.order_type === 'medication'));
      
      // Simulate pending meds and vitals tasks
      const meds = [];
      const vitals = [];
      for (const patient of patientsRes.data.slice(0, 5)) {
        const medsRes = await medicationsAPI.getByPatient(patient.id);
        medsRes.data.filter(m => m.status === 'active').forEach(m => {
          meds.push({ ...m, patient_name: patient.first_name + ' ' + patient.last_name });
        });
        vitals.push({
          patient_id: patient.id,
          patient_name: patient.first_name + ' ' + patient.last_name,
          last_recorded: 'Due now'
        });
      }
      setPendingMeds(meds.slice(0, 10));
      setPendingVitals(vitals);
    } catch (err) {
      console.error('Dashboard fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleRecordVitals = async (e) => {
    e.preventDefault();
    if (!selectedPatient) return;
    
    try {
      const data = { ...newVitals, patient_id: selectedPatient.patient_id };
      Object.keys(data).forEach(key => {
        if (data[key] === '') data[key] = null;
        if (['blood_pressure_systolic', 'blood_pressure_diastolic', 'heart_rate', 'respiratory_rate', 'oxygen_saturation'].includes(key) && data[key]) {
          data[key] = parseInt(data[key]);
        }
        if (['temperature', 'weight', 'height'].includes(key) && data[key]) {
          data[key] = parseFloat(data[key]);
        }
      });
      await vitalsAPI.create(data);
      toast.success('Vitals recorded successfully');
      setVitalsDialogOpen(false);
      setNewVitals({
        blood_pressure_systolic: '', blood_pressure_diastolic: '',
        heart_rate: '', respiratory_rate: '', temperature: '',
        oxygen_saturation: '', weight: '', height: '', notes: ''
      });
      fetchData();
    } catch (err) {
      toast.error('Failed to record vitals');
    }
  };

  const markMedAdministered = async (medId) => {
    toast.success('Medication marked as administered');
    setPendingMeds(pendingMeds.filter(m => m.id !== medId));
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="nurse-dashboard">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900" style={{ fontFamily: 'Manrope' }}>
            Nursing Workstation
          </h1>
          <p className="text-slate-500 mt-1">
            Welcome, {user?.first_name} • {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
          </p>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-amber-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Pending Vitals</p>
                <p className="text-2xl font-bold text-slate-900">{pendingVitals.length}</p>
              </div>
              <Heart className="w-8 h-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Meds Due</p>
                <p className="text-2xl font-bold text-slate-900">{pendingMeds.length}</p>
              </div>
              <Pill className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Med Orders</p>
                <p className="text-2xl font-bold text-slate-900">{pendingOrders.length}</p>
              </div>
              <ClipboardList className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-emerald-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">My Patients</p>
                <p className="text-2xl font-bold text-slate-900">{patients.length}</p>
              </div>
              <User className="w-8 h-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Vitals Due */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Heart className="w-5 h-5 text-red-500" /> Vitals Due
              </CardTitle>
              <CardDescription>Record patient vital signs</CardDescription>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3">
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
              </div>
            ) : pendingVitals.length === 0 ? (
              <p className="text-center py-8 text-slate-500">All vitals recorded</p>
            ) : (
              <div className="space-y-2">
                {pendingVitals.map((v, idx) => (
                  <div 
                    key={idx} 
                    className="flex items-center justify-between p-3 rounded-lg border border-slate-200 hover:border-amber-200 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center">
                        <Activity className="w-5 h-5 text-amber-600" />
                      </div>
                      <div>
                        <p className="font-medium text-slate-900">{v.patient_name}</p>
                        <p className="text-sm text-slate-500">{v.last_recorded}</p>
                      </div>
                    </div>
                    <Dialog open={vitalsDialogOpen && selectedPatient?.patient_id === v.patient_id} onOpenChange={(open) => {
                      setVitalsDialogOpen(open);
                      if (open) setSelectedPatient(v);
                    }}>
                      <DialogTrigger asChild>
                        <Button size="sm" variant="outline" className="gap-1">
                          <Plus className="w-4 h-4" /> Record
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>Record Vitals - {v.patient_name}</DialogTitle>
                        </DialogHeader>
                        <form onSubmit={handleRecordVitals} className="space-y-4 mt-4">
                          <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                              <Label>Systolic BP</Label>
                              <Input type="number" value={newVitals.blood_pressure_systolic} onChange={(e) => setNewVitals({ ...newVitals, blood_pressure_systolic: e.target.value })} />
                            </div>
                            <div className="space-y-2">
                              <Label>Diastolic BP</Label>
                              <Input type="number" value={newVitals.blood_pressure_diastolic} onChange={(e) => setNewVitals({ ...newVitals, blood_pressure_diastolic: e.target.value })} />
                            </div>
                            <div className="space-y-2">
                              <Label>Heart Rate</Label>
                              <Input type="number" value={newVitals.heart_rate} onChange={(e) => setNewVitals({ ...newVitals, heart_rate: e.target.value })} />
                            </div>
                            <div className="space-y-2">
                              <Label>Temperature</Label>
                              <Input type="number" step="0.1" value={newVitals.temperature} onChange={(e) => setNewVitals({ ...newVitals, temperature: e.target.value })} />
                            </div>
                            <div className="space-y-2">
                              <Label>SpO2 %</Label>
                              <Input type="number" value={newVitals.oxygen_saturation} onChange={(e) => setNewVitals({ ...newVitals, oxygen_saturation: e.target.value })} />
                            </div>
                            <div className="space-y-2">
                              <Label>Resp Rate</Label>
                              <Input type="number" value={newVitals.respiratory_rate} onChange={(e) => setNewVitals({ ...newVitals, respiratory_rate: e.target.value })} />
                            </div>
                          </div>
                          <Button type="submit" className="w-full">Save Vitals</Button>
                        </form>
                      </DialogContent>
                    </Dialog>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Medication Administration Record (MAR) */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Pill className="w-5 h-5 text-blue-500" /> Medication Administration
            </CardTitle>
            <CardDescription>Medications due for administration</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3">
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
              </div>
            ) : pendingMeds.length === 0 ? (
              <p className="text-center py-8 text-slate-500">No medications due</p>
            ) : (
              <div className="space-y-2">
                {pendingMeds.map((med) => (
                  <div 
                    key={med.id} 
                    className="flex items-center justify-between p-3 rounded-lg border border-slate-200 hover:border-blue-200 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <Checkbox 
                        onCheckedChange={() => markMedAdministered(med.id)}
                        className="h-5 w-5"
                      />
                      <div>
                        <p className="font-medium text-slate-900">{med.name}</p>
                        <p className="text-sm text-slate-500">
                          {med.dosage} • {med.frequency} • {med.route}
                        </p>
                        <p className="text-xs text-slate-400">Patient: {med.patient_name}</p>
                      </div>
                    </div>
                    <Badge variant="outline" className="text-xs">Due Now</Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Pending Orders */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ClipboardList className="w-5 h-5 text-purple-500" /> Pending Medication Orders
          </CardTitle>
          <CardDescription>New orders requiring attention</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              <Skeleton className="h-16 w-full" />
            </div>
          ) : pendingOrders.length === 0 ? (
            <p className="text-center py-8 text-slate-500">No pending medication orders</p>
          ) : (
            <div className="space-y-2">
              {pendingOrders.map((order) => (
                <div 
                  key={order.id} 
                  className="flex items-center justify-between p-4 rounded-lg border border-slate-200"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-slate-900">{order.description}</p>
                      <Badge className={order.priority === 'stat' ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-700'}>
                        {order.priority}
                      </Badge>
                    </div>
                    <p className="text-sm text-slate-500">Ordered by: {order.ordered_by_name}</p>
                  </div>
                  <Button size="sm" variant="outline">
                    <Check className="w-4 h-4 mr-1" /> Acknowledge
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
