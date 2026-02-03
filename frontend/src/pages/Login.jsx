import { useState } from 'react';
import { useNavigate, Navigate, Link } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { toast } from 'sonner';
import { Activity, Shield, Users, Calendar, Building2, LogIn, Smartphone } from 'lucide-react';

const getRoleRedirect = (role) => {
  switch (role) {
    case 'super_admin': return '/platform-admin';
    case 'hospital_admin': return '/hospital-settings';
    case 'physician': return '/dashboard';
    case 'nurse': return '/nurse-station';
    case 'scheduler': return '/scheduling';
    case 'admin': return '/admin';
    default: return '/dashboard';
  }
};

export default function LoginPage() {
  const { user, login, requires2FA, complete2FALogin, cancel2FA } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [totpCode, setTotpCode] = useState('');

  if (user) {
    return <Navigate to={getRoleRedirect(user.role)} replace />;
  }

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const userData = await login(loginForm.email, loginForm.password);
      toast.success('Welcome back!');
      navigate(getRoleRedirect(userData.role));
    } catch (err) {
      if (err.message === '2FA_REQUIRED') {
        // 2FA dialog will be shown
        toast.info('Please enter your 2FA code');
      } else {
        toast.error(err.response?.data?.detail || 'Login failed');
      }
    } finally {
      setLoading(false);
    }
  };

  const handle2FASubmit = async (e) => {
    e.preventDefault();
    if (totpCode.length !== 6 && !totpCode.includes('-')) {
      toast.error('Please enter a valid code');
      return;
    }
    
    setLoading(true);
    try {
      const userData = await complete2FALogin(totpCode);
      toast.success('Welcome back!');
      navigate(getRoleRedirect(userData.role));
    } catch (err) {
      toast.error(err.message || 'Invalid 2FA code');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel2FA = () => {
    cancel2FA();
    setTotpCode('');
  };

  return (
    <div className="min-h-screen flex" data-testid="login-page">
      {/* Left side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
        <div 
          className="absolute inset-0 bg-cover bg-center"
          style={{ 
            backgroundImage: 'url(https://images.unsplash.com/photo-1717497932377-7758b8d5b45e?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzZ8MHwxfHNlYXJjaHwxfHxtb2Rlcm4lMjBob3NwaXRhbCUyMGFyY2hpdGVjdHVyZSUyMGJyaWdodHxlbnwwfHx8fDE3NzAwNzY5Njh8MA&ixlib=rb-4.1.0&q=85)'
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900/90 via-slate-800/85 to-sky-900/80" />
        <div className="relative z-10 flex flex-col justify-between p-12 text-white">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-12 h-12 rounded-xl bg-sky-500 flex items-center justify-center">
                <Activity className="w-7 h-7" />
              </div>
              <span className="text-3xl font-bold tracking-tight" style={{ fontFamily: 'Manrope' }}>
                Yacco EMR
              </span>
            </div>
            <p className="text-slate-300 text-lg mt-1">Electronic Medical Records</p>
          </div>
          
          <div className="space-y-8">
            <h2 className="text-4xl font-bold leading-tight" style={{ fontFamily: 'Manrope' }}>
              Comprehensive Clinical Care, Simplified.
            </h2>
            <div className="grid grid-cols-2 gap-6">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0">
                  <Shield className="w-5 h-5" />
                </div>
                <div>
                  <p className="font-semibold">HIPAA Compliant</p>
                  <p className="text-sm text-slate-400">Secure patient data</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0">
                  <Users className="w-5 h-5" />
                </div>
                <div>
                  <p className="font-semibold">Multi-Role Support</p>
                  <p className="text-sm text-slate-400">Full care team access</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0">
                  <Calendar className="w-5 h-5" />
                </div>
                <div>
                  <p className="font-semibold">Smart Scheduling</p>
                  <p className="text-sm text-slate-400">Efficient workflows</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0">
                  <Activity className="w-5 h-5" />
                </div>
                <div>
                  <p className="font-semibold">AI-Assisted Docs</p>
                  <p className="text-sm text-slate-400">GPT-5.2 powered</p>
                </div>
              </div>
            </div>
          </div>
          
          <p className="text-slate-400 text-sm">
            © {new Date().getFullYear()} Yacco Healthcare Systems. All rights reserved.
          </p>
        </div>
      </div>
      
      {/* Right side - Login Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-slate-50">
        <div className="w-full max-w-md">
          {/* Mobile Header */}
          <div className="lg:hidden mb-8 text-center">
            <div className="flex items-center justify-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-xl bg-sky-500 flex items-center justify-center">
                <Activity className="w-5 h-5 text-white" />
              </div>
              <span className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Manrope' }}>
                Yacco EMR
              </span>
            </div>
          </div>
          
          {/* Sign In Card */}
          <Card className="border-slate-200 shadow-lg">
            <CardHeader className="text-center pb-2">
              <CardTitle className="text-2xl" style={{ fontFamily: 'Manrope' }}>Welcome Back</CardTitle>
              <CardDescription>Sign in to access your hospital's EMR system</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleLogin} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="login-email">Email</Label>
                  <Input 
                    id="login-email"
                    data-testid="login-email-input"
                    type="email"
                    placeholder="you@hospital.com"
                    value={loginForm.email}
                    onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="login-password">Password</Label>
                  <Input 
                    id="login-password"
                    data-testid="login-password-input"
                    type="password"
                    placeholder="••••••••"
                    value={loginForm.password}
                    onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                    required
                  />
                </div>
                <div className="flex justify-end">
                  <Link to="/forgot-password" className="text-sm text-sky-600 hover:text-sky-700">
                    Forgot password?
                  </Link>
                </div>
                <Button 
                  type="submit" 
                  className="w-full bg-slate-900 hover:bg-slate-800 gap-2"
                  disabled={loading}
                  data-testid="login-submit-btn"
                >
                  {loading ? (
                    'Signing in...'
                  ) : (
                    <>
                      <LogIn className="w-4 h-4" />
                      Sign In
                    </>
                  )}
                </Button>
              </form>
              
              {/* Hospital Registration Link */}
              <div className="mt-8 pt-6 border-t text-center">
                <p className="text-sm text-slate-500 mb-4">
                  New to Yacco EMR? Register your healthcare organization to get started.
                </p>
                <Link to="/register-hospital">
                  <Button variant="outline" className="w-full gap-2 border-sky-200 text-sky-700 hover:bg-sky-50 hover:text-sky-800">
                    <Building2 className="w-4 h-4" />
                    Register Your Hospital
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
          
          {/* Help text */}
          <p className="text-center text-sm text-slate-500 mt-6">
            Staff accounts are created by your Hospital Administrator.
            <br />
            Contact your admin if you need access.
          </p>
        </div>
      </div>
    </div>
  );
}
