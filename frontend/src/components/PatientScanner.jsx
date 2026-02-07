import { useState, useEffect } from 'react';
import { useZxing } from 'react-zxing';
import { patientAPI } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { toast } from 'sonner';
import { formatDate, calculateAge } from '@/lib/utils';
import {
  QrCode, Camera, X, User, Calendar, Phone, Mail, MapPin,
  Shield, AlertCircle, CheckCircle, Search, Loader2, ScanLine
} from 'lucide-react';

export default function PatientScanner({ onPatientFound, buttonLabel = "Scan Patient" }) {
  const [scannerOpen, setScannerOpen] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [scannedPatient, setScannedPatient] = useState(null);
  const [searching, setSearching] = useState(false);
  const [manualMRN, setManualMRN] = useState('');
  const [error, setError] = useState(null);

  const { ref } = useZxing({
    onDecodeResult(result) {
      handleScanResult(result.getText());
    },
    onError(error) {
      console.error('Scanner error:', error);
    },
    paused: !scanning,
  });

  const handleScanResult = async (data) => {
    setScanning(false);
    setSearching(true);
    setError(null);

    try {
      // Try to parse as JSON (QR code format)
      let patientData;
      let isQRCode = false;
      try {
        patientData = JSON.parse(data);
        isQRCode = true;
      } catch {
        // If not JSON, treat as MRN directly
        patientData = { mrn: data };
      }

      const mrn = patientData.mrn || data;
      
      // Search for patient by MRN
      const response = await patientAPI.getAll({ search: mrn });
      const patients = response.data.patients || response.data || [];
      
      // Find exact MRN match
      const patient = patients.find(p => p.mrn === mrn);
      
      if (patient) {
        // Patient found in database - use full database record
        setScannedPatient({
          ...patient,
          physician: patientData.physician || 'Not Assigned',
          fromQR: isQRCode
        });
        toast.success(`Patient found: ${patient.first_name} ${patient.last_name}`);
        if (onPatientFound) {
          onPatientFound(patient);
        }
      } else if (isQRCode && patientData.firstName && patientData.lastName) {
        // Patient not in database but we have QR data - display QR info
        setScannedPatient({
          mrn: patientData.mrn,
          first_name: patientData.firstName,
          last_name: patientData.lastName,
          date_of_birth: patientData.dob,
          physician: patientData.physician || 'Not Assigned',
          fromQR: true,
          notInDatabase: true
        });
        toast.warning('Patient scanned but not found in local database');
      } else {
        setError(`No patient found with MRN: ${mrn}`);
        toast.error('Patient not found');
      }
    } catch (err) {
      console.error('Search error:', err);
      
      // Even if search fails, try to display QR data if available
      try {
        const patientData = JSON.parse(data);
        if (patientData.firstName && patientData.lastName) {
          setScannedPatient({
            mrn: patientData.mrn,
            first_name: patientData.firstName,
            last_name: patientData.lastName,
            date_of_birth: patientData.dob,
            physician: patientData.physician || 'Not Assigned',
            fromQR: true,
            notInDatabase: true
          });
          toast.warning('Displaying scanned data (database unavailable)');
          return;
        }
      } catch {
        // Not valid JSON
      }
      
      setError('Failed to search for patient');
      toast.error('Failed to search for patient');
    } finally {
      setSearching(false);
    }
  };

  const handleManualSearch = async () => {
    if (!manualMRN.trim()) {
      toast.error('Please enter an MRN');
      return;
    }
    await handleScanResult(manualMRN.trim());
  };

  const startScanning = () => {
    setScanning(true);
    setScannedPatient(null);
    setError(null);
  };

  const stopScanning = () => {
    setScanning(false);
  };

  const closeDialog = () => {
    setScannerOpen(false);
    setScanning(false);
    setScannedPatient(null);
    setError(null);
    setManualMRN('');
  };

  return (
    <>
      <Button 
        onClick={() => setScannerOpen(true)} 
        variant="outline" 
        className="gap-2"
      >
        <QrCode className="w-4 h-4" />
        {buttonLabel}
      </Button>

      <Dialog open={scannerOpen} onOpenChange={closeDialog}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ScanLine className="w-5 h-5 text-sky-600" />
              Patient Identification Scanner
            </DialogTitle>
            <DialogDescription>
              Scan patient barcode/QR code or enter MRN manually to verify identity
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            {/* Scanner View */}
            {scanning ? (
              <div className="relative">
                <div className="aspect-square bg-black rounded-lg overflow-hidden">
                  <video ref={ref} className="w-full h-full object-cover" />
                </div>
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div className="w-48 h-48 border-2 border-sky-500 rounded-lg animate-pulse" />
                </div>
                <Button 
                  onClick={stopScanning} 
                  variant="destructive" 
                  size="sm"
                  className="absolute top-2 right-2"
                >
                  <X className="w-4 h-4" />
                </Button>
                <p className="text-center text-sm text-slate-500 mt-2">
                  Position barcode or QR code within the frame
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Start Scanner Button */}
                <Button 
                  onClick={startScanning} 
                  className="w-full bg-sky-600 hover:bg-sky-700 gap-2 h-16 text-lg"
                >
                  <Camera className="w-6 h-6" />
                  Start Camera Scanner
                </Button>

                <div className="flex items-center gap-4">
                  <Separator className="flex-1" />
                  <span className="text-sm text-slate-500">or</span>
                  <Separator className="flex-1" />
                </div>

                {/* Manual MRN Entry */}
                <div className="space-y-2">
                  <p className="text-sm font-medium text-slate-700">Enter MRN Manually</p>
                  <div className="flex gap-2">
                    <Input
                      placeholder="Enter patient MRN..."
                      value={manualMRN}
                      onChange={(e) => setManualMRN(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleManualSearch()}
                      className="flex-1"
                    />
                    <Button onClick={handleManualSearch} disabled={searching}>
                      {searching ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Search className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* Loading State */}
            {searching && (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-8 h-8 animate-spin text-sky-600" />
                <span className="ml-2 text-slate-600">Searching for patient...</span>
              </div>
            )}

            {/* Error State */}
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="w-4 h-4" />
                <AlertTitle>Not Found</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Patient Found */}
            {scannedPatient && (
              <Card className="border-emerald-300 bg-emerald-50">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-emerald-800 flex items-center gap-2">
                      <CheckCircle className="w-5 h-5" />
                      Patient Verified
                    </CardTitle>
                    <Badge className="bg-emerald-600">CONFIRMED</Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Patient Identity */}
                  <div className="flex items-center gap-4">
                    <div className="w-16 h-16 rounded-full bg-emerald-200 text-emerald-700 flex items-center justify-center text-xl font-bold">
                      {scannedPatient.first_name?.[0]}{scannedPatient.last_name?.[0]}
                    </div>
                    <div>
                      <p className="text-xl font-bold text-slate-900">
                        {scannedPatient.first_name} {scannedPatient.last_name}
                      </p>
                      <p className="text-lg font-mono font-semibold text-emerald-700">
                        MRN: {scannedPatient.mrn}
                      </p>
                    </div>
                  </div>

                  <Separator />

                  {/* Patient Details */}
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4 text-slate-400" />
                      <div>
                        <p className="text-slate-500">Date of Birth</p>
                        <p className="font-medium">
                          {formatDate(scannedPatient.date_of_birth)}
                          {scannedPatient.date_of_birth && (
                            <span className="text-slate-500 ml-1">
                              ({calculateAge(scannedPatient.date_of_birth)} yrs)
                            </span>
                          )}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <User className="w-4 h-4 text-slate-400" />
                      <div>
                        <p className="text-slate-500">Gender</p>
                        <p className="font-medium capitalize">{scannedPatient.gender || 'N/A'}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Phone className="w-4 h-4 text-slate-400" />
                      <div>
                        <p className="text-slate-500">Phone</p>
                        <p className="font-medium">{scannedPatient.phone || 'N/A'}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Mail className="w-4 h-4 text-slate-400" />
                      <div>
                        <p className="text-slate-500">Email</p>
                        <p className="font-medium truncate">{scannedPatient.email || 'N/A'}</p>
                      </div>
                    </div>
                  </div>

                  {/* Address */}
                  {scannedPatient.address && (
                    <div className="flex items-start gap-2 text-sm">
                      <MapPin className="w-4 h-4 text-slate-400 mt-0.5" />
                      <div>
                        <p className="text-slate-500">Address</p>
                        <p className="font-medium">{scannedPatient.address}</p>
                      </div>
                    </div>
                  )}

                  {/* Emergency Contact */}
                  {(scannedPatient.emergency_contact_name || scannedPatient.emergency_contact_phone) && (
                    <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                      <p className="text-sm font-medium text-red-800 flex items-center gap-2 mb-1">
                        <AlertCircle className="w-4 h-4" />
                        Emergency Contact
                      </p>
                      <p className="text-sm">
                        {scannedPatient.emergency_contact_name || 'N/A'} - {scannedPatient.emergency_contact_phone || 'N/A'}
                      </p>
                    </div>
                  )}

                  {/* Insurance */}
                  {(scannedPatient.insurance_provider || scannedPatient.insurance_id) && (
                    <div className="p-3 bg-sky-50 border border-sky-200 rounded-lg">
                      <p className="text-sm font-medium text-sky-800 flex items-center gap-2 mb-1">
                        <Shield className="w-4 h-4" />
                        Insurance
                      </p>
                      <p className="text-sm">
                        {scannedPatient.insurance_provider || 'N/A'} - {scannedPatient.insurance_id || 'N/A'}
                      </p>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex gap-2 pt-2">
                    <Button 
                      onClick={() => {
                        setScannedPatient(null);
                        setManualMRN('');
                      }}
                      variant="outline"
                      className="flex-1"
                    >
                      Scan Another
                    </Button>
                    <Button 
                      onClick={closeDialog}
                      className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                    >
                      Confirm & Close
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
