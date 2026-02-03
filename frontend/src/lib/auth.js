import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from './api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [requires2FA, setRequires2FA] = useState(false);
  const [pendingCredentials, setPendingCredentials] = useState(null);

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
      const payload = { email, password };
      if (totpCode) {
        payload.totp_code = totpCode;
      }
      
      const response = await authAPI.login(email, password, totpCode);
      const { token, user: userData } = response.data;
      localStorage.setItem('yacco_token', token);
      localStorage.setItem('yacco_user', JSON.stringify(userData));
      setUser(userData);
      setRequires2FA(false);
      setPendingCredentials(null);
      return userData;
    } catch (error) {
      // Check if 2FA is required
      if (error.response?.status === 403 && error.response?.data?.detail === '2FA_REQUIRED') {
        setRequires2FA(true);
        setPendingCredentials({ email, password });
        throw new Error('2FA_REQUIRED');
      }
      throw error;
    }
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
    setPendingCredentials(null);
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
      cancel2FA 
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
