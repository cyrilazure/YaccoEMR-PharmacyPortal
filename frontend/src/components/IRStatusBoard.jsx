import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import {
  RefreshCw, Clock, Heart, Play, Timer, CheckCircle,
  User, AlertTriangle, Activity, Zap, Monitor
} from 'lucide-react';
import api from '@/lib/api';

// IR API
const irAPI = {
  getDashboard: () => api.get('/interventional-radiology/dashboard'),
  getProcedures: (params) => api.get('/interventional-radiology/procedures', { params }),
  getSedationRecords: (procedureId) => api.get(`/interventional-radiology/sedation/${procedureId}`),
};

// Status Colors
const STATUS_COLORS = {
  scheduled: { bg: 'bg-blue-100', text: 'text-blue-800', border: 'border-blue-300' },
  pre_procedure: { bg: 'bg-yellow-100', text: 'text-yellow-800', border: 'border-yellow-300' },
  in_progress: { bg: 'bg-purple-100', text: 'text-purple-800', border: 'border-purple-400', pulse: true },
  recovery: { bg: 'bg-orange-100', text: 'text-orange-800', border: 'border-orange-300' },
  completed: { bg: 'bg-green-100', text: 'text-green-800', border: 'border-green-300' },
  cancelled: { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-300' },
};

// Status Icons
const STATUS_ICONS = {
  scheduled: Clock,
  pre_procedure: AlertTriangle,
  in_progress: Play,
  recovery: Timer,
  completed: CheckCircle,
};

// Procedure Room Card
function ProcedureRoomCard({ procedure, latestVitals, onSelect }) {
  const status = procedure?.status || 'empty';
  const colors = STATUS_COLORS[status] || STATUS_COLORS.scheduled;
  const StatusIcon = STATUS_ICONS[status] || Clock;

  if (!procedure) {
    return (
      <Card className="h-full border-2 border-dashed border-gray-200">
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center text-gray-400">
            <Monitor className="w-12 h-12 mx-auto mb-2 opacity-30" />
            <p>Room Available</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card 
      className={cn(
        "h-full border-2 transition-all cursor-pointer hover:shadow-lg",
        colors.border,
        colors.bg,
        colors.pulse && "animate-pulse"
      )}
      onClick={() => onSelect?.(procedure)}
      data-testid={`room-card-${procedure.id}`}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <Badge className={cn(colors.bg, colors.text, "border", colors.border)}>
            <StatusIcon className="w-3 h-3 mr-1" />
            {status.replace(/_/g, ' ').toUpperCase()}
          </Badge>
          <span className="text-xs font-mono text-gray-500">{procedure.case_number}</span>
        </div>
        <CardTitle className="text-lg mt-2">{procedure.patient_name}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div>
          <p className="font-medium text-sm">{procedure.procedure_description}</p>
          <p className="text-xs text-gray-600">{procedure.procedure_type?.replace(/_/g, ' ')}</p>
        </div>
        
        <div className="flex items-center gap-2 text-sm">
          <User className="w-4 h-4 text-gray-500" />
          <span className="text-gray-600">{procedure.attending_physician_name}</span>
        </div>

        <div className="flex gap-4 text-sm">
          <div>
            <span className="text-gray-500">Scheduled:</span>
            <span className="ml-1 font-mono">{procedure.scheduled_time}</span>
          </div>
          <div>
            <span className="text-gray-500">Est:</span>
            <span className="ml-1">{procedure.estimated_duration_minutes}min</span>
          </div>
        </div>

        {/* Vitals Display (for in-progress procedures) */}
        {status === 'in_progress' && latestVitals && (
          <div className="bg-white/80 rounded-lg p-3 border">
            <div className="flex items-center gap-2 mb-2">
              <Heart className="w-4 h-4 text-red-500" />
              <span className="text-xs font-medium">Latest Vitals</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-gray-500">HR:</span>
                <span className={cn("ml-1 font-mono", 
                  (latestVitals.heart_rate > 100 || latestVitals.heart_rate < 60) ? 'text-red-600 font-bold' : ''
                )}>
                  {latestVitals.heart_rate} bpm
                </span>
              </div>
              <div>
                <span className="text-gray-500">BP:</span>
                <span className={cn("ml-1 font-mono",
                  latestVitals.blood_pressure_systolic > 140 ? 'text-red-600 font-bold' : ''
                )}>
                  {latestVitals.blood_pressure_systolic}/{latestVitals.blood_pressure_diastolic}
                </span>
              </div>
              <div>
                <span className="text-gray-500">SpO2:</span>
                <span className={cn("ml-1 font-mono",
                  latestVitals.oxygen_saturation < 95 ? 'text-red-600 font-bold' : 'text-green-600'
                )}>
                  {latestVitals.oxygen_saturation}%
                </span>
              </div>
              <div>
                <span className="text-gray-500">RR:</span>
                <span className="ml-1 font-mono">{latestVitals.respiratory_rate}/min</span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Recovery Patient Card
function RecoveryPatientCard({ procedure }) {
  return (
    <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg border border-orange-200">
      <div>
        <p className="font-medium">{procedure.patient_name}</p>
        <p className="text-xs text-gray-600">{procedure.procedure_description}</p>
        <p className="text-xs text-gray-500">{procedure.case_number}</p>
      </div>
      <div className="text-right">
        <Badge className="bg-orange-100 text-orange-700">In Recovery</Badge>
        <p className="text-xs text-gray-500 mt-1">
          {procedure.attending_physician_name}
        </p>
      </div>
    </div>
  );
}

// Main Status Board Component
export default function IRStatusBoard({ 
  fullScreen = false,
  refreshInterval = 15000,  // 15 seconds default
  onSelectProcedure  // callback when a procedure is clicked
}) {
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);
  const [vitalsMap, setVitalsMap] = useState({});
  const [lastUpdated, setLastUpdated] = useState(new Date());

  // Fetch dashboard data
  const fetchData = useCallback(async () => {
    try {
      const response = await irAPI.getDashboard();
      setDashboard(response.data);
      setLastUpdated(new Date());
      
      // Fetch vitals for in-progress procedures
      const inProgress = response.data.in_progress || [];
      const vitalsPromises = inProgress.map(async (proc) => {
        try {
          const vitalsRes = await irAPI.getSedationRecords(proc.id);
          const records = vitalsRes.data.records || [];
          return { 
            id: proc.id, 
            vitals: records.length > 0 ? records[records.length - 1] : null 
          };
        } catch {
          return { id: proc.id, vitals: null };
        }
      });
      
      const vitalsResults = await Promise.all(vitalsPromises);
      const newVitalsMap = {};
      vitalsResults.forEach(({ id, vitals }) => {
        if (vitals) newVitalsMap[id] = vitals;
      });
      setVitalsMap(newVitalsMap);
      
    } catch (err) {
      console.error('Failed to fetch IR data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch and auto-refresh
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchData, refreshInterval]);

  // Get procedures by room (mock 4 rooms)
  const getRoomProcedures = () => {
    const inProgress = dashboard?.in_progress || [];
    const rooms = [null, null, null, null];
    inProgress.forEach((proc, idx) => {
      if (idx < 4) rooms[idx] = proc;
    });
    return rooms;
  };

  const rooms = getRoomProcedures();
  const recoveryPatients = dashboard?.in_recovery || [];
  const upcomingToday = (dashboard?.today_schedule || []).filter(p => p.status === 'scheduled').slice(0, 5);

  return (
    <div className={cn(
      "space-y-4",
      fullScreen && "fixed inset-0 bg-slate-100 p-6 z-50"
    )} data-testid="ir-status-board">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Activity className="w-7 h-7 text-purple-600" />
            IR Suite Status Board
          </h1>
          <p className="text-sm text-slate-500">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={fetchData} variant="outline" className="gap-2">
            <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="bg-purple-50 border-purple-200">
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-full bg-purple-200">
                <Play className="w-5 h-5 text-purple-700" />
              </div>
              <div>
                <p className="text-3xl font-bold text-purple-800">{dashboard?.in_progress?.length || 0}</p>
                <p className="text-sm text-purple-600">In Progress</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-orange-50 border-orange-200">
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-full bg-orange-200">
                <Timer className="w-5 h-5 text-orange-700" />
              </div>
              <div>
                <p className="text-3xl font-bold text-orange-800">{recoveryPatients.length}</p>
                <p className="text-sm text-orange-600">In Recovery</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-full bg-blue-200">
                <Clock className="w-5 h-5 text-blue-700" />
              </div>
              <div>
                <p className="text-3xl font-bold text-blue-800">{upcomingToday.length}</p>
                <p className="text-sm text-blue-600">Upcoming Today</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-green-50 border-green-200">
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-full bg-green-200">
                <CheckCircle className="w-5 h-5 text-green-700" />
              </div>
              <div>
                <p className="text-3xl font-bold text-green-800">{dashboard?.status_counts?.completed || 0}</p>
                <p className="text-sm text-green-600">Completed Today</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <div className="grid md:grid-cols-3 gap-6">
        {/* Procedure Rooms (2/3 width) */}
        <div className="md:col-span-2">
          <h2 className="font-semibold mb-3 flex items-center gap-2">
            <Monitor className="w-5 h-5 text-purple-600" />
            Procedure Rooms
          </h2>
          <div className="grid grid-cols-2 gap-4 h-[500px]">
            {rooms.map((proc, idx) => (
              <div key={idx} className="h-full">
                <div className="text-xs font-medium text-gray-500 mb-1">Room {idx + 1}</div>
                <ProcedureRoomCard 
                  procedure={proc} 
                  latestVitals={proc ? vitalsMap[proc.id] : null}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Sidebar - Recovery & Upcoming */}
        <div className="space-y-6">
          {/* Recovery Area */}
          <div>
            <h2 className="font-semibold mb-3 flex items-center gap-2">
              <Timer className="w-5 h-5 text-orange-600" />
              Recovery Area ({recoveryPatients.length})
            </h2>
            <ScrollArea className="h-[200px]">
              {recoveryPatients.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  No patients in recovery
                </div>
              ) : (
                <div className="space-y-2">
                  {recoveryPatients.map((proc) => (
                    <RecoveryPatientCard key={proc.id} procedure={proc} />
                  ))}
                </div>
              )}
            </ScrollArea>
          </div>

          {/* Upcoming */}
          <div>
            <h2 className="font-semibold mb-3 flex items-center gap-2">
              <Clock className="w-5 h-5 text-blue-600" />
              Upcoming Today
            </h2>
            <ScrollArea className="h-[250px]">
              {upcomingToday.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  No upcoming procedures
                </div>
              ) : (
                <div className="space-y-2">
                  {upcomingToday.map((proc) => (
                    <div 
                      key={proc.id}
                      className="flex items-center justify-between p-3 bg-blue-50 rounded-lg border border-blue-200"
                    >
                      <div>
                        <p className="font-medium text-sm">{proc.patient_name}</p>
                        <p className="text-xs text-gray-600">{proc.procedure_description}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-mono text-lg font-bold text-blue-700">{proc.scheduled_time}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </div>
        </div>
      </div>
    </div>
  );
}
