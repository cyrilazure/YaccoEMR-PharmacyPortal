import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import { hospitalDashboardAPI } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Select, SelectContent, SelectItem, 
  SelectTrigger, SelectValue 
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { toast } from 'sonner';
import { 
  Users, Calendar, Activity, Bell, Building2, MapPin,
  Stethoscope, ClipboardList, DollarSign, Clock,
  ChevronRight, RefreshCw, Loader2, AlertCircle,
  LayoutDashboard, UserCog, Pill, TestTube
} from 'lucide-react';

// Role portal info
const ROLE_PORTALS = {
  physician: { label: 'Physician Portal', icon: Stethoscope, color: 'emerald' },
  nurse: { label: 'Nurse Station', icon: Activity, color: 'blue' },
  scheduler: { label: 'Scheduling', icon: Calendar, color: 'purple' },
  biller: { label: 'Billing', icon: DollarSign, color: 'orange' },
  hospital_admin: { label: 'Admin Dashboard', icon: UserCog, color: 'slate' },
  admin: { label: 'Admin Dashboard', icon: UserCog, color: 'slate' },
  lab_tech: { label: 'Lab Portal', icon: TestTube, color: 'cyan' },
  pharmacist: { label: 'Pharmacy', icon: Pill, color: 'pink' },
};

