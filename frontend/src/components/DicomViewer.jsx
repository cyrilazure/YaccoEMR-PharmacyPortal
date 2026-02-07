import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Dialog, DialogContent, DialogDescription,
  DialogHeader, DialogTitle, DialogFooter
} from '@/components/ui/dialog';
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
  Monitor, ZoomIn, ZoomOut, RotateCw, Move, Contrast,
  Ruler, PenTool, Maximize, ExternalLink, Search, RefreshCw,
  Image, Grid3X3, Layers, PlayCircle, PauseCircle, Info,
  Settings, Download, Share2, Loader2, AlertCircle
} from 'lucide-react';
import api from '@/lib/api';

// PACS/DICOM API
const pacsAPI = {
  getConfig: () => api.get('/pacs/config'),
  getStatus: () => api.get('/pacs/status'),
  searchStudies: (data) => api.post('/pacs/studies/search', data),
  getStudy: (studyUid) => api.get(`/pacs/studies/${studyUid}`),
  getViewerUrl: (studyUid, accession, patientId) => 
    api.get('/pacs/viewer/url', { params: { study_uid: studyUid, accession_number: accession, patient_id: patientId } }),
  getThumbnail: (studyUid) => api.get(`/pacs/studies/${studyUid}/thumbnail`),
  getWorklist: (params) => api.get('/pacs/worklist', { params }),
};

// Viewer Types
const VIEWER_TYPES = [
  { id: 'ohif', name: 'OHIF Viewer', description: 'Open-source HTML5 viewer', icon: '🔬' },
  { id: 'meddream', name: 'MedDream', description: 'Zero-footprint viewer', icon: '💊' },
  { id: 'weasis', name: 'Weasis', description: 'Desktop/Web viewer', icon: '🖥️' },
];

// Demo Studies (when PACS not configured)
const DEMO_STUDIES = [
  {
    study_instance_uid: '1.2.840.113619.2.5.1762583153.215519.978957063.121',
    patient_id: 'DEMO001',
    patient_name: 'Demo Patient A',
    study_date: '20250207',
    accession_number: 'ACC001',
    modality: 'CT',
    study_description: 'CT Chest with Contrast',
    number_of_series: 3,
    number_of_instances: 245,
  },
  {
    study_instance_uid: '1.2.840.113619.2.5.1762583153.215519.978957063.122',
    patient_id: 'DEMO002',
    patient_name: 'Demo Patient B',
    study_date: '20250207',
    accession_number: 'ACC002',
    modality: 'MR',
    study_description: 'MRI Brain without Contrast',
    number_of_series: 5,
    number_of_instances: 180,
  },
  {
    study_instance_uid: '1.2.840.113619.2.5.1762583153.215519.978957063.123',
    patient_id: 'DEMO003',
    patient_name: 'Demo Patient C',
    study_date: '20250206',
    accession_number: 'ACC003',
    modality: 'CR',
    study_description: 'Chest X-Ray 2 Views',
    number_of_series: 1,
    number_of_instances: 2,
  },
];

