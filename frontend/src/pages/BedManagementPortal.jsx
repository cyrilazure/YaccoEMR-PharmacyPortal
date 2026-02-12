import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/lib/auth';
import { getErrorMessage } from '@/lib/utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
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
import { toast } from 'sonner';
import {
  Bed, RefreshCw, Plus, Search, CheckCircle, AlertCircle,
  Building2, Users, Activity, ArrowRightLeft, LogOut,
  Loader2, AlertTriangle, Settings, Heart
} from 'lucide-react';
import api from '@/lib/api';

const bedAPI = {
  getCensus: () => api.get('/beds/census'),
  getWards: () => api.get('/beds/wards'),
  getBeds: (params) => api.get('/beds/beds', { params }),
  getAdmissions: (params) => api.get('/beds/admissions', { params }),
  createAdmission: (data) => api.post('/beds/admissions/create', data),
  transferPatient: (id, data) => api.post(`/beds/admissions/${id}/transfer`, data),
  dischargePatient: (id, data) => api.post(`/beds/admissions/${id}/discharge`, data),
  updateBedStatus: (id, status) => api.put(`/beds/beds/${id}/status`, null, { params: { status } }),
  seedWards: () => api.post('/beds/wards/seed-defaults'),
  bulkCreateBeds: (wardId, params) => api.post(`/beds/beds/bulk-create`, null, { params: { ward_id: wardId, ...params } }),
};

