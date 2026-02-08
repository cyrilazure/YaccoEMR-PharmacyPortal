import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import {
  CheckCircle, Clock, Package, Truck, MapPin, Phone,
  Pill, Building2, User, Calendar, Search, Loader2,
  ChevronRight, AlertCircle, Home, RefreshCw, QrCode,
  Activity, Bell
} from 'lucide-react';

const API_BASE = process.env.REACT_APP_BACKEND_URL || '';

// Status step component
function StatusStep({ step, label, description, completed, current, timestamp }) {
  return (
    <div className={`flex items-start gap-4 ${completed ? 'opacity-100' : 'opacity-50'}`}>
      {/* Step indicator */}
      <div className="flex flex-col items-center">
        <div className={`
          w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all
          ${current ? 'bg-blue-600 border-blue-600 text-white animate-pulse' : 
            completed ? 'bg-green-600 border-green-600 text-white' : 
            'bg-white border-slate-300 text-slate-400'}
        `}>
          {completed && !current ? (
            <CheckCircle className="w-5 h-5" />
          ) : current ? (
            <Clock className="w-5 h-5 animate-spin" />
          ) : (
            <span className="font-semibold">{step}</span>
          )}
        </div>
        {step < 5 && (
          <div className={`w-0.5 h-16 ${completed ? 'bg-green-600' : 'bg-slate-200'}`} />
        )}
      </div>
      
      {/* Step content */}
      <div className="flex-1 pb-8">
        <h4 className={`font-semibold ${current ? 'text-blue-600' : completed ? 'text-green-600' : 'text-slate-500'}`}>
          {label}
        </h4>
        <p className="text-sm text-slate-500">{description}</p>
        {timestamp && (
          <p className="text-xs text-slate-400 mt-1">
            {new Date(timestamp).toLocaleString()}
          </p>
        )}
        {current && (
          <Badge className="mt-2 bg-blue-100 text-blue-700 animate-pulse">
            Current Status
          </Badge>
        )}
      </div>
    </div>
  );
}

