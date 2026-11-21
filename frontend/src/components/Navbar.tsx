import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Calendar, 
  Stethoscope, 
  BarChart3, 
  LogOut, 
  Tv, 
  UserCheck, 
  ShieldCheck,
  Activity
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout, login } = useAuth();
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center gap-8">
            <Link to="/" className="flex items-center gap-2 text-sky-700 hover:text-sky-800 font-bold text-xl tracking-tight">
              <Activity className="h-6 w-6 text-sky-600" />
              <span>Clinic<span className="text-slate-900">Q</span></span>
            </Link>

            <nav className="hidden md:flex items-center gap-1">
              <Link
                to="/queue-display"
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5 ${
                  isActive('/queue-display')
                    ? 'bg-sky-50 text-sky-700'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                }`}
              >
                <Tv className="h-4 w-4" />
                Live Waiting Screen
              </Link>

              {user && (
                <>
                  <Link
                    to="/book"
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5 ${
                      isActive('/book')
                        ? 'bg-sky-50 text-sky-700'
                        : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                    }`}
                  >
                    <Calendar className="h-4 w-4" />
                    Book Appointment
                  </Link>

                  {(user.role === 'receptionist' || user.role === 'admin') && (
                    <Link
                      to="/receptionist"
                      className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5 ${
                        isActive('/receptionist')
                          ? 'bg-sky-50 text-sky-700'
                          : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                      }`}
                    >
                      <UserCheck className="h-4 w-4" />
                      Check-in & Desk
                    </Link>
                  )}

                  {(user.role === 'doctor' || user.role === 'admin') && (
                    <Link
                      to="/doctor"
                      className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5 ${
                        isActive('/doctor')
                          ? 'bg-sky-50 text-sky-700'
                          : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                      }`}
                    >
                      <Stethoscope className="h-4 w-4" />
                      Doctor Console
                    </Link>
                  )}

                  {user.role === 'admin' && (
                    <Link
                      to="/admin"
                      className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5 ${
                        isActive('/admin')
                          ? 'bg-sky-50 text-sky-700'
                          : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                      }`}
                    >
                      <BarChart3 className="h-4 w-4" />
                      Admin Analytics
                    </Link>
                  )}
                </>
              )}
            </nav>
          </div>

          <div className="flex items-center gap-3">
            {user ? (
              <div className="flex items-center gap-3">
                <div className="text-right hidden sm:block">
                  <div className="text-sm font-medium text-slate-900">{user.full_name}</div>
                  <div className="text-xs uppercase tracking-wider font-semibold text-sky-600 flex items-center justify-end gap-1">
                    <ShieldCheck className="h-3 w-3" />
                    {user.role}
                  </div>
                </div>
                <button
                  onClick={logout}
                  className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
                  title="Sign out"
                  aria-label="Sign out"
                >
                  <LogOut className="h-5 w-5" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-1 sm:gap-2 flex-wrap sm:flex-nowrap justify-end">
                <span className="text-xs text-slate-500 hidden md:inline">Switch demo user:</span>
                <button
                  onClick={() => login('admin@clinicq.local')}
                  className="px-2 py-1 min-h-[26px] sm:px-2.5 text-[11px] sm:text-xs font-medium rounded border border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
                >
                  Admin
                </button>
                <button
                  onClick={() => login('dr.smith@clinicq.local')}
                  className="px-2 py-1 min-h-[26px] sm:px-2.5 text-[11px] sm:text-xs font-medium rounded border border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
                >
                  Doctor
                </button>
                <button
                  onClick={() => login('reception@clinicq.local')}
                  className="px-2 py-1 min-h-[26px] sm:px-2.5 text-[11px] sm:text-xs font-medium rounded border border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
                >
                  Receptionist
                </button>
                <button
                  onClick={() => login('patient1@clinicq.local')}
                  className="px-2 py-1 min-h-[26px] sm:px-2.5 text-[11px] sm:text-xs font-semibold rounded bg-sky-700 text-white hover:bg-sky-800 shadow-sm"
                >
                  Patient
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
