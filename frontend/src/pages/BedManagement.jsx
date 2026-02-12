import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/lib/auth';
import { patientAPI, usersAPI } from '@/lib/api';
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
import { toast } from 'sonner';
import { formatDateTime } from '@/lib/utils';
import { 
  Bed, UserPlus, ArrowRightLeft, LogOut as DischargeIcon,
  Activity, Users, Clock, Building2
} from 'lucide-react';

const API_BASE = process.env.REACT_APP_BACKEND_URL;

export default function BedManagement() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [beds, setBeds] = useState([]);
  const [availableBeds, setAvailableBeds] = useState([]);
  const [adtEvents, setAdtEvents] = useState([]);
  const [patients, setPatients] = useState([]);
  const [providers, setProviders] = useState([]);
  const [selectedWard, setSelectedWard] = useState('all');
  
  const [admitDialogOpen, setAdmitDialogOpen] = useState(false);
  const [transferDialogOpen, setTransferDialogOpen] = useState(false);
  const [dischargeDialogOpen, setDischargeDialogOpen] = useState(false);
  const [selectedBed, setSelectedBed] = useState(null);
  
  const [admitForm, setAdmitForm] = useState({
    patient_id: '', patient_class: 'I', ward: '', room: '', bed: '',
    attending_physician_id: '', admitting_diagnosis: ''
  });
  
  const [transferForm, setTransferForm] = useState({
    patient_id: '', from_location: '', to_ward: '', to_room: '', to_bed: '', reason: ''
  });
  
  const [dischargeForm, setDischargeForm] = useState({
    patient_id: '', discharge_disposition: 'home', discharge_diagnosis: '', follow_up_instructions: ''
  });

  const wards = ['ICU', 'MED-SURG', 'PEDS', 'OB', 'PSYCH'];

  const fetchData = useCallback(async () => {
    const token = localStorage.getItem('yacco_token');
    const headers = { 'Authorization': `Bearer ${token}` };
    
    try {
      const [bedsRes, availableRes, eventsRes, patientsRes, usersRes] = await Promise.all([
        fetch(`${API_BASE}/api/hl7/beds${selectedWard !== 'all' ? `?ward=${selectedWard}` : ''}`, { headers }),
        fetch(`${API_BASE}/api/hl7/beds/available${selectedWard !== 'all' ? `?ward=${selectedWard}` : ''}`, { headers }),
        fetch(`${API_BASE}/api/hl7/adt/events?limit=50`, { headers }),
        patientAPI.getAll(),
        usersAPI.getAll()
      ]);
      
      if (bedsRes.ok) setBeds(await bedsRes.json());
      if (availableRes.ok) setAvailableBeds(await availableRes.json());
      if (eventsRes.ok) setAdtEvents(await eventsRes.json());
      setPatients(patientsRes.data);
      setProviders(usersRes.data.filter(u => u.role === 'physician'));
    } catch (err) {
      console.error('Error fetching bed data:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedWard]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleAdmit = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('yacco_token');
    
    try {
      const res = await fetch(`${API_BASE}/api/hl7/adt/admit`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(admitForm)
      });
      
      if (res.ok) {
        toast.success('Patient admitted successfully');
        setAdmitDialogOpen(false);
        setAdmitForm({
          patient_id: '', patient_class: 'I', ward: '', room: '', bed: '',
          attending_physician_id: '', admitting_diagnosis: ''
        });
        fetchData();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Failed to admit patient');
      }
    } catch (err) {
      toast.error('Connection error');
    }
  };

  const handleTransfer = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('yacco_token');
    
    try {
      const res = await fetch(`${API_BASE}/api/hl7/adt/transfer`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(transferForm)
      });
      
      if (res.ok) {
        toast.success('Patient transferred successfully');
        setTransferDialogOpen(false);
        setTransferForm({
          patient_id: '', from_location: '', to_ward: '', to_room: '', to_bed: '', reason: ''
        });
        fetchData();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Failed to transfer patient');
      }
    } catch (err) {
      toast.error('Connection error');
    }
  };

  const handleDischarge = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('yacco_token');
    
    try {
      const res = await fetch(`${API_BASE}/api/hl7/adt/discharge`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(dischargeForm)
      });
      
      if (res.ok) {
        toast.success('Patient discharged successfully');
        setDischargeDialogOpen(false);
        setDischargeForm({
          patient_id: '', discharge_disposition: 'home', discharge_diagnosis: '', follow_up_instructions: ''
        });
        fetchData();
      } else {
        const error = await res.json();
        toast.error(error.detail || 'Failed to discharge patient');
      }
    } catch (err) {
      toast.error('Connection error');
    }
  };

  const getEventTypeColor = (eventType) => {
    const colors = {
      'A01': 'bg-emerald-100 text-emerald-700',
      'A02': 'bg-blue-100 text-blue-700',
      'A03': 'bg-amber-100 text-amber-700',
    };
    return colors[eventType] || 'bg-slate-100 text-slate-700';
  };

  const getEventTypeName = (eventType) => {
    const names = {
      'A01': 'Admit',
      'A02': 'Transfer',
      'A03': 'Discharge',
    };
    return names[eventType] || eventType;
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="bed-management-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900" style={{ fontFamily: 'Manrope' }}>
            Bed Management
          </h1>
          <p className="text-slate-500 mt-1">ADT - Admissions, Discharges, Transfers</p>
        </div>
        <div className="flex gap-2">
          <Dialog open={admitDialogOpen} onOpenChange={setAdmitDialogOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2 bg-emerald-600 hover:bg-emerald-700">
                <UserPlus className="w-4 h-4" /> Admit
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Admit Patient</DialogTitle>
                <DialogDescription>Assign a bed to a patient</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleAdmit} className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label>Patient</Label>
                  <Select value={admitForm.patient_id} onValueChange={(v) => setAdmitForm({ ...admitForm, patient_id: v })}>
                    <SelectTrigger><SelectValue placeholder="Select patient" /></SelectTrigger>
                    <SelectContent>
                      {patients.map((p) => (
                        <SelectItem key={p.id} value={p.id}>{p.first_name} {p.last_name} ({p.mrn})</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Patient Class</Label>
                  <Select value={admitForm.patient_class} onValueChange={(v) => setAdmitForm({ ...admitForm, patient_class: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="I">Inpatient</SelectItem>
                      <SelectItem value="O">Outpatient</SelectItem>
                      <SelectItem value="E">Emergency</SelectItem>
                      <SelectItem value="P">Pre-admit</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div className="space-y-2">
                    <Label>Ward</Label>
                    <Select value={admitForm.ward} onValueChange={(v) => setAdmitForm({ ...admitForm, ward: v })}>
                      <SelectTrigger><SelectValue placeholder="Ward" /></SelectTrigger>
                      <SelectContent>
                        {wards.map((w) => (
                          <SelectItem key={w} value={w}>{w}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Room</Label>
                    <Input value={admitForm.room} onChange={(e) => setAdmitForm({ ...admitForm, room: e.target.value })} placeholder="101" />
                  </div>
                  <div className="space-y-2">
                    <Label>Bed</Label>
                    <Select value={admitForm.bed} onValueChange={(v) => setAdmitForm({ ...admitForm, bed: v })}>
                      <SelectTrigger><SelectValue placeholder="Bed" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="A">A</SelectItem>
                        <SelectItem value="B">B</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Attending Physician</Label>
                  <Select value={admitForm.attending_physician_id} onValueChange={(v) => setAdmitForm({ ...admitForm, attending_physician_id: v })}>
                    <SelectTrigger><SelectValue placeholder="Select physician" /></SelectTrigger>
                    <SelectContent>
                      {providers.map((p) => (
                        <SelectItem key={p.id} value={p.id}>Dr. {p.first_name} {p.last_name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Admitting Diagnosis</Label>
                  <Input value={admitForm.admitting_diagnosis} onChange={(e) => setAdmitForm({ ...admitForm, admitting_diagnosis: e.target.value })} />
                </div>
                <Button type="submit" className="w-full">Admit Patient</Button>
              </form>
            </DialogContent>
          </Dialog>

          <Dialog open={transferDialogOpen} onOpenChange={setTransferDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" className="gap-2">
                <ArrowRightLeft className="w-4 h-4" /> Transfer
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Transfer Patient</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleTransfer} className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label>Patient</Label>
                  <Select value={transferForm.patient_id} onValueChange={(v) => {
                    const bed = beds.find(b => b.patient_id === v);
                    setTransferForm({ 
                      ...transferForm, 
                      patient_id: v,
                      from_location: bed ? `${bed.ward}-${bed.room}-${bed.bed}` : ''
                    });
                  }}>
                    <SelectTrigger><SelectValue placeholder="Select patient" /></SelectTrigger>
                    <SelectContent>
                      {beds.map((b) => (
                        <SelectItem key={b.patient_id} value={b.patient_id}>
                          {b.patient_name} ({b.ward} {b.room}{b.bed})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-3 gap-3">
                  <div className="space-y-2">
                    <Label>To Ward</Label>
                    <Select value={transferForm.to_ward} onValueChange={(v) => setTransferForm({ ...transferForm, to_ward: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {wards.map((w) => (
                          <SelectItem key={w} value={w}>{w}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Room</Label>
                    <Input value={transferForm.to_room} onChange={(e) => setTransferForm({ ...transferForm, to_room: e.target.value })} />
                  </div>
                  <div className="space-y-2">
                    <Label>Bed</Label>
                    <Select value={transferForm.to_bed} onValueChange={(v) => setTransferForm({ ...transferForm, to_bed: v })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="A">A</SelectItem>
                        <SelectItem value="B">B</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Reason</Label>
                  <Input value={transferForm.reason} onChange={(e) => setTransferForm({ ...transferForm, reason: e.target.value })} />
                </div>
                <Button type="submit" className="w-full">Transfer Patient</Button>
              </form>
            </DialogContent>
          </Dialog>

          <Dialog open={dischargeDialogOpen} onOpenChange={setDischargeDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" className="gap-2">
                <DischargeIcon className="w-4 h-4" /> Discharge
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Discharge Patient</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleDischarge} className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label>Patient</Label>
                  <Select value={dischargeForm.patient_id} onValueChange={(v) => setDischargeForm({ ...dischargeForm, patient_id: v })}>
                    <SelectTrigger><SelectValue placeholder="Select patient" /></SelectTrigger>
                    <SelectContent>
                      {beds.map((b) => (
                        <SelectItem key={b.patient_id} value={b.patient_id}>
                          {b.patient_name} ({b.ward} {b.room}{b.bed})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Discharge Disposition</Label>
                  <Select value={dischargeForm.discharge_disposition} onValueChange={(v) => setDischargeForm({ ...dischargeForm, discharge_disposition: v })}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="home">Home</SelectItem>
                      <SelectItem value="snf">Skilled Nursing Facility</SelectItem>
                      <SelectItem value="rehab">Rehabilitation</SelectItem>
                      <SelectItem value="transfer">Transfer to Another Facility</SelectItem>
                      <SelectItem value="ama">Against Medical Advice</SelectItem>
                      <SelectItem value="expired">Expired</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Discharge Diagnosis</Label>
                  <Input value={dischargeForm.discharge_diagnosis} onChange={(e) => setDischargeForm({ ...dischargeForm, discharge_diagnosis: e.target.value })} />
                </div>
                <div className="space-y-2">
                  <Label>Follow-up Instructions</Label>
                  <Input value={dischargeForm.follow_up_instructions} onChange={(e) => setDischargeForm({ ...dischargeForm, follow_up_instructions: e.target.value })} />
                </div>
                <Button type="submit" className="w-full">Discharge Patient</Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-emerald-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Occupied Beds</p>
                <p className="text-2xl font-bold text-slate-900">{beds.length}</p>
              </div>
              <Bed className="w-8 h-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-sky-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Available Beds</p>
                <p className="text-2xl font-bold text-slate-900">{availableBeds.length}</p>
              </div>
              <Bed className="w-8 h-8 text-sky-500" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-amber-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Today's ADT Events</p>
                <p className="text-2xl font-bold text-slate-900">{adtEvents.length}</p>
              </div>
              <Activity className="w-8 h-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Wards</p>
                <p className="text-2xl font-bold text-slate-900">{wards.length}</p>
              </div>
              <Building2 className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Ward Filter */}
      <Card>
        <CardContent className="py-4">
          <div className="flex items-center gap-4">
            <Label>Filter by Ward:</Label>
            <Select value={selectedWard} onValueChange={setSelectedWard}>
              <SelectTrigger className="w-[200px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Wards</SelectItem>
                {wards.map((w) => (
                  <SelectItem key={w} value={w}>{w}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs defaultValue="census">
        <TabsList>
          <TabsTrigger value="census">Bed Census</TabsTrigger>
          <TabsTrigger value="available">Available Beds</TabsTrigger>
          <TabsTrigger value="events">ADT Events</TabsTrigger>
        </TabsList>

        <TabsContent value="census" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Current Bed Census</CardTitle>
              <CardDescription>Currently occupied beds</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-3">
                  <Skeleton className="h-16 w-full" />
                  <Skeleton className="h-16 w-full" />
                </div>
              ) : beds.length === 0 ? (
                <p className="text-slate-500 text-center py-8">No patients currently admitted</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {beds.map((bed) => (
                    <div key={bed.id} className="p-4 rounded-lg border border-slate-200 hover:border-emerald-200 transition-colors">
                      <div className="flex items-center justify-between mb-2">
                        <Badge className="bg-emerald-100 text-emerald-700">
                          {bed.ward} {bed.room}{bed.bed}
                        </Badge>
                        <Badge variant="outline">{bed.status}</Badge>
                      </div>
                      <p className="font-medium text-slate-900">{bed.patient_name}</p>
                      <p className="text-sm text-slate-500">Admitted: {formatDateTime(bed.admit_datetime)}</p>
                      {bed.attending_physician && (
                        <p className="text-xs text-slate-400 mt-1">{bed.attending_physician}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="available" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Available Beds</CardTitle>
              <CardDescription>Beds ready for patient placement</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <Skeleton className="h-64 w-full" />
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                  {availableBeds.slice(0, 30).map((bed, idx) => (
                    <div 
                      key={idx}
                      className="p-3 rounded-lg border border-sky-200 bg-sky-50 text-center cursor-pointer hover:bg-sky-100 transition-colors"
                      onClick={() => {
                        setAdmitForm({ ...admitForm, ward: bed.ward, room: bed.room, bed: bed.bed });
                        setAdmitDialogOpen(true);
                      }}
                    >
                      <p className="font-medium text-sky-700">{bed.ward}</p>
                      <p className="text-lg font-bold text-sky-900">{bed.room}{bed.bed}</p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="events" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>ADT Events History</CardTitle>
              <CardDescription>Recent admissions, discharges, and transfers</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-3">
                  <Skeleton className="h-16 w-full" />
                  <Skeleton className="h-16 w-full" />
                </div>
              ) : adtEvents.length === 0 ? (
                <p className="text-slate-500 text-center py-8">No ADT events recorded</p>
              ) : (
                <div className="space-y-3">
                  {adtEvents.map((event) => (
                    <div key={event.id} className="p-4 rounded-lg border border-slate-200">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <Badge className={getEventTypeColor(event.event_type)}>
                            {getEventTypeName(event.event_type)}
                          </Badge>
                          <div>
                            <p className="font-medium text-slate-900">{event.patient_name}</p>
                            <p className="text-sm text-slate-500">MRN: {event.mrn}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-slate-600">{event.location}</p>
                          <p className="text-xs text-slate-400">{formatDateTime(event.created_at)}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
