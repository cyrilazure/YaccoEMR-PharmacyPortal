import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import { dashboardAPI, patientAPI, appointmentsAPI, ordersAPI } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Input } from '@/components/ui/input';
import { formatDate, formatTime, getRoleDisplayName, getStatusColor, calculateAge } from '@/lib/utils';
import { toast } from 'sonner';
import { 
  Users, Calendar, ClipboardList, FileText, ArrowRight, 
  Activity, Clock, TrendingUp, UserPlus, AlertCircle,
  Video, BarChart3, Search, Hash, IdCard, Phone, Stethoscope
} from 'lucide-react';

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [recentPatients, setRecentPatients] = useState([]);
  const [todayAppointments, setTodayAppointments] = useState([]);
  const [pendingOrders, setPendingOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, patientsRes, ordersRes] = await Promise.all([
        dashboardAPI.getStats(),
        patientAPI.getAll(),
        ordersAPI.getAll({ status: 'pending' })
      ]);
      
      setStats(statsRes.data);
      setRecentPatients(patientsRes.data.slice(0, 5));
      setPendingOrders(ordersRes.data.slice(0, 5));
      
      // Get today's appointments
      const today = new Date().toISOString().split('T')[0];
      const apptsRes = await appointmentsAPI.getAll({ date: today });
      setTodayAppointments(apptsRes.data.slice(0, 5));
    } catch (err) {
      console.error('Dashboard fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ title, value, icon: Icon, trend, color }) => (
    <Card className="hover-card">
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
    <div className="space-y-6 animate-fade-in" data-testid="dashboard-page">
      {/* Welcome Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900" style={{ fontFamily: 'Manrope' }}>
            Welcome back, {user?.first_name}
          </h1>
          <p className="text-slate-500 mt-1">
            {getRoleDisplayName(user?.role)} Dashboard • {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>
        <Link to="/patients">
          <Button className="gap-2 bg-sky-600 hover:bg-sky-700" data-testid="new-patient-btn">
            <UserPlus className="w-4 h-4" /> New Patient
          </Button>
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard 
          title="Total Patients" 
          value={stats?.total_patients || 0} 
          icon={Users} 
          color="bg-sky-100 text-sky-600"
        />
        <StatCard 
          title="Today's Appointments" 
          value={stats?.today_appointments || 0} 
          icon={Calendar} 
          color="bg-amber-100 text-amber-600"
        />
        <StatCard 
          title="Pending Orders" 
          value={stats?.pending_orders || 0} 
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

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upcoming Appointments */}
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle style={{ fontFamily: 'Manrope' }}>Today's Schedule</CardTitle>
              <CardDescription>Your appointments for today</CardDescription>
            </div>
            <Link to="/appointments">
              <Button variant="ghost" size="sm" className="gap-1 text-sky-600">
                View All <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3">
                {[1, 2, 3].map(i => (
                  <Skeleton key={i} className="h-16 w-full" />
                ))}
              </div>
            ) : todayAppointments.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                <Calendar className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No appointments scheduled for today</p>
              </div>
            ) : (
              <div className="space-y-3">
                {todayAppointments.map((appt) => (
                  <div 
                    key={appt.id} 
                    className="flex items-center justify-between p-4 rounded-lg border border-slate-200 hover:border-sky-200 hover:bg-sky-50/50 transition-colors"
                    data-testid={`appointment-${appt.id}`}
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center">
                        <Clock className="w-5 h-5 text-slate-600" />
                      </div>
                      <div>
                        <p className="font-medium text-slate-900">{appt.patient_name || 'Patient'}</p>
                        <p className="text-sm text-slate-500">
                          {formatTime(appt.start_time)} - {formatTime(appt.end_time)} • {appt.appointment_type}
                        </p>
                      </div>
                    </div>
                    <Badge className={getStatusColor(appt.status)}>{appt.status}</Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Pending Orders */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle style={{ fontFamily: 'Manrope' }}>Pending Orders</CardTitle>
              <CardDescription>Orders awaiting action</CardDescription>
            </div>
            <Link to="/orders">
              <Button variant="ghost" size="sm" className="gap-1 text-sky-600">
                View All <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3">
                {[1, 2, 3].map(i => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : pendingOrders.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                <ClipboardList className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No pending orders</p>
              </div>
            ) : (
              <div className="space-y-2">
                {pendingOrders.map((order) => (
                  <div 
                    key={order.id} 
                    className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-100"
                    data-testid={`order-${order.id}`}
                  >
                    <div className="flex items-center gap-3">
                      <AlertCircle className="w-4 h-4 text-amber-500" />
                      <div>
                        <p className="text-sm font-medium text-slate-900 truncate max-w-[150px]">
                          {order.description}
                        </p>
                        <p className="text-xs text-slate-500">{order.order_type}</p>
                      </div>
                    </div>
                    <Badge variant="outline" className="text-xs">{order.priority}</Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Patients */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <div>
            <CardTitle style={{ fontFamily: 'Manrope' }}>Recent Patients</CardTitle>
            <CardDescription>Recently added or updated patient records</CardDescription>
          </div>
          <Link to="/patients">
            <Button variant="ghost" size="sm" className="gap-1 text-sky-600">
              View All <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              {[1, 2, 3, 4, 5].map(i => (
                <Skeleton key={i} className="h-24 w-full" />
              ))}
            </div>
          ) : recentPatients.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              <Users className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No patients registered yet</p>
              <Link to="/patients">
                <Button variant="outline" className="mt-4">Add First Patient</Button>
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              {recentPatients.map((patient) => (
                <Link 
                  key={patient.id} 
                  to={`/patients/${patient.id}`}
                  className="block"
                  data-testid={`patient-card-${patient.id}`}
                >
                  <div className="p-4 rounded-lg border border-slate-200 hover:border-sky-300 hover:shadow-md transition-all">
                    <div className="w-10 h-10 rounded-full bg-sky-100 text-sky-700 flex items-center justify-center mb-3 font-semibold">
                      {patient.first_name?.[0]}{patient.last_name?.[0]}
                    </div>
                    <p className="font-medium text-slate-900 truncate">
                      {patient.first_name} {patient.last_name}
                    </p>
                    <p className="text-xs text-slate-500">
                      {calculateAge(patient.date_of_birth)} yrs • {patient.gender}
                    </p>
                    <p className="text-xs text-slate-400 mt-1">{patient.mrn}</p>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
