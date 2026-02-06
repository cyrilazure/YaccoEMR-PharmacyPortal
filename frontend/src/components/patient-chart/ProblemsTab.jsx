import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { toast } from 'sonner';
import { Plus, AlertTriangle, Loader2, CheckCircle, Clock, XCircle } from 'lucide-react';
import { problemsAPI } from '@/lib/api';
import { formatDate } from '@/lib/utils';

export default function ProblemsTab({ patientId, problems, onRefresh, user }) {
  const [problemDialogOpen, setProblemDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [newProblem, setNewProblem] = useState({
    description: '', icd_code: '', onset_date: '', status: 'active', notes: ''
  });

  const handleAddProblem = async () => {
    if (!newProblem.description) {
      toast.error('Problem description is required');
      return;
    }
    setSaving(true);
    try {
      await problemsAPI.create({
        patient_id: patientId,
        ...newProblem
      });
      toast.success('Problem added successfully');
      setProblemDialogOpen(false);
      setNewProblem({ description: '', icd_code: '', onset_date: '', status: 'active', notes: '' });
      onRefresh();
    } catch (err) {
      toast.error('Failed to add problem');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateStatus = async (problemId, newStatus) => {
    try {
      await problemsAPI.update(problemId, { status: newStatus });
      toast.success(`Problem marked as ${newStatus}`);
      onRefresh();
    } catch (err) {
      toast.error('Failed to update problem');
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      active: { className: 'bg-red-100 text-red-700', icon: AlertTriangle },
      resolved: { className: 'bg-green-100 text-green-700', icon: CheckCircle },
      chronic: { className: 'bg-amber-100 text-amber-700', icon: Clock },
      inactive: { className: 'bg-gray-100 text-gray-700', icon: XCircle }
    };
    const style = styles[status] || styles.active;
    const Icon = style.icon;
    return (
      <Badge className={`${style.className} gap-1`}>
        <Icon className="w-3 h-3" /> {status}
      </Badge>
    );
  };

  const activeProblems = problems.filter(p => p.status === 'active' || p.status === 'chronic');
  const resolvedProblems = problems.filter(p => p.status === 'resolved' || p.status === 'inactive');

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-red-50 border-red-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-red-600" />
              <p className="text-sm text-red-700">Active</p>
              <p className="text-2xl font-bold text-red-800">{problems.filter(p => p.status === 'active').length}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-amber-50 border-amber-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <Clock className="w-8 h-8 mx-auto mb-2 text-amber-600" />
              <p className="text-sm text-amber-700">Chronic</p>
              <p className="text-2xl font-bold text-amber-800">{problems.filter(p => p.status === 'chronic').length}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-green-50 border-green-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <CheckCircle className="w-8 h-8 mx-auto mb-2 text-green-600" />
              <p className="text-sm text-green-700">Resolved</p>
              <p className="text-2xl font-bold text-green-800">{resolvedProblems.length}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-center">
              <AlertTriangle className="w-8 h-8 mx-auto mb-2 text-gray-400" />
              <p className="text-sm text-gray-600">Total</p>
              <p className="text-2xl font-bold">{problems.length}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Active Problems */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-600" />
              Active Problems
            </CardTitle>
            <CardDescription>Current health conditions requiring attention</CardDescription>
          </div>
          <Button onClick={() => setProblemDialogOpen(true)} className="gap-2" data-testid="add-problem-btn">
            <Plus className="w-4 h-4" /> Add Problem
          </Button>
        </CardHeader>
        <CardContent>
          {activeProblems.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-400 opacity-50" />
              <p>No active problems</p>
            </div>
          ) : (
            <div className="space-y-3">
              {activeProblems.map((problem) => (
                <div key={problem.id} className="p-4 border rounded-lg hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="font-medium">{problem.description}</p>
                        {getStatusBadge(problem.status)}
                      </div>
                      <div className="flex flex-wrap gap-4 text-sm text-gray-500">
                        {problem.icd_code && <span>ICD-10: {problem.icd_code}</span>}
                        {problem.onset_date && <span>Onset: {formatDate(problem.onset_date)}</span>}
                      </div>
                      {problem.notes && <p className="text-sm text-gray-600 mt-2 italic">{problem.notes}</p>}
                    </div>
                    <div className="flex gap-2 ml-4">
                      {problem.status === 'active' && (
                        <>
                          <Button size="sm" variant="outline" onClick={() => handleUpdateStatus(problem.id, 'chronic')}>
                            Mark Chronic
                          </Button>
                          <Button size="sm" variant="outline" className="text-green-600" onClick={() => handleUpdateStatus(problem.id, 'resolved')}>
                            Resolve
                          </Button>
                        </>
                      )}
                      {problem.status === 'chronic' && (
                        <Button size="sm" variant="outline" className="text-green-600" onClick={() => handleUpdateStatus(problem.id, 'resolved')}>
                          Resolve
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Resolved Problems */}
      {resolvedProblems.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-gray-600">
              <CheckCircle className="w-5 h-5" />
              Resolved Problems
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {resolvedProblems.map((problem) => (
                <div key={problem.id} className="p-3 border rounded-lg bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-600">{problem.description}</p>
                      <div className="flex gap-4 text-sm text-gray-400">
                        {problem.icd_code && <span>ICD-10: {problem.icd_code}</span>}
                        {problem.onset_date && <span>Onset: {formatDate(problem.onset_date)}</span>}
                      </div>
                    </div>
                    {getStatusBadge(problem.status)}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Add Problem Dialog */}
      <Dialog open={problemDialogOpen} onOpenChange={setProblemDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-600" />
              Add Problem
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Problem Description *</Label>
              <Input
                value={newProblem.description}
                onChange={(e) => setNewProblem({...newProblem, description: e.target.value})}
                placeholder="e.g., Type 2 Diabetes Mellitus"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>ICD-10 Code</Label>
                <Input
                  value={newProblem.icd_code}
                  onChange={(e) => setNewProblem({...newProblem, icd_code: e.target.value})}
                  placeholder="e.g., E11.9"
                />
              </div>
              <div className="space-y-2">
                <Label>Onset Date</Label>
                <Input
                  type="date"
                  value={newProblem.onset_date}
                  onChange={(e) => setNewProblem({...newProblem, onset_date: e.target.value})}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Status</Label>
              <Select value={newProblem.status} onValueChange={(v) => setNewProblem({...newProblem, status: v})}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="chronic">Chronic</SelectItem>
                  <SelectItem value="resolved">Resolved</SelectItem>
                  <SelectItem value="inactive">Inactive</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea
                value={newProblem.notes}
                onChange={(e) => setNewProblem({...newProblem, notes: e.target.value})}
                placeholder="Additional notes..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setProblemDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleAddProblem} disabled={saving} className="bg-emerald-600 hover:bg-emerald-700">
              {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Add Problem
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
