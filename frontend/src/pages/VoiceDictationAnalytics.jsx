import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/lib/auth';
import { getErrorMessage, cn } from '@/lib/utils';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select, SelectContent, SelectItem,
  SelectTrigger, SelectValue
} from '@/components/ui/select';
import {
  Table, TableBody, TableCell,
  TableHead, TableHeader, TableRow
} from '@/components/ui/table';
import { toast } from 'sonner';
import {
  Mic, RefreshCw, BarChart3, Users, Clock, Sparkles,
  TrendingUp, Award, FileText, Calendar, Activity,
  Filter, Download, Search, CheckCircle, Loader2
} from 'lucide-react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, BarChart, Bar, Legend
} from 'recharts';
import api from '@/lib/api';

// Voice Dictation Analytics API
const analyticsAPI = {
  getAnalytics: (params) => api.get('/voice-dictation/analytics', { params }),
  getAuditLogs: (params) => api.get('/voice-dictation/audit-logs', { params }),
};

const COLORS = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#6366f1'];

// Role Badge Component
function RoleBadge({ role }) {
  const colors = {
    radiologist: 'bg-purple-100 text-purple-800',
    physician: 'bg-blue-100 text-blue-800',
    nurse: 'bg-green-100 text-green-800',
    nursing_supervisor: 'bg-emerald-100 text-emerald-800',
    floor_supervisor: 'bg-teal-100 text-teal-800',
    hospital_admin: 'bg-orange-100 text-orange-800',
    super_admin: 'bg-red-100 text-red-800',
  };
  return (
    <Badge className={colors[role] || 'bg-gray-100 text-gray-800'}>
      {role?.replace(/_/g, ' ')}
    </Badge>
  );
}

// Context Badge Component
function ContextBadge({ context }) {
  const colors = {
    radiology: 'bg-purple-100 text-purple-700',
    clinical: 'bg-blue-100 text-blue-700',
    nursing: 'bg-green-100 text-green-700',
    general: 'bg-gray-100 text-gray-700',
    ai_expand_soap_note: 'bg-indigo-100 text-indigo-700',
    ai_expand_radiology_report: 'bg-violet-100 text-violet-700',
    ai_expand_progress_note: 'bg-cyan-100 text-cyan-700',
    ai_expand_nursing_assessment: 'bg-emerald-100 text-emerald-700',
  };
  return (
    <Badge variant="outline" className={colors[context] || 'bg-gray-100'}>
      {context?.replace(/_/g, ' ')}
    </Badge>
  );
}

