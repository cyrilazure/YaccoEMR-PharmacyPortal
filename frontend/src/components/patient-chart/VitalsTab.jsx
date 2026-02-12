import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { toast } from 'sonner';
import { Plus, Activity, Thermometer, Droplets, Wind, Scale, Ruler, Heart, Loader2 } from 'lucide-react';
import { vitalsAPI } from '@/lib/api';
import { formatDateTime } from '@/lib/utils';

export default function VitalsTab({ patientId, vitals, onRefresh, user }) {
  const [vitalsDialogOpen, setVitalsDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [newVitals, setNewVitals] = useState({
    blood_pressure_systolic: '', blood_pressure_diastolic: '',
    heart_rate: '', respiratory_rate: '', temperature: '',
    oxygen_saturation: '', weight: '', height: '', notes: ''
  });

  const handleAddVitals = async () => {
    setSaving(true);
    try {
      const vitalsData = {
        patient_id: patientId,
        blood_pressure_systolic: newVitals.blood_pressure_systolic ? parseInt(newVitals.blood_pressure_systolic) : null,
        blood_pressure_diastolic: newVitals.blood_pressure_diastolic ? parseInt(newVitals.blood_pressure_diastolic) : null,
        heart_rate: newVitals.heart_rate ? parseInt(newVitals.heart_rate) : null,
        respiratory_rate: newVitals.respiratory_rate ? parseInt(newVitals.respiratory_rate) : null,
        temperature: newVitals.temperature ? parseFloat(newVitals.temperature) : null,
        oxygen_saturation: newVitals.oxygen_saturation ? parseInt(newVitals.oxygen_saturation) : null,
        weight: newVitals.weight ? parseFloat(newVitals.weight) : null,
        height: newVitals.height ? parseFloat(newVitals.height) : null,
        notes: newVitals.notes
      };
      await vitalsAPI.create(vitalsData);
      toast.success('Vitals recorded successfully');
      setVitalsDialogOpen(false);
      setNewVitals({
        blood_pressure_systolic: '', blood_pressure_diastolic: '',
        heart_rate: '', respiratory_rate: '', temperature: '',
        oxygen_saturation: '', weight: '', height: '', notes: ''
      });
      onRefresh();
    } catch (err) {
      toast.error('Failed to record vitals');
    } finally {
      setSaving(false);
    }
  };

  const latestVitals = vitals[0];

  const getVitalStatus = (type, value) => {
    if (!value) return 'normal';
    const ranges = {
      systolic: { low: 90, high: 140 },
      diastolic: { low: 60, high: 90 },
      heart_rate: { low: 60, high: 100 },
      respiratory_rate: { low: 12, high: 20 },
      temperature: { low: 36.1, high: 37.2 },
      oxygen_saturation: { low: 95, high: 100 }
    };
    const range = ranges[type];
    if (!range) return 'normal';
    if (value < range.low) return 'low';
    if (value > range.high) return 'high';
    return 'normal';
  };

  const getStatusColor = (status) => {
    if (status === 'high') return 'text-red-600 bg-red-50 border-red-200';
    if (status === 'low') return 'text-blue-600 bg-blue-50 border-blue-200';
    return 'text-gray-700 bg-gray-50 border-gray-200';
  };

  return (
    <div className="space-y-6">
      {/* Current Vitals Summary */}
      {latestVitals && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Current Vitals</CardTitle>
            <CardDescription>Recorded: {formatDateTime(latestVitals.recorded_at)}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {latestVitals.blood_pressure_systolic && (
                <div className={`p-4 rounded-lg border ${getStatusColor(getVitalStatus('systolic', latestVitals.blood_pressure_systolic))}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <Droplets className="w-5 h-5" />
                    <span className="text-sm font-medium">Blood Pressure</span>
                  </div>
                  <p className="text-2xl font-bold">
                    {latestVitals.blood_pressure_systolic}/{latestVitals.blood_pressure_diastolic}
                    <span className="text-sm font-normal ml-1">mmHg</span>
                  </p>
                </div>
              )}
              {latestVitals.heart_rate && (
                <div className={`p-4 rounded-lg border ${getStatusColor(getVitalStatus('heart_rate', latestVitals.heart_rate))}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <Heart className="w-5 h-5" />
                    <span className="text-sm font-medium">Heart Rate</span>
                  </div>
                  <p className="text-2xl font-bold">
                    {latestVitals.heart_rate}
                    <span className="text-sm font-normal ml-1">bpm</span>
                  </p>
                </div>
              )}
              {latestVitals.respiratory_rate && (
                <div className={`p-4 rounded-lg border ${getStatusColor(getVitalStatus('respiratory_rate', latestVitals.respiratory_rate))}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <Wind className="w-5 h-5" />
                    <span className="text-sm font-medium">Respiratory Rate</span>
                  </div>
                  <p className="text-2xl font-bold">
                    {latestVitals.respiratory_rate}
                    <span className="text-sm font-normal ml-1">/min</span>
                  </p>
                </div>
              )}
              {latestVitals.temperature && (
                <div className={`p-4 rounded-lg border ${getStatusColor(getVitalStatus('temperature', latestVitals.temperature))}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <Thermometer className="w-5 h-5" />
                    <span className="text-sm font-medium">Temperature</span>
                  </div>
                  <p className="text-2xl font-bold">
                    {latestVitals.temperature}
                    <span className="text-sm font-normal ml-1">°C</span>
                  </p>
                </div>
              )}
              {latestVitals.oxygen_saturation && (
                <div className={`p-4 rounded-lg border ${getStatusColor(getVitalStatus('oxygen_saturation', latestVitals.oxygen_saturation))}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <Activity className="w-5 h-5" />
                    <span className="text-sm font-medium">O₂ Saturation</span>
                  </div>
                  <p className="text-2xl font-bold">
                    {latestVitals.oxygen_saturation}
                    <span className="text-sm font-normal ml-1">%</span>
                  </p>
                </div>
              )}
              {latestVitals.weight && (
                <div className="p-4 rounded-lg border bg-gray-50 border-gray-200">
                  <div className="flex items-center gap-2 mb-2">
                    <Scale className="w-5 h-5 text-gray-600" />
                    <span className="text-sm font-medium text-gray-700">Weight</span>
                  </div>
                  <p className="text-2xl font-bold text-gray-700">
                    {latestVitals.weight}
                    <span className="text-sm font-normal ml-1">kg</span>
                  </p>
                </div>
              )}
              {latestVitals.height && (
                <div className="p-4 rounded-lg border bg-gray-50 border-gray-200">
                  <div className="flex items-center gap-2 mb-2">
                    <Ruler className="w-5 h-5 text-gray-600" />
                    <span className="text-sm font-medium text-gray-700">Height</span>
                  </div>
                  <p className="text-2xl font-bold text-gray-700">
                    {latestVitals.height}
                    <span className="text-sm font-normal ml-1">cm</span>
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Vitals History */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Vitals History</CardTitle>
            <CardDescription>{vitals.length} recordings</CardDescription>
          </div>
          <Button onClick={() => setVitalsDialogOpen(true)} className="gap-2" data-testid="add-vitals-btn">
            <Plus className="w-4 h-4" /> Record Vitals
          </Button>
        </CardHeader>
        <CardContent>
          {vitals.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Activity className="w-12 h-12 mx-auto mb-4 opacity-30" />
              <p>No vitals recorded yet</p>
            </div>
          ) : (
            <div className="space-y-4">
              {vitals.slice(0, 10).map((v, index) => (
                <div key={v.id || index} className="p-4 border rounded-lg hover:bg-gray-50">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-500">{formatDateTime(v.recorded_at)}</span>
                    <span className="text-xs text-gray-400">Recorded by: {v.recorded_by_name}</span>
                  </div>
                  <div className="flex flex-wrap gap-4 text-sm">
                    {v.blood_pressure_systolic && (
                      <span><strong>BP:</strong> {v.blood_pressure_systolic}/{v.blood_pressure_diastolic} mmHg</span>
                    )}
                    {v.heart_rate && <span><strong>HR:</strong> {v.heart_rate} bpm</span>}
                    {v.respiratory_rate && <span><strong>RR:</strong> {v.respiratory_rate}/min</span>}
                    {v.temperature && <span><strong>Temp:</strong> {v.temperature}°C</span>}
                    {v.oxygen_saturation && <span><strong>SpO₂:</strong> {v.oxygen_saturation}%</span>}
                    {v.weight && <span><strong>Wt:</strong> {v.weight} kg</span>}
                  </div>
                  {v.notes && <p className="text-sm text-gray-600 mt-2 italic">{v.notes}</p>}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add Vitals Dialog */}
      <Dialog open={vitalsDialogOpen} onOpenChange={setVitalsDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-emerald-600" />
              Record Vitals
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Systolic BP (mmHg)</Label>
                <Input
                  type="number"
                  value={newVitals.blood_pressure_systolic}
                  onChange={(e) => setNewVitals({...newVitals, blood_pressure_systolic: e.target.value})}
                  placeholder="120"
                />
              </div>
              <div className="space-y-2">
                <Label>Diastolic BP (mmHg)</Label>
                <Input
                  type="number"
                  value={newVitals.blood_pressure_diastolic}
                  onChange={(e) => setNewVitals({...newVitals, blood_pressure_diastolic: e.target.value})}
                  placeholder="80"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Heart Rate (bpm)</Label>
                <Input
                  type="number"
                  value={newVitals.heart_rate}
                  onChange={(e) => setNewVitals({...newVitals, heart_rate: e.target.value})}
                  placeholder="72"
                />
              </div>
              <div className="space-y-2">
                <Label>Respiratory Rate (/min)</Label>
                <Input
                  type="number"
                  value={newVitals.respiratory_rate}
                  onChange={(e) => setNewVitals({...newVitals, respiratory_rate: e.target.value})}
                  placeholder="16"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Temperature (°C)</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={newVitals.temperature}
                  onChange={(e) => setNewVitals({...newVitals, temperature: e.target.value})}
                  placeholder="36.5"
                />
              </div>
              <div className="space-y-2">
                <Label>O₂ Saturation (%)</Label>
                <Input
                  type="number"
                  value={newVitals.oxygen_saturation}
                  onChange={(e) => setNewVitals({...newVitals, oxygen_saturation: e.target.value})}
                  placeholder="98"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Weight (kg)</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={newVitals.weight}
                  onChange={(e) => setNewVitals({...newVitals, weight: e.target.value})}
                  placeholder="70"
                />
              </div>
              <div className="space-y-2">
                <Label>Height (cm)</Label>
                <Input
                  type="number"
                  value={newVitals.height}
                  onChange={(e) => setNewVitals({...newVitals, height: e.target.value})}
                  placeholder="170"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea
                value={newVitals.notes}
                onChange={(e) => setNewVitals({...newVitals, notes: e.target.value})}
                placeholder="Additional observations..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setVitalsDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleAddVitals} disabled={saving} className="bg-emerald-600 hover:bg-emerald-700">
              {saving && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Save Vitals
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
