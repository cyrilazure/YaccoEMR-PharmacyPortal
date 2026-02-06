import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import { 
  patientAPI, vitalsAPI, problemsAPI, medicationsAPI, 
  allergiesAPI, notesAPI, ordersAPI, aiAPI, labAPI, radiologyAPI, prescriptionAPI 
} from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
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
import { calculateAge, formatDate, formatDateTime, getStatusColor } from '@/lib/utils';
import { 
  ArrowLeft, User, Heart, AlertTriangle, Pill, FileText, ClipboardList,
  Plus, Activity, Thermometer, Droplets, Wind, Scale, Ruler,
  Sparkles, Check, Loader2, Calendar, FlaskConical, TrendingUp, TrendingDown, Scan, Send
} from 'lucide-react';

export default function PatientChart() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [patient, setPatient] = useState(null);
  const [vitals, setVitals] = useState([]);
  const [problems, setProblems] = useState([]);
  const [medications, setMedications] = useState([]);
  const [allergies, setAllergies] = useState([]);
  const [notes, setNotes] = useState([]);
  const [orders, setOrders] = useState([]);
  const [labOrders, setLabOrders] = useState([]);
  const [labResults, setLabResults] = useState([]);
  const [labPanels, setLabPanels] = useState([]);
  const [radiologyOrders, setRadiologyOrders] = useState([]);
  const [radiologyModalities, setRadiologyModalities] = useState([]);
  const [radiologyStudyTypes, setRadiologyStudyTypes] = useState([]);
  const [prescriptions, setPrescriptions] = useState([]);
  const [ghanaPharmacies, setGhanaPharmacies] = useState([]);
  const [drugDatabase, setDrugDatabase] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Dialog states
  const [vitalsDialogOpen, setVitalsDialogOpen] = useState(false);
  const [problemDialogOpen, setProblemDialogOpen] = useState(false);
  const [medDialogOpen, setMedDialogOpen] = useState(false);
  const [allergyDialogOpen, setAllergyDialogOpen] = useState(false);
  const [noteDialogOpen, setNoteDialogOpen] = useState(false);
  const [orderDialogOpen, setOrderDialogOpen] = useState(false);
  const [aiDialogOpen, setAiDialogOpen] = useState(false);
  const [labOrderDialogOpen, setLabOrderDialogOpen] = useState(false);
  const [radiologyOrderDialogOpen, setRadiologyOrderDialogOpen] = useState(false);
  const [prescriptionDialogOpen, setPrescriptionDialogOpen] = useState(false);
  
  // Form states
  const [newVitals, setNewVitals] = useState({
    blood_pressure_systolic: '', blood_pressure_diastolic: '',
    heart_rate: '', respiratory_rate: '', temperature: '',
    oxygen_saturation: '', weight: '', height: '', notes: ''
  });
  const [newProblem, setNewProblem] = useState({
    description: '', icd_code: '', onset_date: '', status: 'active', notes: ''
  });
  const [newMedication, setNewMedication] = useState({
    name: '', dosage: '', frequency: '', route: 'oral', 
    start_date: '', end_date: '', status: 'active', notes: ''
  });
  const [newAllergy, setNewAllergy] = useState({
    allergen: '', reaction: '', severity: 'mild', notes: ''
  });
  const [newNote, setNewNote] = useState({
    note_type: 'progress_note', chief_complaint: '', subjective: '',
    objective: '', assessment: '', plan: '', content: ''
  });
  const [newOrder, setNewOrder] = useState({
    order_type: 'lab', description: '', priority: 'routine', instructions: '', diagnosis: ''
  });
  const [newLabOrder, setNewLabOrder] = useState({
    panel_code: 'CBC', priority: 'routine', clinical_notes: '', diagnosis: '', fasting_required: false
  });
  const [newRadiologyOrder, setNewRadiologyOrder] = useState({
    modality: 'xray',
    study_type: '',
    body_part: '',
    laterality: 'bilateral',
    clinical_indication: '',
    priority: 'routine',
    contrast_required: false,
    special_instructions: ''
  });
  const [newPrescription, setNewPrescription] = useState({
    pharmacy_id: '',
    diagnosis: '',
    clinical_notes: '',
    priority: 'routine',
    medications: [{
      medication_name: '',
      dosage: '',
      dosage_unit: 'mg',
      frequency: 'BID',
      route: 'oral',
      duration_value: 7,
      duration_unit: 'days',
      quantity: 1,
      refills: 0,
      special_instructions: ''
    }]
  });
  const [aiRequest, setAiRequest] = useState({
    note_type: 'progress_note', symptoms: '', findings: '', context: ''
  });
  const [aiGenerating, setAiGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [simulatingLab, setSimulatingLab] = useState(null);

  useEffect(() => {
    fetchAllData();
    fetchLabPanels();
    fetchRadiologyModalities();
  }, [id]);

  const fetchLabPanels = async () => {
    try {
      const res = await labAPI.getPanels();
      setLabPanels(res.data.panels || []);
    } catch (err) {
      console.error('Failed to fetch lab panels', err);
    }
  };

  const fetchRadiologyModalities = async () => {
    try {
      const res = await radiologyAPI.getModalities();
      setRadiologyModalities(res.data.modalities || []);
    } catch (err) {
      console.error('Failed to fetch radiology modalities', err);
    }
  };

  const fetchRadiologyData = async () => {
    try {
      const ordersRes = await radiologyAPI.getPatientOrders(id);
      setRadiologyOrders(ordersRes.data.orders || []);
    } catch (err) {
      console.error('Failed to fetch radiology data', err);
    }
  };

  const handleModalityChange = async (modality) => {
    setNewRadiologyOrder({ ...newRadiologyOrder, modality, study_type: '', body_part: '' });
    try {
      const res = await radiologyAPI.getStudyTypes(modality);
      setRadiologyStudyTypes(res.data.study_types || []);
    } catch (err) {
      console.error('Failed to fetch study types', err);
    }
  };

  const fetchLabData = async () => {
    try {
      const [ordersRes, resultsRes] = await Promise.all([
        labAPI.getPatientOrders(id),
        labAPI.getPatientResults(id)
      ]);
      setLabOrders(ordersRes.data.orders || []);
      setLabResults(resultsRes.data.results || []);
    } catch (err) {
      console.error('Failed to fetch lab data', err);
    }
  };

  const fetchAllData = async () => {
    try {
      const [patientRes, vitalsRes, problemsRes, medsRes, allergiesRes, notesRes, ordersRes] = 
        await Promise.all([
          patientAPI.getById(id),
          vitalsAPI.getByPatient(id),
          problemsAPI.getByPatient(id),
          medicationsAPI.getByPatient(id),
          allergiesAPI.getByPatient(id),
          notesAPI.getByPatient(id),
          ordersAPI.getAll({ patient_id: id })
        ]);
      
      setPatient(patientRes.data);
      setVitals(vitalsRes.data);
      setProblems(problemsRes.data);
      setMedications(medsRes.data);
      setAllergies(allergiesRes.data);
      setNotes(notesRes.data);
      setOrders(ordersRes.data);
      
      // Fetch lab data separately
      fetchLabData();
      fetchRadiologyData();
    } catch (err) {
      toast.error('Failed to load patient data');
      navigate('/patients');
    } finally {
      setLoading(false);
    }
  };

  // Form handlers
  const handleSaveVitals = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const data = { ...newVitals, patient_id: id };
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
      toast.success('Vitals recorded');
      setVitalsDialogOpen(false);
      setNewVitals({ blood_pressure_systolic: '', blood_pressure_diastolic: '', heart_rate: '', respiratory_rate: '', temperature: '', oxygen_saturation: '', weight: '', height: '', notes: '' });
      fetchAllData();
    } catch (err) {
      toast.error('Failed to save vitals');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveProblem = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await problemsAPI.create({ ...newProblem, patient_id: id });
      toast.success('Problem added');
      setProblemDialogOpen(false);
      setNewProblem({ description: '', icd_code: '', onset_date: '', status: 'active', notes: '' });
      fetchAllData();
    } catch (err) {
      toast.error('Failed to save problem');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveMedication = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await medicationsAPI.create({ ...newMedication, patient_id: id });
      toast.success('Medication added');
      setMedDialogOpen(false);
      setNewMedication({ name: '', dosage: '', frequency: '', route: 'oral', start_date: '', end_date: '', status: 'active', notes: '' });
      fetchAllData();
    } catch (err) {
      toast.error('Failed to save medication');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveAllergy = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await allergiesAPI.create({ ...newAllergy, patient_id: id });
      toast.success('Allergy added');
      setAllergyDialogOpen(false);
      setNewAllergy({ allergen: '', reaction: '', severity: 'mild', notes: '' });
      fetchAllData();
    } catch (err) {
      toast.error('Failed to save allergy');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveNote = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await notesAPI.create({ ...newNote, patient_id: id });
      toast.success('Note saved');
      setNoteDialogOpen(false);
      setNewNote({ note_type: 'progress_note', chief_complaint: '', subjective: '', objective: '', assessment: '', plan: '', content: '' });
      fetchAllData();
    } catch (err) {
      toast.error('Failed to save note');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveOrder = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await ordersAPI.create({ ...newOrder, patient_id: id });
      toast.success('Order placed');
      setOrderDialogOpen(false);
      setNewOrder({ order_type: 'lab', description: '', priority: 'routine', instructions: '', diagnosis: '' });
      fetchAllData();
    } catch (err) {
      toast.error('Failed to place order');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveLabOrder = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const selectedPanel = labPanels.find(p => p.code === newLabOrder.panel_code);
      await labAPI.createOrder({
        ...newLabOrder,
        patient_id: id,
        patient_name: `${patient?.first_name} ${patient?.last_name}`,
        ordering_provider_id: user.id,
        ordering_provider_name: `${user.first_name} ${user.last_name}`,
        panel_name: selectedPanel?.name || newLabOrder.panel_code
      });
      toast.success('Lab order placed');
      setLabOrderDialogOpen(false);
      setNewLabOrder({ panel_code: 'CBC', priority: 'routine', clinical_notes: '', diagnosis: '', fasting_required: false });
      fetchLabData();
    } catch (err) {
      toast.error('Failed to place lab order');
    } finally {
      setSaving(false);
    }
  };

  const handleSimulateLabResults = async (orderId) => {
    setSimulatingLab(orderId);
    try {
      await labAPI.simulateResults(orderId, 'mixed');
      toast.success('Lab results generated');
      fetchLabData();
    } catch (err) {
      toast.error('Failed to generate lab results');
    } finally {
      setSimulatingLab(null);
    }
  };

  const handleSaveRadiologyOrder = async (e) => {
    e.preventDefault();
    if (!newRadiologyOrder.study_type || !newRadiologyOrder.clinical_indication) {
      toast.error('Study type and clinical indication are required');
      return;
    }
    setSaving(true);
    try {
      await radiologyAPI.createOrder({ ...newRadiologyOrder, patient_id: id });
      toast.success('Radiology order placed');
      setRadiologyOrderDialogOpen(false);
      setNewRadiologyOrder({
        modality: 'xray', study_type: '', body_part: '', laterality: 'bilateral',
        clinical_indication: '', priority: 'routine', contrast_required: false, special_instructions: ''
      });
      fetchRadiologyData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to place radiology order');
    } finally {
      setSaving(false);
    }
  };

  const getLabResultFlag = (flag) => {
    const flagStyles = {
      'N': { label: 'Normal', className: 'bg-green-100 text-green-700' },
      'L': { label: 'Low', className: 'bg-amber-100 text-amber-700' },
      'H': { label: 'High', className: 'bg-amber-100 text-amber-700' },
      'LL': { label: 'Critical Low', className: 'bg-red-100 text-red-700' },
      'HH': { label: 'Critical High', className: 'bg-red-100 text-red-700' },
      'A': { label: 'Abnormal', className: 'bg-orange-100 text-orange-700' }
    };
    return flagStyles[flag] || { label: flag, className: 'bg-slate-100 text-slate-700' };
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

  const handleGenerateAINote = async () => {
    setAiGenerating(true);
    try {
      const res = await aiAPI.generateNote({ ...aiRequest, patient_id: id });
      setNewNote({
        ...newNote,
        note_type: aiRequest.note_type,
        content: res.data.generated_note
      });
      setAiDialogOpen(false);
      setNoteDialogOpen(true);
      toast.success('AI note generated! Review and save.');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'AI generation failed');
    } finally {
      setAiGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  const latestVitals = vitals[0];

  return (
    <div className="space-y-6 animate-fade-in" data-testid="patient-chart-page">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/patients')} data-testid="back-btn">
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <div className="w-14 h-14 rounded-full bg-sky-100 text-sky-700 flex items-center justify-center text-xl font-semibold">
              {patient?.first_name?.[0]}{patient?.last_name?.[0]}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Manrope' }}>
                {patient?.first_name} {patient?.last_name}
              </h1>
              <div className="flex items-center gap-3 text-sm text-slate-500">
                <span>MRN: <Badge variant="outline" className="font-mono ml-1">{patient?.mrn}</Badge></span>
                <span>•</span>
                <span>{calculateAge(patient?.date_of_birth)} years old</span>
                <span>•</span>
                <span className="capitalize">{patient?.gender}</span>
                <span>•</span>
                <span>DOB: {formatDate(patient?.date_of_birth)}</span>
              </div>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Dialog open={aiDialogOpen} onOpenChange={setAiDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" className="gap-2" data-testid="ai-assist-btn">
                <Sparkles className="w-4 h-4 text-amber-500" /> AI Assist
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-amber-500" /> AI Documentation Assistant
                </DialogTitle>
                <DialogDescription>
                  Generate clinical notes using GPT-5.2
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label>Note Type</Label>
                  <Select value={aiRequest.note_type} onValueChange={(v) => setAiRequest({ ...aiRequest, note_type: v })}>
                    <SelectTrigger data-testid="ai-note-type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="progress_note">Progress Note</SelectItem>
                      <SelectItem value="h_and_p">History & Physical</SelectItem>
                      <SelectItem value="discharge_summary">Discharge Summary</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Chief Complaint / Symptoms</Label>
                  <Textarea 
                    placeholder="Describe the patient's symptoms..."
                    value={aiRequest.symptoms}
                    onChange={(e) => setAiRequest({ ...aiRequest, symptoms: e.target.value })}
                    data-testid="ai-symptoms"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Clinical Findings</Label>
                  <Textarea 
                    placeholder="Physical exam findings, lab results..."
                    value={aiRequest.findings}
                    onChange={(e) => setAiRequest({ ...aiRequest, findings: e.target.value })}
                    data-testid="ai-findings"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Additional Context</Label>
                  <Textarea 
                    placeholder="Medical history, relevant information..."
                    value={aiRequest.context}
                    onChange={(e) => setAiRequest({ ...aiRequest, context: e.target.value })}
                    data-testid="ai-context"
                  />
                </div>
                <Button 
                  className="w-full gap-2" 
                  onClick={handleGenerateAINote}
                  disabled={aiGenerating}
                  data-testid="generate-ai-btn"
                >
                  {aiGenerating ? (
                    <><Loader2 className="w-4 h-4 animate-spin" /> Generating...</>
                  ) : (
                    <><Sparkles className="w-4 h-4" /> Generate Note</>
                  )}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Quick Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Allergies Alert */}
        <Card className={allergies.length > 0 ? "border-red-200 bg-red-50" : ""}>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className={`w-4 h-4 ${allergies.length > 0 ? "text-red-600" : "text-slate-400"}`} />
              <span className="font-medium text-sm">Allergies</span>
            </div>
            {allergies.length === 0 ? (
              <p className="text-sm text-slate-500">NKDA</p>
            ) : (
              <div className="flex flex-wrap gap-1">
                {allergies.slice(0, 3).map((a) => (
                  <Badge key={a.id} className="badge-allergy text-xs">{a.allergen}</Badge>
                ))}
                {allergies.length > 3 && <Badge variant="outline" className="text-xs">+{allergies.length - 3}</Badge>}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Latest Vitals */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-4 h-4 text-emerald-600" />
              <span className="font-medium text-sm">Latest Vitals</span>
            </div>
            {latestVitals ? (
              <div className="text-sm text-slate-600 space-y-1">
                {latestVitals.blood_pressure_systolic && (
                  <p>BP: {latestVitals.blood_pressure_systolic}/{latestVitals.blood_pressure_diastolic} mmHg</p>
                )}
                {latestVitals.heart_rate && <p>HR: {latestVitals.heart_rate} bpm</p>}
              </div>
            ) : (
              <p className="text-sm text-slate-500">No vitals recorded</p>
            )}
          </CardContent>
        </Card>

        {/* Active Problems */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <FileText className="w-4 h-4 text-amber-600" />
              <span className="font-medium text-sm">Active Problems</span>
            </div>
            <p className="text-2xl font-bold text-slate-900">
              {problems.filter(p => p.status === 'active').length}
            </p>
          </CardContent>
        </Card>

        {/* Active Meds */}
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Pill className="w-4 h-4 text-blue-600" />
              <span className="font-medium text-sm">Active Medications</span>
            </div>
            <p className="text-2xl font-bold text-slate-900">
              {medications.filter(m => m.status === 'active').length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-9 w-full max-w-5xl">
          <TabsTrigger value="overview" data-testid="tab-overview">Overview</TabsTrigger>
          <TabsTrigger value="vitals" data-testid="tab-vitals">Vitals</TabsTrigger>
          <TabsTrigger value="problems" data-testid="tab-problems">Problems</TabsTrigger>
          <TabsTrigger value="medications" data-testid="tab-medications">Meds</TabsTrigger>
          <TabsTrigger value="labs" data-testid="tab-labs">Labs</TabsTrigger>
          <TabsTrigger value="imaging" data-testid="tab-imaging">Imaging</TabsTrigger>
          <TabsTrigger value="pharmacy" data-testid="tab-pharmacy">Pharmacy</TabsTrigger>
          <TabsTrigger value="notes" data-testid="tab-notes">Notes</TabsTrigger>
          <TabsTrigger value="orders" data-testid="tab-orders">Orders</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Patient Demographics */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="w-5 h-5" /> Demographics
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div><span className="text-slate-500">Name:</span> <span className="font-medium">{patient?.first_name} {patient?.last_name}</span></div>
                  <div><span className="text-slate-500">MRN:</span> <span className="font-mono">{patient?.mrn}</span></div>
                  <div><span className="text-slate-500">DOB:</span> {formatDate(patient?.date_of_birth)}</div>
                  <div><span className="text-slate-500">Age:</span> {calculateAge(patient?.date_of_birth)} years</div>
                  <div><span className="text-slate-500">Gender:</span> <span className="capitalize">{patient?.gender}</span></div>
                  <div><span className="text-slate-500">Phone:</span> {patient?.phone || 'N/A'}</div>
                  <div className="col-span-2"><span className="text-slate-500">Email:</span> {patient?.email || 'N/A'}</div>
                  <div className="col-span-2"><span className="text-slate-500">Address:</span> {patient?.address || 'N/A'}</div>
                </div>
                <div className="pt-3 border-t">
                  <p className="text-sm text-slate-500 mb-1">Emergency Contact</p>
                  <p className="text-sm">{patient?.emergency_contact_name || 'Not provided'} {patient?.emergency_contact_phone && `• ${patient.emergency_contact_phone}`}</p>
                </div>
                <div className="pt-3 border-t">
                  <p className="text-sm text-slate-500 mb-1">Insurance</p>
                  <p className="text-sm">{patient?.insurance_provider || 'Not provided'} {patient?.insurance_id && `• ID: ${patient.insurance_id}`}</p>
                </div>
              </CardContent>
            </Card>

            {/* Allergies Card */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-red-500" /> Allergies
                </CardTitle>
                <Dialog open={allergyDialogOpen} onOpenChange={setAllergyDialogOpen}>
                  <DialogTrigger asChild>
                    <Button size="sm" variant="outline" className="gap-1" data-testid="add-allergy-btn">
                      <Plus className="w-4 h-4" /> Add
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>Add Allergy</DialogTitle>
                    </DialogHeader>
                    <form onSubmit={handleSaveAllergy} className="space-y-4 mt-4">
                      <div className="space-y-2">
                        <Label>Allergen *</Label>
                        <Input value={newAllergy.allergen} onChange={(e) => setNewAllergy({ ...newAllergy, allergen: e.target.value })} required data-testid="allergy-allergen" />
                      </div>
                      <div className="space-y-2">
                        <Label>Reaction *</Label>
                        <Input value={newAllergy.reaction} onChange={(e) => setNewAllergy({ ...newAllergy, reaction: e.target.value })} required data-testid="allergy-reaction" />
                      </div>
                      <div className="space-y-2">
                        <Label>Severity</Label>
                        <Select value={newAllergy.severity} onValueChange={(v) => setNewAllergy({ ...newAllergy, severity: v })}>
                          <SelectTrigger data-testid="allergy-severity">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="mild">Mild</SelectItem>
                            <SelectItem value="moderate">Moderate</SelectItem>
                            <SelectItem value="severe">Severe</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <Button type="submit" className="w-full" disabled={saving} data-testid="save-allergy-btn">
                        {saving ? 'Saving...' : 'Save Allergy'}
                      </Button>
                    </form>
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent>
                {allergies.length === 0 ? (
                  <p className="text-slate-500 text-center py-4">No known drug allergies (NKDA)</p>
                ) : (
                  <div className="space-y-2">
                    {allergies.map((allergy) => (
                      <div key={allergy.id} className="p-3 rounded-lg bg-red-50 border border-red-100" data-testid={`allergy-${allergy.id}`}>
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-red-900">{allergy.allergen}</span>
                          <Badge className={`text-xs ${allergy.severity === 'severe' ? 'bg-red-600' : allergy.severity === 'moderate' ? 'bg-amber-500' : 'bg-slate-400'}`}>
                            {allergy.severity}
                          </Badge>
                        </div>
                        <p className="text-sm text-red-700 mt-1">Reaction: {allergy.reaction}</p>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Vitals Tab */}
        <TabsContent value="vitals" className="mt-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Vital Signs</CardTitle>
                <CardDescription>Track patient vitals over time</CardDescription>
              </div>
              <Dialog open={vitalsDialogOpen} onOpenChange={setVitalsDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="gap-2" data-testid="add-vitals-btn">
                    <Plus className="w-4 h-4" /> Record Vitals
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-lg">
                  <DialogHeader>
                    <DialogTitle>Record Vital Signs</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleSaveVitals} className="space-y-4 mt-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label className="flex items-center gap-1"><Heart className="w-3 h-3" /> Systolic (mmHg)</Label>
                        <Input type="number" value={newVitals.blood_pressure_systolic} onChange={(e) => setNewVitals({ ...newVitals, blood_pressure_systolic: e.target.value })} data-testid="vitals-systolic" />
                      </div>
                      <div className="space-y-2">
                        <Label className="flex items-center gap-1"><Heart className="w-3 h-3" /> Diastolic (mmHg)</Label>
                        <Input type="number" value={newVitals.blood_pressure_diastolic} onChange={(e) => setNewVitals({ ...newVitals, blood_pressure_diastolic: e.target.value })} data-testid="vitals-diastolic" />
                      </div>
                      <div className="space-y-2">
                        <Label className="flex items-center gap-1"><Activity className="w-3 h-3" /> Heart Rate (bpm)</Label>
                        <Input type="number" value={newVitals.heart_rate} onChange={(e) => setNewVitals({ ...newVitals, heart_rate: e.target.value })} data-testid="vitals-hr" />
                      </div>
                      <div className="space-y-2">
                        <Label className="flex items-center gap-1"><Wind className="w-3 h-3" /> Resp Rate</Label>
                        <Input type="number" value={newVitals.respiratory_rate} onChange={(e) => setNewVitals({ ...newVitals, respiratory_rate: e.target.value })} data-testid="vitals-rr" />
                      </div>
                      <div className="space-y-2">
                        <Label className="flex items-center gap-1"><Thermometer className="w-3 h-3" /> Temp (°F)</Label>
                        <Input type="number" step="0.1" value={newVitals.temperature} onChange={(e) => setNewVitals({ ...newVitals, temperature: e.target.value })} data-testid="vitals-temp" />
                      </div>
                      <div className="space-y-2">
                        <Label className="flex items-center gap-1"><Droplets className="w-3 h-3" /> SpO2 (%)</Label>
                        <Input type="number" value={newVitals.oxygen_saturation} onChange={(e) => setNewVitals({ ...newVitals, oxygen_saturation: e.target.value })} data-testid="vitals-spo2" />
                      </div>
                      <div className="space-y-2">
                        <Label className="flex items-center gap-1"><Scale className="w-3 h-3" /> Weight (kg)</Label>
                        <Input type="number" step="0.1" value={newVitals.weight} onChange={(e) => setNewVitals({ ...newVitals, weight: e.target.value })} data-testid="vitals-weight" />
                      </div>
                      <div className="space-y-2">
                        <Label className="flex items-center gap-1"><Ruler className="w-3 h-3" /> Height (cm)</Label>
                        <Input type="number" value={newVitals.height} onChange={(e) => setNewVitals({ ...newVitals, height: e.target.value })} data-testid="vitals-height" />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Notes</Label>
                      <Textarea value={newVitals.notes} onChange={(e) => setNewVitals({ ...newVitals, notes: e.target.value })} data-testid="vitals-notes" />
                    </div>
                    <Button type="submit" className="w-full" disabled={saving} data-testid="save-vitals-btn">
                      {saving ? 'Saving...' : 'Save Vitals'}
                    </Button>
                  </form>
                </DialogContent>
              </Dialog>
            </CardHeader>
            <CardContent>
              {vitals.length === 0 ? (
                <p className="text-slate-500 text-center py-8">No vitals recorded yet</p>
              ) : (
                <div className="space-y-3">
                  {vitals.map((v) => (
                    <div key={v.id} className="p-4 rounded-lg border border-slate-200 hover:border-sky-200 transition-colors" data-testid={`vitals-${v.id}`}>
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-sm text-slate-500">{formatDateTime(v.recorded_at)}</span>
                      </div>
                      <div className="grid grid-cols-4 gap-4 text-sm">
                        {v.blood_pressure_systolic && (
                          <div><span className="text-slate-500">BP:</span> <span className="font-medium">{v.blood_pressure_systolic}/{v.blood_pressure_diastolic} mmHg</span></div>
                        )}
                        {v.heart_rate && (
                          <div><span className="text-slate-500">HR:</span> <span className="font-medium">{v.heart_rate} bpm</span></div>
                        )}
                        {v.respiratory_rate && (
                          <div><span className="text-slate-500">RR:</span> <span className="font-medium">{v.respiratory_rate}/min</span></div>
                        )}
                        {v.temperature && (
                          <div><span className="text-slate-500">Temp:</span> <span className="font-medium">{v.temperature}°F</span></div>
                        )}
                        {v.oxygen_saturation && (
                          <div><span className="text-slate-500">SpO2:</span> <span className="font-medium">{v.oxygen_saturation}%</span></div>
                        )}
                        {v.weight && (
                          <div><span className="text-slate-500">Weight:</span> <span className="font-medium">{v.weight} kg</span></div>
                        )}
                        {v.height && (
                          <div><span className="text-slate-500">Height:</span> <span className="font-medium">{v.height} cm</span></div>
                        )}
                      </div>
                      {v.notes && <p className="text-sm text-slate-600 mt-2 pt-2 border-t">{v.notes}</p>}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Problems Tab */}
        <TabsContent value="problems" className="mt-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Problem List</CardTitle>
                <CardDescription>Active and historical diagnoses</CardDescription>
              </div>
              <Dialog open={problemDialogOpen} onOpenChange={setProblemDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="gap-2" data-testid="add-problem-btn">
                    <Plus className="w-4 h-4" /> Add Problem
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Add Problem / Diagnosis</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleSaveProblem} className="space-y-4 mt-4">
                    <div className="space-y-2">
                      <Label>Description *</Label>
                      <Input value={newProblem.description} onChange={(e) => setNewProblem({ ...newProblem, description: e.target.value })} required data-testid="problem-description" />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>ICD Code</Label>
                        <Input value={newProblem.icd_code} onChange={(e) => setNewProblem({ ...newProblem, icd_code: e.target.value })} placeholder="e.g., I10" data-testid="problem-icd" />
                      </div>
                      <div className="space-y-2">
                        <Label>Onset Date</Label>
                        <Input type="date" value={newProblem.onset_date} onChange={(e) => setNewProblem({ ...newProblem, onset_date: e.target.value })} data-testid="problem-onset" />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Status</Label>
                      <Select value={newProblem.status} onValueChange={(v) => setNewProblem({ ...newProblem, status: v })}>
                        <SelectTrigger data-testid="problem-status">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="active">Active</SelectItem>
                          <SelectItem value="resolved">Resolved</SelectItem>
                          <SelectItem value="chronic">Chronic</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Notes</Label>
                      <Textarea value={newProblem.notes} onChange={(e) => setNewProblem({ ...newProblem, notes: e.target.value })} data-testid="problem-notes" />
                    </div>
                    <Button type="submit" className="w-full" disabled={saving} data-testid="save-problem-btn">
                      {saving ? 'Saving...' : 'Save Problem'}
                    </Button>
                  </form>
                </DialogContent>
              </Dialog>
            </CardHeader>
            <CardContent>
              {problems.length === 0 ? (
                <p className="text-slate-500 text-center py-8">No problems documented</p>
              ) : (
                <div className="space-y-2">
                  {problems.map((p) => (
                    <div key={p.id} className="p-4 rounded-lg border border-slate-200 hover:border-sky-200 transition-colors" data-testid={`problem-${p.id}`}>
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-slate-900">{p.description}</p>
                          <p className="text-sm text-slate-500">
                            {p.icd_code && <span className="font-mono mr-2">{p.icd_code}</span>}
                            {p.onset_date && <span>Onset: {formatDate(p.onset_date)}</span>}
                          </p>
                        </div>
                        <Badge className={getStatusColor(p.status)}>{p.status}</Badge>
                      </div>
                      {p.notes && <p className="text-sm text-slate-600 mt-2">{p.notes}</p>}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Medications Tab */}
        <TabsContent value="medications" className="mt-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Medications</CardTitle>
                <CardDescription>Current and past medications</CardDescription>
              </div>
              {/* Hide Add Medication for nurses, nursing supervisors, and floor supervisors - they can only view medications */}
              {!['nurse', 'nursing_supervisor', 'floor_supervisor'].includes(user?.role) && (
              <Dialog open={medDialogOpen} onOpenChange={setMedDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="gap-2" data-testid="add-medication-btn">
                    <Plus className="w-4 h-4" /> Add Medication
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Add Medication</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleSaveMedication} className="space-y-4 mt-4">
                    <div className="space-y-2">
                      <Label>Medication Name *</Label>
                      <Input value={newMedication.name} onChange={(e) => setNewMedication({ ...newMedication, name: e.target.value })} required data-testid="med-name" />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Dosage *</Label>
                        <Input value={newMedication.dosage} onChange={(e) => setNewMedication({ ...newMedication, dosage: e.target.value })} placeholder="e.g., 10mg" required data-testid="med-dosage" />
                      </div>
                      <div className="space-y-2">
                        <Label>Frequency *</Label>
                        <Input value={newMedication.frequency} onChange={(e) => setNewMedication({ ...newMedication, frequency: e.target.value })} placeholder="e.g., BID" required data-testid="med-frequency" />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Route</Label>
                      <Select value={newMedication.route} onValueChange={(v) => setNewMedication({ ...newMedication, route: v })}>
                        <SelectTrigger data-testid="med-route">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="oral">Oral</SelectItem>
                          <SelectItem value="IV">IV</SelectItem>
                          <SelectItem value="IM">IM</SelectItem>
                          <SelectItem value="topical">Topical</SelectItem>
                          <SelectItem value="inhaled">Inhaled</SelectItem>
                          <SelectItem value="sublingual">Sublingual</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Start Date</Label>
                        <Input type="date" value={newMedication.start_date} onChange={(e) => setNewMedication({ ...newMedication, start_date: e.target.value })} data-testid="med-start" />
                      </div>
                      <div className="space-y-2">
                        <Label>End Date</Label>
                        <Input type="date" value={newMedication.end_date} onChange={(e) => setNewMedication({ ...newMedication, end_date: e.target.value })} data-testid="med-end" />
                      </div>
                    </div>
                    <Button type="submit" className="w-full" disabled={saving} data-testid="save-medication-btn">
                      {saving ? 'Saving...' : 'Save Medication'}
                    </Button>
                  </form>
                </DialogContent>
              </Dialog>
              )}
              {['nurse', 'nursing_supervisor', 'floor_supervisor'].includes(user?.role) && (
                <Badge variant="outline" className="text-amber-600 border-amber-300">
                  View Only
                </Badge>
              )}
            </CardHeader>
            <CardContent>
              {medications.length === 0 ? (
                <p className="text-slate-500 text-center py-8">No medications documented</p>
              ) : (
                <div className="space-y-2">
                  {medications.map((m) => (
                    <div key={m.id} className="p-4 rounded-lg border border-slate-200 hover:border-sky-200 transition-colors" data-testid={`medication-${m.id}`}>
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-slate-900">{m.name}</p>
                          <p className="text-sm text-slate-500">
                            {m.dosage} • {m.frequency} • {m.route}
                          </p>
                        </div>
                        <Badge className={getStatusColor(m.status)}>{m.status}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notes Tab */}
        <TabsContent value="notes" className="mt-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Clinical Notes</CardTitle>
                <CardDescription>Progress notes, H&P, and documentation</CardDescription>
              </div>
              <div className="flex gap-2">
                <Dialog open={aiDialogOpen} onOpenChange={setAiDialogOpen}>
                  <DialogTrigger asChild>
                    <Button variant="outline" className="gap-2" data-testid="ai-note-btn">
                      <Sparkles className="w-4 h-4 text-amber-500" /> AI Generate
                    </Button>
                  </DialogTrigger>
                </Dialog>
                <Dialog open={noteDialogOpen} onOpenChange={setNoteDialogOpen}>
                  <DialogTrigger asChild>
                    <Button className="gap-2" data-testid="add-note-btn">
                      <Plus className="w-4 h-4" /> New Note
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                      <DialogTitle>Create Clinical Note</DialogTitle>
                    </DialogHeader>
                    <form onSubmit={handleSaveNote} className="space-y-4 mt-4">
                      <div className="space-y-2">
                        <Label>Note Type</Label>
                        <Select value={newNote.note_type} onValueChange={(v) => setNewNote({ ...newNote, note_type: v })}>
                          <SelectTrigger data-testid="note-type">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="progress_note">Progress Note</SelectItem>
                            <SelectItem value="h_and_p">History & Physical</SelectItem>
                            <SelectItem value="discharge_summary">Discharge Summary</SelectItem>
                            <SelectItem value="consultation">Consultation</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label>Chief Complaint</Label>
                        <Input value={newNote.chief_complaint} onChange={(e) => setNewNote({ ...newNote, chief_complaint: e.target.value })} data-testid="note-cc" />
                      </div>
                      <div className="space-y-2">
                        <Label>Subjective</Label>
                        <Textarea value={newNote.subjective} onChange={(e) => setNewNote({ ...newNote, subjective: e.target.value })} rows={3} data-testid="note-subjective" />
                      </div>
                      <div className="space-y-2">
                        <Label>Objective</Label>
                        <Textarea value={newNote.objective} onChange={(e) => setNewNote({ ...newNote, objective: e.target.value })} rows={3} data-testid="note-objective" />
                      </div>
                      <div className="space-y-2">
                        <Label>Assessment</Label>
                        <Textarea value={newNote.assessment} onChange={(e) => setNewNote({ ...newNote, assessment: e.target.value })} rows={3} data-testid="note-assessment" />
                      </div>
                      <div className="space-y-2">
                        <Label>Plan</Label>
                        <Textarea value={newNote.plan} onChange={(e) => setNewNote({ ...newNote, plan: e.target.value })} rows={3} data-testid="note-plan" />
                      </div>
                      {newNote.content && (
                        <div className="space-y-2">
                          <Label>AI Generated Content</Label>
                          <Textarea value={newNote.content} onChange={(e) => setNewNote({ ...newNote, content: e.target.value })} rows={8} className="font-mono text-sm" data-testid="note-content" />
                        </div>
                      )}
                      <Button type="submit" className="w-full" disabled={saving} data-testid="save-note-btn">
                        {saving ? 'Saving...' : 'Save Note'}
                      </Button>
                    </form>
                  </DialogContent>
                </Dialog>
              </div>
            </CardHeader>
            <CardContent>
              {notes.length === 0 ? (
                <p className="text-slate-500 text-center py-8">No clinical notes</p>
              ) : (
                <div className="space-y-3">
                  {notes.map((n) => (
                    <div key={n.id} className="p-4 rounded-lg border border-slate-200 hover:border-sky-200 transition-colors" data-testid={`note-${n.id}`}>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="capitalize">{n.note_type.replace('_', ' ')}</Badge>
                          {n.signed && <Badge className="bg-emerald-100 text-emerald-700"><Check className="w-3 h-3 mr-1" /> Signed</Badge>}
                        </div>
                        <span className="text-sm text-slate-500">{formatDateTime(n.created_at)}</span>
                      </div>
                      <p className="text-sm text-slate-600 mb-1">Author: {n.author_name}</p>
                      {n.chief_complaint && <p className="text-sm"><span className="font-medium">CC:</span> {n.chief_complaint}</p>}
                      {n.assessment && <p className="text-sm mt-2"><span className="font-medium">Assessment:</span> {n.assessment}</p>}
                      {n.plan && <p className="text-sm mt-2"><span className="font-medium">Plan:</span> {n.plan}</p>}
                      {n.content && <p className="text-sm mt-2 whitespace-pre-wrap">{n.content.substring(0, 300)}...</p>}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Orders Tab */}
        <TabsContent value="orders" className="mt-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Orders</CardTitle>
                <CardDescription>Labs, imaging, and medication orders</CardDescription>
              </div>
              {/* Hide New Order for nurses, nursing supervisors, and floor supervisors */}
              {!['nurse', 'nursing_supervisor', 'floor_supervisor'].includes(user?.role) ? (
              <Dialog open={orderDialogOpen} onOpenChange={setOrderDialogOpen}>
                <DialogTrigger asChild>
                  <Button className="gap-2" data-testid="add-order-btn">
                    <Plus className="w-4 h-4" /> New Order
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Place Order</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleSaveOrder} className="space-y-4 mt-4">
                    <div className="space-y-2">
                      <Label>Order Type</Label>
                      <Select value={newOrder.order_type} onValueChange={(v) => setNewOrder({ ...newOrder, order_type: v })}>
                        <SelectTrigger data-testid="order-type">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="lab">Lab</SelectItem>
                          <SelectItem value="imaging">Imaging</SelectItem>
                          <SelectItem value="medication">Medication</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Description *</Label>
                      <Input value={newOrder.description} onChange={(e) => setNewOrder({ ...newOrder, description: e.target.value })} placeholder="e.g., CBC with Differential" required data-testid="order-description" />
                    </div>
                    <div className="space-y-2">
                      <Label>Priority</Label>
                      <Select value={newOrder.priority} onValueChange={(v) => setNewOrder({ ...newOrder, priority: v })}>
                        <SelectTrigger data-testid="order-priority">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="routine">Routine</SelectItem>
                          <SelectItem value="urgent">Urgent</SelectItem>
                          <SelectItem value="stat">STAT</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Diagnosis / Indication</Label>
                      <Input value={newOrder.diagnosis} onChange={(e) => setNewOrder({ ...newOrder, diagnosis: e.target.value })} data-testid="order-diagnosis" />
                    </div>
                    <div className="space-y-2">
                      <Label>Instructions</Label>
                      <Textarea value={newOrder.instructions} onChange={(e) => setNewOrder({ ...newOrder, instructions: e.target.value })} data-testid="order-instructions" />
                    </div>
                    <Button type="submit" className="w-full" disabled={saving} data-testid="save-order-btn">
                      {saving ? 'Placing Order...' : 'Place Order'}
                    </Button>
                  </form>
                </DialogContent>
              </Dialog>
              ) : (
                <Badge variant="outline" className="text-amber-600 border-amber-300">
                  View Only
                </Badge>
              )}
            </CardHeader>
            <CardContent>
              {orders.length === 0 ? (
                <p className="text-slate-500 text-center py-8">No orders placed</p>
              ) : (
                <div className="space-y-2">
                  {orders.map((o) => (
                    <div key={o.id} className="p-4 rounded-lg border border-slate-200 hover:border-sky-200 transition-colors" data-testid={`order-${o.id}`}>
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <Badge variant="outline" className="capitalize">{o.order_type}</Badge>
                            <Badge className={o.priority === 'stat' ? 'bg-red-100 text-red-700' : o.priority === 'urgent' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-700'}>
                              {o.priority}
                            </Badge>
                          </div>
                          <p className="font-medium text-slate-900">{o.description}</p>
                          <p className="text-sm text-slate-500">Ordered by: {o.ordered_by_name} • {formatDateTime(o.created_at)}</p>
                        </div>
                        <Badge className={getStatusColor(o.status)}>{o.status}</Badge>
                      </div>
                      {o.result && <p className="text-sm mt-2 p-2 bg-slate-50 rounded"><span className="font-medium">Result:</span> {o.result}</p>}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Labs Tab */}
        <TabsContent value="labs" className="mt-6 space-y-6">
          {/* Lab Orders Card */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <FlaskConical className="w-5 h-5" /> Lab Orders
              </CardTitle>
              {/* Hide Order Lab for nurses, nursing supervisors, and floor supervisors - they can only view lab orders and results */}
              {!['nurse', 'nursing_supervisor', 'floor_supervisor'].includes(user?.role) ? (
              <Dialog open={labOrderDialogOpen} onOpenChange={setLabOrderDialogOpen}>
                <DialogTrigger asChild>
                  <Button size="sm" className="gap-2" data-testid="add-lab-order-btn">
                    <Plus className="w-4 h-4" /> Order Lab
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Order Lab Test</DialogTitle>
                    <DialogDescription>Select lab panel and specify details</DialogDescription>
                  </DialogHeader>
                  <form onSubmit={handleSaveLabOrder} className="space-y-4 mt-4">
                    <div className="space-y-2">
                      <Label>Lab Panel</Label>
                      <Select value={newLabOrder.panel_code} onValueChange={(v) => setNewLabOrder({ ...newLabOrder, panel_code: v })}>
                        <SelectTrigger data-testid="lab-panel-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {labPanels.map((panel) => (
                            <SelectItem key={panel.code} value={panel.code}>
                              {panel.name} ({panel.test_count} tests)
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Priority</Label>
                      <Select value={newLabOrder.priority} onValueChange={(v) => setNewLabOrder({ ...newLabOrder, priority: v })}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="routine">Routine</SelectItem>
                          <SelectItem value="urgent">Urgent</SelectItem>
                          <SelectItem value="stat">STAT</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Clinical Notes</Label>
                      <Textarea 
                        value={newLabOrder.clinical_notes} 
                        onChange={(e) => setNewLabOrder({ ...newLabOrder, clinical_notes: e.target.value })}
                        placeholder="Relevant clinical information..."
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Diagnosis/Indication</Label>
                      <Input 
                        value={newLabOrder.diagnosis} 
                        onChange={(e) => setNewLabOrder({ ...newLabOrder, diagnosis: e.target.value })}
                        placeholder="e.g., Annual wellness exam, R73.03"
                      />
                    </div>
                    <div className="flex items-center gap-2">
                      <input 
                        type="checkbox" 
                        id="fasting"
                        checked={newLabOrder.fasting_required}
                        onChange={(e) => setNewLabOrder({ ...newLabOrder, fasting_required: e.target.checked })}
                        className="rounded"
                      />
                      <Label htmlFor="fasting">Fasting Required</Label>
                    </div>
                    <Button type="submit" className="w-full" disabled={saving}>
                      {saving ? 'Ordering...' : 'Place Lab Order'}
                    </Button>
                  </form>
                </DialogContent>
              </Dialog>
              ) : (
                <Badge variant="outline" className="text-amber-600 border-amber-300">
                  View Only
                </Badge>
              )}
            </CardHeader>
            <CardContent>
              {labOrders.length === 0 ? (
                <p className="text-slate-500 text-center py-8">No lab orders placed</p>
              ) : (
                <div className="space-y-2">
                  {labOrders.map((order) => (
                    <div key={order.id} className="p-4 rounded-lg border border-slate-200 hover:border-sky-200 transition-colors" data-testid={`lab-order-${order.id}`}>
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-slate-900">{order.panel_name}</span>
                            <Badge className={order.priority === 'stat' ? 'bg-red-100 text-red-700' : order.priority === 'urgent' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-700'}>
                              {order.priority}
                            </Badge>
                          </div>
                          <p className="text-sm text-slate-500">
                            Accession: <span className="font-mono">{order.accession_number}</span> • 
                            Ordered: {formatDateTime(order.ordered_at)}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge className={getStatusColor(order.status)}>{order.status}</Badge>
                          {order.status === 'ordered' && (
                            <Button 
                              size="sm" 
                              variant="outline" 
                              onClick={() => handleSimulateLabResults(order.id)}
                              disabled={simulatingLab === order.id}
                              data-testid={`simulate-results-${order.id}`}
                            >
                              {simulatingLab === order.id ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Simulate Results'}
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Lab Results Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5" /> Lab Results
              </CardTitle>
              <CardDescription>Recent laboratory test results</CardDescription>
            </CardHeader>
            <CardContent>
              {labResults.length === 0 ? (
                <p className="text-slate-500 text-center py-8">No lab results available</p>
              ) : (
                <div className="space-y-4">
                  {labResults.map((result) => (
                    <Card key={result.id} className="border-l-4 border-l-sky-500">
                      <CardHeader className="py-3">
                        <div className="flex items-center justify-between">
                          <div>
                            <CardTitle className="text-base">{result.panel_name}</CardTitle>
                            <CardDescription>
                              {formatDateTime(result.resulted_at)} • {result.performing_lab}
                            </CardDescription>
                          </div>
                          <Badge variant="outline" className="font-mono text-xs">{result.accession_number}</Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="pt-0">
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b">
                                <th className="text-left py-2 font-medium text-slate-600">Test</th>
                                <th className="text-right py-2 font-medium text-slate-600">Result</th>
                                <th className="text-center py-2 font-medium text-slate-600">Flag</th>
                                <th className="text-right py-2 font-medium text-slate-600">Reference Range</th>
                              </tr>
                            </thead>
                            <tbody>
                              {result.results?.map((r, idx) => {
                                const flagInfo = getLabResultFlag(r.flag);
                                return (
                                  <tr key={idx} className="border-b last:border-0">
                                    <td className="py-2">
                                      <span className="font-medium">{r.test_name}</span>
                                      <span className="text-slate-400 ml-1 text-xs">({r.test_code})</span>
                                    </td>
                                    <td className="text-right py-2 font-mono">
                                      <span className={r.flag !== 'N' ? 'font-bold' : ''}>
                                        {r.value}
                                      </span>
                                      <span className="text-slate-500 ml-1">{r.unit}</span>
                                    </td>
                                    <td className="text-center py-2">
                                      {r.flag !== 'N' && (
                                        <Badge className={`${flagInfo.className} text-xs`}>
                                          {r.flag === 'H' || r.flag === 'HH' ? (
                                            <TrendingUp className="w-3 h-3 mr-1" />
                                          ) : r.flag === 'L' || r.flag === 'LL' ? (
                                            <TrendingDown className="w-3 h-3 mr-1" />
                                          ) : null}
                                          {flagInfo.label}
                                        </Badge>
                                      )}
                                    </td>
                                    <td className="text-right py-2 text-slate-500">
                                      {r.reference_low} - {r.reference_high} {r.unit}
                                    </td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                        {result.notes && (
                          <p className="text-sm text-slate-500 mt-3 p-2 bg-slate-50 rounded">
                            <span className="font-medium">Note:</span> {result.notes}
                          </p>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Imaging/Radiology Tab */}
        <TabsContent value="imaging" className="mt-6 space-y-6">
          {/* Radiology Orders Card */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Imaging Orders</CardTitle>
                <CardDescription>Radiology and imaging studies</CardDescription>
              </div>
              {!['nurse', 'nursing_supervisor', 'floor_supervisor'].includes(user?.role) && (
                <Dialog open={radiologyOrderDialogOpen} onOpenChange={setRadiologyOrderDialogOpen}>
                  <Button onClick={() => setRadiologyOrderDialogOpen(true)} className="gap-2 bg-purple-600 hover:bg-purple-700">
                    <Scan className="w-4 h-4" /> Order Imaging
                  </Button>
                  <DialogContent className="max-w-2xl">
                    <DialogHeader>
                      <DialogTitle>Order Radiology Study</DialogTitle>
                      <DialogDescription>Place imaging order for {patient?.first_name} {patient?.last_name}</DialogDescription>
                    </DialogHeader>
                    <form onSubmit={handleSaveRadiologyOrder} className="space-y-4 mt-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Imaging Modality *</Label>
                          <Select value={newRadiologyOrder.modality} onValueChange={handleModalityChange}>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              {radiologyModalities.map(mod => (
                                <SelectItem key={mod.value} value={mod.value}>
                                  {mod.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <Label>Study Type *</Label>
                          <Select 
                            value={newRadiologyOrder.study_type} 
                            onValueChange={(v) => {
                              const study = radiologyStudyTypes.find(s => s.code === v);
                              setNewRadiologyOrder({
                                ...newRadiologyOrder,
                                study_type: study?.name || v,
                                body_part: study?.body_part || ''
                              });
                            }}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select study type" />
                            </SelectTrigger>
                            <SelectContent>
                              {radiologyStudyTypes.map(study => (
                                <SelectItem key={study.code} value={study.code}>
                                  {study.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Body Part</Label>
                          <Input 
                            value={newRadiologyOrder.body_part}
                            onChange={(e) => setNewRadiologyOrder({...newRadiologyOrder, body_part: e.target.value})}
                            placeholder="Auto-filled from study type"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Laterality</Label>
                          <Select value={newRadiologyOrder.laterality} onValueChange={(v) => setNewRadiologyOrder({...newRadiologyOrder, laterality: v})}>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="bilateral">Bilateral</SelectItem>
                              <SelectItem value="left">Left</SelectItem>
                              <SelectItem value="right">Right</SelectItem>
                              <SelectItem value="na">N/A</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      
                      <div className="space-y-2">
                        <Label>Clinical Indication *</Label>
                        <Textarea
                          value={newRadiologyOrder.clinical_indication}
                          onChange={(e) => setNewRadiologyOrder({...newRadiologyOrder, clinical_indication: e.target.value})}
                          placeholder="Reason for imaging study..."
                          rows={3}
                          required
                        />
                      </div>
                      
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Priority</Label>
                          <Select value={newRadiologyOrder.priority} onValueChange={(v) => setNewRadiologyOrder({...newRadiologyOrder, priority: v})}>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="routine">Routine</SelectItem>
                              <SelectItem value="urgent">Urgent</SelectItem>
                              <SelectItem value="stat">STAT</SelectItem>
                              <SelectItem value="emergency">Emergency</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <Label className="flex items-center gap-2">
                            <input
                              type="checkbox"
                              checked={newRadiologyOrder.contrast_required}
                              onChange={(e) => setNewRadiologyOrder({...newRadiologyOrder, contrast_required: e.target.checked})}
                              className="rounded"
                            />
                            Contrast Required
                          </Label>
                        </div>
                      </div>
                      
                      <div className="space-y-2">
                        <Label>Special Instructions</Label>
                        <Textarea
                          value={newRadiologyOrder.special_instructions}
                          onChange={(e) => setNewRadiologyOrder({...newRadiologyOrder, special_instructions: e.target.value})}
                          placeholder="Any special instructions or precautions..."
                          rows={2}
                        />
                      </div>
                      
                      <Button type="submit" className="w-full bg-purple-600 hover:bg-purple-700" disabled={saving}>
                        {saving ? 'Placing Order...' : 'Place Imaging Order'}
                      </Button>
                    </form>
                  </DialogContent>
                </Dialog>
              )}
            </CardHeader>
            <CardContent>
              {radiologyOrders.length === 0 ? (
                <p className="text-slate-500 text-center py-8">No imaging orders placed</p>
              ) : (
                <div className="space-y-4">
                  {radiologyOrders.map((order) => (
                    <Card key={order.id} className="border-purple-200">
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <div>
                            <CardTitle className="text-base flex items-center gap-2">
                              <Scan className="w-5 h-5 text-purple-600" />
                              {order.study_type}
                            </CardTitle>
                            <CardDescription className="mt-1">
                              Accession: {order.accession_number} • {order.modality?.toUpperCase()}
                            </CardDescription>
                          </div>
                          <div className="flex gap-2">
                            <Badge className={getPriorityBadge(order.priority)}>
                              {order.priority?.toUpperCase()}
                            </Badge>
                            <Badge className={getStatusBadge(order.status)}>
                              {order.status?.replace(/_/g, ' ')}
                            </Badge>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2 text-sm">
                          <p><span className="font-medium">Body Part:</span> {order.body_part} ({order.laterality})</p>
                          <p><span className="font-medium">Indication:</span> {order.clinical_indication}</p>
                          <p><span className="font-medium">Contrast:</span> {order.contrast_required ? 'Required' : 'Not Required'}</p>
                          <p className="text-slate-500">Ordered: {new Date(order.created_at).toLocaleDateString()}</p>
                          {order.result && (
                            <div className="mt-4 p-4 bg-emerald-50 rounded-lg border border-emerald-200">
                              <h5 className="font-medium text-emerald-800 mb-2">Radiology Report</h5>
                              <p className="text-sm"><span className="font-medium">Findings:</span> {order.result.findings}</p>
                              <p className="text-sm mt-1"><span className="font-medium">Impression:</span> {order.result.impression}</p>
                              {order.result.recommendations && (
                                <p className="text-sm mt-1"><span className="font-medium">Recommendations:</span> {order.result.recommendations}</p>
                              )}
                              {order.result.critical_finding && (
                                <Badge className="mt-2 bg-red-100 text-red-700">
                                  <AlertTriangle className="w-3 h-3 mr-1" /> Critical Finding
                                </Badge>
                              )}
                            </div>
                          )}
                        </div>
                      </CardContent>
                    </Card>
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
