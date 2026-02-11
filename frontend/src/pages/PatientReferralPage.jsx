import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Send, Search, Building2, User, FileText, Clock,
  CheckCircle, XCircle, AlertCircle, RefreshCw, Filter, Plus,
  ChevronDown, ChevronUp, Loader2, Phone, MapPin, Calendar,
  ClipboardList, Stethoscope, Pill, Image, History, Download
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
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
import { Textarea } from '../components/ui/textarea';
import { Checkbox } from '../components/ui/checkbox';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Status badge colors
const STATUS_COLORS = {
  draft: 'bg-gray-100 text-gray-800',
  pending: 'bg-yellow-100 text-yellow-800',
  sent: 'bg-blue-100 text-blue-800',
  received: 'bg-purple-100 text-purple-800',
  accepted: 'bg-green-100 text-green-800',
  declined: 'bg-red-100 text-red-800',
  completed: 'bg-emerald-100 text-emerald-800',
  cancelled: 'bg-gray-100 text-gray-800'
};

const PRIORITY_COLORS = {
  routine: 'bg-gray-100 text-gray-700',
  urgent: 'bg-orange-100 text-orange-800',
  emergent: 'bg-red-100 text-red-800',
  stat: 'bg-red-200 text-red-900'
};

export default function PatientReferralPage() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('outgoing');
  const [referrals, setReferrals] = useState([]);
  const [stats, setStats] = useState({ outgoing: {}, incoming: {} });
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  
  // Create referral dialog
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [patientSearchQuery, setPatientSearchQuery] = useState('');
  const [patientResults, setPatientResults] = useState([]);
  const [searchingPatients, setSearchingPatients] = useState(false);
  
  // Hospital search
  const [hospitalSearchQuery, setHospitalSearchQuery] = useState('');
  const [hospitalResults, setHospitalResults] = useState([]);
  const [searchingHospitals, setSearchingHospitals] = useState(false);
  const [selectedHospital, setSelectedHospital] = useState(null);
  
  // Referral form
  const [referralForm, setReferralForm] = useState({
    referral_type: 'standard',
    priority: 'routine',
    reason: '',
    clinical_summary: '',
    diagnosis: '',
    destination_department: '',
    include_medical_history: true,
    include_lab_results: true,
    include_imaging: true,
    include_prescriptions: true,
    referral_notes: ''
  });
  const [submitting, setSubmitting] = useState(false);
  
  // View referral detail
  const [selectedReferral, setSelectedReferral] = useState(null);
  const [showDetailDialog, setShowDetailDialog] = useState(false);

  // Get auth token
  const getToken = () => localStorage.getItem('yacco_token');
  
  const authHeaders = {
    'Authorization': `Bearer ${getToken()}`,
    'Content-Type': 'application/json'
  };

  // Load user from localStorage
  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (userData) {
      setUser(JSON.parse(userData));
    } else {
      navigate('/login');
    }
  }, [navigate]);

  // Fetch referrals
  const fetchReferrals = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        direction: activeTab,
        limit: '100'
      });
      if (statusFilter !== 'all') {
        params.append('status', statusFilter);
      }
      
      const response = await fetch(`${API_URL}/api/referrals/?${params}`, {
        headers: authHeaders
      });
      
      if (response.ok) {
        const data = await response.json();
        setReferrals(data.referrals || []);
      }
    } catch (error) {
      console.error('Error fetching referrals:', error);
      toast.error('Failed to load referrals');
    } finally {
      setLoading(false);
    }
  }, [activeTab, statusFilter]);

  // Fetch stats
  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/referrals/stats/summary`, {
        headers: authHeaders
      });
      
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  }, []);

  useEffect(() => {
    if (user) {
      fetchReferrals();
      fetchStats();
    }
  }, [user, fetchReferrals, fetchStats]);

  // Search patients
  const searchPatients = async (query) => {
    if (query.length < 2) {
      setPatientResults([]);
      return;
    }
    
    try {
      setSearchingPatients(true);
      const response = await fetch(`${API_URL}/api/patients/search?query=${encodeURIComponent(query)}`, {
        headers: authHeaders
      });
      
      if (response.ok) {
        const data = await response.json();
        setPatientResults(data.patients || []);
      }
    } catch (error) {
      console.error('Error searching patients:', error);
    } finally {
      setSearchingPatients(false);
    }
  };

  // Search hospitals
  const searchHospitals = async (query) => {
    if (query.length < 2) {
      setHospitalResults([]);
      return;
    }
    
    try {
      setSearchingHospitals(true);
      const response = await fetch(`${API_URL}/api/referrals/search/hospitals?query=${encodeURIComponent(query)}`, {
        headers: authHeaders
      });
      
      if (response.ok) {
        const data = await response.json();
        setHospitalResults(data.hospitals || []);
      }
    } catch (error) {
      console.error('Error searching hospitals:', error);
    } finally {
      setSearchingHospitals(false);
    }
  };

  // Create referral
  const handleCreateReferral = async () => {
    if (!selectedPatient || !selectedHospital) {
      toast.error('Please select a patient and destination hospital');
      return;
    }
    
    if (!referralForm.reason || !referralForm.clinical_summary) {
      toast.error('Please provide reason and clinical summary');
      return;
    }
    
    try {
      setSubmitting(true);
      
      const payload = {
        patient_id: selectedPatient.id,
        destination_organization_id: selectedHospital.id,
        destination_hospital_name: selectedHospital.name,
        destination_hospital_address: selectedHospital.address,
        destination_department: referralForm.destination_department,
        referral_type: referralForm.referral_type,
        priority: referralForm.priority,
        reason: referralForm.reason,
        clinical_summary: referralForm.clinical_summary,
        diagnosis: referralForm.diagnosis,
        include_medical_history: referralForm.include_medical_history,
        include_lab_results: referralForm.include_lab_results,
        include_imaging: referralForm.include_imaging,
        include_prescriptions: referralForm.include_prescriptions,
        referral_notes: referralForm.referral_notes
      };
      
      const response = await fetch(`${API_URL}/api/referrals/`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify(payload)
      });
      
      if (response.ok) {
        const data = await response.json();
        toast.success(`Referral ${data.referral.referral_number} created successfully`);
        setShowCreateDialog(false);
        resetForm();
        fetchReferrals();
        fetchStats();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to create referral');
      }
    } catch (error) {
      console.error('Error creating referral:', error);
      toast.error('Failed to create referral');
    } finally {
      setSubmitting(false);
    }
  };

  // Update referral status
  const handleUpdateStatus = async (referralId, newStatus, notes = '') => {
    try {
      const response = await fetch(`${API_URL}/api/referrals/${referralId}/status`, {
        method: 'PUT',
        headers: authHeaders,
        body: JSON.stringify({
          status: newStatus,
          receiving_notes: notes
        })
      });
      
      if (response.ok) {
        toast.success(`Referral status updated to ${newStatus}`);
        fetchReferrals();
        fetchStats();
        setShowDetailDialog(false);
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to update status');
      }
    } catch (error) {
      console.error('Error updating status:', error);
      toast.error('Failed to update status');
    }
  };

  const resetForm = () => {
    setSelectedPatient(null);
    setSelectedHospital(null);
    setPatientSearchQuery('');
    setHospitalSearchQuery('');
    setPatientResults([]);
    setHospitalResults([]);
    setReferralForm({
      referral_type: 'standard',
      priority: 'routine',
      reason: '',
      clinical_summary: '',
      diagnosis: '',
      destination_department: '',
      include_medical_history: true,
      include_lab_results: true,
      include_imaging: true,
      include_prescriptions: true,
      referral_notes: ''
    });
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Filter referrals by search query
  const filteredReferrals = referrals.filter(ref => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      ref.patient_name?.toLowerCase().includes(query) ||
      ref.referral_number?.toLowerCase().includes(query) ||
      ref.destination_hospital_name?.toLowerCase().includes(query) ||
      ref.source_hospital_name?.toLowerCase().includes(query)
    );
  });

  return (
    <div className="min-h-screen bg-gray-50" data-testid="referral-page">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Patient Referrals</h1>
              <p className="text-sm text-gray-500">Manage patient transfers between hospitals</p>
            </div>
          </div>
          <Button 
            onClick={() => setShowCreateDialog(true)}
            className="bg-blue-600 hover:bg-blue-700"
            data-testid="create-referral-btn"
          >
            <Plus className="h-4 w-4 mr-2" />
            New Referral
          </Button>
        </div>
      </div>

      <div className="p-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Outgoing Referrals</p>
                  <p className="text-2xl font-bold">{stats.outgoing?.total || 0}</p>
                </div>
                <Send className="h-8 w-8 text-blue-500" />
              </div>
              <p className="text-xs text-gray-400 mt-2">{stats.outgoing?.pending || 0} pending</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Incoming Referrals</p>
                  <p className="text-2xl font-bold">{stats.incoming?.total || 0}</p>
                </div>
                <ArrowLeft className="h-8 w-8 text-purple-500" />
              </div>
              <p className="text-xs text-gray-400 mt-2">{stats.incoming?.pending || 0} awaiting action</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Completed</p>
                  <p className="text-2xl font-bold text-green-600">{stats.outgoing?.completed || 0}</p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-500" />
              </div>
              <p className="text-xs text-gray-400 mt-2">Successfully transferred</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Accepted</p>
                  <p className="text-2xl font-bold text-emerald-600">{stats.incoming?.accepted || 0}</p>
                </div>
                <FileText className="h-8 w-8 text-emerald-500" />
              </div>
              <p className="text-xs text-gray-400 mt-2">Incoming patients</p>
            </CardContent>
          </Card>
        </div>

        {/* Tabs and Filters */}
        <div className="bg-white rounded-lg shadow">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <div className="border-b px-4 py-2 flex items-center justify-between">
              <TabsList>
                <TabsTrigger value="outgoing" data-testid="outgoing-tab">
                  <Send className="h-4 w-4 mr-2" />
                  Outgoing
                </TabsTrigger>
                <TabsTrigger value="incoming" data-testid="incoming-tab">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Incoming
                </TabsTrigger>
                <TabsTrigger value="all">
                  All
                </TabsTrigger>
              </TabsList>
              
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="Search referrals..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9 w-64"
                    data-testid="search-referrals"
                  />
                </div>
                
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-40">
                    <Filter className="h-4 w-4 mr-2" />
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="sent">Sent</SelectItem>
                    <SelectItem value="received">Received</SelectItem>
                    <SelectItem value="accepted">Accepted</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                    <SelectItem value="declined">Declined</SelectItem>
                  </SelectContent>
                </Select>
                
                <Button variant="outline" size="icon" onClick={fetchReferrals}>
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <TabsContent value={activeTab} className="p-0">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                </div>
              ) : filteredReferrals.length === 0 ? (
                <div className="text-center py-12">
                  <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">No referrals found</p>
                </div>
              ) : (
                <div className="divide-y">
                  {filteredReferrals.map((referral) => (
                    <div 
                      key={referral.id}
                      className="p-4 hover:bg-gray-50 cursor-pointer transition-colors"
                      onClick={() => {
                        setSelectedReferral(referral);
                        setShowDetailDialog(true);
                      }}
                      data-testid={`referral-${referral.id}`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <span className="font-mono text-sm text-blue-600">{referral.referral_number}</span>
                            <Badge className={STATUS_COLORS[referral.status] || 'bg-gray-100'}>
                              {referral.status?.toUpperCase()}
                            </Badge>
                            <Badge className={PRIORITY_COLORS[referral.priority] || 'bg-gray-100'}>
                              {referral.priority?.toUpperCase()}
                            </Badge>
                          </div>
                          
                          <h3 className="font-semibold text-gray-900">{referral.patient_name}</h3>
                          <p className="text-sm text-gray-500">MRN: {referral.patient_mrn || 'N/A'}</p>
                          
                          <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
                            <span className="flex items-center gap-1">
                              <Building2 className="h-4 w-4" />
                              {activeTab === 'incoming' ? referral.source_hospital_name : referral.destination_hospital_name}
                            </span>
                            <span className="flex items-center gap-1">
                              <Calendar className="h-4 w-4" />
                              {formatDate(referral.created_at)}
                            </span>
                          </div>
                          
                          <p className="text-sm text-gray-600 mt-2 line-clamp-2">{referral.reason}</p>
                        </div>
                        
                        <ChevronDown className="h-5 w-5 text-gray-400" />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>

      {/* Create Referral Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create Patient Referral</DialogTitle>
            <DialogDescription>
              Transfer a patient to another hospital with their medical records
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 py-4">
            {/* Patient Selection */}
            <div className="space-y-2">
              <Label>Select Patient *</Label>
              {selectedPatient ? (
                <Card className="bg-blue-50 border-blue-200">
                  <CardContent className="py-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-semibold">{selectedPatient.first_name} {selectedPatient.last_name}</p>
                        <p className="text-sm text-gray-600">MRN: {selectedPatient.mrn}</p>
                      </div>
                      <Button variant="ghost" size="sm" onClick={() => setSelectedPatient(null)}>
                        Change
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-2">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      placeholder="Search by name or MRN..."
                      value={patientSearchQuery}
                      onChange={(e) => {
                        setPatientSearchQuery(e.target.value);
                        searchPatients(e.target.value);
                      }}
                      className="pl-9"
                      data-testid="patient-search"
                    />
                  </div>
                  {searchingPatients && <p className="text-sm text-gray-500">Searching...</p>}
                  {patientResults.length > 0 && (
                    <div className="border rounded-md max-h-40 overflow-y-auto">
                      {patientResults.map((patient) => (
                        <div
                          key={patient.id}
                          className="p-2 hover:bg-gray-100 cursor-pointer border-b last:border-b-0"
                          onClick={() => {
                            setSelectedPatient(patient);
                            setPatientResults([]);
                            setPatientSearchQuery('');
                          }}
                        >
                          <p className="font-medium">{patient.first_name} {patient.last_name}</p>
                          <p className="text-sm text-gray-500">MRN: {patient.mrn}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Hospital Selection */}
            <div className="space-y-2">
              <Label>Destination Hospital *</Label>
              {selectedHospital ? (
                <Card className="bg-green-50 border-green-200">
                  <CardContent className="py-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-semibold">{selectedHospital.name}</p>
                        <p className="text-sm text-gray-600">{selectedHospital.address}, {selectedHospital.city}</p>
                        {selectedHospital.departments?.length > 0 && (
                          <p className="text-xs text-gray-500 mt-1">
                            Departments: {selectedHospital.departments.slice(0, 3).join(', ')}
                            {selectedHospital.departments.length > 3 && '...'}
                          </p>
                        )}
                      </div>
                      <Button variant="ghost" size="sm" onClick={() => setSelectedHospital(null)}>
                        Change
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <div className="space-y-2">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      placeholder="Search hospitals by name or city..."
                      value={hospitalSearchQuery}
                      onChange={(e) => {
                        setHospitalSearchQuery(e.target.value);
                        searchHospitals(e.target.value);
                      }}
                      className="pl-9"
                      data-testid="hospital-search"
                    />
                  </div>
                  {searchingHospitals && <p className="text-sm text-gray-500">Searching...</p>}
                  {hospitalResults.length > 0 && (
                    <div className="border rounded-md max-h-40 overflow-y-auto">
                      {hospitalResults.map((hospital) => (
                        <div
                          key={hospital.id}
                          className="p-2 hover:bg-gray-100 cursor-pointer border-b last:border-b-0"
                          onClick={() => {
                            setSelectedHospital(hospital);
                            setHospitalResults([]);
                            setHospitalSearchQuery('');
                          }}
                        >
                          <p className="font-medium">{hospital.name}</p>
                          <p className="text-sm text-gray-500">{hospital.city}, {hospital.region}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Referral Details */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Referral Type</Label>
                <Select
                  value={referralForm.referral_type}
                  onValueChange={(v) => setReferralForm({...referralForm, referral_type: v})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="standard">Standard</SelectItem>
                    <SelectItem value="emergency">Emergency</SelectItem>
                    <SelectItem value="specialist">Specialist Consultation</SelectItem>
                    <SelectItem value="second_opinion">Second Opinion</SelectItem>
                    <SelectItem value="transfer">Full Transfer</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label>Priority</Label>
                <Select
                  value={referralForm.priority}
                  onValueChange={(v) => setReferralForm({...referralForm, priority: v})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="routine">Routine</SelectItem>
                    <SelectItem value="urgent">Urgent</SelectItem>
                    <SelectItem value="emergent">Emergent</SelectItem>
                    <SelectItem value="stat">STAT</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Department (Optional)</Label>
              <Input
                placeholder="e.g., Cardiology, Oncology..."
                value={referralForm.destination_department}
                onChange={(e) => setReferralForm({...referralForm, destination_department: e.target.value})}
              />
            </div>

            <div className="space-y-2">
              <Label>Reason for Referral *</Label>
              <Textarea
                placeholder="Explain why this patient needs to be referred..."
                value={referralForm.reason}
                onChange={(e) => setReferralForm({...referralForm, reason: e.target.value})}
                rows={3}
                data-testid="referral-reason"
              />
            </div>

            <div className="space-y-2">
              <Label>Clinical Summary *</Label>
              <Textarea
                placeholder="Provide a summary of the patient's condition, history, and current treatment..."
                value={referralForm.clinical_summary}
                onChange={(e) => setReferralForm({...referralForm, clinical_summary: e.target.value})}
                rows={4}
                data-testid="clinical-summary"
              />
            </div>

            <div className="space-y-2">
              <Label>Diagnosis</Label>
              <Input
                placeholder="Primary diagnosis or ICD code..."
                value={referralForm.diagnosis}
                onChange={(e) => setReferralForm({...referralForm, diagnosis: e.target.value})}
              />
            </div>

            {/* Records to Include */}
            <div className="space-y-3">
              <Label>Include Patient Records</Label>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="include_medical_history"
                    checked={referralForm.include_medical_history}
                    onCheckedChange={(c) => setReferralForm({...referralForm, include_medical_history: c})}
                  />
                  <label htmlFor="include_medical_history" className="text-sm flex items-center gap-1">
                    <History className="h-4 w-4" /> Medical History
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="include_lab_results"
                    checked={referralForm.include_lab_results}
                    onCheckedChange={(c) => setReferralForm({...referralForm, include_lab_results: c})}
                  />
                  <label htmlFor="include_lab_results" className="text-sm flex items-center gap-1">
                    <ClipboardList className="h-4 w-4" /> Lab Results
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="include_imaging"
                    checked={referralForm.include_imaging}
                    onCheckedChange={(c) => setReferralForm({...referralForm, include_imaging: c})}
                  />
                  <label htmlFor="include_imaging" className="text-sm flex items-center gap-1">
                    <Image className="h-4 w-4" /> Imaging Studies
                  </label>
                </div>
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="include_prescriptions"
                    checked={referralForm.include_prescriptions}
                    onCheckedChange={(c) => setReferralForm({...referralForm, include_prescriptions: c})}
                  />
                  <label htmlFor="include_prescriptions" className="text-sm flex items-center gap-1">
                    <Pill className="h-4 w-4" /> Prescriptions
                  </label>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Additional Notes</Label>
              <Textarea
                placeholder="Any additional information for the receiving hospital..."
                value={referralForm.referral_notes}
                onChange={(e) => setReferralForm({...referralForm, referral_notes: e.target.value})}
                rows={2}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setShowCreateDialog(false);
              resetForm();
            }}>
              Cancel
            </Button>
            <Button 
              onClick={handleCreateReferral}
              disabled={submitting || !selectedPatient || !selectedHospital}
              className="bg-blue-600 hover:bg-blue-700"
              data-testid="submit-referral"
            >
              {submitting ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" />
                  Create & Send Referral
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Referral Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          {selectedReferral && (
            <>
              <DialogHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <DialogTitle className="flex items-center gap-2">
                      {selectedReferral.referral_number}
                      <Badge className={STATUS_COLORS[selectedReferral.status]}>
                        {selectedReferral.status?.toUpperCase()}
                      </Badge>
                    </DialogTitle>
                    <DialogDescription>
                      Created {formatDate(selectedReferral.created_at)}
                    </DialogDescription>
                  </div>
                  <Badge className={PRIORITY_COLORS[selectedReferral.priority]}>
                    {selectedReferral.priority?.toUpperCase()}
                  </Badge>
                </div>
              </DialogHeader>

              <div className="space-y-4 py-4">
                {/* Patient Info */}
                <Card>
                  <CardHeader className="py-3">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <User className="h-4 w-4" /> Patient Information
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="py-2">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-gray-500">Name:</span>
                        <p className="font-medium">{selectedReferral.patient_name}</p>
                      </div>
                      <div>
                        <span className="text-gray-500">MRN:</span>
                        <p className="font-medium">{selectedReferral.patient_mrn || 'N/A'}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Source & Destination */}
                <div className="grid grid-cols-2 gap-4">
                  <Card>
                    <CardHeader className="py-3">
                      <CardTitle className="text-sm flex items-center gap-2">
                        <Building2 className="h-4 w-4" /> From
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="py-2 text-sm">
                      <p className="font-medium">{selectedReferral.source_hospital_name}</p>
                      <p className="text-gray-500">Dr. {selectedReferral.referring_physician_name}</p>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="py-3">
                      <CardTitle className="text-sm flex items-center gap-2">
                        <Building2 className="h-4 w-4" /> To
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="py-2 text-sm">
                      <p className="font-medium">{selectedReferral.destination_hospital_name}</p>
                      {selectedReferral.destination_department && (
                        <p className="text-gray-500">{selectedReferral.destination_department}</p>
                      )}
                    </CardContent>
                  </Card>
                </div>

                {/* Clinical Details */}
                <Card>
                  <CardHeader className="py-3">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Stethoscope className="h-4 w-4" /> Clinical Details
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="py-2 space-y-3 text-sm">
                    <div>
                      <span className="text-gray-500">Reason for Referral:</span>
                      <p>{selectedReferral.reason}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Clinical Summary:</span>
                      <p>{selectedReferral.clinical_summary}</p>
                    </div>
                    {selectedReferral.diagnosis && (
                      <div>
                        <span className="text-gray-500">Diagnosis:</span>
                        <p>{selectedReferral.diagnosis}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Timeline */}
                <Card>
                  <CardHeader className="py-3">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Clock className="h-4 w-4" /> Timeline
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="py-2 text-sm space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Created:</span>
                      <span>{formatDate(selectedReferral.created_at)}</span>
                    </div>
                    {selectedReferral.sent_at && (
                      <div className="flex justify-between">
                        <span className="text-gray-500">Sent:</span>
                        <span>{formatDate(selectedReferral.sent_at)}</span>
                      </div>
                    )}
                    {selectedReferral.received_at && (
                      <div className="flex justify-between">
                        <span className="text-gray-500">Received:</span>
                        <span>{formatDate(selectedReferral.received_at)}</span>
                      </div>
                    )}
                    {selectedReferral.accepted_at && (
                      <div className="flex justify-between">
                        <span className="text-gray-500">Accepted:</span>
                        <span>{formatDate(selectedReferral.accepted_at)}</span>
                      </div>
                    )}
                    {selectedReferral.completed_at && (
                      <div className="flex justify-between">
                        <span className="text-gray-500">Completed:</span>
                        <span>{formatDate(selectedReferral.completed_at)}</span>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>

              {/* Actions based on status and role */}
              <DialogFooter className="flex-col sm:flex-row gap-2">
                {activeTab === 'incoming' && selectedReferral.status === 'sent' && (
                  <Button 
                    onClick={() => handleUpdateStatus(selectedReferral.id, 'received')}
                    className="bg-purple-600 hover:bg-purple-700"
                  >
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Mark as Received
                  </Button>
                )}
                {activeTab === 'incoming' && selectedReferral.status === 'received' && (
                  <>
                    <Button 
                      onClick={() => handleUpdateStatus(selectedReferral.id, 'accepted')}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Accept Referral
                    </Button>
                    <Button 
                      variant="destructive"
                      onClick={() => handleUpdateStatus(selectedReferral.id, 'declined')}
                    >
                      <XCircle className="h-4 w-4 mr-2" />
                      Decline
                    </Button>
                  </>
                )}
                {activeTab === 'incoming' && selectedReferral.status === 'accepted' && (
                  <Button 
                    onClick={() => handleUpdateStatus(selectedReferral.id, 'completed')}
                    className="bg-emerald-600 hover:bg-emerald-700"
                  >
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Mark as Completed
                  </Button>
                )}
                {activeTab === 'outgoing' && ['pending', 'sent'].includes(selectedReferral.status) && (
                  <Button 
                    variant="destructive"
                    onClick={() => handleUpdateStatus(selectedReferral.id, 'cancelled')}
                  >
                    <XCircle className="h-4 w-4 mr-2" />
                    Cancel Referral
                  </Button>
                )}
                <Button variant="outline" onClick={() => setShowDetailDialog(false)}>
                  Close
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
