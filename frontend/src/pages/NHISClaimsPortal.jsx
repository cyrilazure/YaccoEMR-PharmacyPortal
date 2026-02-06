import React, { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth';
import { getErrorMessage, formatCurrency } from '@/lib/utils';
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
import { 
  RefreshCw, Clock, CheckCircle, XCircle, AlertCircle, 
  FileText, Users, Activity, TrendingUp, Loader2, Search,
  Plus, Send, DollarSign, CreditCard, Building, Verified, User
} from 'lucide-react';
import api from '@/lib/api';

const nhisAPI = {
  verifyMember: (data) => api.post('/nhis/verify-member', data),
  getMemberDetails: (id) => api.get(`/nhis/member/${id}`),
  getDrugTariff: (params) => api.get('/nhis/tariff', { params }),
  createClaim: (data) => api.post('/nhis/claims/pharmacy', data),
  getClaims: (params) => api.get('/nhis/claims', { params }),
  getClaimDetails: (id) => api.get(`/nhis/claims/${id}`),
  submitClaim: (id) => api.post(`/nhis/claims/${id}/submit`),
  updateClaimStatus: (id, data) => api.put(`/nhis/claims/${id}/status`, data),
  getDashboard: () => api.get('/nhis/dashboard'),
  getClaimsSummary: (params) => api.get('/nhis/reports/claims-summary', { params }),
};

export default function NHISClaimsPortal() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);
  const [claims, setClaims] = useState([]);
  const [drugTariff, setDrugTariff] = useState([]);
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Member Verification
  const [membershipId, setMembershipId] = useState('');
  const [verifiedMember, setVerifiedMember] = useState(null);
  const [verifying, setVerifying] = useState(false);
  
  // Create Claim Dialog
  const [createClaimOpen, setCreateClaimOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [claimForm, setClaimForm] = useState({
    patient_id: '',
    patient_name: '',
    membership_id: '',
    diagnosis_codes: '',
    prescription_date: new Date().toISOString().split('T')[0],
    dispensing_date: new Date().toISOString().split('T')[0],
    prescriber_name: '',
    notes: ''
  });
  const [claimItems, setClaimItems] = useState([]);
  
  // Drug Search
  const [drugSearch, setDrugSearch] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [dashboardRes, claimsRes, tariffRes] = await Promise.all([
        nhisAPI.getDashboard(),
        nhisAPI.getClaims({}),
        nhisAPI.getDrugTariff({ covered_only: true })
      ]);
      
      setDashboard(dashboardRes.data);
      setClaims(claimsRes.data.claims || []);
      setDrugTariff(tariffRes.data.drugs || []);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to load NHIS data'));
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyMember = async () => {
    if (!membershipId.trim()) {
      toast.error('Please enter NHIS membership ID');
      return;
    }
    
    setVerifying(true);
    try {
      const res = await nhisAPI.verifyMember({ membership_id: membershipId });
      setVerifiedMember(res.data);
      
      if (res.data.verified) {
        toast.success('Member verified successfully');
        setClaimForm(prev => ({
          ...prev,
          membership_id: res.data.membership_id,
          patient_name: res.data.full_name
        }));
      } else {
        toast.warning(res.data.message);
      }
    } catch (err) {
      toast.error(getErrorMessage(err, 'Verification failed'));
    } finally {
      setVerifying(false);
    }
  };

  const handleAddDrug = (drug) => {
    const existing = claimItems.find(i => i.item_code === drug.code);
    if (existing) {
      toast.warning('Drug already added to claim');
      return;
    }
    
    setClaimItems(prev => [...prev, {
      item_code: drug.code,
      item_name: drug.name,
      quantity: 1,
      unit_price: drug.nhis_price || 0,
      total_price: drug.nhis_price || 0,
      nhis_price: drug.nhis_price,
      is_covered: drug.covered
    }]);
  };

  const updateItemQuantity = (code, quantity) => {
    setClaimItems(prev => prev.map(item => {
      if (item.item_code === code) {
        return {
          ...item,
          quantity: parseInt(quantity) || 1,
          total_price: (parseInt(quantity) || 1) * item.unit_price
        };
      }
      return item;
    }));
  };

  const removeItem = (code) => {
    setClaimItems(prev => prev.filter(i => i.item_code !== code));
  };

  const handleCreateClaim = async (e) => {
    e.preventDefault();
    if (!claimForm.membership_id || claimItems.length === 0) {
      toast.error('Please verify member and add items');
      return;
    }
    
    setSaving(true);
    try {
      const payload = {
        ...claimForm,
        diagnosis_codes: claimForm.diagnosis_codes.split(',').map(c => c.trim()).filter(Boolean),
        claim_items: claimItems
      };
      
      await nhisAPI.createClaim(payload);
      toast.success('Claim created successfully');
      setCreateClaimOpen(false);
      resetClaimForm();
      fetchData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to create claim'));
    } finally {
      setSaving(false);
    }
  };

  const resetClaimForm = () => {
    setClaimForm({
      patient_id: '',
      patient_name: '',
      membership_id: '',
      diagnosis_codes: '',
      prescription_date: new Date().toISOString().split('T')[0],
      dispensing_date: new Date().toISOString().split('T')[0],
      prescriber_name: user ? `${user.first_name} ${user.last_name}` : '',
      notes: ''
    });
    setClaimItems([]);
    setVerifiedMember(null);
    setMembershipId('');
  };

  const handleSubmitClaim = async (claimId) => {
    try {
      await nhisAPI.submitClaim(claimId);
      toast.success('Claim submitted to NHIS');
      fetchData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to submit claim'));
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      draft: { color: 'bg-gray-100 text-gray-700', icon: FileText },
      submitted: { color: 'bg-blue-100 text-blue-700', icon: Send },
      under_review: { color: 'bg-yellow-100 text-yellow-700', icon: Clock },
      approved: { color: 'bg-green-100 text-green-700', icon: CheckCircle },
      rejected: { color: 'bg-red-100 text-red-700', icon: XCircle },
      partially_approved: { color: 'bg-orange-100 text-orange-700', icon: AlertCircle },
      paid: { color: 'bg-emerald-100 text-emerald-700', icon: DollarSign }
    };
    const config = statusConfig[status] || { color: 'bg-gray-100 text-gray-700', icon: FileText };
    const Icon = config.icon;
    
    return (
      <Badge className={`${config.color} gap-1`}>
        <Icon className="w-3 h-3" />
        {status?.replace('_', ' ')}
      </Badge>
    );
  };

  const filteredTariff = drugTariff.filter(d => 
    !drugSearch || 
    d.name.toLowerCase().includes(drugSearch.toLowerCase()) ||
    d.code.toLowerCase().includes(drugSearch.toLowerCase())
  );

  const claimTotal = claimItems.reduce((sum, item) => sum + item.total_price, 0);

  return (
    <div className="space-y-6 animate-fade-in" data-testid="nhis-claims-portal">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <CreditCard className="w-7 h-7 text-green-600" />
            NHIS Claims Portal
          </h1>
          <p className="text-slate-500 mt-1">National Health Insurance Scheme - Pharmacy Claims</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setCreateClaimOpen(true)} className="gap-2 bg-green-600 hover:bg-green-700" data-testid="new-claim-btn">
            <Plus className="w-4 h-4" />
            New Claim
          </Button>
          <Button onClick={fetchData} variant="outline" className="gap-2" data-testid="refresh-btn">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Dashboard Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="text-center">
              <FileText className="w-8 h-8 mx-auto mb-2 text-slate-400" />
              <p className="text-sm text-slate-600">Total Claims</p>
              <p className="text-2xl font-bold">{dashboard?.summary?.total_claims || 0}</p>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <Send className="w-8 h-8 mx-auto mb-2 text-blue-600" />
              <p className="text-sm text-blue-700">Submitted</p>
              <p className="text-2xl font-bold text-blue-800">{dashboard?.summary?.by_status?.submitted || 0}</p>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-green-50 border-green-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-600" />
              <p className="text-sm text-green-700">Approved</p>
              <p className="text-2xl font-bold text-green-800">{dashboard?.summary?.by_status?.approved || 0}</p>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-emerald-50 border-emerald-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <DollarSign className="w-8 h-8 mx-auto mb-2 text-emerald-600" />
              <p className="text-sm text-emerald-700">Total Claimed</p>
              <p className="text-xl font-bold text-emerald-800">₵{dashboard?.financials?.total_claimed?.toFixed(2) || '0.00'}</p>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-purple-50 border-purple-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <TrendingUp className="w-8 h-8 mx-auto mb-2 text-purple-600" />
              <p className="text-sm text-purple-700">Paid</p>
              <p className="text-xl font-bold text-purple-800">₵{dashboard?.financials?.total_paid?.toFixed(2) || '0.00'}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="dashboard" data-testid="tab-dashboard">Dashboard</TabsTrigger>
          <TabsTrigger value="claims" data-testid="tab-claims">Claims</TabsTrigger>
          <TabsTrigger value="verify" data-testid="tab-verify">Verify Member</TabsTrigger>
          <TabsTrigger value="tariff" data-testid="tab-tariff">Drug Tariff</TabsTrigger>
        </TabsList>

        {/* Dashboard Tab */}
        <TabsContent value="dashboard" className="mt-4 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Claims by Status</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 flex items-center gap-2">
                      <FileText className="w-4 h-4 text-gray-400" /> Draft
                    </span>
                    <span className="font-bold">{dashboard?.summary?.by_status?.draft || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 flex items-center gap-2">
                      <Send className="w-4 h-4 text-blue-500" /> Submitted
                    </span>
                    <span className="font-bold">{dashboard?.summary?.by_status?.submitted || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500" /> Approved
                    </span>
                    <span className="font-bold">{dashboard?.summary?.by_status?.approved || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 flex items-center gap-2">
                      <XCircle className="w-4 h-4 text-red-500" /> Rejected
                    </span>
                    <span className="font-bold">{dashboard?.summary?.by_status?.rejected || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 flex items-center gap-2">
                      <DollarSign className="w-4 h-4 text-emerald-500" /> Paid
                    </span>
                    <span className="font-bold">{dashboard?.summary?.by_status?.paid || 0}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Financial Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Total Claimed:</span>
                    <span className="font-bold text-blue-600">₵{dashboard?.financials?.total_claimed?.toFixed(2) || '0.00'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Total Approved:</span>
                    <span className="font-bold text-green-600">₵{dashboard?.financials?.total_approved?.toFixed(2) || '0.00'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Total Paid:</span>
                    <span className="font-bold text-emerald-600">₵{dashboard?.financials?.total_paid?.toFixed(2) || '0.00'}</span>
                  </div>
                  <div className="flex justify-between border-t pt-2">
                    <span className="text-sm text-gray-600">Pending Payment:</span>
                    <span className="font-bold text-amber-600">₵{dashboard?.financials?.pending_payment?.toFixed(2) || '0.00'}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle className="text-base">This Month</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex gap-8">
                  <div>
                    <p className="text-sm text-gray-600">Claims Submitted</p>
                    <p className="text-2xl font-bold">{dashboard?.current_month?.claims_submitted || 0}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Amount Claimed</p>
                    <p className="text-2xl font-bold text-blue-600">₵{dashboard?.current_month?.amount_claimed?.toFixed(2) || '0.00'}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Claims Tab */}
        <TabsContent value="claims" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Pharmacy Claims</CardTitle>
                <CardDescription>NHIS pharmacy claim submissions</CardDescription>
              </div>
              <Button onClick={() => setCreateClaimOpen(true)} className="gap-2 bg-green-600 hover:bg-green-700">
                <Plus className="w-4 h-4" /> New Claim
              </Button>
            </CardHeader>
            <CardContent>
              {claims.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <FileText className="w-12 h-12 mx-auto mb-4 opacity-30" />
                  <p>No claims found</p>
                  <Button onClick={() => setCreateClaimOpen(true)} className="mt-4" variant="outline">
                    Create First Claim
                  </Button>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Claim #</TableHead>
                      <TableHead>Patient</TableHead>
                      <TableHead>NHIS ID</TableHead>
                      <TableHead>Items</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {claims.map((claim) => (
                      <TableRow key={claim.id} data-testid={`claim-row-${claim.id}`}>
                        <TableCell className="font-mono text-sm">{claim.claim_number}</TableCell>
                        <TableCell>
                          <div>
                            <p className="font-medium">{claim.patient_name}</p>
                            <p className="text-xs text-gray-500">{claim.member_name}</p>
                          </div>
                        </TableCell>
                        <TableCell className="font-mono text-xs">{claim.membership_id}</TableCell>
                        <TableCell>{claim.claim_items?.length || 0} items</TableCell>
                        <TableCell className="font-semibold">₵{claim.total_claimed?.toFixed(2)}</TableCell>
                        <TableCell>{getStatusBadge(claim.status)}</TableCell>
                        <TableCell className="text-sm text-gray-500">
                          {new Date(claim.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell className="text-right">
                          {claim.status === 'draft' && (
                            <Button 
                              size="sm" 
                              onClick={() => handleSubmitClaim(claim.id)}
                              className="bg-blue-600 hover:bg-blue-700"
                              data-testid={`submit-claim-${claim.id}`}
                            >
                              <Send className="w-3 h-3 mr-1" /> Submit
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

        {/* Verify Member Tab */}
        <TabsContent value="verify" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Verified className="w-5 h-5 text-green-600" />
                Verify NHIS Member
              </CardTitle>
              <CardDescription>Check patient&apos;s NHIS membership status and coverage</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex gap-4 items-end">
                <div className="flex-1 space-y-2">
                  <Label>NHIS Membership ID</Label>
                  <Input 
                    value={membershipId}
                    onChange={(e) => setMembershipId(e.target.value)}
                    placeholder="e.g., NHIS-2024-001234"
                    data-testid="membership-id-input"
                  />
                </div>
                <Button 
                  onClick={handleVerifyMember} 
                  disabled={verifying}
                  className="gap-2"
                  data-testid="verify-member-btn"
                >
                  {verifying && <Loader2 className="w-4 h-4 animate-spin" />}
                  <Search className="w-4 h-4" />
                  Verify
                </Button>
              </div>

              {verifiedMember && (
                <Card className={verifiedMember.verified ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
                  <CardContent className="pt-6">
                    <div className="flex items-start gap-4">
                      <div className={`p-3 rounded-full ${verifiedMember.verified ? 'bg-green-100' : 'bg-red-100'}`}>
                        {verifiedMember.verified ? 
                          <CheckCircle className="w-6 h-6 text-green-600" /> : 
                          <XCircle className="w-6 h-6 text-red-600" />
                        }
                      </div>
                      <div className="flex-1 grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm text-gray-500">Full Name</p>
                          <p className="font-semibold">{verifiedMember.full_name || 'N/A'}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-500">Membership ID</p>
                          <p className="font-mono">{verifiedMember.membership_id}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-500">Status</p>
                          <Badge className={verifiedMember.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}>
                            {verifiedMember.status?.toUpperCase()}
                          </Badge>
                        </div>
                        <div>
                          <p className="text-sm text-gray-500">Expiry Date</p>
                          <p className="font-medium">{verifiedMember.expiry_date || 'N/A'}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-500">Coverage Type</p>
                          <p className="font-medium">{verifiedMember.coverage_type || 'N/A'}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-500">Region</p>
                          <p className="font-medium">{verifiedMember.region || 'N/A'}</p>
                        </div>
                      </div>
                    </div>
                    <p className={`mt-4 text-sm ${verifiedMember.verified ? 'text-green-700' : 'text-red-700'}`}>
                      {verifiedMember.message}
                    </p>
                  </CardContent>
                </Card>
              )}

              <div className="text-sm text-gray-500 bg-gray-50 p-4 rounded-lg">
                <p className="font-medium mb-2">Sample NHIS IDs for Testing:</p>
                <ul className="space-y-1">
                  <li><code className="bg-gray-200 px-1 rounded">NHIS-2024-001234</code> - Active (Kofi Mensah Asante)</li>
                  <li><code className="bg-gray-200 px-1 rounded">NHIS-2023-005678</code> - Active (Ama Serwaa Boateng)</li>
                  <li><code className="bg-gray-200 px-1 rounded">NHIS-2022-009012</code> - Expired (Kwame Owusu Darko)</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Drug Tariff Tab */}
        <TabsContent value="tariff" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>NHIS Drug Tariff</CardTitle>
              <CardDescription>Approved drug prices under National Health Insurance Scheme</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-4">
                <Input
                  placeholder="Search drugs by name or code..."
                  value={drugSearch}
                  onChange={(e) => setDrugSearch(e.target.value)}
                  className="max-w-md"
                  data-testid="tariff-search"
                />
              </div>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Code</TableHead>
                    <TableHead>Drug Name</TableHead>
                    <TableHead>NHIS Price</TableHead>
                    <TableHead>Covered</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredTariff.slice(0, 50).map((drug) => (
                    <TableRow key={drug.code}>
                      <TableCell className="font-mono text-sm">{drug.code}</TableCell>
                      <TableCell>{drug.name}</TableCell>
                      <TableCell className="font-semibold">
                        {drug.nhis_price ? `₵${drug.nhis_price.toFixed(2)}` : '-'}
                      </TableCell>
                      <TableCell>
                        {drug.covered ? 
                          <Badge className="bg-green-100 text-green-700">Covered</Badge> : 
                          <Badge className="bg-red-100 text-red-700">Not Covered</Badge>
                        }
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              <p className="text-sm text-gray-500 mt-4">
                Showing {Math.min(filteredTariff.length, 50)} of {filteredTariff.length} drugs
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Create Claim Dialog */}
      <Dialog open={createClaimOpen} onOpenChange={setCreateClaimOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>Create NHIS Pharmacy Claim</DialogTitle>
            <DialogDescription>Submit claim for medication dispensing</DialogDescription>
          </DialogHeader>
          <div className="overflow-y-auto flex-1 pr-2">
            <form onSubmit={handleCreateClaim} className="space-y-6">
              {/* Member Verification */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <User className="w-4 h-4" />
                    Member Verification
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex gap-4 items-end">
                    <div className="flex-1 space-y-2">
                      <Label>NHIS Membership ID *</Label>
                      <Input 
                        value={membershipId}
                        onChange={(e) => setMembershipId(e.target.value)}
                        placeholder="e.g., NHIS-2024-001234"
                      />
                    </div>
                    <Button type="button" onClick={handleVerifyMember} disabled={verifying}>
                      {verifying && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                      Verify
                    </Button>
                  </div>
                  
                  {verifiedMember && verifiedMember.verified && (
                    <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                      <p className="text-sm text-green-700">
                        <CheckCircle className="w-4 h-4 inline mr-1" />
                        Verified: {verifiedMember.full_name} - {verifiedMember.coverage_type}
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Claim Details */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">Claim Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Patient Name</Label>
                      <Input 
                        value={claimForm.patient_name}
                        onChange={(e) => setClaimForm({...claimForm, patient_name: e.target.value})}
                        placeholder="Auto-filled from verification"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Diagnosis Codes (ICD-10)</Label>
                      <Input 
                        value={claimForm.diagnosis_codes}
                        onChange={(e) => setClaimForm({...claimForm, diagnosis_codes: e.target.value})}
                        placeholder="e.g., B50.9, J06.9"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Prescription Date</Label>
                      <Input 
                        type="date"
                        value={claimForm.prescription_date}
                        onChange={(e) => setClaimForm({...claimForm, prescription_date: e.target.value})}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Dispensing Date</Label>
                      <Input 
                        type="date"
                        value={claimForm.dispensing_date}
                        onChange={(e) => setClaimForm({...claimForm, dispensing_date: e.target.value})}
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Prescriber Name</Label>
                    <Input 
                      value={claimForm.prescriber_name}
                      onChange={(e) => setClaimForm({...claimForm, prescriber_name: e.target.value})}
                      placeholder="Dr. ..."
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Drug Selection */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">Medications</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>Search NHIS Drug Tariff</Label>
                    <Input 
                      value={drugSearch}
                      onChange={(e) => setDrugSearch(e.target.value)}
                      placeholder="Search by drug name or code..."
                    />
                  </div>
                  
                  {drugSearch && (
                    <div className="max-h-48 overflow-y-auto border rounded-lg">
                      {filteredTariff.slice(0, 10).map(drug => (
                        <div 
                          key={drug.code}
                          className="p-2 hover:bg-gray-50 cursor-pointer flex justify-between items-center border-b last:border-b-0"
                          onClick={() => handleAddDrug(drug)}
                        >
                          <div>
                            <p className="font-medium text-sm">{drug.name}</p>
                            <p className="text-xs text-gray-500">{drug.code}</p>
                          </div>
                          <div className="text-right">
                            <p className="font-semibold text-green-600">₵{drug.nhis_price?.toFixed(2)}</p>
                            <Button type="button" size="sm" variant="ghost" className="text-xs">
                              <Plus className="w-3 h-3 mr-1" /> Add
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Selected Items */}
                  {claimItems.length > 0 && (
                    <div className="border rounded-lg">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Drug</TableHead>
                            <TableHead>Qty</TableHead>
                            <TableHead>Unit Price</TableHead>
                            <TableHead>Total</TableHead>
                            <TableHead></TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {claimItems.map(item => (
                            <TableRow key={item.item_code}>
                              <TableCell>
                                <p className="font-medium text-sm">{item.item_name}</p>
                                <p className="text-xs text-gray-500">{item.item_code}</p>
                              </TableCell>
                              <TableCell>
                                <Input 
                                  type="number"
                                  min="1"
                                  value={item.quantity}
                                  onChange={(e) => updateItemQuantity(item.item_code, e.target.value)}
                                  className="w-16"
                                />
                              </TableCell>
                              <TableCell>₵{item.unit_price.toFixed(2)}</TableCell>
                              <TableCell className="font-semibold">₵{item.total_price.toFixed(2)}</TableCell>
                              <TableCell>
                                <Button 
                                  type="button"
                                  size="sm" 
                                  variant="ghost" 
                                  onClick={() => removeItem(item.item_code)}
                                  className="text-red-500 hover:text-red-700"
                                >
                                  <XCircle className="w-4 h-4" />
                                </Button>
                              </TableCell>
                            </TableRow>
                          ))}
                          <TableRow className="bg-gray-50">
                            <TableCell colSpan={3} className="font-semibold text-right">Total Claim:</TableCell>
                            <TableCell colSpan={2} className="font-bold text-green-600 text-lg">
                              ₵{claimTotal.toFixed(2)}
                            </TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </div>
                  )}
                </CardContent>
              </Card>

              <div className="space-y-2">
                <Label>Notes (Optional)</Label>
                <Textarea 
                  value={claimForm.notes}
                  onChange={(e) => setClaimForm({...claimForm, notes: e.target.value})}
                  placeholder="Additional notes for the claim..."
                  rows={2}
                />
              </div>

              <DialogFooter className="sticky bottom-0 bg-white pt-4 border-t">
                <Button type="button" variant="outline" onClick={() => { setCreateClaimOpen(false); resetClaimForm(); }}>
                  Cancel
                </Button>
                <Button 
                  type="submit" 
                  disabled={saving || !verifiedMember?.verified || claimItems.length === 0}
                  className="bg-green-600 hover:bg-green-700"
                  data-testid="create-claim-submit"
                >
                  {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                  Create Claim (₵{claimTotal.toFixed(2)})
                </Button>
              </DialogFooter>
            </form>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
