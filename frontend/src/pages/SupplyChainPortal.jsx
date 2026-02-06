import React, { useState, useEffect } from 'react';
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
  RefreshCw, Package, AlertTriangle, TrendingUp, Loader2, Search,
  Plus, ArrowDownCircle, ArrowUpCircle, FileText, Clock, Truck,
  BarChart3, AlertCircle, CheckCircle, DollarSign, Calendar, Building
} from 'lucide-react';
import api from '@/lib/api';

const supplyAPI = {
  getInventory: (params) => api.get('/supply-chain/inventory', { params }),
  createInventoryItem: (data) => api.post('/supply-chain/inventory', data),
  getInventoryItem: (id) => api.get(`/supply-chain/inventory/${id}`),
  receiveStock: (data) => api.post('/supply-chain/stock/receive', data),
  getBatches: (params) => api.get('/supply-chain/stock/batches', { params }),
  recordMovement: (data) => api.post('/supply-chain/stock/movement', data),
  getMovements: (params) => api.get('/supply-chain/stock/movements', { params }),
  getPurchaseOrders: (params) => api.get('/supply-chain/purchase-orders', { params }),
  createPurchaseOrder: (data) => api.post('/supply-chain/purchase-orders', data),
  updatePOStatus: (id, status, notes) => api.put(`/supply-chain/purchase-orders/${id}/status`, null, { params: { status, notes } }),
  getSuppliers: (params) => api.get('/supply-chain/suppliers', { params }),
  createSupplier: (data) => api.post('/supply-chain/suppliers', data),
  seedSuppliers: () => api.post('/supply-chain/suppliers/seed'),
  getDashboard: () => api.get('/supply-chain/dashboard'),
  getExpiringReport: (params) => api.get('/supply-chain/reports/expiring', { params }),
  getValuationReport: () => api.get('/supply-chain/reports/stock-valuation'),
};

