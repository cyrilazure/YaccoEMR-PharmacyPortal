import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/lib/auth';
import { getErrorMessage } from '@/lib/utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { toast } from 'sonner';
import { Ambulance, Plus, RefreshCw, Clock, CheckCircle, XCircle, Car, Users, Activity, TrendingUp, Loader2, MapPin, FileText, AlertTriangle, Search, User } from 'lucide-react';
import api, { patientAPI } from '@/lib/api';

const ambulanceAPI = {
  getVehicles: (params) => api.get('/ambulance/vehicles', { params }),
  createVehicle: (data) => api.post('/ambulance/vehicles', data),
  updateVehicleStatus: (id, status, notes) => api.put(`/ambulance/vehicles/${id}/status`, null, { params: { status, notes } }),
  getRequests: (params) => api.get('/ambulance/requests', { params }),
  createRequest: (data) => api.post('/ambulance/requests', data),
  approveRequest: (id) => api.put(`/ambulance/requests/${id}/approve`),
  dispatchAmbulance: (id, data) => api.post(`/ambulance/requests/${id}/dispatch`, data),
  updateTripStatus: (id, data) => api.put(`/ambulance/requests/${id}/update-status`, data),
  getDashboard: () => api.get('/ambulance/dashboard'),
  clockIn: (data) => api.post('/ambulance/staff/clock-in', data),
  clockOut: (shiftId) => api.post('/ambulance/staff/clock-out', null, { params: { shift_id: shiftId } }),
  getActiveShifts: () => api.get('/ambulance/staff/active-shifts'),
};

