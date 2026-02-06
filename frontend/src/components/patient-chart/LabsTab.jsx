import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { toast } from 'sonner';
import { Plus, FlaskConical, TrendingUp, TrendingDown, Loader2, Clock, CheckCircle, AlertTriangle, Activity } from 'lucide-react';
import { labAPI } from '@/lib/api';
import { formatDateTime } from '@/lib/utils';

export default function LabsTab({ patientId, user }) {
  const [labOrders, setLabOrders] = useState([]);
  const [labResults, setLabResults] = useState([]);
  const [labPanels, setLabPanels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [labOrderDialogOpen, setLabOrderDialogOpen] = useState(false);
  const [viewResultsDialogOpen, setViewResultsDialogOpen] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [simulatingLab, setSimulatingLab] = useState(null);
  const [saving, setSaving] = useState(false);
  
  const [newLabOrder, setNewLabOrder] = useState({
    panel_code: 'CBC',
    priority: 'routine',
    clinical_notes: '',
    diagnosis: '',
    fasting_required: false
  });

  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [patientId]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [ordersRes, resultsRes, panelsRes] = await Promise.all([
        labAPI.getPatientOrders(patientId),
        labAPI.getPatientResults(patientId),
        labAPI.getPanels()
      ]);
      setLabOrders(ordersRes.data.orders || []);
      setLabResults(resultsRes.data.results || []);
      setLabPanels(panelsRes.data.panels || []);
    } catch (err) {
      console.error('Failed to fetch lab data', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateLabOrder = async () => {
    setSaving(true);
    try {
      await labAPI.createOrder({
        patient_id: patientId,
        ...newLabOrder
      });
      toast.success('Lab order created successfully');
      setLabOrderDialogOpen(false);
      setNewLabOrder({ panel_code: 'CBC', priority: 'routine', clinical_notes: '', diagnosis: '', fasting_required: false });
      fetchData();
    } catch (err) {
      toast.error('Failed to create lab order');
    } finally {
      setSaving(false);
    }
  };

  const handleSimulateResults = async (orderId) => {
    setSimulatingLab(orderId);
    try {
      await labAPI.simulateResults(orderId);
      toast.success('Lab results generated');
      fetchData();
    } catch (err) {
      toast.error('Failed to simulate results');
    } finally {
      setSimulatingLab(null);
    }
  };

  const viewOrderResults = (order) => {
    setSelectedOrder(order);
    setViewResultsDialogOpen(true);
  };

  const getOrderStatusBadge = (status) => {
    const styles = {
      ordered: 'bg-yellow-100 text-yellow-800',
      collected: 'bg-blue-100 text-blue-800',
      processing: 'bg-purple-100 text-purple-800',
      resulted: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800'
    };
    return <Badge className={styles[status] || 'bg-gray-100'}>{status}</Badge>;
  };

  const getResultFlag = (result) => {
    if (!result.flag || result.flag === 'N') return null;
    if (result.flag === 'H' || result.flag === 'HH') {
      return <Badge className="bg-red-100 text-red-700 gap-1"><TrendingUp className="w-3 h-3" /> High</Badge>;
    }
    if (result.flag === 'L' || result.flag === 'LL') {
      return <Badge className="bg-blue-100 text-blue-700 gap-1"><TrendingDown className="w-3 h-3" /> Low</Badge>;
    }
    if (result.flag === 'A') {
      return <Badge className="bg-amber-100 text-amber-700 gap-1"><AlertTriangle className="w-3 h-3" /> Abnormal</Badge>;
    }
    return null;
  };

  // Group results by order
  const getResultsForOrder = (orderId) => {
    return labResults.filter(r => r.order_id === orderId);
  };

  // Get latest results grouped by test code for trends
  const getLatestResultsByTest = () => {
    const byTest = {};
    labResults.forEach(r => {
      if (!byTest[r.test_code] || new Date(r.result_date) > new Date(byTest[r.test_code].result_date)) {
        byTest[r.test_code] = r;
      }
    });
    return Object.values(byTest);
  };

  // Get abnormal results count
  const abnormalCount = labResults.filter(r => r.flag && r.flag !== 'N').length;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <FlaskConical className="w-8 h-8 text-blue-500" />
              <div>
                <p className="text-sm text-gray-500">Total Orders</p>
                <p className="text-2xl font-bold">{labOrders.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <Clock className="w-8 h-8 text-yellow-500" />
              <div>
                <p className="text-sm text-gray-500">Pending</p>
                <p className="text-2xl font-bold">{labOrders.filter(o => o.status !== 'resulted').length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <CheckCircle className="w-8 h-8 text-green-500" />
              <div>
                <p className="text-sm text-gray-500">Resulted</p>
                <p className="text-2xl font-bold">{labOrders.filter(o => o.status === 'resulted').length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className={abnormalCount > 0 ? 'border-red-200 bg-red-50' : ''}>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className={`w-8 h-8 ${abnormalCount > 0 ? 'text-red-500' : 'text-gray-400'}`} />
              <div>
                <p className="text-sm text-gray-500">Abnormal</p>
                <p className={`text-2xl font-bold ${abnormalCount > 0 ? 'text-red-600' : ''}`}>{abnormalCount}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Lab Orders Section */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <FlaskConical className="w-5 h-5 text-emerald-600" />
              Lab Orders
            </CardTitle>
            <CardDescription>Diagnostic laboratory orders and results</CardDescription>
          </div>
          <Button onClick={() => setLabOrderDialogOpen(true)} className="gap-2" data-testid="new-lab-order-btn">
            <Plus className="w-4 h-4" /> New Lab Order
          </Button>
        </CardHeader>
        <CardContent>
          {labOrders.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <FlaskConical className="w-12 h-12 mx-auto mb-4 opacity-30" />
              <p>No lab orders found</p>
              <Button onClick={() => setLabOrderDialogOpen(true)} className="mt-4" variant="outline">
                Create First Lab Order
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Panel</TableHead>
                  <TableHead>Ordered</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Results</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {labOrders.map((order) => {
                  const orderResults = getResultsForOrder(order.id);
                  const hasAbnormal = orderResults.some(r => r.flag && r.flag !== 'N');
                  
                  return (
                    <TableRow key={order.id} className={hasAbnormal ? 'bg-red-50' : ''}>
                      <TableCell>
                        <div>
                          <p className="font-medium">{order.panel_name || order.panel_code}</p>
                          {order.diagnosis && <p className="text-xs text-gray-500">{order.diagnosis}</p>}
                        </div>
                      </TableCell>
                      <TableCell className="text-sm text-gray-500">
                        {formatDateTime(order.ordered_at)}
                      </TableCell>
                      <TableCell>
                        <Badge className={order.priority === 'stat' ? 'bg-red-100 text-red-700' : order.priority === 'urgent' ? 'bg-amber-100 text-amber-700' : 'bg-gray-100'}>
                          {order.priority}
                        </Badge>
                      </TableCell>
                      <TableCell>{getOrderStatusBadge(order.status)}</TableCell>
                      <TableCell>
                        {orderResults.length > 0 ? (
                          <div className="flex items-center gap-2">
                            <span className="text-sm">{orderResults.length} tests</span>
                            {hasAbnormal && <Badge className="bg-red-100 text-red-700 text-xs">Abnormal</Badge>}
                          </div>
                        ) : (
                          <span className="text-sm text-gray-400">Pending</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex gap-2 justify-end">
                          {order.status === 'resulted' ? (
                            <Button size="sm" variant="outline" onClick={() => viewOrderResults(order)} data-testid={`view-results-${order.id}`}>
                              View Results
                            </Button>
                          ) : (
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => handleSimulateResults(order.id)}
                              disabled={simulatingLab === order.id}
                              data-testid={`simulate-${order.id}`}
                            >
                              {simulatingLab === order.id ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Simulate Results'}
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Latest Results Summary */}
      {labResults.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-blue-600" />
              Latest Lab Results
            </CardTitle>
            <CardDescription>Most recent values for each test</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {getLatestResultsByTest().slice(0, 12).map((result) => (
                <div 
                  key={result.id} 
                  className={`p-3 rounded-lg border ${
                    result.flag === 'H' || result.flag === 'HH' ? 'border-red-200 bg-red-50' :
                    result.flag === 'L' || result.flag === 'LL' ? 'border-blue-200 bg-blue-50' :
                    result.flag === 'A' ? 'border-amber-200 bg-amber-50' :
                    'border-gray-200 bg-gray-50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-medium text-gray-500">{result.test_code}</span>
                    {getResultFlag(result)}
                  </div>
                  <p className="text-lg font-bold">{result.value} <span className="text-xs font-normal text-gray-500">{result.unit}</span></p>
                  <p className="text-xs text-gray-400">{result.test_name}</p>
                  <p className="text-xs text-gray-400 mt-1">Ref: {result.reference_low}-{result.reference_high}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Create Lab Order Dialog */}
      <Dialog open={labOrderDialogOpen} onOpenChange={setLabOrderDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FlaskConical className="w-5 h-5 text-emerald-600" />
              Order Lab Tests
            </DialogTitle>
            <DialogDescription>Select a lab panel and provide clinical details</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Lab Panel *</Label>
              <Select value={newLabOrder.panel_code} onValueChange={(v) => setNewLabOrder({...newLabOrder, panel_code: v})}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {labPanels.map(panel => (
                    <SelectItem key={panel.code} value={panel.code}>
                      <div>
                        <span className="font-medium">{panel.code}</span>
                        <span className="text-gray-500 ml-2">- {panel.name}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Priority</Label>
              <Select value={newLabOrder.priority} onValueChange={(v) => setNewLabOrder({...newLabOrder, priority: v})}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="routine">Routine</SelectItem>
                  <SelectItem value="urgent">Urgent</SelectItem>
                  <SelectItem value="stat">STAT</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Clinical Indication / Diagnosis</Label>
              <Textarea
                value={newLabOrder.diagnosis}
                onChange={(e) => setNewLabOrder({...newLabOrder, diagnosis: e.target.value})}
                placeholder="Reason for ordering labs..."
              />
            </div>
            <div className="space-y-2">
              <Label>Clinical Notes</Label>
              <Textarea
                value={newLabOrder.clinical_notes}
                onChange={(e) => setNewLabOrder({...newLabOrder, clinical_notes: e.target.value})}
                placeholder="Additional notes for lab..."
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="fasting"
                checked={newLabOrder.fasting_required}
                onChange={(e) => setNewLabOrder({...newLabOrder, fasting_required: e.target.checked})}
                className="rounded"
              />
              <Label htmlFor="fasting" className="cursor-pointer">Fasting Required</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setLabOrderDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleCreateLabOrder} disabled={saving} className="bg-emerald-600 hover:bg-emerald-700">
              {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Order Labs
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* View Results Dialog */}
      <Dialog open={viewResultsDialogOpen} onOpenChange={setViewResultsDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FlaskConical className="w-5 h-5 text-blue-600" />
              Lab Results - {selectedOrder?.panel_name || selectedOrder?.panel_code}
            </DialogTitle>
            <DialogDescription>
              Ordered: {selectedOrder && formatDateTime(selectedOrder.ordered_at)}
            </DialogDescription>
          </DialogHeader>
          <div className="overflow-y-auto flex-1">
            {selectedOrder && (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Test</TableHead>
                    <TableHead>Result</TableHead>
                    <TableHead>Reference Range</TableHead>
                    <TableHead>Flag</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {getResultsForOrder(selectedOrder.id).map((result) => (
                    <TableRow key={result.id} className={result.flag && result.flag !== 'N' ? 'bg-red-50' : ''}>
                      <TableCell>
                        <div>
                          <p className="font-medium">{result.test_code}</p>
                          <p className="text-xs text-gray-500">{result.test_name}</p>
                        </div>
                      </TableCell>
                      <TableCell className="font-semibold">
                        {result.value} <span className="text-gray-500 font-normal">{result.unit}</span>
                      </TableCell>
                      <TableCell className="text-sm text-gray-500">
                        {result.reference_low} - {result.reference_high} {result.unit}
                      </TableCell>
                      <TableCell>{getResultFlag(result)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setViewResultsDialogOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
