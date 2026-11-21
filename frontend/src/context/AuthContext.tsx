import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, Role } from '../types';
import { apiRequest } from '../api/client';

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, role?: Role) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('access_token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchMe = async () => {
      if (!token) {
        setIsLoading(false);
        return;
      }
      try {
        const me = await apiRequest<User>('/api/v1/auth/me');
        setUser(me);
      } catch (err) {
        console.error('Failed to restore auth session:', err);
        logout();
      } finally {
        setIsLoading(false);
      }
    };

    fetchMe();
  }, [token]);

  const login = async (email: string, _role?: Role) => {
    setIsLoading(true);
    try {
      const data = await apiRequest<{ access_token: string; user?: User }>('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password: 'password123' }),
      });
      localStorage.setItem('access_token', data.access_token);
      setToken(data.access_token);
      const me = data.user || (await apiRequest<User>('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${data.access_token}` },
      }));
      setUser(me);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        logout,
        isLoading,
        isAuthenticated: !!token && !!user,
      }}
    >
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
