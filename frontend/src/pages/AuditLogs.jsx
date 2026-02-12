import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/lib/auth';
import { auditAPI } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
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
import { 
  FileText, Search, Download, RefreshCw, 
  AlertTriangle, ShieldAlert, CheckCircle2, XCircle,
  Clock, User, Activity, Shield, ChevronLeft, ChevronRight
} from 'lucide-react';

const SEVERITY_COLORS = {
  info: 'bg-blue-100 text-blue-700',
  warning: 'bg-amber-100 text-amber-700',
  alert: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700'
};

export default function AuditLogs() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [totalCount, setTotalCount] = useState(0);
  
  const [filters, setFilters] = useState({
    user_id: '',
    action: '',
    resource_type: '',
    severity: '',
    search: ''
  });
  
  const [page, setPage] = useState(0);
  const pageSize = 50;
  const [selectedLog, setSelectedLog] = useState(null);
  const [actions, setActions] = useState([]);
  const [resourceTypes, setResourceTypes] = useState([]);

  const fetchLogs = useCallback(async () => {
    try {
      setLoading(true);
      const params = {
        skip: page * pageSize,
        limit: pageSize,
        ...Object.fromEntries(Object.entries(filters).filter(([_, v]) => v !== ''))
      };
      
      const [logsRes, countRes, statsRes] = await Promise.all([
        auditAPI.getLogs(params),
        auditAPI.getLogsCount(params),
        auditAPI.getStats(30)
      ]);
      
      setLogs(logsRes.data.logs || []);
      setTotalCount(countRes.data.count || 0);
      setStats(statsRes.data);
    } catch (err) {
      console.error('Failed to fetch logs:', err);
      toast.error('Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  }, [page, filters]);

  const fetchFilterOptions = useCallback(async () => {
    try {
      const [actionsRes, typesRes] = await Promise.all([
        auditAPI.getActions(),
        auditAPI.getResourceTypes()
      ]);
      setActions(actionsRes.data.actions || []);
      setResourceTypes(typesRes.data.resource_types || []);
    } catch (err) {
      console.error('Failed to fetch filter options:', err);
    }
  }, []);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  useEffect(() => {
    fetchFilterOptions();
  }, [fetchFilterOptions]);

  const handleExport = async (format) => {
    try {
      const params = {
        format,
        ...Object.fromEntries(Object.entries(filters).filter(([_, v]) => v !== ''))
      };
      const res = await auditAPI.exportLogs(params);
      
      const blob = new Blob([format === 'csv' ? res.data : JSON.stringify(res.data, null, 2)], {
        type: format === 'csv' ? 'text/csv' : 'application/json'
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit_logs_${new Date().toISOString().split('T')[0]}.${format}`;
      a.click();
      toast.success(`Exported as ${format.toUpperCase()}`);
    } catch (err) {
      toast.error('Export failed');
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical': return <ShieldAlert className="w-4 h-4 text-red-500" />;
      case 'alert': return <AlertTriangle className="w-4 h-4 text-orange-500" />;
      case 'warning': return <AlertTriangle className="w-4 h-4 text-amber-500" />;
      default: return <Activity className="w-4 h-4 text-blue-500" />;
    }
  };

  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <div className="space-y-6 animate-fade-in" data-testid="audit-logs">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900" style={{ fontFamily: 'Manrope' }}>
            Audit Logs
          </h1>
          <p className="text-slate-500 mt-1">
            Security and compliance event tracking
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => handleExport('csv')}>
            <Download className="w-4 h-4 mr-2" />
            CSV
          </Button>
          <Button variant="outline" onClick={() => handleExport('json')}>
            <Download className="w-4 h-4 mr-2" />
            JSON
          </Button>
          <Button onClick={fetchLogs}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Total Events</p>
                  <p className="text-2xl font-bold">{stats.total_logs || 0}</p>
                </div>
                <FileText className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Failed Logins</p>
                  <p className="text-2xl font-bold text-red-600">{stats.failed_logins || 0}</p>
                </div>
                <XCircle className="w-8 h-8 text-red-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">PHI Access</p>
                  <p className="text-2xl font-bold text-purple-600">{stats.phi_access || 0}</p>
                </div>
                <Shield className="w-8 h-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">Active Users</p>
                  <p className="text-2xl font-bold text-emerald-600">{stats.active_users || 0}</p>
                </div>
                <User className="w-8 h-8 text-emerald-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Search className="w-5 h-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <Input
              placeholder="Search..."
              value={filters.search}
              onChange={(e) => setFilters({...filters, search: e.target.value})}
            />
            <Select value={filters.action || "all"} onValueChange={(v) => setFilters({...filters, action: v === "all" ? "" : v})}>
              <SelectTrigger>
                <SelectValue placeholder="All Actions" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Actions</SelectItem>
                {actions.map(a => (
                  <SelectItem key={a} value={a}>{a}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filters.resource_type || "all"} onValueChange={(v) => setFilters({...filters, resource_type: v === "all" ? "" : v})}>
              <SelectTrigger>
                <SelectValue placeholder="All Resources" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Resources</SelectItem>
                {resourceTypes.map(t => (
                  <SelectItem key={t} value={t}>{t}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filters.severity || "all"} onValueChange={(v) => setFilters({...filters, severity: v === "all" ? "" : v})}>
              <SelectTrigger>
                <SelectValue placeholder="All Severities" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Severities</SelectItem>
                <SelectItem value="info">Info</SelectItem>
                <SelectItem value="warning">Warning</SelectItem>
                <SelectItem value="alert">Alert</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={() => setFilters({user_id: '', action: '', resource_type: '', severity: '', search: ''})}>
              Clear Filters
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Logs Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Event Log</CardTitle>
            <span className="text-sm text-slate-500">{totalCount} total events</span>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {[1,2,3,4,5].map(i => <Skeleton key={i} className="h-12 w-full" />)}
            </div>
          ) : logs.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              <FileText className="w-12 h-12 mx-auto mb-3 text-slate-300" />
              <p>No audit logs found</p>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Time</TableHead>
                    <TableHead>User</TableHead>
                    <TableHead>Action</TableHead>
                    <TableHead>Resource</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {logs.map((log) => (
                    <TableRow key={log.id} className="cursor-pointer hover:bg-slate-50" onClick={() => setSelectedLog(log)}>
                      <TableCell className="text-sm">
                        <div className="flex items-center gap-2">
                          <Clock className="w-3 h-3 text-slate-400" />
                          {formatDateTime(log.timestamp)}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <User className="w-3 h-3 text-slate-400" />
                          {log.user_name || log.user_id || 'System'}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{log.action}</Badge>
                      </TableCell>
                      <TableCell>{log.resource_type}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          {getSeverityIcon(log.severity)}
                          <Badge className={SEVERITY_COLORS[log.severity] || SEVERITY_COLORS.info}>
                            {log.severity || 'info'}
                          </Badge>
                        </div>
                      </TableCell>
                      <TableCell>
                        {log.success !== false ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                        ) : (
                          <XCircle className="w-4 h-4 text-red-500" />
                        )}
                      </TableCell>
                      <TableCell>
                        <Button variant="ghost" size="sm">View</Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              
              {/* Pagination */}
              <div className="flex items-center justify-between mt-4">
                <p className="text-sm text-slate-500">
                  Page {page + 1} of {totalPages || 1}
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page === 0}
                    onClick={() => setPage(p => Math.max(0, p - 1))}
                  >
                    <ChevronLeft className="w-4 h-4" />
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page >= totalPages - 1}
                    onClick={() => setPage(p => p + 1)}
                  >
                    Next
                    <ChevronRight className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Log Detail Dialog */}
      <Dialog open={!!selectedLog} onOpenChange={() => setSelectedLog(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Audit Log Detail</DialogTitle>
          </DialogHeader>
          {selectedLog && (
            <div className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-500">Event ID</p>
                  <p className="font-mono text-sm">{selectedLog.id}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Timestamp</p>
                  <p>{formatDateTime(selectedLog.timestamp)}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">User</p>
                  <p>{selectedLog.user_name || selectedLog.user_id || 'System'}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Action</p>
                  <Badge>{selectedLog.action}</Badge>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Resource Type</p>
                  <p>{selectedLog.resource_type}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Resource ID</p>
                  <p className="font-mono text-sm">{selectedLog.resource_id || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">IP Address</p>
                  <p className="font-mono text-sm">{selectedLog.ip_address || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">PHI Access</p>
                  <Badge variant={selectedLog.phi_accessed ? "destructive" : "secondary"}>
                    {selectedLog.phi_accessed ? 'Yes' : 'No'}
                  </Badge>
                </div>
              </div>
              {selectedLog.details && (
                <div>
                  <p className="text-sm text-slate-500 mb-2">Details</p>
                  <pre className="bg-slate-100 p-3 rounded-lg text-sm overflow-auto max-h-48">
                    {JSON.stringify(selectedLog.details, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
