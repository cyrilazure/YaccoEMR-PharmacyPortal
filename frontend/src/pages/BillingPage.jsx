import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import { billingAPI, patientAPI } from '@/lib/api';
import { formatCurrency } from '@/lib/utils';
import api from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { toast } from 'sonner';
import {
  CreditCard, DollarSign, FileText, Receipt, Plus, Send, Eye,
  TrendingUp, Clock, CheckCircle, XCircle, AlertCircle, Building2,
  Shield, Search, IdCard, Heart
} from 'lucide-react';

export default function BillingPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [invoices, setInvoices] = useState([]);
  const [claims, setClaims] = useState([]);
  const [stats, setStats] = useState(null);
  const [patients, setPatients] = useState([]);
  const [serviceCodes, setServiceCodes] = useState([]);
  const [paystackConfig, setPaystackConfig] = useState(null);
  const [hospitalBankAccount, setHospitalBankAccount] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('invoices');
  
  // Invoice creation state
  const [showCreateInvoice, setShowCreateInvoice] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [lineItems, setLineItems] = useState([{ description: '', service_code: '', quantity: 1, unit_price: 0, discount: 0 }]);
  const [invoiceNotes, setInvoiceNotes] = useState('');
  
  // View invoice state
  const [viewInvoice, setViewInvoice] = useState(null);
  const [paymentEmail, setPaymentEmail] = useState('');
  const [paymentVerificationOpen, setPaymentVerificationOpen] = useState(false);
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState(null);
  const [paymentVerification, setPaymentVerification] = useState({
    amount: 0,
    reference_number: '',
    transaction_id: '',
    notes: '',
    verified: false
  });
  
  // NHIS Insurance state
  const [nhisSearch, setNhisSearch] = useState('');
  const [nhisResults, setNhisResults] = useState([]);
  const [nhisSearching, setNhisSearching] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [invoicesRes, claimsRes, statsRes, patientsRes, codesRes, paystackRes] = await Promise.all([
        billingAPI.getInvoices(),
        billingAPI.getClaims(),
        billingAPI.getStats(),
        patientAPI.getAll(),
        billingAPI.getServiceCodes(),
        billingAPI.getPaystackConfig()
      ]);
      
      setInvoices(invoicesRes.data.invoices || []);
      setClaims(claimsRes.data.claims || []);
      setStats(statsRes.data);
      setPatients(patientsRes.data || []);
      setServiceCodes(codesRes.data.service_codes || []);
      setPaystackConfig(paystackRes.data);
      
      // Fetch hospital's primary bank account for direct deposit
      try {
        const bankRes = await api.get('/finance/bank-accounts');
        const primaryAccount = bankRes.data.accounts?.find(acc => acc.is_primary);
        setHospitalBankAccount(primaryAccount || bankRes.data.accounts?.[0]);
      } catch (err) {
        console.log('Bank account info not available');
      }
    } catch (err) {
      console.error('Error loading billing data:', err);
      toast.error('Failed to load billing data');
    } finally {
      setLoading(false);
    }
  };

  const handleAddLineItem = () => {
    setLineItems([...lineItems, { description: '', service_code: '', quantity: 1, unit_price: 0, discount: 0 }]);
  };

  const handleRemoveLineItem = (index) => {
    setLineItems(lineItems.filter((_, i) => i !== index));
  };

  const handleLineItemChange = (index, field, value) => {
    const updated = [...lineItems];
    updated[index][field] = value;
    
    // Auto-fill price from service code
    if (field === 'service_code') {
      const code = serviceCodes.find(c => c.code === value);
      if (code) {
        updated[index].description = code.description;
        updated[index].unit_price = code.price;
      }
    }
    
    setLineItems(updated);
  };

  const calculateTotal = () => {
    return lineItems.reduce((sum, item) => {
      return sum + (item.quantity * item.unit_price) - (item.discount || 0);
    }, 0);
  };

  const handleCreateInvoice = async () => {
    if (!selectedPatient) {
      toast.error('Please select a patient');
      return;
    }
    
    if (lineItems.length === 0 || !lineItems[0].description) {
      toast.error('Please add at least one line item');
      return;
    }
    
    try {
      const patient = patients.find(p => p.id === selectedPatient);
      await billingAPI.createInvoice({
        patient_id: selectedPatient,
        patient_name: `${patient.first_name} ${patient.last_name}`,
        line_items: lineItems.filter(item => item.description),
        notes: invoiceNotes
      });
      
      toast.success('Invoice created successfully');
      setShowCreateInvoice(false);
      setSelectedPatient(null);
      setLineItems([{ description: '', service_code: '', quantity: 1, unit_price: 0, discount: 0 }]);
      setInvoiceNotes('');
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create invoice');
    }
  };

  const handleSendInvoice = async (invoiceId) => {
    try {
      await billingAPI.sendInvoice(invoiceId);
      toast.success('Invoice sent to patient');
      loadData();
    } catch (err) {
      toast.error('Failed to send invoice');
    }
  };

  const handleInitiatePayment = async () => {
    if (!viewInvoice || !paymentEmail) {
      toast.error('Please enter an email address');
      return;
    }
    
    try {
      const res = await billingAPI.initializePaystack(viewInvoice.id, paymentEmail);
      window.open(res.data.authorization_url, '_blank');
      toast.success('Payment page opened in new tab');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to initialize payment');
    }
  };

  const handleRecordPayment = async (invoice, method) => {
    // For Visa/MasterCard - Use Paystack for secure card processing
    if (method === 'visa' || method === 'mastercard') {
      // Redirect to Paystack payment page for card processing
      if (!paymentEmail) {
        // Ask for email first
        const email = prompt('Enter patient email for card payment:');
        if (!email) return;
        setPaymentEmail(email);
      }
      
      toast.info('Redirecting to secure card payment page...');
      handleInitiatePayment();
      return;
    }
    
    // For Mobile Money - Need to collect mobile number
    if (method === 'mobile_money') {
      const mobileNumber = prompt('Enter patient Mobile Money number (e.g., 0244123456):');
      if (!mobileNumber) return;
      
      // TODO: Integrate with MTN/Vodafone MoMo API
      // For now, show verification dialog with mobile number
      setSelectedPaymentMethod(method);
      setPaymentVerification({
        amount: invoice.balance_due,
        reference_number: mobileNumber,
        transaction_id: '',
        notes: 'Mobile Money payment - awaiting confirmation',
        verified: false
      });
      setPaymentVerificationOpen(true);
      toast.info('Mobile Money payment initiated. Verify patient has approved on their phone.');
      return;
    }
    
    // For Bank Transfer, Cash, NHIS - Open verification dialog
    setSelectedPaymentMethod(method);
    setPaymentVerification({
      amount: invoice.balance_due,
      reference_number: '',
      transaction_id: '',
      notes: '',
      verified: false
    });
    setPaymentVerificationOpen(true);
  };

  const handleConfirmPayment = async () => {
    if (!paymentVerification.verified) {
      toast.error('Please confirm you have verified the payment');
      return;
    }
    
    if (!paymentVerification.reference_number && selectedPaymentMethod !== 'cash') {
      toast.error('Please enter transaction reference/ID');
      return;
    }
    
    try {
      await billingAPI.recordPayment({
        invoice_id: viewInvoice.id,
        amount: paymentVerification.amount,
        payment_method: selectedPaymentMethod,
        reference: paymentVerification.reference_number || paymentVerification.transaction_id,
        notes: `${selectedPaymentMethod} payment - ${paymentVerification.notes}`
      });
      toast.success('Payment recorded successfully');
      setPaymentVerificationOpen(false);
      loadData();
      setViewInvoice(null);
    } catch (err) {
      toast.error('Failed to record payment');
    }
  };

  const handleReverseInvoice = async (invoiceId) => {
    if (!confirm('Are you sure you want to reverse this invoice? This will reopen the billing encounter.')) {
      return;
    }
    
    try {
      await billingAPI.reverseInvoice(invoiceId);
      toast.success('Invoice reversed successfully');
      loadData();
      setViewInvoice(null);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to reverse invoice');
    }
  };

  const handleVoidInvoice = async (invoiceId) => {
    if (!confirm('Are you sure you want to void this invoice? This action cannot be undone.')) {
      return;
    }
    
    try {
      await billingAPI.voidInvoice(invoiceId);
      toast.success('Invoice voided');
      loadData();
      setViewInvoice(null);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to void invoice');
    }
  };

  const handleChangePaymentMethod = async (invoiceId) => {
    const newMethod = prompt('Enter new payment method (cash, nhis_insurance, visa, mastercard, mobile_money):');
    if (!newMethod) return;
    
    try {
      await billingAPI.changePaymentMethod(invoiceId, newMethod);
      toast.success('Payment method updated');
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to change payment method');
    }
  };

  // NHIS Insurance Lookup
  const handleNHISSearch = async () => {
    if (!nhisSearch.trim()) return;
    
    setNhisSearching(true);
    try {
      // Search patients by NHIS ID
      const res = await patientAPI.getAll({ search: nhisSearch });
      // Filter only those with insurance info
      const withInsurance = res.data.filter(p => p.nhis_id || p.insurance_id || p.insurance_provider);
      setNhisResults(withInsurance);
      if (withInsurance.length === 0) {
        toast.info('No patients found with NHIS coverage');
      }
    } catch (err) {
      toast.error('NHIS search failed');
    } finally {
      setNhisSearching(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      'draft': { label: 'Draft', className: 'bg-gray-100 text-gray-700' },
      'sent': { label: 'Sent', className: 'bg-blue-100 text-blue-700' },
      'paid': { label: 'Paid', className: 'bg-green-100 text-green-700' },
      'partially_paid': { label: 'Partially Paid', className: 'bg-amber-100 text-amber-700' },
      'overdue': { label: 'Overdue', className: 'bg-red-100 text-red-700' },
      'reversed': { label: 'Reversed', className: 'bg-purple-100 text-purple-700' },
      'voided': { label: 'Voided', className: 'bg-slate-100 text-slate-600' },
      'pending_insurance': { label: 'Pending Insurance', className: 'bg-yellow-100 text-yellow-700' },
      'cancelled': { label: 'Cancelled', className: 'bg-red-100 text-red-700' }
    };
    const config = statusConfig[status] || { label: status, className: 'bg-gray-100 text-gray-700' };
    return <Badge className={config.className}>{config.label}</Badge>;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Manrope' }}>
            Billing & Revenue
          </h1>
          <p className="text-slate-500">Manage invoices, payments, and insurance claims</p>
        </div>
        <Button onClick={() => setShowCreateInvoice(true)} className="bg-sky-600 hover:bg-sky-700 gap-2">
          <Plus className="w-4 h-4" />
          New Invoice
        </Button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Total Billed</p>
                  <p className="text-2xl font-bold text-slate-900">
                    ${stats.total_billed?.toLocaleString() || '0'}
                  </p>
                </div>
                <div className="w-10 h-10 rounded-lg bg-sky-100 flex items-center justify-center">
                  <DollarSign className="w-5 h-5 text-sky-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Collected</p>
                  <p className="text-2xl font-bold text-green-600">
                    ${stats.total_collected?.toLocaleString() || '0'}
                  </p>
                </div>
                <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Outstanding</p>
                  <p className="text-2xl font-bold text-amber-600">
                    ${stats.total_outstanding?.toLocaleString() || '0'}
                  </p>
                </div>
                <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
                  <Clock className="w-5 h-5 text-amber-600" />
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Collection Rate</p>
                  <p className="text-2xl font-bold text-slate-900">
                    {stats.collection_rate?.toFixed(1) || '0'}%
                  </p>
                </div>
                <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-purple-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="invoices" className="gap-2">
            <Receipt className="w-4 h-4" />
            Invoices ({invoices.length})
          </TabsTrigger>
          <TabsTrigger value="claims" className="gap-2">
            <Building2 className="w-4 h-4" />
            Insurance Claims ({claims.length})
          </TabsTrigger>
          <TabsTrigger value="nhis" className="gap-2">
            <Heart className="w-4 h-4" />
            Insurance Lookup
          </TabsTrigger>
        </TabsList>

        <TabsContent value="invoices" className="mt-4">
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-50 border-b">
                    <tr>
                      <th className="text-left p-4 font-medium text-slate-600">Invoice #</th>
                      <th className="text-left p-4 font-medium text-slate-600">Patient</th>
                      <th className="text-left p-4 font-medium text-slate-600">Date</th>
                      <th className="text-right p-4 font-medium text-slate-600">Total</th>
                      <th className="text-right p-4 font-medium text-slate-600">Balance</th>
                      <th className="text-center p-4 font-medium text-slate-600">Status</th>
                      <th className="text-right p-4 font-medium text-slate-600">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {invoices.map((invoice) => (
                      <tr key={invoice.id} className="hover:bg-slate-50">
                        <td className="p-4 font-mono text-sm">{invoice.invoice_number}</td>
                        <td className="p-4">{invoice.patient_name}</td>
                        <td className="p-4 text-slate-500">{invoice.created_at?.slice(0, 10)}</td>
                        <td className="p-4 text-right font-medium">{formatCurrency(invoice.total)}</td>
                        <td className="p-4 text-right font-medium text-amber-600">
                          {formatCurrency(invoice.balance_due)}
                        </td>
                        <td className="p-4 text-center">{getStatusBadge(invoice.status)}</td>
                        <td className="p-4 text-right">
                          <div className="flex justify-end gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setViewInvoice(invoice)}
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            {invoice.status === 'draft' && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleSendInvoice(invoice.id)}
                              >
                                <Send className="w-4 h-4" />
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                    {invoices.length === 0 && (
                      <tr>
                        <td colSpan={7} className="p-8 text-center text-slate-500">
                          No invoices yet. Create your first invoice.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="claims" className="mt-4">
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-slate-50 border-b">
                    <tr>
                      <th className="text-left p-4 font-medium text-slate-600">Claim #</th>
                      <th className="text-left p-4 font-medium text-slate-600">Insurance</th>
                      <th className="text-left p-4 font-medium text-slate-600">Patient</th>
                      <th className="text-right p-4 font-medium text-slate-600">Amount</th>
                      <th className="text-center p-4 font-medium text-slate-600">Status</th>
                      <th className="text-left p-4 font-medium text-slate-600">Submitted</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {claims.map((claim) => (
                      <tr key={claim.id} className="hover:bg-slate-50">
                        <td className="p-4 font-mono text-sm">{claim.claim_number}</td>
                        <td className="p-4">{claim.insurance_provider}</td>
                        <td className="p-4">{claim.patient_id}</td>
                        <td className="p-4 text-right font-medium">{formatCurrency(claim.total_charges)}</td>
                        <td className="p-4 text-center">{getStatusBadge(claim.status)}</td>
                        <td className="p-4 text-slate-500">{claim.submitted_at?.slice(0, 10) || '-'}</td>
                      </tr>
                    ))}
                    {claims.length === 0 && (
                      <tr>
                        <td colSpan={6} className="p-8 text-center text-slate-500">
                          No insurance claims yet.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* NHIS Lookup Tab */}
        <TabsContent value="nhis" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Heart className="w-5 h-5 text-red-500" />
                NHIS Insurance Verification
              </CardTitle>
              <CardDescription>
                Search for patients with National Health Insurance Scheme (NHIS) coverage
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Search Section */}
              <div className="flex items-center gap-4">
                <div className="relative flex-1 max-w-md">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <Input
                    placeholder="Search by NHIS ID, patient name, or phone..."
                    value={nhisSearch}
                    onChange={(e) => setNhisSearch(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleNHISSearch()}
                    className="pl-9"
                  />
                </div>
                <Button onClick={handleNHISSearch} disabled={nhisSearching}>
                  {nhisSearching ? 'Searching...' : 'Search NHIS'}
                </Button>
              </div>

              {/* Search Results */}
              {nhisResults.length > 0 && (
                <div className="space-y-4">
                  <p className="text-sm text-gray-500">{nhisResults.length} patient(s) with insurance found</p>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-slate-50 border-b">
                        <tr>
                          <th className="text-left p-4 font-medium text-slate-600">Patient Name</th>
                          <th className="text-left p-4 font-medium text-slate-600">Insurance ID</th>
                          <th className="text-left p-4 font-medium text-slate-600">Phone</th>
                          <th className="text-left p-4 font-medium text-slate-600">Insurance Provider</th>
                          <th className="text-center p-4 font-medium text-slate-600">Status</th>
                          <th className="text-center p-4 font-medium text-slate-600">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {nhisResults.map((patient) => (
                          <tr 
                            key={patient.id} 
                            className="hover:bg-blue-50 cursor-pointer transition-colors"
                            onClick={() => navigate(`/patients/${patient.id}`)}
                          >
                            <td className="p-4 font-medium text-blue-600 hover:text-blue-800">
                              {patient.first_name} {patient.last_name}
                            </td>
                            <td className="p-4 font-mono">
                              {patient.nhis_id || patient.insurance_id || '-'}
                            </td>
                            <td className="p-4">{patient.phone || '-'}</td>
                            <td className="p-4">{patient.insurance_provider || 'NHIS Ghana'}</td>
                            <td className="p-4 text-center">
                              <Badge className="bg-green-100 text-green-700">
                                <CheckCircle className="w-3 h-3 mr-1" />
                                Active
                              </Badge>
                            </td>
                            <td className="p-4 text-center">
                              <div className="flex items-center justify-center gap-2">
                                <Button 
                                  size="sm" 
                                  variant="outline"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    navigate(`/patients/${patient.id}`);
                                  }}
                                >
                                  <Eye className="w-4 h-4 mr-1" />
                                  View
                                </Button>
                                <Button 
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedPatient(patient.id);
                                    setShowCreateInvoice(true);
                                  }}
                                >
                                  <Receipt className="w-4 h-4 mr-1" />
                                  Bill
                                </Button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {nhisResults.length === 0 && !nhisSearching && (
                <div className="text-center py-12 text-slate-500">
                  <Shield className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Search for patients to verify NHIS coverage</p>
                  <p className="text-sm mt-2">Enter NHIS ID, patient name, or phone number</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Create Invoice Dialog */}
      <Dialog open={showCreateInvoice} onOpenChange={setShowCreateInvoice}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create New Invoice</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-6">
            {/* Patient Selection */}
            <div className="space-y-2">
              <Label>Patient</Label>
              <Select value={selectedPatient} onValueChange={setSelectedPatient}>
                <SelectTrigger>
                  <SelectValue placeholder="Select patient" />
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

            {/* Line Items */}
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <Label>Line Items</Label>
                <Button type="button" variant="outline" size="sm" onClick={handleAddLineItem}>
                  <Plus className="w-4 h-4 mr-1" /> Add Item
                </Button>
              </div>
              
              {lineItems.map((item, index) => (
                <div key={index} className="grid grid-cols-12 gap-2 items-end">
                  <div className="col-span-3">
                    <Label className="text-xs">Service Code</Label>
                    <Select
                      value={item.service_code}
                      onValueChange={(v) => handleLineItemChange(index, 'service_code', v)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Code" />
                      </SelectTrigger>
                      <SelectContent>
                        {serviceCodes.map((code) => (
                          <SelectItem key={code.code} value={code.code}>
                            {code.code} - {code.description.slice(0, 30)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="col-span-4">
                    <Label className="text-xs">Description</Label>
                    <Input
                      value={item.description}
                      onChange={(e) => handleLineItemChange(index, 'description', e.target.value)}
                      placeholder="Description"
                    />
                  </div>
                  <div className="col-span-1">
                    <Label className="text-xs">Qty</Label>
                    <Input
                      type="number"
                      min="1"
                      value={item.quantity}
                      onChange={(e) => handleLineItemChange(index, 'quantity', parseInt(e.target.value))}
                    />
                  </div>
                  <div className="col-span-2">
                    <Label className="text-xs">Price</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={item.unit_price}
                      onChange={(e) => handleLineItemChange(index, 'unit_price', parseFloat(e.target.value))}
                    />
                  </div>
                  <div className="col-span-1">
                    <Label className="text-xs">Discount</Label>
                    <Input
                      type="number"
                      step="0.01"
                      value={item.discount}
                      onChange={(e) => handleLineItemChange(index, 'discount', parseFloat(e.target.value))}
                    />
                  </div>
                  <div className="col-span-1">
                    {lineItems.length > 1 && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemoveLineItem(index)}
                        className="text-red-500"
                      >
                        <XCircle className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
              
              <div className="flex justify-end border-t pt-4">
                <div className="text-right">
                  <p className="text-sm text-slate-500">Total</p>
                  <p className="text-2xl font-bold">{formatCurrency(calculateTotal())}</p>
                </div>
              </div>
            </div>

            {/* Notes */}
            <div className="space-y-2">
              <Label>Notes (Optional)</Label>
              <Input
                value={invoiceNotes}
                onChange={(e) => setInvoiceNotes(e.target.value)}
                placeholder="Additional notes for the invoice"
              />
            </div>

            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowCreateInvoice(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateInvoice} className="bg-sky-600 hover:bg-sky-700">
                Create Invoice
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* View Invoice Dialog */}
      <Dialog open={!!viewInvoice} onOpenChange={() => setViewInvoice(null)}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>Invoice {viewInvoice?.invoice_number}</DialogTitle>
          </DialogHeader>
          
          <div className="overflow-y-auto pr-2" style={{ maxHeight: 'calc(90vh - 120px)' }}>
          {viewInvoice && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-500">Patient</p>
                  <p className="font-medium">{viewInvoice.patient_name}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Status</p>
                  {getStatusBadge(viewInvoice.status)}
                </div>
                <div>
                  <p className="text-sm text-slate-500">Date</p>
                  <p className="font-medium">{viewInvoice.created_at?.slice(0, 10)}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Due Date</p>
                  <p className="font-medium">{viewInvoice.due_date?.slice(0, 10)}</p>
                </div>
              </div>

              <div className="border rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="text-left p-3">Description</th>
                      <th className="text-right p-3">Qty</th>
                      <th className="text-right p-3">Price</th>
                      <th className="text-right p-3">Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {viewInvoice.line_items?.map((item, i) => (
                      <tr key={i}>
                        <td className="p-3">{item.description}</td>
                        <td className="p-3 text-right">{item.quantity}</td>
                        <td className="p-3 text-right">{formatCurrency(item.unit_price)}</td>
                        <td className="p-3 text-right">{formatCurrency(item.quantity * item.unit_price)}</td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="bg-slate-50 font-medium">
                    <tr>
                      <td colSpan={3} className="p-3 text-right">Total:</td>
                      <td className="p-3 text-right">{formatCurrency(viewInvoice.total)}</td>
                    </tr>
                    <tr>
                      <td colSpan={3} className="p-3 text-right">Paid:</td>
                      <td className="p-3 text-right text-green-600">{formatCurrency(viewInvoice.amount_paid)}</td>
                    </tr>
                    <tr className="text-lg">
                      <td colSpan={3} className="p-3 text-right">Balance Due:</td>
                      <td className="p-3 text-right text-amber-600">{formatCurrency(viewInvoice.balance_due)}</td>
                    </tr>
                  </tfoot>
                </table>
              </div>

              {viewInvoice.balance_due > 0 && (
                <div className="space-y-4 border-t pt-4">
                  <h4 className="font-medium">Payment Options</h4>
                  
                  {/* Hospital Bank Details for Direct Deposit */}
                  <Card className="border-emerald-200 bg-emerald-50">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base flex items-center gap-2 text-emerald-800">
                        <Building2 className="w-5 h-5" />
                        Direct Bank Deposit (No Gateway Fees)
                      </CardTitle>
                      <CardDescription className="text-emerald-700">
                        Transfer {formatCurrency(viewInvoice.balance_due)} directly to hospital account
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      {hospitalBankAccount ? (
                        <Alert className="bg-white border-emerald-300">
                          <Building2 className="w-4 h-4 text-emerald-600" />
                          <AlertTitle className="text-emerald-800 font-bold">Hospital Bank Account Details</AlertTitle>
                          <AlertDescription className="space-y-4 mt-3">
                            {/* Domestic Bank Transfer (Ghana) */}
                            <div className="border-l-4 border-emerald-500 pl-4 bg-emerald-50 p-3 rounded">
                              <h5 className="font-bold text-emerald-900 mb-2">🇬🇭 For Transfers Within Ghana</h5>
                              <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                                <div>
                                  <span className="text-gray-600">Bank Name:</span>
                                  <span className="font-bold ml-2 block">{hospitalBankAccount.bank_name}</span>
                                </div>
                                <div>
                                  <span className="text-gray-600">Account Number:</span>
                                  <span className="font-mono font-bold ml-2 text-lg block">{hospitalBankAccount.account_number}</span>
                                </div>
                                <div>
                                  <span className="text-gray-600">Account Name:</span>
                                  <span className="font-medium ml-2 block">{hospitalBankAccount.account_name}</span>
                                </div>
                                <div>
                                  <span className="text-gray-600">Branch:</span>
                                  <span className="font-medium ml-2 block">{hospitalBankAccount.branch || 'Main Branch'}</span>
                                </div>
                                <div>
                                  <span className="text-gray-600">Account Type:</span>
                                  <span className="font-medium ml-2 block capitalize">{hospitalBankAccount.account_type}</span>
                                </div>
                                <div>
                                  <span className="text-gray-600">Currency:</span>
                                  <span className="font-bold ml-2 block">{hospitalBankAccount.currency}</span>
                                </div>
                                {hospitalBankAccount.bank_code && (
                                  <div>
                                    <span className="text-gray-600">Bank Code:</span>
                                    <span className="font-mono ml-2 block">{hospitalBankAccount.bank_code}</span>
                                  </div>
                                )}
                                <div className="col-span-2 border-t pt-2 mt-2">
                                  <span className="text-gray-600">Amount to Pay:</span>
                                  <span className="font-bold text-emerald-700 ml-2 text-xl">{formatCurrency(viewInvoice.balance_due)}</span>
                                </div>
                                <div className="col-span-2">
                                  <span className="text-gray-600">Payment Reference:</span>
                                  <span className="font-mono ml-2 bg-emerald-200 px-2 py-1 rounded font-bold">{viewInvoice.invoice_number}</span>
                                </div>
                              </div>
                            </div>

                            {/* International Transfer Option */}
                            {hospitalBankAccount.swift_code && (
                              <div className="border-l-4 border-blue-500 pl-4 bg-blue-50 p-3 rounded">
                                <h5 className="font-bold text-blue-900 mb-2">🌍 For International Transfers</h5>
                                <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                                  <div>
                                    <span className="text-gray-600">SWIFT Code:</span>
                                    <span className="font-mono font-bold ml-2 block">{hospitalBankAccount.swift_code}</span>
                                  </div>
                                  <div>
                                    <span className="text-gray-600">Bank Name:</span>
                                    <span className="font-medium ml-2 block">{hospitalBankAccount.bank_name}</span>
                                  </div>
                                  <div className="col-span-2">
                                    <span className="text-gray-600">Beneficiary Name:</span>
                                    <span className="font-medium ml-2 block">{hospitalBankAccount.account_name}</span>
                                  </div>
                                  <div className="col-span-2">
                                    <span className="text-gray-600">Account Number:</span>
                                    <span className="font-mono font-bold ml-2 text-lg block">{hospitalBankAccount.account_number}</span>
                                  </div>
                                  <div>
                                    <span className="text-gray-600">Country:</span>
                                    <span className="font-medium ml-2 block">Ghana</span>
                                  </div>
                                  <div>
                                    <span className="text-gray-600">Currency:</span>
                                    <span className="font-bold ml-2 block">{hospitalBankAccount.currency}</span>
                                  </div>
                                </div>
                              </div>
                            )}
                            
                            {/* Transfer Instructions */}
                            <div className="mt-3 p-3 bg-emerald-100 rounded text-sm text-emerald-800">
                              <strong>💡 How to Make Bank Transfer:</strong>
                              <div className="grid md:grid-cols-2 gap-4 mt-2">
                                <div>
                                  <p className="font-semibold mb-1">📱 Mobile Banking:</p>
                                  <ol className="list-decimal ml-5 space-y-1 text-xs">
                                    <li>Open your bank app (GCB Mobile, Ecobank Mobile, etc.)</li>
                                    <li>Select "Transfer Money"</li>
                                    <li>Choose "To Other Bank" or "Same Bank"</li>
                                    <li>Enter Account: <strong>{hospitalBankAccount.account_number}</strong></li>
                                    <li>Amount: <strong>{formatCurrency(viewInvoice.balance_due)}</strong></li>
                                    <li>Reference: <strong>{viewInvoice.invoice_number}</strong></li>
                                    <li>Confirm and save receipt</li>
                                  </ol>
                                </div>
                                <div>
                                  <p className="font-semibold mb-1">🏦 Bank Branch:</p>
                                  <ol className="list-decimal ml-5 space-y-1 text-xs">
                                    <li>Visit any {hospitalBankAccount.bank_name} branch or any bank</li>
                                    <li>Fill deposit/transfer slip with:
                                      <ul className="ml-4 mt-1">
                                        <li>• Account: {hospitalBankAccount.account_number}</li>
                                        <li>• Name: {hospitalBankAccount.account_name}</li>
                                        <li>• Amount: {formatCurrency(viewInvoice.balance_due)}</li>
                                      </ul>
                                    </li>
                                    <li>Complete transfer and get receipt</li>
                                    <li>Keep receipt for verification</li>
                                  </ol>
                                </div>
                              </div>
                              <p className="mt-3 text-xs bg-white p-2 rounded border border-emerald-300">
                                <strong>⏱️ Processing Time:</strong> Local transfers: Same day to 1 business day | International: 3-5 business days
                                <br/>
                                <strong>💵 Fees:</strong> No fees from hospital. Your bank may charge transfer fees.
                                <br/>
                                <strong>📞 After Payment:</strong> Contact billing office at hospital with your receipt to confirm payment.
                              </p>
                            </div>
                          </AlertDescription>
                        </Alert>
                      ) : (
                        <Alert>
                          <AlertCircle className="w-4 h-4" />
                          <AlertTitle>Bank Account Not Configured</AlertTitle>
                          <AlertDescription>
                            Contact hospital IT Admin to set up bank account details for direct deposits.
                          </AlertDescription>
                        </Alert>
                      )}
                    </CardContent>
                  </Card>
                  
                  {paystackConfig?.enabled && (
                    <div className="flex gap-2 items-end">
                      <div className="flex-1">
                        <Label>Email for Paystack Payment</Label>
                        <Input
                          type="email"
                          placeholder="patient@email.com"
                          value={paymentEmail}
                          onChange={(e) => setPaymentEmail(e.target.value)}
                        />
                      </div>
                      <Button onClick={handleInitiatePayment} className="bg-green-600 hover:bg-green-700">
                        <CreditCard className="w-4 h-4 mr-2" />
                        Pay with Paystack
                      </Button>
                    </div>
                  )}
                  
                  <div>
                    <Label className="mb-2 block text-sm font-medium">Or Record Manual Payment</Label>
                    <div className="grid grid-cols-3 gap-2">
                    <Button
                      variant="outline"
                      onClick={() => handleRecordPayment(viewInvoice, 'cash')}
                      className="gap-2"
                    >
                      <DollarSign className="w-4 h-4" />
                      Cash
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => handleRecordPayment(viewInvoice, 'nhis_insurance')}
                      className="gap-2"
                    >
                      <Shield className="w-4 h-4" />
                      NHIS
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => handleRecordPayment(viewInvoice, 'visa')}
                      className="gap-2"
                    >
                      <CreditCard className="w-4 h-4" />
                      Visa
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => handleRecordPayment(viewInvoice, 'mastercard')}
                      className="gap-2"
                    >
                      <CreditCard className="w-4 h-4" />
                      MasterCard
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => handleRecordPayment(viewInvoice, 'mobile_money')}
                      className="gap-2"
                    >
                      <Heart className="w-4 h-4" />
                      Mobile Money
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => handleRecordPayment(viewInvoice, 'bank_transfer')}
                      className="gap-2"
                    >
                      <Building2 className="w-4 h-4" />
                      Bank Transfer
                    </Button>
                  </div>
                  </div>
                </div>
              )}
              
              {/* Invoice Actions */}
              {viewInvoice.status === 'sent' && (
                <div className="border-t pt-4">
                  <h4 className="font-medium mb-3 text-red-700">Invoice Management</h4>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      className="text-red-600 border-red-300 hover:bg-red-50"
                      onClick={() => handleReverseInvoice(viewInvoice.id)}
                    >
                      <XCircle className="w-4 h-4 mr-2" />
                      Reverse Invoice
                    </Button>
                    <Button
                      variant="outline"
                      className="text-gray-600"
                      onClick={() => handleChangePaymentMethod(viewInvoice.id)}
                    >
                      <AlertCircle className="w-4 h-4 mr-2" />
                      Change Payment Type
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Payment Verification Dialog */}
      <Dialog open={paymentVerificationOpen} onOpenChange={setPaymentVerificationOpen}>
        <DialogContent className="max-w-md max-h-[85vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-emerald-600" />
              Verify {selectedPaymentMethod?.toUpperCase().replace('_', ' ')} Payment
            </DialogTitle>
            <DialogDescription>
              Confirm payment receipt - Amount: {formatCurrency(paymentVerification.amount)}
            </DialogDescription>
          </DialogHeader>
          
          <div className="overflow-y-auto pr-2" style={{ maxHeight: 'calc(85vh - 160px)' }}>
          <div className="space-y-4 py-2">
            <Alert className="bg-amber-50 border-amber-300">
              <AlertCircle className="w-4 h-4 text-amber-600" />
              <AlertTitle className="text-amber-800">Payment Verification Required</AlertTitle>
              <AlertDescription className="text-amber-700 text-sm">
                Only record payment after you have VERIFIED funds received. Do not record unverified payments.
              </AlertDescription>
            </Alert>
            
            <div className="space-y-2">
              <Label>Amount Received *</Label>
              <Input
                type="number"
                step="0.01"
                value={paymentVerification.amount}
                onChange={(e) => setPaymentVerification({...paymentVerification, amount: parseFloat(e.target.value)})}
                className="font-bold text-lg"
                required
              />
              <p className="text-xs text-gray-500">Verify this matches the amount received</p>
            </div>
            
            {selectedPaymentMethod === 'bank_transfer' && (
              <div className="space-y-2">
                <Label>Bank Transaction Reference *</Label>
                <Input
                  value={paymentVerification.reference_number}
                  onChange={(e) => setPaymentVerification({...paymentVerification, reference_number: e.target.value})}
                  placeholder="e.g., TRF/2026/02/12345"
                  required
                />
                <p className="text-xs text-gray-500">Enter the reference from bank statement or transfer receipt</p>
              </div>
            )}
            
            {selectedPaymentMethod === 'mobile_money' && (
              <div className="space-y-2">
                <Label>Mobile Money Transaction ID *</Label>
                <Input
                  value={paymentVerification.transaction_id}
                  onChange={(e) => setPaymentVerification({...paymentVerification, transaction_id: e.target.value})}
                  placeholder="e.g., MM123456789"
                  required
                />
                <p className="text-xs text-gray-500">Transaction ID from mobile money confirmation SMS</p>
              </div>
            )}
            
            {(selectedPaymentMethod === 'visa' || selectedPaymentMethod === 'mastercard') && (
              <div className="space-y-2">
                <Label>Card Transaction Reference/Approval Code *</Label>
                <Input
                  value={paymentVerification.reference_number}
                  onChange={(e) => setPaymentVerification({...paymentVerification, reference_number: e.target.value})}
                  placeholder="POS approval code or receipt number"
                  required
                />
                <p className="text-xs text-gray-500">Approval code from POS terminal receipt</p>
              </div>
            )}
            
            {selectedPaymentMethod === 'cash' && (
              <div className="space-y-2">
                <Label>Receipt Number (Optional)</Label>
                <Input
                  value={paymentVerification.reference_number}
                  onChange={(e) => setPaymentVerification({...paymentVerification, reference_number: e.target.value})}
                  placeholder="Cash receipt number"
                />
              </div>
            )}
            
            {selectedPaymentMethod === 'nhis_insurance' && (
              <div className="space-y-2">
                <Label>NHIS Claim/Authorization Number *</Label>
                <Input
                  value={paymentVerification.reference_number}
                  onChange={(e) => setPaymentVerification({...paymentVerification, reference_number: e.target.value})}
                  placeholder="NHIS authorization or claim number"
                  required
                />
              </div>
            )}
            
            <div className="space-y-2">
              <Label>Additional Notes</Label>
              <Input
                value={paymentVerification.notes}
                onChange={(e) => setPaymentVerification({...paymentVerification, notes: e.target.value})}
                placeholder="Any additional payment details..."
              />
            </div>
            
            <div className="flex items-center gap-3 p-4 bg-red-50 border-2 border-red-300 rounded-lg">
              <input
                type="checkbox"
                id="verify-payment"
                checked={paymentVerification.verified}
                onChange={(e) => setPaymentVerification({...paymentVerification, verified: e.target.checked})}
                className="rounded w-5 h-5"
              />
              <Label htmlFor="verify-payment" className="text-red-800 font-semibold cursor-pointer flex-1">
                <Shield className="w-5 h-5 inline mr-2" />
                I confirm that I have VERIFIED this payment was received
              </Label>
            </div>
          </div>
          </div>
          
          <DialogFooter className="mt-4">
            <Button 
              variant="outline" 
              onClick={() => setPaymentVerificationOpen(false)}
              type="button"
            >
              Cancel
            </Button>
            <Button 
              onClick={handleConfirmPayment}
              disabled={!paymentVerification.verified}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              <CheckCircle className="w-4 h-4 mr-2" />
              Record Verified Payment
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
