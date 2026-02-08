import { useState } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { Globe, Shield, Lock, Eye, EyeOff, LogOut, Loader2, Smartphone, Send } from 'lucide-react';

export default function SuperAdminLogin() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [credentials, setCredentials] = useState({
    email: '',
    password: ''
  });
  
  // OTP States
  const [loginStep, setLoginStep] = useState('credentials'); // 'credentials', 'phone', 'otp'
  const [pendingUserId, setPendingUserId] = useState('');
  const [otpSessionId, setOtpSessionId] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [phoneMasked, setPhoneMasked] = useState('');
  const [resending, setResending] = useState(false);

  // If already logged in as super_admin, redirect to dashboard
  if (user?.role === 'super_admin') {
    return <Navigate to="/platform/super-admin" replace />;
  }

  // If logged in as other role, show access denied with logout option
  if (user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
        <Card className="w-full max-w-md text-center border-slate-700 bg-slate-800/50">
          <CardContent className="pt-8 pb-6">
            <Shield className="w-16 h-16 mx-auto mb-4 text-red-500" />
            <h2 className="text-xl font-bold mb-2 text-white">Access Denied</h2>
            <p className="text-slate-400 mb-6">This portal is restricted to Platform Owners only.</p>
            <p className="text-slate-500 text-sm mb-4">
              You are currently logged in as: <span className="text-slate-300">{user.email}</span>
            </p>
            <Button 
              variant="outline" 
              className="border-slate-600 text-slate-300 hover:bg-slate-700"
              onClick={() => {
                logout();
                toast.success('Logged out successfully');
              }}
            >
              <LogOut className="w-4 h-4 mr-2" />
              Logout & Login as Platform Owner
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // Use the direct API instead of useAuth to handle OTP flow
      const response = await api.post('/auth/login/init', { 
        email: credentials.email, 
        password: credentials.password 
      });
      
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
      toast.error(err.response?.data?.detail || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  const handlePhoneSubmit = async (e) => {
    e.preventDefault();
    if (phoneNumber.length < 9) {
      toast.error('Please enter a valid phone number');
      return;
    }
    
    setLoading(true);
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
      toast.error(err.response?.data?.detail || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleOTPVerify = async (e) => {
    e.preventDefault();
    if (otpCode.length !== 6) {
      toast.error('Please enter a valid 6-digit OTP');
      return;
    }
    
    setLoading(true);
    try {
      const response = await api.post('/auth/login/verify', null, { 
        params: { otp_session_id: otpSessionId, otp_code: otpCode }
      });
      
      const { token, user: userData } = response.data;
      
      // Check if user is super_admin
      if (userData.role !== 'super_admin') {
        toast.error('Access denied. This portal is for Platform Owners only.');
        setLoginStep('credentials');
        return;
      }
      
      // Store auth data
      localStorage.setItem('yacco_token', token);
      localStorage.setItem('yacco_user', JSON.stringify(userData));
      
      toast.success('Welcome back, Platform Owner!');
      window.location.href = '/platform/super-admin';
      
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Invalid OTP');
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
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
      {/* Background Pattern */}
      <div className="absolute inset-0 bg-grid-slate-700/25 opacity-50"></div>
      
      <div className="relative z-10 w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <Globe className="w-8 h-8 text-white" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-white mb-2" style={{ fontFamily: 'Manrope' }}>
            Yacco EMR
          </h1>
          <p className="text-slate-400">Platform Owner Portal</p>
        </div>

        {/* Login Card */}
        <Card className="border-slate-700 bg-slate-800/50 backdrop-blur-sm">
          <CardHeader className="text-center pb-2">
            <div className="mx-auto w-12 h-12 rounded-full bg-indigo-500/10 flex items-center justify-center mb-3">
              {loginStep === 'credentials' && <Shield className="w-6 h-6 text-indigo-400" />}
              {loginStep === 'phone' && <Smartphone className="w-6 h-6 text-indigo-400" />}
              {loginStep === 'otp' && <Lock className="w-6 h-6 text-indigo-400" />}
            </div>
            <CardTitle className="text-white">
              {loginStep === 'credentials' && 'Owner Access'}
              {loginStep === 'phone' && 'Phone Verification'}
              {loginStep === 'otp' && 'Enter OTP Code'}
            </CardTitle>
            <CardDescription className="text-slate-400">
              {loginStep === 'credentials' && 'Secure login for platform administration'}
              {loginStep === 'phone' && 'Enter your phone number to receive OTP'}
              {loginStep === 'otp' && `Enter the 6-digit code sent to ${phoneMasked}`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {/* Step 1: Credentials */}
            {loginStep === 'credentials' && (
              <form onSubmit={handleLogin} className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-slate-300">Email Address</Label>
                  <Input
                    type="email"
                    placeholder="Enter your email"
                    value={credentials.email}
                    onChange={(e) => setCredentials({ ...credentials, email: e.target.value })}
                    required
                    className="bg-slate-700/50 border-slate-600 text-white placeholder:text-slate-500 focus:border-indigo-500"
                    data-testid="admin-email"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label className="text-slate-300">Password</Label>
                  <div className="relative">
                    <Input
                      type={showPassword ? "text" : "password"}
                      placeholder="••••••••"
                      value={credentials.password}
                      onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
                      required
                      className="bg-slate-700/50 border-slate-600 text-white placeholder:text-slate-500 focus:border-indigo-500 pr-10"
                      data-testid="admin-password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-slate-300"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <Button
                  type="submit"
                  className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white"
                  disabled={loading}
                  data-testid="admin-login-btn"
                >
                  {loading ? (
                    <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Authenticating...</>
                  ) : (
                    <><Lock className="w-4 h-4 mr-2" /> Continue</>
                  )}
                </Button>
              </form>
            )}

            {/* Step 2: Phone Input */}
            {loginStep === 'phone' && (
              <form onSubmit={handlePhoneSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-slate-300">Phone Number</Label>
                  <Input
                    type="tel"
                    placeholder="0241234567"
                    value={phoneNumber}
                    onChange={(e) => setPhoneNumber(e.target.value.replace(/[^\d+]/g, ''))}
                    className="bg-slate-700/50 border-slate-600 text-white placeholder:text-slate-500 focus:border-indigo-500 text-center text-lg"
                    autoFocus
                  />
                  <p className="text-xs text-slate-500 text-center">
                    Enter your Ghana phone number (e.g., 0241234567)
                  </p>
                </div>

                <Button
                  type="submit"
                  className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white"
                  disabled={loading || phoneNumber.length < 9}
                >
                  {loading ? (
                    <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Sending...</>
                  ) : (
                    <><Send className="w-4 h-4 mr-2" /> Send OTP</>
                  )}
                </Button>

                <Button
                  type="button"
                  variant="ghost"
                  className="w-full text-slate-400 hover:text-white hover:bg-slate-700"
                  onClick={handleBack}
                >
                  ← Back to Login
                </Button>
              </form>
            )}

            {/* Step 3: OTP Verification */}
            {loginStep === 'otp' && (
              <form onSubmit={handleOTPVerify} className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-slate-300">OTP Code</Label>
                  <Input
                    type="text"
                    placeholder="000000"
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    className="bg-slate-700/50 border-slate-600 text-white text-center text-2xl tracking-widest font-mono focus:border-indigo-500"
                    maxLength={6}
                    autoFocus
                  />
                  <p className="text-xs text-slate-500 text-center">
                    Code sent to {phoneMasked}
                  </p>
                </div>

                <Button
                  type="submit"
                  className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white"
                  disabled={loading || otpCode.length !== 6}
                >
                  {loading ? (
                    <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Verifying...</>
                  ) : (
                    <><Shield className="w-4 h-4 mr-2" /> Verify & Access Platform</>
                  )}
                </Button>

                <div className="flex items-center justify-between">
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="text-slate-400 hover:text-white"
                    onClick={handleBack}
                  >
                    ← Back
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="text-slate-400 hover:text-white"
                    onClick={handleResendOTP}
                    disabled={resending}
                  >
                    {resending ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : null}
                    Resend OTP
                  </Button>
                </div>
              </form>
            )}

            {/* Security Notice */}
            <div className="mt-6 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
              <p className="text-xs text-amber-400 text-center">
                🔒 Restricted access. All login attempts are logged and monitored.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Footer - No links to other portals */}
        <p className="text-center text-slate-600 text-xs mt-8">
          © {new Date().getFullYear()} Yacco Healthcare Systems
        </p>
      </div>
    </div>
  );
}
