import React, { useState, useEffect, useCallback } from 'react';
import { useZxing } from 'react-zxing';
import { useAuth } from '@/lib/auth';
import { getErrorMessage } from '@/lib/utils';
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
  Pill, RefreshCw, Search, CheckCircle, AlertCircle, Clock, User, Package, FileText, Eye, Check, X,
  AlertTriangle, Loader2, CreditCard, DollarSign, TrendingUp, Send, Plus, ArrowDownCircle,
  Building, Verified, ArrowUpCircle, BarChart3, Truck, MapPin, Phone, Camera, XCircle
} from 'lucide-react';
import api from '@/lib/api';

// ========== API DEFINITIONS ==========
const prescriptionAPI = {
  getQueue: (status) => api.get('/prescriptions/pharmacy/queue', { params: { status } }),
  updateStatus: (id, data) => api.put(`/prescriptions/${id}/status`, data),
};

const supplyAPI = {
  getInventory: (params) => api.get('/supply-chain/inventory', { params }),
  createInventoryItem: (data) => api.post('/supply-chain/inventory', data),
  receiveStock: (data) => api.post('/supply-chain/stock/receive', data),
  getBatches: (params) => api.get('/supply-chain/stock/batches', { params }),
  getSuppliers: (params) => api.get('/supply-chain/suppliers', { params }),
  seedSuppliers: () => api.post('/supply-chain/suppliers/seed'),
  getDashboard: () => api.get('/supply-chain/dashboard'),
};

const fdaAPI = {
  lookupByBarcode: (barcode) => api.get('/fda/lookup/barcode', { params: { barcode } }),
  verifyDrug: (params) => api.get('/fda/verify', { params }),
};

const nhisAPI = {
  verifyMember: (data) => api.post('/nhis/verify-member', data),
  getDrugTariff: (params) => api.get('/nhis/tariff', { params }),
  createClaim: (data) => api.post('/nhis/claims/pharmacy', data),
  getClaims: (params) => api.get('/nhis/claims', { params }),
  submitClaim: (id) => api.post(`/nhis/claims/${id}/submit`),
  getDashboard: () => api.get('/nhis/dashboard'),
};

const pharmacyNetworkAPI = {
  getPharmacies: (params) => api.get('/pharmacy-network/pharmacies', { params }),
  getStats: () => api.get('/pharmacy-network/stats'),
  getRegions: () => api.get('/pharmacy-network/regions'),
};

