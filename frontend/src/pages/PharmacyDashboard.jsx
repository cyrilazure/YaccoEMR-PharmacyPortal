import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
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
  TrendingUp, Bell, Truck, Shield, Calendar, ArrowRight
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
  getCurrentUser: () => api.get('/pharmacy-portal/auth/me', { headers: getAuthHeader() }),
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
    
    // Auto-fill price from drug
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

          {/* Items */}
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
                          {drugs.map((drug) => (
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
  const [showNewSale, setShowNewSale] = useState(false);

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
              <div className="w-10 h-10 bg-gradient-to-br from-green-600 to-blue-500 rounded-xl flex items-center justify-center">
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
                    <Button onClick={() => setShowNewSale(true)} className="h-20 flex-col gap-2">
                      <ShoppingCart className="w-6 h-6" />
                      New Sale
                    </Button>
                    <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => setActiveTab('prescriptions')}>
                      <FileText className="w-6 h-6" />
                      View Prescriptions
                    </Button>
                    <Button variant="outline" className="h-20 flex-col gap-2" onClick={() => setActiveTab('inventory')}>
                      <Package className="w-6 h-6" />
                      Check Inventory
                    </Button>
                    <Button variant="outline" className="h-20 flex-col gap-2">
                      <Shield className="w-6 h-6" />
                      Submit NHIS Claim
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
                  <Button size="sm">
                    <Plus className="w-4 h-4 mr-2" /> Add Drug
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
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
                      {drugs.map((drug) => (
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
                    <Button size="sm">
                      <Plus className="w-4 h-4 mr-2" /> Receive Stock
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
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
                                <Button size="sm" variant="outline">
                                  <CheckCircle className="w-4 h-4 mr-1" /> Accept
                                </Button>
                                <Button size="sm" className="bg-green-600 hover:bg-green-700">
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
                  <Button size="sm">
                    <Plus className="w-4 h-4 mr-2" /> Add Staff
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
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
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>

      {/* New Sale Dialog */}
      <NewSaleDialog
        open={showNewSale}
        onOpenChange={setShowNewSale}
        drugs={drugs}
        onSuccess={fetchData}
      />
    </div>
  );
}
