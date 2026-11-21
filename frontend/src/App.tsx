import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { BookingPage } from './pages/BookingPage';
import { QueueDisplayPage } from './pages/QueueDisplayPage';
import { ReceptionistPage } from './pages/ReceptionistPage';
import { DoctorConsolePage } from './pages/DoctorConsolePage';
import { AdminAnalyticsPage } from './pages/AdminAnalyticsPage';

const ProtectedRoute: React.FC<{
  children: React.ReactNode;
  allowedRoles?: string[];
}> = ({ children, allowedRoles }) => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-slate-500 font-medium text-sm animate-pulse">Checking credentials...</div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/book" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/book" replace />;
  }

  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
          <Routes>
            {/* Fullscreen Waiting Screen (No Navbar) */}
            <Route path="/queue-display" element={<QueueDisplayPage />} />

            {/* Standard Pages with App Navbar */}
            <Route
              path="/*"
              element={
                <div className="flex-1 flex flex-col">
                  <Navbar />
                  <main className="flex-1">
                    <Routes>
                      <Route path="/" element={<Navigate to="/book" replace />} />
                      <Route path="/book" element={<BookingPage />} />
                      <Route
                        path="/receptionist"
                        element={
                          <ProtectedRoute allowedRoles={['receptionist', 'admin']}>
                            <ReceptionistPage />
                          </ProtectedRoute>
                        }
                      />
                      <Route
                        path="/doctor"
                        element={
                          <ProtectedRoute allowedRoles={['doctor', 'admin']}>
                            <DoctorConsolePage />
                          </ProtectedRoute>
                        }
                      />
                      <Route
                        path="/admin"
                        element={
                          <ProtectedRoute allowedRoles={['admin']}>
                            <AdminAnalyticsPage />
                          </ProtectedRoute>
                        }
                      />
                      <Route path="*" element={<Navigate to="/book" replace />} />
                    </Routes>
                  </main>
                </div>
              }
            />
          </Routes>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
};