export default function SupplyChainPortal() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);
  const [inventory, setInventory] = useState([]);
  const [batches, setBatches] = useState([]);
  const [movements, setMovements] = useState([]);
  const [purchaseOrders, setPurchaseOrders] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Search & Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [lowStockOnly, setLowStockOnly] = useState(false);
  
  // Dialogs
  const [addItemOpen, setAddItemOpen] = useState(false);
  const [receiveStockOpen, setReceiveStockOpen] = useState(false);
  const [createPOOpen, setCreatePOOpen] = useState(false);
  const [addSupplierOpen, setAddSupplierOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  
  // Forms
  const [itemForm, setItemForm] = useState({
    drug_name: '',
    drug_code: '',
    fda_registration: '',
    manufacturer: '',
    category: '',
    unit_of_measure: 'tablet',
    unit_cost: 0,
    selling_price: 0,
    reorder_level: 10,
    max_stock_level: 1000,
    storage_location: '',
    storage_conditions: '',
    is_controlled: false,
    schedule: ''
  });
  
  const [receiveForm, setReceiveForm] = useState({
    inventory_item_id: '',
    quantity: 0,
    batch_number: '',
    expiry_date: '',
    supplier_name: '',
    unit_cost: 0,
    invoice_number: '',
    notes: ''
  });
  
  const [poForm, setPOForm] = useState({
    supplier_name: '',
    expected_date: '',
    items: [],
    notes: ''
  });
  
  const [supplierForm, setSupplierForm] = useState({
    name: '',
    contact_person: '',
    email: '',
    phone: '',
    address: '',
    city: '',
    region: '',
    payment_terms: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [dashboardRes, inventoryRes, batchesRes, posRes, suppliersRes] = await Promise.all([
        supplyAPI.getDashboard(),
        supplyAPI.getInventory({ low_stock_only: lowStockOnly, search: searchTerm || undefined }),
        supplyAPI.getBatches({}),
        supplyAPI.getPurchaseOrders({}),
        supplyAPI.getSuppliers({})
      ]);
      
      setDashboard(dashboardRes.data);
      setInventory(inventoryRes.data.items || []);
      setBatches(batchesRes.data.batches || []);
      setPurchaseOrders(posRes.data.orders || []);
      setSuppliers(suppliersRes.data.suppliers || []);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to load supply chain data'));
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    setLoading(true);
    try {
      const res = await supplyAPI.getInventory({ search: searchTerm || undefined, low_stock_only: lowStockOnly });
      setInventory(res.data.items || []);
    } catch (err) {
      toast.error('Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleAddItem = async (e) => {
    e.preventDefault();
    if (!itemForm.drug_name) {
      toast.error('Drug name is required');
      return;
    }
    
    setSaving(true);
    try {
      await supplyAPI.createInventoryItem(itemForm);
      toast.success('Inventory item added');
      setAddItemOpen(false);
      setItemForm({
        drug_name: '', drug_code: '', fda_registration: '', manufacturer: '',
        category: '', unit_of_measure: 'tablet', unit_cost: 0, selling_price: 0,
        reorder_level: 10, max_stock_level: 1000, storage_location: '',
        storage_conditions: '', is_controlled: false, schedule: ''
      });
      fetchData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to add item'));
    } finally {
      setSaving(false);
    }
  };

  const handleReceiveStock = async (e) => {
    e.preventDefault();
    if (!receiveForm.inventory_item_id || !receiveForm.quantity || !receiveForm.batch_number || !receiveForm.expiry_date) {
      toast.error('Please fill in all required fields');
      return;
    }
    
    setSaving(true);
    try {
      await supplyAPI.receiveStock(receiveForm);
      toast.success('Stock received successfully');
      setReceiveStockOpen(false);
      setReceiveForm({
        inventory_item_id: '', quantity: 0, batch_number: '', expiry_date: '',
        supplier_name: '', unit_cost: 0, invoice_number: '', notes: ''
      });
      setSelectedItem(null);
      fetchData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to receive stock'));
    } finally {
      setSaving(false);
    }
  };

  const handleSeedSuppliers = async () => {
    try {
      const res = await supplyAPI.seedSuppliers();
      toast.success(res.data.message);
      fetchData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to seed suppliers'));
    }
  };

  const handleAddSupplier = async (e) => {
    e.preventDefault();
    if (!supplierForm.name) {
      toast.error('Supplier name is required');
      return;
    }
    
    setSaving(true);
    try {
      await supplyAPI.createSupplier(supplierForm);
      toast.success('Supplier added');
      setAddSupplierOpen(false);
      setSupplierForm({
        name: '', contact_person: '', email: '', phone: '',
        address: '', city: '', region: '', payment_terms: ''
      });
      fetchData();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to add supplier'));
    } finally {
      setSaving(false);
    }
  };

  const openReceiveStock = (item) => {
    setSelectedItem(item);
    setReceiveForm({
      ...receiveForm,
      inventory_item_id: item.id,
      unit_cost: item.unit_cost || 0
    });
    setReceiveStockOpen(true);
  };

  const getStockStatusBadge = (status) => {
    const statusConfig = {
      in_stock: { color: 'bg-green-100 text-green-700', icon: CheckCircle },
      low_stock: { color: 'bg-amber-100 text-amber-700', icon: AlertTriangle },
      out_of_stock: { color: 'bg-red-100 text-red-700', icon: AlertCircle },
      expiring_soon: { color: 'bg-orange-100 text-orange-700', icon: Clock }
    };
    const config = statusConfig[status] || { color: 'bg-gray-100 text-gray-700', icon: Package };
    const Icon = config.icon;
    
    return (
      <Badge className={`${config.color} gap-1`}>
        <Icon className="w-3 h-3" />
        {status?.replace('_', ' ')}
      </Badge>
    );
  };

  const getPOStatusBadge = (status) => {
    const colors = {
      draft: 'bg-gray-100 text-gray-700',
      submitted: 'bg-blue-100 text-blue-700',
      approved: 'bg-green-100 text-green-700',
      ordered: 'bg-purple-100 text-purple-700',
      received: 'bg-emerald-100 text-emerald-700',
      cancelled: 'bg-red-100 text-red-700'
    };
    return <Badge className={colors[status] || 'bg-gray-100'}>{status?.replace('_', ' ')}</Badge>;
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="supply-chain-portal">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Package className="w-7 h-7 text-indigo-600" />
            Supply Chain & Inventory
          </h1>
          <p className="text-slate-500 mt-1">Manage pharmacy stock, orders, and suppliers</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setAddItemOpen(true)} className="gap-2" data-testid="add-item-btn">
            <Plus className="w-4 h-4" />
            Add Item
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
              <Package className="w-8 h-8 mx-auto mb-2 text-slate-400" />
              <p className="text-sm text-slate-600">Total Items</p>
              <p className="text-2xl font-bold">{dashboard?.inventory?.total_items || 0}</p>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-red-50 border-red-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <AlertCircle className="w-8 h-8 mx-auto mb-2 text-red-600" />
              <p className="text-sm text-red-700">Out of Stock</p>
              <p className="text-2xl font-bold text-red-800">{dashboard?.inventory?.out_of_stock || 0}</p>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-amber-50 border-amber-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-amber-600" />
              <p className="text-sm text-amber-700">Low Stock</p>
              <p className="text-2xl font-bold text-amber-800">{dashboard?.inventory?.low_stock || 0}</p>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-orange-50 border-orange-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <Clock className="w-8 h-8 mx-auto mb-2 text-orange-600" />
              <p className="text-sm text-orange-700">Expiring Soon</p>
              <p className="text-2xl font-bold text-orange-800">{dashboard?.alerts?.expiring_soon || 0}</p>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-green-50 border-green-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <DollarSign className="w-8 h-8 mx-auto mb-2 text-green-600" />
              <p className="text-sm text-green-700">Stock Value</p>
              <p className="text-xl font-bold text-green-800">₵{dashboard?.inventory?.total_value?.toLocaleString() || '0'}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="dashboard" data-testid="tab-dashboard">Dashboard</TabsTrigger>
          <TabsTrigger value="inventory" data-testid="tab-inventory">Inventory</TabsTrigger>
          <TabsTrigger value="batches" data-testid="tab-batches">Batches</TabsTrigger>
          <TabsTrigger value="orders" data-testid="tab-orders">Purchase Orders</TabsTrigger>
          <TabsTrigger value="suppliers" data-testid="tab-suppliers">Suppliers</TabsTrigger>
        </TabsList>

        {/* Dashboard Tab */}
        <TabsContent value="dashboard" className="mt-4 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <BarChart3 className="w-4 h-4" />
                  Inventory Overview
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500" /> In Stock
                    </span>
                    <span className="font-bold text-green-600">
                      {(dashboard?.inventory?.total_items || 0) - (dashboard?.inventory?.out_of_stock || 0) - (dashboard?.inventory?.low_stock || 0)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-amber-500" /> Low Stock
                    </span>
                    <span className="font-bold text-amber-600">{dashboard?.inventory?.low_stock || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 text-red-500" /> Out of Stock
                    </span>
                    <span className="font-bold text-red-600">{dashboard?.inventory?.out_of_stock || 0}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-orange-500" />
                  Alerts
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Items Expiring (90 days)</span>
                    <Badge className="bg-orange-100 text-orange-700">{dashboard?.alerts?.expiring_soon || 0}</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Need Reorder</span>
                    <Badge className="bg-amber-100 text-amber-700">{dashboard?.alerts?.needs_reorder || 0}</Badge>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Pending POs</span>
                    <Badge className="bg-blue-100 text-blue-700">{dashboard?.purchase_orders?.pending || 0}</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="md:col-span-2">
              <CardHeader>
                <CardTitle className="text-base">Recent Stock Movements</CardTitle>
              </CardHeader>
              <CardContent>
                {dashboard?.recent_movements?.length > 0 ? (
                  <div className="space-y-2">
                    {dashboard.recent_movements.slice(0, 5).map(movement => (
                      <div key={movement.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                        <div className="flex items-center gap-3">
                          {movement.movement_type === 'received' ? (
                            <ArrowDownCircle className="w-5 h-5 text-green-500" />
                          ) : (
                            <ArrowUpCircle className="w-5 h-5 text-blue-500" />
                          )}
                          <div>
                            <p className="font-medium text-sm">{movement.drug_name}</p>
                            <p className="text-xs text-gray-500">{movement.movement_type} - {movement.quantity} units</p>
                          </div>
                        </div>
                        <p className="text-xs text-gray-400">
                          {new Date(movement.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-4">No recent movements</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Inventory Tab */}
        <TabsContent value="inventory" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Inventory Items</CardTitle>
                <CardDescription>Manage drug catalog and stock levels</CardDescription>
              </div>
              <Button onClick={() => setAddItemOpen(true)} className="gap-2">
                <Plus className="w-4 h-4" /> Add Item
              </Button>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4 mb-4">
                <div className="flex-1 relative">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                  <Input
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                    placeholder="Search by drug name or code..."
                    className="pl-10"
                    data-testid="inventory-search"
                  />
                </div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={lowStockOnly}
                    onChange={(e) => { setLowStockOnly(e.target.checked); }}
                    className="rounded"
                  />
                  <span className="text-sm">Low stock only</span>
                </label>
                <Button onClick={handleSearch} variant="outline">Search</Button>
              </div>
              
              {inventory.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <Package className="w-12 h-12 mx-auto mb-4 opacity-30" />
                  <p>No inventory items found</p>
                  <Button onClick={() => setAddItemOpen(true)} className="mt-4" variant="outline">
                    Add First Item
                  </Button>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Drug Name</TableHead>
                      <TableHead>Code</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Stock</TableHead>
                      <TableHead>Reorder Level</TableHead>
                      <TableHead>Unit Cost</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {inventory.map((item) => (
                      <TableRow key={item.id} data-testid={`inventory-row-${item.id}`}>
                        <TableCell>
                          <div>
                            <p className="font-medium">{item.drug_name}</p>
                            {item.manufacturer && <p className="text-xs text-gray-500">{item.manufacturer}</p>}
                          </div>
                        </TableCell>
                        <TableCell className="font-mono text-sm">{item.drug_code}</TableCell>
                        <TableCell>{item.category || '-'}</TableCell>
                        <TableCell className="font-semibold">{item.current_stock || 0}</TableCell>
                        <TableCell>{item.reorder_level}</TableCell>
                        <TableCell>₵{item.unit_cost?.toFixed(2) || '0.00'}</TableCell>
                        <TableCell>{getStockStatusBadge(item.stock_status)}</TableCell>
                        <TableCell className="text-right">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => openReceiveStock(item)}
                            className="gap-1"
                            data-testid={`receive-stock-${item.id}`}
                          >
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

        {/* Batches Tab */}
        <TabsContent value="batches" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Stock Batches</CardTitle>
              <CardDescription>Track batch numbers and expiry dates</CardDescription>
            </CardHeader>
            <CardContent>
              {batches.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <FileText className="w-12 h-12 mx-auto mb-4 opacity-30" />
                  <p>No batches found</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Drug Name</TableHead>
                      <TableHead>Batch #</TableHead>
                      <TableHead>Qty Remaining</TableHead>
                      <TableHead>Expiry Date</TableHead>
                      <TableHead>Supplier</TableHead>
                      <TableHead>Received</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {batches.map((batch) => {
                      const isExpiringSoon = new Date(batch.expiry_date) <= new Date(Date.now() + 90 * 24 * 60 * 60 * 1000);
                      return (
                        <TableRow key={batch.id} className={isExpiringSoon ? 'bg-orange-50' : ''}>
                          <TableCell className="font-medium">{batch.drug_name}</TableCell>
                          <TableCell className="font-mono text-sm">{batch.batch_number}</TableCell>
                          <TableCell className="font-semibold">{batch.quantity_remaining}</TableCell>
                          <TableCell>
                            <span className={isExpiringSoon ? 'text-orange-600 font-semibold' : ''}>
                              {batch.expiry_date}
                            </span>
                            {isExpiringSoon && <Badge className="ml-2 bg-orange-100 text-orange-700 text-xs">Expiring</Badge>}
                          </TableCell>
                          <TableCell>{batch.supplier_name || '-'}</TableCell>
                          <TableCell className="text-sm text-gray-500">
                            {new Date(batch.received_at).toLocaleDateString()}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Purchase Orders Tab */}
        <TabsContent value="orders" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Purchase Orders</CardTitle>
                <CardDescription>Manage supplier orders</CardDescription>
              </div>
              <Button onClick={() => setCreatePOOpen(true)} className="gap-2">
                <Plus className="w-4 h-4" /> Create PO
              </Button>
            </CardHeader>
            <CardContent>
              {purchaseOrders.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <FileText className="w-12 h-12 mx-auto mb-4 opacity-30" />
                  <p>No purchase orders found</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>PO #</TableHead>
                      <TableHead>Supplier</TableHead>
                      <TableHead>Items</TableHead>
                      <TableHead>Total Amount</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Created</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {purchaseOrders.map((po) => (
                      <TableRow key={po.id}>
                        <TableCell className="font-mono text-sm">{po.po_number}</TableCell>
                        <TableCell className="font-medium">{po.supplier_name}</TableCell>
                        <TableCell>{po.total_items} items ({po.total_quantity} units)</TableCell>
                        <TableCell className="font-semibold">₵{po.total_amount?.toFixed(2)}</TableCell>
                        <TableCell>{getPOStatusBadge(po.status)}</TableCell>
                        <TableCell className="text-sm text-gray-500">
                          {new Date(po.created_at).toLocaleDateString()}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Suppliers Tab */}
        <TabsContent value="suppliers" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Suppliers</CardTitle>
                <CardDescription>Manage pharmaceutical suppliers</CardDescription>
              </div>
              <div className="flex gap-2">
                <Button onClick={handleSeedSuppliers} variant="outline" className="gap-2">
                  <Truck className="w-4 h-4" /> Seed Ghana Suppliers
                </Button>
                <Button onClick={() => setAddSupplierOpen(true)} className="gap-2">
                  <Plus className="w-4 h-4" /> Add Supplier
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {suppliers.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <Building className="w-12 h-12 mx-auto mb-4 opacity-30" />
                  <p>No suppliers found</p>
                  <div className="flex gap-2 justify-center mt-4">
                    <Button onClick={handleSeedSuppliers} variant="outline">
                      Load Ghana Suppliers
                    </Button>
                    <Button onClick={() => setAddSupplierOpen(true)}>
                      Add Custom Supplier
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {suppliers.map((supplier) => (
                    <Card key={supplier.id} className="border">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-base flex items-center gap-2">
                          <Building className="w-4 h-4 text-gray-400" />
                          {supplier.name}
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="text-sm space-y-1">
                        {supplier.city && <p className="text-gray-600">{supplier.city}, {supplier.region}</p>}
                        {supplier.phone && <p className="text-gray-600">{supplier.phone}</p>}
                        {supplier.email && <p className="text-gray-600">{supplier.email}</p>}
                        {supplier.contact_person && (
                          <p className="text-gray-500 text-xs">Contact: {supplier.contact_person}</p>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Add Inventory Item Dialog */}
      <Dialog open={addItemOpen} onOpenChange={setAddItemOpen}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>Add Inventory Item</DialogTitle>
            <DialogDescription>Add a new drug to the inventory catalog</DialogDescription>
          </DialogHeader>
          <div className="overflow-y-auto pr-2" style={{ maxHeight: 'calc(85vh - 160px)' }}>
            <form onSubmit={handleAddItem} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Drug Name *</Label>
                  <Input
                    value={itemForm.drug_name}
                    onChange={(e) => setItemForm({...itemForm, drug_name: e.target.value})}
                    placeholder="e.g., Paracetamol 500mg"
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
                    placeholder="FDA registration number"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Manufacturer</Label>
                  <Input
                    value={itemForm.manufacturer}
                    onChange={(e) => setItemForm({...itemForm, manufacturer: e.target.value})}
                    placeholder="e.g., Ernest Chemist"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Category</Label>
                  <Select value={itemForm.category} onValueChange={(v) => setItemForm({...itemForm, category: v})}>
                    <SelectTrigger><SelectValue placeholder="Select category" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Antimalarials">Antimalarials</SelectItem>
                      <SelectItem value="Antibiotics">Antibiotics</SelectItem>
                      <SelectItem value="Cardiovascular">Cardiovascular</SelectItem>
                      <SelectItem value="Diabetes">Diabetes</SelectItem>
                      <SelectItem value="Analgesics">Analgesics</SelectItem>
                      <SelectItem value="Respiratory">Respiratory</SelectItem>
                      <SelectItem value="GI">Gastrointestinal</SelectItem>
                      <SelectItem value="Vitamins">Vitamins & Supplements</SelectItem>
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
                      <SelectItem value="vial">Vial</SelectItem>
                      <SelectItem value="ampule">Ampule</SelectItem>
                      <SelectItem value="bottle">Bottle</SelectItem>
                      <SelectItem value="tube">Tube</SelectItem>
                      <SelectItem value="sachet">Sachet</SelectItem>
                      <SelectItem value="box">Box</SelectItem>
                      <SelectItem value="pack">Pack</SelectItem>
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
                    value={itemForm.unit_cost}
                    onChange={(e) => setItemForm({...itemForm, unit_cost: parseFloat(e.target.value) || 0})}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Selling Price (₵)</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={itemForm.selling_price}
                    onChange={(e) => setItemForm({...itemForm, selling_price: parseFloat(e.target.value) || 0})}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Reorder Level</Label>
                  <Input
                    type="number"
                    value={itemForm.reorder_level}
                    onChange={(e) => setItemForm({...itemForm, reorder_level: parseInt(e.target.value) || 10})}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Max Stock Level</Label>
                  <Input
                    type="number"
                    value={itemForm.max_stock_level}
                    onChange={(e) => setItemForm({...itemForm, max_stock_level: parseInt(e.target.value) || 1000})}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Storage Location</Label>
                  <Input
                    value={itemForm.storage_location}
                    onChange={(e) => setItemForm({...itemForm, storage_location: e.target.value})}
                    placeholder="e.g., Shelf A-1"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Storage Conditions</Label>
                  <Select value={itemForm.storage_conditions} onValueChange={(v) => setItemForm({...itemForm, storage_conditions: v})}>
                    <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Room temperature">Room Temperature</SelectItem>
                      <SelectItem value="Refrigerated (2-8°C)">Refrigerated (2-8°C)</SelectItem>
                      <SelectItem value="Frozen">Frozen</SelectItem>
                      <SelectItem value="Cool and dry">Cool and Dry</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={itemForm.is_controlled}
                      onChange={(e) => setItemForm({...itemForm, is_controlled: e.target.checked})}
                      className="rounded"
                    />
                    Controlled Drug
                  </Label>
                </div>
                <div className="space-y-2">
                  <Label>Schedule</Label>
                  <Select value={itemForm.schedule} onValueChange={(v) => setItemForm({...itemForm, schedule: v})}>
                    <SelectTrigger><SelectValue placeholder="Select schedule" /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="OTC">OTC (Over the Counter)</SelectItem>
                      <SelectItem value="POM">POM (Prescription Only)</SelectItem>
                      <SelectItem value="CD">CD (Controlled Drug)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setAddItemOpen(false)}>Cancel</Button>
                <Button type="submit" disabled={saving}>
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
            <DialogDescription>
              {selectedItem ? `Receiving stock for: ${selectedItem.drug_name}` : 'Record incoming stock'}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleReceiveStock} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Quantity *</Label>
                <Input
                  type="number"
                  min="1"
                  value={receiveForm.quantity}
                  onChange={(e) => setReceiveForm({...receiveForm, quantity: parseInt(e.target.value) || 0})}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Batch Number *</Label>
                <Input
                  value={receiveForm.batch_number}
                  onChange={(e) => setReceiveForm({...receiveForm, batch_number: e.target.value})}
                  placeholder="e.g., BTH-2026-001"
                  required
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Expiry Date *</Label>
                <Input
                  type="date"
                  value={receiveForm.expiry_date}
                  onChange={(e) => setReceiveForm({...receiveForm, expiry_date: e.target.value})}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Unit Cost (₵)</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={receiveForm.unit_cost}
                  onChange={(e) => setReceiveForm({...receiveForm, unit_cost: parseFloat(e.target.value) || 0})}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Supplier</Label>
              <Select value={receiveForm.supplier_name} onValueChange={(v) => setReceiveForm({...receiveForm, supplier_name: v})}>
                <SelectTrigger><SelectValue placeholder="Select supplier" /></SelectTrigger>
                <SelectContent>
                  {suppliers.map(s => (
                    <SelectItem key={s.id} value={s.name}>{s.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Invoice Number</Label>
              <Input
                value={receiveForm.invoice_number}
                onChange={(e) => setReceiveForm({...receiveForm, invoice_number: e.target.value})}
                placeholder="Supplier invoice #"
              />
            </div>
            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea
                value={receiveForm.notes}
                onChange={(e) => setReceiveForm({...receiveForm, notes: e.target.value})}
                placeholder="Additional notes..."
                rows={2}
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => { setReceiveStockOpen(false); setSelectedItem(null); }}>
                Cancel
              </Button>
              <Button type="submit" disabled={saving} className="bg-green-600 hover:bg-green-700">
                {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                <ArrowDownCircle className="w-4 h-4 mr-2" />
                Receive Stock
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Add Supplier Dialog */}
      <Dialog open={addSupplierOpen} onOpenChange={setAddSupplierOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Add Supplier</DialogTitle>
            <DialogDescription>Register a new pharmaceutical supplier</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleAddSupplier} className="space-y-4">
            <div className="space-y-2">
              <Label>Supplier Name *</Label>
              <Input
                value={supplierForm.name}
                onChange={(e) => setSupplierForm({...supplierForm, name: e.target.value})}
                placeholder="e.g., Ernest Chemist Ltd"
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Contact Person</Label>
                <Input
                  value={supplierForm.contact_person}
                  onChange={(e) => setSupplierForm({...supplierForm, contact_person: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <Label>Phone</Label>
                <Input
                  value={supplierForm.phone}
                  onChange={(e) => setSupplierForm({...supplierForm, phone: e.target.value})}
                  placeholder="+233 ..."
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Email</Label>
              <Input
                type="email"
                value={supplierForm.email}
                onChange={(e) => setSupplierForm({...supplierForm, email: e.target.value})}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>City</Label>
                <Input
                  value={supplierForm.city}
                  onChange={(e) => setSupplierForm({...supplierForm, city: e.target.value})}
                  placeholder="e.g., Accra"
                />
              </div>
              <div className="space-y-2">
                <Label>Region</Label>
                <Select value={supplierForm.region} onValueChange={(v) => setSupplierForm({...supplierForm, region: v})}>
                  <SelectTrigger><SelectValue placeholder="Select region" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Greater Accra">Greater Accra</SelectItem>
                    <SelectItem value="Ashanti">Ashanti</SelectItem>
                    <SelectItem value="Western">Western</SelectItem>
                    <SelectItem value="Eastern">Eastern</SelectItem>
                    <SelectItem value="Central">Central</SelectItem>
                    <SelectItem value="Northern">Northern</SelectItem>
                    <SelectItem value="Volta">Volta</SelectItem>
                    <SelectItem value="Upper East">Upper East</SelectItem>
                    <SelectItem value="Upper West">Upper West</SelectItem>
                    <SelectItem value="Brong Ahafo">Brong Ahafo</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-2">
              <Label>Address</Label>
              <Input
                value={supplierForm.address}
                onChange={(e) => setSupplierForm({...supplierForm, address: e.target.value})}
                placeholder="Street address"
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setAddSupplierOpen(false)}>Cancel</Button>
              <Button type="submit" disabled={saving}>
                {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
                Add Supplier
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
