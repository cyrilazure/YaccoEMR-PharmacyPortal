import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/lib/auth';
import { getErrorMessage, cn } from '@/lib/utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Switch } from '@/components/ui/switch';
import { Checkbox } from '@/components/ui/checkbox';
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
  Clock, Play, FileText, Eye, Calendar, Upload, User,
  AlertTriangle, Loader2, Scan, Monitor, ZoomIn, ZoomOut,
  RotateCw, Move, Maximize2, Minimize2, Contrast, Ruler,
  PenTool, Save, Send, MessageSquare, Phone, History,
  ChevronRight, Activity, Clipboard, Plus, Edit2, Check, X, Mic
} from 'lucide-react';
import api from '@/lib/api';
import VoiceDictation from '@/components/VoiceDictation';

const radiologyAPI = {
  // Queue and Orders
  getQueue: (params) => api.get('/radiology/orders/queue', { params }),
  getWorklist: (params) => api.get('/radiology/worklist', { params }),
  updateOrder: (id, data) => api.put(`/radiology/orders/${id}`, data),
  assignOrder: (id, radiologistId) => api.post(`/radiology/orders/${id}/assign`, null, { params: { radiologist_id: radiologistId } }),
  getOrderTimeline: (id) => api.get(`/radiology/orders/${id}/timeline`),
  
  // Dashboard
  getDashboard: () => api.get('/radiology/dashboard/radiologist'),
  
  // Results (legacy)
  createResult: (data) => api.post('/radiology/results/create', data),
  
  // Structured Reports
  createReport: (data) => api.post('/radiology/reports/create', data),
  updateReport: (id, data) => api.put(`/radiology/reports/${id}`, data),
  finalizeReport: (id) => api.post(`/radiology/reports/${id}/finalize`),
  getReport: (id) => api.get(`/radiology/reports/${id}`),
  getPatientReports: (patientId) => api.get(`/radiology/reports/patient/${patientId}`),
  communicateCritical: (id, data) => api.post(`/radiology/reports/${id}/communicate-critical`, null, { params: data }),
  
  // Notes
  createNote: (data) => api.post('/radiology/notes/create', data),
  getPatientNotes: (patientId) => api.get(`/radiology/notes/patient/${patientId}`),
  
  // Modalities
  getModalities: () => api.get('/radiology/modalities'),
  getStudyTypes: (modality) => api.get('/radiology/study-types', { params: { modality } }),
};

// Image Viewer Placeholder Component
function ImageViewer({ order, onClose }) {
  const [zoom, setZoom] = useState(100);
  const [contrast, setContrast] = useState(100);
  const [rotation, setRotation] = useState(0);
  
  return (
    <div className="fixed inset-0 bg-black z-50 flex flex-col">
      {/* Viewer Header */}
      <div className="h-14 bg-slate-900 flex items-center justify-between px-4 border-b border-slate-700">
        <div className="flex items-center gap-4">
          <Monitor className="w-5 h-5 text-purple-400" />
          <div>
            <p className="text-white font-medium">{order?.patient_name}</p>
            <p className="text-slate-400 text-sm">{order?.study_type} - {order?.accession_number}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge className="bg-purple-600">{order?.modality?.toUpperCase()}</Badge>
          <Button variant="ghost" size="sm" onClick={onClose} className="text-white hover:bg-slate-800">
            <X className="w-5 h-5" />
          </Button>
        </div>
      </div>
      
      {/* Toolbar */}
      <div className="h-12 bg-slate-800 flex items-center gap-2 px-4">
        <Button variant="ghost" size="sm" onClick={() => setZoom(z => Math.min(z + 25, 400))} className="text-slate-300 hover:text-white hover:bg-slate-700">
          <ZoomIn className="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="sm" onClick={() => setZoom(z => Math.max(z - 25, 25))} className="text-slate-300 hover:text-white hover:bg-slate-700">
          <ZoomOut className="w-4 h-4" />
        </Button>
        <span className="text-slate-400 text-sm px-2">{zoom}%</span>
        <Separator orientation="vertical" className="h-6 bg-slate-600" />
        <Button variant="ghost" size="sm" onClick={() => setRotation(r => (r + 90) % 360)} className="text-slate-300 hover:text-white hover:bg-slate-700">
          <RotateCw className="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="sm" className="text-slate-300 hover:text-white hover:bg-slate-700">
          <Move className="w-4 h-4" />
        </Button>
        <Separator orientation="vertical" className="h-6 bg-slate-600" />
        <Button variant="ghost" size="sm" onClick={() => setContrast(c => Math.min(c + 20, 200))} className="text-slate-300 hover:text-white hover:bg-slate-700">
          <Contrast className="w-4 h-4" />
        </Button>
        <span className="text-slate-400 text-sm px-2">W/L: {contrast}</span>
        <Separator orientation="vertical" className="h-6 bg-slate-600" />
        <Button variant="ghost" size="sm" className="text-slate-300 hover:text-white hover:bg-slate-700">
          <Ruler className="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="sm" className="text-slate-300 hover:text-white hover:bg-slate-700">
          <PenTool className="w-4 h-4" />
        </Button>
      </div>
      
      {/* Main Viewer Area */}
      <div className="flex-1 flex items-center justify-center bg-black">
        <div 
          className="relative border border-slate-700 rounded"
          style={{ 
            transform: `scale(${zoom/100}) rotate(${rotation}deg)`,
            filter: `contrast(${contrast}%)`
          }}
        >
          {/* Placeholder Image */}
          <div className="w-[600px] h-[500px] bg-gradient-to-br from-slate-800 to-slate-900 flex flex-col items-center justify-center">
            <Scan className="w-24 h-24 text-slate-600 mb-4" />
            <p className="text-slate-400 text-lg">PACS/DICOM Viewer Placeholder</p>
            <p className="text-slate-500 text-sm mt-2">Study: {order?.study_type}</p>
            <p className="text-slate-500 text-sm">Body Part: {order?.body_part}</p>
            <p className="text-slate-600 text-xs mt-4">Connect to your PACS server for real images</p>
          </div>
        </div>
      </div>
      
      {/* Footer with study info */}
      <div className="h-10 bg-slate-900 flex items-center justify-between px-4 text-xs text-slate-400">
        <span>Patient: {order?.patient_name} | MRN: {order?.patient_mrn} | DOB: {order?.patient_dob}</span>
        <span>Ordered by: {order?.ordering_physician} | {new Date(order?.created_at).toLocaleString()}</span>
      </div>
    </div>
  );
}

