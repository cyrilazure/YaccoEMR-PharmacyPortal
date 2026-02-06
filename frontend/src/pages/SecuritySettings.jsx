import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/lib/auth';
import { twoFactorAPI, rbacAPI, passwordAPI } from '@/lib/api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from '@/components/ui/alert';
import { toast } from 'sonner';
import { 
  Shield, ShieldCheck, ShieldAlert, Key, Smartphone, 
  Copy, CheckCircle2, XCircle, AlertTriangle, Lock,
  QrCode, RefreshCw, Eye, EyeOff
} from 'lucide-react';

export default function SecuritySettings() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [twoFAStatus, setTwoFAStatus] = useState(null);
  const [permissions, setPermissions] = useState(null);
  
  // Roles that should NOT see permissions tab - HIDE FOR ALL USERS NOW
  const showPermissions = false; // Permissions tab disabled as per user request
  
  // 2FA Setup state
  const [setupDialogOpen, setSetupDialogOpen] = useState(false);
  const [setupData, setSetupData] = useState(null);
  const [verifyCode, setVerifyCode] = useState('');
  const [setupStep, setSetupStep] = useState(1);
  const [saving, setSaving] = useState(false);
  
  // Disable 2FA state
  const [disableDialogOpen, setDisableDialogOpen] = useState(false);
  const [disableCode, setDisableCode] = useState('');
  
  // Backup codes state
  const [showBackupCodes, setShowBackupCodes] = useState(false);
  const [regenerateDialogOpen, setRegenerateDialogOpen] = useState(false);
  const [regenerateCode, setRegenerateCode] = useState('');
  const [newBackupCodes, setNewBackupCodes] = useState(null);
  
  // Password change state
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPasswords, setShowPasswords] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [twoFARes, permRes] = await Promise.all([
        twoFactorAPI.getStatus(),
        rbacAPI.getMyPermissions()
      ]);
      
      setTwoFAStatus(twoFARes.data);
      setPermissions(permRes.data);
    } catch (err) {
      console.error('Security settings fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSetup2FA = async () => {
    setSaving(true);
    try {
      const response = await twoFactorAPI.setup();
      setSetupData(response.data);
      setSetupStep(1);
      setSetupDialogOpen(true);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to initialize 2FA setup');
    } finally {
      setSaving(false);
    }
  };

  const handleVerify2FA = async () => {
    if (verifyCode.length !== 6) {
      toast.error('Please enter a 6-digit code');
      return;
    }
    
    setSaving(true);
    try {
      await twoFactorAPI.verify(verifyCode);
      toast.success('Two-factor authentication enabled successfully!');
      setSetupDialogOpen(false);
      setSetupStep(1);
      setVerifyCode('');
      setSetupData(null);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Invalid verification code');
    } finally {
      setSaving(false);
    }
  };

  const handleDisable2FA = async () => {
    if (disableCode.length !== 6) {
      toast.error('Please enter a 6-digit code');
      return;
    }
    
    setSaving(true);
    try {
      await twoFactorAPI.disable(disableCode);
      toast.success('Two-factor authentication disabled');
      setDisableDialogOpen(false);
      setDisableCode('');
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Invalid code');
    } finally {
      setSaving(false);
    }
  };

  const handleRegenerateBackupCodes = async () => {
    if (regenerateCode.length !== 6) {
      toast.error('Please enter a 6-digit code');
      return;
    }
    
    setSaving(true);
    try {
      const response = await twoFactorAPI.regenerateBackupCodes(regenerateCode);
      setNewBackupCodes(response.data.backup_codes);
      toast.success('New backup codes generated');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Invalid code');
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = async () => {
    if (newPassword !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }
    
    if (newPassword.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }
    
    setSaving(true);
    try {
      await passwordAPI.changePassword(currentPassword, newPassword);
      toast.success('Password changed successfully');
      setPasswordDialogOpen(false);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to change password');
    } finally {
      setSaving(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <Skeleton className="h-12 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Skeleton className="h-64" />
          <Skeleton className="h-64" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="security-settings">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900" style={{ fontFamily: 'Manrope' }}>
          Security Settings
        </h1>
        <p className="text-slate-500 mt-1">
          Manage your account security, two-factor authentication, and permissions
        </p>
      </div>

      <Tabs defaultValue="2fa">
        <TabsList>
          <TabsTrigger value="2fa" className="gap-2">
            <Smartphone className="w-4 h-4" /> Two-Factor Auth
          </TabsTrigger>
          <TabsTrigger value="password" className="gap-2">
            <Lock className="w-4 h-4" /> Password
          </TabsTrigger>
          {showPermissions && (
            <TabsTrigger value="permissions" className="gap-2">
              <Shield className="w-4 h-4" /> Permissions
            </TabsTrigger>
          )}
        </TabsList>

        {/* 2FA Tab */}
        <TabsContent value="2fa" className="mt-6 space-y-6">
          {/* 2FA Status Card */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {twoFAStatus?.enabled ? (
                    <ShieldCheck className="w-8 h-8 text-emerald-500" />
                  ) : (
                    <ShieldAlert className="w-8 h-8 text-amber-500" />
                  )}
                  <div>
                    <CardTitle>Two-Factor Authentication</CardTitle>
                    <CardDescription>
                      Add an extra layer of security to your account
                    </CardDescription>
                  </div>
                </div>
                <Badge className={twoFAStatus?.enabled ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}>
                  {twoFAStatus?.enabled ? 'Enabled' : 'Disabled'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {twoFAStatus?.enabled ? (
                <>
                  <Alert className="border-emerald-200 bg-emerald-50">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                    <AlertTitle className="text-emerald-800">2FA is Active</AlertTitle>
                    <AlertDescription className="text-emerald-700">
                      Your account is protected with two-factor authentication.
                      {twoFAStatus?.last_used && (
                        <span className="block mt-1 text-sm">
                          Last used: {new Date(twoFAStatus.last_used).toLocaleString()}
                        </span>
                      )}
                    </AlertDescription>
                  </Alert>
                  
                  <div className="flex items-center justify-between p-4 rounded-lg border border-slate-200">
                    <div>
                      <p className="font-medium text-slate-900">Backup Codes</p>
                      <p className="text-sm text-slate-500">
                        {twoFAStatus?.backup_codes_remaining || 0} codes remaining
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" onClick={() => setRegenerateDialogOpen(true)}>
                        <RefreshCw className="w-4 h-4 mr-2" /> Regenerate
                      </Button>
                    </div>
                  </div>
                  
                  <Button variant="destructive" onClick={() => setDisableDialogOpen(true)}>
                    Disable 2FA
                  </Button>
                </>
              ) : (
                <>
                  <Alert className="border-amber-200 bg-amber-50">
                    <AlertTriangle className="h-4 w-4 text-amber-600" />
                    <AlertTitle className="text-amber-800">2FA Not Enabled</AlertTitle>
                    <AlertDescription className="text-amber-700">
                      Your account is not protected with two-factor authentication. 
                      Enable 2FA to add an extra layer of security.
                    </AlertDescription>
                  </Alert>
                  
                  <Button onClick={handleSetup2FA} disabled={saving} className="bg-sky-600 hover:bg-sky-700">
                    <Smartphone className="w-4 h-4 mr-2" />
                    {saving ? 'Setting up...' : 'Enable Two-Factor Authentication'}
                  </Button>
                </>
              )}
            </CardContent>
          </Card>

          {/* How 2FA Works */}
          <Card>
            <CardHeader>
              <CardTitle>How Two-Factor Authentication Works</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="w-12 h-12 rounded-full bg-sky-100 text-sky-600 flex items-center justify-center mx-auto mb-3">
                    <Smartphone className="w-6 h-6" />
                  </div>
                  <h4 className="font-medium text-slate-900">1. Install App</h4>
                  <p className="text-sm text-slate-500">
                    Download Google Authenticator, Authy, or any TOTP app
                  </p>
                </div>
                <div className="text-center">
                  <div className="w-12 h-12 rounded-full bg-sky-100 text-sky-600 flex items-center justify-center mx-auto mb-3">
                    <QrCode className="w-6 h-6" />
                  </div>
                  <h4 className="font-medium text-slate-900">2. Scan QR Code</h4>
                  <p className="text-sm text-slate-500">
                    Link your account by scanning the QR code
                  </p>
                </div>
                <div className="text-center">
                  <div className="w-12 h-12 rounded-full bg-sky-100 text-sky-600 flex items-center justify-center mx-auto mb-3">
                    <Key className="w-6 h-6" />
                  </div>
                  <h4 className="font-medium text-slate-900">3. Enter Code</h4>
                  <p className="text-sm text-slate-500">
                    Enter the 6-digit code when logging in
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Password Tab */}
        <TabsContent value="password" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lock className="w-5 h-5" /> Change Password
              </CardTitle>
              <CardDescription>
                Update your password to keep your account secure
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={() => setPasswordDialogOpen(true)} className="bg-sky-600 hover:bg-sky-700">
                <Key className="w-4 h-4 mr-2" /> Change Password
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Permissions Tab */}
        <TabsContent value="permissions" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" /> Your Permissions
              </CardTitle>
              <CardDescription>
                Role: <Badge variant="outline" className="ml-2 capitalize">{permissions?.display_name}</Badge>
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-slate-600 mb-4">{permissions?.description}</p>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50">
                  <span className="text-slate-700">Total Permissions</span>
                  <Badge>{permissions?.permission_count || 0}</Badge>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {permissions?.permissions?.slice(0, 18).map((perm) => (
                    <div key={perm} className="flex items-center gap-2 p-2 rounded bg-slate-50">
                      <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                      <span className="text-xs text-slate-600 truncate">{perm}</span>
                    </div>
                  ))}
                </div>
                
                {permissions?.permission_count > 18 && (
                  <p className="text-sm text-slate-500 text-center">
                    And {permissions.permission_count - 18} more permissions...
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* 2FA Setup Dialog */}
      <Dialog open={setupDialogOpen} onOpenChange={setSetupDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Smartphone className="w-5 h-5 text-sky-600" />
              Set Up Two-Factor Authentication
            </DialogTitle>
            <DialogDescription>
              {setupStep === 1 ? 'Scan this QR code with your authenticator app' : 
               setupStep === 2 ? 'Enter the code from your app to verify' :
               'Save your backup codes'}
            </DialogDescription>
          </DialogHeader>
          
          {setupStep === 1 && setupData && (
            <div className="space-y-4">
              {/* QR Code Display - Improved */}
              <div className="flex flex-col items-center justify-center p-6 bg-white border-2 border-gray-200 rounded-lg">
                {setupData.qr_code ? (
                  <img 
                    src={setupData.qr_code} 
                    alt="QR Code for 2FA Setup" 
                    className="w-52 h-52 rounded"
                    style={{ imageRendering: 'pixelated' }}
                  />
                ) : (
                  <div className="w-52 h-52 bg-gray-100 flex items-center justify-center rounded">
                    <QrCode className="w-16 h-16 text-gray-400" />
                  </div>
                )}
              </div>
              
              {/* App Recommendations */}
              <div className="text-center text-sm text-gray-500">
                <p className="font-medium mb-1">Recommended Apps:</p>
                <p>Google Authenticator, Microsoft Authenticator, Authy, or 1Password</p>
              </div>
              
              {/* Manual Entry Key */}
              <Alert className="bg-slate-50">
                <AlertDescription>
                  <p className="font-medium mb-2 text-slate-700">Can&apos;t scan? Enter this key manually:</p>
                  <div className="flex items-center gap-2 p-3 bg-white rounded border font-mono text-sm tracking-wider">
                    <code className="flex-1 text-center select-all">{setupData.manual_entry_key || setupData.secret}</code>
                    <Button size="sm" variant="ghost" onClick={() => copyToClipboard(setupData.secret)} title="Copy secret key">
                      <Copy className="w-4 h-4" />
                    </Button>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    Account: {setupData.account_name} | Issuer: {setupData.issuer}
                  </p>
                </AlertDescription>
              </Alert>
              
              <Button onClick={() => setSetupStep(2)} className="w-full bg-sky-600 hover:bg-sky-700">
                I&apos;ve Scanned the QR Code - Continue
              </Button>
            </div>
          )}
          
          {setupStep === 2 && (
            <div className="space-y-4">
              <Alert className="bg-blue-50 border-blue-200">
                <AlertDescription className="text-blue-700">
                  Open your authenticator app and enter the 6-digit code shown for &quot;Yacco EMR&quot;
                </AlertDescription>
              </Alert>
              
              <div className="space-y-2">
                <Label>Enter 6-digit code from your authenticator app</Label>
                <Input
                  type="text"
                  placeholder="000000"
                  value={verifyCode}
                  onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  className="text-center text-3xl tracking-[0.5em] font-mono h-16"
                  maxLength={6}
                  autoFocus
                />
              </div>
              
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setSetupStep(1)} className="flex-1">
                  Back
                </Button>
                <Button 
                  onClick={handleVerify2FA} 
                  disabled={saving || verifyCode.length !== 6} 
                  className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                >
                  {saving ? 'Verifying...' : 'Verify & Enable'}
                </Button>
              </div>
            </div>
          )}
          
          {setupStep === 3 && setupData && (
            <div className="space-y-4">
              <Alert className="border-amber-200 bg-amber-50">
                <AlertTriangle className="h-4 w-4 text-amber-600" />
                <AlertTitle className="text-amber-800">Save Your Backup Codes</AlertTitle>
                <AlertDescription className="text-amber-700">
                  Store these codes in a safe place. You can use them to access your account if you lose your phone.
                  Each code can only be used once.
                </AlertDescription>
              </Alert>
              
              <div className="grid grid-cols-2 gap-2 p-4 bg-slate-50 rounded-lg font-mono text-sm">
                {setupData.backup_codes.map((code, i) => (
                  <div key={i} className="p-2 bg-white rounded border text-center select-all">{code}</div>
                ))}
              </div>
              
              <Button 
                onClick={() => copyToClipboard(setupData.backup_codes.join('\n'))} 
                variant="outline"
                className="w-full"
              >
                <Copy className="w-4 h-4 mr-2" /> Copy All Codes
              </Button>
              
              <Button onClick={() => { setSetupDialogOpen(false); fetchData(); }} className="w-full bg-emerald-600 hover:bg-emerald-700">
                <CheckCircle2 className="w-4 h-4 mr-2" /> Done - I&apos;ve Saved My Codes
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Disable 2FA Dialog */}
      <Dialog open={disableDialogOpen} onOpenChange={setDisableDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Disable Two-Factor Authentication</DialogTitle>
            <DialogDescription>
              Enter your authenticator code to disable 2FA. This will make your account less secure.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Enter 6-digit code</Label>
              <Input
                type="text"
                placeholder="000000"
                value={disableCode}
                onChange={(e) => setDisableCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                className="text-center text-2xl tracking-widest font-mono"
                maxLength={6}
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setDisableDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              onClick={handleDisable2FA} 
              disabled={saving || disableCode.length !== 6}
            >
              {saving ? 'Disabling...' : 'Disable 2FA'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Regenerate Backup Codes Dialog */}
      <Dialog open={regenerateDialogOpen} onOpenChange={(open) => {
        setRegenerateDialogOpen(open);
        if (!open) {
          setRegenerateCode('');
          setNewBackupCodes(null);
        }
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Regenerate Backup Codes</DialogTitle>
            <DialogDescription>
              {newBackupCodes ? 'Your new backup codes have been generated' : 'Enter your authenticator code to generate new backup codes. Old codes will be invalidated.'}
            </DialogDescription>
          </DialogHeader>
          
          {!newBackupCodes ? (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Enter 6-digit code</Label>
                <Input
                  type="text"
                  placeholder="000000"
                  value={regenerateCode}
                  onChange={(e) => setRegenerateCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  className="text-center text-2xl tracking-widest font-mono"
                  maxLength={6}
                />
              </div>
              
              <DialogFooter>
                <Button variant="outline" onClick={() => setRegenerateDialogOpen(false)}>
                  Cancel
                </Button>
                <Button 
                  onClick={handleRegenerateBackupCodes} 
                  disabled={saving || regenerateCode.length !== 6}
                >
                  {saving ? 'Generating...' : 'Generate New Codes'}
                </Button>
              </DialogFooter>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-2 p-4 bg-slate-50 rounded-lg font-mono text-sm">
                {newBackupCodes.map((code, i) => (
                  <div key={i} className="p-2 bg-white rounded border">{code}</div>
                ))}
              </div>
              
              <Button 
                onClick={() => copyToClipboard(newBackupCodes.join('\n'))} 
                variant="outline"
                className="w-full"
              >
                <Copy className="w-4 h-4 mr-2" /> Copy All Codes
              </Button>
              
              <Button onClick={() => {
                setRegenerateDialogOpen(false);
                fetchData();
              }} className="w-full">
                Done
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Change Password Dialog */}
      <Dialog open={passwordDialogOpen} onOpenChange={setPasswordDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Change Password</DialogTitle>
            <DialogDescription>
              Enter your current password and choose a new one
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Current Password</Label>
              <div className="relative">
                <Input
                  type={showPasswords ? 'text' : 'password'}
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3"
                  onClick={() => setShowPasswords(!showPasswords)}
                >
                  {showPasswords ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </Button>
              </div>
            </div>
            
            <div className="space-y-2">
              <Label>New Password</Label>
              <Input
                type={showPasswords ? 'text' : 'password'}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
            </div>
            
            <div className="space-y-2">
              <Label>Confirm New Password</Label>
              <Input
                type={showPasswords ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </div>
            
            {newPassword && confirmPassword && newPassword !== confirmPassword && (
              <Alert variant="destructive">
                <XCircle className="h-4 w-4" />
                <AlertDescription>Passwords do not match</AlertDescription>
              </Alert>
            )}
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setPasswordDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleChangePassword} 
              disabled={saving || !currentPassword || !newPassword || newPassword !== confirmPassword}
            >
              {saving ? 'Changing...' : 'Change Password'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
