import React, { useEffect, useState } from 'react';
import { DailySummaryResponse, AuditLog } from '../types';
import { apiRequest } from '../api/client';
import { 
  BarChart3, 
  Calendar, 
  Clock, 
  Users, 
  AlertTriangle, 
  Activity, 
  ShieldAlert, 
  TrendingUp,
  RefreshCw,
  Zap
} from 'lucide-react';

export const AdminAnalyticsPage: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState<string>('2026-11-21');
  const [summary, setSummary] = useState<DailySummaryResponse | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [isLoadingSummary, setIsLoadingSummary] = useState(false);
  const [isLoadingLogs, setIsLoadingLogs] = useState(false);
  const [isTriggeringSweep, setIsTriggeringSweep] = useState(false);
  const [jobNotice, setJobNotice] = useState<string | null>(null);

  const fetchSummary = async () => {
    setIsLoadingSummary(true);
    try {
      const data = await apiRequest<DailySummaryResponse>(`/api/v1/analytics/daily-summary?date=${selectedDate}`);
      setSummary(data);
    } catch (err: any) {
      console.error('Failed to load daily summary', err);
    } finally {
      setIsLoadingSummary(false);
    }
  };

  const fetchAuditLogs = async () => {
    setIsLoadingLogs(true);
    try {
      const data = await apiRequest<{ items: AuditLog[] } | AuditLog[]>('/api/v1/audit/logs?limit=25');
      const logs = Array.isArray(data) ? data : data.items || [];
      setAuditLogs(logs);
    } catch (err: any) {
      console.error('Failed to load audit logs', err);
    } finally {
      setIsLoadingLogs(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, [selectedDate]);

  useEffect(() => {
    fetchAuditLogs();
  }, []);

  const handleRunNoShowSweep = async () => {
    setIsTriggeringSweep(true);
    setJobNotice(null);
    try {
      const res = await apiRequest<{ success: boolean; updated_count: number; message: string }>(
        '/api/v1/jobs/sweep-no-shows',
        { method: 'POST' }
      );
      setJobNotice(`Sweep executed successfully: ${res.updated_count} expired appointments flagged as no-show.`);
      fetchSummary();
      fetchAuditLogs();
    } catch (err: any) {
      setJobNotice(`Failed to run no-show sweep: ${err.message}`);
    } finally {
      setIsTriggeringSweep(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2 text-sky-600 font-semibold text-xs tracking-wider uppercase">
            <BarChart3 className="w-4 h-4" />
            Executive & Operational Metrics
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight mt-1">
            Clinic Operations & Audit Intelligence
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Monitor real-time patient throughput, queue wait times, doctor utilization, and security audit trails.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handleRunNoShowSweep}
            disabled={isTriggeringSweep}
            className="px-4 py-2 bg-amber-600 hover:bg-amber-700 disabled:bg-slate-300 text-white rounded-xl text-xs font-bold shadow-sm transition flex items-center gap-2"
          >
            <Zap className={`w-4 h-4 ${isTriggeringSweep ? 'animate-spin' : ''}`} />
            {isTriggeringSweep ? 'Running Sweep...' : 'Trigger No-Show Sweep'}
          </button>

          <button
            onClick={() => {
              fetchSummary();
              fetchAuditLogs();
            }}
            className="px-3.5 py-2 border border-slate-300 rounded-xl text-xs text-slate-700 bg-white hover:bg-slate-50 font-semibold flex items-center gap-1.5 shadow-sm"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
        </div>
      </div>

      {jobNotice && (
        <div className="mb-6 p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-sm flex items-center gap-2">
          <Activity className="w-4 h-4 text-amber-600 shrink-0" />
          {jobNotice}
        </div>
      )}

      {/* Date Filter */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm mb-6 flex items-center gap-3">
        <Calendar className="w-4 h-4 text-sky-600" />
        <span className="text-sm font-semibold text-slate-700">Analytics Target Date:</span>
        <input
          type="date"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
          className="border border-slate-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 font-medium"
        />
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase tracking-wider">
            <span>Total Bookings</span>
            <Users className="w-4 h-4 text-sky-600" />
          </div>
          <div className="text-3xl font-black text-slate-900 mt-2 font-mono">
            {summary ? summary.total_appointments ?? summary.total_bookings ?? 0 : '-'}
          </div>
          <div className="text-xs text-slate-500 mt-1">Scheduled for this date</div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase tracking-wider">
            <span>Checked In</span>
            <TrendingUp className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-3xl font-black text-emerald-600 mt-2 font-mono">
            {summary?.total_checked_in ?? 0}
          </div>
          <div className="text-xs text-slate-500 mt-1">Arrived at clinic</div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase tracking-wider">
            <span>Average Wait</span>
            <Clock className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-3xl font-black text-amber-600 mt-2 font-mono">
            {summary ? Math.round((summary.average_clinic_wait_minutes ?? summary.clinic_avg_wait_minutes ?? 0) * 10) / 10 : '-'}m
          </div>
          <div className="text-xs text-slate-500 mt-1">Check-in to consultation</div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 text-xs font-semibold uppercase tracking-wider">
            <span>No-Show Rate</span>
            <AlertTriangle className="w-4 h-4 text-rose-500" />
          </div>
          <div className="text-3xl font-black text-rose-600 mt-2 font-mono">
            {summary ? Math.round((summary.no_show_rate ?? 0) * 100) : 0}%
          </div>
          <div className="text-xs text-slate-500 mt-1">{summary?.no_show_count ?? 0} missed appointments</div>
        </div>
      </div>

      {/* Doctor Performance Breakdown */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm mb-8 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-800">
            Physician Workload & Wait Times Breakdown
          </h2>
        </div>

        {isLoadingSummary ? (
          <div className="p-8 text-center text-slate-400 text-sm animate-pulse">Calculating physician metrics...</div>
        ) : !summary || ((summary.doctor_metrics?.length ?? 0) === 0 && (summary.doctors?.length ?? 0) === 0) ? (
          <div className="p-8 text-center text-slate-500 text-sm">No physician activity recorded for this date.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-100 text-xs uppercase font-semibold text-slate-700 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3">Physician</th>
                  <th className="px-6 py-3">Specialty</th>
                  <th className="px-6 py-3">Room</th>
                  <th className="px-6 py-3 text-center">Bookings</th>
                  <th className="px-6 py-3 text-center">Completed</th>
                  <th className="px-6 py-3 text-center">Avg Wait</th>
                  <th className="px-6 py-3 text-center">Avg Consult</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {(summary.doctor_metrics || summary.doctors || []).map((doc: any) => (
                  <tr key={doc.doctor_id} className="hover:bg-slate-50 transition">
                    <td className="px-6 py-4 font-bold text-slate-900">{doc.doctor_name}</td>
                    <td className="px-6 py-4 text-sky-700 font-medium">{doc.specialty}</td>
                    <td className="px-6 py-4 font-mono font-semibold">Room {doc.room_number || '-'}</td>
                    <td className="px-6 py-4 text-center font-mono font-semibold">
                      {doc.total_bookings ?? doc.total_appointments ?? 0}
                    </td>
                    <td className="px-6 py-4 text-center font-mono text-emerald-600 font-semibold">
                      {doc.completed_count ?? 0}
                    </td>
                    <td className="px-6 py-4 text-center font-mono text-amber-600">
                      {Math.round((doc.average_wait_minutes ?? doc.avg_wait_minutes ?? 0) * 10) / 10}m
                    </td>
                    <td className="px-6 py-4 text-center font-mono text-slate-700">
                      {Math.round((doc.average_consultation_minutes ?? doc.avg_consultation_minutes ?? 0) * 10) / 10}m
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Security Audit Trail */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-sky-600" />
            Security & Operational Audit Trail
          </h2>
          <span className="text-xs text-slate-500 font-mono">Last 25 entries</span>
        </div>

        {isLoadingLogs ? (
          <div className="p-8 text-center text-slate-400 text-sm animate-pulse">Loading audit trail...</div>
        ) : auditLogs.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-sm">No audit logs recorded yet.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono text-slate-600">
              <thead className="bg-slate-100 uppercase font-semibold text-slate-700 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3">Timestamp</th>
                  <th className="px-6 py-3">Action</th>
                  <th className="px-6 py-3">Entity</th>
                  <th className="px-6 py-3">User / IP</th>
                  <th className="px-6 py-3">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50">
                    <td className="px-6 py-3 text-slate-500 whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-3 font-bold text-sky-800 uppercase">{log.action}</td>
                    <td className="px-6 py-3 text-slate-700 font-semibold">
                      {log.entity_name} #{log.entity_id}
                    </td>
                    <td className="px-6 py-3 text-slate-600">
                      User #{log.user_id ?? 'system'} | {log.ip_address ?? 'internal'}
                    </td>
                    <td className="px-6 py-3 text-slate-500 max-w-xs truncate" title={JSON.stringify(log.details)}>
                      {JSON.stringify(log.details)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
