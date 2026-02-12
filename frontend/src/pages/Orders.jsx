import { useState, useEffect, useCallback } from 'react';
import { ordersAPI, patientAPI } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';
import { formatDateTime, getStatusColor } from '@/lib/utils';
import { ClipboardList, Search, FlaskConical, Scan, Pill, Clock, Check } from 'lucide-react';

export default function Orders() {
  const [orders, setOrders] = useState([]);
  const [patients, setPatients] = useState({});
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  const fetchOrders = useCallback(async () => {
    try {
      const params = filter !== 'all' ? { status: filter } : {};
      const [ordersRes, patientsRes] = await Promise.all([
        ordersAPI.getAll(params),
        patientAPI.getAll()
      ]);
      
      setOrders(ordersRes.data);
      
      const patientMap = {};
      patientsRes.data.forEach(p => {
        patientMap[p.id] = p.first_name + ' ' + p.last_name;
      });
      setPatients(patientMap);
    } catch (err) {
      toast.error('Failed to load orders');
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  const handleStatusChange = async (orderId, newStatus) => {
    try {
      await ordersAPI.updateStatus(orderId, newStatus);
      toast.success('Order status updated');
      fetchOrders();
    } catch (err) {
      toast.error('Failed to update order');
    }
  };

  const getOrderIcon = (type) => {
    if (type === 'lab') return <FlaskConical className="w-5 h-5 text-purple-600" />;
    if (type === 'imaging') return <Scan className="w-5 h-5 text-blue-600" />;
    if (type === 'medication') return <Pill className="w-5 h-5 text-emerald-600" />;
    return <ClipboardList className="w-5 h-5 text-slate-600" />;
  };

  const filteredOrders = orders.filter(order => {
    if (!searchTerm) return true;
    const patientName = patients[order.patient_id] || '';
    return order.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
           patientName.toLowerCase().includes(searchTerm.toLowerCase());
  });

  const labOrders = filteredOrders.filter(o => o.order_type === 'lab');
  const imagingOrders = filteredOrders.filter(o => o.order_type === 'imaging');
  const medOrders = filteredOrders.filter(o => o.order_type === 'medication');
  const pendingCount = orders.filter(o => o.status === 'pending').length;
  const completedCount = orders.filter(o => o.status === 'completed').length;
  const statCount = orders.filter(o => o.priority === 'stat').length;

  const OrderCard = ({ order }) => (
    <div 
      className="p-4 rounded-lg border border-slate-200 hover:border-sky-200 transition-colors"
      data-testid={'order-card-' + order.id}
    >
      <div className="flex items-start justify-between">
        <div className="flex gap-3">
          <div className="mt-1">{getOrderIcon(order.order_type)}</div>
          <div>
            <p className="font-medium text-slate-900">{order.description}</p>
            <p className="text-sm text-slate-500">
              Patient: {patients[order.patient_id] || 'Unknown'}
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Ordered by {order.ordered_by_name} - {formatDateTime(order.created_at)}
            </p>
            {order.diagnosis && (
              <p className="text-sm text-slate-600 mt-2">
                <span className="font-medium">Dx:</span> {order.diagnosis}
              </p>
            )}
            {order.result && (
              <div className="mt-2 p-2 bg-emerald-50 rounded border border-emerald-100">
                <p className="text-sm text-emerald-800">
                  <span className="font-medium">Result:</span> {order.result}
                </p>
              </div>
            )}
          </div>
        </div>
        <div className="flex flex-col items-end gap-2">
          <div className="flex items-center gap-2">
            <Badge className={order.priority === 'stat' ? 'bg-red-100 text-red-700' : order.priority === 'urgent' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-700'}>
              {order.priority}
            </Badge>
            <Badge className={getStatusColor(order.status)}>{order.status}</Badge>
          </div>
          {order.status !== 'completed' && order.status !== 'cancelled' && (
            <Select onValueChange={(v) => handleStatusChange(order.id, v)}>
              <SelectTrigger className="w-[140px] h-8 text-sm" data-testid={'order-status-' + order.id}>
                <SelectValue placeholder="Update status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="cancelled">Cancelled</SelectItem>
              </SelectContent>
            </Select>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6 animate-fade-in" data-testid="orders-page">
      <div>
        <h1 className="text-3xl font-bold text-slate-900" style={{ fontFamily: 'Manrope' }}>
          Orders
        </h1>
        <p className="text-slate-500 mt-1">Manage lab, imaging, and medication orders</p>
      </div>

      <Card>
        <CardContent className="py-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
              <Input 
                placeholder="Search orders or patients..."
                className="pl-10"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                data-testid="order-search"
              />
            </div>
            <Select value={filter} onValueChange={setFilter}>
              <SelectTrigger className="w-[180px]" data-testid="order-filter">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Orders</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="cancelled">Cancelled</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
              <Clock className="w-5 h-5 text-amber-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{pendingCount}</p>
              <p className="text-sm text-slate-500">Pending</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
              <FlaskConical className="w-5 h-5 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{labOrders.length}</p>
              <p className="text-sm text-slate-500">Lab Orders</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <Scan className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{imagingOrders.length}</p>
              <p className="text-sm text-slate-500">Imaging</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
              <Check className="w-5 h-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{completedCount}</p>
              <p className="text-sm text-slate-500">Completed</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all" data-testid="tab-all-orders">All ({filteredOrders.length})</TabsTrigger>
          <TabsTrigger value="lab" data-testid="tab-lab-orders">Labs ({labOrders.length})</TabsTrigger>
          <TabsTrigger value="imaging" data-testid="tab-imaging-orders">Imaging ({imagingOrders.length})</TabsTrigger>
          <TabsTrigger value="medication" data-testid="tab-med-orders">Medications ({medOrders.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>All Orders</CardTitle>
              <CardDescription>{filteredOrders.length} total orders</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-3">
                  <Skeleton className="h-24 w-full" />
                  <Skeleton className="h-24 w-full" />
                  <Skeleton className="h-24 w-full" />
                </div>
              ) : filteredOrders.length === 0 ? (
                <div className="text-center py-12 text-slate-500">
                  <ClipboardList className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p className="text-lg font-medium">No orders found</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {filteredOrders.map(order => <OrderCard key={order.id} order={order} />)}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="lab" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FlaskConical className="w-5 h-5 text-purple-600" /> Lab Orders
              </CardTitle>
            </CardHeader>
            <CardContent>
              {labOrders.length === 0 ? (
                <p className="text-center py-8 text-slate-500">No lab orders</p>
              ) : (
                <div className="space-y-3">
                  {labOrders.map(order => <OrderCard key={order.id} order={order} />)}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="imaging" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Scan className="w-5 h-5 text-blue-600" /> Imaging Orders
              </CardTitle>
            </CardHeader>
            <CardContent>
              {imagingOrders.length === 0 ? (
                <p className="text-center py-8 text-slate-500">No imaging orders</p>
              ) : (
                <div className="space-y-3">
                  {imagingOrders.map(order => <OrderCard key={order.id} order={order} />)}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="medication" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Pill className="w-5 h-5 text-emerald-600" /> Medication Orders
              </CardTitle>
            </CardHeader>
            <CardContent>
              {medOrders.length === 0 ? (
                <p className="text-center py-8 text-slate-500">No medication orders</p>
              ) : (
                <div className="space-y-3">
                  {medOrders.map(order => <OrderCard key={order.id} order={order} />)}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