export default function AmbulancePortal() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);
  const [vehicles, setVehicles] = useState([]);
  const [requests, setRequests] = useState([]);
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Dialogs
  const [addVehicleOpen, setAddVehicleOpen] = useState(false);
  const [requestAmbulanceOpen, setRequestAmbulanceOpen] = useState(false);
  const [dispatchOpen, setDispatchOpen] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [saving, setSaving] = useState(false);
  
  // Forms
  const [vehicleForm, setVehicleForm] = useState({
    vehicle_number: '',
    vehicle_type: 'basic_ambulance',
    equipment_level: 'basic',
    make_model: '',
    year: new Date().getFullYear(),
    capacity: 1,
    has_oxygen: true,
    has_defibrillator: false,
    has_ventilator: false,
    has_stretcher: true,
    notes: ''
  });
  
  const [requestForm, setRequestForm] = useState({
    patient_id: '',
    patient_name: '',
    patient_mrn: '',
    pickup_location: '',
    destination_facility: '',
    destination_address: '',
    referral_reason: '',
    diagnosis_summary: '',
    trip_type: 'emergency',
    priority_level: 'urgent',
    special_requirements: '',
    physician_notes: ''
  });
  
  const [dispatchForm, setDispatchForm] = useState({
    vehicle_id: '',
    driver_id: '',
    paramedic_id: '',
    estimated_arrival: '',
    notes: ''
  });
  
  // Patient search state
  const [patientSearchQuery, setPatientSearchQuery] = useState('');
  const [patientSearchResults, setPatientSearchResults] = useState([]);
  const [searchingPatients, setSearchingPatients] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [entryMode, setEntryMode] = useState('search'); // 'search' or 'manual'

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [dashboardRes, vehiclesRes, requestsRes] = await Promise.all([
        ambulanceAPI.getDashboard(),
        ambulanceAPI.getVehicles({}),
        ambulanceAPI.getRequests({})
      ]);
      
      setDashboard(dashboardRes.data);
      setVehicles(vehiclesRes.data.vehicles || []);
      setRequests(requestsRes.data.requests || []);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to load ambulance data'));
    } finally {
      setLoading(false);
    }
  };

  const handleAddVehicle = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await ambulanceAPI.createVehicle(vehicleForm);
      toast.success('Ambulance vehicle registered');
      setAddVehicleOpen(false);
      setVehicleForm({
        vehicle_number: '', vehicle_type: 'basic_ambulance', equipment_level: 'basic',
        make_model: '', year: new Date().getFullYear(), capacity: 1,
        has_oxygen: true, has_defibrillator: false, has_ventilator: false,
        has_stretcher: true, notes: ''
      });
      fetchData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to register vehicle'));
    } finally {
      setSaving(false);
    }
  };

  const handleRequestAmbulance = async (e) => {
    e.preventDefault();
    if (!requestForm.patient_name || !requestForm.pickup_location || !requestForm.referral_reason) {
      toast.error('Please fill in required fields');
      return;
    }
    
    setSaving(true);
    try {
      await ambulanceAPI.createRequest(requestForm);
      toast.success('Ambulance request submitted');
      setRequestAmbulanceOpen(false);
      setRequestForm({
        patient_id: '', patient_name: '', patient_mrn: '',
        pickup_location: '', destination_facility: '', destination_address: '',
        referral_reason: '', diagnosis_summary: '', trip_type: 'emergency',
        priority_level: 'urgent', special_requirements: '', physician_notes: ''
      });
      fetchData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to create request'));
    } finally {
      setSaving(false);
    }
  };

  const handleApprove = async (requestId) => {
    try {
      await ambulanceAPI.approveRequest(requestId);
      toast.success('Request approved');
      fetchData();
    } catch (err) {
      toast.error('Failed to approve request');
    }
  };

  const handleDispatch = async (e) => {
    e.preventDefault();
    if (!dispatchForm.vehicle_id) {
      toast.error('Please select a vehicle');
      return;
    }
    
    setSaving(true);
    try {
      await ambulanceAPI.dispatchAmbulance(selectedRequest.id, {
        ...dispatchForm,
        request_id: selectedRequest.id
      });
      toast.success('Ambulance dispatched');
      setDispatchOpen(false);
      setSelectedRequest(null);
      fetchData();
    } catch (err) {
      toast.error('Failed to dispatch');
    } finally {
      setSaving(false);
    }
  };

  const handleStatusUpdate = async (requestId, status) => {
    try {
      await ambulanceAPI.updateTripStatus(requestId, { status });
      toast.success(`Status updated to ${status}`);
      fetchData();
    } catch (err) {
      toast.error('Failed to update status');
    }
  };

  const getStatusBadge = (status) => {
    const colors = {
      requested: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-blue-100 text-blue-800',
      dispatched: 'bg-purple-100 text-purple-800',
      en_route: 'bg-indigo-100 text-indigo-800',
      arrived: 'bg-cyan-100 text-cyan-800',
      transporting: 'bg-violet-100 text-violet-800',
      completed: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Ambulance className="w-7 h-7 text-red-600" />
            Ambulance & Emergency Transport
          </h1>
          <p className="text-slate-500 mt-1">Manage fleet, dispatch, and patient referrals</p>
        </div>
        <Button onClick={fetchData} variant="outline" className="gap-2">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="text-center">
              <Car className="w-8 h-8 mx-auto mb-2 text-slate-400" />
              <p className="text-sm text-slate-600">Total Fleet</p>
              <p className="text-2xl font-bold">{dashboard?.fleet?.total || 0}</p>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-green-50 border-green-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-600" />
              <p className="text-sm text-green-700">Available</p>
              <p className="text-2xl font-bold text-green-800">{dashboard?.fleet?.available || 0}</p>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <Activity className="w-8 h-8 mx-auto mb-2 text-blue-600" />
              <p className="text-sm text-blue-700">In Use</p>
              <p className="text-2xl font-bold text-blue-800">{dashboard?.fleet?.in_use || 0}</p>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-amber-50 border-amber-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-amber-600" />
              <p className="text-sm text-amber-700">Active Requests</p>
              <p className="text-2xl font-bold text-amber-800">{dashboard?.requests?.active || 0}</p>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-emerald-50 border-emerald-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <TrendingUp className="w-8 h-8 mx-auto mb-2 text-emerald-600" />
              <p className="text-sm text-emerald-700">Today</p>
              <p className="text-2xl font-bold text-emerald-800">{dashboard?.requests?.completed_today || 0}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
          <TabsTrigger value="requests">Requests</TabsTrigger>
          <TabsTrigger value="fleet">Fleet</TabsTrigger>
        </TabsList>

        {/* Dashboard Tab */}
        <TabsContent value="dashboard" className="mt-4 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Trip Statistics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Emergency Trips:</span>
                    <span className="font-bold">{dashboard?.requests?.total_emergency || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Scheduled Transfers:</span>
                    <span className="font-bold">{dashboard?.requests?.total_scheduled || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Active Staff:</span>
                    <span className="font-bold">{dashboard?.staff?.active_shifts || 0}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button 
                  onClick={() => setRequestAmbulanceOpen(true)}
                  className="w-full gap-2 bg-red-600 hover:bg-red-700"
                >
                  <Ambulance className="w-4 h-4" />
                  Request Ambulance
                </Button>
                <Button 
                  onClick={() => setAddVehicleOpen(true)}
                  variant="outline"
                  className="w-full gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Register Vehicle
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Requests Tab */}
        <TabsContent value="requests" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Ambulance Requests</CardTitle>
                <CardDescription>Active and recent transport requests</CardDescription>
              </div>
              <Button onClick={() => setRequestAmbulanceOpen(true)} className="gap-2 bg-red-600 hover:bg-red-700">
                <Plus className="w-4 h-4" /> Request Ambulance
              </Button>
            </CardHeader>
            <CardContent>
              {requests.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <Ambulance className="w-12 h-12 mx-auto mb-4 opacity-30" />
                  <p>No ambulance requests</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Request #</TableHead>
                      <TableHead>Patient</TableHead>
                      <TableHead>From → To</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Priority</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Vehicle</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {requests.map((req) => (
                      <TableRow key={req.id}>
                        <TableCell className="font-mono text-sm">{req.request_number}</TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{req.patient_name}</p>
                            <p className="text-xs text-gray-500">{req.patient_mrn}</p>
                          </div>
                        </TableCell>
                        <TableCell className="text-sm">
                          <div className="max-w-xs">
                            <p className="truncate">{req.pickup_location}</p>
                            <p className="text-xs text-gray-400">→ {req.destination_facility}</p>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="capitalize">{req.trip_type?.replace('_', ' ')}</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge className={req.priority_level === 'emergency' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}>
                            {req.priority_level?.toUpperCase()}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge className={getStatusBadge(req.status)}>
                            {req.status?.replace('_', ' ')}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm">
                          {req.vehicle_id ? (
                            vehicles.find(v => v.id === req.vehicle_id)?.vehicle_number || 'Assigned'
                          ) : 'None'}
                        </TableCell>
                        <TableCell className="text-right">
                          {req.status === 'requested' && (
                            <Button size="sm" onClick={() => handleApprove(req.id)} className="mr-1">
                              Approve
                            </Button>
                          )}
                          {req.status === 'approved' && (
                            <Button size="sm" onClick={() => { setSelectedRequest(req); setDispatchOpen(true); }}>
                              Dispatch
                            </Button>
                          )}
                          {req.status === 'dispatched' && (
                            <Button size="sm" onClick={() => handleStatusUpdate(req.id, 'en_route')}>
                              En Route
                            </Button>
                          )}
                          {req.status === 'en_route' && (
                            <Button size="sm" onClick={() => handleStatusUpdate(req.id, 'arrived')}>
                              Arrived
                            </Button>
                          )}
                          {req.status === 'arrived' && (
                            <Button size="sm" onClick={() => handleStatusUpdate(req.id, 'completed')} className="bg-green-600">
                              Complete
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Fleet Tab */}
        <TabsContent value="fleet" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Ambulance Fleet</CardTitle>
                <CardDescription>Registered vehicles and equipment</CardDescription>
              </div>
              <Button onClick={() => setAddVehicleOpen(true)} className="gap-2">
                <Plus className="w-4 h-4" /> Register Vehicle
              </Button>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {vehicles.map((vehicle) => (
                  <Card key={vehicle.id} className="border-2">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base flex items-center gap-2">
                          <Ambulance className="w-5 h-5 text-red-600" />
                          {vehicle.vehicle_number}
                        </CardTitle>
                        <Badge className={vehicle.status === 'available' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}>
                          {vehicle.status}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2 text-sm">
                        <p><span className="text-gray-600">Type:</span> <span className="capitalize">{vehicle.vehicle_type?.replace('_', ' ')}</span></p>
                        <p><span className="text-gray-600">Equipment:</span> <span className="capitalize">{vehicle.equipment_level}</span></p>
                        {vehicle.make_model && <p><span className="text-gray-600">Model:</span> {vehicle.make_model} ({vehicle.year})</p>}
                        <div className="flex flex-wrap gap-2 mt-2">
                          {vehicle.has_oxygen && <Badge variant="outline" className="text-xs">Oxygen</Badge>}
                          {vehicle.has_defibrillator && <Badge variant="outline" className="text-xs">Defibrillator</Badge>}
                          {vehicle.has_ventilator && <Badge variant="outline" className="text-xs">Ventilator</Badge>}
                          {vehicle.has_stretcher && <Badge variant="outline" className="text-xs">Stretcher</Badge>}
                        </div>
                        <p className="text-xs text-gray-500 mt-2">Trips: {vehicle.total_trips || 0} | Mileage: {vehicle.total_mileage || 0} km</p>
                      </div>
                    </CardContent>
                  </Card>
                ))}
                {vehicles.length === 0 && (
                  <div className="col-span-2 text-center py-12 text-gray-500">
                    <Car className="w-12 h-12 mx-auto mb-4 opacity-30" />
                    <p>No vehicles registered</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Add Vehicle Dialog - Continued in next message due to length */}
      
      {/* Add Vehicle Dialog */}
      <Dialog open={addVehicleOpen} onOpenChange={setAddVehicleOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Register Ambulance Vehicle</DialogTitle>
            <DialogDescription>Add vehicle to fleet</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleAddVehicle} className="space-y-4 mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Vehicle Number/Plate *</Label>
                <Input value={vehicleForm.vehicle_number} onChange={(e) => setVehicleForm({...vehicleForm, vehicle_number: e.target.value})} placeholder="GW-1234-21" required />
              </div>
              <div className="space-y-2">
                <Label>Make & Model</Label>
                <Input value={vehicleForm.make_model} onChange={(e) => setVehicleForm({...vehicleForm, make_model: e.target.value})} placeholder="Toyota Land Cruiser" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Vehicle Type</Label>
                <Select value={vehicleForm.vehicle_type} onValueChange={(v) => setVehicleForm({...vehicleForm, vehicle_type: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="basic_ambulance">Basic Ambulance</SelectItem>
                    <SelectItem value="advanced_ambulance">Advanced Ambulance</SelectItem>
                    <SelectItem value="patient_transport">Patient Transport</SelectItem>
                    <SelectItem value="emergency_response">Emergency Response</SelectItem>
                    <SelectItem value="icu_ambulance">ICU Ambulance</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Equipment Level</Label>
                <Select value={vehicleForm.equipment_level} onValueChange={(v) => setVehicleForm({...vehicleForm, equipment_level: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="basic">Basic</SelectItem>
                    <SelectItem value="intermediate">Intermediate</SelectItem>
                    <SelectItem value="advanced">Advanced</SelectItem>
                    <SelectItem value="critical">Critical/ICU</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-4 gap-2">
              <Label className="flex items-center gap-2"><input type="checkbox" checked={vehicleForm.has_oxygen} onChange={(e) => setVehicleForm({...vehicleForm, has_oxygen: e.target.checked})} /> Oxygen</Label>
              <Label className="flex items-center gap-2"><input type="checkbox" checked={vehicleForm.has_defibrillator} onChange={(e) => setVehicleForm({...vehicleForm, has_defibrillator: e.target.checked})} /> Defibrillator</Label>
              <Label className="flex items-center gap-2"><input type="checkbox" checked={vehicleForm.has_ventilator} onChange={(e) => setVehicleForm({...vehicleForm, has_ventilator: e.target.checked})} /> Ventilator</Label>
              <Label className="flex items-center gap-2"><input type="checkbox" checked={vehicleForm.has_stretcher} onChange={(e) => setVehicleForm({...vehicleForm, has_stretcher: e.target.checked})} /> Stretcher</Label>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setAddVehicleOpen(false)}>Cancel</Button>
              <Button type="submit" disabled={saving}>{saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}Register Vehicle</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Request Ambulance Dialog */}
      <Dialog open={requestAmbulanceOpen} onOpenChange={setRequestAmbulanceOpen}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>Request Ambulance/Patient Transfer</DialogTitle>
            <DialogDescription>Submit request for emergency transport or inter-facility transfer</DialogDescription>
          </DialogHeader>
          <div className="overflow-y-auto pr-2" style={{ maxHeight: 'calc(85vh - 160px)' }}>
          <form onSubmit={handleRequestAmbulance} className="space-y-4 mt-2">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Patient Name *</Label>
                <Input value={requestForm.patient_name} onChange={(e) => setRequestForm({...requestForm, patient_name: e.target.value})} required />
              </div>
              <div className="space-y-2">
                <Label>MRN Number *</Label>
                <Input value={requestForm.patient_mrn} onChange={(e) => setRequestForm({...requestForm, patient_mrn: e.target.value})} placeholder="Medical record number" required />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Pickup Location *</Label>
              <Input value={requestForm.pickup_location} onChange={(e) => setRequestForm({...requestForm, pickup_location: e.target.value})} placeholder="Ward, department, or address" required />
            </div>
            <div className="space-y-2">
              <Label>Destination Facility *</Label>
              <Input value={requestForm.destination_facility} onChange={(e) => setRequestForm({...requestForm, destination_facility: e.target.value})} placeholder="Hospital name" required />
            </div>
            <div className="space-y-2">
              <Label>Referral Reason *</Label>
              <Textarea value={requestForm.referral_reason} onChange={(e) => setRequestForm({...requestForm, referral_reason: e.target.value})} placeholder="Reason for transfer..." required />
            </div>
            <div className="space-y-2">
              <Label>Diagnosis Summary</Label>
              <Textarea value={requestForm.diagnosis_summary} onChange={(e) => setRequestForm({...requestForm, diagnosis_summary: e.target.value})} placeholder="Brief clinical summary..." />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Trip Type</Label>
                <Select value={requestForm.trip_type} onValueChange={(v) => setRequestForm({...requestForm, trip_type: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="emergency">Emergency</SelectItem>
                    <SelectItem value="scheduled">Scheduled Transfer</SelectItem>
                    <SelectItem value="inter_facility">Inter-Facility</SelectItem>
                    <SelectItem value="discharge">Discharge Transport</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Priority</Label>
                <Select value={requestForm.priority_level} onValueChange={(v) => setRequestForm({...requestForm, priority_level: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="routine">Routine</SelectItem>
                    <SelectItem value="urgent">Urgent</SelectItem>
                    <SelectItem value="emergency">Emergency</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter className="mt-4">
              <Button type="button" variant="outline" onClick={() => setRequestAmbulanceOpen(false)}>Cancel</Button>
              <Button type="submit" disabled={saving} className="bg-red-600 hover:bg-red-700">{saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}Submit Request</Button>
            </DialogFooter>
          </form>
          </div>
        </DialogContent>
      </Dialog>

      {/* Dispatch Dialog */}
      <Dialog open={dispatchOpen} onOpenChange={setDispatchOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Dispatch Ambulance</DialogTitle>
            <DialogDescription>Assign vehicle to {selectedRequest?.patient_name}</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleDispatch} className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label>Select Vehicle *</Label>
              <Select value={dispatchForm.vehicle_id} onValueChange={(v) => setDispatchForm({...dispatchForm, vehicle_id: v})}>
                <SelectTrigger><SelectValue placeholder="Choose vehicle" /></SelectTrigger>
                <SelectContent>
                  {vehicles.filter(v => v.status === 'available').map(v => (
                    <SelectItem key={v.id} value={v.id}>{v.vehicle_number} - {v.vehicle_type?.replace('_', ' ')}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Estimated Arrival</Label>
              <Input type="time" value={dispatchForm.estimated_arrival} onChange={(e) => setDispatchForm({...dispatchForm, estimated_arrival: e.target.value})} />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDispatchOpen(false)}>Cancel</Button>
              <Button type="submit" disabled={saving} className="bg-red-600">{saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}Dispatch</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

