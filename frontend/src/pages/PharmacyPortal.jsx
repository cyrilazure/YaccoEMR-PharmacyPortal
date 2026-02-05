import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/lib/auth';
import { getErrorMessage } from '@/lib/utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Textarea } from '@/components/ui/textarea';
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
import { toast } from 'sonner';
import {
  Pill, RefreshCw, Search, CheckCircle, AlertCircle,
  Clock, User, Package, FileText, Eye, Check, X,
  AlertTriangle, Loader2, ChevronRight
} from 'lucide-react';
import api from '@/lib/api';

const prescriptionAPI = {
  getQueue: (status) => api.get('/prescriptions/pharmacy/queue', { params: { status } }),
  updateStatus: (id, data) => api.put(`/prescriptions/${id}/status`, data),
  getPatientPrescriptions: (patientId) => api.get(`/prescriptions/patient/${patientId}`),
};

export default function PharmacyPortal() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [prescriptions, setPrescriptions] = useState([]);
  const [stats, setStats] = useState({});
  const [activeTab, setActiveTab] = useState('pending');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRx, setSelectedRx] = useState(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [dispenseDialogOpen, setDispenseDialogOpen] = useState(false);
  const [pharmacistNotes, setPharmacistNotes] = useState('');
  const [saving, setSaving] = useState(false);

  const fetchPrescriptions = useCallback(async () => {
    setLoading(true);
    try {
      const response = await prescriptionAPI.getQueue();
      setPrescriptions(response.data.prescriptions || []);
      setStats(response.data.stats || {});
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to load prescriptions'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPrescriptions();
    const interval = setInterval(fetchPrescriptions, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [fetchPrescriptions]);

  const handleUpdateStatus = async (rxId, newStatus) => {
    setSaving(true);
    try {
      await prescriptionAPI.updateStatus(rxId, {
        status: newStatus,
        pharmacist_notes: pharmacistNotes
      });
      toast.success(`Prescription ${newStatus.replace('_', ' ')}`);
      setDispenseDialogOpen(false);
      setViewDialogOpen(false);
      setPharmacistNotes('');
      fetchPrescriptions();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to update prescription'));
    } finally {
      setSaving(false);
    }
  };

  const getStatusBadge = (status) => {
    const colors = {
      pending_verification: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-blue-100 text-blue-800',
      dispensed: 'bg-green-100 text-green-800',
      partially_dispensed: 'bg-orange-100 text-orange-800',
      ready_for_pickup: 'bg-purple-100 text-purple-800',
      picked_up: 'bg-gray-100 text-gray-800',
      cancelled: 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getPriorityBadge = (priority) => {
    const colors = {
      routine: 'bg-gray-100 text-gray-600',
      urgent: 'bg-amber-100 text-amber-700',
      stat: 'bg-red-100 text-red-700'
    };
    return colors[priority] || 'bg-gray-100 text-gray-600';
  };

  const filteredPrescriptions = prescriptions.filter(rx => {
    const matchesSearch = !searchQuery || 
      rx.patient_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      rx.rx_number?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      rx.patient_mrn?.toLowerCase().includes(searchQuery.toLowerCase());
    
    if (activeTab === 'pending') {
      return matchesSearch && rx.status === 'pending_verification';
    } else if (activeTab === 'approved') {
      return matchesSearch && rx.status === 'approved';
    } else if (activeTab === 'dispensed') {
      return matchesSearch && ['dispensed', 'ready_for_pickup', 'picked_up'].includes(rx.status);
    }
    return matchesSearch;
  });

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Pill className="w-7 h-7 text-emerald-600" />
            Pharmacy Portal
          </h1>
          <p className="text-slate-500 mt-1">Manage and dispense electronic prescriptions</p>
        </div>
        <Button onClick={fetchPrescriptions} variant="outline" className="gap-2">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-yellow-700">Pending Verification</p>
                <p className="text-3xl font-bold text-yellow-800">{stats.pending || 0}</p>
              </div>
              <Clock className="w-10 h-10 text-yellow-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-700">Approved</p>
                <p className="text-3xl font-bold text-blue-800">{stats.approved || 0}</p>
              </div>
              <CheckCircle className="w-10 h-10 text-blue-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-700">Dispensed</p>
                <p className="text-3xl font-bold text-green-800">{stats.dispensed || 0}</p>
              </div>
              <Package className="w-10 h-10 text-green-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-700">Ready for Pickup</p>
                <p className="text-3xl font-bold text-purple-800">{stats.ready || 0}</p>
              </div>
              <User className="w-10 h-10 text-purple-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search Bar */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <Input
          placeholder="Search by patient name, MRN, or Rx number..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-3 w-full max-w-md">
          <TabsTrigger value="pending" className="gap-2">
            <Clock className="w-4 h-4" /> Pending
            {stats.pending > 0 && <Badge className="ml-1 bg-yellow-500">{stats.pending}</Badge>}
          </TabsTrigger>
          <TabsTrigger value="approved" className="gap-2">
            <CheckCircle className="w-4 h-4" /> Approved
            {stats.approved > 0 && <Badge className="ml-1 bg-blue-500">{stats.approved}</Badge>}
          </TabsTrigger>
          <TabsTrigger value="dispensed" className="gap-2">
            <Package className="w-4 h-4" /> Dispensed
          </TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="mt-4">
          <Card>
            <CardContent className="p-0">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
                </div>
              ) : filteredPrescriptions.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <Pill className="w-12 h-12 mx-auto mb-4 opacity-30" />
                  <p>No prescriptions found</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Rx Number</TableHead>
                      <TableHead>Patient</TableHead>
                      <TableHead>Prescriber</TableHead>
                      <TableHead>Medications</TableHead>
                      <TableHead>Priority</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredPrescriptions.map((rx) => (
                      <TableRow key={rx.id} className="hover:bg-gray-50">
                        <TableCell className="font-mono font-medium">{rx.rx_number}</TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{rx.patient_name}</p>
                            <p className="text-sm text-gray-500">{rx.patient_mrn}</p>
                          </div>
                        </TableCell>
                        <TableCell>{rx.prescriber_name}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{rx.medications?.length || 0} items</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge className={getPriorityBadge(rx.priority)}>
                            {rx.priority?.toUpperCase()}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge className={getStatusBadge(rx.status)}>
                            {rx.status?.replace(/_/g, ' ')}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm text-gray-500">
                          {new Date(rx.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex gap-2 justify-end">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setSelectedRx(rx);
                                setViewDialogOpen(true);
                              }}
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            {rx.status === 'pending_verification' && (
                              <Button
                                size="sm"
                                className="bg-emerald-600 hover:bg-emerald-700"
                                onClick={() => handleUpdateStatus(rx.id, 'approved')}
                              >
                                <Check className="w-4 h-4" />
                              </Button>
                            )}
                            {rx.status === 'approved' && (
                              <Button
                                size="sm"
                                className="bg-blue-600 hover:bg-blue-700"
                                onClick={() => {
                                  setSelectedRx(rx);
                                  setDispenseDialogOpen(true);
                                }}
                              >
                                Dispense
                              </Button>
                            )}
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
      </Tabs>

      {/* View Prescription Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Prescription Details
            </DialogTitle>
            <DialogDescription>
              {selectedRx?.rx_number}
            </DialogDescription>
          </DialogHeader>
          
          {selectedRx && (
            <div className="space-y-4 py-4">
              {/* Patient Info */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-700 mb-2">Patient Information</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Name:</span>
                    <span className="ml-2 font-medium">{selectedRx.patient_name}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">MRN:</span>
                    <span className="ml-2 font-mono">{selectedRx.patient_mrn}</span>
                  </div>
                </div>
              </div>

              {/* Prescriber Info */}
              <div className="bg-blue-50 rounded-lg p-4">
                <h4 className="font-medium text-blue-700 mb-2">Prescriber Information</h4>
                <div className="text-sm">
                  <span className="text-blue-600">Prescriber:</span>
                  <span className="ml-2 font-medium">{selectedRx.prescriber_name}</span>
                </div>
              </div>

              {/* Medications */}
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Medications</h4>
                <div className="space-y-2">
                  {selectedRx.medications?.map((med, idx) => (
                    <div key={idx} className="border rounded-lg p-3 bg-white">
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="font-medium text-gray-900">{med.medication_name}</p>
                          <p className="text-sm text-gray-500">
                            {med.dosage} {med.dosage_unit} • {med.frequency} • {med.route}
                          </p>
                          <p className="text-sm text-gray-500">
                            Duration: {med.duration_value} {med.duration_unit} • Qty: {med.quantity}
                          </p>
                          {med.special_instructions && (
                            <p className="text-sm text-amber-600 mt-1">
                              <AlertTriangle className="w-3 h-3 inline mr-1" />
                              {med.special_instructions}
                            </p>
                          )}
                        </div>
                        <Badge variant="outline">#{idx + 1}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Clinical Notes */}
              {selectedRx.clinical_notes && (
                <div className="bg-yellow-50 rounded-lg p-4">
                  <h4 className="font-medium text-yellow-700 mb-2">Clinical Notes</h4>
                  <p className="text-sm text-gray-700">{selectedRx.clinical_notes}</p>
                </div>
              )}

              {/* Diagnosis */}
              {selectedRx.diagnosis && (
                <div>
                  <span className="text-sm text-gray-500">Diagnosis:</span>
                  <span className="ml-2 text-sm font-medium">{selectedRx.diagnosis}</span>
                </div>
              )}
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setViewDialogOpen(false)}>
              Close
            </Button>
            {selectedRx?.status === 'pending_verification' && (
              <>
                <Button
                  variant="destructive"
                  onClick={() => handleUpdateStatus(selectedRx.id, 'cancelled')}
                  disabled={saving}
                >
                  <X className="w-4 h-4 mr-2" /> Reject
                </Button>
                <Button
                  className="bg-emerald-600 hover:bg-emerald-700"
                  onClick={() => handleUpdateStatus(selectedRx.id, 'approved')}
                  disabled={saving}
                >
                  <Check className="w-4 h-4 mr-2" /> Approve
                </Button>
              </>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dispense Dialog */}
      <Dialog open={dispenseDialogOpen} onOpenChange={setDispenseDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Package className="w-5 h-5 text-blue-600" />
              Dispense Prescription
            </DialogTitle>
            <DialogDescription>
              {selectedRx?.rx_number} - {selectedRx?.patient_name}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Pharmacist Notes (Optional)</Label>
              <Textarea
                value={pharmacistNotes}
                onChange={(e) => setPharmacistNotes(e.target.value)}
                placeholder="Add any notes about dispensing..."
                rows={3}
              />
            </div>

            <div className="bg-blue-50 rounded-lg p-4">
              <h4 className="font-medium text-blue-700 mb-2">Medications to Dispense</h4>
              <ul className="text-sm space-y-1">
                {selectedRx?.medications?.map((med, idx) => (
                  <li key={idx} className="flex items-center gap-2">
                    <Pill className="w-4 h-4 text-blue-500" />
                    {med.medication_name} - {med.dosage} {med.dosage_unit} x {med.quantity}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDispenseDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              className="bg-green-600 hover:bg-green-700"
              onClick={() => handleUpdateStatus(selectedRx?.id, 'dispensed')}
              disabled={saving}
            >
              {saving ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Check className="w-4 h-4 mr-2" />
              )}
              Confirm Dispense
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