// Structured Report Dialog Component
function StructuredReportDialog({ open, onOpenChange, order, onSubmit }) {
  const [saving, setSaving] = useState(false);
  const [reportForm, setReportForm] = useState({
    study_quality: 'diagnostic',
    comparison_studies: '',
    technique: '',
    clinical_indication: order?.clinical_indication || '',
    clinical_history: order?.relevant_history || '',
    findings_text: '',
    findings_sections: [],
    impression: '',
    differential_diagnosis: [],
    recommendations: '',
    follow_up: '',
    critical_finding: false,
    critical_finding_details: '',
    status: 'draft'
  });
  
  useEffect(() => {
    if (order) {
      setReportForm(prev => ({
        ...prev,
        clinical_indication: order.clinical_indication || '',
        clinical_history: order.relevant_history || ''
      }));
    }
  }, [order]);
  
  const handleSubmit = async (finalizeNow = false) => {
    if (!reportForm.findings_text || !reportForm.impression) {
      toast.error('Findings and Impression are required');
      return;
    }
    
    setSaving(true);
    try {
      await onSubmit({
        ...reportForm,
        order_id: order.id,
        status: finalizeNow ? 'finalized' : 'draft'
      });
      toast.success(finalizeNow ? 'Report finalized' : 'Report saved as draft');
      onOpenChange(false);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to save report'));
    } finally {
      setSaving(false);
    }
  };
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-purple-600" />
            Radiology Report - {order?.study_type}
          </DialogTitle>
          <DialogDescription>
            {order?.accession_number} | {order?.patient_name} | MRN: {order?.patient_mrn}
          </DialogDescription>
        </DialogHeader>
        
        <ScrollArea className="flex-1 pr-4">
          <div className="space-y-6 py-4">
            {/* Study Information */}
            <div className="bg-slate-50 rounded-lg p-4">
              <h3 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
                <Activity className="w-4 h-4" /> Study Information
              </h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Study Quality</Label>
                  <Select value={reportForm.study_quality} onValueChange={(v) => setReportForm({...reportForm, study_quality: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="diagnostic">Diagnostic</SelectItem>
                      <SelectItem value="limited">Limited</SelectItem>
                      <SelectItem value="non-diagnostic">Non-Diagnostic</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2 col-span-2">
                  <Label>Comparison Studies</Label>
                  <Input
                    value={reportForm.comparison_studies}
                    onChange={(e) => setReportForm({...reportForm, comparison_studies: e.target.value})}
                    placeholder="e.g., CT Chest 2024-01-15"
                  />
                </div>
              </div>
              <div className="space-y-2 mt-3">
                <Label>Technique</Label>
                <Textarea
                  value={reportForm.technique}
                  onChange={(e) => setReportForm({...reportForm, technique: e.target.value})}
                  placeholder="Describe the imaging technique used..."
                  rows={2}
                />
              </div>
            </div>
            
            {/* Clinical Information */}
            <div className="bg-blue-50 rounded-lg p-4">
              <h3 className="font-semibold text-blue-700 mb-3">Clinical Information</h3>
              <div className="space-y-3">
                <div className="space-y-2">
                  <Label>Clinical Indication</Label>
                  <Textarea
                    value={reportForm.clinical_indication}
                    onChange={(e) => setReportForm({...reportForm, clinical_indication: e.target.value})}
                    rows={2}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Relevant Clinical History</Label>
                  <Textarea
                    value={reportForm.clinical_history}
                    onChange={(e) => setReportForm({...reportForm, clinical_history: e.target.value})}
                    rows={2}
                  />
                </div>
              </div>
            </div>
            
            {/* Findings */}
            <div className="bg-purple-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-purple-700">Findings *</h3>
                <VoiceDictation
                  onTranscriptionComplete={(text) => setReportForm({...reportForm, findings_text: text})}
                  context="radiology"
                  targetField="findings"
                  appendMode={!!reportForm.findings_text}
                  currentValue={reportForm.findings_text}
                  buttonVariant="outline"
                  buttonSize="sm"
                />
              </div>
              <Textarea
                value={reportForm.findings_text}
                onChange={(e) => setReportForm({...reportForm, findings_text: e.target.value})}
                placeholder="Describe the imaging findings in detail... or use voice dictation"
                rows={6}
                className="bg-white"
              />
            </div>
            
            {/* Impression */}
            <div className="bg-emerald-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-emerald-700">Impression *</h3>
                <VoiceDictation
                  onTranscriptionComplete={(text) => setReportForm({...reportForm, impression: text})}
                  context="radiology"
                  targetField="impression"
                  appendMode={!!reportForm.impression}
                  currentValue={reportForm.impression}
                  buttonVariant="outline"
                  buttonSize="sm"
                />
              </div>
              <Textarea
                value={reportForm.impression}
                onChange={(e) => setReportForm({...reportForm, impression: e.target.value})}
                placeholder="Summary impression and diagnosis... or use voice dictation"
                rows={3}
                className="bg-white"
              />
            </div>
            
            {/* Recommendations */}
            <div className="bg-amber-50 rounded-lg p-4">
              <h3 className="font-semibold text-amber-700 mb-3">Recommendations & Follow-up</h3>
              <div className="space-y-3">
                <div className="space-y-2">
                  <Label>Recommendations</Label>
                  <Textarea
                    value={reportForm.recommendations}
                    onChange={(e) => setReportForm({...reportForm, recommendations: e.target.value})}
                    placeholder="Additional imaging, clinical correlation, etc."
                    rows={2}
                    className="bg-white"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Follow-up</Label>
                  <Input
                    value={reportForm.follow_up}
                    onChange={(e) => setReportForm({...reportForm, follow_up: e.target.value})}
                    placeholder="e.g., Repeat CT in 3 months"
                    className="bg-white"
                  />
                </div>
              </div>
            </div>
            
            {/* Critical Finding */}
            <div className={cn(
              "rounded-lg p-4",
              reportForm.critical_finding ? "bg-red-100 border-2 border-red-300" : "bg-slate-50"
            )}>
              <div className="flex items-center justify-between mb-3">
                <h3 className={cn(
                  "font-semibold flex items-center gap-2",
                  reportForm.critical_finding ? "text-red-700" : "text-slate-700"
                )}>
                  <AlertTriangle className="w-4 h-4" />
                  Critical Finding
                </h3>
                <Switch
                  checked={reportForm.critical_finding}
                  onCheckedChange={(v) => setReportForm({...reportForm, critical_finding: v})}
                />
              </div>
              {reportForm.critical_finding && (
                <Textarea
                  value={reportForm.critical_finding_details}
                  onChange={(e) => setReportForm({...reportForm, critical_finding_details: e.target.value})}
                  placeholder="Describe the critical finding - requires immediate communication"
                  rows={2}
                  className="bg-white border-red-300"
                />
              )}
            </div>
          </div>
        </ScrollArea>
        
        <DialogFooter className="gap-2 pt-4 border-t">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button variant="outline" onClick={() => handleSubmit(false)} disabled={saving}>
            <Save className="w-4 h-4 mr-2" />
            Save Draft
          </Button>
          <Button onClick={() => handleSubmit(true)} disabled={saving} className="bg-emerald-600 hover:bg-emerald-700">
            {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
            <Check className="w-4 h-4 mr-2" />
            Finalize & Sign
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Order Timeline Component
function OrderTimeline({ timeline }) {
  const getStatusIcon = (status) => {
    switch (status) {
      case 'ordered': return <Clipboard className="w-4 h-4" />;
      case 'scheduled': return <Calendar className="w-4 h-4" />;
      case 'in_progress': return <Play className="w-4 h-4" />;
      case 'completed': return <CheckCircle className="w-4 h-4" />;
      case 'under_review': return <Eye className="w-4 h-4" />;
      case 'reported': return <FileText className="w-4 h-4" />;
      default: return <Clock className="w-4 h-4" />;
    }
  };
  
  const getStatusColor = (status) => {
    switch (status) {
      case 'ordered': return 'bg-yellow-500';
      case 'scheduled': return 'bg-blue-500';
      case 'in_progress': return 'bg-purple-500';
      case 'completed': return 'bg-green-500';
      case 'under_review': return 'bg-orange-500';
      case 'reported': return 'bg-emerald-600';
      default: return 'bg-gray-500';
    }
  };
  
  return (
    <div className="space-y-4">
      {timeline?.map((event, idx) => (
        <div key={idx} className="flex gap-3">
          <div className={cn("w-8 h-8 rounded-full flex items-center justify-center text-white", getStatusColor(event.status))}>
            {getStatusIcon(event.status)}
          </div>
          <div className="flex-1">
            <p className="font-medium text-slate-800 capitalize">{event.status?.replace(/_/g, ' ')}</p>
            <p className="text-sm text-slate-600">{event.details}</p>
            <p className="text-xs text-slate-400 mt-1">
              {event.user} • {event.timestamp ? new Date(event.timestamp).toLocaleString() : ''}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function RadiologyPortal() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [orders, setOrders] = useState([]);
  const [stats, setStats] = useState({});
  const [dashboard, setDashboard] = useState(null);
  const [activeTab, setActiveTab] = useState('worklist');
  const [searchQuery, setSearchQuery] = useState('');
  const [modalityFilter, setModalityFilter] = useState('all');
  const [priorityFilter, setPriorityFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [assignedToMeOnly, setAssignedToMeOnly] = useState(false);
  
  // Selected items and dialogs
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [scheduleDialogOpen, setScheduleDialogOpen] = useState(false);
  const [reportDialogOpen, setReportDialogOpen] = useState(false);
  const [viewerOpen, setViewerOpen] = useState(false);
  const [timelineDialogOpen, setTimelineDialogOpen] = useState(false);
  const [criticalDialogOpen, setCriticalDialogOpen] = useState(false);
  const [noteDialogOpen, setNoteDialogOpen] = useState(false);
  const [orderTimeline, setOrderTimeline] = useState([]);
  const [saving, setSaving] = useState(false);
  
  // Role-based permissions
  const isRadiologist = user?.role === 'radiologist';
  const isRadiologyStaff = user?.role === 'radiology_staff';
  const canCreateReports = isRadiologist;
  const canViewFullDetails = isRadiologist;
  
  // Forms
  const [scheduleForm, setScheduleForm] = useState({
    scheduled_date: '',
    scheduled_time: '',
    room: ''
  });
  
  const [criticalForm, setCriticalForm] = useState({
    communicated_to: '',
    communication_method: 'phone',
    notes: ''
  });
  
  const [noteForm, setNoteForm] = useState({
    note_type: 'progress_note',
    content: '',
    urgency: 'routine'
  });

  // Fetch data
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      if (isRadiologist) {
        // Fetch radiologist dashboard
        const dashResponse = await radiologyAPI.getDashboard();
        setDashboard(dashResponse.data);
        setStats(dashResponse.data.stats || {});
        
        // For worklist, use combined data
        const combined = [
          ...(dashResponse.data.assigned_studies || []),
          ...(dashResponse.data.unassigned_studies || [])
        ];
        setOrders(combined);
      } else {
        // Regular queue for staff
        const params = {};
        if (modalityFilter && modalityFilter !== 'all') params.modality = modalityFilter;
        if (priorityFilter && priorityFilter !== 'all') params.priority = priorityFilter;
        
        const response = await radiologyAPI.getQueue(params);
        setOrders(response.data.orders || []);
        setStats(response.data.stats || {});
      }
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to load data'));
    } finally {
      setLoading(false);
    }
  }, [isRadiologist, modalityFilter, priorityFilter]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // Actions
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
      fetchData();
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
      fetchData();
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
      toast.success('Study completed');
      fetchData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to complete'));
    } finally {
      setSaving(false);
    }
  };

  const handleAssignToMe = async (order) => {
    setSaving(true);
    try {
      await radiologyAPI.assignOrder(order.id);
      toast.success('Study assigned to you');
      fetchData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to assign'));
    } finally {
      setSaving(false);
    }
  };

  const handleCreateReport = async (reportData) => {
    await radiologyAPI.createReport(reportData);
    fetchData();
  };

  const handleViewTimeline = async (order) => {
    try {
      const response = await radiologyAPI.getOrderTimeline(order.id);
      setOrderTimeline(response.data.timeline || []);
      setSelectedOrder(order);
      setTimelineDialogOpen(true);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to load timeline'));
    }
  };

  const handleCommunicateCritical = async () => {
    if (!criticalForm.communicated_to) {
      toast.error('Please specify who was contacted');
      return;
    }
    
    setSaving(true);
    try {
      await radiologyAPI.communicateCritical(selectedOrder.report_id, criticalForm);
      toast.success('Critical finding communication documented');
      setCriticalDialogOpen(false);
      setCriticalForm({ communicated_to: '', communication_method: 'phone', notes: '' });
      fetchData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to document communication'));
    } finally {
      setSaving(false);
    }
  };

  const handleCreateNote = async () => {
    if (!noteForm.content) {
      toast.error('Note content is required');
      return;
    }
    
    setSaving(true);
    try {
      await radiologyAPI.createNote({
        ...noteForm,
        patient_id: selectedOrder.patient_id,
        order_id: selectedOrder.id,
        report_id: selectedOrder.report_id
      });
      toast.success('Note created');
      setNoteDialogOpen(false);
      setNoteForm({ note_type: 'progress_note', content: '', urgency: 'routine' });
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to create note'));
    } finally {
      setSaving(false);
    }
  };

  // Badge helpers
  const getStatusBadge = (status) => {
    const colors = {
      ordered: 'bg-yellow-100 text-yellow-800',
      scheduled: 'bg-blue-100 text-blue-800',
      in_progress: 'bg-purple-100 text-purple-800',
      completed: 'bg-green-100 text-green-800',
      under_review: 'bg-orange-100 text-orange-800',
      reported: 'bg-emerald-100 text-emerald-800',
      cancelled: 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getPriorityBadge = (priority) => {
    const colors = {
      routine: 'bg-gray-100 text-gray-600',
      urgent: 'bg-amber-100 text-amber-700',
      stat: 'bg-red-100 text-red-700 font-bold',
      emergency: 'bg-red-200 text-red-800 font-bold'
    };
    return colors[priority] || 'bg-gray-100 text-gray-600';
  };

  const getModalityIcon = (modality) => {
    const icons = { xray: '🩻', ct: '🔬', mri: '🧲', ultrasound: '📡', mammography: '🔍' };
    return icons[modality] || '📷';
  };

  // Filtering
  const filteredOrders = orders.filter(order => {
    const matchesSearch = !searchQuery || 
      order.patient_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      order.accession_number?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      order.patient_mrn?.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || order.status === statusFilter;
    const matchesAssigned = !assignedToMeOnly || order.assigned_radiologist_id === user?.id;
    
    return matchesSearch && matchesStatus && matchesAssigned;
  });

  return (
    <div className="space-y-6 animate-fade-in" data-testid="radiology-portal">
      {/* Image Viewer */}
      {viewerOpen && selectedOrder && (
        <ImageViewer order={selectedOrder} onClose={() => setViewerOpen(false)} />
      )}
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Scan className="w-7 h-7 text-purple-600" />
            {isRadiologist ? 'Radiologist Workstation' : 'Radiology Tech Station'}
          </h1>
          <p className="text-slate-500 mt-1">
            {isRadiologist ? 'Review studies, create reports, and communicate findings' : 'Manage imaging orders and workflow'}
          </p>
        </div>
        <div className="flex gap-2">
          {isRadiologist && (
            <Badge variant="outline" className="text-purple-600 border-purple-300 px-3 py-1">
              <User className="w-3 h-3 mr-1" />
              Radiologist
            </Badge>
          )}
          {isRadiologyStaff && (
            <Badge variant="outline" className="text-blue-600 border-blue-300 px-3 py-1">
              Radiology Tech
            </Badge>
          )}
          <Button onClick={fetchData} variant="outline" className="gap-2" data-testid="refresh-btn">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
        {isRadiologist ? (
          <>
            <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
              <CardContent className="pt-3 pb-3">
                <div className="text-center">
                  <p className="text-xs font-medium text-purple-600">My Assigned</p>
                  <p className="text-2xl font-bold text-purple-800">{stats.my_assigned || 0}</p>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
              <CardContent className="pt-3 pb-3">
                <div className="text-center">
                  <p className="text-xs font-medium text-orange-600">Pending Review</p>
                  <p className="text-2xl font-bold text-orange-800">{stats.pending_review || 0}</p>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-red-50 to-red-100 border-red-200">
              <CardContent className="pt-3 pb-3">
                <div className="text-center">
                  <p className="text-xs font-medium text-red-600">STAT Pending</p>
                  <p className="text-2xl font-bold text-red-800">{stats.stat_pending || 0}</p>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-emerald-50 to-emerald-100 border-emerald-200">
              <CardContent className="pt-3 pb-3">
                <div className="text-center">
                  <p className="text-xs font-medium text-emerald-600">My Reports Today</p>
                  <p className="text-2xl font-bold text-emerald-800">{stats.my_reports_today || 0}</p>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-pink-50 to-pink-100 border-pink-200">
              <CardContent className="pt-3 pb-3">
                <div className="text-center">
                  <p className="text-xs font-medium text-pink-600">Critical Pending</p>
                  <p className="text-2xl font-bold text-pink-800">{stats.critical_pending || 0}</p>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
              <CardContent className="pt-3 pb-3">
                <div className="text-center">
                  <p className="text-xs font-medium text-blue-600">Under Review</p>
                  <p className="text-2xl font-bold text-blue-800">{stats.under_review || 0}</p>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-slate-50 to-slate-100 border-slate-200">
              <CardContent className="pt-3 pb-3">
                <div className="text-center">
                  <p className="text-xs font-medium text-slate-600">Total Queue</p>
                  <p className="text-2xl font-bold text-slate-800">{stats.total_queue || 0}</p>
                </div>
              </CardContent>
            </Card>
          </>
        ) : (
          <>
            <Card className="bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200">
              <CardContent className="pt-3 pb-3">
                <div className="text-center">
                  <p className="text-xs font-medium text-yellow-600">Ordered</p>
                  <p className="text-2xl font-bold text-yellow-800">{stats.ordered || 0}</p>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
              <CardContent className="pt-3 pb-3">
                <div className="text-center">
                  <p className="text-xs font-medium text-blue-600">Scheduled</p>
                  <p className="text-2xl font-bold text-blue-800">{stats.scheduled || 0}</p>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
              <CardContent className="pt-3 pb-3">
                <div className="text-center">
                  <p className="text-xs font-medium text-purple-600">In Progress</p>
                  <p className="text-2xl font-bold text-purple-800">{stats.in_progress || 0}</p>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
              <CardContent className="pt-3 pb-3">
                <div className="text-center">
                  <p className="text-xs font-medium text-green-600">Completed</p>
                  <p className="text-2xl font-bold text-green-800">{stats.completed || 0}</p>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-emerald-50 to-emerald-100 border-emerald-200">
              <CardContent className="pt-3 pb-3">
                <div className="text-center">
                  <p className="text-xs font-medium text-emerald-600">Reported</p>
                  <p className="text-2xl font-bold text-emerald-800">{stats.reported || 0}</p>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-red-50 to-red-100 border-red-200 col-span-2">
              <CardContent className="pt-3 pb-3">
                <div className="text-center">
                  <p className="text-xs font-medium text-red-600">STAT Pending</p>
                  <p className="text-2xl font-bold text-red-800">{stats.stat_pending || 0}</p>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="worklist" className="gap-2">
            <Clipboard className="w-4 h-4" /> Worklist
          </TabsTrigger>
          {isRadiologist && (
            <>
              <TabsTrigger value="stat" className="gap-2">
                <AlertTriangle className="w-4 h-4" /> STAT Studies
              </TabsTrigger>
              <TabsTrigger value="critical" className="gap-2">
                <AlertCircle className="w-4 h-4" /> Critical Findings
              </TabsTrigger>
              <TabsTrigger value="reports" className="gap-2">
                <FileText className="w-4 h-4" /> My Reports
              </TabsTrigger>
            </>
          )}
        </TabsList>

        {/* Worklist Tab */}
        <TabsContent value="worklist" className="space-y-4">
          {/* Filters */}
          <div className="flex flex-wrap gap-3 items-center">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                placeholder="Search patient, accession, MRN..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
                data-testid="search-input"
              />
            </div>
            <Select value={modalityFilter} onValueChange={setModalityFilter}>
              <SelectTrigger className="w-36">
                <SelectValue placeholder="Modality" />
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
                <SelectValue placeholder="Priority" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Priority</SelectItem>
                <SelectItem value="stat">STAT</SelectItem>
                <SelectItem value="emergency">Emergency</SelectItem>
                <SelectItem value="urgent">Urgent</SelectItem>
                <SelectItem value="routine">Routine</SelectItem>
              </SelectContent>
            </Select>
            {isRadiologist && (
              <>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-36">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="completed">Ready for Review</SelectItem>
                    <SelectItem value="under_review">Under Review</SelectItem>
                    <SelectItem value="reported">Reported</SelectItem>
                  </SelectContent>
                </Select>
                <div className="flex items-center gap-2">
                  <Checkbox
                    id="assigned-me"
                    checked={assignedToMeOnly}
                    onCheckedChange={setAssignedToMeOnly}
                  />
                  <Label htmlFor="assigned-me" className="text-sm">My Assigned Only</Label>
                </div>
              </>
            )}
          </div>

          {/* Orders Table */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center justify-between">
                <span>Imaging Orders Queue</span>
                <Badge variant="outline">{filteredOrders.length} studies</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-purple-600" />
                </div>
              ) : filteredOrders.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <Scan className="w-12 h-12 mx-auto mb-4 opacity-30" />
                  <p>No studies found</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[120px]">Accession</TableHead>
                      <TableHead>Patient</TableHead>
                      <TableHead>Study</TableHead>
                      <TableHead>Modality</TableHead>
                      <TableHead>Priority</TableHead>
                      <TableHead>Status</TableHead>
                      {isRadiologist && <TableHead>Assigned To</TableHead>}
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredOrders.map((order) => (
                      <TableRow 
                        key={order.id} 
                        className={cn(
                          order.priority === 'stat' || order.priority === 'emergency' ? 'bg-red-50' : 'hover:bg-gray-50',
                          order.assigned_radiologist_id === user?.id ? 'border-l-4 border-l-purple-500' : ''
                        )}
                        data-testid={`order-row-${order.accession_number}`}
                      >
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
                        {isRadiologist && (
                          <TableCell className="text-sm">
                            {order.assigned_radiologist_name || (
                              <span className="text-gray-400">Unassigned</span>
                            )}
                          </TableCell>
                        )}
                        <TableCell className="text-right">
                          <div className="flex gap-1 justify-end flex-wrap">
                            {/* View Images */}
                            {(order.status === 'completed' || order.status === 'under_review' || order.status === 'reported') && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => {
                                  setSelectedOrder(order);
                                  setViewerOpen(true);
                                }}
                                title="View Images"
                              >
                                <Monitor className="w-4 h-4" />
                              </Button>
                            )}
                            
                            {/* View Details */}
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setSelectedOrder(order);
                                setViewDialogOpen(true);
                              }}
                              title="View Details"
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            
                            {/* Timeline */}
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleViewTimeline(order)}
                              title="Status Timeline"
                            >
                              <History className="w-4 h-4" />
                            </Button>
                            
                            {/* Tech Actions */}
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
                            
                            {order.status === 'scheduled' && !isRadiologist && (
                              <Button
                                size="sm"
                                className="bg-purple-600 hover:bg-purple-700"
                                onClick={() => handleStartStudy(order)}
                              >
                                <Play className="w-4 h-4 mr-1" /> Start
                              </Button>
                            )}
                            
                            {order.status === 'in_progress' && !isRadiologist && (
                              <Button
                                size="sm"
                                className="bg-green-600 hover:bg-green-700"
                                onClick={() => handleCompleteStudy(order)}
                              >
                                <CheckCircle className="w-4 h-4 mr-1" /> Complete
                              </Button>
                            )}
                            
                            {/* Radiologist Actions */}
                            {isRadiologist && order.status === 'completed' && !order.assigned_radiologist_id && (
                              <Button
                                size="sm"
                                className="bg-orange-600 hover:bg-orange-700"
                                onClick={() => handleAssignToMe(order)}
                              >
                                <User className="w-4 h-4 mr-1" /> Claim
                              </Button>
                            )}
                            
                            {isRadiologist && (order.status === 'completed' || order.status === 'under_review') && order.assigned_radiologist_id === user?.id && (
                              <Button
                                size="sm"
                                className="bg-emerald-600 hover:bg-emerald-700"
                                onClick={() => {
                                  setSelectedOrder(order);
                                  setReportDialogOpen(true);
                                }}
                                data-testid={`report-btn-${order.id}`}
                              >
                                <FileText className="w-4 h-4 mr-1" /> Report
                              </Button>
                            )}
                            
                            {/* Add Note */}
                            {isRadiologist && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => {
                                  setSelectedOrder(order);
                                  setNoteDialogOpen(true);
                                }}
                                title="Add Note"
                              >
                                <MessageSquare className="w-4 h-4" />
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

        {/* STAT Studies Tab */}
        {isRadiologist && (
          <TabsContent value="stat" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-red-600 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5" />
                  STAT & Emergency Studies
                </CardTitle>
                <CardDescription>High-priority studies requiring immediate attention</CardDescription>
              </CardHeader>
              <CardContent>
                {dashboard?.stat_studies?.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-500 opacity-50" />
                    <p>No STAT studies pending</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {dashboard?.stat_studies?.map((order) => (
                      <div 
                        key={order.id} 
                        className="flex items-center justify-between p-4 bg-red-50 rounded-lg border border-red-200"
                      >
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                            <AlertTriangle className="w-5 h-5 text-red-600" />
                          </div>
                          <div>
                            <p className="font-medium">{order.patient_name} - {order.study_type}</p>
                            <p className="text-sm text-gray-600">
                              {order.accession_number} | {order.modality?.toUpperCase()} | Ordered: {new Date(order.created_at).toLocaleString()}
                            </p>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Badge className={getStatusBadge(order.status)}>{order.status?.replace(/_/g, ' ')}</Badge>
                          {order.status === 'completed' && (
                            <Button 
                              size="sm"
                              className="bg-red-600 hover:bg-red-700"
                              onClick={() => {
                                setSelectedOrder(order);
                                setReportDialogOpen(true);
                              }}
                            >
                              <FileText className="w-4 h-4 mr-1" /> Report Now
                            </Button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {/* Critical Findings Tab */}
        {isRadiologist && (
          <TabsContent value="critical" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-pink-600 flex items-center gap-2">
                  <AlertCircle className="w-5 h-5" />
                  Critical Findings Requiring Communication
                </CardTitle>
                <CardDescription>Critical findings that need to be communicated to ordering physician</CardDescription>
              </CardHeader>
              <CardContent>
                {dashboard?.critical_findings?.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-500 opacity-50" />
                    <p>No pending critical finding communications</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {dashboard?.critical_findings?.map((finding) => (
                      <div 
                        key={finding.id} 
                        className="flex items-center justify-between p-4 bg-pink-50 rounded-lg border border-pink-200"
                      >
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-full bg-pink-100 flex items-center justify-center">
                            <Phone className="w-5 h-5 text-pink-600" />
                          </div>
                          <div>
                            <p className="font-medium">{finding.patient_name}</p>
                            <p className="text-sm text-pink-700">{finding.critical_finding_details || 'Critical finding identified'}</p>
                            <p className="text-xs text-gray-500">
                              {finding.study_type} | Reported: {new Date(finding.finalized_at || finding.created_at).toLocaleString()}
                            </p>
                          </div>
                        </div>
                        <Button 
                          size="sm"
                          className="bg-pink-600 hover:bg-pink-700"
                          onClick={() => {
                            setSelectedOrder(finding);
                            setCriticalDialogOpen(true);
                          }}
                        >
                          <Phone className="w-4 h-4 mr-1" /> Document Communication
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {/* My Reports Tab */}
        {isRadiologist && (
          <TabsContent value="reports" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-emerald-600" />
                  My Recent Reports
                </CardTitle>
              </CardHeader>
              <CardContent>
                {dashboard?.my_recent_reports?.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <FileText className="w-12 h-12 mx-auto mb-4 opacity-30" />
                    <p>No reports yet</p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Accession</TableHead>
                        <TableHead>Patient</TableHead>
                        <TableHead>Study</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Reported</TableHead>
                        <TableHead>Critical</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {dashboard?.my_recent_reports?.map((report) => (
                        <TableRow key={report.id}>
                          <TableCell className="font-mono text-sm">{report.accession_number}</TableCell>
                          <TableCell>{report.patient_name}</TableCell>
                          <TableCell>{report.study_type}</TableCell>
                          <TableCell>
                            <Badge className={report.status === 'finalized' ? 'bg-emerald-100 text-emerald-800' : 'bg-yellow-100 text-yellow-800'}>
                              {report.status}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-sm">{new Date(report.finalized_at || report.created_at).toLocaleString()}</TableCell>
                          <TableCell>
                            {report.critical_finding && (
                              <Badge className="bg-red-100 text-red-700">
                                <AlertTriangle className="w-3 h-3 mr-1" /> Critical
                              </Badge>
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
        )}
      </Tabs>

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
                  {canViewFullDetails && (
                    <p className="text-sm text-gray-500">DOB: {selectedOrder.patient_dob}</p>
                  )}
                </div>
                <div className="bg-purple-50 rounded-lg p-4">
                  <h4 className="font-medium text-purple-700 mb-2">Study</h4>
                  <p className="font-medium">{selectedOrder.study_type}</p>
                  <p className="text-sm text-gray-500">Modality: {selectedOrder.modality?.toUpperCase()}</p>
                  <p className="text-sm text-gray-500">Body Part: {selectedOrder.body_part}</p>
                </div>
              </div>
              
              {canViewFullDetails && (
                <>
                  <div className="bg-blue-50 rounded-lg p-4">
                    <h4 className="font-medium text-blue-700 mb-2">Clinical Indication</h4>
                    <p className="text-sm">{selectedOrder.clinical_indication || 'Not provided'}</p>
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
                </>
              )}
              
              <div className="flex flex-wrap gap-3 text-sm">
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
                <div>
                  <span className="text-gray-500">Priority:</span>
                  <Badge className={`ml-2 ${getPriorityBadge(selectedOrder.priority)}`}>
                    {selectedOrder.priority?.toUpperCase()}
                  </Badge>
                </div>
              </div>
              
              <Separator />
              
              <div className="text-sm text-gray-500">
                <p>Ordering Physician: {selectedOrder.ordering_physician}</p>
                <p>Ordered: {new Date(selectedOrder.created_at).toLocaleString()}</p>
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

      {/* Structured Report Dialog */}
      <StructuredReportDialog
        open={reportDialogOpen}
        onOpenChange={setReportDialogOpen}
        order={selectedOrder}
        onSubmit={handleCreateReport}
      />

      {/* Timeline Dialog */}
      <Dialog open={timelineDialogOpen} onOpenChange={setTimelineDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <History className="w-5 h-5" />
              Status Timeline
            </DialogTitle>
            <DialogDescription>{selectedOrder?.accession_number}</DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <OrderTimeline timeline={orderTimeline} />
          </div>
        </DialogContent>
      </Dialog>

      {/* Critical Finding Communication Dialog */}
      <Dialog open={criticalDialogOpen} onOpenChange={setCriticalDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="text-pink-600 flex items-center gap-2">
              <Phone className="w-5 h-5" />
              Document Critical Finding Communication
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="bg-pink-50 p-3 rounded-lg">
              <p className="text-sm text-pink-700">
                <strong>Patient:</strong> {selectedOrder?.patient_name}<br />
                <strong>Study:</strong> {selectedOrder?.study_type}
              </p>
            </div>
            
            <div className="space-y-2">
              <Label>Communicated To *</Label>
              <Input
                value={criticalForm.communicated_to}
                onChange={(e) => setCriticalForm({...criticalForm, communicated_to: e.target.value})}
                placeholder="Name of person contacted"
              />
            </div>
            
            <div className="space-y-2">
              <Label>Communication Method</Label>
              <Select value={criticalForm.communication_method} onValueChange={(v) => setCriticalForm({...criticalForm, communication_method: v})}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="phone">Phone Call</SelectItem>
                  <SelectItem value="page">Page</SelectItem>
                  <SelectItem value="in_person">In Person</SelectItem>
                  <SelectItem value="verbal">Verbal</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea
                value={criticalForm.notes}
                onChange={(e) => setCriticalForm({...criticalForm, notes: e.target.value})}
                placeholder="Additional notes about the communication..."
                rows={2}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setCriticalDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCommunicateCritical} disabled={saving} className="bg-pink-600 hover:bg-pink-700">
              {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Document Communication
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Note Dialog */}
      <Dialog open={noteDialogOpen} onOpenChange={setNoteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5" />
              Add Radiology Note
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Note Type</Label>
              <Select value={noteForm.note_type} onValueChange={(v) => setNoteForm({...noteForm, note_type: v})}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="progress_note">Progress Note</SelectItem>
                  <SelectItem value="addendum">Addendum</SelectItem>
                  <SelectItem value="procedure_note">Procedure Note</SelectItem>
                  <SelectItem value="communication">Communication Note</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Urgency</Label>
              <Select value={noteForm.urgency} onValueChange={(v) => setNoteForm({...noteForm, urgency: v})}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="routine">Routine</SelectItem>
                  <SelectItem value="urgent">Urgent</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Content *</Label>
              <Textarea
                value={noteForm.content}
                onChange={(e) => setNoteForm({...noteForm, content: e.target.value})}
                placeholder="Enter note content..."
                rows={4}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setNoteDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateNote} disabled={saving}>
              {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Save Note
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
