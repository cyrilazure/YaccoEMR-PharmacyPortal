import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Table, TableBody, TableCell,
  TableHead, TableHeader, TableRow
} from '@/components/ui/table';
import {
  Dialog, DialogContent, DialogDescription,
  DialogHeader, DialogTitle, DialogFooter
} from '@/components/ui/dialog';
import {
  Select, SelectContent, SelectItem,
  SelectTrigger, SelectValue
} from '@/components/ui/select';
import { toast } from 'sonner';
import {
  Pill, Package, ShoppingCart, FileText, Users, Settings,
  LogOut, BarChart3, AlertTriangle, Clock, Search, Plus,
  RefreshCw, Loader2, CheckCircle, XCircle, DollarSign,
  TrendingUp, Bell, Truck, Shield, Calendar, ArrowRight,
  Download, Edit, Trash2, Eye, Database, Hash
} from 'lucide-react';
import api from '@/lib/api';

const API_BASE = process.env.REACT_APP_BACKEND_URL || '';

// Pharmacy Portal API with auth header
const getAuthHeader = () => {
  const token = localStorage.getItem('pharmacy_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const pharmacyDashAPI = {
  getDashboard: () => api.get('/pharmacy-portal/dashboard', { headers: getAuthHeader() }),
  getDrugs: (params) => api.get('/pharmacy-portal/drugs', { params, headers: getAuthHeader() }),
  addDrug: (data) => api.post('/pharmacy-portal/drugs', data, { headers: getAuthHeader() }),
  updateDrug: (id, data) => api.put(`/pharmacy-portal/drugs/${id}`, data, { headers: getAuthHeader() }),
  seedDrugs: (categories) => api.post('/pharmacy-portal/drugs/seed', { categories }, { headers: getAuthHeader() }),
  getInventory: (params) => api.get('/pharmacy-portal/inventory', { params, headers: getAuthHeader() }),
  receiveInventory: (data) => api.post('/pharmacy-portal/inventory/receive', data, { headers: getAuthHeader() }),
  getInventoryAlerts: () => api.get('/pharmacy-portal/inventory/alerts', { headers: getAuthHeader() }),
  getSales: (params) => api.get('/pharmacy-portal/sales', { params, headers: getAuthHeader() }),
  createSale: (data) => api.post('/pharmacy-portal/sales', data, { headers: getAuthHeader() }),
  getPrescriptions: (params) => api.get('/pharmacy-portal/prescriptions/incoming', { params, headers: getAuthHeader() }),
  acceptPrescription: (id) => api.put(`/pharmacy-portal/prescriptions/${id}/accept`, {}, { headers: getAuthHeader() }),
  dispensePrescription: (id) => api.put(`/pharmacy-portal/prescriptions/${id}/dispense`, {}, { headers: getAuthHeader() }),
  getInsuranceClaims: (params) => api.get('/pharmacy-portal/insurance/claims', { params, headers: getAuthHeader() }),
  submitInsuranceClaim: (data) => api.post('/pharmacy-portal/insurance/claims', data, { headers: getAuthHeader() }),
  getReorderSuggestions: () => api.get('/pharmacy-portal/reorder/suggestions', { headers: getAuthHeader() }),
  getStaff: () => api.get('/pharmacy-portal/admin/staff', { headers: getAuthHeader() }),
  createStaff: (data) => api.post('/pharmacy-portal/admin/staff', data, { headers: getAuthHeader() }),
  getAuditLogs: (params) => api.get('/pharmacy-portal/audit-logs', { params, headers: getAuthHeader() }),
  getAuditLogsSummary: (days) => api.get('/pharmacy-portal/audit-logs/summary', { params: { days }, headers: getAuthHeader() }),
  getCurrentUser: () => api.get('/pharmacy-portal/auth/me', { headers: getAuthHeader() }),
  searchMedications: (query, category) => api.get('/pharmacy-portal/medications/search', { params: { query, category }, headers: getAuthHeader() }),
  getMedicationCategories: () => api.get('/pharmacy-portal/medications/categories', { headers: getAuthHeader() }),
  getDepartments: () => api.get('/pharmacy-portal/admin/departments', { headers: getAuthHeader() }),
  getRoles: () => api.get('/pharmacy-portal/admin/roles', { headers: getAuthHeader() }),
  // Phase 3: E-Prescriptions from Hospital
  getEPrescriptions: (params) => api.get('/pharmacy-portal/prescriptions/incoming', { params, headers: getAuthHeader() }),
  acceptEPrescription: (id) => api.put(`/pharmacy-portal/eprescription/${id}/accept`, {}, { headers: getAuthHeader() }),
  markEPrescriptionReady: (id) => api.put(`/pharmacy-portal/eprescription/${id}/ready`, {}, { headers: getAuthHeader() }),
  dispenseEPrescription: (id, notes) => api.put(`/pharmacy-portal/eprescription/${id}/dispense`, { dispensing_notes: notes }, { headers: getAuthHeader() }),
  // Phase 3: Supply Requests
  getOutgoingSupplyRequests: (status) => api.get('/pharmacy-portal/supply-requests/outgoing', { params: { status }, headers: getAuthHeader() }),
  getIncomingSupplyRequests: (status) => api.get('/pharmacy-portal/supply-requests/incoming', { params: { status }, headers: getAuthHeader() }),
  createSupplyRequest: (data) => api.post('/pharmacy-portal/supply-requests/create', data, { headers: getAuthHeader() }),
  respondToSupplyRequest: (id, response, notes, items) => api.put(`/pharmacy-portal/supply-requests/${id}/respond`, { response, response_notes: notes, available_items: items }, { headers: getAuthHeader() }),
  fulfillSupplyRequest: (id, method, notes) => api.put(`/pharmacy-portal/supply-requests/${id}/fulfill`, { delivery_method: method, delivery_notes: notes }, { headers: getAuthHeader() }),
  // Phase 3: Network Directory
  getPharmacyNetwork: (params) => api.get('/pharmacy-portal/network/pharmacies', { params, headers: getAuthHeader() }),
};

// Dashboard Stats Card
function StatCard({ title, value, icon: Icon, color, subtext }) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-500">{title}</p>
            <p className={`text-3xl font-bold ${color}`}>{value}</p>
            {subtext && <p className="text-xs text-slate-400 mt-1">{subtext}</p>}
          </div>
          <div className={`p-3 rounded-xl ${color.replace('text-', 'bg-').replace('-600', '-100')}`}>
            <Icon className={`w-6 h-6 ${color}`} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Add Drug Dialog Component
function AddDrugDialog({ open, onOpenChange, onSuccess }) {
  const [formData, setFormData] = useState({
    generic_name: '',
    brand_name: '',
    manufacturer: '',
    strength: '',
    dosage_form: 'tablet',
    category: 'pharmacy_only',
    unit_price: '',
    pack_size: '1',
    reorder_level: '10',
    description: ''
  });
  const [loading, setLoading] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);

  const dosageForms = [
    'tablet', 'capsule', 'syrup', 'suspension', 'injection', 'cream',
    'ointment', 'gel', 'drops', 'inhaler', 'suppository', 'patch', 'powder', 'solution', 'spray', 'lotion'
  ];

  const categories = [
    { value: 'prescription_only', label: 'Prescription Only (POM)' },
    { value: 'over_the_counter', label: 'Over the Counter (OTC)' },
    { value: 'controlled_substance', label: 'Controlled Drug (CD)' },
    { value: 'pharmacy_only', label: 'Pharmacy Only (P)' },
    { value: 'general_sale', label: 'General Sale (GSL)' }
  ];

  const searchGlobalDatabase = async (query) => {
    if (!query || query.length < 2) {
      setSearchResults([]);
      return;
    }
    setSearching(true);
    try {
      const response = await pharmacyDashAPI.searchMedications(query);
      setSearchResults(response.data.medications || []);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setSearching(false);
    }
  };

  const selectMedication = (med) => {
    setFormData({
      ...formData,
      generic_name: med.generic_name,
      brand_name: med.brand_names?.[0] || '',
      strength: med.strengths?.[0] || '',
      dosage_form: med.dosage_forms?.[0] || 'tablet'
    });
    setSearchResults([]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.generic_name || !formData.unit_price) {
      toast.error('Please fill required fields');
      return;
    }
    setLoading(true);
    try {
      await pharmacyDashAPI.addDrug({
        ...formData,
        unit_price: parseFloat(formData.unit_price),
        pack_size: parseInt(formData.pack_size),
        reorder_level: parseInt(formData.reorder_level)
      });
      toast.success('Drug added to catalog');
      onSuccess();
      onOpenChange(false);
      setFormData({
        generic_name: '', brand_name: '', manufacturer: '', strength: '',
        dosage_form: 'tablet', category: 'pharmacy_only', unit_price: '',
        pack_size: '1', reorder_level: '10', description: ''
      });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add drug');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Pill className="w-5 h-5 text-blue-600" />
            Add Drug to Catalog
          </DialogTitle>
          <DialogDescription>
            Search the global database or enter drug details manually
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Search Global Database */}
          <div className="space-y-2">
            <Label>Search Global Database</Label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="Type drug name to search..."
                className="pl-10"
                onChange={(e) => searchGlobalDatabase(e.target.value)}
              />
              {searching && (
                <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin text-slate-400" />
              )}
            </div>
            {searchResults.length > 0 && (
              <div className="border rounded-lg max-h-40 overflow-y-auto">
                {searchResults.map((med, idx) => (
                  <div
                    key={idx}
                    className="p-2 hover:bg-slate-50 cursor-pointer border-b last:border-b-0"
                    onClick={() => selectMedication(med)}
                  >
                    <p className="font-medium text-sm">{med.generic_name}</p>
                    <p className="text-xs text-slate-500">
                      {med.brand_names?.slice(0, 3).join(', ')} • {med.dosage_forms?.join(', ')}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Generic Name *</Label>
              <Input
                value={formData.generic_name}
                onChange={(e) => setFormData({ ...formData, generic_name: e.target.value })}
                placeholder="e.g., Paracetamol"
                required
              />
            </div>
            <div className="space-y-2">
              <Label>Brand Name</Label>
              <Input
                value={formData.brand_name}
                onChange={(e) => setFormData({ ...formData, brand_name: e.target.value })}
                placeholder="e.g., Panadol"
              />
            </div>
            <div className="space-y-2">
              <Label>Manufacturer</Label>
              <Input
                value={formData.manufacturer}
                onChange={(e) => setFormData({ ...formData, manufacturer: e.target.value })}
                placeholder="e.g., GSK"
              />
            </div>
            <div className="space-y-2">
              <Label>Strength</Label>
              <Input
                value={formData.strength}
                onChange={(e) => setFormData({ ...formData, strength: e.target.value })}
                placeholder="e.g., 500mg"
              />
            </div>
            <div className="space-y-2">
              <Label>Dosage Form</Label>
              <Select value={formData.dosage_form} onValueChange={(v) => setFormData({ ...formData, dosage_form: v })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {dosageForms.map((form) => (
                    <SelectItem key={form} value={form}>{form.charAt(0).toUpperCase() + form.slice(1)}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Category</Label>
              <Select value={formData.category} onValueChange={(v) => setFormData({ ...formData, category: v })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {categories.map((cat) => (
                    <SelectItem key={cat.value} value={cat.value}>{cat.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Unit Price (₵) *</Label>
              <Input
                type="number"
                step="0.01"
                value={formData.unit_price}
                onChange={(e) => setFormData({ ...formData, unit_price: e.target.value })}
                placeholder="0.00"
                required
              />
            </div>
            <div className="space-y-2">
              <Label>Pack Size</Label>
              <Input
                type="number"
                value={formData.pack_size}
                onChange={(e) => setFormData({ ...formData, pack_size: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label>Reorder Level</Label>
              <Input
                type="number"
                value={formData.reorder_level}
                onChange={(e) => setFormData({ ...formData, reorder_level: e.target.value })}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" type="button" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={loading}>
              {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Plus className="w-4 h-4 mr-2" />}
              Add Drug
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// Receive Stock Dialog Component
function ReceiveStockDialog({ open, onOpenChange, drugs, onSuccess }) {
  const [formData, setFormData] = useState({
    drug_id: '',
    batch_number: '',
    quantity: '',
    cost_price: '',
    selling_price: '',
    expiry_date: '',
    supplier: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.drug_id || !formData.batch_number || !formData.quantity) {
      toast.error('Please fill required fields');
      return;
    }
    setLoading(true);
    try {
      await pharmacyDashAPI.receiveInventory({
        ...formData,
        quantity: parseInt(formData.quantity),
        cost_price: parseFloat(formData.cost_price || 0),
        selling_price: parseFloat(formData.selling_price || 0)
      });
      toast.success('Stock received successfully');
      onSuccess();
      onOpenChange(false);
      setFormData({
        drug_id: '', batch_number: '', quantity: '',
        cost_price: '', selling_price: '', expiry_date: '', supplier: ''
      });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to receive stock');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Package className="w-5 h-5 text-green-600" />
            Receive Stock
          </DialogTitle>
          <DialogDescription>
            Record incoming inventory from supplier
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label>Drug *</Label>
            <Select value={formData.drug_id} onValueChange={(v) => setFormData({ ...formData, drug_id: v })}>
              <SelectTrigger>
                <SelectValue placeholder="Select drug" />
              </SelectTrigger>
              <SelectContent>
                {drugs.map((drug) => (
                  <SelectItem key={drug.id} value={drug.id}>
                    {drug.generic_name} {drug.strength && `(${drug.strength})`}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Batch Number *</Label>
              <Input
                value={formData.batch_number}
                onChange={(e) => setFormData({ ...formData, batch_number: e.target.value })}
                placeholder="e.g., BTH-2024-001"
                required
              />
            </div>
            <div className="space-y-2">
              <Label>Quantity *</Label>
              <Input
                type="number"
                value={formData.quantity}
                onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                placeholder="0"
                required
              />
            </div>
            <div className="space-y-2">
              <Label>Cost Price (₵)</Label>
              <Input
                type="number"
                step="0.01"
                value={formData.cost_price}
                onChange={(e) => setFormData({ ...formData, cost_price: e.target.value })}
                placeholder="0.00"
              />
            </div>
            <div className="space-y-2">
              <Label>Selling Price (₵)</Label>
              <Input
                type="number"
                step="0.01"
                value={formData.selling_price}
                onChange={(e) => setFormData({ ...formData, selling_price: e.target.value })}
                placeholder="0.00"
              />
            </div>
            <div className="space-y-2">
              <Label>Expiry Date *</Label>
              <Input
                type="date"
                value={formData.expiry_date}
                onChange={(e) => setFormData({ ...formData, expiry_date: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label>Supplier</Label>
              <Input
                value={formData.supplier}
                onChange={(e) => setFormData({ ...formData, supplier: e.target.value })}
                placeholder="e.g., Tobinco Pharma"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" type="button" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={loading} className="bg-green-600 hover:bg-green-700">
              {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <CheckCircle className="w-4 h-4 mr-2" />}
              Receive Stock
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// Add Staff Dialog Component
function AddStaffDialog({ open, onOpenChange, onSuccess }) {
  const [formData, setFormData] = useState({
    email: '',
    first_name: '',
    last_name: '',
    phone: '',
    role: 'pharmacist',
    department: 'dispensary',
    license_number: ''
  });
  const [loading, setLoading] = useState(false);

  const roles = [
    { value: 'superintendent_pharmacist', label: 'Superintendent Pharmacist' },
    { value: 'pharmacist', label: 'Pharmacist' },
    { value: 'pharmacy_technician', label: 'Pharmacy Technician' },
    { value: 'pharmacy_assistant', label: 'Pharmacy Assistant' },
    { value: 'cashier', label: 'Cashier' },
    { value: 'inventory_manager', label: 'Inventory Manager' },
    { value: 'delivery_staff', label: 'Delivery Staff' }
  ];

  const departments = [
    { value: 'dispensary', label: 'Dispensary' },
    { value: 'inventory', label: 'Inventory' },
    { value: 'procurement', label: 'Procurement' },
    { value: 'sales', label: 'Sales' },
    { value: 'delivery', label: 'Delivery' },
    { value: 'administration', label: 'Administration' },
    { value: 'compounding', label: 'Compounding' },
    { value: 'clinical_services', label: 'Clinical Services' }
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.email || !formData.first_name || !formData.last_name || !formData.phone) {
      toast.error('Please fill all required fields');
      return;
    }
    setLoading(true);
    try {
      const response = await pharmacyDashAPI.createStaff(formData);
      toast.success(`Staff created. Temporary password: ${response.data.default_password}`);
      onSuccess();
      onOpenChange(false);
      setFormData({
        email: '', first_name: '', last_name: '', phone: '',
        role: 'pharmacist', department: 'dispensary', license_number: ''
      });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create staff');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Users className="w-5 h-5 text-purple-600" />
            Add Staff Member
          </DialogTitle>
          <DialogDescription>
            Create a new staff account for your pharmacy
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>First Name *</Label>
              <Input
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label>Last Name *</Label>
              <Input
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label>Email *</Label>
              <Input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
              />
            </div>
            <div className="space-y-2">
              <Label>Phone *</Label>
              <Input
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                placeholder="+233 XX XXX XXXX"
                required
              />
            </div>
            <div className="space-y-2">
              <Label>Role *</Label>
              <Select value={formData.role} onValueChange={(v) => setFormData({ ...formData, role: v })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {roles.map((role) => (
                    <SelectItem key={role.value} value={role.value}>{role.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Department</Label>
              <Select value={formData.department} onValueChange={(v) => setFormData({ ...formData, department: v })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {departments.map((dept) => (
                    <SelectItem key={dept.value} value={dept.value}>{dept.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {(formData.role === 'pharmacist' || formData.role === 'superintendent_pharmacist') && (
            <div className="space-y-2">
              <Label>License Number (PSGH)</Label>
              <Input
                value={formData.license_number}
                onChange={(e) => setFormData({ ...formData, license_number: e.target.value })}
                placeholder="PSGH/XXXXX"
              />
            </div>
          )}

          <div className="bg-blue-50 p-3 rounded-lg text-sm text-blue-700">
            <p>The staff member will receive a temporary password based on their phone number (last 8 digits).</p>
          </div>

          <DialogFooter>
            <Button variant="outline" type="button" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button type="submit" disabled={loading} className="bg-purple-600 hover:bg-purple-700">
              {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Plus className="w-4 h-4 mr-2" />}
              Create Staff
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// Seed Drugs Dialog Component
function SeedDrugsDialog({ open, onOpenChange, onSuccess }) {
  const [loading, setLoading] = useState(false);
  const [selectedCategories, setSelectedCategories] = useState([]);

  const categoryGroups = [
    { name: 'Pain & Fever', categories: ['analgesic', 'nsaid', 'opioid_analgesic'] },
    { name: 'Antibiotics', categories: ['antibiotic_penicillin', 'antibiotic_cephalosporin', 'antibiotic_macrolide', 'antibiotic_fluoroquinolone', 'antibiotic_aminoglycoside'] },
    { name: 'Antimalarials', categories: ['antimalarial'] },
    { name: 'Cardiovascular', categories: ['antihypertensive_acei', 'antihypertensive_arb', 'antihypertensive_beta_blocker', 'antihypertensive_ccb', 'cardiovascular_statin'] },
    { name: 'Diabetes', categories: ['antidiabetic_biguanide', 'antidiabetic_sulfonylurea', 'antidiabetic_insulin'] },
    { name: 'GI & Antiemetics', categories: ['gastrointestinal_ppi', 'gastrointestinal_antiemetic', 'gastrointestinal_antidiarrheal'] },
    { name: 'Respiratory', categories: ['respiratory_bronchodilator', 'respiratory_corticosteroid', 'antihistamine'] },
    { name: 'Vitamins & Supplements', categories: ['vitamin', 'mineral'] }
  ];

  const toggleCategory = (cat) => {
    if (selectedCategories.includes(cat)) {
      setSelectedCategories(selectedCategories.filter(c => c !== cat));
    } else {
      setSelectedCategories([...selectedCategories, cat]);
    }
  };

  const selectAll = () => {
    const allCats = categoryGroups.flatMap(g => g.categories);
    setSelectedCategories(allCats);
  };

  const handleSeed = async () => {
    setLoading(true);
    try {
      const response = await pharmacyDashAPI.seedDrugs(selectedCategories.length > 0 ? selectedCategories : null);
      toast.success(`Added ${response.data.added} drugs to catalog (${response.data.skipped} already existed)`);
      onSuccess();
      onOpenChange(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to seed drugs');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Database className="w-5 h-5 text-indigo-600" />
            Import from Global Drug Database
          </DialogTitle>
          <DialogDescription>
            Quickly populate your catalog with 200+ common medications from Ghana and worldwide
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-600">Select categories to import:</p>
            <Button variant="outline" size="sm" onClick={selectAll}>
              Select All
            </Button>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {categoryGroups.map((group) => (
              <Card key={group.name} className="cursor-pointer" onClick={() => {
                const allSelected = group.categories.every(c => selectedCategories.includes(c));
                if (allSelected) {
                  setSelectedCategories(selectedCategories.filter(c => !group.categories.includes(c)));
                } else {
                  setSelectedCategories([...new Set([...selectedCategories, ...group.categories])]);
                }
              }}>
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{group.name}</span>
                    <Badge className={
                      group.categories.every(c => selectedCategories.includes(c))
                        ? 'bg-green-100 text-green-700'
                        : 'bg-slate-100 text-slate-500'
                    }>
                      {group.categories.length} types
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="bg-amber-50 p-3 rounded-lg text-sm text-amber-700">
            <AlertTriangle className="w-4 h-4 inline mr-2" />
            Drugs will be added with ₵0.00 price. You'll need to set prices manually after import.
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleSeed} disabled={loading} className="bg-indigo-600 hover:bg-indigo-700">
            {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Download className="w-4 h-4 mr-2" />}
            Import {selectedCategories.length > 0 ? 'Selected' : 'All'} Drugs
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// New Sale Dialog
function NewSaleDialog({ open, onOpenChange, drugs, onSuccess }) {
  const [items, setItems] = useState([{ drug_id: '', quantity: 1, unit_price: 0, discount: 0 }]);
  const [saleType, setSaleType] = useState('retail');
  const [customerName, setCustomerName] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [loading, setLoading] = useState(false);

  const addItem = () => {
    setItems([...items, { drug_id: '', quantity: 1, unit_price: 0, discount: 0 }]);
  };

  const updateItem = (index, field, value) => {
    const newItems = [...items];
    newItems[index][field] = value;
    
    if (field === 'drug_id') {
      const drug = drugs.find(d => d.id === value);
      if (drug) {
        newItems[index].unit_price = drug.unit_price || 0;
      }
    }
    
    setItems(newItems);
  };

  const removeItem = (index) => {
    if (items.length > 1) {
      setItems(items.filter((_, i) => i !== index));
    }
  };

  const calculateTotal = () => {
    return items.reduce((total, item) => {
      return total + (item.quantity * item.unit_price) - (item.discount || 0);
    }, 0);
  };

  const handleSubmit = async () => {
    const validItems = items.filter(item => item.drug_id && item.quantity > 0);
    if (validItems.length === 0) {
      toast.error('Please add at least one item');
      return;
    }

    setLoading(true);
    try {
      await pharmacyDashAPI.createSale({
        items: validItems,
        sale_type: saleType,
        customer_name: customerName,
        customer_phone: customerPhone,
        payment_method: paymentMethod
      });
      toast.success('Sale completed successfully');
      onSuccess();
      onOpenChange(false);
      setItems([{ drug_id: '', quantity: 1, unit_price: 0, discount: 0 }]);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create sale');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ShoppingCart className="w-5 h-5 text-green-600" />
            New Sale / Dispensing
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Sale Type</Label>
              <Select value={saleType} onValueChange={setSaleType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="retail">Retail (Individual)</SelectItem>
                  <SelectItem value="wholesale">Wholesale</SelectItem>
                  <SelectItem value="hospital">Hospital Supply</SelectItem>
                  <SelectItem value="nhis">NHIS Covered</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Payment Method</Label>
              <Select value={paymentMethod} onValueChange={setPaymentMethod}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="cash">Cash</SelectItem>
                  <SelectItem value="mobile_money">Mobile Money</SelectItem>
                  <SelectItem value="card">Card</SelectItem>
                  <SelectItem value="credit">Credit</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Customer Name</Label>
              <Input
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                placeholder="Optional"
              />
            </div>
            <div className="space-y-2">
              <Label>Customer Phone</Label>
              <Input
                value={customerPhone}
                onChange={(e) => setCustomerPhone(e.target.value)}
                placeholder="Optional"
              />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Items</Label>
              <Button type="button" size="sm" variant="outline" onClick={addItem}>
                <Plus className="w-4 h-4 mr-1" /> Add Item
              </Button>
            </div>
            
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Drug</TableHead>
                  <TableHead className="w-24">Qty</TableHead>
                  <TableHead className="w-32">Unit Price</TableHead>
                  <TableHead className="w-24">Discount</TableHead>
                  <TableHead className="w-20"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((item, index) => (
                  <TableRow key={index}>
                    <TableCell>
                      <Select
                        value={item.drug_id}
                        onValueChange={(v) => updateItem(index, 'drug_id', v)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select drug" />
                        </SelectTrigger>
                        <SelectContent>
                          {drugs.filter(d => d.current_stock > 0).map((drug) => (
                            <SelectItem key={drug.id} value={drug.id}>
                              {drug.generic_name} ({drug.current_stock} in stock)
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </TableCell>
                    <TableCell>
                      <Input
                        type="number"
                        min="1"
                        value={item.quantity}
                        onChange={(e) => updateItem(index, 'quantity', parseInt(e.target.value) || 1)}
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        type="number"
                        step="0.01"
                        value={item.unit_price}
                        onChange={(e) => updateItem(index, 'unit_price', parseFloat(e.target.value) || 0)}
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        type="number"
                        step="0.01"
                        value={item.discount}
                        onChange={(e) => updateItem(index, 'discount', parseFloat(e.target.value) || 0)}
                      />
                    </TableCell>
                    <TableCell>
                      <Button
                        type="button"
                        size="sm"
                        variant="ghost"
                        onClick={() => removeItem(index)}
                        disabled={items.length === 1}
                      >
                        <XCircle className="w-4 h-4 text-red-500" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
            <span className="font-semibold">Total:</span>
            <span className="text-2xl font-bold text-green-600">
              ₵{calculateTotal().toFixed(2)}
            </span>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={loading} className="bg-green-600 hover:bg-green-700">
            {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <CheckCircle className="w-4 h-4 mr-2" />}
            Complete Sale
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Main Pharmacy Dashboard Component
export default function PharmacyDashboard() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);
  const [pharmacy, setPharmacy] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [drugs, setDrugs] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [alerts, setAlerts] = useState(null);
  const [sales, setSales] = useState([]);
  const [prescriptions, setPrescriptions] = useState([]);
  const [reorderSuggestions, setReorderSuggestions] = useState([]);
  const [staff, setStaff] = useState([]);
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Dialog states
  const [showNewSale, setShowNewSale] = useState(false);
  const [showAddDrug, setShowAddDrug] = useState(false);
  const [showReceiveStock, setShowReceiveStock] = useState(false);
  const [showAddStaff, setShowAddStaff] = useState(false);
  const [showSeedDrugs, setShowSeedDrugs] = useState(false);
  const [drugSearch, setDrugSearch] = useState('');

  // Check auth on mount
  useEffect(() => {
    const token = localStorage.getItem('pharmacy_token');
    const savedUser = localStorage.getItem('pharmacy_user');
    const savedPharmacy = localStorage.getItem('pharmacy_info');

    if (!token) {
      navigate('/pharmacy');
      return;
    }

    if (savedUser) setUser(JSON.parse(savedUser));
    if (savedPharmacy) setPharmacy(JSON.parse(savedPharmacy));
  }, [navigate]);

  // Fetch dashboard data
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [dashRes, drugsRes, alertsRes, prescriptionsRes] = await Promise.all([
        pharmacyDashAPI.getDashboard(),
        pharmacyDashAPI.getDrugs({}),
        pharmacyDashAPI.getInventoryAlerts(),
        pharmacyDashAPI.getPrescriptions({})
      ]);

      setDashboard(dashRes.data);
      setDrugs(drugsRes.data.drugs || []);
      setAlerts(alertsRes.data);
      setPrescriptions(prescriptionsRes.data.prescriptions || []);
    } catch (error) {
      if (error.response?.status === 401) {
        toast.error('Session expired. Please login again.');
        localStorage.removeItem('pharmacy_token');
        navigate('/pharmacy');
      }
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    if (user) {
      fetchData();
    }
  }, [user, fetchData]);

  // Fetch additional data based on tab
  useEffect(() => {
    const fetchTabData = async () => {
      try {
        if (activeTab === 'inventory') {
          const [invRes, reorderRes] = await Promise.all([
            pharmacyDashAPI.getInventory({}),
            pharmacyDashAPI.getReorderSuggestions()
          ]);
          setInventory(invRes.data.inventory || []);
          setReorderSuggestions(reorderRes.data.suggestions || []);
        } else if (activeTab === 'sales') {
          const salesRes = await pharmacyDashAPI.getSales({ limit: 50 });
          setSales(salesRes.data.sales || []);
        } else if (activeTab === 'staff') {
          const staffRes = await pharmacyDashAPI.getStaff();
          setStaff(staffRes.data.staff || []);
        }
      } catch (error) {
        console.error('Failed to fetch tab data:', error);
      }
    };

    if (user) {
      fetchTabData();
    }
  }, [activeTab, user]);

  // Handle logout
  const handleLogout = () => {
    localStorage.removeItem('pharmacy_token');
    localStorage.removeItem('pharmacy_user');
    localStorage.removeItem('pharmacy_info');
    toast.success('Logged out successfully');
    navigate('/pharmacy');
  };

  // Filter drugs by search
  const filteredDrugs = drugs.filter(drug => 
    drugSearch === '' || 
    drug.generic_name?.toLowerCase().includes(drugSearch.toLowerCase()) ||
    drug.brand_name?.toLowerCase().includes(drugSearch.toLowerCase())
  );

  if (loading && !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50" data-testid="pharmacy-dashboard">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center">
                <Pill className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-800">{pharmacy?.name || 'Pharmacy Portal'}</h1>
                <p className="text-xs text-slate-500">
                  {user?.first_name} {user?.last_name} • {user?.role?.replace(/_/g, ' ')}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="outline" size="sm" onClick={fetchData}>
                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button variant="outline" size="sm" onClick={handleLogout}>
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid grid-cols-6 w-full max-w-3xl mb-6">
            <TabsTrigger value="dashboard" className="gap-2">
              <BarChart3 className="w-4 h-4" /> Dashboard
            </TabsTrigger>
            <TabsTrigger value="drugs" className="gap-2">
              <Pill className="w-4 h-4" /> Drugs
            </TabsTrigger>
            <TabsTrigger value="inventory" className="gap-2">
              <Package className="w-4 h-4" /> Inventory
            </TabsTrigger>
            <TabsTrigger value="sales" className="gap-2">
              <ShoppingCart className="w-4 h-4" /> Sales
            </TabsTrigger>
            <TabsTrigger value="prescriptions" className="gap-2">
              <FileText className="w-4 h-4" /> Rx
            </TabsTrigger>
            <TabsTrigger value="staff" className="gap-2">
              <Users className="w-4 h-4" /> Staff
            </TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard">
            <div className="space-y-6">
              {/* Stats Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard
                  title="Today's Sales"
                  value={dashboard?.today_sales_count || 0}
                  icon={ShoppingCart}
                  color="text-green-600"
                  subtext={`₵${(dashboard?.today_revenue || 0).toFixed(2)} revenue`}
                />
                <StatCard
                  title="Pending Rx"
                  value={dashboard?.pending_prescriptions || 0}
                  icon={FileText}
                  color="text-blue-600"
                />
                <StatCard
                  title="Low Stock"
                  value={dashboard?.low_stock_count || 0}
                  icon={AlertTriangle}
                  color="text-orange-600"
                />
                <StatCard
                  title="Total Drugs"
                  value={dashboard?.total_drugs || 0}
                  icon={Pill}
                  color="text-purple-600"
                />
              </div>

              {/* Quick Actions */}
              <Card>
                <CardHeader>
                  <CardTitle>Quick Actions</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <Button onClick={() => setShowNewSale(true)} className="h-20 flex-col gap-2 bg-green-600 hover:bg-green-700">
                      <ShoppingCart className="w-6 h-6" />
                      New Sale
                    </Button>
                    <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => setActiveTab('prescriptions')}>
                      <FileText className="w-6 h-6" />
                      View Prescriptions
                    </Button>
                    <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => setShowReceiveStock(true)}>
                      <Package className="w-6 h-6" />
                      Receive Stock
                    </Button>
                    <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => setShowSeedDrugs(true)}>
                      <Database className="w-6 h-6" />
                      Import Drugs
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Alerts */}
              {alerts && (alerts.low_stock_count > 0 || alerts.expiring_soon_count > 0) && (
                <Card className="border-orange-200 bg-orange-50">
                  <CardHeader>
                    <CardTitle className="text-orange-800 flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5" />
                      Inventory Alerts
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid md:grid-cols-3 gap-4">
                      {alerts.low_stock_count > 0 && (
                        <div className="p-4 bg-white rounded-lg">
                          <p className="font-semibold text-orange-700">{alerts.low_stock_count} Low Stock Items</p>
                          <p className="text-sm text-slate-500">Need reorder</p>
                        </div>
                      )}
                      {alerts.expiring_soon_count > 0 && (
                        <div className="p-4 bg-white rounded-lg">
                          <p className="font-semibold text-yellow-700">{alerts.expiring_soon_count} Expiring Soon</p>
                          <p className="text-sm text-slate-500">Within 90 days</p>
                        </div>
                      )}
                      {alerts.expired_count > 0 && (
                        <div className="p-4 bg-white rounded-lg">
                          <p className="font-semibold text-red-700">{alerts.expired_count} Expired</p>
                          <p className="text-sm text-slate-500">Remove from inventory</p>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          {/* Drugs Catalog Tab */}
          <TabsContent value="drugs">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Drug Catalog ({drugs.length})</CardTitle>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => setShowSeedDrugs(true)}>
                      <Download className="w-4 h-4 mr-2" /> Import Database
                    </Button>
                    <Button size="sm" onClick={() => setShowAddDrug(true)}>
                      <Plus className="w-4 h-4 mr-2" /> Add Drug
                    </Button>
                  </div>
                </div>
                <div className="pt-4">
                  <div className="relative max-w-sm">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      placeholder="Search drugs..."
                      value={drugSearch}
                      onChange={(e) => setDrugSearch(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {drugs.length === 0 ? (
                  <div className="text-center py-12">
                    <Pill className="w-16 h-16 mx-auto mb-4 text-slate-300" />
                    <p className="text-slate-500 mb-4">No drugs in catalog yet</p>
                    <Button onClick={() => setShowSeedDrugs(true)}>
                      <Download className="w-4 h-4 mr-2" /> Import from Global Database
                    </Button>
                  </div>
                ) : (
                  <ScrollArea className="h-[500px]">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Drug Name</TableHead>
                          <TableHead>Brand</TableHead>
                          <TableHead>Strength</TableHead>
                          <TableHead>Form</TableHead>
                          <TableHead>Stock</TableHead>
                          <TableHead>Price</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredDrugs.map((drug) => (
                          <TableRow key={drug.id}>
                            <TableCell className="font-medium">{drug.generic_name}</TableCell>
                            <TableCell>{drug.brand_name || '-'}</TableCell>
                            <TableCell>{drug.strength}</TableCell>
                            <TableCell>
                              <Badge variant="outline">{drug.dosage_form}</Badge>
                            </TableCell>
                            <TableCell>
                              <Badge className={
                                drug.current_stock === 0 ? 'bg-red-100 text-red-700' :
                                drug.current_stock <= drug.reorder_level ? 'bg-orange-100 text-orange-700' :
                                'bg-green-100 text-green-700'
                              }>
                                {drug.current_stock}
                              </Badge>
                            </TableCell>
                            <TableCell>₵{(drug.unit_price || 0).toFixed(2)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </ScrollArea>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Inventory Tab */}
          <TabsContent value="inventory">
            <div className="space-y-6">
              {/* Reorder Suggestions */}
              {reorderSuggestions.length > 0 && (
                <Card className="border-blue-200">
                  <CardHeader>
                    <CardTitle className="text-blue-800 flex items-center gap-2">
                      <Truck className="w-5 h-5" />
                      Reorder Suggestions ({reorderSuggestions.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Drug</TableHead>
                          <TableHead>Current Stock</TableHead>
                          <TableHead>Reorder Level</TableHead>
                          <TableHead>Suggested Qty</TableHead>
                          <TableHead>Est. Cost</TableHead>
                          <TableHead>Priority</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {reorderSuggestions.slice(0, 10).map((item) => (
                          <TableRow key={item.drug_id}>
                            <TableCell className="font-medium">{item.drug_name}</TableCell>
                            <TableCell>{item.current_stock}</TableCell>
                            <TableCell>{item.reorder_level}</TableCell>
                            <TableCell className="font-semibold text-blue-600">
                              {item.suggested_quantity}
                            </TableCell>
                            <TableCell>₵{(item.estimated_cost || 0).toFixed(2)}</TableCell>
                            <TableCell>
                              <Badge className={
                                item.priority === 'high' ? 'bg-red-100 text-red-700' :
                                'bg-yellow-100 text-yellow-700'
                              }>
                                {item.priority}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              )}

              {/* Current Inventory */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>Current Inventory</CardTitle>
                    <Button size="sm" onClick={() => setShowReceiveStock(true)} className="bg-green-600 hover:bg-green-700">
                      <Plus className="w-4 h-4 mr-2" /> Receive Stock
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {inventory.length === 0 ? (
                    <div className="text-center py-12 text-slate-500">
                      <Package className="w-16 h-16 mx-auto mb-4 text-slate-300" />
                      <p>No inventory batches recorded</p>
                      <p className="text-sm mt-2">Add drugs to catalog first, then receive stock</p>
                    </div>
                  ) : (
                    <ScrollArea className="h-[400px]">
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Drug</TableHead>
                            <TableHead>Batch #</TableHead>
                            <TableHead>Qty</TableHead>
                            <TableHead>Cost</TableHead>
                            <TableHead>Sell Price</TableHead>
                            <TableHead>Expiry</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {inventory.map((item) => (
                            <TableRow key={item.id}>
                              <TableCell className="font-medium">{item.drug_name}</TableCell>
                              <TableCell className="font-mono text-sm">{item.batch_number}</TableCell>
                              <TableCell>{item.quantity_remaining}</TableCell>
                              <TableCell>₵{(item.cost_price || 0).toFixed(2)}</TableCell>
                              <TableCell>₵{(item.selling_price || 0).toFixed(2)}</TableCell>
                              <TableCell>
                                <Badge variant="outline">{item.expiry_date}</Badge>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </ScrollArea>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Sales Tab */}
          <TabsContent value="sales">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Sales History</CardTitle>
                  <Button onClick={() => setShowNewSale(true)} className="bg-green-600 hover:bg-green-700">
                    <Plus className="w-4 h-4 mr-2" /> New Sale
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {sales.length === 0 ? (
                  <div className="text-center py-12 text-slate-500">
                    <ShoppingCart className="w-16 h-16 mx-auto mb-4 text-slate-300" />
                    <p>No sales recorded yet</p>
                  </div>
                ) : (
                  <ScrollArea className="h-[500px]">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Date</TableHead>
                          <TableHead>Sale ID</TableHead>
                          <TableHead>Type</TableHead>
                          <TableHead>Items</TableHead>
                          <TableHead>Total</TableHead>
                          <TableHead>Payment</TableHead>
                          <TableHead>Status</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {sales.map((sale) => (
                          <TableRow key={sale.id}>
                            <TableCell className="text-sm">{new Date(sale.created_at).toLocaleDateString()}</TableCell>
                            <TableCell className="font-mono text-sm">{sale.id.slice(0, 8)}</TableCell>
                            <TableCell>
                              <Badge variant="outline">{sale.sale_type}</Badge>
                            </TableCell>
                            <TableCell>{sale.items?.length || 0}</TableCell>
                            <TableCell className="font-semibold">₵{(sale.total_amount || 0).toFixed(2)}</TableCell>
                            <TableCell>{sale.payment_method}</TableCell>
                            <TableCell>
                              <Badge className="bg-green-100 text-green-700">{sale.payment_status}</Badge>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </ScrollArea>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Prescriptions Tab */}
          <TabsContent value="prescriptions">
            <Card>
              <CardHeader>
                <CardTitle>Incoming Prescriptions ({prescriptions.length})</CardTitle>
              </CardHeader>
              <CardContent>
                {prescriptions.length === 0 ? (
                  <div className="text-center py-12 text-slate-500">
                    <FileText className="w-16 h-16 mx-auto mb-4 text-slate-300" />
                    <p>No pending prescriptions</p>
                    <p className="text-sm mt-2">E-prescriptions from hospitals will appear here</p>
                  </div>
                ) : (
                  <ScrollArea className="h-[400px]">
                    <div className="space-y-4">
                      {prescriptions.map((rx) => (
                        <Card key={rx.id} className="border-l-4 border-l-blue-500">
                          <CardContent className="pt-4">
                            <div className="flex items-start justify-between">
                              <div>
                                <p className="font-semibold">{rx.patient_name}</p>
                                <p className="text-sm text-slate-500">From: {rx.prescriber_name}</p>
                                <p className="text-sm text-slate-500">Hospital: {rx.hospital_name}</p>
                              </div>
                              <div className="flex gap-2">
                                <Button size="sm" variant="outline" onClick={async () => {
                                  try {
                                    await pharmacyDashAPI.acceptPrescription(rx.id);
                                    toast.success('Prescription accepted');
                                    fetchData();
                                  } catch (error) {
                                    toast.error('Failed to accept');
                                  }
                                }}>
                                  <CheckCircle className="w-4 h-4 mr-1" /> Accept
                                </Button>
                                <Button size="sm" className="bg-green-600 hover:bg-green-700" onClick={async () => {
                                  try {
                                    await pharmacyDashAPI.dispensePrescription(rx.id);
                                    toast.success('Prescription dispensed');
                                    fetchData();
                                  } catch (error) {
                                    toast.error('Failed to dispense');
                                  }
                                }}>
                                  Dispense <ArrowRight className="w-4 h-4 ml-1" />
                                </Button>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </ScrollArea>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Staff Tab */}
          <TabsContent value="staff">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Staff Members ({staff.length})</CardTitle>
                  <Button size="sm" onClick={() => setShowAddStaff(true)} className="bg-purple-600 hover:bg-purple-700">
                    <Plus className="w-4 h-4 mr-2" /> Add Staff
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {staff.length === 0 ? (
                  <div className="text-center py-12 text-slate-500">
                    <Users className="w-16 h-16 mx-auto mb-4 text-slate-300" />
                    <p>No additional staff members</p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Name</TableHead>
                        <TableHead>Email</TableHead>
                        <TableHead>Role</TableHead>
                        <TableHead>Department</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {staff.map((member) => (
                        <TableRow key={member.id}>
                          <TableCell className="font-medium">{member.first_name} {member.last_name}</TableCell>
                          <TableCell>{member.email}</TableCell>
                          <TableCell>
                            <Badge variant="outline">{member.role?.replace(/_/g, ' ')}</Badge>
                          </TableCell>
                          <TableCell>{member.department?.replace(/_/g, ' ')}</TableCell>
                          <TableCell>
                            <Badge className={member.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}>
                              {member.is_active ? 'Active' : 'Inactive'}
                            </Badge>
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
      </main>

      {/* Dialogs */}
      <NewSaleDialog
        open={showNewSale}
        onOpenChange={setShowNewSale}
        drugs={drugs}
        onSuccess={fetchData}
      />
      <AddDrugDialog
        open={showAddDrug}
        onOpenChange={setShowAddDrug}
        onSuccess={fetchData}
      />
      <ReceiveStockDialog
        open={showReceiveStock}
        onOpenChange={setShowReceiveStock}
        drugs={drugs}
        onSuccess={fetchData}
      />
      <AddStaffDialog
        open={showAddStaff}
        onOpenChange={setShowAddStaff}
        onSuccess={async () => {
          const staffRes = await pharmacyDashAPI.getStaff();
          setStaff(staffRes.data.staff || []);
        }}
      />
      <SeedDrugsDialog
        open={showSeedDrugs}
        onOpenChange={setShowSeedDrugs}
        onSuccess={fetchData}
      />
    </div>
  );
}
