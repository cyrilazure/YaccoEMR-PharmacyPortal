import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import { billingAPI, patientAPI, billingShiftsAPI } from '@/lib/api';
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
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import { toast } from 'sonner';
import {
  CreditCard, DollarSign, FileText, Receipt, Plus, Send, Eye,
  TrendingUp, Clock, CheckCircle, XCircle, AlertCircle, Building2,
  Shield, Search, IdCard, Heart, Printer, LogIn, LogOut, Timer,
  Wallet, Smartphone, Banknote, BarChart3, Users, RefreshCw, Loader2,
  Calendar, ArrowUp, ArrowDown, Minus
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
  
  // Shift Management State
  const [activeShift, setActiveShift] = useState(null);
  const [shiftMetrics, setShiftMetrics] = useState(null);
  const [outstanding, setOutstanding] = useState(null);
  const [recentPayments, setRecentPayments] = useState([]);
  const [clockInOpen, setClockInOpen] = useState(false);
  const [clockOutOpen, setClockOutOpen] = useState(false);
  const [shiftType, setShiftType] = useState('day');
  const [clockingIn, setClockingIn] = useState(false);
  const [clockingOut, setClockingOut] = useState(false);
  const [closingNotes, setClosingNotes] = useState('');
  const [actualCash, setActualCash] = useState('');
  
  // Admin Dashboard State
  const [adminDashboard, setAdminDashboard] = useState(null);
  const [allShifts, setAllShifts] = useState([]);
  const [loadingAdminData, setLoadingAdminData] = useState(false);
  
  // Hospital Info for receipts
  const [hospitalInfo, setHospitalInfo] = useState(null);
  
  // Senior Biller Dashboard State
  const [seniorBillerDashboard, setSeniorBillerDashboard] = useState(null);
  
  // Check user roles
  const isAdmin = ['hospital_admin', 'hospital_it_admin', 'finance_manager', 'admin'].includes(user?.role);
  const isSeniorBiller = user?.role === 'senior_biller';
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
  
  // Insurance Details Dialog
  const [viewInsuranceOpen, setViewInsuranceOpen] = useState(false);
  const [selectedInsurancePatient, setSelectedInsurancePatient] = useState(null);
  
  // Print Receipt State
  const [printReceiptOpen, setPrintReceiptOpen] = useState(false);
  const [receiptInvoice, setReceiptInvoice] = useState(null);
  const receiptRef = useRef(null);

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
      
      // Fetch hospital info for receipts
      try {
        const hospitalRes = await api.get('/hospital/info');
        setHospitalInfo(hospitalRes.data);
      } catch (err) {
        // Fallback to user's hospital info
        setHospitalInfo({
          name: user?.hospital_name || 'Hospital',
          phone: user?.hospital_phone || '',
          email: user?.hospital_email || '',
          address: user?.hospital_address || '',
          region: user?.region || '',
          district: user?.district || ''
        });
      }
      
      // Load shift data
      await loadShiftData();
      
    } catch (err) {
      console.error('Error loading billing data:', err);
      toast.error('Failed to load billing data');
    } finally {
      setLoading(false);
    }
  };
  
  // Load shift-based dashboard data
  const loadShiftData = useCallback(async () => {
    try {
      if (isAdmin) {
        // Admin gets full dashboard
        const adminRes = await billingShiftsAPI.getAdminDashboard();
        setAdminDashboard(adminRes.data);
        
        const shiftsRes = await billingShiftsAPI.getAllShifts({ limit: 20 });
        setAllShifts(shiftsRes.data.shifts || []);
      }
      
      if (isSeniorBiller) {
        // Senior biller gets department-wide view
        const seniorRes = await billingShiftsAPI.getSeniorBillerDashboard();
        setSeniorBillerDashboard(seniorRes.data);
        
        const shiftsRes = await billingShiftsAPI.getAllShifts({ limit: 20 });
        setAllShifts(shiftsRes.data.shifts || []);
      }
      
      // All billers get their shift data
      const billerRes = await billingShiftsAPI.getBillerDashboard();
      if (billerRes.data.has_active_shift) {
        setActiveShift(billerRes.data.shift);
        setShiftMetrics(billerRes.data.shift_metrics);
      } else {
        setActiveShift(null);
        setShiftMetrics(null);
      }
      setOutstanding(billerRes.data.outstanding);
      setRecentPayments(billerRes.data.recent_payments || []);
      
    } catch (err) {
      console.error('Error loading shift data:', err);
    }
  }, [isAdmin, isSeniorBiller]);
  
  // Clock In Handler
  const handleClockIn = async () => {
    setClockingIn(true);
    try {
      await billingShiftsAPI.clockIn({ shift_type: shiftType });
      toast.success('Shift started successfully!');
      setClockInOpen(false);
      await loadShiftData();
      loadData();
    } catch (err) {
      console.error('Clock in error:', err);
      toast.error(err.response?.data?.detail || 'Failed to clock in');
    } finally {
      setClockingIn(false);
    }
  };
  
  // Clock Out Handler
  const handleClockOut = async () => {
    setClockingOut(true);
    try {
      await billingShiftsAPI.clockOut({
        closing_notes: closingNotes,
        actual_cash: actualCash ? parseFloat(actualCash) : null
      });
      toast.success('Shift closed successfully!');
      setClockOutOpen(false);
      setClosingNotes('');
      setActualCash('');
      await loadShiftData();
      loadData();
    } catch (err) {
      console.error('Clock out error:', err);
      toast.error(err.response?.data?.detail || 'Failed to clock out');
    } finally {
      setClockingOut(false);
    }
  };
  
  // Calculate shift duration
  const getShiftDuration = (startTime) => {
    if (!startTime) return '0h 0m';
    const start = new Date(startTime);
    const now = new Date();
    const diff = Math.floor((now - start) / 1000 / 60);
    const hours = Math.floor(diff / 60);
    const minutes = diff % 60;
    return `${hours}h ${minutes}m`;
  };

  // Print Receipt Handler
  const handlePrintReceipt = (invoice) => {
    setReceiptInvoice(invoice);
    setPrintReceiptOpen(true);
  };

  const printReceipt = () => {
    const printContent = receiptRef.current;
    if (!printContent) return;

    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Payment Receipt - ${receiptInvoice?.invoice_number}</title>
          <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; max-width: 400px; margin: 0 auto; }
            .receipt { border: 2px solid #000; padding: 20px; }
            .header { text-align: center; border-bottom: 2px dashed #000; padding-bottom: 15px; margin-bottom: 15px; }
            .header img { height: 48px; width: auto; margin: 0 auto 8px; display: block; object-fit: contain; }
            .hospital-name { font-size: 18px; font-weight: bold; margin-bottom: 5px; }
            .hospital-info { font-size: 11px; color: #555; }
            .receipt-title { font-size: 16px; font-weight: bold; margin: 15px 0; text-align: center; background: #f0f0f0; padding: 8px; }
            .info-row { display: flex; justify-content: space-between; margin: 8px 0; font-size: 12px; }
            .info-label { color: #666; }
            .info-value { font-weight: 600; }
            .divider { border-top: 1px dashed #000; margin: 15px 0; }
            .items-header { font-weight: bold; font-size: 12px; border-bottom: 1px solid #000; padding-bottom: 5px; margin-bottom: 10px; }
            .item-row { display: flex; justify-content: space-between; font-size: 11px; margin: 5px 0; }
            .totals { margin-top: 15px; border-top: 2px solid #000; padding-top: 10px; }
            .total-row { display: flex; justify-content: space-between; font-size: 13px; margin: 5px 0; }
            .grand-total { font-size: 16px; font-weight: bold; background: #000; color: #fff; padding: 10px; margin-top: 10px; }
            .payment-info { margin-top: 15px; padding: 10px; background: #e8f5e9; border: 1px solid #4caf50; }
            .payment-badge { display: inline-block; background: #4caf50; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px; font-weight: bold; }
            .footer { text-align: center; margin-top: 20px; font-size: 10px; color: #666; }
            .footer-thanks { font-size: 14px; font-weight: bold; margin-bottom: 5px; }
            @media print { body { padding: 0; } .receipt { border: none; } }
          </style>
        </head>
        <body>
          ${printContent.innerHTML}
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => {
      printWindow.print();
      printWindow.close();
    }, 250);
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
          <p className="text-slate-500">
            {isAdmin ? 'Hospital-wide financial overview' : 'Manage invoices, payments, and insurance claims'}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="icon" onClick={() => { loadData(); loadShiftData(); }}>
            <RefreshCw className="w-4 h-4" />
          </Button>
          <Button onClick={() => setShowCreateInvoice(true)} className="bg-sky-600 hover:bg-sky-700 gap-2">
            <Plus className="w-4 h-4" />
            New Invoice
          </Button>
        </div>
      </div>

      {/* Shift Clock In/Out Status Card (For Billers) */}
      {!isAdmin && (
        <Card className={activeShift ? "border-emerald-200 bg-emerald-50/50" : "border-amber-200 bg-amber-50/50"}>
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${activeShift ? 'bg-emerald-100' : 'bg-amber-100'}`}>
                  {activeShift ? <Timer className="w-6 h-6 text-emerald-600" /> : <Clock className="w-6 h-6 text-amber-600" />}
                </div>
                <div>
                  {activeShift ? (
                    <>
                      <div className="flex items-center gap-2">
                        <Badge className="bg-emerald-500">ON SHIFT</Badge>
                        <span className="text-sm font-medium text-emerald-700">{activeShift.shift_type?.toUpperCase()} Shift</span>
                      </div>
                      <p className="text-sm text-slate-600 mt-1">
                        Started: {new Date(activeShift.start_time).toLocaleTimeString()} • Duration: <span className="font-semibold">{getShiftDuration(activeShift.start_time)}</span>
                      </p>
                    </>
                  ) : (
                    <>
                      <p className="font-medium text-amber-700">Not Clocked In</p>
                      <p className="text-sm text-slate-500">Clock in to start tracking your shift collections</p>
                    </>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3">
                {activeShift ? (
                  <Button onClick={() => setClockOutOpen(true)} variant="outline" className="border-red-300 text-red-600 hover:bg-red-50">
                    <LogOut className="w-4 h-4 mr-2" /> Clock Out
                  </Button>
                ) : (
                  <Button onClick={() => setClockInOpen(true)} className="bg-emerald-600 hover:bg-emerald-700">
                    <LogIn className="w-4 h-4 mr-2" /> Clock In
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Shift-Scoped KPIs (Biller View) */}
      {!isAdmin && activeShift && shiftMetrics && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          <Card className="bg-gradient-to-br from-sky-50 to-sky-100 border-sky-200">
            <CardContent className="p-4 text-center">
              <FileText className="w-6 h-6 mx-auto mb-2 text-sky-600" />
              <p className="text-xs text-sky-700 font-medium">Invoices (Shift)</p>
              <p className="text-xl font-bold text-sky-900">{shiftMetrics.invoices_generated}</p>
              <p className="text-xs text-sky-600">₵{shiftMetrics.invoices_amount?.toLocaleString()}</p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
            <CardContent className="p-4 text-center">
              <Receipt className="w-6 h-6 mx-auto mb-2 text-green-600" />
              <p className="text-xs text-green-700 font-medium">Payments (Shift)</p>
              <p className="text-xl font-bold text-green-900">{shiftMetrics.payments_received}</p>
              <p className="text-xs text-green-600">₵{shiftMetrics.payments_amount?.toLocaleString()}</p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-emerald-50 to-emerald-100 border-emerald-200">
            <CardContent className="p-4 text-center">
              <Banknote className="w-6 h-6 mx-auto mb-2 text-emerald-600" />
              <p className="text-xs text-emerald-700 font-medium">Cash</p>
              <p className="text-xl font-bold text-emerald-900">₵{shiftMetrics.cash_collected?.toLocaleString() || '0'}</p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
            <CardContent className="p-4 text-center">
              <Smartphone className="w-6 h-6 mx-auto mb-2 text-purple-600" />
              <p className="text-xs text-purple-700 font-medium">Mobile Money</p>
              <p className="text-xl font-bold text-purple-900">₵{shiftMetrics.mobile_money_collected?.toLocaleString() || '0'}</p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
            <CardContent className="p-4 text-center">
              <CreditCard className="w-6 h-6 mx-auto mb-2 text-blue-600" />
              <p className="text-xs text-blue-700 font-medium">Card</p>
              <p className="text-xl font-bold text-blue-900">₵{shiftMetrics.card_payments?.toLocaleString() || '0'}</p>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-teal-50 to-teal-100 border-teal-200">
            <CardContent className="p-4 text-center">
              <Shield className="w-6 h-6 mx-auto mb-2 text-teal-600" />
              <p className="text-xs text-teal-700 font-medium">Insurance</p>
              <p className="text-xl font-bold text-teal-900">₵{shiftMetrics.insurance_billed?.toLocaleString() || '0'}</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Admin Financial Dashboard */}
      {isAdmin && adminDashboard && (
        <div className="space-y-4">
          {/* Period Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="bg-gradient-to-br from-sky-500 to-sky-600 text-white">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sky-100 text-sm">Today's Revenue</p>
                    <p className="text-3xl font-bold">₵{adminDashboard.daily?.revenue?.toLocaleString() || '0'}</p>
                    <p className="text-sky-200 text-sm mt-1">{adminDashboard.daily?.payments_count || 0} payments</p>
                  </div>
                  <Calendar className="w-10 h-10 opacity-50" />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-emerald-500 to-emerald-600 text-white">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-emerald-100 text-sm">This Week</p>
                    <p className="text-3xl font-bold">₵{adminDashboard.weekly?.revenue?.toLocaleString() || '0'}</p>
                    <p className="text-emerald-200 text-sm mt-1">{adminDashboard.weekly?.invoices_count || 0} invoices</p>
                  </div>
                  <TrendingUp className="w-10 h-10 opacity-50" />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-purple-100 text-sm">This Month</p>
                    <p className="text-3xl font-bold">₵{adminDashboard.monthly?.revenue?.toLocaleString() || '0'}</p>
                    <p className="text-purple-200 text-sm mt-1">{adminDashboard.monthly?.invoices_count || 0} invoices</p>
                  </div>
                  <BarChart3 className="w-10 h-10 opacity-50" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Payment Mode Distribution & Shifts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">Payment Methods (Monthly)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(adminDashboard.payment_modes || {}).map(([mode, amount]) => {
                    const total = Object.values(adminDashboard.payment_modes || {}).reduce((a, b) => a + b, 0) || 1;
                    const percentage = ((amount / total) * 100).toFixed(1);
                    const icons = { cash: Banknote, mobile_money: Smartphone, card: CreditCard, insurance: Shield, bank_transfer: Building2 };
                    const colors = { cash: 'emerald', mobile_money: 'purple', card: 'blue', insurance: 'teal', bank_transfer: 'slate' };
                    const Icon = icons[mode] || Wallet;
                    const color = colors[mode] || 'gray';
                    return (
                      <div key={mode} className="flex items-center gap-3">
                        <Icon className={`w-5 h-5 text-${color}-500`} />
                        <div className="flex-1">
                          <div className="flex justify-between text-sm mb-1">
                            <span className="capitalize">{mode.replace('_', ' ')}</span>
                            <span className="font-semibold">₵{amount.toLocaleString()}</span>
                          </div>
                          <Progress value={parseFloat(percentage)} className="h-2" />
                        </div>
                        <span className="text-sm text-slate-500 w-12 text-right">{percentage}%</span>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center justify-between">
                  Shift Overview
                  <Badge variant="outline">{adminDashboard.shifts?.active || 0} Active</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 bg-emerald-50 rounded-lg text-center">
                      <Users className="w-5 h-5 mx-auto mb-1 text-emerald-600" />
                      <p className="text-2xl font-bold text-emerald-700">{adminDashboard.shifts?.active || 0}</p>
                      <p className="text-xs text-emerald-600">Active Shifts</p>
                    </div>
                    <div className="p-3 bg-blue-50 rounded-lg text-center">
                      <CheckCircle className="w-5 h-5 mx-auto mb-1 text-blue-600" />
                      <p className="text-2xl font-bold text-blue-700">{adminDashboard.shifts?.completed_today || 0}</p>
                      <p className="text-xs text-blue-600">Completed Today</p>
                    </div>
                  </div>
                  <Separator />
                  <div className="p-3 bg-amber-50 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-amber-700 font-medium">Outstanding Balances</p>
                        <p className="text-xl font-bold text-amber-800">₵{adminDashboard.outstanding?.total_outstanding?.toLocaleString() || '0'}</p>
                      </div>
                      <AlertCircle className="w-6 h-6 text-amber-500" />
                    </div>
                  </div>
                  <div className="p-3 bg-teal-50 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-teal-700 font-medium">Pending Insurance Claims</p>
                        <p className="text-xl font-bold text-teal-800">₵{adminDashboard.pending_insurance_claims?.toLocaleString() || '0'}</p>
                      </div>
                      <Shield className="w-6 h-6 text-teal-500" />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Senior Biller Department Dashboard */}
      {isSeniorBiller && seniorBillerDashboard && (
        <div className="space-y-4">
          {/* Department Header */}
          <Alert className="bg-indigo-50 border-indigo-200">
            <Users className="w-4 h-4 text-indigo-600" />
            <AlertTitle className="text-indigo-800">Senior Biller Dashboard</AlertTitle>
            <AlertDescription className="text-indigo-700">
              Viewing all billing activity for: {seniorBillerDashboard.department || 'All Departments'}
            </AlertDescription>
          </Alert>

          {/* Today's Summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className="bg-gradient-to-br from-indigo-500 to-indigo-600 text-white">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-indigo-100 text-sm">Active Billers</p>
                    <p className="text-3xl font-bold">{seniorBillerDashboard.today_summary?.active_billers || 0}</p>
                  </div>
                  <Users className="w-10 h-10 opacity-50" />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-emerald-500 to-emerald-600 text-white">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-emerald-100 text-sm">Today's Revenue</p>
                    <p className="text-3xl font-bold">₵{seniorBillerDashboard.today_summary?.total_payments_amount?.toLocaleString() || '0'}</p>
                  </div>
                  <DollarSign className="w-10 h-10 opacity-50" />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-blue-100 text-sm">Invoices Today</p>
                    <p className="text-3xl font-bold">{seniorBillerDashboard.today_summary?.total_invoices || 0}</p>
                    <p className="text-blue-200 text-sm">₵{seniorBillerDashboard.today_summary?.total_invoice_amount?.toLocaleString() || '0'}</p>
                  </div>
                  <FileText className="w-10 h-10 opacity-50" />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-purple-100 text-sm">Payments Today</p>
                    <p className="text-3xl font-bold">{seniorBillerDashboard.today_summary?.total_payments || 0}</p>
                  </div>
                  <Receipt className="w-10 h-10 opacity-50" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Payment Breakdown and Active Shifts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">Payment Methods (Today)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(seniorBillerDashboard.payment_breakdown || {}).map(([mode, amount]) => {
                    const icons = { cash: Banknote, mobile_money: Smartphone, card: CreditCard, insurance: Shield, bank_transfer: Building2 };
                    const colors = { cash: 'emerald', mobile_money: 'purple', card: 'blue', insurance: 'teal', bank_transfer: 'slate' };
                    const Icon = icons[mode] || Wallet;
                    const color = colors[mode] || 'gray';
                    return (
                      <div key={mode} className="flex items-center gap-3 justify-between p-2 bg-slate-50 rounded">
                        <div className="flex items-center gap-2">
                          <Icon className={`w-5 h-5 text-${color}-500`} />
                          <span className="capitalize">{mode.replace('_', ' ')}</span>
                        </div>
                        <span className="font-semibold">₵{(amount || 0).toLocaleString()}</span>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center justify-between">
                  Active Shifts
                  <Badge className="bg-emerald-500">{seniorBillerDashboard.active_shifts?.length || 0} Active</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {seniorBillerDashboard.active_shifts?.length > 0 ? (
                    seniorBillerDashboard.active_shifts.map((shift) => (
                      <div key={shift.id} className="p-3 border rounded-lg hover:bg-slate-50">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium">{shift.biller_name}</p>
                            <p className="text-xs text-slate-500">
                              {shift.shift_type?.toUpperCase()} • Started {new Date(shift.start_time).toLocaleTimeString()}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="font-semibold text-emerald-600">₵{(shift.payments_collected || 0).toLocaleString()}</p>
                            <p className="text-xs text-slate-500">{shift.invoices_count || 0} invoices</p>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-center text-slate-500 py-4">No active shifts</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* Outstanding Balances (Persistent - Shows for all) */}
      {outstanding && (outstanding.total_outstanding > 0 || outstanding.pending_insurance_value > 0) && (
        <Card className="border-amber-200 bg-amber-50/30">
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-amber-600" />
              Outstanding Balances (Persistent)
            </CardTitle>
            <CardDescription>These balances persist until cleared - not affected by shift changes</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-3 bg-white rounded-lg border">
                <p className="text-sm text-slate-500">Total Outstanding</p>
                <p className="text-xl font-bold text-amber-600">₵{outstanding.total_outstanding?.toLocaleString() || '0'}</p>
              </div>
              <div className="p-3 bg-white rounded-lg border">
                <p className="text-sm text-slate-500">Partially Paid</p>
                <p className="text-xl font-bold text-orange-600">{outstanding.partially_paid_count || 0}</p>
              </div>
              <div className="p-3 bg-white rounded-lg border">
                <p className="text-sm text-slate-500">Unpaid Invoices</p>
                <p className="text-xl font-bold text-red-600">{outstanding.unpaid_count || 0}</p>
              </div>
              <div className="p-3 bg-white rounded-lg border">
                <p className="text-sm text-slate-500">Pending Insurance</p>
                <p className="text-xl font-bold text-teal-600">₵{outstanding.pending_insurance_value?.toLocaleString() || '0'}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stats Cards (Shows for non-admin when no active shift, or simplified view) */}
      {!isAdmin && !activeShift && stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Total Billed</p>
                  <p className="text-2xl font-bold text-slate-900">
                    ₵{stats.total_billed?.toLocaleString() || '0'}
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
                    ₵{stats.total_collected?.toLocaleString() || '0'}
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
                    ₵{stats.total_outstanding?.toLocaleString() || '0'}
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
          {(isAdmin || isSeniorBiller) && (
            <TabsTrigger value="reconciliation" className="gap-2">
              <CheckCircle className="w-4 h-4" />
              Shift Reconciliation
            </TabsTrigger>
          )}
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
                              title="View Invoice"
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            {invoice.status === 'draft' && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleSendInvoice(invoice.id)}
                                title="Send Invoice"
                              >
                                <Send className="w-4 h-4" />
                              </Button>
                            )}
                            {(invoice.status === 'paid' || invoice.balance_due === 0) && (
                              <Button
                                size="sm"
                                variant="outline"
                                className="text-green-600 border-green-300 hover:bg-green-50"
                                onClick={() => handlePrintReceipt(invoice)}
                                title="Print Receipt"
                              >
                                <Printer className="w-4 h-4" />
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

        {/* Insurance Lookup Tab */}
        <TabsContent value="nhis" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-blue-500" />
                Insurance Verification
              </CardTitle>
              <CardDescription>
                Search for patients with health insurance coverage (NHIS & Private Insurers)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Search Section */}
              <div className="flex items-center gap-4">
                <div className="relative flex-1 max-w-md">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <Input
                    placeholder="Search by Insurance ID, patient name, or phone..."
                    value={nhisSearch}
                    onChange={(e) => setNhisSearch(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleNHISSearch()}
                    className="pl-9"
                  />
                </div>
                <Button onClick={handleNHISSearch} disabled={nhisSearching}>
                  {nhisSearching ? 'Searching...' : 'Search Insurance'}
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
                            onClick={() => {
                              setSelectedInsurancePatient(patient);
                              setViewInsuranceOpen(true);
                            }}
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
                                    setSelectedInsurancePatient(patient);
                                    setViewInsuranceOpen(true);
                                  }}
                                >
                                  <Eye className="w-4 h-4 mr-1" />
                                  View Insurance
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
                  <p>Search for patients to verify insurance coverage</p>
                  <p className="text-sm mt-2">Enter Insurance ID, patient name, or phone number</p>
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

      {/* Insurance Details Dialog - Billing View Only */}
      <Dialog open={viewInsuranceOpen} onOpenChange={setViewInsuranceOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-blue-600" />
              Insurance Information
            </DialogTitle>
            <DialogDescription>
              Patient insurance details for billing purposes
            </DialogDescription>
          </DialogHeader>
          
          {selectedInsurancePatient && (
            <div className="space-y-4">
              {/* Patient Basic Info (Non-Medical) */}
              <div className="p-4 bg-slate-50 rounded-lg">
                <h4 className="font-semibold text-slate-700 mb-3">Patient Information</h4>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-slate-500">Full Name</p>
                    <p className="font-medium">{selectedInsurancePatient.first_name} {selectedInsurancePatient.last_name}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Date of Birth</p>
                    <p className="font-medium">{selectedInsurancePatient.date_of_birth || 'Not provided'}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Phone</p>
                    <p className="font-medium">{selectedInsurancePatient.phone || 'Not provided'}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">MRN</p>
                    <p className="font-medium font-mono">{selectedInsurancePatient.mrn || 'N/A'}</p>
                  </div>
                </div>
              </div>

              {/* Insurance Details */}
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h4 className="font-semibold text-blue-800 mb-3 flex items-center gap-2">
                  <IdCard className="w-4 h-4" />
                  Insurance Coverage
                </h4>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-blue-600">Insurance Provider</p>
                    <p className="font-semibold text-blue-900">{selectedInsurancePatient.insurance_provider || 'NHIS Ghana'}</p>
                  </div>
                  <div>
                    <p className="text-blue-600">Insurance/Policy ID</p>
                    <p className="font-semibold text-blue-900 font-mono">{selectedInsurancePatient.nhis_id || selectedInsurancePatient.insurance_id || 'Not provided'}</p>
                  </div>
                  <div>
                    <p className="text-blue-600">Insurance Plan</p>
                    <p className="font-semibold text-blue-900">{selectedInsurancePatient.insurance_plan || 'Standard'}</p>
                  </div>
                  <div>
                    <p className="text-blue-600">Coverage Status</p>
                    <Badge className="bg-green-100 text-green-700 mt-1">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Active
                    </Badge>
                  </div>
                </div>
              </div>

              {/* Billing Address */}
              <div className="p-4 bg-gray-50 rounded-lg">
                <h4 className="font-semibold text-slate-700 mb-2">Billing Address</h4>
                <p className="text-sm text-slate-600">{selectedInsurancePatient.address || 'Address not provided'}</p>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3 pt-2">
                <Button 
                  className="flex-1"
                  onClick={() => {
                    setSelectedPatient(selectedInsurancePatient.id);
                    setViewInsuranceOpen(false);
                    setShowCreateInvoice(true);
                  }}
                >
                  <Receipt className="w-4 h-4 mr-2" />
                  Create Invoice
                </Button>
                <Button 
                  variant="outline"
                  onClick={() => setViewInsuranceOpen(false)}
                >
                  Close
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Print Receipt Dialog */}
      <Dialog open={printReceiptOpen} onOpenChange={setPrintReceiptOpen}>
        <DialogContent className="max-w-md max-h-[90vh] flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Printer className="w-5 h-5 text-green-600" />
              Payment Receipt
            </DialogTitle>
            <DialogDescription>
              Preview and print receipt for patient
            </DialogDescription>
          </DialogHeader>
          
          {receiptInvoice && (
            <>
              {/* Receipt Preview - Scrollable */}
              <div className="overflow-y-auto flex-1 max-h-[60vh] pr-2">
                <div ref={receiptRef} className="border rounded-lg p-4 bg-white">
                  <div className="receipt">
                    {/* Header - Dynamic Hospital Info with Logo */}
                    <div className="header text-center border-b-2 border-dashed pb-4 mb-4">
                      {hospitalInfo?.logo_url && (
                        <div className="mb-2">
                          <img 
                            src={hospitalInfo.logo_url} 
                            alt={hospitalInfo?.name || 'Hospital Logo'}
                            className="h-12 w-auto mx-auto object-contain"
                            onError={(e) => { e.target.style.display = 'none'; }}
                          />
                        </div>
                      )}
                      <div className="hospital-name text-lg font-bold uppercase">
                        {hospitalInfo?.name || user?.hospital_name || 'HOSPITAL'}
                      </div>
                      <div className="hospital-info text-xs text-gray-500 mt-1">
                        {hospitalInfo?.address && <>{hospitalInfo.address}<br /></>}
                        {(hospitalInfo?.district || hospitalInfo?.region) && (
                          <>{hospitalInfo.district}{hospitalInfo.district && hospitalInfo.region ? ', ' : ''}{hospitalInfo.region}<br /></>
                        )}
                        {hospitalInfo?.phone && <>Tel: {hospitalInfo.phone}</>}
                        {hospitalInfo?.phone && hospitalInfo?.email && <> | </>}
                        {hospitalInfo?.email && <>Email: {hospitalInfo.email}</>}
                      </div>
                    </div>

                    {/* Receipt Title */}
                    <div className="receipt-title text-center font-bold bg-gray-100 py-2 mb-4">
                      PAYMENT RECEIPT
                    </div>

                    {/* Receipt Info */}
                    <div className="space-y-2 text-sm">
                      <div className="info-row flex justify-between">
                        <span className="info-label text-gray-500">Receipt No:</span>
                        <span className="info-value font-semibold">{receiptInvoice.invoice_number}</span>
                      </div>
                      <div className="info-row flex justify-between">
                        <span className="info-label text-gray-500">Date:</span>
                        <span className="info-value font-semibold">{new Date().toLocaleDateString('en-GB')}</span>
                      </div>
                      <div className="info-row flex justify-between">
                        <span className="info-label text-gray-500">Time:</span>
                        <span className="info-value font-semibold">{new Date().toLocaleTimeString()}</span>
                      </div>
                    </div>

                    <Separator className="my-4" />

                    {/* Patient Info */}
                    <div className="space-y-2 text-sm">
                      <div className="info-row flex justify-between">
                        <span className="info-label text-gray-500">Patient Name:</span>
                        <span className="info-value font-semibold">{receiptInvoice.patient_name}</span>
                      </div>
                      {receiptInvoice.patient_mrn && (
                        <div className="info-row flex justify-between">
                          <span className="info-label text-gray-500">MRN:</span>
                          <span className="info-value font-mono">{receiptInvoice.patient_mrn}</span>
                        </div>
                      )}
                    </div>

                    <Separator className="my-4" />

                    {/* Items */}
                    <div className="items-section">
                      <div className="items-header font-bold text-sm border-b pb-2 mb-2">Service Details</div>
                      {receiptInvoice.line_items?.map((item, index) => (
                        <div key={index} className="item-row flex justify-between text-xs py-1">
                          <span className="flex-1">{item.description}</span>
                          <span className="font-semibold">₵{(item.quantity * item.unit_price).toFixed(2)}</span>
                        </div>
                      )) || (
                        <div className="item-row flex justify-between text-xs py-1">
                          <span>Medical Services</span>
                          <span className="font-semibold">₵{receiptInvoice.total?.toFixed(2)}</span>
                        </div>
                      )}
                    </div>

                    <Separator className="my-4" />

                    {/* Totals */}
                    <div className="totals space-y-2">
                      <div className="total-row flex justify-between text-sm">
                        <span>Subtotal:</span>
                        <span>₵{receiptInvoice.subtotal?.toFixed(2) || receiptInvoice.total?.toFixed(2)}</span>
                      </div>
                      {receiptInvoice.tax_amount > 0 && (
                      <div className="total-row flex justify-between text-sm">
                        <span>Tax:</span>
                        <span>₵{receiptInvoice.tax_amount?.toFixed(2)}</span>
                      </div>
                    )}
                    {receiptInvoice.discount > 0 && (
                      <div className="total-row flex justify-between text-sm text-green-600">
                        <span>Discount:</span>
                        <span>-₵{receiptInvoice.discount?.toFixed(2)}</span>
                      </div>
                    )}
                    <div className="grand-total flex justify-between text-lg font-bold bg-black text-white p-3 -mx-4 mt-4">
                      <span>TOTAL PAID:</span>
                      <span>₵{receiptInvoice.total?.toFixed(2)}</span>
                    </div>
                  </div>

                  {/* Payment Status */}
                  <div className="payment-info mt-4 p-3 bg-green-50 border border-green-200 rounded">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-green-700">Payment Status:</span>
                      <span className="payment-badge bg-green-500 text-white px-3 py-1 rounded text-xs font-bold">
                        ✓ PAID
                      </span>
                    </div>
                    <div className="text-xs text-green-600 mt-2">
                      Payment Method: {receiptInvoice.payment_method || 'Cash/Mobile Money'}
                    </div>
                  </div>

                  {/* Footer */}
                  <div className="footer text-center mt-6 text-xs text-gray-500">
                    <div className="footer-thanks text-sm font-bold mb-1">Thank you for choosing us!</div>
                    <p>This is a computer-generated receipt.</p>
                    <p>For inquiries, please contact our billing department.</p>
                  </div>
                </div>
              </div>
            </div>

              {/* Print Button */}
              <DialogFooter className="mt-4">
                <Button variant="outline" onClick={() => setPrintReceiptOpen(false)}>
                  Close
                </Button>
                <Button onClick={printReceipt} className="bg-green-600 hover:bg-green-700">
                  <Printer className="w-4 h-4 mr-2" />
                  Print Receipt
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Clock In Dialog */}
      <Dialog open={clockInOpen} onOpenChange={setClockInOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <LogIn className="w-5 h-5 text-emerald-600" />
              Start Billing Shift
            </DialogTitle>
            <DialogDescription>
              Clock in to start tracking your shift collections
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Select Shift Type</Label>
              <Select value={shiftType} onValueChange={setShiftType}>
                <SelectTrigger>
                  <SelectValue placeholder="Select shift type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="day">Day Shift (7AM - 3PM)</SelectItem>
                  <SelectItem value="evening">Evening Shift (3PM - 11PM)</SelectItem>
                  <SelectItem value="night">Night Shift (11PM - 7AM)</SelectItem>
                  <SelectItem value="12hr_day">12-Hour Day (7AM - 7PM)</SelectItem>
                  <SelectItem value="12hr_night">12-Hour Night (7PM - 7AM)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Alert>
              <Clock className="w-4 h-4" />
              <AlertTitle>Current Time</AlertTitle>
              <AlertDescription>{new Date().toLocaleString()}</AlertDescription>
            </Alert>
            <Alert className="bg-blue-50 border-blue-200">
              <AlertCircle className="w-4 h-4 text-blue-600" />
              <AlertDescription className="text-blue-700">
                Your shift metrics (invoices, payments) will be tracked from this point. Outstanding balances remain visible.
              </AlertDescription>
            </Alert>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setClockInOpen(false)}>Cancel</Button>
            <Button onClick={handleClockIn} disabled={clockingIn} className="bg-emerald-600 hover:bg-emerald-700">
              {clockingIn ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Clocking In...</> : <><LogIn className="w-4 h-4 mr-2" /> Clock In</>}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Clock Out Dialog */}
      <Dialog open={clockOutOpen} onOpenChange={setClockOutOpen}>
        <DialogContent className="max-w-md max-h-[90vh] flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <LogOut className="w-5 h-5 text-red-600" />
              End Billing Shift
            </DialogTitle>
            <DialogDescription>Close your shift and submit your collection summary</DialogDescription>
          </DialogHeader>
          <div className="overflow-y-auto flex-1 max-h-[60vh] pr-2">
            <div className="space-y-4 py-4">
              {activeShift && shiftMetrics && (
                <div className="p-4 bg-slate-50 rounded-lg space-y-3">
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <p className="text-slate-500">Shift Type</p>
                      <p className="font-semibold">{activeShift.shift_type?.toUpperCase()}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Duration</p>
                      <p className="font-semibold text-emerald-600">{getShiftDuration(activeShift.start_time)}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Invoices Created</p>
                      <p className="font-semibold">{shiftMetrics.invoices_generated}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Payments Received</p>
                      <p className="font-semibold">{shiftMetrics.payments_received}</p>
                    </div>
                  </div>
                  <Separator />
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <p className="text-slate-500">Total Cash</p>
                      <p className="font-semibold text-emerald-600">₵{shiftMetrics.cash_collected?.toLocaleString() || '0'}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Mobile Money</p>
                      <p className="font-semibold text-purple-600">₵{shiftMetrics.mobile_money_collected?.toLocaleString() || '0'}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Card Payments</p>
                      <p className="font-semibold text-blue-600">₵{shiftMetrics.card_payments?.toLocaleString() || '0'}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Insurance Billed</p>
                      <p className="font-semibold text-teal-600">₵{shiftMetrics.insurance_billed?.toLocaleString() || '0'}</p>
                    </div>
                  </div>
                  <Separator />
                  <div className="p-3 bg-emerald-50 rounded-lg">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-emerald-700">Total Collections</span>
                      <span className="text-xl font-bold text-emerald-800">₵{shiftMetrics.payments_amount?.toLocaleString() || '0'}</span>
                    </div>
                  </div>
                </div>
              )}
              
              <div className="space-y-2">
                <Label>Actual Cash on Hand (for reconciliation)</Label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">₵</span>
                  <Input
                    type="number"
                    step="0.01"
                    placeholder="Enter actual cash amount"
                    value={actualCash}
                    onChange={(e) => setActualCash(e.target.value)}
                    className="pl-8"
                  />
                </div>
                <p className="text-xs text-slate-500">Optional: Enter the actual cash you collected to help identify discrepancies</p>
              </div>
              
              <div className="space-y-2">
                <Label>Closing Notes</Label>
                <Textarea
                  placeholder="Any notes about this shift..."
                  value={closingNotes}
                  onChange={(e) => setClosingNotes(e.target.value)}
                  rows={3}
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setClockOutOpen(false)}>Cancel</Button>
            <Button onClick={handleClockOut} disabled={clockingOut} variant="destructive">
              {clockingOut ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Clocking Out...</> : <><LogOut className="w-4 h-4 mr-2" /> Clock Out</>}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
