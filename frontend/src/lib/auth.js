import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from './api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [requires2FA, setRequires2FA] = useState(false);
  const [pendingCredentials, setPendingCredentials] = useState(null);
  
  // OTP States
  const [requiresOTP, setRequiresOTP] = useState(false);
  const [requiresPhone, setRequiresPhone] = useState(false);
  const [pendingUserId, setPendingUserId] = useState(null);
  const [otpSessionId, setOtpSessionId] = useState(null);
  const [otpPhoneMasked, setOtpPhoneMasked] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('yacco_token');
    const storedUser = localStorage.getItem('yacco_user');
    
    if (token && storedUser) {
      setUser(JSON.parse(storedUser));
      // Verify token is still valid
      authAPI.getMe()
        .then((res) => {
          setUser(res.data);
          localStorage.setItem('yacco_user', JSON.stringify(res.data));
        })
        .catch(() => {
          logout();
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email, password, totpCode = null) => {
    try {
      // Use new OTP flow
      const response = await authAPI.loginInit(email, password);
      
      if (response.data.phone_required) {
        // Phone number is required - show phone input
        setRequiresPhone(true);
        setPendingUserId(response.data.user_id);
        setPendingCredentials({ email, password });
        throw new Error('PHONE_REQUIRED');
      } else if (response.data.otp_required) {
        // OTP is required, show OTP input
        setRequiresOTP(true);
        setOtpSessionId(response.data.otp_session_id);
        setOtpPhoneMasked(response.data.phone_masked);
        setPendingCredentials({ email, password });
        throw new Error('OTP_REQUIRED');
      } else {
        // No OTP required (shouldn't happen with new flow)
        const { token, user: userData } = response.data;
        localStorage.setItem('yacco_token', token);
        localStorage.setItem('yacco_user', JSON.stringify(userData));
        setUser(userData);
        resetOTPState();
        return userData;
      }
    } catch (error) {
      if (error.message === 'OTP_REQUIRED' || error.message === 'PHONE_REQUIRED') {
        throw error;
      }
      // Check if 2FA is required (legacy TOTP)
      if (error.response?.status === 403 && error.response?.data?.detail === '2FA_REQUIRED') {
        setRequires2FA(true);
        setPendingCredentials({ email, password });
        throw new Error('2FA_REQUIRED');
      }
      throw error;
    }
  };

  const submitPhoneNumber = async (phoneNumber) => {
    if (!pendingUserId) {
      throw new Error('No pending login');
    }
    
    const response = await authAPI.loginSubmitPhone(pendingUserId, phoneNumber);
    
    // Phone submitted, now show OTP step
    setRequiresPhone(false);
    setRequiresOTP(true);
    setOtpSessionId(response.data.otp_session_id);
    setOtpPhoneMasked(response.data.phone_masked);
    
    return response.data;
  };

  const completeOTPLogin = async (otpCode) => {
    if (!otpSessionId) {
      throw new Error('No pending OTP session');
    }
    
    const response = await authAPI.loginVerify(otpSessionId, otpCode);
    const { token, user: userData } = response.data;
    
    localStorage.setItem('yacco_token', token);
    localStorage.setItem('yacco_user', JSON.stringify(userData));
    setUser(userData);
    resetOTPState();
    return userData;
  };

  const resendOTP = async () => {
    if (!otpSessionId) {
      throw new Error('No pending OTP session');
    }
    await authAPI.resendOTP(otpSessionId);
  };

  const resetOTPState = () => {
    setRequiresOTP(false);
    setRequiresPhone(false);
    setPendingUserId(null);
    setOtpSessionId(null);
    setOtpPhoneMasked('');
    setPendingCredentials(null);
  };

  const cancelOTP = () => {
    resetOTPState();
  };

  const complete2FALogin = async (totpCode) => {
    if (!pendingCredentials) {
      throw new Error('No pending login');
    }
    
    const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: pendingCredentials.email,
        password: pendingCredentials.password,
        totp_code: totpCode
      })
    });
    
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || 'Invalid 2FA code');
    }
    
    const { token, user: userData } = await response.json();
    localStorage.setItem('yacco_token', token);
    localStorage.setItem('yacco_user', JSON.stringify(userData));
    setUser(userData);
    setRequires2FA(false);
    setPendingCredentials(null);
    return userData;
  };

  const cancel2FA = () => {
    setRequires2FA(false);
    setPendingCredentials(null);
  };

  const register = async (userData) => {
    const response = await authAPI.register(userData);
    const { token, user: newUser } = response.data;
    localStorage.setItem('yacco_token', token);
    localStorage.setItem('yacco_user', JSON.stringify(newUser));
    setUser(newUser);
    return newUser;
  };

  const logout = () => {
    localStorage.removeItem('yacco_token');
    localStorage.removeItem('yacco_user');
    setUser(null);
    setRequires2FA(false);
    resetOTPState();
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      login, 
      register, 
      logout, 
      loading, 
      requires2FA, 
      complete2FALogin, 
      cancel2FA,
      // OTP methods
      requiresOTP,
      requiresPhone,
      otpPhoneMasked,
      submitPhoneNumber,
      completeOTPLogin,
      resendOTP,
      cancelOTP
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
