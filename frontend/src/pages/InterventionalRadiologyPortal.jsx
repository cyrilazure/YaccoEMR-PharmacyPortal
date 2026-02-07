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
import { ScrollArea } from '@/components/ui/scroll-area';
import { Switch } from '@/components/ui/switch';
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
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
  Activity, RefreshCw, Search, CheckCircle, AlertCircle,
  Clock, Play, FileText, Eye, Calendar, User, Heart,
  AlertTriangle, Loader2, Syringe, Monitor, Thermometer,
  Plus, Edit2, Check, X, Clipboard, Timer, Zap, 
  ClipboardCheck, FileSignature, Stethoscope, Droplets,
  Shield, PenTool, Send
} from 'lucide-react';
import api from '@/lib/api';
import VoiceDictation from '@/components/VoiceDictation';
import IRStatusBoard from '@/components/IRStatusBoard';

// IR API
const irAPI = {
  getDashboard: () => api.get('/interventional-radiology/dashboard'),
  getProcedures: (params) => api.get('/interventional-radiology/procedures', { params }),
  getProcedure: (id) => api.get(`/interventional-radiology/procedures/${id}`),
  createProcedure: (data) => api.post('/interventional-radiology/procedures/create', data),
  updateStatus: (id, status) => api.put(`/interventional-radiology/procedures/${id}/status`, null, { params: { status } }),
  createPreAssessment: (data) => api.post('/interventional-radiology/pre-assessment/create', data),
  createIntraNote: (data) => api.post('/interventional-radiology/intra-procedure/create', data),
  createPostNote: (data) => api.post('/interventional-radiology/post-procedure/create', data),
  recordSedation: (data) => api.post('/interventional-radiology/sedation/record', data),
  getSedationRecords: (procedureId) => api.get(`/interventional-radiology/sedation/${procedureId}`),
};

const PROCEDURE_TYPES = [
  { value: 'angiography', label: 'Angiography' },
  { value: 'angioplasty', label: 'Angioplasty' },
  { value: 'biopsy', label: 'Biopsy' },
  { value: 'drainage', label: 'Drainage' },
  { value: 'embolization', label: 'Embolization' },
  { value: 'ablation', label: 'Ablation' },
  { value: 'stent_placement', label: 'Stent Placement' },
  { value: 'thrombolysis', label: 'Thrombolysis' },
  { value: 'vertebroplasty', label: 'Vertebroplasty' },
  { value: 'port_placement', label: 'Port Placement' },
  { value: 'line_placement', label: 'Line Placement' },
  { value: 'nephrostomy', label: 'Nephrostomy' },
  { value: 'cholecystostomy', label: 'Cholecystostomy' },
  { value: 'other', label: 'Other' },
];

const SEDATION_LEVELS = [
  { value: 'none', label: 'None' },
  { value: 'minimal', label: 'Minimal (Anxiolysis)' },
  { value: 'moderate', label: 'Moderate (Conscious)' },
  { value: 'deep', label: 'Deep Sedation' },
  { value: 'general', label: 'General Anesthesia' },
];

// Status Badge Component
function StatusBadge({ status }) {
  const colors = {
    scheduled: 'bg-blue-100 text-blue-800',
    pre_procedure: 'bg-yellow-100 text-yellow-800',
    in_progress: 'bg-purple-100 text-purple-800 animate-pulse',
    recovery: 'bg-orange-100 text-orange-800',
    completed: 'bg-green-100 text-green-800',
    cancelled: 'bg-red-100 text-red-800',
  };
  return (
    <Badge className={colors[status] || 'bg-gray-100 text-gray-800'}>
      {status?.replace(/_/g, ' ').toUpperCase()}
    </Badge>
  );
}

// Sedation Chart Component
function SedationChart({ records }) {
  if (!records || records.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <Heart className="w-12 h-12 mx-auto mb-2 opacity-30" />
        <p>No vitals recorded yet</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-5 gap-4 text-center text-sm font-medium text-gray-500 border-b pb-2">
        <div>Time</div>
        <div>HR</div>
        <div>BP</div>
        <div>SpO2</div>
        <div>RR</div>
      </div>
      <ScrollArea className="h-[300px]">
        {records.map((record, idx) => (
          <div key={idx} className="grid grid-cols-5 gap-4 text-center py-2 border-b border-gray-100">
            <div className="text-sm">{new Date(record.timestamp).toLocaleTimeString()}</div>
            <div className={cn("font-medium", record.heart_rate > 100 || record.heart_rate < 60 ? "text-red-600" : "text-green-600")}>
              {record.heart_rate}
            </div>
            <div className={cn("font-medium", record.blood_pressure_systolic > 140 ? "text-red-600" : "text-green-600")}>
              {record.blood_pressure_systolic}/{record.blood_pressure_diastolic}
            </div>
            <div className={cn("font-medium", record.oxygen_saturation < 95 ? "text-red-600" : "text-green-600")}>
              {record.oxygen_saturation}%
            </div>
            <div className="font-medium">{record.respiratory_rate}</div>
          </div>
        ))}
      </ScrollArea>
    </div>
  );
}

