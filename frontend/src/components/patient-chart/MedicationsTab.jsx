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
import { Plus, Pill, Loader2, CheckCircle, Clock, XCircle, AlertTriangle } from 'lucide-react';
import { medicationsAPI } from '@/lib/api';
import { formatDate } from '@/lib/utils';

export default function MedicationsTab({ patientId, medications, onRefresh, user }) {
  const [medDialogOpen, setMedDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [newMedication, setNewMedication] = useState({
    name: '', dosage: '', frequency: '', route: 'oral', 
    start_date: '', end_date: '', status: 'active', notes: ''
  });

  const handleAddMedication = async () => {
    if (!newMedication.name) {
      toast.error('Medication name is required');
      return;
    }
    setSaving(true);
    try {
      await medicationsAPI.create({
        patient_id: patientId,
        ...newMedication
      });
      toast.success('Medication added successfully');
      setMedDialogOpen(false);
      setNewMedication({ name: '', dosage: '', frequency: '', route: 'oral', start_date: '', end_date: '', status: 'active', notes: '' });
      onRefresh();
    } catch (err) {
      toast.error('Failed to add medication');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateStatus = async (medId, newStatus) => {
    try {
      await medicationsAPI.update(medId, { status: newStatus });
      toast.success(`Medication marked as ${newStatus}`);
      onRefresh();
    } catch (err) {
      toast.error('Failed to update medication');
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      active: { className: 'bg-green-100 text-green-700', icon: CheckCircle },
      discontinued: { className: 'bg-red-100 text-red-700', icon: XCircle },
      on_hold: { className: 'bg-amber-100 text-amber-700', icon: Clock },
      completed: { className: 'bg-gray-100 text-gray-700', icon: CheckCircle }
    };
    const style = styles[status] || styles.active;
    const Icon = style.icon;
    return (
      <Badge className={`${style.className} gap-1`}>
        <Icon className="w-3 h-3" /> {status?.replace('_', ' ')}
      </Badge>
    );
  };

  const activeMeds = medications.filter(m => m.status === 'active');
  const inactiveMeds = medications.filter(m => m.status !== 'active');

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-green-50 border-green-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <Pill className="w-8 h-8 mx-auto mb-2 text-green-600" />
              <p className="text-sm text-green-700">Active</p>
              <p className="text-2xl font-bold text-green-800">{activeMeds.length}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-amber-50 border-amber-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <Clock className="w-8 h-8 mx-auto mb-2 text-amber-600" />
              <p className="text-sm text-amber-700">On Hold</p>
              <p className="text-2xl font-bold text-amber-800">{medications.filter(m => m.status === 'on_hold').length}</p>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-red-50 border-red-200">
          <CardContent className="pt-4">
            <div className="text-center">
              <XCircle className="w-8 h-8 mx-auto mb-2 text-red-600" />
              <p className="text-sm text-red-700">Discontinued</p>
              <p className="text-2xl font-bold text-red-800">{medications.filter(m => m.status === 'discontinued').length}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-center">
              <Pill className="w-8 h-8 mx-auto mb-2 text-gray-400" />
              <p className="text-sm text-gray-600">Total</p>
              <p className="text-2xl font-bold">{medications.length}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Active Medications */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Pill className="w-5 h-5 text-green-600" />
              Active Medications
            </CardTitle>
            <CardDescription>Current medication regimen</CardDescription>
          </div>
          <Button onClick={() => setMedDialogOpen(true)} className="gap-2" data-testid="add-medication-btn">
            <Plus className="w-4 h-4" /> Add Medication
          </Button>
        </CardHeader>
        <CardContent>
          {activeMeds.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Pill className="w-12 h-12 mx-auto mb-4 opacity-30" />
              <p>No active medications</p>
            </div>
          ) : (
            <div className="space-y-3">
              {activeMeds.map((med) => (
                <div key={med.id} className="p-4 border rounded-lg hover:bg-gray-50 border-green-200 bg-green-50/30">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="font-semibold text-lg">{med.name}</p>
                        {getStatusBadge(med.status)}
                      </div>
                      <div className="flex flex-wrap gap-4 text-sm">
                        {med.dosage && <span className="text-gray-700"><strong>Dosage:</strong> {med.dosage}</span>}
                        {med.frequency && <span className="text-gray-700"><strong>Frequency:</strong> {med.frequency}</span>}
                        {med.route && <span className="text-gray-700"><strong>Route:</strong> {med.route}</span>}
                      </div>
                      <div className="flex gap-4 text-sm text-gray-500 mt-1">
                        {med.start_date && <span>Started: {formatDate(med.start_date)}</span>}
                        {med.end_date && <span>Ends: {formatDate(med.end_date)}</span>}
                      </div>
                      {med.notes && <p className="text-sm text-gray-600 mt-2 italic">{med.notes}</p>}
                    </div>
                    <div className="flex gap-2 ml-4">
                      <Button size="sm" variant="outline" onClick={() => handleUpdateStatus(med.id, 'on_hold')}>
                        Hold
                      </Button>
                      <Button size="sm" variant="outline" className="text-red-600" onClick={() => handleUpdateStatus(med.id, 'discontinued')}>
                        Discontinue
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Inactive Medications */}
      {inactiveMeds.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-gray-600">
              <Pill className="w-5 h-5" />
              Medication History
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {inactiveMeds.map((med) => (
                <div key={med.id} className="p-3 border rounded-lg bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-600">{med.name}</p>
                      <div className="flex gap-4 text-sm text-gray-400">
                        {med.dosage && <span>{med.dosage}</span>}
                        {med.frequency && <span>{med.frequency}</span>}
                        {med.route && <span>{med.route}</span>}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {getStatusBadge(med.status)}
                      {med.status !== 'active' && (
                        <Button size="sm" variant="outline" onClick={() => handleUpdateStatus(med.id, 'active')}>
                          Reactivate
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Add Medication Dialog */}
      <Dialog open={medDialogOpen} onOpenChange={setMedDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Pill className="w-5 h-5 text-green-600" />
              Add Medication
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Medication Name *</Label>
              <Input
                value={newMedication.name}
                onChange={(e) => setNewMedication({...newMedication, name: e.target.value})}
                placeholder="e.g., Metformin"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Dosage</Label>
                <Input
                  value={newMedication.dosage}
                  onChange={(e) => setNewMedication({...newMedication, dosage: e.target.value})}
                  placeholder="e.g., 500mg"
                />
              </div>
              <div className="space-y-2">
                <Label>Frequency</Label>
                <Input
                  value={newMedication.frequency}
                  onChange={(e) => setNewMedication({...newMedication, frequency: e.target.value})}
                  placeholder="e.g., Twice daily"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Route</Label>
                <Select value={newMedication.route} onValueChange={(v) => setNewMedication({...newMedication, route: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="oral">Oral</SelectItem>
                    <SelectItem value="iv">IV</SelectItem>
                    <SelectItem value="im">IM</SelectItem>
                    <SelectItem value="sc">Subcutaneous</SelectItem>
                    <SelectItem value="topical">Topical</SelectItem>
                    <SelectItem value="inhaled">Inhaled</SelectItem>
                    <SelectItem value="rectal">Rectal</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Status</Label>
                <Select value={newMedication.status} onValueChange={(v) => setNewMedication({...newMedication, status: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="on_hold">On Hold</SelectItem>
                    <SelectItem value="discontinued">Discontinued</SelectItem>
                    <SelectItem value="completed">Completed</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Start Date</Label>
                <Input
                  type="date"
                  value={newMedication.start_date}
                  onChange={(e) => setNewMedication({...newMedication, start_date: e.target.value})}
                />
              </div>
              <div className="space-y-2">
                <Label>End Date</Label>
                <Input
                  type="date"
                  value={newMedication.end_date}
                  onChange={(e) => setNewMedication({...newMedication, end_date: e.target.value})}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea
                value={newMedication.notes}
                onChange={(e) => setNewMedication({...newMedication, notes: e.target.value})}
                placeholder="Instructions, precautions..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setMedDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleAddMedication} disabled={saving} className="bg-emerald-600 hover:bg-emerald-700">
              {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Add Medication
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
