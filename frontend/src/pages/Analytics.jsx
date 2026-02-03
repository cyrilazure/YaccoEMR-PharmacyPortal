import { useState, useEffect } from 'react';
import { useAuth } from '@/lib/auth';
import { dashboardAPI, patientAPI, ordersAPI, appointmentsAPI } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';
import { Users, Calendar, ClipboardList, FileText, TrendingUp, Activity } from 'lucide-react';

export default function Analytics() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [patients, setPatients] = useState([]);
  const [orders, setOrders] = useState([]);

  useEffect(() => {
    fetchAnalyticsData();
  }, []);

  const fetchAnalyticsData = async () => {
    try {
      const [statsRes, patientsRes, ordersRes] = await Promise.all([
        dashboardAPI.getStats(),
        patientAPI.getAll(),
        ordersAPI.getAll({})
      ]);
      
      setStats(statsRes.data);
      setPatients(patientsRes.data);
      setOrders(ordersRes.data);
    } catch (err) {
      console.error('Analytics fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Calculate order stats
  const ordersByType = [
    { name: 'Lab', value: orders.filter(o => o.order_type === 'lab').length, color: '#8b5cf6' },
    { name: 'Imaging', value: orders.filter(o => o.order_type === 'imaging').length, color: '#3b82f6' },
    { name: 'Medication', value: orders.filter(o => o.order_type === 'medication').length, color: '#10b981' },
  ];

  const ordersByStatus = [
    { name: 'Pending', value: orders.filter(o => o.status === 'pending').length, color: '#f59e0b' },
    { name: 'In Progress', value: orders.filter(o => o.status === 'in_progress').length, color: '#3b82f6' },
    { name: 'Completed', value: orders.filter(o => o.status === 'completed').length, color: '#10b981' },
    { name: 'Cancelled', value: orders.filter(o => o.status === 'cancelled').length, color: '#94a3b8' },
  ];

  // Patient demographics
  const patientsByGender = [
    { name: 'Male', value: patients.filter(p => p.gender === 'male').length, color: '#3b82f6' },
    { name: 'Female', value: patients.filter(p => p.gender === 'female').length, color: '#ec4899' },
    { name: 'Other', value: patients.filter(p => p.gender === 'other').length, color: '#8b5cf6' },
  ];

  // Mock weekly data
  const weeklyPatients = [
    { day: 'Mon', patients: 12 },
    { day: 'Tue', patients: 18 },
    { day: 'Wed', patients: 15 },
    { day: 'Thu', patients: 22 },
    { day: 'Fri', patients: 20 },
    { day: 'Sat', patients: 8 },
    { day: 'Sun', patients: 5 },
  ];

  const StatCard = ({ title, value, icon: Icon, color, trend }) => (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-slate-500">{title}</p>
            {loading ? (
              <Skeleton className="h-8 w-20 mt-1" />
            ) : (
              <p className="text-3xl font-bold text-slate-900 mt-1" style={{ fontFamily: 'Manrope' }}>
                {value}
              </p>
            )}
            {trend && (
              <p className="text-xs text-emerald-600 mt-1 flex items-center gap-1">
                <TrendingUp className="w-3 h-3" /> {trend}
              </p>
            )}
          </div>
          <div className={`w-12 h-12 rounded-xl ${color} flex items-center justify-center`}>
            <Icon className="w-6 h-6" />
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6 animate-fade-in" data-testid="analytics-page">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900" style={{ fontFamily: 'Manrope' }}>
          Analytics
        </h1>
        <p className="text-slate-500 mt-1">Clinical and operational insights</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard 
          title="Total Patients" 
          value={stats?.total_patients || patients.length} 
          icon={Users} 
          color="bg-sky-100 text-sky-600"
          trend="+12% this month"
        />
        <StatCard 
          title="Today's Appointments" 
          value={stats?.today_appointments || 0} 
          icon={Calendar} 
          color="bg-amber-100 text-amber-600"
        />
        <StatCard 
          title="Pending Orders" 
          value={stats?.pending_orders || orders.filter(o => o.status === 'pending').length} 
          icon={ClipboardList} 
          color="bg-emerald-100 text-emerald-600"
        />
        <StatCard 
          title="Clinical Notes" 
          value={stats?.recent_notes || 0} 
          icon={FileText} 
          color="bg-purple-100 text-purple-600"
        />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Orders by Type */}
        <Card>
          <CardHeader>
            <CardTitle>Orders by Type</CardTitle>
            <CardDescription>Distribution of order types</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-64 w-full" />
            ) : (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={ordersByType}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {ordersByType.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
            <div className="flex justify-center gap-6 mt-4">
              {ordersByType.map((item) => (
                <div key={item.name} className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                  <span className="text-sm text-slate-600">{item.name}: {item.value}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Orders by Status */}
        <Card>
          <CardHeader>
            <CardTitle>Order Status</CardTitle>
            <CardDescription>Current order pipeline</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-64 w-full" />
            ) : (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={ordersByStatus}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 12 }} />
                  <YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {ordersByStatus.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Patient Demographics */}
        <Card>
          <CardHeader>
            <CardTitle>Patient Demographics</CardTitle>
            <CardDescription>Gender distribution</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-64 w-full" />
            ) : (
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie
                    data={patientsByGender}
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {patientsByGender.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Weekly Patient Visits */}
        <Card>
          <CardHeader>
            <CardTitle>Weekly Patient Visits</CardTitle>
            <CardDescription>Patient visit trend</CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-64 w-full" />
            ) : (
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={weeklyPatients}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="day" tick={{ fill: '#64748b', fontSize: 12 }} />
                  <YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
                  <Tooltip />
                  <Line 
                    type="monotone" 
                    dataKey="patients" 
                    stroke="#0284c7" 
                    strokeWidth={2}
                    dot={{ fill: '#0284c7', strokeWidth: 2 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-100 flex items-center justify-center">
                <Activity className="w-6 h-6 text-emerald-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Order Completion Rate</p>
                <p className="text-2xl font-bold text-slate-900">
                  {orders.length > 0 
                    ? Math.round((orders.filter(o => o.status === 'completed').length / orders.length) * 100)
                    : 0}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-red-100 flex items-center justify-center">
                <ClipboardList className="w-6 h-6 text-red-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">STAT Orders</p>
                <p className="text-2xl font-bold text-slate-900">
                  {orders.filter(o => o.priority === 'stat').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-blue-100 flex items-center justify-center">
                <Users className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Avg Patients/Day</p>
                <p className="text-2xl font-bold text-slate-900">
                  {Math.round(weeklyPatients.reduce((a, b) => a + b.patients, 0) / 7)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
