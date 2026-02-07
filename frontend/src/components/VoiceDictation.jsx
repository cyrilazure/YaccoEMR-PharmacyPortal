import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import {
  Mic,
  MicOff,
  Square,
  Loader2,
  Wand2,
  Copy,
  Check,
  Settings,
  Volume2,
  AlertCircle,
  Sparkles,
} from 'lucide-react';
import api from '@/lib/api';
import { cn } from '@/lib/utils';

// Voice Dictation API
const voiceAPI = {
  transcribe: (formData) => api.post('/voice-dictation/transcribe', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  correctTerminology: (data) => api.post('/voice-dictation/correct-terminology', data),
  aiExpand: (text, noteType, context) => api.post('/voice-dictation/ai-expand', null, {
    params: { text, note_type: noteType, context }
  }),
};

/**
 * VoiceDictation Component
 * 
 * A reusable voice dictation component that supports both:
 * 1. OpenAI Whisper (server-side, high accuracy)
 * 2. Browser Web Speech API (client-side, real-time)
 * 
 * Features:
 * - Medical terminology auto-correction
 * - Context-aware transcription (radiology, nursing, clinical)
 * - Auto-populate to target fields
 * 
 * Usage:
 * <VoiceDictation
 *   onTranscriptionComplete={(text) => setFieldValue(text)}
 *   context="radiology"
 *   targetField="findings"
 *   appendMode={false}
 * />
 */
export default function VoiceDictation({
  onTranscriptionComplete,
  context = 'general', // general, radiology, nursing, clinical
  targetField = null, // Optional: field name being populated
  appendMode = false, // Append to existing text or replace
  currentValue = '', // Current value of target field (for append mode)
  className = '',
  buttonVariant = 'outline',
  buttonSize = 'sm',
  showLabel = true,
  disabled = false,
}) {
  // State
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcribedText, setTranscribedText] = useState('');
  const [correctedText, setCorrectedText] = useState('');
  const [corrections, setCorrections] = useState([]);
  const [showResultDialog, setShowResultDialog] = useState(false);
  const [showSettingsDialog, setShowSettingsDialog] = useState(false);
  const [copied, setCopied] = useState(false);
  
  // Settings
  const [settings, setSettings] = useState({
    method: 'whisper', // whisper or browser
    autoCorrect: true,
    language: 'en',
  });
  
  // Refs
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recognitionRef = useRef(null);
  const streamRef = useRef(null);
  
  // Browser Speech Recognition setup
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = settings.language;
      
      recognitionRef.current.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }
        
        if (finalTranscript) {
          setTranscribedText(prev => prev + finalTranscript + ' ');
        }
      };
      
      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        if (event.error !== 'no-speech') {
          toast.error(`Speech recognition error: ${event.error}`);
        }
      };
      
      recognitionRef.current.onend = () => {
        if (isRecording && settings.method === 'browser') {
          // Restart if still recording (continuous mode)
          try {
            recognitionRef.current.start();
          } catch (e) {
            // Ignore if already started
          }
        }
      };
    }
    
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [settings.language, settings.method, isRecording]);
  
  // Start recording
  const startRecording = useCallback(async () => {
    setTranscribedText('');
    setCorrectedText('');
    setCorrections([]);
    
    if (settings.method === 'whisper') {
      // OpenAI Whisper - record audio
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        streamRef.current = stream;
        
        const mediaRecorder = new MediaRecorder(stream, {
          mimeType: 'audio/webm'
        });
        mediaRecorderRef.current = mediaRecorder;
        audioChunksRef.current = [];
        
        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };
        
        mediaRecorder.start(1000); // Collect data every second
        setIsRecording(true);
        toast.info('Recording started. Click Stop when done.');
        
      } catch (err) {
        console.error('Microphone access error:', err);
        toast.error('Could not access microphone. Please check permissions.');
      }
    } else {
      // Browser Speech API - real-time
      if (recognitionRef.current) {
        try {
          recognitionRef.current.start();
          setIsRecording(true);
          toast.info('Listening... Speak now.');
        } catch (err) {
          toast.error('Speech recognition not supported in this browser.');
        }
      } else {
        toast.error('Speech recognition not available. Try using Chrome or Edge.');
      }
    }
  }, [settings.method]);
  
  // Stop recording
  const stopRecording = useCallback(async () => {
    setIsRecording(false);
    
    if (settings.method === 'whisper') {
      // Stop Whisper recording and send to server
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
        
        // Wait for final data
        await new Promise(resolve => {
          mediaRecorderRef.current.onstop = resolve;
        });
        
        // Stop all tracks
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
        }
        
        // Create audio blob
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        
        if (audioBlob.size < 1000) {
          toast.error('Recording too short. Please try again.');
          return;
        }
        
        // Send to server
        setIsProcessing(true);
        toast.info('Processing audio with AI...');
        
        try {
          const formData = new FormData();
          formData.append('audio', audioBlob, 'recording.webm');
          formData.append('context', context);
          formData.append('language', settings.language);
          
          const response = await voiceAPI.transcribe(formData);
          const data = response.data;
          
          setTranscribedText(data.text);
          setCorrectedText(data.corrected_text);
          setCorrections(data.corrections_made || []);
          setShowResultDialog(true);
          
          if (data.corrections_made?.length > 0) {
            toast.success(`Transcription complete! ${data.corrections_made.length} medical term(s) corrected.`);
          } else {
            toast.success('Transcription complete!');
          }
          
        } catch (err) {
          console.error('Transcription error:', err);
          toast.error('Failed to transcribe audio. Please try again.');
        } finally {
          setIsProcessing(false);
        }
      }
    } else {
      // Stop browser speech recognition
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      
      // Apply medical terminology corrections
      if (transcribedText && settings.autoCorrect) {
        setIsProcessing(true);
        try {
          const response = await voiceAPI.correctTerminology({
            text: transcribedText,
            context: context
          });
          setCorrectedText(response.data.corrected_text);
          setCorrections(response.data.corrections_made || []);
        } catch (err) {
          // Use original text if correction fails
          setCorrectedText(transcribedText);
        } finally {
          setIsProcessing(false);
        }
      } else {
        setCorrectedText(transcribedText);
      }
      
      if (transcribedText) {
        setShowResultDialog(true);
      }
    }
  }, [settings.method, settings.language, settings.autoCorrect, context, transcribedText]);
  
  // Apply transcription to target field
  const applyTranscription = useCallback((useOriginal = false) => {
    const textToUse = useOriginal ? transcribedText : (correctedText || transcribedText);
    
    if (onTranscriptionComplete) {
      if (appendMode && currentValue) {
        onTranscriptionComplete(currentValue + ' ' + textToUse);
      } else {
        onTranscriptionComplete(textToUse);
      }
    }
    
    setShowResultDialog(false);
    toast.success(`Text ${appendMode ? 'appended to' : 'inserted into'} ${targetField || 'field'}`);
  }, [transcribedText, correctedText, onTranscriptionComplete, appendMode, currentValue, targetField]);
  
  // Copy to clipboard
  const copyToClipboard = useCallback(async () => {
    const textToCopy = correctedText || transcribedText;
    await navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    toast.success('Copied to clipboard!');
  }, [correctedText, transcribedText]);
  
  // Check browser support
  const browserSpeechSupported = 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
  
  return (
    <>
      {/* Main Button */}
      <div className={cn("flex items-center gap-2", className)}>
        {!isRecording ? (
          <Button
            type="button"
            variant={buttonVariant}
            size={buttonSize}
            onClick={startRecording}
            disabled={disabled || isProcessing}
            className="gap-2"
            data-testid="voice-dictation-start"
          >
            {isProcessing ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Mic className="w-4 h-4" />
            )}
            {showLabel && (isProcessing ? 'Processing...' : 'Dictate')}
          </Button>
        ) : (
          <Button
            type="button"
            variant="destructive"
            size={buttonSize}
            onClick={stopRecording}
            className="gap-2 animate-pulse"
            data-testid="voice-dictation-stop"
          >
            <Square className="w-4 h-4 fill-current" />
            {showLabel && 'Stop'}
          </Button>
        )}
        
        <Button
          type="button"
          variant="ghost"
          size="icon"
          onClick={() => setShowSettingsDialog(true)}
          disabled={isRecording || isProcessing}
          className="h-8 w-8"
          title="Dictation Settings"
        >
          <Settings className="w-4 h-4" />
        </Button>
        
        {isRecording && settings.method === 'browser' && (
          <span className="text-sm text-red-500 flex items-center gap-1">
            <Volume2 className="w-4 h-4 animate-pulse" />
            Listening...
          </span>
        )}
      </div>
      
      {/* Real-time transcript for browser mode */}
      {isRecording && settings.method === 'browser' && transcribedText && (
        <div className="mt-2 p-2 bg-slate-50 rounded text-sm text-slate-700 max-h-32 overflow-y-auto">
          {transcribedText}
        </div>
      )}
      
      {/* Result Dialog */}
      <Dialog open={showResultDialog} onOpenChange={setShowResultDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Wand2 className="w-5 h-5 text-purple-600" />
              Transcription Result
            </DialogTitle>
            <DialogDescription>
              Review the transcribed text before inserting into {targetField || 'the field'}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {/* Corrections Badge */}
            {corrections.length > 0 && (
              <div className="flex items-center gap-2 flex-wrap">
                <Badge className="bg-purple-100 text-purple-700">
                  <Wand2 className="w-3 h-3 mr-1" />
                  {corrections.length} Medical Term{corrections.length > 1 ? 's' : ''} Corrected
                </Badge>
                {corrections.slice(0, 3).map((c, i) => (
                  <Badge key={i} variant="outline" className="text-xs">
                    "{c.original}" → "{c.corrected}"
                  </Badge>
                ))}
                {corrections.length > 3 && (
                  <Badge variant="outline" className="text-xs">
                    +{corrections.length - 3} more
                  </Badge>
                )}
              </div>
            )}
            
            {/* Corrected Text */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Check className="w-4 h-4 text-green-600" />
                {corrections.length > 0 ? 'Corrected Text' : 'Transcribed Text'}
              </Label>
              <Textarea
                value={correctedText || transcribedText}
                onChange={(e) => setCorrectedText(e.target.value)}
                rows={6}
                className="bg-green-50 border-green-200"
              />
            </div>
            
            {/* Original Text (if different) */}
            {corrections.length > 0 && (
              <div className="space-y-2">
                <Label className="text-slate-500 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  Original Transcription
                </Label>
                <Textarea
                  value={transcribedText}
                  readOnly
                  rows={3}
                  className="bg-slate-50 text-slate-600"
                />
              </div>
            )}
          </div>
          
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setShowResultDialog(false)}>
              Cancel
            </Button>
            <Button variant="outline" onClick={copyToClipboard}>
              {copied ? <Check className="w-4 h-4 mr-2" /> : <Copy className="w-4 h-4 mr-2" />}
              {copied ? 'Copied!' : 'Copy'}
            </Button>
            {corrections.length > 0 && (
              <Button variant="outline" onClick={() => applyTranscription(true)}>
                Use Original
              </Button>
            )}
            <Button onClick={() => applyTranscription(false)} className="bg-purple-600 hover:bg-purple-700">
              <Check className="w-4 h-4 mr-2" />
              {appendMode ? 'Append' : 'Insert'} Text
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Settings Dialog */}
      <Dialog open={showSettingsDialog} onOpenChange={setShowSettingsDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Voice Dictation Settings</DialogTitle>
            <DialogDescription>
              Configure how voice dictation works
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-6 py-4">
            {/* Method Selection */}
            <div className="space-y-3">
              <Label>Transcription Method</Label>
              <Select
                value={settings.method}
                onValueChange={(v) => setSettings({...settings, method: v})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="whisper">
                    <div className="flex flex-col">
                      <span>OpenAI Whisper (Recommended)</span>
                      <span className="text-xs text-slate-500">High accuracy, medical terms</span>
                    </div>
                  </SelectItem>
                  <SelectItem value="browser" disabled={!browserSpeechSupported}>
                    <div className="flex flex-col">
                      <span>Browser Speech API {!browserSpeechSupported && '(Not supported)'}</span>
                      <span className="text-xs text-slate-500">Real-time, free</span>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
              
              {settings.method === 'whisper' && (
                <p className="text-xs text-slate-500">
                  Records audio and sends to AI for high-accuracy transcription
                </p>
              )}
              {settings.method === 'browser' && (
                <p className="text-xs text-slate-500">
                  Uses your browser's built-in speech recognition (real-time)
                </p>
              )}
            </div>
            
            {/* Language */}
            <div className="space-y-3">
              <Label>Language</Label>
              <Select
                value={settings.language}
                onValueChange={(v) => setSettings({...settings, language: v})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="es">Spanish</SelectItem>
                  <SelectItem value="fr">French</SelectItem>
                  <SelectItem value="de">German</SelectItem>
                  <SelectItem value="pt">Portuguese</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            {/* Auto-correct */}
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <Label>Medical Terminology Correction</Label>
                <p className="text-xs text-slate-500">
                  Automatically correct common medical terms
                </p>
              </div>
              <Switch
                checked={settings.autoCorrect}
                onCheckedChange={(v) => setSettings({...settings, autoCorrect: v})}
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button onClick={() => setShowSettingsDialog(false)}>
              Done
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

/**
 * Compact version for inline use
 */
export function VoiceDictationButton({
  onTranscriptionComplete,
  context = 'general',
  disabled = false,
}) {
  return (
    <VoiceDictation
      onTranscriptionComplete={onTranscriptionComplete}
      context={context}
      showLabel={false}
      buttonVariant="ghost"
      buttonSize="icon"
      disabled={disabled}
    />
  );
}