// Study List Component
function StudyList({ studies, onSelectStudy, selectedStudy }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Patient</TableHead>
          <TableHead>Accession</TableHead>
          <TableHead>Modality</TableHead>
          <TableHead>Description</TableHead>
          <TableHead>Date</TableHead>
          <TableHead>Images</TableHead>
          <TableHead>Action</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {studies.map((study) => (
          <TableRow 
            key={study.study_instance_uid}
            className={selectedStudy?.study_instance_uid === study.study_instance_uid ? 'bg-blue-50' : ''}
          >
            <TableCell>
              <div>
                <p className="font-medium">{study.patient_name}</p>
                <p className="text-xs text-gray-500">{study.patient_id}</p>
              </div>
            </TableCell>
            <TableCell className="font-mono text-sm">{study.accession_number}</TableCell>
            <TableCell>
              <Badge variant="outline">{study.modality}</Badge>
            </TableCell>
            <TableCell className="max-w-[200px] truncate">{study.study_description}</TableCell>
            <TableCell>
              {study.study_date?.substring(0, 4)}-{study.study_date?.substring(4, 6)}-{study.study_date?.substring(6, 8)}
            </TableCell>
            <TableCell>{study.number_of_instances || '-'}</TableCell>
            <TableCell>
              <Button 
                size="sm" 
                onClick={() => onSelectStudy(study)}
                variant={selectedStudy?.study_instance_uid === study.study_instance_uid ? 'default' : 'outline'}
              >
                <Image className="w-4 h-4 mr-1" />
                View
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

// Viewer Selection Component
function ViewerSelector({ selectedViewer, onSelectViewer, viewerUrls }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-4">
        {VIEWER_TYPES.map((viewer) => (
          <Card 
            key={viewer.id}
            className={`cursor-pointer transition-all ${
              selectedViewer === viewer.id 
                ? 'ring-2 ring-blue-500 bg-blue-50' 
                : 'hover:bg-gray-50'
            }`}
            onClick={() => onSelectViewer(viewer.id)}
          >
            <CardContent className="pt-4 text-center">
              <span className="text-3xl">{viewer.icon}</span>
              <h3 className="font-semibold mt-2">{viewer.name}</h3>
              <p className="text-xs text-gray-500">{viewer.description}</p>
              {viewerUrls?.[viewer.id] && (
                <Badge className="mt-2 bg-green-100 text-green-700">Available</Badge>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// Mock Viewer Display (when PACS not connected)
function MockViewerDisplay({ study, toolSelected, onToolSelect }) {
  const tools = [
    { id: 'zoom_in', icon: ZoomIn, label: 'Zoom In' },
    { id: 'zoom_out', icon: ZoomOut, label: 'Zoom Out' },
    { id: 'rotate', icon: RotateCw, label: 'Rotate' },
    { id: 'pan', icon: Move, label: 'Pan' },
    { id: 'contrast', icon: Contrast, label: 'Window/Level' },
    { id: 'ruler', icon: Ruler, label: 'Measure' },
    { id: 'annotate', icon: PenTool, label: 'Annotate' },
    { id: 'fullscreen', icon: Maximize, label: 'Fullscreen' },
  ];

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex gap-1 p-2 bg-gray-100 rounded-t-lg border-b">
        {tools.map((tool) => (
          <Button
            key={tool.id}
            size="sm"
            variant={toolSelected === tool.id ? 'default' : 'outline'}
            onClick={() => onToolSelect(tool.id)}
            className="h-8 w-8 p-0"
            title={tool.label}
          >
            <tool.icon className="w-4 h-4" />
          </Button>
        ))}
        <Separator orientation="vertical" className="mx-2 h-8" />
        <Button size="sm" variant="outline" className="h-8 px-2">
          <Grid3X3 className="w-4 h-4 mr-1" /> 1x1
        </Button>
        <Button size="sm" variant="outline" className="h-8 px-2">
          <Layers className="w-4 h-4 mr-1" /> Series
        </Button>
      </div>

      {/* Image Display Area */}
      <div className="flex-1 bg-black rounded-b-lg flex items-center justify-center min-h-[400px]">
        <div className="text-center text-white">
          <AlertCircle className="w-16 h-16 mx-auto mb-4 text-gray-500" />
          <h3 className="text-lg font-semibold mb-2">Demo Mode</h3>
          <p className="text-gray-400 text-sm max-w-md">
            PACS server not configured. Connect to a dcm4chee server<br />
            to view real DICOM images.
          </p>
          {study && (
            <div className="mt-4 p-4 bg-gray-900 rounded-lg text-left text-sm">
              <p><span className="text-gray-500">Study:</span> {study.study_description}</p>
              <p><span className="text-gray-500">Patient:</span> {study.patient_name}</p>
              <p><span className="text-gray-500">Modality:</span> {study.modality}</p>
              <p><span className="text-gray-500">Images:</span> {study.number_of_instances}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// External Viewer Embed/Launch Component
function ExternalViewerEmbed({ viewerUrl, viewerType, study }) {
  const [loading, setLoading] = useState(true);

  if (!viewerUrl) {
    return (
      <div className="flex items-center justify-center h-[500px] bg-gray-100 rounded-lg">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 mx-auto mb-4 text-gray-400" />
          <p className="text-gray-600">No viewer URL configured</p>
          <p className="text-sm text-gray-500">Configure DICOM_VIEWER_URL in environment</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative h-[500px] rounded-lg overflow-hidden border">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 z-10">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      )}
      <iframe
        src={viewerUrl}
        className="w-full h-full"
        title={`${viewerType} DICOM Viewer`}
        onLoad={() => setLoading(false)}
        frameBorder="0"
        allow="fullscreen"
      />
      <div className="absolute top-2 right-2">
        <Button
          size="sm"
          variant="secondary"
          className="gap-2"
          onClick={() => window.open(viewerUrl, '_blank')}
        >
          <ExternalLink className="w-4 h-4" />
          Open in New Tab
        </Button>
      </div>
    </div>
  );
}

// Main DICOM Viewer Component
export default function DicomViewer({ 
  patientId, 
  studyUid,
  accessionNumber,
  embedded = false,
  onStudySelect 
}) {
  const [loading, setLoading] = useState(true);
  const [pacsConfig, setPacsConfig] = useState(null);
  const [pacsStatus, setPacsStatus] = useState(null);
  const [studies, setStudies] = useState([]);
  const [selectedStudy, setSelectedStudy] = useState(null);
  const [selectedViewer, setSelectedViewer] = useState('ohif');
  const [viewerUrl, setViewerUrl] = useState(null);
  const [toolSelected, setToolSelected] = useState('pan');
  const [searchParams, setSearchParams] = useState({
    patient_id: patientId || '',
    patient_name: '',
    accession_number: accessionNumber || '',
    modality: '',
    limit: 50
  });

  // Fetch PACS configuration
  const fetchPacsConfig = useCallback(async () => {
    try {
      const [configRes, statusRes] = await Promise.all([
        pacsAPI.getConfig(),
        pacsAPI.getStatus()
      ]);
      setPacsConfig(configRes.data);
      setPacsStatus(statusRes.data);
    } catch (err) {
      console.error('Failed to fetch PACS config:', err);
      setPacsConfig({ status: 'demo_mode' });
    }
  }, []);

  // Search studies
  const searchStudies = useCallback(async () => {
    setLoading(true);
    try {
      const response = await pacsAPI.searchStudies(searchParams);
      if (response.data.mode === 'demo') {
        // Use demo studies in demo mode
        setStudies(DEMO_STUDIES);
      } else {
        setStudies(response.data.studies || []);
      }
    } catch (err) {
      console.error('Failed to search studies:', err);
      // Fallback to demo studies
      setStudies(DEMO_STUDIES);
    } finally {
      setLoading(false);
    }
  }, [searchParams]);

  // Get viewer URL for selected study
  const fetchViewerUrl = useCallback(async (study) => {
    try {
      const response = await pacsAPI.getViewerUrl(
        study.study_instance_uid,
        study.accession_number,
        study.patient_id
      );
      setViewerUrl(response.data.viewer_url);
    } catch (err) {
      console.error('Failed to get viewer URL:', err);
      // Generate demo viewer URLs
      const demoUrls = {
        ohif: `https://viewer.ohif.org/viewer?StudyInstanceUIDs=${study.study_instance_uid}`,
        meddream: `https://demo.meddream.com/?study=${study.study_instance_uid}`,
        weasis: null
      };
      setViewerUrl(demoUrls[selectedViewer]);
    }
  }, [selectedViewer]);

  useEffect(() => {
    fetchPacsConfig();
  }, [fetchPacsConfig]);

  useEffect(() => {
    searchStudies();
  }, [searchStudies]);

  useEffect(() => {
    if (selectedStudy) {
      fetchViewerUrl(selectedStudy);
      onStudySelect?.(selectedStudy);
    }
  }, [selectedStudy, fetchViewerUrl, onStudySelect]);

  // Handle study selection from props
  useEffect(() => {
    if (studyUid && studies.length > 0) {
      const study = studies.find(s => s.study_instance_uid === studyUid);
      if (study) setSelectedStudy(study);
    }
  }, [studyUid, studies]);

  const isConnected = pacsStatus?.status === 'connected';

  return (
    <div className="space-y-4" data-testid="dicom-viewer">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Monitor className="w-6 h-6 text-purple-600" />
            DICOM Viewer
          </h2>
          <p className="text-sm text-gray-500">
            {isConnected ? (
              <Badge className="bg-green-100 text-green-700">Connected to {pacsConfig?.pacs_host}</Badge>
            ) : (
              <Badge variant="outline" className="text-amber-600">Demo Mode - No PACS Connected</Badge>
            )}
          </p>
        </div>
        <Button onClick={searchStudies} variant="outline" className="gap-2">
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {!embedded && (
        <>
          {/* Search Form */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Search className="w-4 h-4" /> Search Studies
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div>
                  <Label className="text-xs">Patient ID</Label>
                  <Input
                    value={searchParams.patient_id}
                    onChange={(e) => setSearchParams({...searchParams, patient_id: e.target.value})}
                    placeholder="MRN..."
                  />
                </div>
                <div>
                  <Label className="text-xs">Patient Name</Label>
                  <Input
                    value={searchParams.patient_name}
                    onChange={(e) => setSearchParams({...searchParams, patient_name: e.target.value})}
                    placeholder="Name..."
                  />
                </div>
                <div>
                  <Label className="text-xs">Accession #</Label>
                  <Input
                    value={searchParams.accession_number}
                    onChange={(e) => setSearchParams({...searchParams, accession_number: e.target.value})}
                    placeholder="ACC..."
                  />
                </div>
                <div>
                  <Label className="text-xs">Modality</Label>
                  <Select
                    value={searchParams.modality}
                    onValueChange={(v) => setSearchParams({...searchParams, modality: v === 'all' ? '' : v})}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All</SelectItem>
                      <SelectItem value="CT">CT</SelectItem>
                      <SelectItem value="MR">MRI</SelectItem>
                      <SelectItem value="CR">X-Ray</SelectItem>
                      <SelectItem value="US">Ultrasound</SelectItem>
                      <SelectItem value="MG">Mammography</SelectItem>
                      <SelectItem value="NM">Nuclear</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-end">
                  <Button onClick={searchStudies} className="w-full">
                    <Search className="w-4 h-4 mr-2" /> Search
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Study List */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Studies ({studies.length})</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[250px]">
                {loading ? (
                  <div className="flex items-center justify-center h-full">
                    <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
                  </div>
                ) : studies.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    No studies found
                  </div>
                ) : (
                  <StudyList 
                    studies={studies} 
                    onSelectStudy={setSelectedStudy}
                    selectedStudy={selectedStudy}
                  />
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </>
      )}

      {/* Viewer Selection & Display */}
      {selectedStudy && (
        <Card>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm">
                Viewing: {selectedStudy.study_description}
              </CardTitle>
              <div className="flex gap-2">
                {VIEWER_TYPES.map((v) => (
                  <Button
                    key={v.id}
                    size="sm"
                    variant={selectedViewer === v.id ? 'default' : 'outline'}
                    onClick={() => setSelectedViewer(v.id)}
                  >
                    {v.icon} {v.name}
                  </Button>
                ))}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {isConnected && viewerUrl ? (
              <ExternalViewerEmbed 
                viewerUrl={viewerUrl}
                viewerType={selectedViewer}
                study={selectedStudy}
              />
            ) : (
              <MockViewerDisplay 
                study={selectedStudy}
                toolSelected={toolSelected}
                onToolSelect={setToolSelected}
              />
            )}
          </CardContent>
        </Card>
      )}

      {/* PACS Setup Instructions (when not connected) */}
      {!isConnected && (
        <Card className="border-amber-200 bg-amber-50">
          <CardHeader>
            <CardTitle className="text-sm text-amber-800 flex items-center gap-2">
              <Settings className="w-4 h-4" /> PACS Configuration
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-amber-700 space-y-2">
            <p>To connect to a real PACS server, set these environment variables:</p>
            <div className="bg-white p-3 rounded-lg font-mono text-xs">
              <p>PACS_HOST=your-dcm4chee-server.com</p>
              <p>PACS_PORT=8080</p>
              <p>PACS_AE_TITLE=DCM4CHEE</p>
              <p>DICOM_VIEWER_URL=https://your-viewer.com</p>
            </div>
            <p className="mt-2">
              <strong>Recommended PACS:</strong> <a href="https://www.dcm4che.org/" className="underline" target="_blank" rel="noopener noreferrer">dcm4chee Archive</a>
            </p>
            <p>
              <strong>Viewers:</strong>{' '}
              <a href="https://ohif.org/" className="underline" target="_blank" rel="noopener noreferrer">OHIF</a>,{' '}
              <a href="https://www.meddream.com/" className="underline" target="_blank" rel="noopener noreferrer">MedDream</a>,{' '}
              <a href="https://nroduit.github.io/en/" className="underline" target="_blank" rel="noopener noreferrer">Weasis</a>
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