export default function HospitalMainDashboard() {
  const { hospitalId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const effectiveHospitalId = hospitalId || user?.organization_id;
  
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [locations, setLocations] = useState([]);

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }
    
    if (user.role === 'super_admin') return;
    
    if (effectiveHospitalId && user.organization_id !== effectiveHospitalId) {
      toast.error('Not authorized for this hospital');
      navigate('/');
    }
  }, [user, effectiveHospitalId, navigate]);

  const fetchData = useCallback(async () => {
    if (!effectiveHospitalId) return;
    
    try {
      setLoading(true);
      const [dashboardRes, locationsRes] = await Promise.all([
        hospitalDashboardAPI.getDashboard(effectiveHospitalId, selectedLocation),
        hospitalDashboardAPI.getLocations(effectiveHospitalId)
      ]);
      
      setDashboard(dashboardRes.data);
      setLocations(locationsRes.data.locations || []);
    } catch (err) {
      console.error('Error fetching dashboard:', err);
      toast.error('Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }, [effectiveHospitalId, selectedLocation]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const userRole = user?.role || 'physician';
  const portalInfo = ROLE_PORTALS[userRole] || ROLE_PORTALS.physician;
  const PortalIcon = portalInfo.icon;

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Building2 className="w-6 h-6 text-emerald-600" />
            {dashboard?.hospital?.name || 'Hospital Dashboard'}
          </h1>
          <p className="text-gray-500 flex items-center gap-2 mt-1">
            <MapPin className="w-4 h-4" />
            {dashboard?.hospital?.city}
            {dashboard?.location && (
              <Badge variant="outline">{dashboard.location.name}</Badge>
            )}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {locations.length > 1 && (
            <Select
              value={selectedLocation || 'all'}
              onValueChange={(v) => setSelectedLocation(v === 'all' ? null : v)}
            >
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="All Locations" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Locations</SelectItem>
                {locations.map(loc => (
                  <SelectItem key={loc.id} value={loc.id}>{loc.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          <Button onClick={fetchData} variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Welcome Banner */}
      <Card className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white border-0">
        <CardContent className="py-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold mb-1">
                Welcome, {dashboard?.user?.name || 'User'}
              </h2>
              <p className="text-emerald-100">
                Role: <span className="capitalize">{userRole.replace('_', ' ')}</span>
              </p>
            </div>
            <Link to={`/hospital/${effectiveHospitalId}/${dashboard?.user?.portal || 'dashboard'}`}>
              <Button variant="secondary" className="gap-2">
                <PortalIcon className="w-4 h-4" />
                Go to {portalInfo.label}
                <ChevronRight className="w-4 h-4" />
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Today's Appointments</p>
                <p className="text-3xl font-bold text-emerald-600">
                  {dashboard?.stats?.todays_appointments || 0}
                </p>
              </div>
              <Calendar className="w-8 h-8 text-emerald-200" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Active Patients</p>
                <p className="text-3xl font-bold text-blue-600">
                  {dashboard?.stats?.active_patients || 0}
                </p>
              </div>
              <Users className="w-8 h-8 text-blue-200" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Pending Orders</p>
                <p className="text-3xl font-bold text-orange-600">
                  {dashboard?.stats?.pending_orders || 0}
                </p>
              </div>
              <ClipboardList className="w-8 h-8 text-orange-200" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total Staff</p>
                <p className="text-3xl font-bold text-purple-600">
                  {dashboard?.stats?.total_users || 0}
                </p>
              </div>
              <Users className="w-8 h-8 text-purple-200" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Quick Links */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <LayoutDashboard className="w-5 h-5 text-emerald-600" />
              Quick Access
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {dashboard?.quick_links?.map((link, idx) => (
                <Link key={idx} to={link.url}>
                  <Button variant="outline" className="w-full justify-start gap-2">
                    <ChevronRight className="w-4 h-4" />
                    {link.label}
                  </Button>
                </Link>
              ))}
              
              {/* Role-specific portals */}
              <div className="pt-4 border-t mt-4">
                <p className="text-sm text-gray-500 mb-2">Portals</p>
                {Object.entries(ROLE_PORTALS).map(([role, info]) => {
                  const Icon = info.icon;
                  return (
                    <Link 
                      key={role} 
                      to={`/hospital/${effectiveHospitalId}/${role === 'hospital_admin' ? 'admin' : role}`}
                    >
                      <Button 
                        variant="ghost" 
                        className={`w-full justify-start gap-2 ${userRole === role ? 'bg-emerald-50 text-emerald-700' : ''}`}
                      >
                        <Icon className="w-4 h-4" />
                        {info.label}
                      </Button>
                    </Link>
                  );
                })}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Departments */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-lg">Departments</CardTitle>
            <CardDescription>Active departments in this location</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[300px]">
              <div className="space-y-3">
                {dashboard?.departments?.map((dept) => (
                  <Link 
                    key={dept.id} 
                    to={`/hospital/${effectiveHospitalId}/department/${dept.id}`}
                  >
                    <div className="p-3 rounded-lg border hover:bg-gray-50 transition-colors">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">{dept.name}</p>
                          <p className="text-xs text-gray-500">{dept.code}</p>
                        </div>
                        <div className="text-right">
                          <Badge variant="secondary">{dept.user_count || 0} staff</Badge>
                        </div>
                      </div>
                    </div>
                  </Link>
                ))}
                {(!dashboard?.departments || dashboard.departments.length === 0) && (
                  <p className="text-center text-gray-500 py-8">No departments found</p>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Notifications & Activity */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Bell className="w-5 h-5 text-emerald-600" />
              Notifications
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[300px]">
              <div className="space-y-3">
                {dashboard?.notifications?.map((notif, idx) => (
                  <Alert key={idx} className="py-2">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription className="text-sm">
                      {notif.message || notif.title}
                    </AlertDescription>
                  </Alert>
                ))}
                {(!dashboard?.notifications || dashboard.notifications.length === 0) && (
                  <div className="text-center text-gray-500 py-8">
                    <Bell className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                    <p>No new notifications</p>
                  </div>
                )}
                
                {/* Recent Activity */}
                <div className="pt-4 border-t">
                  <p className="text-sm font-medium text-gray-500 mb-3">Recent Activity</p>
                  {dashboard?.recent_activity?.slice(0, 5).map((activity, idx) => (
                    <div key={idx} className="flex items-start gap-2 py-2 border-b last:border-0">
                      <Activity className="w-4 h-4 text-gray-400 mt-1" />
                      <div>
                        <p className="text-sm">{activity.action?.replace('_', ' ')}</p>
                        <p className="text-xs text-gray-400">
                          {new Date(activity.timestamp).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {/* Locations Grid (if multiple) */}
      {locations.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <MapPin className="w-5 h-5 text-emerald-600" />
              Hospital Locations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {locations.map((loc) => (
                <Card key={loc.id} className="border">
                  <CardContent className="pt-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-medium">{loc.name}</h4>
                        <p className="text-sm text-gray-500">{loc.address}</p>
                        <div className="flex items-center gap-2 mt-2">
                          <Badge variant="outline" className="text-xs capitalize">
                            {loc.location_type?.replace('_', ' ')}
                          </Badge>
                          {loc.is_24_hour && (
                            <Badge className="bg-emerald-100 text-emerald-700 text-xs">24 Hour</Badge>
                          )}
                        </div>
                      </div>
                      <Badge>{loc.user_count || 0} staff</Badge>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