export default function VoiceDictationAnalytics() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [totalLogs, setTotalLogs] = useState(0);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Filters
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [logFilter, setLogFilter] = useState({ context: '', user_id: '' });
  const [logPage, setLogPage] = useState(0);
  const LOG_LIMIT = 50;

  // Fetch analytics
  const fetchAnalytics = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      
      const response = await analyticsAPI.getAnalytics(params);
      setAnalytics(response.data);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to load analytics'));
    } finally {
      setLoading(false);
    }
  }, [dateFrom, dateTo]);

  // Fetch audit logs
  const fetchAuditLogs = useCallback(async () => {
    try {
      const params = {
        limit: LOG_LIMIT,
        skip: logPage * LOG_LIMIT,
      };
      if (logFilter.context) params.context = logFilter.context;
      if (logFilter.user_id) params.user_id = logFilter.user_id;
      
      const response = await analyticsAPI.getAuditLogs(params);
      setAuditLogs(response.data.logs || []);
      setTotalLogs(response.data.total || 0);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to load audit logs'));
    }
  }, [logPage, logFilter]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  useEffect(() => {
    if (activeTab === 'audit') {
      fetchAuditLogs();
    }
  }, [activeTab, fetchAuditLogs]);

  // Prepare chart data
  const dailyChartData = analytics?.daily_usage 
    ? Object.entries(analytics.daily_usage).map(([date, count]) => ({
        date: date.substring(5), // MM-DD
        count
      }))
    : [];

  const roleChartData = analytics?.usage_by_role
    ? Object.entries(analytics.usage_by_role).map(([role, data]) => ({
        name: role.replace(/_/g, ' '),
        count: data.count,
        duration: Math.round(data.duration / 60)
      }))
    : [];

  const contextChartData = analytics?.usage_by_context
    ? Object.entries(analytics.usage_by_context).map(([context, count]) => ({
        name: context.replace(/_/g, ' '),
        value: count
      }))
    : [];

  return (
    <div className="space-y-6 animate-fade-in" data-testid="voice-analytics">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Mic className="w-7 h-7 text-purple-600" />
            Voice Dictation Analytics
          </h1>
          <p className="text-slate-500 mt-1">Usage statistics and audit logs for voice dictation</p>
        </div>
        <div className="flex gap-2 items-center">
          <div className="flex gap-2 items-center">
            <Input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="w-36"
              placeholder="From"
            />
            <span className="text-gray-400">to</span>
            <Input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="w-36"
              placeholder="To"
            />
          </div>
          <Button onClick={fetchAnalytics} variant="outline" className="gap-2">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* Summary Stats */}
      {analytics?.summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
            <CardContent className="pt-4">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-full bg-purple-200">
                  <Mic className="w-6 h-6 text-purple-700" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-purple-800">{analytics.summary.total_transcriptions}</p>
                  <p className="text-sm text-purple-600">Total Transcriptions</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
            <CardContent className="pt-4">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-full bg-blue-200">
                  <Clock className="w-6 h-6 text-blue-700" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-blue-800">{analytics.summary.total_duration_minutes}</p>
                  <p className="text-sm text-blue-600">Total Minutes</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
            <CardContent className="pt-4">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-full bg-green-200">
                  <Sparkles className="w-6 h-6 text-green-700" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-green-800">{analytics.summary.total_corrections_made}</p>
                  <p className="text-sm text-green-600">Terms Corrected</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-amber-50 to-amber-100 border-amber-200">
            <CardContent className="pt-4">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-full bg-amber-200">
                  <Activity className="w-6 h-6 text-amber-700" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-amber-800">{analytics.summary.avg_duration_seconds}s</p>
                  <p className="text-sm text-amber-600">Avg. Duration</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview" className="gap-2">
            <BarChart3 className="w-4 h-4" /> Overview
          </TabsTrigger>
          <TabsTrigger value="users" className="gap-2">
            <Users className="w-4 h-4" /> Top Users
          </TabsTrigger>
          <TabsTrigger value="audit" className="gap-2">
            <FileText className="w-4 h-4" /> Audit Logs
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Daily Usage Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-purple-600" />
                  Daily Usage Trend
                </CardTitle>
                <CardDescription>Transcriptions per day (last 30 days)</CardDescription>
              </CardHeader>
              <CardContent>
                {dailyChartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={250}>
                    <AreaChart data={dailyChartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip />
                      <Area 
                        type="monotone" 
                        dataKey="count" 
                        stroke="#8b5cf6" 
                        fill="#c4b5fd" 
                        name="Transcriptions"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[250px] flex items-center justify-center text-gray-500">
                    No data available
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Usage by Context */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Activity className="w-5 h-5 text-blue-600" />
                  Usage by Context
                </CardTitle>
                <CardDescription>Distribution of transcription contexts</CardDescription>
              </CardHeader>
              <CardContent>
                {contextChartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={250}>
                    <PieChart>
                      <Pie
                        data={contextChartData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={80}
                        paddingAngle={2}
                        dataKey="value"
                        label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                        labelLine={false}
                      >
                        {contextChartData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[250px] flex items-center justify-center text-gray-500">
                    No data available
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Usage by Role */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Users className="w-5 h-5 text-green-600" />
                Usage by Role
              </CardTitle>
              <CardDescription>Transcription count and duration by user role</CardDescription>
            </CardHeader>
            <CardContent>
              {roleChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={roleChartData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="count" fill="#8b5cf6" name="Transcriptions" />
                    <Bar dataKey="duration" fill="#10b981" name="Minutes" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[300px] flex items-center justify-center text-gray-500">
                  No data available
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Top Users Tab */}
        <TabsContent value="users">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Award className="w-5 h-5 text-amber-500" />
                Top Users by Transcription Count
              </CardTitle>
            </CardHeader>
            <CardContent>
              {analytics?.top_users?.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-12">#</TableHead>
                      <TableHead>User</TableHead>
                      <TableHead className="text-right">Transcriptions</TableHead>
                      <TableHead className="text-right">Duration (min)</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {analytics.top_users.map((user, idx) => (
                      <TableRow key={idx}>
                        <TableCell>
                          {idx === 0 && <span className="text-2xl">🥇</span>}
                          {idx === 1 && <span className="text-2xl">🥈</span>}
                          {idx === 2 && <span className="text-2xl">🥉</span>}
                          {idx > 2 && <span className="text-gray-500">{idx + 1}</span>}
                        </TableCell>
                        <TableCell className="font-medium">{user.name}</TableCell>
                        <TableCell className="text-right">
                          <Badge variant="outline" className="bg-purple-50">{user.count}</Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <span className="text-gray-600">{Math.round(user.duration / 60)}</span>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  No user data available
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Audit Logs Tab */}
        <TabsContent value="audit">
          <Card>
            <CardHeader>
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <CardTitle>Audit Logs</CardTitle>
                  <CardDescription>Detailed log of all voice dictation activities</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Select
                    value={logFilter.context}
                    onValueChange={(v) => {
                      setLogFilter({...logFilter, context: v === 'all' ? '' : v});
                      setLogPage(0);
                    }}
                  >
                    <SelectTrigger className="w-40">
                      <SelectValue placeholder="All Contexts" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Contexts</SelectItem>
                      <SelectItem value="radiology">Radiology</SelectItem>
                      <SelectItem value="clinical">Clinical</SelectItem>
                      <SelectItem value="nursing">Nursing</SelectItem>
                      <SelectItem value="general">General</SelectItem>
                    </SelectContent>
                  </Select>
                  <Button variant="outline" onClick={fetchAuditLogs}>
                    <RefreshCw className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>User</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Context</TableHead>
                    <TableHead>Duration</TableHead>
                    <TableHead>Corrections</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {auditLogs.map((log, idx) => (
                    <TableRow key={idx}>
                      <TableCell className="font-mono text-sm">
                        {new Date(log.timestamp).toLocaleString()}
                      </TableCell>
                      <TableCell>{log.user_name}</TableCell>
                      <TableCell><RoleBadge role={log.user_role} /></TableCell>
                      <TableCell><ContextBadge context={log.context} /></TableCell>
                      <TableCell>{log.duration_seconds ? `${log.duration_seconds.toFixed(1)}s` : '-'}</TableCell>
                      <TableCell>
                        {log.corrections_count > 0 ? (
                          <Badge className="bg-green-100 text-green-700">{log.corrections_count}</Badge>
                        ) : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              
              {/* Pagination */}
              <div className="flex items-center justify-between mt-4">
                <p className="text-sm text-gray-500">
                  Showing {logPage * LOG_LIMIT + 1}-{Math.min((logPage + 1) * LOG_LIMIT, totalLogs)} of {totalLogs}
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={logPage === 0}
                    onClick={() => setLogPage(p => p - 1)}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={(logPage + 1) * LOG_LIMIT >= totalLogs}
                    onClick={() => setLogPage(p => p + 1)}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
