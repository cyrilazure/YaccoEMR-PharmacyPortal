import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth';
import { recordsSharingAPI, patientAPI } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Checkbox } from '@/components/ui/checkbox';
import { toast } from 'sonner';
import {
  Search, Send, Inbox, Bell, CheckCircle, XCircle, Clock,
  FileText, User, Building2, Calendar, AlertCircle, Eye,
  UserSearch, Share2, Shield, ArrowRight
} from 'lucide-react';

export default function RecordsSharing() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('search');
  const [loading, setLoading] = useState(false);
  
  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  
  // Request state
  const [incomingRequests, setIncomingRequests] = useState([]);
  const [outgoingRequests, setOutgoingRequests] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [accessGrants, setAccessGrants] = useState([]);
  const [stats, setStats] = useState(null);
  
  // Dialog state
  const [showRequestDialog, setShowRequestDialog] = useState(false);
  const [selectedPhysician, setSelectedPhysician] = useState(null);
  const [showRespondDialog, setShowRespondDialog] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [showRecordsDialog, setShowRecordsDialog] = useState(false);
  const [sharedRecords, setSharedRecords] = useState(null);
  
  // Form state
  const [patients, setPatients] = useState([]);
  const [requestForm, setRequestForm] = useState({
    patient_id: '',
    patient_name: '',
    reason: '',
    urgency: 'routine',
    requested_records: ['all'],
    consent_signed: true
  });
  const [responseForm, setResponseForm] = useState({
    approved: true,
    notes: '',
    access_duration_days: 30
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [incomingRes, outgoingRes, notificationsRes, grantsRes, statsRes, patientsRes] = await Promise.all([
        recordsSharingAPI.getIncomingRequests(),
        recordsSharingAPI.getOutgoingRequests(),
        recordsSharingAPI.getNotifications(),
        recordsSharingAPI.getMyAccessGrants(),
        recordsSharingAPI.getStats(),
        patientAPI.getAll()
      ]);
      
      setIncomingRequests(incomingRes.data.requests || []);
      setOutgoingRequests(outgoingRes.data.requests || []);
      setNotifications(notificationsRes.data.notifications || []);
      setAccessGrants(grantsRes.data.access_grants || []);
      setStats(statsRes.data);
      setPatients(patientsRes.data || []);
    } catch (err) {
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setSearching(true);
    try {
      const res = await recordsSharingAPI.searchPhysicians({ query: searchQuery });
      setSearchResults(res.data.physicians || []);
    } catch (err) {
      toast.error('Search failed');
    } finally {
      setSearching(false);
    }
  };

  const handleSelectPhysician = (physician) => {
    setSelectedPhysician(physician);
    setShowRequestDialog(true);
  };

  const handlePatientSelect = (patientId) => {
    const patient = patients.find(p => p.id === patientId);
    setRequestForm({
      ...requestForm,
      patient_id: patientId,
      patient_name: patient ? `${patient.first_name} ${patient.last_name}` : ''
    });
  };

  const handleSubmitRequest = async () => {
    if (!requestForm.patient_id || !requestForm.reason) {
      toast.error('Please fill in all required fields');
      return;
    }
    
    try {
      await recordsSharingAPI.createRequest({
        target_physician_id: selectedPhysician.id,
        ...requestForm
      });
      
      toast.success('Records request submitted successfully');
      setShowRequestDialog(false);
      setSelectedPhysician(null);
      setRequestForm({
        patient_id: '',
        patient_name: '',
        reason: '',
        urgency: 'routine',
        requested_records: ['all'],
        consent_signed: true
      });
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to submit request');
    }
  };

  const handleOpenResponse = (request) => {
    setSelectedRequest(request);
    setResponseForm({
      approved: true,
      notes: '',
      access_duration_days: 30
    });
    setShowRespondDialog(true);
  };

  const handleSubmitResponse = async () => {
    try {
      await recordsSharingAPI.respondToRequest(selectedRequest.id, responseForm);
      
      toast.success(responseForm.approved ? 'Request approved' : 'Request declined');
      setShowRespondDialog(false);
      setSelectedRequest(null);
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to respond');
    }
  };

  const handleViewSharedRecords = async (grant) => {
    try {
      const res = await recordsSharingAPI.getSharedRecords(grant.patient_id);
      setSharedRecords(res.data);
      setShowRecordsDialog(true);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to load records');
    }
  };

  const handleMarkNotificationRead = async (notificationId) => {
    try {
      await recordsSharingAPI.markNotificationRead(notificationId);
      loadData();
    } catch (err) {
      console.error('Error marking notification read:', err);
    }
  };

  const getStatusBadge = (status) => {
    const config = {
      pending: { color: 'bg-amber-100 text-amber-700', icon: Clock },
      approved: { color: 'bg-green-100 text-green-700', icon: CheckCircle },
      rejected: { color: 'bg-red-100 text-red-700', icon: XCircle },
      cancelled: { color: 'bg-slate-100 text-slate-500', icon: XCircle },
      expired: { color: 'bg-slate-100 text-slate-500', icon: Clock },
    };
    const c = config[status] || config.pending;
    const Icon = c.icon;
    
    return (
      <Badge className={`${c.color} gap-1`}>
        <Icon className="w-3 h-3" />
        {status.toUpperCase()}
      </Badge>
    );
  };

  const unreadNotifications = notifications.filter(n => !n.read);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Manrope' }}>
            Records Sharing
          </h1>
          <p className="text-slate-500">Request and share patient medical records with other physicians</p>
        </div>
        {unreadNotifications.length > 0 && (
          <Badge className="bg-red-500 text-white">
            {unreadNotifications.length} New Notifications
          </Badge>
        )}
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Pending Incoming</p>
                  <p className="text-2xl font-bold text-amber-600">{stats.incoming_requests?.pending || 0}</p>
                </div>
                <Inbox className="w-8 h-8 text-amber-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Pending Outgoing</p>
                  <p className="text-2xl font-bold text-sky-600">{stats.outgoing_requests?.pending || 0}</p>
                </div>
                <Send className="w-8 h-8 text-sky-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Active Access</p>
                  <p className="text-2xl font-bold text-green-600">{stats.active_access_grants || 0}</p>
                </div>
                <Shield className="w-8 h-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Unread Alerts</p>
                  <p className="text-2xl font-bold text-red-600">{stats.unread_notifications || 0}</p>
                </div>
                <Bell className="w-8 h-8 text-red-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-5 w-full max-w-2xl">
          <TabsTrigger value="search" className="gap-2">
            <UserSearch className="w-4 h-4" />
            Find Physicians
          </TabsTrigger>
          <TabsTrigger value="incoming" className="gap-2">
            <Inbox className="w-4 h-4" />
            Incoming ({incomingRequests.filter(r => r.status === 'pending').length})
          </TabsTrigger>
          <TabsTrigger value="outgoing" className="gap-2">
            <Send className="w-4 h-4" />
            Outgoing
          </TabsTrigger>
          <TabsTrigger value="access" className="gap-2">
            <Shield className="w-4 h-4" />
            My Access
          </TabsTrigger>
          <TabsTrigger value="notifications" className="gap-2">
            <Bell className="w-4 h-4" />
            Alerts ({unreadNotifications.length})
          </TabsTrigger>
        </TabsList>

        {/* Search Tab */}
        <TabsContent value="search" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Search Physicians</CardTitle>
              <CardDescription>Find physicians at other hospitals to request patient records</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  placeholder="Search by name, specialty, or email..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                />
                <Button onClick={handleSearch} disabled={searching}>
                  <Search className="w-4 h-4 mr-2" />
                  {searching ? 'Searching...' : 'Search'}
                </Button>
              </div>

              {searchResults.length > 0 && (
                <div className="border rounded-lg divide-y">
                  {searchResults.map((physician) => (
                    <div key={physician.id} className="p-4 flex items-center justify-between hover:bg-slate-50">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-full bg-sky-100 flex items-center justify-center">
                          <User className="w-6 h-6 text-sky-600" />
                        </div>
                        <div>
                          <p className="font-medium">Dr. {physician.first_name} {physician.last_name}</p>
                          <p className="text-sm text-slate-500">{physician.specialty || 'General Practice'}</p>
                          <div className="flex items-center gap-1 text-sm text-slate-400">
                            <Building2 className="w-3 h-3" />
                            {physician.organization_name || 'Independent'}
                          </div>
                        </div>
                      </div>
                      <Button onClick={() => handleSelectPhysician(physician)} className="gap-2">
                        <Share2 className="w-4 h-4" />
                        Request Records
                      </Button>
                    </div>
                  ))}
                </div>
              )}

              {searchResults.length === 0 && searchQuery && !searching && (
                <p className="text-center text-slate-500 py-8">No physicians found matching your search.</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Incoming Requests Tab */}
        <TabsContent value="incoming" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Incoming Records Requests</CardTitle>
              <CardDescription>Requests from other physicians for your patient's records</CardDescription>
            </CardHeader>
            <CardContent>
              {incomingRequests.length > 0 ? (
                <div className="space-y-3">
                  {incomingRequests.map((request) => (
                    <div key={request.id} className="border rounded-lg p-4 hover:bg-slate-50">
                      <div className="flex items-start justify-between">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <p className="font-medium">Dr. {request.requesting_physician_name}</p>
                            {getStatusBadge(request.status)}
                            {request.urgency === 'urgent' && (
                              <Badge className="bg-orange-100 text-orange-700">URGENT</Badge>
                            )}
                            {request.urgency === 'emergency' && (
                              <Badge className="bg-red-100 text-red-700">EMERGENCY</Badge>
                            )}
                          </div>
                          <p className="text-sm text-slate-500">
                            From: {request.requesting_organization}
                          </p>
                          <p className="text-sm">
                            <strong>Patient:</strong> {request.patient_name}
                          </p>
                          <p className="text-sm text-slate-600">
                            <strong>Reason:</strong> {request.reason}
                          </p>
                          <p className="text-xs text-slate-400">
                            {new Date(request.created_at).toLocaleString()}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          {request.status === 'pending' && (
                            <Button onClick={() => handleOpenResponse(request)} size="sm">
                              Respond
                            </Button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-slate-500 py-8">No incoming requests.</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Outgoing Requests Tab */}
        <TabsContent value="outgoing" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Outgoing Records Requests</CardTitle>
              <CardDescription>Your requests for patient records from other physicians</CardDescription>
            </CardHeader>
            <CardContent>
              {outgoingRequests.length > 0 ? (
                <div className="space-y-3">
                  {outgoingRequests.map((request) => (
                    <div key={request.id} className="border rounded-lg p-4 hover:bg-slate-50">
                      <div className="flex items-start justify-between">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <p className="font-medium">To: Dr. {request.target_physician_name}</p>
                            {getStatusBadge(request.status)}
                          </div>
                          <p className="text-sm text-slate-500">
                            At: {request.target_organization}
                          </p>
                          <p className="text-sm">
                            <strong>Patient:</strong> {request.patient_name}
                          </p>
                          <p className="text-sm text-slate-600">
                            <strong>Reason:</strong> {request.reason}
                          </p>
                          {request.status === 'approved' && (
                            <p className="text-sm text-green-600">
                              Access expires: {new Date(request.access_expires_at).toLocaleDateString()}
                            </p>
                          )}
                          {request.response_notes && (
                            <p className="text-sm text-slate-500 italic">
                              Response: {request.response_notes}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-slate-500 py-8">No outgoing requests.</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Access Grants Tab */}
        <TabsContent value="access" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>My Access Grants</CardTitle>
              <CardDescription>Patient records you have been granted access to view</CardDescription>
            </CardHeader>
            <CardContent>
              {accessGrants.length > 0 ? (
                <div className="space-y-3">
                  {accessGrants.map((grant) => (
                    <div key={grant.id} className="border rounded-lg p-4 hover:bg-slate-50">
                      <div className="flex items-start justify-between">
                        <div className="space-y-1">
                          <p className="font-medium">{grant.patient_name}</p>
                          <p className="text-sm text-slate-500">MRN: {grant.patient_mrn}</p>
                          <p className="text-sm text-slate-500">
                            From: Dr. {grant.granting_physician_name} at {grant.granting_organization_name}
                          </p>
                          <p className="text-sm text-green-600">
                            Access until: {new Date(grant.expires_at).toLocaleDateString()}
                          </p>
                        </div>
                        <Button onClick={() => handleViewSharedRecords(grant)} className="gap-2">
                          <Eye className="w-4 h-4" />
                          View Records
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-slate-500 py-8">No active access grants.</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Notifications</CardTitle>
                <CardDescription>Alerts about records requests and access grants</CardDescription>
              </div>
              {unreadNotifications.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => recordsSharingAPI.markAllNotificationsRead().then(loadData)}
                >
                  Mark All Read
                </Button>
              )}
            </CardHeader>
            <CardContent>
              {notifications.length > 0 ? (
                <div className="space-y-2">
                  {notifications.map((notification) => (
                    <div
                      key={notification.id}
                      className={`border rounded-lg p-4 ${!notification.read ? 'bg-sky-50 border-sky-200' : ''}`}
                      onClick={() => !notification.read && handleMarkNotificationRead(notification.id)}
                    >
                      <div className="flex items-start gap-3">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                          notification.type === 'request_approved' ? 'bg-green-100' :
                          notification.type === 'request_rejected' ? 'bg-red-100' :
                          'bg-sky-100'
                        }`}>
                          {notification.type === 'request_approved' ? (
                            <CheckCircle className="w-5 h-5 text-green-600" />
                          ) : notification.type === 'request_rejected' ? (
                            <XCircle className="w-5 h-5 text-red-600" />
                          ) : (
                            <Bell className="w-5 h-5 text-sky-600" />
                          )}
                        </div>
                        <div className="flex-1">
                          <p className="font-medium">{notification.title}</p>
                          <p className="text-sm text-slate-600">{notification.message}</p>
                          <p className="text-xs text-slate-400 mt-1">
                            {new Date(notification.created_at).toLocaleString()}
                          </p>
                        </div>
                        {!notification.read && (
                          <div className="w-2 h-2 rounded-full bg-sky-500"></div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-slate-500 py-8">No notifications.</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Request Records Dialog */}
      <Dialog open={showRequestDialog} onOpenChange={setShowRequestDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Request Medical Records</DialogTitle>
            <DialogDescription>
              Request patient records from Dr. {selectedPhysician?.first_name} {selectedPhysician?.last_name} at {selectedPhysician?.organization_name}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Select Patient *</Label>
              <Select value={requestForm.patient_id} onValueChange={handlePatientSelect}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a patient" />
                </SelectTrigger>
                <SelectContent>
                  {patients.map((patient) => (
                    <SelectItem key={patient.id} value={patient.id}>
                      {patient.first_name} {patient.last_name} ({patient.mrn})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Reason for Request *</Label>
              <Textarea
                placeholder="Clinical reason for requesting these records..."
                value={requestForm.reason}
                onChange={(e) => setRequestForm({ ...requestForm, reason: e.target.value })}
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <Label>Urgency</Label>
              <Select value={requestForm.urgency} onValueChange={(v) => setRequestForm({ ...requestForm, urgency: v })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="routine">Routine</SelectItem>
                  <SelectItem value="urgent">Urgent</SelectItem>
                  <SelectItem value="emergency">Emergency</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-2 p-3 bg-green-50 rounded-lg">
              <Checkbox
                checked={requestForm.consent_signed}
                onCheckedChange={(checked) => setRequestForm({ ...requestForm, consent_signed: checked })}
              />
              <Label className="text-sm text-green-800">
                Patient has signed consent form for records release
              </Label>
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button variant="outline" onClick={() => setShowRequestDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleSubmitRequest} className="bg-sky-600 hover:bg-sky-700">
                Submit Request
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Respond Dialog */}
      <Dialog open={showRespondDialog} onOpenChange={setShowRespondDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Respond to Records Request</DialogTitle>
            <DialogDescription>
              Request from Dr. {selectedRequest?.requesting_physician_name} for {selectedRequest?.patient_name}'s records
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="p-4 bg-slate-50 rounded-lg space-y-2">
              <p><strong>Reason:</strong> {selectedRequest?.reason}</p>
              <p><strong>Requested Records:</strong> {selectedRequest?.requested_records?.join(', ')}</p>
            </div>

            <div className="space-y-2">
              <Label>Your Decision</Label>
              <Select value={responseForm.approved.toString()} onValueChange={(v) => setResponseForm({ ...responseForm, approved: v === 'true' })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="true">Approve - Grant Access</SelectItem>
                  <SelectItem value="false">Decline - Deny Access</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {responseForm.approved && (
              <div className="space-y-2">
                <Label>Access Duration</Label>
                <Select value={responseForm.access_duration_days.toString()} onValueChange={(v) => setResponseForm({ ...responseForm, access_duration_days: parseInt(v) })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="7">7 days</SelectItem>
                    <SelectItem value="14">14 days</SelectItem>
                    <SelectItem value="30">30 days</SelectItem>
                    <SelectItem value="60">60 days</SelectItem>
                    <SelectItem value="90">90 days</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}

            <div className="space-y-2">
              <Label>Notes (Optional)</Label>
              <Textarea
                placeholder="Additional notes..."
                value={responseForm.notes}
                onChange={(e) => setResponseForm({ ...responseForm, notes: e.target.value })}
                rows={2}
              />
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button variant="outline" onClick={() => setShowRespondDialog(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleSubmitResponse}
                className={responseForm.approved ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}
              >
                {responseForm.approved ? 'Approve Request' : 'Decline Request'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* View Shared Records Dialog */}
      <Dialog open={showRecordsDialog} onOpenChange={setShowRecordsDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh]">
          <DialogHeader>
            <DialogTitle>
              Shared Patient Records - {sharedRecords?.patient?.first_name} {sharedRecords?.patient?.last_name}
            </DialogTitle>
            <DialogDescription>
              Access expires: {sharedRecords?.access_info?.expires_at ? new Date(sharedRecords.access_info.expires_at).toLocaleDateString() : 'N/A'}
            </DialogDescription>
          </DialogHeader>
          
          <ScrollArea className="h-[60vh]">
            {sharedRecords && (
              <div className="space-y-6 p-4">
                {/* Patient Info */}
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg">Patient Information</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div><strong>Name:</strong> {sharedRecords.patient?.first_name} {sharedRecords.patient?.last_name}</div>
                      <div><strong>MRN:</strong> {sharedRecords.patient?.mrn}</div>
                      <div><strong>DOB:</strong> {sharedRecords.patient?.date_of_birth}</div>
                      <div><strong>Gender:</strong> {sharedRecords.patient?.gender}</div>
                    </div>
                  </CardContent>
                </Card>

                {/* Problems */}
                {sharedRecords.problems?.length > 0 && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-lg">Active Problems</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="list-disc list-inside space-y-1">
                        {sharedRecords.problems.filter(p => p.status === 'active').map((problem, i) => (
                          <li key={i}>{problem.name} ({problem.icd10_code})</li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                )}

                {/* Medications */}
                {sharedRecords.medications?.length > 0 && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-lg">Current Medications</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-1">
                        {sharedRecords.medications.filter(m => m.status === 'active').map((med, i) => (
                          <li key={i}>{med.name} {med.dosage} - {med.frequency}</li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                )}

                {/* Allergies */}
                {sharedRecords.allergies?.length > 0 && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-lg">Allergies</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="list-disc list-inside space-y-1">
                        {sharedRecords.allergies.map((allergy, i) => (
                          <li key={i} className="text-red-600">{allergy.allergen} - {allergy.reaction}</li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                )}

                {/* Vitals */}
                {sharedRecords.vitals?.length > 0 && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-lg">Recent Vitals</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-sm">
                        <p><strong>BP:</strong> {sharedRecords.vitals[0]?.blood_pressure_systolic}/{sharedRecords.vitals[0]?.blood_pressure_diastolic} mmHg</p>
                        <p><strong>HR:</strong> {sharedRecords.vitals[0]?.heart_rate} bpm</p>
                        <p><strong>Temp:</strong> {sharedRecords.vitals[0]?.temperature}°F</p>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Notes */}
                {sharedRecords.notes?.length > 0 && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-lg">Clinical Notes</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {sharedRecords.notes.slice(0, 3).map((note, i) => (
                        <div key={i} className="border-b pb-3">
                          <p className="text-sm text-slate-500">{new Date(note.created_at).toLocaleDateString()} - {note.note_type}</p>
                          {note.assessment && <p className="mt-1"><strong>Assessment:</strong> {note.assessment}</p>}
                          {note.plan && <p><strong>Plan:</strong> {note.plan}</p>}
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                )}
              </div>
            )}
          </ScrollArea>
        </DialogContent>
      </Dialog>
    </div>
  );
}