export default function BedManagementPortal() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [census, setCensus] = useState({ summary: {}, wards: [], critical_care: {} });
  const [wards, setWards] = useState([]);
  const [beds, setBeds] = useState([]);
  const [admissions, setAdmissions] = useState([]);
  const [activeTab, setActiveTab] = useState('census');
  const [selectedWard, setSelectedWard] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Dialogs
  const [admitDialogOpen, setAdmitDialogOpen] = useState(false);
  const [transferDialogOpen, setTransferDialogOpen] = useState(false);
  const [dischargeDialogOpen, setDischargeDialogOpen] = useState(false);
  const [selectedAdmission, setSelectedAdmission] = useState(null);
  const [selectedBed, setSelectedBed] = useState(null);
  const [saving, setSaving] = useState(false);
  
  // Admit form
  const [admitForm, setAdmitForm] = useState({
    patient_id: '',
    bed_id: '',
    admitting_diagnosis: '',
    admitting_physician_id: '',
    admission_source: 'emergency',
    notes: '',
    isolation_required: false
  });
  
  // Transfer form
  const [transferForm, setTransferForm] = useState({
    to_bed_id: '',
    transfer_reason: '',
    notes: ''
  });
  
  // Discharge form
  const [dischargeForm, setDischargeForm] = useState({
    discharge_disposition: 'home',
    discharge_diagnosis: '',
    discharge_instructions: '',
    follow_up_required: true,
    follow_up_date: ''
  });

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [censusRes, wardsRes, admissionsRes] = await Promise.all([
        bedAPI.getCensus(),
        bedAPI.getWards(),
        bedAPI.getAdmissions({})
      ]);
      
      setCensus(censusRes.data);
      setWards(wardsRes.data.wards || []);
      setAdmissions(admissionsRes.data.admissions || []);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to load data'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 60000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const fetchWardBeds = async (wardId) => {
    try {
      const response = await bedAPI.getBeds({ ward_id: wardId });
      setBeds(response.data.beds || []);
    } catch (err) {
      toast.error('Failed to load beds');
    }
  };

  const handleSeedWards = async () => {
    setSaving(true);
    try {
      const response = await bedAPI.seedWards();
      toast.success(response.data.message);
      fetchData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to seed wards'));
    } finally {
      setSaving(false);
    }
  };

  const handleBulkCreateBeds = async (wardId) => {
    setSaving(true);
    try {
      const response = await bedAPI.bulkCreateBeds(wardId, {
        room_prefix: 'R',
        beds_per_room: 4,
        num_rooms: 5
      });
      toast.success(response.data.message);
      fetchData();
      if (selectedWard) fetchWardBeds(selectedWard.id);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to create beds'));
    } finally {
      setSaving(false);
    }
  };

  const handleAdmit = async () => {
    if (!admitForm.patient_id || !admitForm.bed_id || !admitForm.admitting_diagnosis) {
      toast.error('Please fill in required fields');
      return;
    }
    
    setSaving(true);
    try {
      await bedAPI.createAdmission({
        ...admitForm,
        admitting_physician_id: user.id
      });
      toast.success('Patient admitted successfully');
      setAdmitDialogOpen(false);
      setAdmitForm({
        patient_id: '', bed_id: '', admitting_diagnosis: '',
        admitting_physician_id: '', admission_source: 'emergency',
        notes: '', isolation_required: false
      });
      fetchData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to admit patient'));
    } finally {
      setSaving(false);
    }
  };

  const handleTransfer = async () => {
    if (!transferForm.to_bed_id || !transferForm.transfer_reason) {
      toast.error('Please select destination bed and reason');
      return;
    }
    
    setSaving(true);
    try {
      await bedAPI.transferPatient(selectedAdmission.id, transferForm);
      toast.success('Patient transferred successfully');
      setTransferDialogOpen(false);
      setTransferForm({ to_bed_id: '', transfer_reason: '', notes: '' });
      fetchData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to transfer'));
    } finally {
      setSaving(false);
    }
  };

  const handleDischarge = async () => {
    if (!dischargeForm.discharge_diagnosis || !dischargeForm.discharge_disposition) {
      toast.error('Please fill in required fields');
      return;
    }
    
    setSaving(true);
    try {
      await bedAPI.dischargePatient(selectedAdmission.id, dischargeForm);
      toast.success('Patient discharged successfully');
      setDischargeDialogOpen(false);
      setDischargeForm({
        discharge_disposition: 'home', discharge_diagnosis: '',
        discharge_instructions: '', follow_up_required: true, follow_up_date: ''
      });
      fetchData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to discharge'));
    } finally {
      setSaving(false);
    }
  };

  const getBedStatusColor = (status) => {
    const colors = {
      available: 'bg-green-500',
      occupied: 'bg-red-500',
      reserved: 'bg-yellow-500',
      cleaning: 'bg-blue-500',
      maintenance: 'bg-gray-500',
      isolation: 'bg-purple-500'
    };
    return colors[status] || 'bg-gray-500';
  };

  const getOccupancyColor = (rate) => {
    if (rate >= 90) return 'text-red-600';
    if (rate >= 75) return 'text-amber-600';
    return 'text-green-600';
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Bed className="w-7 h-7 text-sky-600" />
            Bed Management
          </h1>
          <p className="text-slate-500 mt-1">Ward census and inpatient capacity management</p>
        </div>
        <div className="flex gap-2">
          {wards.length === 0 && (
            <Button onClick={handleSeedWards} disabled={saving} variant="outline">
              <Plus className="w-4 h-4 mr-2" /> Setup Default Wards
            </Button>
          )}
          <Button onClick={fetchData} variant="outline" className="gap-2">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card className="bg-gradient-to-br from-slate-50 to-slate-100 border-slate-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-600">Total Beds</p>
                <p className="text-3xl font-bold text-slate-800">{census.summary?.total_beds || 0}</p>
              </div>
              <Bed className="w-10 h-10 text-slate-400" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-700">Available</p>
                <p className="text-3xl font-bold text-green-800">{census.summary?.available || 0}</p>
              </div>
              <CheckCircle className="w-10 h-10 text-green-400" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-red-50 to-red-100 border-red-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-red-700">Occupied</p>
                <p className="text-3xl font-bold text-red-800">{census.summary?.occupied || 0}</p>
              </div>
              <Users className="w-10 h-10 text-red-400" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-700">Isolation</p>
                <p className="text-3xl font-bold text-purple-800">{census.summary?.isolation || 0}</p>
              </div>
              <AlertTriangle className="w-10 h-10 text-purple-400" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-sky-50 to-sky-100 border-sky-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-sky-700">Occupancy</p>
                <p className={`text-3xl font-bold ${getOccupancyColor(census.summary?.overall_occupancy)}`}>
                  {census.summary?.overall_occupancy || 0}%
                </p>
              </div>
              <Activity className="w-10 h-10 text-sky-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Critical Care Alert */}
      {census.critical_care && census.critical_care.available <= 2 && census.critical_care.total > 0 && (
        <Card className="bg-red-50 border-red-300">
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <Heart className="w-6 h-6 text-red-600" />
              <div>
                <p className="font-semibold text-red-800">Critical Care Capacity Alert</p>
                <p className="text-sm text-red-700">
                  Only {census.critical_care.available} ICU/CCU beds available out of {census.critical_care.total}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="census" className="gap-2">
            <Activity className="w-4 h-4" /> Ward Census
          </TabsTrigger>
          <TabsTrigger value="admissions" className="gap-2">
            <Users className="w-4 h-4" /> Current Admissions
          </TabsTrigger>
          <TabsTrigger value="beds" className="gap-2">
            <Bed className="w-4 h-4" /> Bed Map
          </TabsTrigger>
        </TabsList>

        {/* Ward Census Tab */}
        <TabsContent value="census" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Ward Census Overview</CardTitle>
              <CardDescription>Real-time bed availability by ward</CardDescription>
            </CardHeader>
            <CardContent>
              {census.wards?.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Building2 className="w-12 h-12 mx-auto mb-4 opacity-30" />
                  <p>No wards configured</p>
                  <Button onClick={handleSeedWards} className="mt-4" disabled={saving}>
                    <Plus className="w-4 h-4 mr-2" /> Setup Default Wards
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {census.wards?.map((ward) => (
                    <div key={ward.ward_id} className="border rounded-lg p-4 hover:bg-gray-50">
                      <div className="flex items-center justify-between mb-2">
                        <div>
                          <h4 className="font-medium">{ward.ward_name}</h4>
                          <p className="text-sm text-gray-500 capitalize">
                            {ward.ward_type?.replace(/_/g, ' ')} • Floor: {ward.floor || 'N/A'}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className={`text-lg font-bold ${getOccupancyColor(ward.occupancy_rate)}`}>
                            {ward.occupancy_rate}%
                          </p>
                          <p className="text-sm text-gray-500">
                            {ward.occupied}/{ward.total_beds} beds
                          </p>
                        </div>
                      </div>
                      <Progress value={ward.occupancy_rate} className="h-2" />
                      <div className="flex gap-4 mt-2 text-sm">
                        <span className="text-green-600">✓ {ward.available} available</span>
                        <span className="text-red-600">● {ward.occupied} occupied</span>
                        {ward.reserved > 0 && <span className="text-yellow-600">◐ {ward.reserved} reserved</span>}
                        {ward.isolation > 0 && <span className="text-purple-600">⚠ {ward.isolation} isolation</span>}
                      </div>
                      {ward.total_beds === 0 && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="mt-2"
                          onClick={() => handleBulkCreateBeds(ward.ward_id)}
                          disabled={saving}
                        >
                          <Plus className="w-4 h-4 mr-1" /> Add Beds
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Current Admissions Tab */}
        <TabsContent value="admissions" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Current Admissions</CardTitle>
                <CardDescription>Patients currently admitted</CardDescription>
              </div>
              <Button onClick={() => setAdmitDialogOpen(true)}>
                <Plus className="w-4 h-4 mr-2" /> Admit Patient
              </Button>
            </CardHeader>
            <CardContent className="p-0">
              {admissions.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Users className="w-12 h-12 mx-auto mb-4 opacity-30" />
                  <p>No current admissions</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Patient</TableHead>
                      <TableHead>Admission #</TableHead>
                      <TableHead>Ward / Bed</TableHead>
                      <TableHead>Diagnosis</TableHead>
                      <TableHead>Admitted</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {admissions.map((adm) => (
                      <TableRow key={adm.id}>
                        <TableCell>
                          <div>
                            <p className="font-medium">{adm.patient_name}</p>
                            <p className="text-sm text-gray-500">{adm.patient_mrn}</p>
                          </div>
                        </TableCell>
                        <TableCell className="font-mono text-sm">{adm.admission_number}</TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{adm.ward_name}</p>
                            <p className="text-sm text-gray-500">Bed: {adm.bed_number}</p>
                          </div>
                        </TableCell>
                        <TableCell className="max-w-xs truncate">{adm.admitting_diagnosis}</TableCell>
                        <TableCell className="text-sm text-gray-500">
                          {new Date(adm.admitted_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex gap-2 justify-end">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setSelectedAdmission(adm);
                                setTransferDialogOpen(true);
                              }}
                            >
                              <ArrowRightLeft className="w-4 h-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              className="text-red-600 hover:text-red-700"
                              onClick={() => {
                                setSelectedAdmission(adm);
                                setDischargeDialogOpen(true);
                              }}
                            >
                              <LogOut className="w-4 h-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Bed Map Tab */}
        <TabsContent value="beds" className="mt-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Ward List */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Wards</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="divide-y">
                  {wards.map((ward) => (
                    <button
                      key={ward.id}
                      className={`w-full p-3 text-left hover:bg-gray-50 ${selectedWard?.id === ward.id ? 'bg-sky-50 border-l-4 border-sky-500' : ''}`}
                      onClick={() => {
                        setSelectedWard(ward);
                        fetchWardBeds(ward.id);
                      }}
                    >
                      <p className="font-medium">{ward.name}</p>
                      <p className="text-sm text-gray-500">{ward.total_beds} beds</p>
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Bed Grid */}
            <Card className="md:col-span-3">
              <CardHeader>
                <CardTitle className="text-base">
                  {selectedWard ? selectedWard.name : 'Select a Ward'}
                </CardTitle>
                <div className="flex gap-4 text-sm">
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-green-500"></span> Available</span>
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-red-500"></span> Occupied</span>
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-yellow-500"></span> Reserved</span>
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-blue-500"></span> Cleaning</span>
                  <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-purple-500"></span> Isolation</span>
                </div>
              </CardHeader>
              <CardContent>
                {!selectedWard ? (
                  <div className="text-center py-8 text-gray-500">
                    <Bed className="w-12 h-12 mx-auto mb-4 opacity-30" />
                    <p>Select a ward to view beds</p>
                  </div>
                ) : beds.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Bed className="w-12 h-12 mx-auto mb-4 opacity-30" />
                    <p>No beds in this ward</p>
                    <Button className="mt-4" onClick={() => handleBulkCreateBeds(selectedWard.id)} disabled={saving}>
                      <Plus className="w-4 h-4 mr-2" /> Add Beds
                    </Button>
                  </div>
                ) : (
                  <div className="grid grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-2">
                    {beds.map((bed) => (
                      <button
                        key={bed.id}
                        className={`p-2 rounded-lg border text-center transition-all hover:scale-105 ${
                          bed.status === 'available' ? 'border-green-300 bg-green-50' :
                          bed.status === 'occupied' ? 'border-red-300 bg-red-50' :
                          bed.status === 'reserved' ? 'border-yellow-300 bg-yellow-50' :
                          bed.status === 'cleaning' ? 'border-blue-300 bg-blue-50' :
                          bed.status === 'isolation' ? 'border-purple-300 bg-purple-50' :
                          'border-gray-300 bg-gray-50'
                        }`}
                        onClick={() => {
                          setSelectedBed(bed);
                          if (bed.status === 'available') {
                            setAdmitForm({ ...admitForm, bed_id: bed.id });
                            setAdmitDialogOpen(true);
                          }
                        }}
                      >
                        <Bed className={`w-5 h-5 mx-auto mb-1 ${
                          bed.status === 'available' ? 'text-green-600' :
                          bed.status === 'occupied' ? 'text-red-600' :
                          bed.status === 'isolation' ? 'text-purple-600' :
                          'text-gray-600'
                        }`} />
                        <p className="text-xs font-medium truncate">{bed.bed_number}</p>
                      </button>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Admit Dialog */}
      <Dialog open={admitDialogOpen} onOpenChange={setAdmitDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Admit Patient</DialogTitle>
            <DialogDescription>Assign patient to a bed</DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Patient ID *</Label>
              <Input
                value={admitForm.patient_id}
                onChange={(e) => setAdmitForm({...admitForm, patient_id: e.target.value})}
                placeholder="Enter patient ID"
              />
            </div>
            <div className="space-y-2">
              <Label>Bed *</Label>
              <Select value={admitForm.bed_id} onValueChange={(v) => setAdmitForm({...admitForm, bed_id: v})}>
                <SelectTrigger>
                  <SelectValue placeholder="Select bed" />
                </SelectTrigger>
                <SelectContent>
                  {beds.filter(b => b.status === 'available').map(bed => (
                    <SelectItem key={bed.id} value={bed.id}>
                      {bed.bed_number} - {bed.room_number}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Admitting Diagnosis *</Label>
              <Textarea
                value={admitForm.admitting_diagnosis}
                onChange={(e) => setAdmitForm({...admitForm, admitting_diagnosis: e.target.value})}
                placeholder="Enter diagnosis..."
              />
            </div>
            <div className="space-y-2">
              <Label>Admission Source</Label>
              <Select value={admitForm.admission_source} onValueChange={(v) => setAdmitForm({...admitForm, admission_source: v})}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="emergency">Emergency</SelectItem>
                  <SelectItem value="direct">Direct Admission</SelectItem>
                  <SelectItem value="transfer">Transfer</SelectItem>
                  <SelectItem value="referral">Referral</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="isolation"
                checked={admitForm.isolation_required}
                onChange={(e) => setAdmitForm({...admitForm, isolation_required: e.target.checked})}
                className="rounded"
              />
              <Label htmlFor="isolation">Requires Isolation</Label>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setAdmitDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleAdmit} disabled={saving}>
              {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Admit Patient
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Transfer Dialog */}
      <Dialog open={transferDialogOpen} onOpenChange={setTransferDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Transfer Patient</DialogTitle>
            <DialogDescription>
              Transfer {selectedAdmission?.patient_name} to a different bed
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Destination Bed *</Label>
              <Select value={transferForm.to_bed_id} onValueChange={(v) => setTransferForm({...transferForm, to_bed_id: v})}>
                <SelectTrigger>
                  <SelectValue placeholder="Select bed" />
                </SelectTrigger>
                <SelectContent>
                  {beds.filter(b => b.status === 'available').map(bed => (
                    <SelectItem key={bed.id} value={bed.id}>
                      {bed.ward_name} - {bed.bed_number}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Transfer Reason *</Label>
              <Textarea
                value={transferForm.transfer_reason}
                onChange={(e) => setTransferForm({...transferForm, transfer_reason: e.target.value})}
                placeholder="Reason for transfer..."
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setTransferDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleTransfer} disabled={saving}>
              {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Transfer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Discharge Dialog */}
      <Dialog open={dischargeDialogOpen} onOpenChange={setDischargeDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Discharge Patient</DialogTitle>
            <DialogDescription>
              Discharge {selectedAdmission?.patient_name}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Discharge Disposition *</Label>
              <Select value={dischargeForm.discharge_disposition} onValueChange={(v) => setDischargeForm({...dischargeForm, discharge_disposition: v})}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="home">Home</SelectItem>
                  <SelectItem value="transfer">Transfer to Another Facility</SelectItem>
                  <SelectItem value="rehab">Rehabilitation</SelectItem>
                  <SelectItem value="SNF">Skilled Nursing Facility</SelectItem>
                  <SelectItem value="AMA">Against Medical Advice</SelectItem>
                  <SelectItem value="deceased">Deceased</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Discharge Diagnosis *</Label>
              <Textarea
                value={dischargeForm.discharge_diagnosis}
                onChange={(e) => setDischargeForm({...dischargeForm, discharge_diagnosis: e.target.value})}
                placeholder="Final diagnosis..."
              />
            </div>
            <div className="space-y-2">
              <Label>Discharge Instructions</Label>
              <Textarea
                value={dischargeForm.discharge_instructions}
                onChange={(e) => setDischargeForm({...dischargeForm, discharge_instructions: e.target.value})}
                placeholder="Instructions for patient..."
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="followup"
                checked={dischargeForm.follow_up_required}
                onChange={(e) => setDischargeForm({...dischargeForm, follow_up_required: e.target.checked})}
                className="rounded"
              />
              <Label htmlFor="followup">Follow-up Required</Label>
            </div>
            {dischargeForm.follow_up_required && (
              <div className="space-y-2">
                <Label>Follow-up Date</Label>
                <Input
                  type="date"
                  value={dischargeForm.follow_up_date}
                  onChange={(e) => setDischargeForm({...dischargeForm, follow_up_date: e.target.value})}
                />
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDischargeDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleDischarge} disabled={saving} className="bg-red-600 hover:bg-red-700">
              {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Discharge
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
