import { useState } from 'react';
import { useNavigate, Navigate, Link } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { Activity, Shield, Users, Calendar, Building2 } from 'lucide-react';

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
  const { user, login, register } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [registerForm, setRegisterForm] = useState({
    email: '', password: '', first_name: '', last_name: '',
    role: 'physician', department: '', specialty: ''
  });

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
      toast.error(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const userData = await register(registerForm);
      toast.success('Account created successfully!');
      navigate(getRoleRedirect(userData.role));
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
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
            © 2024 Yacco Healthcare Systems. All rights reserved.
          </p>
        </div>
      </div>
      
      {/* Right side - Auth Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-slate-50">
        <div className="w-full max-w-md">
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
          
          <Card className="border-slate-200 shadow-lg">
            <CardHeader className="text-center pb-2">
              <CardTitle className="text-2xl" style={{ fontFamily: 'Manrope' }}>Welcome</CardTitle>
              <CardDescription>Sign in to your account or create a new one</CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="login" className="w-full">
                <TabsList className="grid w-full grid-cols-2 mb-6">
                  <TabsTrigger value="login" data-testid="login-tab">Sign In</TabsTrigger>
                  <TabsTrigger value="register" data-testid="register-tab">Register</TabsTrigger>
                </TabsList>
                
                <TabsContent value="login">
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
                    <Button 
                      type="submit" 
                      className="w-full bg-slate-900 hover:bg-slate-800"
                      disabled={loading}
                      data-testid="login-submit-btn"
                    >
                      {loading ? 'Signing in...' : 'Sign In'}
                    </Button>
                  </form>
                </TabsContent>
                
                <TabsContent value="register">
                  <form onSubmit={handleRegister} className="space-y-4">
                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-2">
                        <Label htmlFor="first_name">First Name</Label>
                        <Input 
                          id="first_name"
                          data-testid="register-firstname-input"
                          placeholder="John"
                          value={registerForm.first_name}
                          onChange={(e) => setRegisterForm({ ...registerForm, first_name: e.target.value })}
                          required
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="last_name">Last Name</Label>
                        <Input 
                          id="last_name"
                          data-testid="register-lastname-input"
                          placeholder="Smith"
                          value={registerForm.last_name}
                          onChange={(e) => setRegisterForm({ ...registerForm, last_name: e.target.value })}
                          required
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="reg-email">Email</Label>
                      <Input 
                        id="reg-email"
                        data-testid="register-email-input"
                        type="email"
                        placeholder="you@hospital.com"
                        value={registerForm.email}
                        onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="reg-password">Password</Label>
                      <Input 
                        id="reg-password"
                        data-testid="register-password-input"
                        type="password"
                        placeholder="••••••••"
                        value={registerForm.password}
                        onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="role">Role</Label>
                      <Select 
                        value={registerForm.role} 
                        onValueChange={(value) => setRegisterForm({ ...registerForm, role: value })}
                      >
                        <SelectTrigger data-testid="register-role-select">
                          <SelectValue placeholder="Select role" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="physician">Physician</SelectItem>
                          <SelectItem value="nurse">Nurse</SelectItem>
                          <SelectItem value="scheduler">Scheduler</SelectItem>
                          <SelectItem value="admin">Administrator</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="space-y-2">
                        <Label htmlFor="department">Department</Label>
                        <Input 
                          id="department"
                          data-testid="register-department-input"
                          placeholder="Internal Medicine"
                          value={registerForm.department}
                          onChange={(e) => setRegisterForm({ ...registerForm, department: e.target.value })}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="specialty">Specialty</Label>
                        <Input 
                          id="specialty"
                          data-testid="register-specialty-input"
                          placeholder="Cardiology"
                          value={registerForm.specialty}
                          onChange={(e) => setRegisterForm({ ...registerForm, specialty: e.target.value })}
                        />
                      </div>
                    </div>
                    <Button 
                      type="submit" 
                      className="w-full bg-slate-900 hover:bg-slate-800"
                      disabled={loading}
                      data-testid="register-submit-btn"
                    >
                      {loading ? 'Creating account...' : 'Create Account'}
                    </Button>
                  </form>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