export default function InterventionalRadiologyPortal() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);
  const [procedures, setProcedures] = useState([]);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedProcedure, setSelectedProcedure] = useState(null);
  const [procedureDetails, setProcedureDetails] = useState(null);
  const [saving, setSaving] = useState(false);

  // Dialogs
  const [newProcedureOpen, setNewProcedureOpen] = useState(false);
  const [preAssessmentOpen, setPreAssessmentOpen] = useState(false);
  const [intraDocOpen, setIntraDocOpen] = useState(false);
  const [postDocOpen, setPostDocOpen] = useState(false);
  const [sedationOpen, setSedationOpen] = useState(false);
  const [viewDetailsOpen, setViewDetailsOpen] = useState(false);

  // Forms
  const [procedureForm, setProcedureForm] = useState({
    patient_id: '',
    patient_name: '',
    patient_mrn: '',
    procedure_type: '',
    procedure_description: '',
    indication: '',
    laterality: 'bilateral',
    scheduled_date: '',
    scheduled_time: '',
    estimated_duration_minutes: 60,
    sedation_required: 'moderate',
    contrast_required: false,
    attending_physician_id: user?.id || '',
    attending_physician_name: `${user?.first_name || ''} ${user?.last_name || ''}`,
    notes: '',
  });

  const [preAssessmentForm, setPreAssessmentForm] = useState({
    allergies_reviewed: false,
    allergies_notes: '',
    medications_reviewed: false,
    anticoagulants: [],
    anticoagulant_held: false,
    last_dose_date: '',
    labs_reviewed: false,
    inr: '',
    platelets: '',
    creatinine: '',
    egfr: '',
    consent_obtained: false,
    consent_date: '',
    npo_status: false,
    npo_since: '',
    iv_access: false,
    iv_gauge: '',
    assessment_notes: '',
  });

  const [intraForm, setIntraForm] = useState({
    access_site: '',
    access_method: '',
    anesthesia_type: 'moderate',
    contrast_used: '',
    contrast_volume_ml: '',
    fluoroscopy_time_minutes: '',
    radiation_dose_mgy: '',
    devices_used: '',
    findings: '',
    intervention_performed: '',
    complications: '',
    estimated_blood_loss_ml: '',
  });

  const [postForm, setPostForm] = useState({
    procedure_end_time: '',
    recovery_start_time: '',
    access_site_status: '',
    vital_signs_stable: true,
    pain_score: '',
    complications: '',
    discharge_criteria_met: false,
    discharge_instructions_given: false,
    follow_up_scheduled: false,
    follow_up_date: '',
    post_procedure_notes: '',
  });

  const [sedationForm, setSedationForm] = useState({
    timestamp: new Date().toISOString(),
    heart_rate: '',
    blood_pressure_systolic: '',
    blood_pressure_diastolic: '',
    respiratory_rate: '',
    oxygen_saturation: '',
    sedation_level: 'alert',
    notes: '',
  });

  // Fetch data
  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    try {
      const response = await irAPI.getDashboard();
      setDashboard(response.data);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to load dashboard'));
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchProcedures = useCallback(async () => {
    try {
      const response = await irAPI.getProcedures({});
      setProcedures(response.data.procedures || []);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to load procedures'));
    }
  }, []);

  const fetchProcedureDetails = useCallback(async (id) => {
    try {
      const response = await irAPI.getProcedure(id);
      setProcedureDetails(response.data);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to load procedure details'));
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
    fetchProcedures();
    const interval = setInterval(fetchDashboard, 30000);
    return () => clearInterval(interval);
  }, [fetchDashboard, fetchProcedures]);

  // Handlers
  const handleCreateProcedure = async () => {
    if (!procedureForm.patient_name || !procedureForm.procedure_type || !procedureForm.scheduled_date) {
      toast.error('Please fill required fields');
      return;
    }
    setSaving(true);
    try {
      await irAPI.createProcedure(procedureForm);
      toast.success('Procedure scheduled');
      setNewProcedureOpen(false);
      fetchDashboard();
      fetchProcedures();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to create procedure'));
    } finally {
      setSaving(false);
    }
  };

  const handleStatusUpdate = async (procedure, newStatus) => {
    setSaving(true);
    try {
      await irAPI.updateStatus(procedure.id, newStatus);
      toast.success(`Status updated to ${newStatus.replace(/_/g, ' ')}`);
      fetchDashboard();
      fetchProcedures();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to update status'));
    } finally {
      setSaving(false);
    }
  };

  const handlePreAssessment = async () => {
    setSaving(true);
    try {
      await irAPI.createPreAssessment({
        procedure_id: selectedProcedure.id,
        ...preAssessmentForm,
        inr: preAssessmentForm.inr ? parseFloat(preAssessmentForm.inr) : null,
        platelets: preAssessmentForm.platelets ? parseInt(preAssessmentForm.platelets) : null,
        creatinine: preAssessmentForm.creatinine ? parseFloat(preAssessmentForm.creatinine) : null,
        egfr: preAssessmentForm.egfr ? parseFloat(preAssessmentForm.egfr) : null,
      });
      toast.success('Pre-procedure assessment saved');
      setPreAssessmentOpen(false);
      fetchDashboard();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to save assessment'));
    } finally {
      setSaving(false);
    }
  };

  const handleIntraDoc = async () => {
    if (!intraForm.findings || !intraForm.intervention_performed) {
      toast.error('Findings and intervention are required');
      return;
    }
    setSaving(true);
    try {
      await irAPI.createIntraNote({
        procedure_id: selectedProcedure.id,
        ...intraForm,
        contrast_volume_ml: intraForm.contrast_volume_ml ? parseInt(intraForm.contrast_volume_ml) : null,
        fluoroscopy_time_minutes: intraForm.fluoroscopy_time_minutes ? parseFloat(intraForm.fluoroscopy_time_minutes) : null,
        radiation_dose_mgy: intraForm.radiation_dose_mgy ? parseFloat(intraForm.radiation_dose_mgy) : null,
        estimated_blood_loss_ml: intraForm.estimated_blood_loss_ml ? parseInt(intraForm.estimated_blood_loss_ml) : null,
        devices_used: intraForm.devices_used ? intraForm.devices_used.split(',').map(d => d.trim()) : [],
      });
      toast.success('Intra-procedure note saved');
      setIntraDocOpen(false);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to save note'));
    } finally {
      setSaving(false);
    }
  };

  const handlePostDoc = async () => {
    setSaving(true);
    try {
      await irAPI.createPostNote({
        procedure_id: selectedProcedure.id,
        ...postForm,
        pain_score: postForm.pain_score ? parseInt(postForm.pain_score) : null,
      });
      toast.success('Post-procedure note saved');
      setPostDocOpen(false);
      fetchDashboard();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to save note'));
    } finally {
      setSaving(false);
    }
  };

  const handleRecordSedation = async () => {
    if (!sedationForm.heart_rate || !sedationForm.blood_pressure_systolic) {
      toast.error('Please fill vital signs');
      return;
    }
    setSaving(true);
    try {
      await irAPI.recordSedation({
        procedure_id: selectedProcedure.id,
        timestamp: new Date().toISOString(),
        heart_rate: parseInt(sedationForm.heart_rate),
        blood_pressure_systolic: parseInt(sedationForm.blood_pressure_systolic),
        blood_pressure_diastolic: parseInt(sedationForm.blood_pressure_diastolic),
        respiratory_rate: parseInt(sedationForm.respiratory_rate),
        oxygen_saturation: parseInt(sedationForm.oxygen_saturation),
        sedation_level: sedationForm.sedation_level,
        notes: sedationForm.notes,
      });
      toast.success('Vitals recorded');
      // Reset form but keep dialog open for continuous monitoring
      setSedationForm({
        ...sedationForm,
        timestamp: new Date().toISOString(),
        heart_rate: '',
        blood_pressure_systolic: '',
        blood_pressure_diastolic: '',
        respiratory_rate: '',
        oxygen_saturation: '',
        notes: '',
      });
      // Refresh details if viewing
      if (procedureDetails) {
        fetchProcedureDetails(selectedProcedure.id);
      }
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to record vitals'));
    } finally {
      setSaving(false);
    }
  };

  const openProcedureDetails = async (procedure) => {
    setSelectedProcedure(procedure);
    await fetchProcedureDetails(procedure.id);
    setViewDetailsOpen(true);
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="ir-portal">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Syringe className="w-7 h-7 text-indigo-600" />
            Interventional Radiology
          </h1>
          <p className="text-slate-500 mt-1">Procedure management, documentation, and monitoring</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setNewProcedureOpen(true)} className="bg-indigo-600 hover:bg-indigo-700 gap-2">
            <Plus className="w-4 h-4" /> New Procedure
          </Button>
          <Button onClick={fetchDashboard} variant="outline" className="gap-2">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <Calendar className="w-8 h-8 mx-auto text-blue-600 mb-2" />
              <p className="text-2xl font-bold text-blue-800">{dashboard?.today_count || 0}</p>
              <p className="text-sm text-blue-600">Today's Cases</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <Play className="w-8 h-8 mx-auto text-purple-600 mb-2" />
              <p className="text-2xl font-bold text-purple-800">{dashboard?.in_progress?.length || 0}</p>
              <p className="text-sm text-purple-600">In Progress</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <Timer className="w-8 h-8 mx-auto text-orange-600 mb-2" />
              <p className="text-2xl font-bold text-orange-800">{dashboard?.in_recovery?.length || 0}</p>
              <p className="text-sm text-orange-600">In Recovery</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <CheckCircle className="w-8 h-8 mx-auto text-green-600 mb-2" />
              <p className="text-2xl font-bold text-green-800">{dashboard?.status_counts?.completed || 0}</p>
              <p className="text-sm text-green-600">Completed</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <Clock className="w-8 h-8 mx-auto text-yellow-600 mb-2" />
              <p className="text-2xl font-bold text-yellow-800">{dashboard?.status_counts?.scheduled || 0}</p>
              <p className="text-sm text-yellow-600">Scheduled</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="dashboard" className="gap-2">
            <Activity className="w-4 h-4" /> Dashboard
          </TabsTrigger>
          <TabsTrigger value="status-board" className="gap-2">
            <Monitor className="w-4 h-4" /> Status Board
          </TabsTrigger>
          <TabsTrigger value="schedule" className="gap-2">
            <Calendar className="w-4 h-4" /> Schedule
          </TabsTrigger>
          <TabsTrigger value="all" className="gap-2">
            <Clipboard className="w-4 h-4" /> All Procedures
          </TabsTrigger>
        </TabsList>

        {/* Status Board Tab */}
        <TabsContent value="status-board">
          <IRStatusBoard refreshInterval={15000} />
        </TabsContent>

        {/* Dashboard Tab */}
        <TabsContent value="dashboard" className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            {/* In Progress */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-purple-700">
                  <Play className="w-5 h-5" /> Procedures In Progress
                </CardTitle>
              </CardHeader>
              <CardContent>
                {dashboard?.in_progress?.length === 0 ? (
                  <p className="text-center py-6 text-gray-500">No procedures in progress</p>
                ) : (
                  <div className="space-y-3">
                    {dashboard?.in_progress?.map((proc) => (
                      <div key={proc.id} className="flex items-center justify-between p-3 bg-purple-50 rounded-lg border border-purple-200">
                        <div>
                          <p className="font-medium">{proc.patient_name}</p>
                          <p className="text-sm text-gray-600">{proc.procedure_description}</p>
                          <p className="text-xs text-gray-500">{proc.case_number}</p>
                        </div>
                        <div className="flex gap-2">
                          <Button size="sm" variant="outline" onClick={() => {
                            setSelectedProcedure(proc);
                            setSedationOpen(true);
                          }}>
                            <Heart className="w-4 h-4 mr-1" /> Vitals
                          </Button>
                          <Button size="sm" onClick={() => openProcedureDetails(proc)}>
                            <Eye className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* In Recovery */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-orange-700">
                  <Timer className="w-5 h-5" /> Patients In Recovery
                </CardTitle>
              </CardHeader>
              <CardContent>
                {dashboard?.in_recovery?.length === 0 ? (
                  <p className="text-center py-6 text-gray-500">No patients in recovery</p>
                ) : (
                  <div className="space-y-3">
                    {dashboard?.in_recovery?.map((proc) => (
                      <div key={proc.id} className="flex items-center justify-between p-3 bg-orange-50 rounded-lg border border-orange-200">
                        <div>
                          <p className="font-medium">{proc.patient_name}</p>
                          <p className="text-sm text-gray-600">{proc.procedure_description}</p>
                        </div>
                        <div className="flex gap-2">
                          <Button size="sm" variant="outline" onClick={() => {
                            setSelectedProcedure(proc);
                            setPostDocOpen(true);
                          }}>
                            <FileText className="w-4 h-4 mr-1" /> Discharge
                          </Button>
                          <Button size="sm" className="bg-green-600 hover:bg-green-700" onClick={() => handleStatusUpdate(proc, 'completed')}>
                            <Check className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Today's Schedule */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="w-5 h-5 text-blue-600" /> Today's Schedule
              </CardTitle>
            </CardHeader>
            <CardContent>
              {dashboard?.today_schedule?.length === 0 ? (
                <p className="text-center py-8 text-gray-500">No procedures scheduled for today</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Time</TableHead>
                      <TableHead>Case #</TableHead>
                      <TableHead>Patient</TableHead>
                      <TableHead>Procedure</TableHead>
                      <TableHead>Physician</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {dashboard?.today_schedule?.map((proc) => (
                      <TableRow key={proc.id}>
                        <TableCell className="font-mono">{proc.scheduled_time}</TableCell>
                        <TableCell className="font-mono text-sm">{proc.case_number}</TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{proc.patient_name}</p>
                            <p className="text-xs text-gray-500">{proc.patient_mrn}</p>
                          </div>
                        </TableCell>
                        <TableCell>{proc.procedure_description}</TableCell>
                        <TableCell>{proc.attending_physician_name}</TableCell>
                        <TableCell><StatusBadge status={proc.status} /></TableCell>
                        <TableCell>
                          <div className="flex gap-1">
                            <Button size="sm" variant="outline" onClick={() => openProcedureDetails(proc)}>
                              <Eye className="w-4 h-4" />
                            </Button>
                            {proc.status === 'scheduled' && (
                              <Button size="sm" variant="outline" onClick={() => {
                                setSelectedProcedure(proc);
                                setPreAssessmentOpen(true);
                              }}>
                                <ClipboardCheck className="w-4 h-4" />
                              </Button>
                            )}
                            {proc.status === 'pre_procedure' && (
                              <Button size="sm" className="bg-purple-600 hover:bg-purple-700" onClick={() => handleStatusUpdate(proc, 'in_progress')}>
                                <Play className="w-4 h-4 mr-1" /> Start
                              </Button>
                            )}
                            {proc.status === 'in_progress' && (
                              <>
                                <Button size="sm" variant="outline" onClick={() => {
                                  setSelectedProcedure(proc);
                                  setIntraDocOpen(true);
                                }}>
                                  <FileText className="w-4 h-4" />
                                </Button>
                                <Button size="sm" className="bg-orange-600 hover:bg-orange-700" onClick={() => handleStatusUpdate(proc, 'recovery')}>
                                  End
                                </Button>
                              </>
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

        {/* Schedule Tab */}
        <TabsContent value="schedule">
          <Card>
            <CardHeader>
              <CardTitle>Upcoming Procedures</CardTitle>
              <CardDescription>View and manage scheduled procedures</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Time</TableHead>
                    <TableHead>Patient</TableHead>
                    <TableHead>Procedure</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {procedures.filter(p => p.status === 'scheduled').map((proc) => (
                    <TableRow key={proc.id}>
                      <TableCell>{proc.scheduled_date}</TableCell>
                      <TableCell>{proc.scheduled_time}</TableCell>
                      <TableCell>{proc.patient_name}</TableCell>
                      <TableCell>{proc.procedure_description}</TableCell>
                      <TableCell><StatusBadge status={proc.status} /></TableCell>
                      <TableCell>
                        <Button size="sm" variant="outline" onClick={() => openProcedureDetails(proc)}>
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* All Procedures Tab */}
        <TabsContent value="all">
          <Card>
            <CardHeader>
              <CardTitle>All Procedures</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Case #</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Patient</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Physician</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {procedures.map((proc) => (
                    <TableRow key={proc.id}>
                      <TableCell className="font-mono text-sm">{proc.case_number}</TableCell>
                      <TableCell>{proc.scheduled_date}</TableCell>
                      <TableCell>{proc.patient_name}</TableCell>
                      <TableCell className="capitalize">{proc.procedure_type?.replace(/_/g, ' ')}</TableCell>
                      <TableCell>{proc.attending_physician_name}</TableCell>
                      <TableCell><StatusBadge status={proc.status} /></TableCell>
                      <TableCell>
                        <Button size="sm" variant="outline" onClick={() => openProcedureDetails(proc)}>
                          <Eye className="w-4 h-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* New Procedure Dialog */}
      <Dialog open={newProcedureOpen} onOpenChange={setNewProcedureOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Plus className="w-5 h-5 text-indigo-600" /> Schedule New IR Procedure
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Patient Name *</Label>
                <Input value={procedureForm.patient_name} onChange={(e) => setProcedureForm({...procedureForm, patient_name: e.target.value})} placeholder="Patient name" />
              </div>
              <div className="space-y-2">
                <Label>MRN</Label>
                <Input value={procedureForm.patient_mrn} onChange={(e) => setProcedureForm({...procedureForm, patient_mrn: e.target.value})} placeholder="Medical record number" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Procedure Type *</Label>
                <Select value={procedureForm.procedure_type} onValueChange={(v) => setProcedureForm({...procedureForm, procedure_type: v})}>
                  <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
                  <SelectContent>
                    {PROCEDURE_TYPES.map(t => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Laterality</Label>
                <Select value={procedureForm.laterality} onValueChange={(v) => setProcedureForm({...procedureForm, laterality: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="left">Left</SelectItem>
                    <SelectItem value="right">Right</SelectItem>
                    <SelectItem value="bilateral">Bilateral</SelectItem>
                    <SelectItem value="na">N/A</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Procedure Description *</Label>
              <Input value={procedureForm.procedure_description} onChange={(e) => setProcedureForm({...procedureForm, procedure_description: e.target.value})} placeholder="Brief description" />
            </div>
            <div className="space-y-2">
              <Label>Clinical Indication</Label>
              <Textarea value={procedureForm.indication} onChange={(e) => setProcedureForm({...procedureForm, indication: e.target.value})} rows={2} />
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Date *</Label>
                <Input type="date" value={procedureForm.scheduled_date} onChange={(e) => setProcedureForm({...procedureForm, scheduled_date: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label>Time *</Label>
                <Input type="time" value={procedureForm.scheduled_time} onChange={(e) => setProcedureForm({...procedureForm, scheduled_time: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label>Est. Duration (min)</Label>
                <Input type="number" value={procedureForm.estimated_duration_minutes} onChange={(e) => setProcedureForm({...procedureForm, estimated_duration_minutes: parseInt(e.target.value)})} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Sedation Required</Label>
                <Select value={procedureForm.sedation_required} onValueChange={(v) => setProcedureForm({...procedureForm, sedation_required: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {SEDATION_LEVELS.map(s => (
                      <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-2 pt-8">
                <Switch checked={procedureForm.contrast_required} onCheckedChange={(v) => setProcedureForm({...procedureForm, contrast_required: v})} />
                <Label>Contrast Required</Label>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea value={procedureForm.notes} onChange={(e) => setProcedureForm({...procedureForm, notes: e.target.value})} rows={2} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setNewProcedureOpen(false)}>Cancel</Button>
            <Button onClick={handleCreateProcedure} disabled={saving} className="bg-indigo-600 hover:bg-indigo-700">
              {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Schedule Procedure
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Pre-Assessment Dialog */}
      <Dialog open={preAssessmentOpen} onOpenChange={setPreAssessmentOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ClipboardCheck className="w-5 h-5 text-yellow-600" /> Pre-Procedure Assessment
            </DialogTitle>
            <DialogDescription>{selectedProcedure?.patient_name} - {selectedProcedure?.procedure_description}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {/* Allergies */}
            <div className="bg-red-50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <Checkbox checked={preAssessmentForm.allergies_reviewed} onCheckedChange={(v) => setPreAssessmentForm({...preAssessmentForm, allergies_reviewed: v})} />
                <Label className="font-semibold text-red-700">Allergies Reviewed</Label>
              </div>
              <Textarea placeholder="Allergy notes..." value={preAssessmentForm.allergies_notes} onChange={(e) => setPreAssessmentForm({...preAssessmentForm, allergies_notes: e.target.value})} rows={2} />
            </div>
            
            {/* Medications */}
            <div className="bg-orange-50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <Checkbox checked={preAssessmentForm.medications_reviewed} onCheckedChange={(v) => setPreAssessmentForm({...preAssessmentForm, medications_reviewed: v})} />
                <Label className="font-semibold text-orange-700">Medications Reviewed</Label>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-2">
                  <Checkbox checked={preAssessmentForm.anticoagulant_held} onCheckedChange={(v) => setPreAssessmentForm({...preAssessmentForm, anticoagulant_held: v})} />
                  <Label>Anticoagulants Held</Label>
                </div>
                <Input type="date" placeholder="Last dose date" value={preAssessmentForm.last_dose_date} onChange={(e) => setPreAssessmentForm({...preAssessmentForm, last_dose_date: e.target.value})} />
              </div>
            </div>
            
            {/* Labs */}
            <div className="bg-blue-50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <Checkbox checked={preAssessmentForm.labs_reviewed} onCheckedChange={(v) => setPreAssessmentForm({...preAssessmentForm, labs_reviewed: v})} />
                <Label className="font-semibold text-blue-700">Labs Reviewed</Label>
              </div>
              <div className="grid grid-cols-4 gap-4">
                <div className="space-y-1">
                  <Label className="text-xs">INR</Label>
                  <Input value={preAssessmentForm.inr} onChange={(e) => setPreAssessmentForm({...preAssessmentForm, inr: e.target.value})} />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Platelets</Label>
                  <Input value={preAssessmentForm.platelets} onChange={(e) => setPreAssessmentForm({...preAssessmentForm, platelets: e.target.value})} />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Creatinine</Label>
                  <Input value={preAssessmentForm.creatinine} onChange={(e) => setPreAssessmentForm({...preAssessmentForm, creatinine: e.target.value})} />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">eGFR</Label>
                  <Input value={preAssessmentForm.egfr} onChange={(e) => setPreAssessmentForm({...preAssessmentForm, egfr: e.target.value})} />
                </div>
              </div>
            </div>
            
            {/* Consent & NPO */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-green-50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Checkbox checked={preAssessmentForm.consent_obtained} onCheckedChange={(v) => setPreAssessmentForm({...preAssessmentForm, consent_obtained: v})} />
                  <Label className="font-semibold text-green-700">Consent Obtained</Label>
                </div>
                <Input type="date" value={preAssessmentForm.consent_date} onChange={(e) => setPreAssessmentForm({...preAssessmentForm, consent_date: e.target.value})} />
              </div>
              <div className="bg-purple-50 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Checkbox checked={preAssessmentForm.npo_status} onCheckedChange={(v) => setPreAssessmentForm({...preAssessmentForm, npo_status: v})} />
                  <Label className="font-semibold text-purple-700">NPO Status Confirmed</Label>
                </div>
                <Input placeholder="NPO since..." value={preAssessmentForm.npo_since} onChange={(e) => setPreAssessmentForm({...preAssessmentForm, npo_since: e.target.value})} />
              </div>
            </div>
            
            {/* IV Access */}
            <div className="bg-slate-50 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <Checkbox checked={preAssessmentForm.iv_access} onCheckedChange={(v) => setPreAssessmentForm({...preAssessmentForm, iv_access: v})} />
                <Label className="font-semibold">IV Access Established</Label>
              </div>
              <Input placeholder="IV gauge (e.g., 18G, 20G)" value={preAssessmentForm.iv_gauge} onChange={(e) => setPreAssessmentForm({...preAssessmentForm, iv_gauge: e.target.value})} />
            </div>
            
            {/* Notes */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Assessment Notes</Label>
                <VoiceDictation
                  onTranscriptionComplete={(text) => setPreAssessmentForm({...preAssessmentForm, assessment_notes: text})}
                  context="clinical"
                  targetField="assessment notes"
                  noteType="nursing_assessment"
                  enableAiExpand={true}
                />
              </div>
              <Textarea value={preAssessmentForm.assessment_notes} onChange={(e) => setPreAssessmentForm({...preAssessmentForm, assessment_notes: e.target.value})} rows={3} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setPreAssessmentOpen(false)}>Cancel</Button>
            <Button onClick={handlePreAssessment} disabled={saving} className="bg-yellow-600 hover:bg-yellow-700">
              {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Save Assessment
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Intra-Procedure Doc Dialog */}
      <Dialog open={intraDocOpen} onOpenChange={setIntraDocOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-purple-600" /> Intra-Procedure Documentation
            </DialogTitle>
            <DialogDescription>{selectedProcedure?.patient_name} - {selectedProcedure?.procedure_description}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Access Site *</Label>
                <Input value={intraForm.access_site} onChange={(e) => setIntraForm({...intraForm, access_site: e.target.value})} placeholder="e.g., Right femoral artery" />
              </div>
              <div className="space-y-2">
                <Label>Access Method</Label>
                <Select value={intraForm.access_method} onValueChange={(v) => setIntraForm({...intraForm, access_method: v})}>
                  <SelectTrigger><SelectValue placeholder="Select method" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="micropuncture">Micropuncture</SelectItem>
                    <SelectItem value="direct_puncture">Direct Puncture</SelectItem>
                    <SelectItem value="cutdown">Cutdown</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Contrast Used</Label>
                <Input value={intraForm.contrast_used} onChange={(e) => setIntraForm({...intraForm, contrast_used: e.target.value})} placeholder="Type" />
              </div>
              <div className="space-y-2">
                <Label>Volume (mL)</Label>
                <Input type="number" value={intraForm.contrast_volume_ml} onChange={(e) => setIntraForm({...intraForm, contrast_volume_ml: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label>Fluoro Time (min)</Label>
                <Input type="number" step="0.1" value={intraForm.fluoroscopy_time_minutes} onChange={(e) => setIntraForm({...intraForm, fluoroscopy_time_minutes: e.target.value})} />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Devices Used</Label>
              <Input value={intraForm.devices_used} onChange={(e) => setIntraForm({...intraForm, devices_used: e.target.value})} placeholder="Comma-separated list" />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Findings *</Label>
                <VoiceDictation
                  onTranscriptionComplete={(text) => setIntraForm({...intraForm, findings: text})}
                  context="radiology"
                  targetField="findings"
                  noteType="radiology_report"
                  enableAiExpand={true}
                />
              </div>
              <Textarea value={intraForm.findings} onChange={(e) => setIntraForm({...intraForm, findings: e.target.value})} rows={4} placeholder="Describe findings..." />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Intervention Performed *</Label>
                <VoiceDictation
                  onTranscriptionComplete={(text) => setIntraForm({...intraForm, intervention_performed: text})}
                  context="radiology"
                  targetField="intervention"
                  noteType="radiology_report"
                  enableAiExpand={true}
                />
              </div>
              <Textarea value={intraForm.intervention_performed} onChange={(e) => setIntraForm({...intraForm, intervention_performed: e.target.value})} rows={3} placeholder="Describe intervention..." />
            </div>
            <div className="space-y-2">
              <Label>Complications</Label>
              <Input value={intraForm.complications} onChange={(e) => setIntraForm({...intraForm, complications: e.target.value})} placeholder="None or describe" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIntraDocOpen(false)}>Cancel</Button>
            <Button onClick={handleIntraDoc} disabled={saving} className="bg-purple-600 hover:bg-purple-700">
              {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Save Documentation
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Post-Procedure Doc Dialog */}
      <Dialog open={postDocOpen} onOpenChange={setPostDocOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-600" /> Post-Procedure Documentation
            </DialogTitle>
            <DialogDescription>{selectedProcedure?.patient_name}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Procedure End Time</Label>
                <Input type="time" value={postForm.procedure_end_time} onChange={(e) => setPostForm({...postForm, procedure_end_time: e.target.value})} />
              </div>
              <div className="space-y-2">
                <Label>Recovery Start Time</Label>
                <Input type="time" value={postForm.recovery_start_time} onChange={(e) => setPostForm({...postForm, recovery_start_time: e.target.value})} />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Access Site Status</Label>
              <Select value={postForm.access_site_status} onValueChange={(v) => setPostForm({...postForm, access_site_status: v})}>
                <SelectTrigger><SelectValue placeholder="Select status" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="hemostasis_achieved">Hemostasis Achieved (Manual)</SelectItem>
                  <SelectItem value="closure_device">Closure Device Deployed</SelectItem>
                  <SelectItem value="pressure_dressing">Pressure Dressing Applied</SelectItem>
                  <SelectItem value="ongoing_bleeding">Ongoing Bleeding - Monitoring</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-2">
                <Checkbox checked={postForm.vital_signs_stable} onCheckedChange={(v) => setPostForm({...postForm, vital_signs_stable: v})} />
                <Label>Vital Signs Stable</Label>
              </div>
              <div className="space-y-2">
                <Label>Pain Score (0-10)</Label>
                <Input type="number" min="0" max="10" value={postForm.pain_score} onChange={(e) => setPostForm({...postForm, pain_score: e.target.value})} />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Complications</Label>
              <Input value={postForm.complications} onChange={(e) => setPostForm({...postForm, complications: e.target.value})} placeholder="None or describe" />
            </div>
            <Separator />
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Checkbox checked={postForm.discharge_criteria_met} onCheckedChange={(v) => setPostForm({...postForm, discharge_criteria_met: v})} />
                <Label className="font-semibold">Discharge Criteria Met</Label>
              </div>
              <div className="flex items-center gap-2">
                <Checkbox checked={postForm.discharge_instructions_given} onCheckedChange={(v) => setPostForm({...postForm, discharge_instructions_given: v})} />
                <Label>Discharge Instructions Given</Label>
              </div>
              <div className="flex items-center gap-2">
                <Checkbox checked={postForm.follow_up_scheduled} onCheckedChange={(v) => setPostForm({...postForm, follow_up_scheduled: v})} />
                <Label>Follow-up Scheduled</Label>
              </div>
              {postForm.follow_up_scheduled && (
                <Input type="date" value={postForm.follow_up_date} onChange={(e) => setPostForm({...postForm, follow_up_date: e.target.value})} />
              )}
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Post-Procedure Notes</Label>
                <VoiceDictation
                  onTranscriptionComplete={(text) => setPostForm({...postForm, post_procedure_notes: text})}
                  context="clinical"
                  targetField="post-procedure notes"
                  noteType="progress_note"
                  enableAiExpand={true}
                />
              </div>
              <Textarea value={postForm.post_procedure_notes} onChange={(e) => setPostForm({...postForm, post_procedure_notes: e.target.value})} rows={3} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setPostDocOpen(false)}>Cancel</Button>
            <Button onClick={handlePostDoc} disabled={saving} className="bg-green-600 hover:bg-green-700">
              {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Save & {postForm.discharge_criteria_met ? 'Complete' : 'Update'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Sedation Monitoring Dialog */}
      <Dialog open={sedationOpen} onOpenChange={setSedationOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Heart className="w-5 h-5 text-red-600" /> Sedation Monitoring
            </DialogTitle>
            <DialogDescription>{selectedProcedure?.patient_name}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Heart Rate *</Label>
                <Input type="number" value={sedationForm.heart_rate} onChange={(e) => setSedationForm({...sedationForm, heart_rate: e.target.value})} placeholder="bpm" />
              </div>
              <div className="space-y-2">
                <Label>Blood Pressure *</Label>
                <div className="flex gap-1">
                  <Input type="number" value={sedationForm.blood_pressure_systolic} onChange={(e) => setSedationForm({...sedationForm, blood_pressure_systolic: e.target.value})} placeholder="Sys" />
                  <span className="self-center">/</span>
                  <Input type="number" value={sedationForm.blood_pressure_diastolic} onChange={(e) => setSedationForm({...sedationForm, blood_pressure_diastolic: e.target.value})} placeholder="Dia" />
                </div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>SpO2 *</Label>
                <Input type="number" value={sedationForm.oxygen_saturation} onChange={(e) => setSedationForm({...sedationForm, oxygen_saturation: e.target.value})} placeholder="%" />
              </div>
              <div className="space-y-2">
                <Label>Resp Rate</Label>
                <Input type="number" value={sedationForm.respiratory_rate} onChange={(e) => setSedationForm({...sedationForm, respiratory_rate: e.target.value})} placeholder="/min" />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Sedation Level</Label>
              <Select value={sedationForm.sedation_level} onValueChange={(v) => setSedationForm({...sedationForm, sedation_level: v})}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="alert">Alert</SelectItem>
                  <SelectItem value="drowsy">Drowsy</SelectItem>
                  <SelectItem value="responsive_verbal">Responsive to Verbal</SelectItem>
                  <SelectItem value="responsive_pain">Responsive to Pain</SelectItem>
                  <SelectItem value="unresponsive">Unresponsive</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Notes</Label>
              <Input value={sedationForm.notes} onChange={(e) => setSedationForm({...sedationForm, notes: e.target.value})} placeholder="Optional notes" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSedationOpen(false)}>Close</Button>
            <Button onClick={handleRecordSedation} disabled={saving} className="bg-red-600 hover:bg-red-700">
              {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Record Vitals
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Procedure Details Dialog */}
      <Dialog open={viewDetailsOpen} onOpenChange={setViewDetailsOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" /> Procedure Details
            </DialogTitle>
            <DialogDescription>{procedureDetails?.procedure?.case_number}</DialogDescription>
          </DialogHeader>
          {procedureDetails && (
            <div className="space-y-6 py-4">
              {/* Procedure Info */}
              <div className="bg-slate-50 rounded-lg p-4">
                <h3 className="font-semibold mb-3">Procedure Information</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div><span className="text-gray-500">Patient:</span> {procedureDetails.procedure.patient_name}</div>
                  <div><span className="text-gray-500">MRN:</span> {procedureDetails.procedure.patient_mrn}</div>
                  <div><span className="text-gray-500">Procedure:</span> {procedureDetails.procedure.procedure_description}</div>
                  <div><span className="text-gray-500">Type:</span> {procedureDetails.procedure.procedure_type}</div>
                  <div><span className="text-gray-500">Date:</span> {procedureDetails.procedure.scheduled_date} {procedureDetails.procedure.scheduled_time}</div>
                  <div><span className="text-gray-500">Status:</span> <StatusBadge status={procedureDetails.procedure.status} /></div>
                  <div><span className="text-gray-500">Physician:</span> {procedureDetails.procedure.attending_physician_name}</div>
                  <div><span className="text-gray-500">Indication:</span> {procedureDetails.procedure.indication}</div>
                </div>
              </div>
              
              {/* Pre-Assessment */}
              {procedureDetails.pre_assessment && (
                <div className="bg-yellow-50 rounded-lg p-4">
                  <h3 className="font-semibold mb-3 text-yellow-800">Pre-Procedure Assessment</h3>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>Allergies Reviewed: {procedureDetails.pre_assessment.allergies_reviewed ? '✓' : '✗'}</div>
                    <div>Labs Reviewed: {procedureDetails.pre_assessment.labs_reviewed ? '✓' : '✗'}</div>
                    <div>Consent Obtained: {procedureDetails.pre_assessment.consent_obtained ? '✓' : '✗'}</div>
                    <div>NPO Status: {procedureDetails.pre_assessment.npo_status ? '✓' : '✗'}</div>
                    <div>IV Access: {procedureDetails.pre_assessment.iv_access ? '✓' : '✗'} {procedureDetails.pre_assessment.iv_gauge}</div>
                  </div>
                </div>
              )}
              
              {/* Intra-Procedure */}
              {procedureDetails.intra_procedure_note && (
                <div className="bg-purple-50 rounded-lg p-4">
                  <h3 className="font-semibold mb-3 text-purple-800">Intra-Procedure Documentation</h3>
                  <div className="space-y-2 text-sm">
                    <p><span className="font-medium">Access:</span> {procedureDetails.intra_procedure_note.access_site} ({procedureDetails.intra_procedure_note.access_method})</p>
                    <p><span className="font-medium">Findings:</span> {procedureDetails.intra_procedure_note.findings}</p>
                    <p><span className="font-medium">Intervention:</span> {procedureDetails.intra_procedure_note.intervention_performed}</p>
                    {procedureDetails.intra_procedure_note.contrast_used && (
                      <p><span className="font-medium">Contrast:</span> {procedureDetails.intra_procedure_note.contrast_used} {procedureDetails.intra_procedure_note.contrast_volume_ml}mL</p>
                    )}
                  </div>
                </div>
              )}
              
              {/* Post-Procedure */}
              {procedureDetails.post_procedure_note && (
                <div className="bg-green-50 rounded-lg p-4">
                  <h3 className="font-semibold mb-3 text-green-800">Post-Procedure Documentation</h3>
                  <div className="space-y-2 text-sm">
                    <p><span className="font-medium">Access Site:</span> {procedureDetails.post_procedure_note.access_site_status}</p>
                    <p><span className="font-medium">Vitals Stable:</span> {procedureDetails.post_procedure_note.vital_signs_stable ? 'Yes' : 'No'}</p>
                    <p><span className="font-medium">Notes:</span> {procedureDetails.post_procedure_note.post_procedure_notes}</p>
                  </div>
                </div>
              )}
              
              {/* Sedation Chart */}
              {procedureDetails.sedation_records?.length > 0 && (
                <div className="bg-red-50 rounded-lg p-4">
                  <h3 className="font-semibold mb-3 text-red-800">Sedation Monitoring</h3>
                  <SedationChart records={procedureDetails.sedation_records} />
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
