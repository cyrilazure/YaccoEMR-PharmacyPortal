import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Activity, Heart, Thermometer, Droplets, Scale,
  Pill, AlertTriangle, FileText, Calendar, Clock, User,
  ChevronDown, ChevronUp, Loader2, Plus, Edit, Stethoscope,
  TrendingUp, TrendingDown, Minus, History, ClipboardList,
  Image, Syringe, Users, RefreshCw, Filter
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Status colors
const CONDITION_STATUS_COLORS = {
  active: 'bg-red-100 text-red-800',
  managed: 'bg-yellow-100 text-yellow-800',
  resolved: 'bg-green-100 text-green-800',
  in_remission: 'bg-blue-100 text-blue-800'
};

const SEVERITY_COLORS = {
  mild: 'bg-green-100 text-green-700',
  moderate: 'bg-yellow-100 text-yellow-700',
  severe: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700'
};

export default function PatientHistoryTab({ patientId: propPatientId }) {
  const params = useParams();
  const navigate = useNavigate();
  const patientId = propPatientId || params.patientId;
  
  const [loading, setLoading] = useState(true);
  const [history, setHistory] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [timeline, setTimeline] = useState([]);
  const [timelineLoading, setTimelineLoading] = useState(false);
  
  // Add condition dialog
  const [showAddCondition, setShowAddCondition] = useState(false);
  const [conditionForm, setConditionForm] = useState({
    condition_type: 'chronic',
    condition_name: '',
    icd_code: '',
    description: '',
    onset_date: '',
    severity: 'moderate',
    current_treatment: '',
    notes: ''
  });
  const [submitting, setSubmitting] = useState(false);

  const getToken = () => localStorage.getItem('yacco_token');
  
  const authHeaders = {
    'Authorization': `Bearer ${getToken()}`,
    'Content-Type': 'application/json'
  };

  // Fetch patient history
  const fetchHistory = useCallback(async () => {
    if (!patientId) return;
    
    try {
      setLoading(true);
      const response = await fetch(
        `${API_URL}/api/patients/${patientId}/history?include_vitals=true&include_labs=true&include_imaging=true&include_prescriptions=true`,
        { headers: authHeaders }
      );
      
      if (response.ok) {
        const data = await response.json();
        setHistory(data);
      } else {
        toast.error('Failed to load patient history');
      }
    } catch (error) {
      console.error('Error fetching history:', error);
      toast.error('Error loading patient history');
    } finally {
      setLoading(false);
    }
  }, [patientId]);

  // Fetch timeline
  const fetchTimeline = useCallback(async () => {
    if (!patientId) return;
    
    try {
      setTimelineLoading(true);
      const response = await fetch(
        `${API_URL}/api/patients/${patientId}/timeline?days_back=365&limit=100`,
        { headers: authHeaders }
      );
      
      if (response.ok) {
        const data = await response.json();
        setTimeline(data.timeline || []);
      }
    } catch (error) {
      console.error('Error fetching timeline:', error);
    } finally {
      setTimelineLoading(false);
    }
  }, [patientId]);

  useEffect(() => {
    fetchHistory();
    fetchTimeline();
  }, [fetchHistory, fetchTimeline]);

  // Add new condition
  const handleAddCondition = async () => {
    if (!conditionForm.condition_name) {
      toast.error('Please enter a condition name');
      return;
    }
    
    try {
      setSubmitting(true);
      const response = await fetch(
        `${API_URL}/api/patients/${patientId}/conditions`,
        {
          method: 'POST',
          headers: authHeaders,
          body: JSON.stringify(conditionForm)
        }
      );
      
      if (response.ok) {
        toast.success('Condition added successfully');
        setShowAddCondition(false);
        setConditionForm({
          condition_type: 'chronic',
          condition_name: '',
          icd_code: '',
          description: '',
          onset_date: '',
          severity: 'moderate',
          current_treatment: '',
          notes: ''
        });
        fetchHistory();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to add condition');
      }
    } catch (error) {
      toast.error('Error adding condition');
    } finally {
      setSubmitting(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Prepare vital chart data
  const prepareVitalChartData = () => {
    if (!history?.vitals) return [];
    
    return history.vitals.slice(0, 20).reverse().map(v => ({
      date: formatDate(v.recorded_at),
      systolic: v.blood_pressure_systolic,
      diastolic: v.blood_pressure_diastolic,
      heartRate: v.heart_rate,
      temperature: v.temperature,
      spo2: v.oxygen_saturation
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
        <span className="ml-2 text-gray-500">Loading patient history...</span>
      </div>
    );
  }

  if (!history) {
    return (
      <div className="text-center py-12">
        <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
        <p className="text-gray-500">No patient history found</p>
      </div>
    );
  }

  const { patient, summary, chronic_conditions, past_diagnoses, allergies, 
          current_medications, vitals, family_history, social_history,
          lab_results, imaging_studies, prescriptions, problems } = history;

  return (
    <div className="space-y-6" data-testid="patient-history">
      {/* Patient Header */}
      <Card>
        <CardContent className="py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="h-16 w-16 bg-blue-100 rounded-full flex items-center justify-center">
                <User className="h-8 w-8 text-blue-600" />
              </div>
              <div>
                <h2 className="text-xl font-bold">{patient?.name}</h2>
                <p className="text-sm text-gray-500">MRN: {patient?.mrn}</p>
                <div className="flex items-center gap-4 mt-1 text-sm text-gray-600">
                  <span>DOB: {formatDate(patient?.date_of_birth)}</span>
                  <span>Gender: {patient?.gender}</span>
                  {patient?.blood_type && <span>Blood Type: {patient?.blood_type}</span>}
                </div>
              </div>
            </div>
            <Button 
              variant="outline" 
              onClick={fetchHistory}
              data-testid="refresh-history"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center gap-2">
              <Heart className="h-5 w-5 text-red-500" />
              <div>
                <p className="text-2xl font-bold">{summary?.active_conditions || 0}</p>
                <p className="text-xs text-gray-500">Active Conditions</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-500" />
              <div>
                <p className="text-2xl font-bold">{summary?.total_allergies || 0}</p>
                <p className="text-xs text-gray-500">Allergies</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center gap-2">
              <Pill className="h-5 w-5 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">{summary?.current_medications_count || 0}</p>
                <p className="text-xs text-gray-500">Medications</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center gap-2">
              <ClipboardList className="h-5 w-5 text-purple-500" />
              <div>
                <p className="text-2xl font-bold">{summary?.total_lab_tests || 0}</p>
                <p className="text-xs text-gray-500">Lab Tests</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <div className="flex items-center gap-2">
              <Image className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-2xl font-bold">{summary?.total_imaging_studies || 0}</p>
                <p className="text-xs text-gray-500">Imaging Studies</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-6 w-full">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="conditions">Conditions</TabsTrigger>
          <TabsTrigger value="vitals">Vitals</TabsTrigger>
          <TabsTrigger value="medications">Medications</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="family">Family History</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Active Conditions */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Heart className="h-5 w-5 text-red-500" />
                  Active Conditions
                </CardTitle>
              </CardHeader>
              <CardContent>
                {chronic_conditions?.filter(c => c.status === 'active').length > 0 ? (
                  <div className="space-y-2">
                    {chronic_conditions.filter(c => c.status === 'active').slice(0, 5).map((condition, idx) => (
                      <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                        <div>
                          <p className="font-medium">{condition.condition_name}</p>
                          <p className="text-xs text-gray-500">Since {formatDate(condition.onset_date)}</p>
                        </div>
                        {condition.severity && (
                          <Badge className={SEVERITY_COLORS[condition.severity] || 'bg-gray-100'}>
                            {condition.severity}
                          </Badge>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-sm">No active conditions</p>
                )}
              </CardContent>
            </Card>

            {/* Allergies */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-orange-500" />
                  Allergies
                </CardTitle>
              </CardHeader>
              <CardContent>
                {allergies?.length > 0 ? (
                  <div className="space-y-2">
                    {allergies.slice(0, 5).map((allergy, idx) => (
                      <div key={idx} className="flex items-center justify-between p-2 bg-orange-50 rounded">
                        <div>
                          <p className="font-medium">{allergy.allergen}</p>
                          <p className="text-xs text-gray-500">{allergy.reaction_type}</p>
                        </div>
                        {allergy.severity && (
                          <Badge className={SEVERITY_COLORS[allergy.severity] || 'bg-gray-100'}>
                            {allergy.severity}
                          </Badge>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-green-600 text-sm">No known allergies</p>
                )}
              </CardContent>
            </Card>

            {/* Recent Vitals */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Activity className="h-5 w-5 text-blue-500" />
                  Latest Vitals
                </CardTitle>
              </CardHeader>
              <CardContent>
                {vitals?.[0] ? (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-2 bg-gray-50 rounded">
                      <p className="text-2xl font-bold text-red-600">
                        {vitals[0].blood_pressure_systolic}/{vitals[0].blood_pressure_diastolic}
                      </p>
                      <p className="text-xs text-gray-500">Blood Pressure</p>
                    </div>
                    <div className="text-center p-2 bg-gray-50 rounded">
                      <p className="text-2xl font-bold text-pink-600">{vitals[0].heart_rate}</p>
                      <p className="text-xs text-gray-500">Heart Rate</p>
                    </div>
                    <div className="text-center p-2 bg-gray-50 rounded">
                      <p className="text-2xl font-bold text-orange-600">{vitals[0].temperature}°F</p>
                      <p className="text-xs text-gray-500">Temperature</p>
                    </div>
                    <div className="text-center p-2 bg-gray-50 rounded">
                      <p className="text-2xl font-bold text-blue-600">{vitals[0].oxygen_saturation}%</p>
                      <p className="text-xs text-gray-500">SpO2</p>
                    </div>
                  </div>
                ) : (
                  <p className="text-gray-500 text-sm">No vitals recorded</p>
                )}
              </CardContent>
            </Card>

            {/* Current Medications */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Pill className="h-5 w-5 text-blue-500" />
                  Current Medications
                </CardTitle>
              </CardHeader>
              <CardContent>
                {current_medications?.length > 0 ? (
                  <div className="space-y-2">
                    {current_medications.slice(0, 5).map((med, idx) => (
                      <div key={idx} className="p-2 bg-blue-50 rounded">
                        <p className="font-medium">{med.medication_name}</p>
                        <p className="text-xs text-gray-500">
                          {med.dosage} - {med.frequency}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-sm">No current medications</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Conditions Tab */}
        <TabsContent value="conditions" className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold">Medical Conditions</h3>
            <Button onClick={() => setShowAddCondition(true)} data-testid="add-condition-btn">
              <Plus className="h-4 w-4 mr-2" />
              Add Condition
            </Button>
          </div>
          
          <div className="space-y-4">
            {/* Chronic Conditions */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Chronic Conditions</CardTitle>
              </CardHeader>
              <CardContent>
                {chronic_conditions?.length > 0 ? (
                  <div className="divide-y">
                    {chronic_conditions.map((condition, idx) => (
                      <div key={idx} className="py-3">
                        <div className="flex items-start justify-between">
                          <div>
                            <div className="flex items-center gap-2">
                              <p className="font-semibold">{condition.condition_name}</p>
                              <Badge className={CONDITION_STATUS_COLORS[condition.status] || 'bg-gray-100'}>
                                {condition.status}
                              </Badge>
                            </div>
                            {condition.icd_code && (
                              <p className="text-xs text-gray-500">ICD: {condition.icd_code}</p>
                            )}
                            {condition.description && (
                              <p className="text-sm text-gray-600 mt-1">{condition.description}</p>
                            )}
                            {condition.current_treatment && (
                              <p className="text-sm text-blue-600 mt-1">
                                <span className="font-medium">Treatment:</span> {condition.current_treatment}
                              </p>
                            )}
                          </div>
                          <div className="text-right text-sm text-gray-500">
                            <p>Onset: {formatDate(condition.onset_date)}</p>
                            {condition.severity && (
                              <Badge className={SEVERITY_COLORS[condition.severity] || 'bg-gray-100'}>
                                {condition.severity}
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500">No chronic conditions recorded</p>
                )}
              </CardContent>
            </Card>

            {/* Past Diagnoses */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Past Diagnoses & Procedures</CardTitle>
              </CardHeader>
              <CardContent>
                {past_diagnoses?.length > 0 ? (
                  <div className="divide-y">
                    {past_diagnoses.map((diagnosis, idx) => (
                      <div key={idx} className="py-3">
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="font-medium">{diagnosis.condition_name}</p>
                            <p className="text-sm text-gray-600">{diagnosis.description}</p>
                          </div>
                          <div className="text-right text-sm text-gray-500">
                            <p>{formatDate(diagnosis.onset_date)}</p>
                            {diagnosis.resolved_date && (
                              <p className="text-green-600">Resolved: {formatDate(diagnosis.resolved_date)}</p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500">No past diagnoses recorded</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Vitals Tab */}
        <TabsContent value="vitals" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Blood Pressure & Heart Rate Trends</CardTitle>
            </CardHeader>
            <CardContent>
              {vitals?.length > 0 ? (
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={prepareVitalChartData()}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" fontSize={12} />
                      <YAxis fontSize={12} />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="systolic" stroke="#ef4444" name="Systolic" />
                      <Line type="monotone" dataKey="diastolic" stroke="#f97316" name="Diastolic" />
                      <Line type="monotone" dataKey="heartRate" stroke="#ec4899" name="Heart Rate" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p className="text-gray-500 text-center py-12">No vital signs data available</p>
              )}
            </CardContent>
          </Card>

          {/* Vital History Table */}
          <Card>
            <CardHeader>
              <CardTitle>Vital Signs History</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2">Date</th>
                      <th className="text-center py-2">BP</th>
                      <th className="text-center py-2">HR</th>
                      <th className="text-center py-2">Temp</th>
                      <th className="text-center py-2">SpO2</th>
                      <th className="text-center py-2">Weight</th>
                    </tr>
                  </thead>
                  <tbody>
                    {vitals?.slice(0, 10).map((v, idx) => (
                      <tr key={idx} className="border-b hover:bg-gray-50">
                        <td className="py-2">{formatDateTime(v.recorded_at)}</td>
                        <td className="text-center">{v.blood_pressure_systolic}/{v.blood_pressure_diastolic}</td>
                        <td className="text-center">{v.heart_rate}</td>
                        <td className="text-center">{v.temperature}°F</td>
                        <td className="text-center">{v.oxygen_saturation}%</td>
                        <td className="text-center">{v.weight} kg</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Medications Tab */}
        <TabsContent value="medications" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Current Medications</CardTitle>
            </CardHeader>
            <CardContent>
              {current_medications?.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {current_medications.map((med, idx) => (
                    <div key={idx} className="p-4 border rounded-lg">
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="font-semibold text-lg">{med.medication_name}</p>
                          {med.generic_name && (
                            <p className="text-sm text-gray-500">{med.generic_name}</p>
                          )}
                        </div>
                        <Badge className="bg-green-100 text-green-800">Active</Badge>
                      </div>
                      <div className="mt-3 space-y-1 text-sm">
                        <p><span className="text-gray-500">Dosage:</span> {med.dosage}</p>
                        <p><span className="text-gray-500">Frequency:</span> {med.frequency}</p>
                        <p><span className="text-gray-500">Route:</span> {med.route}</p>
                        {med.prescriber_name && (
                          <p><span className="text-gray-500">Prescriber:</span> {med.prescriber_name}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">No current medications</p>
              )}
            </CardContent>
          </Card>

          {/* Prescription History */}
          <Card>
            <CardHeader>
              <CardTitle>Prescription History</CardTitle>
            </CardHeader>
            <CardContent>
              {prescriptions?.length > 0 ? (
                <div className="space-y-3">
                  {prescriptions.slice(0, 10).map((rx, idx) => (
                    <div key={idx} className="p-3 border rounded-lg">
                      <div className="flex items-center justify-between">
                        <p className="text-sm text-gray-500">{formatDate(rx.created_at)}</p>
                        <Badge className={
                          rx.status === 'active' ? 'bg-blue-100 text-blue-800' :
                          rx.status === 'dispensed' ? 'bg-green-100 text-green-800' :
                          'bg-gray-100 text-gray-800'
                        }>
                          {rx.status}
                        </Badge>
                      </div>
                      <div className="mt-2">
                        {rx.medications?.map((m, midx) => (
                          <p key={midx} className="text-sm">
                            • {m.name} - {m.dosage} ({m.quantity})
                          </p>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">No prescription history</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Timeline Tab */}
        <TabsContent value="timeline" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="h-5 w-5" />
                Medical Timeline
              </CardTitle>
              <CardDescription>Complete history of medical events</CardDescription>
            </CardHeader>
            <CardContent>
              {timelineLoading ? (
                <div className="flex justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </div>
              ) : timeline.length > 0 ? (
                <div className="relative">
                  <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-200"></div>
                  <div className="space-y-6">
                    {timeline.map((event, idx) => (
                      <div key={idx} className="relative pl-10">
                        <div className={`absolute left-2 w-4 h-4 rounded-full border-2 border-white ${
                          event.type === 'condition' ? 'bg-red-500' :
                          event.type === 'prescription' ? 'bg-blue-500' :
                          event.type === 'lab_result' ? 'bg-purple-500' :
                          event.type === 'imaging' ? 'bg-green-500' :
                          event.type === 'clinical_note' ? 'bg-orange-500' :
                          'bg-gray-500'
                        }`}></div>
                        <div className="bg-gray-50 rounded-lg p-3">
                          <div className="flex items-center justify-between">
                            <Badge variant="outline" className="text-xs">
                              {event.type.replace('_', ' ').toUpperCase()}
                            </Badge>
                            <span className="text-xs text-gray-500">{formatDate(event.date)}</span>
                          </div>
                          <p className="font-medium mt-1">{event.title}</p>
                          {event.description && (
                            <p className="text-sm text-gray-600">{event.description}</p>
                          )}
                          {event.status && (
                            <Badge className="mt-2" variant="secondary">{event.status}</Badge>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">No timeline events found</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Family History Tab */}
        <TabsContent value="family" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Family Medical History
              </CardTitle>
            </CardHeader>
            <CardContent>
              {family_history?.length > 0 ? (
                <div className="space-y-3">
                  {family_history.map((item, idx) => (
                    <div key={idx} className="p-3 border rounded-lg">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">{item.condition_name}</p>
                          <p className="text-sm text-gray-500">
                            {item.family_member_relationship}
                          </p>
                        </div>
                        {item.notes && (
                          <p className="text-sm text-gray-600">{item.notes}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">No family history recorded</p>
              )}
            </CardContent>
          </Card>

          {/* Social History */}
          <Card>
            <CardHeader>
              <CardTitle>Social History</CardTitle>
            </CardHeader>
            <CardContent>
              {social_history?.length > 0 ? (
                <div className="space-y-3">
                  {social_history.map((item, idx) => (
                    <div key={idx} className="p-3 border rounded-lg">
                      <p className="font-medium">{item.condition_name}</p>
                      {item.description && (
                        <p className="text-sm text-gray-600">{item.description}</p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">No social history recorded</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Add Condition Dialog */}
      <Dialog open={showAddCondition} onOpenChange={setShowAddCondition}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Add Medical Condition</DialogTitle>
            <DialogDescription>
              Record a new medical condition for this patient
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Condition Type</Label>
                <Select
                  value={conditionForm.condition_type}
                  onValueChange={(v) => setConditionForm({...conditionForm, condition_type: v})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="chronic">Chronic</SelectItem>
                    <SelectItem value="acute">Acute</SelectItem>
                    <SelectItem value="surgical">Surgical</SelectItem>
                    <SelectItem value="family_history">Family History</SelectItem>
                    <SelectItem value="social_history">Social History</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Severity</Label>
                <Select
                  value={conditionForm.severity}
                  onValueChange={(v) => setConditionForm({...conditionForm, severity: v})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="mild">Mild</SelectItem>
                    <SelectItem value="moderate">Moderate</SelectItem>
                    <SelectItem value="severe">Severe</SelectItem>
                    <SelectItem value="critical">Critical</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Condition Name *</Label>
              <Input
                placeholder="e.g., Type 2 Diabetes Mellitus"
                value={conditionForm.condition_name}
                onChange={(e) => setConditionForm({...conditionForm, condition_name: e.target.value})}
                data-testid="condition-name-input"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>ICD Code</Label>
                <Input
                  placeholder="e.g., E11.9"
                  value={conditionForm.icd_code}
                  onChange={(e) => setConditionForm({...conditionForm, icd_code: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <Label>Onset Date</Label>
                <Input
                  type="date"
                  value={conditionForm.onset_date}
                  onChange={(e) => setConditionForm({...conditionForm, onset_date: e.target.value})}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea
                placeholder="Brief description of the condition..."
                value={conditionForm.description}
                onChange={(e) => setConditionForm({...conditionForm, description: e.target.value})}
                rows={2}
              />
            </div>

            <div className="space-y-2">
              <Label>Current Treatment</Label>
              <Textarea
                placeholder="Current treatment plan..."
                value={conditionForm.current_treatment}
                onChange={(e) => setConditionForm({...conditionForm, current_treatment: e.target.value})}
                rows={2}
              />
            </div>

            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea
                placeholder="Additional notes..."
                value={conditionForm.notes}
                onChange={(e) => setConditionForm({...conditionForm, notes: e.target.value})}
                rows={2}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddCondition(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleAddCondition}
              disabled={submitting || !conditionForm.condition_name}
              data-testid="save-condition-btn"
            >
              {submitting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                'Save Condition'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
