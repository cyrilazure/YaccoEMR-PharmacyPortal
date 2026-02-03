import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { Activity, ArrowLeft, Mail, CheckCircle } from 'lucide-react';
import { passwordAPI } from '@/lib/api';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [resetToken, setResetToken] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await passwordAPI.requestReset(email);
      setSent(true);
      // In demo mode, the token is returned (would be sent via email in production)
      if (response.data.reset_token) {
        setResetToken(response.data.reset_token);
      }
      toast.success('Password reset instructions sent!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to send reset email');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-2">
            <div className="w-12 h-12 rounded-xl bg-sky-500 flex items-center justify-center">
              <Activity className="w-7 h-7 text-white" />
            </div>
            <span className="text-3xl font-bold text-slate-900" style={{ fontFamily: 'Manrope' }}>
              Yacco EMR
            </span>
          </div>
        </div>

        <Card className="border-slate-200 shadow-lg">
          <CardHeader className="text-center pb-2">
            <CardTitle className="text-2xl" style={{ fontFamily: 'Manrope' }}>
              {sent ? 'Check Your Email' : 'Forgot Password'}
            </CardTitle>
            <CardDescription>
              {sent 
                ? 'We\'ve sent password reset instructions to your email'
                : 'Enter your email to receive a password reset link'
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!sent ? (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email">Email Address</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input 
                      id="email"
                      type="email"
                      placeholder="you@hospital.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="pl-10"
                      required
                    />
                  </div>
                </div>
                <Button 
                  type="submit" 
                  className="w-full bg-sky-600 hover:bg-sky-700"
                  disabled={loading}
                >
                  {loading ? 'Sending...' : 'Send Reset Link'}
                </Button>
              </form>
            ) : (
              <div className="space-y-6">
                <div className="flex justify-center">
                  <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center">
                    <CheckCircle className="w-8 h-8 text-green-600" />
                  </div>
                </div>
                
                <p className="text-center text-slate-600">
                  If an account exists for <strong>{email}</strong>, you will receive an email with instructions to reset your password.
                </p>

                {/* Demo Mode - Show token */}
                {resetToken && (
                  <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                    <p className="text-sm text-amber-800 font-medium mb-2">
                      Demo Mode - Reset Token:
                    </p>
                    <code className="text-xs bg-amber-100 p-2 rounded block break-all">
                      {resetToken}
                    </code>
                    <p className="text-xs text-amber-600 mt-2">
                      In production, this would be sent via email.
                    </p>
                    <Link to={`/reset-password?token=${resetToken}`}>
                      <Button className="w-full mt-3 bg-amber-600 hover:bg-amber-700" size="sm">
                        Go to Reset Password Page
                      </Button>
                    </Link>
                  </div>
                )}

                <Button 
                  variant="outline"
                  className="w-full"
                  onClick={() => {
                    setSent(false);
                    setResetToken('');
                  }}
                >
                  Try a different email
                </Button>
              </div>
            )}
            
            <div className="mt-6 text-center">
              <Link 
                to="/login" 
                className="text-sm text-sky-600 hover:text-sky-700 inline-flex items-center gap-1"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Sign In
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
