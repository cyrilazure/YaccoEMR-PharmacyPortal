import React, { useState } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Dialog, DialogContent, DialogDescription, 
  DialogHeader, DialogTitle 
} from '@/components/ui/dialog';
import { toast } from 'sonner';
import { 
  Shield, 
  Lock, 
  Mail, 
  Eye, 
  EyeOff, 
  Loader2,
  AlertCircle,
  Activity,
  Smartphone,
  Send
} from 'lucide-react';

export default function POLogin() {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // OTP States
  const [loginStep, setLoginStep] = useState('credentials'); // 'credentials', 'phone', 'otp'
  const [pendingUserId, setPendingUserId] = useState('');
  const [otpSessionId, setOtpSessionId] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [phoneMasked, setPhoneMasked] = useState('');
  const [resending, setResending] = useState(false);

  // If already logged in as super_admin, redirect to portal
  if (user?.role === 'super_admin') {
    return <Navigate to="/platform-admin" replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      // Step 1: Initialize login with OTP flow
      const response = await api.post('/auth/login/init', { email, password });
      
      if (response.data.phone_required) {
        // Phone number is needed
        setPendingUserId(response.data.user_id);
        setLoginStep('phone');
        toast.info('Please enter your phone number for verification');
      } else if (response.data.otp_required) {
        // OTP sent to existing phone
        setOtpSessionId(response.data.otp_session_id);
        setPhoneMasked(response.data.phone_masked);
        setLoginStep('otp');
        toast.success('OTP sent to your phone');
      }
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  const handlePhoneSubmit = async (e) => {
    e.preventDefault();
    if (phoneNumber.length < 9) {
      setError('Please enter a valid phone number');
      return;
    }
    
    setLoading(true);
    setError('');
    try {
      const response = await api.post('/auth/login/submit-phone', { 
        user_id: pendingUserId, 
        phone_number: phoneNumber 
      });
      setOtpSessionId(response.data.otp_session_id);
      setPhoneMasked(response.data.phone_masked);
      setLoginStep('otp');
      toast.success('OTP sent to your phone');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleOTPVerify = async (e) => {
    e.preventDefault();
    if (otpCode.length !== 6) {
      setError('Please enter a valid 6-digit OTP');
      return;
    }
    
    setLoading(true);
    setError('');
    try {
      const response = await api.post('/auth/login/verify', null, { 
        params: { otp_session_id: otpSessionId, otp_code: otpCode }
      });
      
      const { token, user: userData } = response.data;
      
      // Check if user is super_admin
      if (userData.role !== 'super_admin') {
        setError('Access denied. This portal is only for Platform Owners.');
        setLoginStep('credentials');
        return;
      }
      
      // Store auth data
      localStorage.setItem('yacco_token', token);
      localStorage.setItem('yacco_user', JSON.stringify(userData));
      
      toast.success('Welcome to Platform Owner Portal!');
      window.location.href = '/platform-admin';
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleResendOTP = async () => {
    setResending(true);
    try {
      await api.post('/auth/login/resend-otp', null, { 
        params: { otp_session_id: otpSessionId }
      });
      toast.success('OTP resent successfully');
    } catch (err) {
      toast.error('Failed to resend OTP');
    } finally {
      setResending(false);
    }
  };

  const handleBack = () => {
    setLoginStep('credentials');
    setOtpCode('');
    setPhoneNumber('');
    setError('');
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="absolute inset-0">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(16,185,129,0.15),transparent_50%)]" />
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_80%,rgba(59,130,246,0.1),transparent_50%)]" />
        </div>
        
        <div className="relative z-10 flex flex-col justify-between p-12 text-white">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-lg">
                <Activity className="w-8 h-8" />
              </div>
              <div>
                <span className="text-3xl font-bold tracking-tight">Yacco EMR</span>
                <p className="text-slate-400 text-sm">Platform Owner Portal</p>
              </div>
            </div>
          </div>
          
          <div className="space-y-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Shield className="w-8 h-8 text-emerald-400" />
                <h1 className="text-3xl font-bold">Platform Administration</h1>
              </div>
              <p className="text-slate-300 text-lg max-w-md leading-relaxed">
                Secure access to manage the Ghana Healthcare Network. Create hospitals, 
                manage users, and oversee all platform operations.
              </p>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                <div className="text-3xl font-bold text-emerald-400 mb-1">16</div>
                <div className="text-sm text-slate-400">Ghana Regions</div>
              </div>
              <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                <div className="text-3xl font-bold text-blue-400 mb-1">Full</div>
                <div className="text-sm text-slate-400">Platform Control</div>
              </div>
            </div>
            
            <div className="space-y-3">
              <div className="flex items-center gap-3 text-slate-300">
                <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center">
                  <Shield className="w-4 h-4 text-emerald-400" />
                </div>
                <span>Create & manage hospitals across all regions</span>
              </div>
              <div className="flex items-center gap-3 text-slate-300">
                <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center">
                  <Lock className="w-4 h-4 text-blue-400" />
                </div>
                <span>Login as any hospital for support access</span>
              </div>
              <div className="flex items-center gap-3 text-slate-300">
                <div className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center">
                  <Activity className="w-4 h-4 text-purple-400" />
                </div>
                <span>Monitor platform health & analytics</span>
              </div>
            </div>
          </div>
          
          <div className="text-sm text-slate-500">
            <p>© 2025 Yacco EMR Ghana. Platform Owner Access Only.</p>
          </div>
        </div>
      </div>

      {/* Right Side - Login Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-slate-50">
        <div className="w-full max-w-md">
          {/* Mobile Header */}
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
              <Activity className="w-7 h-7 text-white" />
            </div>
            <div>
              <span className="text-2xl font-bold">Yacco EMR</span>
              <p className="text-slate-500 text-sm">Platform Owner Portal</p>
            </div>
          </div>

          <Card className="border-0 shadow-2xl">
            <CardHeader className="space-y-1 pb-6">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-10 h-10 rounded-lg bg-slate-900 flex items-center justify-center">
                  <Shield className="w-5 h-5 text-emerald-400" />
                </div>
              </div>
              <CardTitle className="text-2xl">Platform Owner Login</CardTitle>
              <CardDescription>
                Enter your Super Admin credentials to access the platform
              </CardDescription>
            </CardHeader>
            
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                {error && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}
                
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="admin@yacco.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="pl-10"
                      required
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="pl-10 pr-10"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                
                <Button 
                  type="submit" 
                  className="w-full bg-slate-900 hover:bg-slate-800 h-11"
                  disabled={loading}
                >
                  {loading ? (
                    <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Authenticating...</>
                  ) : (
                    <><Shield className="w-4 h-4 mr-2" /> Access Platform</>
                  )}
                </Button>
              </form>
            </CardContent>
            
            <CardFooter className="flex flex-col gap-4 pt-0">
              <div className="w-full h-px bg-slate-200" />
              <p className="text-center text-sm text-slate-500">
                This portal is restricted to Platform Owners only.
                <br />
                Hospital staff should use the{' '}
                <a href="/login" className="text-emerald-600 hover:underline">
                  regular login
                </a>.
              </p>
            </CardFooter>
          </Card>
        </div>
      </div>
    </div>
  );
}
