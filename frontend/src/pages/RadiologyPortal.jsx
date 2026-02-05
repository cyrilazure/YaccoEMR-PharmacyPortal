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
  Image, RefreshCw, Search, CheckCircle, AlertCircle,
  Clock, Play, FileText, Eye, Calendar, Upload,
  AlertTriangle, Loader2, Scan, Monitor
} from 'lucide-react';
import api from '@/lib/api';

const radiologyAPI = {
  getQueue: (params) => api.get('/radiology/orders/queue', { params }),
  updateOrder: (id, data) => api.put(`/radiology/orders/${id}`, data),
  createResult: (data) => api.post('/radiology/results/create', data),
  getModalities: () => api.get('/radiology/modalities'),
  getStudyTypes: (modality) => api.get('/radiology/study-types', { params: { modality } }),
};

export default function RadiologyPortal() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [orders, setOrders] = useState([]);
  const [stats, setStats] = useState({});
  const [activeTab, setActiveTab] = useState('queue');
  const [searchQuery, setSearchQuery] = useState('');
  const [modalityFilter, setModalityFilter] = useState('all');
  const [priorityFilter, setPriorityFilter] = useState('all');
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [scheduleDialogOpen, setScheduleDialogOpen] = useState(false);
  const [resultDialogOpen, setResultDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  
  // Role-based permissions
  const isRadiologist = user?.role === 'radiologist';
  const isRadiologyStaff = user?.role === 'radiology_staff';
  const canCreateReports = isRadiologist; // Only radiologists can create reports
  const canViewFullDetails = isRadiologist; // Only radiologists can view full patient clinical details
  
  // Schedule form
  const [scheduleForm, setScheduleForm] = useState({
    scheduled_date: '',
    scheduled_time: '',
    room: ''
  });
  
  // Result form
  const [resultForm, setResultForm] = useState({
    findings: '',
    impression: '',
    recommendations: '',
    critical_finding: false
  });

  const fetchOrders = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (modalityFilter && modalityFilter !== 'all') params.modality = modalityFilter;
      if (priorityFilter && priorityFilter !== 'all') params.priority = priorityFilter;
      
      const response = await radiologyAPI.getQueue(params);
      setOrders(response.data.orders || []);
      setStats(response.data.stats || {});
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to load orders'));
    } finally {
      setLoading(false);
    }
  }, [modalityFilter, priorityFilter]);

  useEffect(() => {
    fetchOrders();
    const interval = setInterval(fetchOrders, 30000);
    return () => clearInterval(interval);
  }, [fetchOrders]);

  const handleSchedule = async () => {
    if (!scheduleForm.scheduled_date || !scheduleForm.scheduled_time) {
      toast.error('Please select date and time');
      return;
    }
    
    setSaving(true);
    try {
      await radiologyAPI.updateOrder(selectedOrder.id, {
        status: 'scheduled',
        ...scheduleForm
      });
      toast.success('Study scheduled successfully');
      setScheduleDialogOpen(false);
      setScheduleForm({ scheduled_date: '', scheduled_time: '', room: '' });
      fetchOrders();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to schedule'));
    } finally {
      setSaving(false);
    }
  };

  const handleStartStudy = async (order) => {
    setSaving(true);
    try {
      await radiologyAPI.updateOrder(order.id, { status: 'in_progress' });
      toast.success('Study started');
      fetchOrders();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to start study'));
    } finally {
      setSaving(false);
    }
  };

  const handleCompleteStudy = async (order) => {
    setSaving(true);
    try {
      await radiologyAPI.updateOrder(order.id, { status: 'completed' });
      toast.success('Study marked as completed');
      fetchOrders();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to complete'));
    } finally {
      setSaving(false);
    }
  };

  const handleSubmitResult = async () => {
    if (!resultForm.findings || !resultForm.impression) {
      toast.error('Findings and impression are required');
      return;
    }
    
    setSaving(true);
    try {
      await radiologyAPI.createResult({
        order_id: selectedOrder.id,
        ...resultForm,
        images_available: true
      });
      toast.success('Radiology report submitted');
      setResultDialogOpen(false);
      setResultForm({ findings: '', impression: '', recommendations: '', critical_finding: false });
      fetchOrders();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to submit report'));
    } finally {
      setSaving(false);
    }
  };

  const getStatusBadge = (status) => {
    const colors = {
      ordered: 'bg-yellow-100 text-yellow-800',
      scheduled: 'bg-blue-100 text-blue-800',
      in_progress: 'bg-purple-100 text-purple-800',
      completed: 'bg-green-100 text-green-800',
      reported: 'bg-emerald-100 text-emerald-800',
      cancelled: 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getPriorityBadge = (priority) => {
    const colors = {
      routine: 'bg-gray-100 text-gray-600',
      urgent: 'bg-amber-100 text-amber-700',
      stat: 'bg-red-100 text-red-700',
      emergency: 'bg-red-200 text-red-800'
    };
    return colors[priority] || 'bg-gray-100 text-gray-600';
  };

  const getModalityIcon = (modality) => {
    const icons = {
      xray: '🩻',
      ct: '🔬',
      mri: '🧲',
      ultrasound: '📡',
      mammography: '🔍'
    };
    return icons[modality] || '📷';
  };

  const filteredOrders = orders.filter(order => {
    const matchesSearch = !searchQuery || 
      order.patient_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      order.accession_number?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      order.patient_mrn?.toLowerCase().includes(searchQuery.toLowerCase());
    
    return matchesSearch;
  });

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Scan className="w-7 h-7 text-purple-600" />
            Radiology Department
          </h1>
          <p className="text-slate-500 mt-1">Manage imaging orders and reports</p>
        </div>
        <Button onClick={fetchOrders} variant="outline" className="gap-2">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
        <Card className="bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <p className="text-sm font-medium text-yellow-700">Ordered</p>
              <p className="text-2xl font-bold text-yellow-800">{stats.ordered || 0}</p>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <p className="text-sm font-medium text-blue-700">Scheduled</p>
              <p className="text-2xl font-bold text-blue-800">{stats.scheduled || 0}</p>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <p className="text-sm font-medium text-purple-700">In Progress</p>
              <p className="text-2xl font-bold text-purple-800">{stats.in_progress || 0}</p>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <p className="text-sm font-medium text-green-700">Completed</p>
              <p className="text-2xl font-bold text-green-800">{stats.completed || 0}</p>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-emerald-50 to-emerald-100 border-emerald-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <p className="text-sm font-medium text-emerald-700">Reported</p>
              <p className="text-2xl font-bold text-emerald-800">{stats.reported || 0}</p>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-red-50 to-red-100 border-red-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <p className="text-sm font-medium text-red-700">STAT Pending</p>
              <p className="text-2xl font-bold text-red-800">{stats.stat_pending || 0}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            placeholder="Search by patient, accession number..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={modalityFilter} onValueChange={setModalityFilter}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="All Modalities" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Modalities</SelectItem>
            <SelectItem value="xray">X-Ray</SelectItem>
            <SelectItem value="ct">CT Scan</SelectItem>
            <SelectItem value="mri">MRI</SelectItem>
            <SelectItem value="ultrasound">Ultrasound</SelectItem>
            <SelectItem value="mammography">Mammography</SelectItem>
          </SelectContent>
        </Select>
        <Select value={priorityFilter} onValueChange={setPriorityFilter}>
          <SelectTrigger className="w-32">
            <SelectValue placeholder="All Priority" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Priority</SelectItem>
            <SelectItem value="stat">STAT</SelectItem>
            <SelectItem value="urgent">Urgent</SelectItem>
            <SelectItem value="routine">Routine</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Orders Table */}
      <Card>
        <CardHeader>
          <CardTitle>Imaging Orders Queue</CardTitle>
          <CardDescription>Active imaging orders requiring attention</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
            </div>
          ) : filteredOrders.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Scan className="w-12 h-12 mx-auto mb-4 opacity-30" />
              <p>No orders found</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Accession</TableHead>
                  <TableHead>Patient</TableHead>
                  <TableHead>Study</TableHead>
                  <TableHead>Modality</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Ordering Physician</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredOrders.map((order) => (
                  <TableRow key={order.id} className={order.priority === 'stat' ? 'bg-red-50' : 'hover:bg-gray-50'}>
                    <TableCell className="font-mono text-sm">{order.accession_number}</TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">{order.patient_name}</p>
                        <p className="text-sm text-gray-500">{order.patient_mrn}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div>
                        <p className="font-medium">{order.study_type}</p>
                        <p className="text-sm text-gray-500">{order.body_part}</p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-lg mr-2">{getModalityIcon(order.modality)}</span>
                      <Badge variant="outline" className="capitalize">{order.modality}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={getPriorityBadge(order.priority)}>
                        {order.priority?.toUpperCase()}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={getStatusBadge(order.status)}>
                        {order.status?.replace(/_/g, ' ')}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm">{order.ordering_physician}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex gap-2 justify-end">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedOrder(order);
                            setViewDialogOpen(true);
                          }}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        
                        {order.status === 'ordered' && (
                          <Button
                            size="sm"
                            className="bg-blue-600 hover:bg-blue-700"
                            onClick={() => {
                              setSelectedOrder(order);
                              setScheduleDialogOpen(true);
                            }}
                          >
                            <Calendar className="w-4 h-4 mr-1" /> Schedule
                          </Button>
                        )}
                        
                        {order.status === 'scheduled' && (
                          <Button
                            size="sm"
                            className="bg-purple-600 hover:bg-purple-700"
                            onClick={() => handleStartStudy(order)}
                          >
                            <Play className="w-4 h-4 mr-1" /> Start
                          </Button>
                        )}
                        
                        {order.status === 'in_progress' && (
                          <Button
                            size="sm"
                            className="bg-green-600 hover:bg-green-700"
                            onClick={() => handleCompleteStudy(order)}
                          >
                            <CheckCircle className="w-4 h-4 mr-1" /> Complete
                          </Button>
                        )}
                        
                        {order.status === 'completed' && (
                          <Button
                            size="sm"
                            className="bg-emerald-600 hover:bg-emerald-700"
                            onClick={() => {
                              setSelectedOrder(order);
                              setResultDialogOpen(true);
                            }}
                          >
                            <FileText className="w-4 h-4 mr-1" /> Report
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

      {/* View Order Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Order Details</DialogTitle>
            <DialogDescription>{selectedOrder?.accession_number}</DialogDescription>
          </DialogHeader>
          
          {selectedOrder && (
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-medium text-gray-700 mb-2">Patient</h4>
                  <p className="font-medium">{selectedOrder.patient_name}</p>
                  <p className="text-sm text-gray-500">MRN: {selectedOrder.patient_mrn}</p>
                  <p className="text-sm text-gray-500">DOB: {selectedOrder.patient_dob}</p>
                </div>
                <div className="bg-purple-50 rounded-lg p-4">
                  <h4 className="font-medium text-purple-700 mb-2">Study</h4>
                  <p className="font-medium">{selectedOrder.study_type}</p>
                  <p className="text-sm text-gray-500">Modality: {selectedOrder.modality}</p>
                  <p className="text-sm text-gray-500">Body Part: {selectedOrder.body_part}</p>
                </div>
              </div>
              
              <div className="bg-blue-50 rounded-lg p-4">
                <h4 className="font-medium text-blue-700 mb-2">Clinical Indication</h4>
                <p className="text-sm">{selectedOrder.clinical_indication}</p>
              </div>
              
              {selectedOrder.relevant_history && (
                <div className="bg-yellow-50 rounded-lg p-4">
                  <h4 className="font-medium text-yellow-700 mb-2">Relevant History</h4>
                  <p className="text-sm">{selectedOrder.relevant_history}</p>
                </div>
              )}
              
              {selectedOrder.special_instructions && (
                <div className="bg-orange-50 rounded-lg p-4">
                  <h4 className="font-medium text-orange-700 mb-2">Special Instructions</h4>
                  <p className="text-sm">{selectedOrder.special_instructions}</p>
                </div>
              )}
              
              <div className="flex gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Contrast:</span>
                  <Badge variant="outline" className="ml-2">
                    {selectedOrder.contrast_required ? 'Required' : 'Not Required'}
                  </Badge>
                </div>
                <div>
                  <span className="text-gray-500">Laterality:</span>
                  <span className="ml-2 capitalize">{selectedOrder.laterality}</span>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Schedule Dialog */}
      <Dialog open={scheduleDialogOpen} onOpenChange={setScheduleDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Schedule Imaging Study</DialogTitle>
            <DialogDescription>
              {selectedOrder?.study_type} for {selectedOrder?.patient_name}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Date *</Label>
                <Input
                  type="date"
                  value={scheduleForm.scheduled_date}
                  onChange={(e) => setScheduleForm({...scheduleForm, scheduled_date: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <Label>Time *</Label>
                <Input
                  type="time"
                  value={scheduleForm.scheduled_time}
                  onChange={(e) => setScheduleForm({...scheduleForm, scheduled_time: e.target.value})}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Room</Label>
              <Input
                value={scheduleForm.room}
                onChange={(e) => setScheduleForm({...scheduleForm, room: e.target.value})}
                placeholder="e.g., Room 101, CT Suite A"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setScheduleDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSchedule} disabled={saving}>
              {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Schedule
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Result/Report Dialog */}
      <Dialog open={resultDialogOpen} onOpenChange={setResultDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Radiology Report
            </DialogTitle>
            <DialogDescription>
              {selectedOrder?.accession_number} - {selectedOrder?.study_type}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Findings *</Label>
              <Textarea
                value={resultForm.findings}
                onChange={(e) => setResultForm({...resultForm, findings: e.target.value})}
                placeholder="Describe the imaging findings..."
                rows={4}
              />
            </div>
            
            <div className="space-y-2">
              <Label>Impression *</Label>
              <Textarea
                value={resultForm.impression}
                onChange={(e) => setResultForm({...resultForm, impression: e.target.value})}
                placeholder="Summary impression..."
                rows={3}
              />
            </div>
            
            <div className="space-y-2">
              <Label>Recommendations</Label>
              <Textarea
                value={resultForm.recommendations}
                onChange={(e) => setResultForm({...resultForm, recommendations: e.target.value})}
                placeholder="Follow-up recommendations..."
                rows={2}
              />
            </div>
            
            <div className="flex items-center gap-2 p-3 bg-red-50 rounded-lg">
              <input
                type="checkbox"
                id="critical"
                checked={resultForm.critical_finding}
                onChange={(e) => setResultForm({...resultForm, critical_finding: e.target.checked})}
                className="rounded border-red-300"
              />
              <Label htmlFor="critical" className="text-red-700 font-medium">
                <AlertTriangle className="w-4 h-4 inline mr-1" />
                Critical Finding - Requires immediate notification
              </Label>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setResultDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmitResult} disabled={saving} className="bg-emerald-600 hover:bg-emerald-700">
              {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Submit Report
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