export default function PharmacyPortal() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [activeModule, setActiveModule] = useState('dispensing');
  
  // Dispensing State
  const [prescriptions, setPrescriptions] = useState([]);
  const [rxStats, setRxStats] = useState({});
  const [rxTab, setRxTab] = useState('pending');
  const [rxSearch, setRxSearch] = useState('');
  const [selectedRx, setSelectedRx] = useState(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [dispenseDialogOpen, setDispenseDialogOpen] = useState(false);
  const [pharmacistNotes, setPharmacistNotes] = useState('');
  
  // Supply Chain State
  const [inventory, setInventory] = useState([]);
  const [inventoryDashboard, setInventoryDashboard] = useState(null);
  const [batches, setBatches] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [inventorySearch, setInventorySearch] = useState('');
  const [addItemOpen, setAddItemOpen] = useState(false);
  const [receiveStockOpen, setReceiveStockOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  
  // NHIS State
  const [nhisDashboard, setNhisDashboard] = useState(null);
  const [nhisClaims, setNhisClaims] = useState([]);
  const [drugTariff, setDrugTariff] = useState([]);
  const [verifiedMember, setVerifiedMember] = useState(null);
  const [membershipId, setMembershipId] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [createClaimOpen, setCreateClaimOpen] = useState(false);
  const [claimItems, setClaimItems] = useState([]);
  const [drugSearch, setDrugSearch] = useState('');
  
  // Pharmacy Directory State
  const [pharmacies, setPharmacies] = useState([]);
  const [directoryStats, setDirectoryStats] = useState(null);
  const [directorySearch, setDirectorySearch] = useState('');
  const [selectedRegion, setSelectedRegion] = useState('');
  const [regions, setRegions] = useState([]);
  
  // Forms
  const [itemForm, setItemForm] = useState({
    drug_name: '', drug_code: '', manufacturer: '', category: '',
    unit_of_measure: 'tablet', unit_cost: '', selling_price: '',
    reorder_level: '', max_stock_level: '', fda_registration: '',
    barcode: ''
  });
  
  const [receiveForm, setReceiveForm] = useState({
    inventory_item_id: '', quantity: '', batch_number: '',
    expiry_date: '', supplier_name: '', unit_cost: ''
  });
  
  // Barcode Scanner State
  const [scannerActive, setScannerActive] = useState(false);
  
  const [claimForm, setClaimForm] = useState({
    patient_name: '', membership_id: '', diagnosis_codes: '',
    prescription_date: new Date().toISOString().split('T')[0],
    dispensing_date: new Date().toISOString().split('T')[0],
    prescriber_name: '', notes: ''
  });
  
  const [saving, setSaving] = useState(false);

  // ========== DATA FETCHING ==========
  const fetchDispensingData = useCallback(async () => {
    try {
      const response = await prescriptionAPI.getQueue();
      setPrescriptions(response.data.prescriptions || []);
      setRxStats(response.data.stats || {});
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to load prescriptions'));
    }
  }, []);

  const fetchInventoryData = useCallback(async () => {
    try {
      const [dashRes, invRes, batchRes, supplierRes] = await Promise.all([
        supplyAPI.getDashboard(),
        supplyAPI.getInventory({ search: inventorySearch || undefined }),
        supplyAPI.getBatches({}),
        supplyAPI.getSuppliers({})
      ]);
      setInventoryDashboard(dashRes.data);
      setInventory(invRes.data.items || []);
      setBatches(batchRes.data.batches || []);
      setSuppliers(supplierRes.data.suppliers || []);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to load inventory'));
    }
  }, [inventorySearch]);

  const fetchNHISData = useCallback(async () => {
    try {
      const [dashRes, claimsRes, tariffRes] = await Promise.all([
        nhisAPI.getDashboard(),
        nhisAPI.getClaims({}),
        nhisAPI.getDrugTariff({ covered_only: true })
      ]);
      setNhisDashboard(dashRes.data);
      setNhisClaims(claimsRes.data.claims || []);
      setDrugTariff(tariffRes.data.drugs || []);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to load NHIS data'));
    }
  }, []);

  const fetchDirectoryData = useCallback(async () => {
    try {
      const [pharmRes, statsRes, regionsRes] = await Promise.all([
        pharmacyNetworkAPI.getPharmacies({ search: directorySearch || undefined, region: selectedRegion || undefined, limit: 50 }),
        pharmacyNetworkAPI.getStats(),
        pharmacyNetworkAPI.getRegions()
      ]);
      setPharmacies(pharmRes.data.pharmacies || []);
      setDirectoryStats(statsRes.data);
      setRegions(regionsRes.data.regions || []);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to load pharmacy directory'));
    }
  }, [directorySearch, selectedRegion]);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchDispensingData(),
        fetchInventoryData(),
        fetchNHISData(),
        fetchDirectoryData()
      ]);
      setLoading(false);
    };
    loadData();
  }, [fetchDispensingData, fetchInventoryData, fetchNHISData, fetchDirectoryData]);

  // ========== HANDLERS ==========
  const handleUpdateRxStatus = async (rxId, newStatus) => {
    setSaving(true);
    try {
      await prescriptionAPI.updateStatus(rxId, { status: newStatus, pharmacist_notes: pharmacistNotes });
      toast.success(`Prescription ${newStatus.replace('_', ' ')}`);
      setDispenseDialogOpen(false);
      setViewDialogOpen(false);
      setPharmacistNotes('');
      fetchDispensingData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to update prescription'));
    } finally {
      setSaving(false);
    }
  };

  const handleAddInventoryItem = async (e) => {
    e.preventDefault();
    if (!itemForm.drug_name) { toast.error('Drug name is required'); return; }
    setSaving(true);
    try {
      const payload = {
        ...itemForm,
        unit_cost: itemForm.unit_cost ? parseFloat(itemForm.unit_cost) : 0,
        selling_price: itemForm.selling_price ? parseFloat(itemForm.selling_price) : 0,
        reorder_level: itemForm.reorder_level ? parseInt(itemForm.reorder_level) : 10,
        max_stock_level: itemForm.max_stock_level ? parseInt(itemForm.max_stock_level) : 1000
      };
      await supplyAPI.createInventoryItem(payload);
      toast.success('Item added to inventory');
      setAddItemOpen(false);
      setItemForm({ drug_name: '', drug_code: '', manufacturer: '', category: '', unit_of_measure: 'tablet', unit_cost: '', selling_price: '', reorder_level: '', max_stock_level: '', fda_registration: '', barcode: '' });
      fetchInventoryData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to add item'));
    } finally {
      setSaving(false);
    }
  };

  const handleReceiveStock = async (e) => {
    e.preventDefault();
    if (!receiveForm.inventory_item_id || !receiveForm.quantity || !receiveForm.batch_number || !receiveForm.expiry_date) {
      toast.error('Fill all required fields'); return;
    }
    setSaving(true);
    try {
      const payload = {
        ...receiveForm,
        quantity: parseInt(receiveForm.quantity) || 0,
        unit_cost: receiveForm.unit_cost ? parseFloat(receiveForm.unit_cost) : 0
      };
      await supplyAPI.receiveStock(payload);
      toast.success('Stock received and logged');
      setReceiveStockOpen(false);
      setReceiveForm({ inventory_item_id: '', quantity: '', batch_number: '', expiry_date: '', supplier_name: '', unit_cost: '' });
      setSelectedItem(null);
      fetchInventoryData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to receive stock'));
    } finally {
      setSaving(false);
    }
  };

  const handleVerifyMember = async () => {
    if (!membershipId.trim()) { toast.error('Enter NHIS membership ID'); return; }
    setVerifying(true);
    try {
      const res = await nhisAPI.verifyMember({ membership_id: membershipId });
      setVerifiedMember(res.data);
      if (res.data.verified) {
        toast.success('Member verified');
        setClaimForm(prev => ({ ...prev, membership_id: res.data.membership_id, patient_name: res.data.full_name }));
      } else {
        toast.warning(res.data.message);
      }
    } catch (err) {
      toast.error(getErrorMessage(err, 'Verification failed'));
    } finally {
      setVerifying(false);
    }
  };

  const handleAddDrugToClaim = (drug) => {
    if (claimItems.find(i => i.item_code === drug.code)) { toast.warning('Drug already added'); return; }
    setClaimItems(prev => [...prev, {
      item_code: drug.code, item_name: drug.name, quantity: 1,
      unit_price: drug.nhis_price || 0, total_price: drug.nhis_price || 0
    }]);
  };

  const handleCreateClaim = async (e) => {
    e.preventDefault();
    if (!claimForm.membership_id || claimItems.length === 0) { toast.error('Verify member and add items'); return; }
    setSaving(true);
    try {
      await nhisAPI.createClaim({
        ...claimForm,
        diagnosis_codes: claimForm.diagnosis_codes.split(',').map(c => c.trim()).filter(Boolean),
        claim_items: claimItems
      });
      toast.success('Claim created');
      setCreateClaimOpen(false);
      setClaimForm({ patient_name: '', membership_id: '', diagnosis_codes: '', prescription_date: new Date().toISOString().split('T')[0], dispensing_date: new Date().toISOString().split('T')[0], prescriber_name: '', notes: '' });
      setClaimItems([]);
      setVerifiedMember(null);
      setMembershipId('');
      fetchNHISData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to create claim'));
    } finally {
      setSaving(false);
    }
  };

  const handleSubmitClaim = async (claimId) => {
    try {
      await nhisAPI.submitClaim(claimId);
      toast.success('Claim submitted to NHIS');
      fetchNHISData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to submit claim'));
    }
  };

  const handleSeedSuppliers = async () => {
    try {
      const res = await supplyAPI.seedSuppliers();
      toast.success(res.data.message);
      fetchInventoryData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to seed suppliers'));
    }
  };

  const openReceiveStock = (item) => {
    setSelectedItem(item);
    setReceiveForm({ ...receiveForm, inventory_item_id: item.id, unit_cost: item.unit_cost || 0 });
    setReceiveStockOpen(true);
  };

  // Barcode Scanner Handler
  const handleBarcodeDetected = async (barcode) => {
    setScannerActive(false);
    toast.info(`Barcode detected: ${barcode}`);
    
    try {
      // Lookup drug info from FDA API
      const res = await fdaAPI.lookupByBarcode(barcode);
      if (res.data.found) {
        const drug = res.data.drug;
        setItemForm({
          ...itemForm,
          barcode: barcode,
          drug_name: drug.name || drug.generic_name || '',
          drug_code: drug.registration_number || '',
          fda_registration: drug.registration_number || '',
          manufacturer: drug.manufacturer || '',
          category: drug.category || '',
        });
        toast.success(`Drug found: ${drug.name || drug.generic_name}`);
      } else {
        setItemForm({ ...itemForm, barcode: barcode });
        toast.warning('Drug not found in FDA database. Please enter details manually.');
      }
    } catch (err) {
      setItemForm({ ...itemForm, barcode: barcode });
      toast.warning('Could not lookup drug info. Please enter details manually.');
    }
  };

  // ========== HELPERS ==========
  const getStatusBadge = (status) => {
    const colors = {
      pending_verification: 'bg-yellow-100 text-yellow-800',
      approved: 'bg-blue-100 text-blue-800',
      dispensed: 'bg-green-100 text-green-800',
      ready_for_pickup: 'bg-purple-100 text-purple-800',
      cancelled: 'bg-red-100 text-red-800',
      draft: 'bg-gray-100 text-gray-700',
      submitted: 'bg-blue-100 text-blue-700',
      paid: 'bg-emerald-100 text-emerald-700',
      rejected: 'bg-red-100 text-red-700',
      in_stock: 'bg-green-100 text-green-700',
      low_stock: 'bg-amber-100 text-amber-700',
      out_of_stock: 'bg-red-100 text-red-700'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const filteredPrescriptions = prescriptions.filter(rx => {
    const matchesSearch = !rxSearch || rx.patient_name?.toLowerCase().includes(rxSearch.toLowerCase()) || rx.rx_number?.toLowerCase().includes(rxSearch.toLowerCase());
    if (rxTab === 'pending') return matchesSearch && rx.status === 'pending_verification';
    if (rxTab === 'approved') return matchesSearch && rx.status === 'approved';
    if (rxTab === 'dispensed') return matchesSearch && ['dispensed', 'ready_for_pickup', 'picked_up'].includes(rx.status);
    return matchesSearch;
  });

  const filteredTariff = drugTariff.filter(d => !drugSearch || d.name.toLowerCase().includes(drugSearch.toLowerCase()) || d.code.toLowerCase().includes(drugSearch.toLowerCase()));
  const claimTotal = claimItems.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-10 h-10 animate-spin text-emerald-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="pharmacy-portal">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Pill className="w-7 h-7 text-emerald-600" />
            Pharmacy Portal
          </h1>
          <p className="text-slate-500 mt-1">Dispensing, Inventory, NHIS Claims & Network Directory</p>
        </div>
        <Button onClick={() => { fetchDispensingData(); fetchInventoryData(); fetchNHISData(); fetchDirectoryData(); }} variant="outline" className="gap-2" data-testid="refresh-all-btn">
          <RefreshCw className="w-4 h-4" /> Refresh All
        </Button>
      </div>

      {/* Main Module Tabs */}
      <Tabs value={activeModule} onValueChange={setActiveModule}>
        <TabsList className="grid grid-cols-4 w-full max-w-2xl">
          <TabsTrigger value="dispensing" className="gap-2" data-testid="tab-dispensing">
            <Pill className="w-4 h-4" /> Dispensing
            {rxStats.pending > 0 && <Badge className="ml-1 bg-yellow-500">{rxStats.pending}</Badge>}
          </TabsTrigger>
          <TabsTrigger value="inventory" className="gap-2" data-testid="tab-inventory">
            <Package className="w-4 h-4" /> Inventory
            {inventoryDashboard?.inventory?.low_stock > 0 && <Badge className="ml-1 bg-amber-500">{inventoryDashboard.inventory.low_stock}</Badge>}
          </TabsTrigger>
          <TabsTrigger value="nhis" className="gap-2" data-testid="tab-nhis">
            <CreditCard className="w-4 h-4" /> Insurance Claims
          </TabsTrigger>
          <TabsTrigger value="directory" className="gap-2" data-testid="tab-directory">
            <Building className="w-4 h-4" /> Directory
          </TabsTrigger>
        </TabsList>

        {/* ==================== DISPENSING TAB ==================== */}
        <TabsContent value="dispensing" className="mt-4 space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className="bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200">
              <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-yellow-700">Pending</p>
                    <p className="text-3xl font-bold text-yellow-800">{rxStats.pending || 0}</p>
                  </div>
                  <Clock className="w-10 h-10 text-yellow-500 opacity-50" />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
              <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-blue-700">Approved</p>
                    <p className="text-3xl font-bold text-blue-800">{rxStats.approved || 0}</p>
                  </div>
                  <CheckCircle className="w-10 h-10 text-blue-500 opacity-50" />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
              <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-green-700">Dispensed</p>
                    <p className="text-3xl font-bold text-green-800">{rxStats.dispensed || 0}</p>
                  </div>
                  <Package className="w-10 h-10 text-green-500 opacity-50" />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
              <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-purple-700">Ready Pickup</p>
                    <p className="text-3xl font-bold text-purple-800">{rxStats.ready || 0}</p>
                  </div>
                  <User className="w-10 h-10 text-purple-500 opacity-50" />
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input placeholder="Search by patient name or Rx number..." value={rxSearch} onChange={(e) => setRxSearch(e.target.value)} className="pl-10" data-testid="rx-search" />
          </div>

          <Tabs value={rxTab} onValueChange={setRxTab}>
            <TabsList className="grid grid-cols-3 w-full max-w-md">
              <TabsTrigger value="pending"><Clock className="w-4 h-4 mr-1" /> Pending</TabsTrigger>
              <TabsTrigger value="approved"><CheckCircle className="w-4 h-4 mr-1" /> Approved</TabsTrigger>
              <TabsTrigger value="dispensed"><Package className="w-4 h-4 mr-1" /> Dispensed</TabsTrigger>
            </TabsList>
            <TabsContent value={rxTab} className="mt-4">
              <Card>
                <CardContent className="p-0">
                  {filteredPrescriptions.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">
                      <Pill className="w-12 h-12 mx-auto mb-4 opacity-30" />
                      <p>No prescriptions found</p>
                    </div>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Rx Number</TableHead>
                          <TableHead>Patient</TableHead>
                          <TableHead>Prescriber</TableHead>
                          <TableHead>Meds</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Date</TableHead>
                          <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredPrescriptions.map((rx) => (
                          <TableRow key={rx.id}>
                            <TableCell className="font-mono font-medium">{rx.rx_number}</TableCell>
                            <TableCell>
                              <p className="font-medium">{rx.patient_name}</p>
                              <p className="text-sm text-gray-500">{rx.patient_mrn}</p>
                            </TableCell>
                            <TableCell>{rx.prescriber_name}</TableCell>
                            <TableCell><Badge variant="outline">{rx.medications?.length || 0}</Badge></TableCell>
                            <TableCell><Badge className={getStatusBadge(rx.status)}>{rx.status?.replace(/_/g, ' ')}</Badge></TableCell>
                            <TableCell className="text-sm text-gray-500">{new Date(rx.created_at).toLocaleDateString()}</TableCell>
                            <TableCell className="text-right">
                              <div className="flex gap-2 justify-end">
                                <Button size="sm" variant="outline" onClick={() => { setSelectedRx(rx); setViewDialogOpen(true); }}><Eye className="w-4 h-4" /></Button>
                                {rx.status === 'pending_verification' && <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700" onClick={() => handleUpdateRxStatus(rx.id, 'approved')}><Check className="w-4 h-4" /></Button>}
                                {rx.status === 'approved' && <Button size="sm" className="bg-blue-600 hover:bg-blue-700" onClick={() => { setSelectedRx(rx); setDispenseDialogOpen(true); }}>Dispense</Button>}
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
          </Tabs>
        </TabsContent>

        {/* ==================== INVENTORY TAB ==================== */}
        <TabsContent value="inventory" className="mt-4 space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <Card>
              <CardContent className="pt-4 text-center">
                <Package className="w-8 h-8 mx-auto mb-2 text-slate-400" />
                <p className="text-sm text-slate-600">Total Items</p>
                <p className="text-2xl font-bold">{inventoryDashboard?.inventory?.total_items || 0}</p>
              </CardContent>
            </Card>
            <Card className="bg-red-50 border-red-200">
              <CardContent className="pt-4 text-center">
                <AlertCircle className="w-8 h-8 mx-auto mb-2 text-red-600" />
                <p className="text-sm text-red-700">Out of Stock</p>
                <p className="text-2xl font-bold text-red-800">{inventoryDashboard?.inventory?.out_of_stock || 0}</p>
              </CardContent>
            </Card>
            <Card className="bg-amber-50 border-amber-200">
              <CardContent className="pt-4 text-center">
                <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-amber-600" />
                <p className="text-sm text-amber-700">Low Stock</p>
                <p className="text-2xl font-bold text-amber-800">{inventoryDashboard?.inventory?.low_stock || 0}</p>
              </CardContent>
            </Card>
            <Card className="bg-orange-50 border-orange-200">
              <CardContent className="pt-4 text-center">
                <Clock className="w-8 h-8 mx-auto mb-2 text-orange-600" />
                <p className="text-sm text-orange-700">Expiring Soon</p>
                <p className="text-2xl font-bold text-orange-800">{inventoryDashboard?.alerts?.expiring_soon || 0}</p>
              </CardContent>
            </Card>
            <Card className="bg-green-50 border-green-200">
              <CardContent className="pt-4 text-center">
                <DollarSign className="w-8 h-8 mx-auto mb-2 text-green-600" />
                <p className="text-sm text-green-700">Stock Value</p>
                <p className="text-xl font-bold text-green-800">₵{inventoryDashboard?.inventory?.total_value?.toLocaleString() || '0'}</p>
              </CardContent>
            </Card>
          </div>

          <div className="flex gap-4 items-center">
            <div className="flex-1 relative max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input placeholder="Search inventory..." value={inventorySearch} onChange={(e) => setInventorySearch(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && fetchInventoryData()} className="pl-10" data-testid="inventory-search" />
            </div>
            <Button onClick={() => setAddItemOpen(true)} className="gap-2" data-testid="add-item-btn"><Plus className="w-4 h-4" /> Add Item</Button>
            {suppliers.length === 0 && <Button onClick={handleSeedSuppliers} variant="outline" className="gap-2"><Truck className="w-4 h-4" /> Load Suppliers</Button>}
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Inventory Items</CardTitle>
              <CardDescription>{inventory.length} items in catalog</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              {inventory.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <Package className="w-12 h-12 mx-auto mb-4 opacity-30" />
                  <p>No inventory items</p>
                  <Button onClick={() => setAddItemOpen(true)} className="mt-4" variant="outline">Add First Item</Button>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Drug Name</TableHead>
                      <TableHead>Code</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Stock</TableHead>
                      <TableHead>Reorder Lvl</TableHead>
                      <TableHead>Unit Cost</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {inventory.slice(0, 20).map((item) => (
                      <TableRow key={item.id}>
                        <TableCell>
                          <p className="font-medium">{item.drug_name}</p>
                          {item.manufacturer && <p className="text-xs text-gray-500">{item.manufacturer}</p>}
                        </TableCell>
                        <TableCell className="font-mono text-sm">{item.drug_code}</TableCell>
                        <TableCell>{item.category || '-'}</TableCell>
                        <TableCell className="font-semibold">{item.current_stock || 0}</TableCell>
                        <TableCell>{item.reorder_level}</TableCell>
                        <TableCell>₵{item.unit_cost?.toFixed(2) || '0.00'}</TableCell>
                        <TableCell><Badge className={getStatusBadge(item.stock_status)}>{item.stock_status?.replace('_', ' ')}</Badge></TableCell>
                        <TableCell className="text-right">
                          <Button size="sm" variant="outline" onClick={() => openReceiveStock(item)} className="gap-1" data-testid={`receive-${item.id}`}>
                            <ArrowDownCircle className="w-3 h-3" /> Receive
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ==================== NHIS CLAIMS TAB ==================== */}
        <TabsContent value="nhis" className="mt-4 space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <Card>
              <CardContent className="pt-4 text-center">
                <FileText className="w-8 h-8 mx-auto mb-2 text-slate-400" />
                <p className="text-sm text-slate-600">Total Claims</p>
                <p className="text-2xl font-bold">{nhisDashboard?.summary?.total_claims || 0}</p>
              </CardContent>
            </Card>
            <Card className="bg-blue-50 border-blue-200">
              <CardContent className="pt-4 text-center">
                <Send className="w-8 h-8 mx-auto mb-2 text-blue-600" />
                <p className="text-sm text-blue-700">Submitted</p>
                <p className="text-2xl font-bold text-blue-800">{nhisDashboard?.summary?.by_status?.submitted || 0}</p>
              </CardContent>
            </Card>
            <Card className="bg-green-50 border-green-200">
              <CardContent className="pt-4 text-center">
                <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-600" />
                <p className="text-sm text-green-700">Approved</p>
                <p className="text-2xl font-bold text-green-800">{nhisDashboard?.summary?.by_status?.approved || 0}</p>
              </CardContent>
            </Card>
            <Card className="bg-emerald-50 border-emerald-200">
              <CardContent className="pt-4 text-center">
                <DollarSign className="w-8 h-8 mx-auto mb-2 text-emerald-600" />
                <p className="text-sm text-emerald-700">Total Claimed</p>
                <p className="text-xl font-bold text-emerald-800">₵{nhisDashboard?.financials?.total_claimed?.toFixed(2) || '0.00'}</p>
              </CardContent>
            </Card>
            <Card className="bg-purple-50 border-purple-200">
              <CardContent className="pt-4 text-center">
                <TrendingUp className="w-8 h-8 mx-auto mb-2 text-purple-600" />
                <p className="text-sm text-purple-700">Total Paid</p>
                <p className="text-xl font-bold text-purple-800">₵{nhisDashboard?.financials?.total_paid?.toFixed(2) || '0.00'}</p>
              </CardContent>
            </Card>
          </div>

          <div className="flex gap-4">
            <Button onClick={() => setCreateClaimOpen(true)} className="gap-2 bg-green-600 hover:bg-green-700" data-testid="new-claim-btn"><Plus className="w-4 h-4" /> New Claim</Button>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Pharmacy Claims</CardTitle>
              <CardDescription>NHIS claim submissions</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              {nhisClaims.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <FileText className="w-12 h-12 mx-auto mb-4 opacity-30" />
                  <p>No claims found</p>
                  <Button onClick={() => setCreateClaimOpen(true)} className="mt-4" variant="outline">Create First Claim</Button>
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
                    {nhisClaims.map((claim) => (
                      <TableRow key={claim.id}>
                        <TableCell className="font-mono text-sm">{claim.claim_number}</TableCell>
                        <TableCell><p className="font-medium">{claim.patient_name}</p></TableCell>
                        <TableCell className="font-mono text-xs">{claim.membership_id}</TableCell>
                        <TableCell>{claim.claim_items?.length || 0} items</TableCell>
                        <TableCell className="font-semibold">₵{claim.total_claimed?.toFixed(2)}</TableCell>
                        <TableCell><Badge className={getStatusBadge(claim.status)}>{claim.status?.replace('_', ' ')}</Badge></TableCell>
                        <TableCell className="text-sm text-gray-500">{new Date(claim.created_at).toLocaleDateString()}</TableCell>
                        <TableCell className="text-right">
                          {claim.status === 'draft' && (
                            <Button size="sm" onClick={() => handleSubmitClaim(claim.id)} className="bg-blue-600 hover:bg-blue-700" data-testid={`submit-claim-${claim.id}`}>
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

        {/* ==================== DIRECTORY TAB ==================== */}
        <TabsContent value="directory" className="mt-4 space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className="bg-gradient-to-br from-emerald-50 to-emerald-100 border-emerald-200">
              <CardContent className="pt-4 text-center">
                <Building className="w-8 h-8 mx-auto mb-2 text-emerald-600" />
                <p className="text-sm text-emerald-700">Total Pharmacies</p>
                <p className="text-2xl font-bold text-emerald-800">{directoryStats?.total_pharmacies || 0}</p>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
              <CardContent className="pt-4 text-center">
                <MapPin className="w-8 h-8 mx-auto mb-2 text-blue-600" />
                <p className="text-sm text-blue-700">Regions Covered</p>
                <p className="text-2xl font-bold text-blue-800">{directoryStats?.regions_covered || 0}</p>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
              <CardContent className="pt-4 text-center">
                <Verified className="w-8 h-8 mx-auto mb-2 text-green-600" />
                <p className="text-sm text-green-700">NHIS Accredited</p>
                <p className="text-2xl font-bold text-green-800">{directoryStats?.nhis_accredited || 0}</p>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-amber-50 to-amber-100 border-amber-200">
              <CardContent className="pt-4 text-center">
                <Clock className="w-8 h-8 mx-auto mb-2 text-amber-600" />
                <p className="text-sm text-amber-700">24/7 Service</p>
                <p className="text-2xl font-bold text-amber-800">{directoryStats?.['24_hour_count'] || 0}</p>
              </CardContent>
            </Card>
          </div>

          <div className="flex gap-4 items-center">
            <div className="flex-1 relative max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input placeholder="Search pharmacies..." value={directorySearch} onChange={(e) => setDirectorySearch(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && fetchDirectoryData()} className="pl-10" data-testid="directory-search" />
            </div>
            <Select value={selectedRegion} onValueChange={(v) => { setSelectedRegion(v === 'all' ? '' : v); }}>
              <SelectTrigger className="w-48"><SelectValue placeholder="Filter by region" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Regions</SelectItem>
                {regions.map(r => <SelectItem key={r.id || r} value={r.name || r}>{r.name || r}</SelectItem>)}
              </SelectContent>
            </Select>
            <Button onClick={fetchDirectoryData} variant="outline">Search</Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {pharmacies.slice(0, 12).map((pharmacy) => (
              <Card key={pharmacy.id} className="hover:shadow-md transition-shadow">
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Building className="w-4 h-4 text-emerald-600" />
                    {pharmacy.name}
                  </CardTitle>
                  <CardDescription>{pharmacy.ownership_type}</CardDescription>
                </CardHeader>
                <CardContent className="text-sm space-y-1">
                  <p className="flex items-center gap-2 text-gray-600"><MapPin className="w-3 h-3" /> {pharmacy.city}, {pharmacy.region}</p>
                  {pharmacy.phone && <p className="flex items-center gap-2 text-gray-600"><Phone className="w-3 h-3" /> {pharmacy.phone}</p>}
                  <div className="flex gap-2 mt-2 flex-wrap">
                    {pharmacy.is_nhis_accredited && <Badge className="bg-green-100 text-green-700 text-xs">NHIS</Badge>}
                    {pharmacy.is_24_hours && <Badge className="bg-amber-100 text-amber-700 text-xs">24/7</Badge>}
                    {pharmacy.has_delivery && <Badge className="bg-blue-100 text-blue-700 text-xs">Delivery</Badge>}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          {pharmacies.length > 12 && <p className="text-center text-gray-500 text-sm">Showing 12 of {pharmacies.length} pharmacies</p>}
        </TabsContent>
      </Tabs>

      {/* ==================== DIALOGS ==================== */}
      
      {/* View Rx Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2"><FileText className="w-5 h-5" /> Prescription Details</DialogTitle>
            <DialogDescription>{selectedRx?.rx_number}</DialogDescription>
          </DialogHeader>
          {selectedRx && (
            <div className="space-y-4 py-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-700 mb-2">Patient</h4>
                <p className="font-medium">{selectedRx.patient_name}</p>
                <p className="text-sm text-gray-500">MRN: {selectedRx.patient_mrn}</p>
              </div>
              <div className="bg-blue-50 rounded-lg p-4">
                <h4 className="font-medium text-blue-700 mb-2">Prescriber</h4>
                <p className="font-medium">{selectedRx.prescriber_name}</p>
              </div>
              <div>
                <h4 className="font-medium text-gray-700 mb-2">Medications ({selectedRx.medications?.length || 0})</h4>
                <div className="space-y-2">
                  {selectedRx.medications?.map((med, idx) => (
                    <div key={idx} className="border rounded-lg p-3 bg-white">
                      <p className="font-medium">{med.medication_name}</p>
                      <p className="text-sm text-gray-500">{med.dosage} {med.dosage_unit} • {med.frequency} • {med.route}</p>
                      <p className="text-sm text-gray-500">Duration: {med.duration_value} {med.duration_unit} • Qty: {med.quantity}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setViewDialogOpen(false)}>Close</Button>
            {selectedRx?.status === 'pending_verification' && (
              <>
                <Button variant="destructive" onClick={() => handleUpdateRxStatus(selectedRx.id, 'cancelled')} disabled={saving}><X className="w-4 h-4 mr-2" /> Reject</Button>
                <Button className="bg-emerald-600 hover:bg-emerald-700" onClick={() => handleUpdateRxStatus(selectedRx.id, 'approved')} disabled={saving}><Check className="w-4 h-4 mr-2" /> Approve</Button>
              </>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dispense Dialog */}
      <Dialog open={dispenseDialogOpen} onOpenChange={setDispenseDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2"><Package className="w-5 h-5 text-blue-600" /> Dispense Prescription</DialogTitle>
            <DialogDescription>{selectedRx?.rx_number} - {selectedRx?.patient_name}</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Pharmacist Notes</Label>
              <Textarea value={pharmacistNotes} onChange={(e) => setPharmacistNotes(e.target.value)} placeholder="Optional notes..." />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDispenseDialogOpen(false)}>Cancel</Button>
            <Button className="bg-blue-600 hover:bg-blue-700" onClick={() => handleUpdateRxStatus(selectedRx.id, 'dispensed')} disabled={saving}>
              {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />} Dispense
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Inventory Item Dialog */}
      <Dialog open={addItemOpen} onOpenChange={setAddItemOpen}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Plus className="w-5 h-5 text-emerald-600" />
              Add Inventory Item
            </DialogTitle>
          </DialogHeader>
          <div className="overflow-y-auto flex-1 pr-2">
            <form onSubmit={handleAddInventoryItem} className="space-y-4">
              {/* Barcode Scanner Section */}
              <div className="p-4 border-2 border-dashed rounded-lg bg-gray-50">
                <div className="flex items-center justify-between mb-2">
                  <Label className="flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
                    </svg>
                    Barcode / GTIN
                  </Label>
                  <Badge className="bg-blue-100 text-blue-700">Optional</Badge>
                </div>
                <div className="flex gap-2">
                  <Input 
                    value={itemForm.barcode} 
                    onChange={(e) => setItemForm({...itemForm, barcode: e.target.value})}
                    placeholder="Scan or enter barcode/GTIN..."
                    className="flex-1"
                    data-testid="barcode-input"
                  />
                  <Button 
                    type="button" 
                    variant="outline" 
                    onClick={() => setScannerActive(true)}
                    className="gap-2"
                    data-testid="scan-barcode-btn"
                  >
                    <Camera className="w-4 h-4" />
                    Scan
                  </Button>
                </div>
                <p className="text-xs text-gray-500 mt-1">Scanning will auto-populate drug information from the FDA database</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Drug Name *</Label>
                  <Input 
                    value={itemForm.drug_name} 
                    onChange={(e) => setItemForm({...itemForm, drug_name: e.target.value})} 
                    placeholder="e.g., Paracetamol 500mg Tablets" 
                    required 
                  />
                </div>
                <div className="space-y-2">
                  <Label>Drug Code</Label>
                  <Input 
                    value={itemForm.drug_code} 
                    onChange={(e) => setItemForm({...itemForm, drug_code: e.target.value})} 
                    placeholder="Auto-generated if empty" 
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>FDA Registration #</Label>
                  <Input 
                    value={itemForm.fda_registration} 
                    onChange={(e) => setItemForm({...itemForm, fda_registration: e.target.value})} 
                    placeholder="e.g., FDA/DRD-2024-001" 
                  />
                </div>
                <div className="space-y-2">
                  <Label>Manufacturer</Label>
                  <Input 
                    value={itemForm.manufacturer} 
                    onChange={(e) => setItemForm({...itemForm, manufacturer: e.target.value})}
                    placeholder="e.g., Ernest Chemist Ltd"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Category *</Label>
                  <Select value={itemForm.category} onValueChange={(v) => setItemForm({...itemForm, category: v})}>
                    <SelectTrigger><SelectValue placeholder="Select category" /></SelectTrigger>
                    <SelectContent className="max-h-60">
                      <SelectItem value="Antimalarials">Antimalarials</SelectItem>
                      <SelectItem value="Antibiotics">Antibiotics</SelectItem>
                      <SelectItem value="Antivirals">Antivirals</SelectItem>
                      <SelectItem value="Antifungals">Antifungals</SelectItem>
                      <SelectItem value="Antiparasitics">Antiparasitics</SelectItem>
                      <SelectItem value="Analgesics & NSAIDs">Analgesics & NSAIDs</SelectItem>
                      <SelectItem value="Antipyretics">Antipyretics</SelectItem>
                      <SelectItem value="Cardiovascular">Cardiovascular</SelectItem>
                      <SelectItem value="Antihypertensives">Antihypertensives</SelectItem>
                      <SelectItem value="Antidiabetics">Antidiabetics</SelectItem>
                      <SelectItem value="Respiratory">Respiratory</SelectItem>
                      <SelectItem value="Antihistamines">Antihistamines</SelectItem>
                      <SelectItem value="Gastrointestinal">Gastrointestinal</SelectItem>
                      <SelectItem value="Antacids & PPIs">Antacids & PPIs</SelectItem>
                      <SelectItem value="Laxatives">Laxatives</SelectItem>
                      <SelectItem value="Antiemetics">Antiemetics</SelectItem>
                      <SelectItem value="CNS & Psychiatry">CNS & Psychiatry</SelectItem>
                      <SelectItem value="Sedatives & Hypnotics">Sedatives & Hypnotics</SelectItem>
                      <SelectItem value="Anticonvulsants">Anticonvulsants</SelectItem>
                      <SelectItem value="Antidepressants">Antidepressants</SelectItem>
                      <SelectItem value="Hormones & Steroids">Hormones & Steroids</SelectItem>
                      <SelectItem value="Contraceptives">Contraceptives</SelectItem>
                      <SelectItem value="Thyroid Medications">Thyroid Medications</SelectItem>
                      <SelectItem value="Vitamins & Supplements">Vitamins & Supplements</SelectItem>
                      <SelectItem value="Iron Preparations">Iron Preparations</SelectItem>
                      <SelectItem value="Dermatological">Dermatological</SelectItem>
                      <SelectItem value="Ophthalmic">Ophthalmic</SelectItem>
                      <SelectItem value="ENT Preparations">ENT Preparations</SelectItem>
                      <SelectItem value="Vaccines">Vaccines</SelectItem>
                      <SelectItem value="IV Fluids">IV Fluids & Solutions</SelectItem>
                      <SelectItem value="Surgical & Wound Care">Surgical & Wound Care</SelectItem>
                      <SelectItem value="Oncology">Oncology</SelectItem>
                      <SelectItem value="Antiretrovirals">Antiretrovirals (ARVs)</SelectItem>
                      <SelectItem value="TB Medications">TB Medications</SelectItem>
                      <SelectItem value="Herbal & Traditional">Herbal & Traditional</SelectItem>
                      <SelectItem value="OTC">OTC (Over The Counter)</SelectItem>
                      <SelectItem value="Controlled Substances">Controlled Substances</SelectItem>
                      <SelectItem value="Medical Devices">Medical Devices</SelectItem>
                      <SelectItem value="Other">Other</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Unit of Measure</Label>
                  <Select value={itemForm.unit_of_measure} onValueChange={(v) => setItemForm({...itemForm, unit_of_measure: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="tablet">Tablet</SelectItem>
                      <SelectItem value="capsule">Capsule</SelectItem>
                      <SelectItem value="bottle">Bottle</SelectItem>
                      <SelectItem value="vial">Vial</SelectItem>
                      <SelectItem value="ampule">Ampule</SelectItem>
                      <SelectItem value="tube">Tube</SelectItem>
                      <SelectItem value="sachet">Sachet</SelectItem>
                      <SelectItem value="pack">Pack</SelectItem>
                      <SelectItem value="box">Box</SelectItem>
                      <SelectItem value="strip">Strip</SelectItem>
                      <SelectItem value="ml">ml</SelectItem>
                      <SelectItem value="unit">Unit</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Unit Cost (₵)</Label>
                  <Input 
                    type="number" 
                    step="0.01"
                    min="0"
                    value={itemForm.unit_cost} 
                    onChange={(e) => setItemForm({...itemForm, unit_cost: e.target.value})}
                    placeholder="0.00"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Selling Price (₵)</Label>
                  <Input 
                    type="number" 
                    step="0.01"
                    min="0"
                    value={itemForm.selling_price} 
                    onChange={(e) => setItemForm({...itemForm, selling_price: e.target.value})}
                    placeholder="0.00"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Reorder Level</Label>
                  <Input 
                    type="number"
                    min="0"
                    value={itemForm.reorder_level} 
                    onChange={(e) => setItemForm({...itemForm, reorder_level: e.target.value})}
                    placeholder="10"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Max Stock Level</Label>
                  <Input 
                    type="number"
                    min="0"
                    value={itemForm.max_stock_level} 
                    onChange={(e) => setItemForm({...itemForm, max_stock_level: e.target.value})}
                    placeholder="1000"
                  />
                </div>
              </div>

              <DialogFooter className="pt-4 border-t">
                <Button type="button" variant="outline" onClick={() => setAddItemOpen(false)}>Cancel</Button>
                <Button type="submit" disabled={saving} className="bg-emerald-600 hover:bg-emerald-700">
                  {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                  Add Item
                </Button>
              </DialogFooter>
            </form>
          </div>
        </DialogContent>
      </Dialog>

      {/* Receive Stock Dialog */}
      <Dialog open={receiveStockOpen} onOpenChange={setReceiveStockOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Receive Stock</DialogTitle>
            <DialogDescription>{selectedItem ? `Receiving: ${selectedItem.drug_name}` : ''}</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleReceiveStock} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Quantity *</Label>
                <Input type="number" min="1" value={receiveForm.quantity} onChange={(e) => setReceiveForm({...receiveForm, quantity: parseInt(e.target.value) || 0})} required />
              </div>
              <div className="space-y-2">
                <Label>Batch Number *</Label>
                <Input value={receiveForm.batch_number} onChange={(e) => setReceiveForm({...receiveForm, batch_number: e.target.value})} placeholder="BTH-2026-001" required />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Expiry Date *</Label>
                <Input type="date" value={receiveForm.expiry_date} onChange={(e) => setReceiveForm({...receiveForm, expiry_date: e.target.value})} required />
              </div>
              <div className="space-y-2">
                <Label>Unit Cost (₵)</Label>
                <Input type="number" step="0.01" value={receiveForm.unit_cost} onChange={(e) => setReceiveForm({...receiveForm, unit_cost: parseFloat(e.target.value) || 0})} />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Supplier</Label>
              <Select value={receiveForm.supplier_name} onValueChange={(v) => setReceiveForm({...receiveForm, supplier_name: v})}>
                <SelectTrigger><SelectValue placeholder="Select supplier" /></SelectTrigger>
                <SelectContent>
                  {suppliers.map(s => <SelectItem key={s.id} value={s.name}>{s.name}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => { setReceiveStockOpen(false); setSelectedItem(null); }}>Cancel</Button>
              <Button type="submit" disabled={saving} className="bg-green-600 hover:bg-green-700">
                {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}<ArrowDownCircle className="w-4 h-4 mr-2" /> Receive
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Create NHIS Claim Dialog */}
      <Dialog open={createClaimOpen} onOpenChange={setCreateClaimOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>Create NHIS Pharmacy Claim</DialogTitle>
          </DialogHeader>
          <div className="overflow-y-auto flex-1 pr-2">
            <form onSubmit={handleCreateClaim} className="space-y-4">
              {/* Member Verification */}
              <Card>
                <CardHeader className="pb-2"><CardTitle className="text-sm">Member Verification</CardTitle></CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex gap-3 items-end">
                    <div className="flex-1 space-y-1">
                      <Label>NHIS Membership ID *</Label>
                      <Input value={membershipId} onChange={(e) => setMembershipId(e.target.value)} placeholder="NHIS-2024-001234" />
                    </div>
                    <Button type="button" onClick={handleVerifyMember} disabled={verifying}>{verifying && <Loader2 className="w-4 h-4 mr-2 animate-spin" />} Verify</Button>
                  </div>
                  {verifiedMember?.verified && (
                    <div className="p-2 bg-green-50 border border-green-200 rounded text-sm text-green-700">
                      <CheckCircle className="w-4 h-4 inline mr-1" /> Verified: {verifiedMember.full_name} - {verifiedMember.coverage_type}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Claim Details */}
              <Card>
                <CardHeader className="pb-2"><CardTitle className="text-sm">Claim Details</CardTitle></CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <Label>Patient Name</Label>
                      <Input value={claimForm.patient_name} onChange={(e) => setClaimForm({...claimForm, patient_name: e.target.value})} />
                    </div>
                    <div className="space-y-1">
                      <Label>Diagnosis Codes</Label>
                      <Input value={claimForm.diagnosis_codes} onChange={(e) => setClaimForm({...claimForm, diagnosis_codes: e.target.value})} placeholder="B50.9, J06.9" />
                    </div>
                    <div className="space-y-1">
                      <Label>Prescription Date</Label>
                      <Input type="date" value={claimForm.prescription_date} onChange={(e) => setClaimForm({...claimForm, prescription_date: e.target.value})} />
                    </div>
                    <div className="space-y-1">
                      <Label>Dispensing Date</Label>
                      <Input type="date" value={claimForm.dispensing_date} onChange={(e) => setClaimForm({...claimForm, dispensing_date: e.target.value})} />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Drug Selection */}
              <Card>
                <CardHeader className="pb-2"><CardTitle className="text-sm">Medications</CardTitle></CardHeader>
                <CardContent className="space-y-3">
                  <Input value={drugSearch} onChange={(e) => setDrugSearch(e.target.value)} placeholder="Search NHIS drug tariff..." />
                  {drugSearch && (
                    <div className="max-h-32 overflow-y-auto border rounded">
                      {filteredTariff.slice(0, 8).map(drug => (
                        <div key={drug.code} className="p-2 hover:bg-gray-50 cursor-pointer flex justify-between items-center border-b last:border-b-0" onClick={() => handleAddDrugToClaim(drug)}>
                          <div><p className="text-sm font-medium">{drug.name}</p><p className="text-xs text-gray-500">{drug.code}</p></div>
                          <p className="text-sm font-semibold text-green-600">₵{drug.nhis_price?.toFixed(2)}</p>
                        </div>
                      ))}
                    </div>
                  )}
                  {claimItems.length > 0 && (
                    <Table>
                      <TableHeader>
                        <TableRow><TableHead>Drug</TableHead><TableHead>Qty</TableHead><TableHead>Price</TableHead><TableHead>Total</TableHead><TableHead></TableHead></TableRow>
                      </TableHeader>
                      <TableBody>
                        {claimItems.map(item => (
                          <TableRow key={item.item_code}>
                            <TableCell className="text-sm">{item.item_name}</TableCell>
                            <TableCell>
                              <Input type="number" min="1" value={item.quantity} onChange={(e) => {
                                const qty = parseInt(e.target.value) || 1;
                                setClaimItems(prev => prev.map(i => i.item_code === item.item_code ? {...i, quantity: qty, total_price: qty * i.unit_price} : i));
                              }} className="w-16" />
                            </TableCell>
                            <TableCell>₵{item.unit_price.toFixed(2)}</TableCell>
                            <TableCell className="font-semibold">₵{(item.quantity * item.unit_price).toFixed(2)}</TableCell>
                            <TableCell><Button type="button" size="sm" variant="ghost" onClick={() => setClaimItems(prev => prev.filter(i => i.item_code !== item.item_code))} className="text-red-500"><X className="w-4 h-4" /></Button></TableCell>
                          </TableRow>
                        ))}
                        <TableRow className="bg-gray-50">
                          <TableCell colSpan={3} className="text-right font-semibold">Total:</TableCell>
                          <TableCell colSpan={2} className="font-bold text-green-600">₵{claimTotal.toFixed(2)}</TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>

              <DialogFooter className="sticky bottom-0 bg-white pt-3 border-t">
                <Button type="button" variant="outline" onClick={() => { setCreateClaimOpen(false); setClaimItems([]); setVerifiedMember(null); setMembershipId(''); }}>Cancel</Button>
                <Button type="submit" disabled={saving || !verifiedMember?.verified || claimItems.length === 0} className="bg-green-600 hover:bg-green-700">
                  {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />} Create Claim (₵{claimTotal.toFixed(2)})
                </Button>
              </DialogFooter>
            </form>
          </div>
        </DialogContent>
      </Dialog>

      {/* Barcode Scanner Dialog */}
      <Dialog open={scannerActive} onOpenChange={setScannerActive}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Camera className="w-5 h-5 text-blue-600" />
              Scan Barcode
            </DialogTitle>
            <DialogDescription>
              Point your camera at the medication barcode
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            {scannerActive && (
              <BarcodeScanner onDetected={handleBarcodeDetected} />
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setScannerActive(false)}>
              <XCircle className="w-4 h-4 mr-2" /> Cancel
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// Barcode Scanner Component using react-zxing
function BarcodeScanner({ onDetected }) {
  const { ref } = useZxing({
    onDecodeResult(result) {
      onDetected(result.getText());
    },
    onError(error) {
      // Silently ignore continuous scanning errors
      console.debug('Scanner:', error);
    },
  });

  return (
    <div className="relative">
      <video 
        ref={ref} 
        className="w-full h-64 rounded-lg bg-black object-cover"
      />
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="w-48 h-32 border-2 border-blue-500 rounded-lg animate-pulse" />
      </div>
      <p className="text-center text-sm text-gray-500 mt-2">
        Position the barcode within the frame
      </p>
    </div>
  );
}
