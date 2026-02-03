import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/lib/auth';
import { auditAPI, usersAPI } from '@/lib/api';
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { toast } from 'sonner';
import { formatDateTime } from '@/lib/utils';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, AreaChart, Area } from 'recharts';
import { 
  FileText, Search, Download, Filter, RefreshCw, 
  AlertTriangle, ShieldAlert, CheckCircle2, XCircle,
  Clock, User, Activity, Shield, TrendingUp
} from 'lucide-react';

const SEVERITY_COLORS = {
  info: 'bg-blue-100 text-blue-700',
  warning: 'bg-amber-100 text-amber-700',
  alert: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700'
};

const ACTION_COLORS = {
  view: '#3b82f6',
  create: '#10b981',
  update: '#f59e0b',
  delete: '#ef4444',
  login: '#8b5cf6',
  logout: '#6b7280',
  failed_login: '#dc2626',
  export: '#0ea5e9'
};

export default function AuditLogs() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [securityStats, setSecurityStats] = useState(null);
  const [alerts, setAlerts] = useState(null);
  const [totalCount, setTotalCount] = useState(0);
  const [users, setUsers] = useState([]);
  
  // Filters
  const [filters, setFilters] = useState({
    user_id: '',
    action: '',
    resource_type: '',
    severity: '',
    success: '',
    search: '',
    start_date: '',
    end_date: ''
  });
  
  // Pagination
  const [page, setPage] = useState(0);
  const [pageSize] = useState(50);
  
  // Detail dialog
  const [selectedLog, setSelectedLog] = useState(null);
  
  // Filter options
  const [actions, setActions] = useState([]);
  const [resourceTypes, setResourceTypes] = useState([]);

  const fetchLogs = useCallback(async () => {
    try {
      const params = {
        skip: page * pageSize,
        limit: pageSize,
        ...Object.fromEntries(Object.entries(filters).filter(([_, v]) => v !== ''))
      };
      
      const [logsRes, countRes] = await Promise.all([
        auditAPI.getLogs(params),
        auditAPI.getLogsCount(params)
      ]);
      
      setLogs(logsRes.data);
      setTotalCount(countRes.data.count);
    } catch (err) {
      console.error('Failed to fetch logs:', err);
      toast.error('Failed to fetch audit logs');
    }
  }, [page, pageSize, filters]);

  const fetchStats = useCallback(async () => {
    try {
      const [statsRes, secRes, alertsRes, actionsRes, typesRes, usersRes] = await Promise.all([
        auditAPI.getStats(7),
        auditAPI.getSecurityStats(30),
        auditAPI.getAlerts(24),
        auditAPI.getActions(),
        auditAPI.getResourceTypes(),
        usersAPI.getAll()
      ]);
      
      setStats(statsRes.data);
      setSecurityStats(secRes.data);
      setAlerts(alertsRes.data);
      setActions(actionsRes.data);
      setResourceTypes(typesRes.data);
      setUsers(usersRes.data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  }, []);

  useEffect(() => {
    Promise.all([fetchLogs(), fetchStats()]).finally(() => setLoading(false));
  }, [fetchLogs, fetchStats]);

  useEffect(() => {
    fetchLogs();
  }, [page, filters, fetchLogs]);

  const handleExport = async (format) => {
    try {
      const params = {
        format,
        ...Object.fromEntries(Object.entries(filters).filter(([_, v]) => v !== '')),
        limit: 10000
      };
      
      if (format === 'csv') {
        const response = await auditAPI.exportLogs(params);
        const blob = new Blob([response.data], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `audit_logs_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
      } else {
        const response = await auditAPI.exportLogs(params);
        const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `audit_logs_${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        window.URL.revokeObjectURL(url);
      }
      
      toast.success(`Audit logs exported as ${format.toUpperCase()}`);
    } catch (err) {
      toast.error('Failed to export logs');
    }
  };

  const resetFilters = () => {
    setFilters({
      user_id: '',
      action: '',
      resource_type: '',
      severity: '',
      success: '',
      search: '',
      start_date: '',
      end_date: ''
    });
    setPage(0);
  };

  // Prepare chart data
  const actionChartData = stats?.action_breakdown 
    ? Object.entries(stats.action_breakdown).map(([name, value]) => ({ name, value, fill: ACTION_COLORS[name] || '#94a3b8' }))
    : [];
  
  const hourlyData = stats?.hourly_activity || [];

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-64" />
        <div className="grid grid-cols-4 gap-4">
          {[1,2,3,4].map(i => <Skeleton key={i} className="h-24" />)}
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="audit-logs">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-900" style={{ fontFamily: 'Manrope' }}>
            HIPAA Audit Logs
          </h1>
          <p className="text-slate-500 mt-1">
            Comprehensive audit trail for compliance and security monitoring
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => handleExport('csv')}>
            <Download className="w-4 h-4 mr-2" /> Export CSV
          </Button>
          <Button variant="outline" onClick={() => handleExport('json')}>
            <Download className="w-4 h-4 mr-2" /> Export JSON
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Events</p>
                <p className="text-2xl font-bold text-slate-900">{stats?.total_logs?.toLocaleString() || 0}</p>
              </div>
              <FileText className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-emerald-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Today's Events</p>
                <p className="text-2xl font-bold text-slate-900">{stats?.today_logs?.toLocaleString() || 0}</p>
              </div>
              <Clock className="w-8 h-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-red-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Failed Logins</p>
                <p className="text-2xl font-bold text-slate-900">{stats?.failed_logins || 0}</p>
              </div>
              <ShieldAlert className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-amber-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Security Alerts</p>
                <p className="text-2xl font-bold text-slate-900">{alerts?.alert_count || 0}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="logs">
        <TabsList>
          <TabsTrigger value="logs">Audit Logs</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
        </TabsList>

        {/* Logs Tab */}
        <TabsContent value="logs" className="mt-6 space-y-4">
          {/* Filters */}
          <Card>
            <CardContent className="p-4">
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                <div>
                  <Input
                    placeholder="Search..."
                    value={filters.search}
                    onChange={(e) => setFilters({...filters, search: e.target.value})}
                    className="h-9"
                  />
                </div>
                <Select value={filters.action} onValueChange={(v) => setFilters({...filters, action: v === 'all' ? '' : v})}>
                  <SelectTrigger className="h-9"><SelectValue placeholder="Action" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Actions</SelectItem>
                    {actions.map(a => (
                      <SelectItem key={a.value} value={a.value}>{a.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={filters.resource_type} onValueChange={(v) => setFilters({...filters, resource_type: v === 'all' ? '' : v})}>
                  <SelectTrigger className="h-9"><SelectValue placeholder="Resource" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Resources</SelectItem>
                    {resourceTypes.map(r => (
                      <SelectItem key={r.value} value={r.value}>{r.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={filters.severity} onValueChange={(v) => setFilters({...filters, severity: v === 'all' ? '' : v})}>
                  <SelectTrigger className="h-9"><SelectValue placeholder="Severity" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Severities</SelectItem>
                    <SelectItem value="info">Info</SelectItem>
                    <SelectItem value="warning">Warning</SelectItem>
                    <SelectItem value="alert">Alert</SelectItem>
                    <SelectItem value="critical">Critical</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={filters.success} onValueChange={(v) => setFilters({...filters, success: v === 'all' ? '' : v})}>
                  <SelectTrigger className="h-9"><SelectValue placeholder="Status" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="true">Success</SelectItem>
                    <SelectItem value="false">Failed</SelectItem>
                  </SelectContent>
                </Select>
                <Button variant="outline" onClick={resetFilters} className="h-9">
                  <RefreshCw className="w-4 h-4 mr-2" /> Reset
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Logs Table */}
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle>Audit Events</CardTitle>
                <span className="text-sm text-slate-500">{totalCount.toLocaleString()} total records</span>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>User</TableHead>
                    <TableHead>Action</TableHead>
                    <TableHead>Resource</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Details</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {logs.map((log) => (
                    <TableRow 
                      key={log.id} 
                      className="cursor-pointer hover:bg-slate-50"
                      onClick={() => setSelectedLog(log)}
                    >
                      <TableCell className="text-sm text-slate-600">
                        {formatDateTime(log.timestamp)}
                      </TableCell>
                      <TableCell>
                        <div>
                          <p className="font-medium text-slate-900">{log.user_name}</p>
                          <p className="text-xs text-slate-500">{log.user_role}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="capitalize">{log.action}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="capitalize">{log.resource_type}</Badge>
                      </TableCell>
                      <TableCell>
                        {log.success ? (
                          <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                        ) : (
                          <XCircle className="w-5 h-5 text-red-500" />
                        )}
                      </TableCell>
                      <TableCell className="max-w-xs truncate text-sm text-slate-600">
                        {log.details || '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              
              {/* Pagination */}
              <div className="flex items-center justify-between mt-4">
                <p className="text-sm text-slate-500">
                  Showing {page * pageSize + 1} - {Math.min((page + 1) * pageSize, totalCount)} of {totalCount}
                </p>
                <div className="flex gap-2">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => setPage(p => Math.max(0, p - 1))}
                    disabled={page === 0}
                  >
                    Previous
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => setPage(p => p + 1)}
                    disabled={(page + 1) * pageSize >= totalCount}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Activity by Action Type</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={actionChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 11 }} />
                    <YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                      {actionChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Hourly Activity Pattern</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={hourlyData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="hour" tick={{ fill: '#64748b', fontSize: 12 }} />
                    <YAxis tick={{ fill: '#64748b', fontSize: 12 }} />
                    <Tooltip />
                    <Area type="monotone" dataKey="count" stroke="#3b82f6" fill="#bfdbfe" />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Top Active Users</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {stats?.user_activity?.slice(0, 8).map((ua, i) => (
                    <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-slate-50">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-sky-100 text-sky-700 flex items-center justify-center text-sm font-semibold">
                          {i + 1}
                        </div>
                        <span className="font-medium text-slate-900">{ua.user_name}</span>
                      </div>
                      <Badge>{ua.count.toLocaleString()} events</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Resource Access Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {Object.entries(stats?.resource_breakdown || {}).slice(0, 8).map(([resource, count]) => (
                    <div key={resource} className="flex items-center justify-between">
                      <span className="capitalize text-slate-700">{resource.replace(/_/g, ' ')}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-32 h-2 bg-slate-200 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-sky-500 rounded-full"
                            style={{ width: `${(count / stats.total_logs) * 100}%` }}
                          />
                        </div>
                        <span className="text-sm text-slate-500 w-16 text-right">{count.toLocaleString()}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Security Tab */}
        <TabsContent value="security" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="w-5 h-5" /> Security Events (30 Days)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(securityStats?.security_events || {}).map(([event, count]) => (
                    <div key={event} className="flex items-center justify-between p-3 rounded-lg border">
                      <span className="capitalize text-slate-700">{event.replace(/_/g, ' ')}</span>
                      <Badge className={count > 0 && event.includes('failed') ? 'bg-red-100 text-red-700' : ''}>
                        {count}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ShieldAlert className="w-5 h-5" /> Failed Logins by IP
                </CardTitle>
              </CardHeader>
              <CardContent>
                {securityStats?.failed_logins_by_ip?.length > 0 ? (
                  <div className="space-y-3">
                    {securityStats.failed_logins_by_ip.map((item, i) => (
                      <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-red-50 border border-red-100">
                        <span className="font-mono text-sm text-slate-700">{item.ip || 'Unknown'}</span>
                        <Badge className="bg-red-100 text-red-700">{item.count} attempts</Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center text-slate-500 py-8">No failed login attempts from suspicious IPs</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="w-5 h-5" /> 2FA Adoption
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <div className="text-4xl font-bold text-sky-600 mb-2">
                    {securityStats?.two_factor_adoption?.percentage || 0}%
                  </div>
                  <p className="text-slate-600">
                    {securityStats?.two_factor_adoption?.enabled || 0} of {securityStats?.two_factor_adoption?.total || 0} users have 2FA enabled
                  </p>
                  <div className="mt-4 h-4 bg-slate-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-emerald-500 rounded-full transition-all"
                      style={{ width: `${securityStats?.two_factor_adoption?.percentage || 0}%` }}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Suspicious Users</CardTitle>
                <CardDescription>Users with multiple failed login attempts</CardDescription>
              </CardHeader>
              <CardContent>
                {securityStats?.suspicious_users?.length > 0 ? (
                  <div className="space-y-3">
                    {securityStats.suspicious_users.map((item, i) => (
                      <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-amber-50 border border-amber-100">
                        <span className="text-slate-700">{item.user_id}</span>
                        <Badge className="bg-amber-100 text-amber-700">{item.failed_attempts} failed</Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center text-slate-500 py-8">No suspicious activity detected</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Alerts Tab */}
        <TabsContent value="alerts" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="w-5 h-5" /> Security Alerts (Last 24 Hours)
              </CardTitle>
              <CardDescription>{alerts?.alert_count || 0} alerts detected</CardDescription>
            </CardHeader>
            <CardContent>
              {alerts?.alerts?.length > 0 ? (
                <div className="space-y-3">
                  {alerts.alerts.map((alert, i) => (
                    <div 
                      key={i} 
                      className={`p-4 rounded-lg border ${
                        alert.severity === 'critical' ? 'bg-red-50 border-red-200' :
                        alert.severity === 'warning' ? 'bg-amber-50 border-amber-200' :
                        'bg-blue-50 border-blue-200'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3">
                          {alert.severity === 'critical' ? (
                            <XCircle className="w-5 h-5 text-red-500 mt-0.5" />
                          ) : alert.severity === 'warning' ? (
                            <AlertTriangle className="w-5 h-5 text-amber-500 mt-0.5" />
                          ) : (
                            <Activity className="w-5 h-5 text-blue-500 mt-0.5" />
                          )}
                          <div>
                            <p className="font-medium text-slate-900">{alert.message}</p>
                            <p className="text-sm text-slate-500 mt-1">Type: {alert.type}</p>
                          </div>
                        </div>
                        <Badge className={SEVERITY_COLORS[alert.severity]}>{alert.severity}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto mb-4" />
                  <p className="text-slate-600">No security alerts in the last 24 hours</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Log Detail Dialog */}
      <Dialog open={!!selectedLog} onOpenChange={() => setSelectedLog(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Audit Log Details</DialogTitle>
          </DialogHeader>
          {selectedLog && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-500">Timestamp</p>
                  <p className="font-medium">{formatDateTime(selectedLog.timestamp)}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Status</p>
                  <Badge className={selectedLog.success ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}>
                    {selectedLog.success ? 'Success' : 'Failed'}
                  </Badge>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-500">User</p>
                  <p className="font-medium">{selectedLog.user_name}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Role</p>
                  <p className="font-medium capitalize">{selectedLog.user_role}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-500">Action</p>
                  <Badge variant="outline" className="capitalize">{selectedLog.action}</Badge>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Resource Type</p>
                  <Badge variant="secondary" className="capitalize">{selectedLog.resource_type}</Badge>
                </div>
              </div>
              {selectedLog.resource_id && (
                <div>
                  <p className="text-sm text-slate-500">Resource ID</p>
                  <p className="font-mono text-sm">{selectedLog.resource_id}</p>
                </div>
              )}
              {selectedLog.patient_id && (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-slate-500">Patient ID</p>
                    <p className="font-mono text-sm">{selectedLog.patient_id}</p>
                  </div>
                  {selectedLog.patient_name && (
                    <div>
                      <p className="text-sm text-slate-500">Patient Name</p>
                      <p className="font-medium">{selectedLog.patient_name}</p>
                    </div>
                  )}
                </div>
              )}
              {selectedLog.ip_address && (
                <div>
                  <p className="text-sm text-slate-500">IP Address</p>
                  <p className="font-mono text-sm">{selectedLog.ip_address}</p>
                </div>
              )}
              {selectedLog.details && (
                <div>
                  <p className="text-sm text-slate-500">Details</p>
                  <p className="text-slate-700">{selectedLog.details}</p>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