// Main tracking page component
export default function PrescriptionTracking() {
  const { trackingCode: urlTrackingCode } = useParams();
  const navigate = useNavigate();
  
  const [trackingCode, setTrackingCode] = useState(urlTrackingCode || '');
  const [loading, setLoading] = useState(false);
  const [trackingData, setTrackingData] = useState(null);
  const [error, setError] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(false);

  // Fetch tracking data
  const fetchTrackingData = async (code) => {
    if (!code) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/api/pharmacy-portal/public/prescription/track/${encodeURIComponent(code)}`);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Prescription not found');
      }
      
      setTrackingData(data);
      
      // Update URL if not already there
      if (!urlTrackingCode) {
        navigate(`/track/${code}`, { replace: true });
      }
    } catch (err) {
      setError(err.message);
      setTrackingData(null);
    } finally {
      setLoading(false);
    }
  };

  // Auto-fetch if tracking code in URL
  useEffect(() => {
    if (urlTrackingCode) {
      setTrackingCode(urlTrackingCode);
      fetchTrackingData(urlTrackingCode);
    }
  }, [urlTrackingCode]);

  // Auto-refresh every 30 seconds if enabled
  useEffect(() => {
    if (!autoRefresh || !trackingCode) return;
    
    const interval = setInterval(() => {
      fetchTrackingData(trackingCode);
    }, 30000);
    
    return () => clearInterval(interval);
  }, [autoRefresh, trackingCode]);

  // Handle search
  const handleSearch = (e) => {
    e.preventDefault();
    if (trackingCode.trim()) {
      fetchTrackingData(trackingCode.trim());
    }
  };

  // Get status color
  const getStatusColor = (status) => {
    const colors = {
      sent: 'bg-blue-100 text-blue-700',
      received: 'bg-indigo-100 text-indigo-700',
      processing: 'bg-yellow-100 text-yellow-700',
      ready: 'bg-green-100 text-green-700',
      out_for_delivery: 'bg-purple-100 text-purple-700',
      dispensed: 'bg-emerald-100 text-emerald-700',
      cancelled: 'bg-red-100 text-red-700'
    };
    return colors[status] || 'bg-slate-100 text-slate-700';
  };

  // Get status icon
  const StatusIcon = ({ status }) => {
    const icons = {
      sent: Package,
      received: CheckCircle,
      processing: Clock,
      ready: CheckCircle,
      out_for_delivery: Truck,
      dispensed: CheckCircle,
      cancelled: AlertCircle
    };
    const Icon = icons[status] || Clock;
    return <Icon className="w-5 h-5" />;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100" data-testid="prescription-tracking-page">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900">Prescription Tracking</h1>
                <p className="text-xs text-slate-500">Track your medication status</p>
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={() => navigate('/')}>
              <Home className="w-4 h-4 mr-2" />
              Home
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Search Section */}
        <Card className="mb-8 border-blue-200 bg-white/80 backdrop-blur">
          <CardHeader className="text-center">
            <CardTitle className="flex items-center justify-center gap-2">
              <QrCode className="w-6 h-6 text-blue-600" />
              Track Your Prescription
            </CardTitle>
            <CardDescription>
              Enter your prescription number or tracking code
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSearch} className="flex gap-3">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <Input
                  type="text"
                  placeholder="e.g., RX-2026-XXXXX or tracking code"
                  value={trackingCode}
                  onChange={(e) => setTrackingCode(e.target.value)}
                  className="pl-10 h-12 text-lg"
                  data-testid="tracking-input"
                />
              </div>
              <Button type="submit" className="h-12 px-6 bg-blue-600 hover:bg-blue-700" disabled={loading}>
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Track'}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Error Message */}
        {error && (
          <Card className="mb-8 border-red-200 bg-red-50">
            <CardContent className="pt-6">
              <div className="flex items-center gap-3 text-red-700">
                <AlertCircle className="w-6 h-6" />
                <div>
                  <p className="font-semibold">Prescription Not Found</p>
                  <p className="text-sm">{error}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Tracking Results */}
        {trackingData && (
          <div className="space-y-6">
            {/* Status Overview Card */}
            <Card className="border-2 border-blue-200 overflow-hidden">
              <div className={`h-2 ${
                trackingData.current_status === 'ready' ? 'bg-gradient-to-r from-green-500 to-emerald-500' :
                trackingData.current_status === 'dispensed' ? 'bg-gradient-to-r from-emerald-500 to-teal-500' :
                'bg-gradient-to-r from-blue-500 to-indigo-500'
              }`} />
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm text-slate-500">Prescription Number</p>
                    <CardTitle className="text-2xl font-mono">{trackingData.rx_number}</CardTitle>
                  </div>
                  <Badge className={`${getStatusColor(trackingData.current_status)} text-lg px-4 py-2`}>
                    <StatusIcon status={trackingData.current_status} />
                    <span className="ml-2 capitalize">{trackingData.current_status?.replace(/_/g, ' ')}</span>
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-3 gap-4 mb-6">
                  <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                    <User className="w-5 h-5 text-slate-400" />
                    <div>
                      <p className="text-xs text-slate-400">Patient</p>
                      <p className="font-medium">{trackingData.patient_name}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                    <Building2 className="w-5 h-5 text-slate-400" />
                    <div>
                      <p className="text-xs text-slate-400">Hospital</p>
                      <p className="font-medium">{trackingData.hospital_name || 'N/A'}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                    <Calendar className="w-5 h-5 text-slate-400" />
                    <div>
                      <p className="text-xs text-slate-400">Date</p>
                      <p className="font-medium">
                        {trackingData.created_at ? new Date(trackingData.created_at).toLocaleDateString() : 'N/A'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="mb-6">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-500">Progress</span>
                    <span className="text-sm font-medium text-blue-600">
                      {trackingData.current_step} of {trackingData.total_steps} steps
                    </span>
                  </div>
                  <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-blue-500 to-green-500 rounded-full transition-all duration-500"
                      style={{ width: `${(trackingData.current_step / trackingData.total_steps) * 100}%` }}
                    />
                  </div>
                </div>

                {/* Ready Alert */}
                {trackingData.current_status === 'ready' && (
                  <div className="p-4 bg-green-50 border border-green-200 rounded-lg mb-6">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                        <CheckCircle className="w-7 h-7 text-green-600" />
                      </div>
                      <div>
                        <p className="font-semibold text-green-800">Ready for Pickup!</p>
                        <p className="text-sm text-green-600">Your prescription is ready at the pharmacy</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Auto-refresh toggle */}
                <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                  <div className="flex items-center gap-2">
                    <Bell className="w-4 h-4 text-blue-600" />
                    <span className="text-sm text-blue-700">Auto-refresh status</span>
                  </div>
                  <Button 
                    variant={autoRefresh ? "default" : "outline"} 
                    size="sm"
                    onClick={() => setAutoRefresh(!autoRefresh)}
                    className={autoRefresh ? 'bg-blue-600' : ''}
                  >
                    <RefreshCw className={`w-4 h-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
                    {autoRefresh ? 'On' : 'Off'}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Timeline */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-blue-600" />
                  Tracking Timeline
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="pl-2">
                  {trackingData.timeline?.map((step) => (
                    <StatusStep
                      key={step.step}
                      step={step.step}
                      label={step.label}
                      description={step.description}
                      completed={step.completed}
                      current={step.current}
                      timestamp={step.timestamp}
                    />
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Medications */}
            {trackingData.medications?.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Pill className="w-5 h-5 text-blue-600" />
                    Medications ({trackingData.medications.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {trackingData.medications.map((med, index) => (
                      <div key={index} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                            <Pill className="w-5 h-5 text-blue-600" />
                          </div>
                          <div>
                            <p className="font-medium">{med.name}</p>
                            {med.dosage && <p className="text-sm text-slate-500">{med.dosage}</p>}
                          </div>
                        </div>
                        <Badge variant="outline">Qty: {med.quantity}</Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Pharmacy Info */}
            {trackingData.pharmacy && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MapPin className="w-5 h-5 text-blue-600" />
                    Pharmacy Location
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="p-4 bg-slate-50 rounded-lg">
                    <h4 className="font-semibold text-lg mb-2">{trackingData.pharmacy.name}</h4>
                    <div className="space-y-2 text-sm text-slate-600">
                      {trackingData.pharmacy.address && (
                        <p className="flex items-center gap-2">
                          <MapPin className="w-4 h-4" />
                          {trackingData.pharmacy.address}, {trackingData.pharmacy.town}
                        </p>
                      )}
                      <p className="flex items-center gap-2">
                        <Building2 className="w-4 h-4" />
                        {trackingData.pharmacy.region}
                      </p>
                      {trackingData.pharmacy.phone && (
                        <p className="flex items-center gap-2">
                          <Phone className="w-4 h-4" />
                          {trackingData.pharmacy.phone}
                        </p>
                      )}
                    </div>
                    {trackingData.delivery_method === 'delivery' && trackingData.delivery_address && (
                      <div className="mt-4 p-3 bg-purple-50 rounded-lg border border-purple-200">
                        <p className="flex items-center gap-2 text-purple-700 font-medium">
                          <Truck className="w-4 h-4" />
                          Delivery to: {trackingData.delivery_address}
                        </p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Empty State - No search yet */}
        {!trackingData && !error && !loading && (
          <Card className="text-center py-12">
            <CardContent>
              <Package className="w-16 h-16 mx-auto mb-4 text-slate-300" />
              <h3 className="text-lg font-semibold text-slate-700 mb-2">Track Your Prescription</h3>
              <p className="text-slate-500 max-w-md mx-auto">
                Enter your prescription number (e.g., RX-2026-XXXXX) to see the current status 
                of your medication. You can find this number on your prescription receipt.
              </p>
            </CardContent>
          </Card>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 text-white py-6 mt-12">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <p className="text-sm text-slate-400">
            Yacco Health - Ghana Healthcare Network
          </p>
          <p className="text-xs text-slate-500 mt-1">
            Need help? Contact your pharmacy or hospital
          </p>
        </div>
      </footer>
    </div>
  );
}
