import React, { useEffect, useState } from 'react';
import { QueueTicket, Doctor } from '../types';
import { apiRequest } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useWebSocket } from '../hooks/useWebSocket';
import { 
  Stethoscope, 
  Volume2, 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  Users, 
  Play, 
  Check, 
  Sparkles,
  Phone,
  RefreshCw
} from 'lucide-react';

export const DoctorConsolePage: React.FC = () => {
  const { user } = useAuth();
  const [doctor, setDoctor] = useState<Doctor | null>(null);
  const [tickets, setTickets] = useState<QueueTicket[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [consultationNotes, setConsultationNotes] = useState('');

  useWebSocket('doctor_console', () => {
    fetchQueue();
  });

  const fetchDoctorProfile = async () => {
    try {
      const res = await apiRequest<{ items: Doctor[] } | Doctor[]>('/api/v1/doctors');
      const docs = Array.isArray(res) ? res : res.items || [];
      // Match doctor profile by logged in user id or fallback to first doctor
      const matched = docs.find((d) => d.user_id === user?.id) || docs[0];
      setDoctor(matched);
      return matched;
    } catch (e) {
      console.error('Failed to load doctor profile', e);
      return null;
    }
  };

  const fetchQueue = async (docId?: number) => {
    const id = docId || doctor?.id;
    if (!id) return;
    setIsLoading(true);
    try {
      const list = await apiRequest<QueueTicket[]>(`/api/v1/queue/doctor/${id}`);
      setTickets(list || []);
    } catch (err: any) {
      console.error('Failed to load queue tickets:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const init = async () => {
      const doc = await fetchDoctorProfile();
      if (doc) {
        fetchQueue(doc.id);
      }
    };
    init();
  }, [user]);

  const handleCallPatient = async (ticketId: number) => {
    setActionMessage(null);
    try {
      await apiRequest(`/api/v1/queue/tickets/${ticketId}/call`, { method: 'POST' });
      setActionMessage({ type: 'success', text: 'Patient called to room! Broadcasted to waiting screens.' });
      fetchQueue();
    } catch (err: any) {
      setActionMessage({ type: 'error', text: err.message || 'Failed to call patient' });
    }
  };

  const handleStartConsultation = async (ticketId: number) => {
    setActionMessage(null);
    try {
      await apiRequest(`/api/v1/queue/tickets/${ticketId}/start`, { method: 'POST' });
      setActionMessage({ type: 'success', text: 'Consultation session started.' });
      fetchQueue();
    } catch (err: any) {
      setActionMessage({ type: 'error', text: err.message || 'Failed to start consultation' });
    }
  };

  const handleCompleteConsultation = async (ticketId: number) => {
    setActionMessage(null);
    try {
      await apiRequest(`/api/v1/queue/tickets/${ticketId}/complete`, {
        method: 'POST',
        body: JSON.stringify({ notes: consultationNotes || undefined }),
      });
      setConsultationNotes('');
      setActionMessage({ type: 'success', text: 'Consultation completed. Metrics updated.' });
      fetchQueue();
    } catch (err: any) {
      setActionMessage({ type: 'error', text: err.message || 'Failed to complete consultation' });
    }
  };

  // Group tickets
  const activeTicket = tickets.find((t) => t.status === 'in_progress' || t.status === 'called');
  const waitingTickets = tickets.filter((t) => t.status === 'checked_in' || t.status === 'waiting');
  const completedTickets = tickets.filter((t) => t.status === 'completed');

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2 text-sky-600 font-semibold text-xs tracking-wider uppercase">
            <Stethoscope className="w-4 h-4" />
            Physician Consultation Room
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight mt-1">
            {doctor?.full_name || 'Doctor Console'} - Room {doctor?.room_number || '101'}
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Specialty: {doctor?.specialty || 'General Practitioner'} | Real-time queue dispatcher
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => fetchQueue()}
            disabled={isLoading}
            className="px-3.5 py-2 border border-slate-300 rounded-lg text-sm text-slate-700 bg-white hover:bg-slate-50 flex items-center gap-1.5 shadow-sm"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh Queue
          </button>
        </div>
      </div>

      {actionMessage && (
        <div
          className={`p-4 rounded-xl mb-6 flex items-start gap-3 border ${
            actionMessage.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}
        >
          {actionMessage.type === 'success' ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          )}
          <div className="text-sm font-medium">{actionMessage.text}</div>
        </div>
      )}

      {/* Main Grid: Active Patient & Queue */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Patient Card (Left 2 Columns) */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-6">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-amber-500" />
                Current Active Patient
              </h2>
              {activeTicket ? (
                <span
                  className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${
                    activeTicket.status === 'called'
                      ? 'bg-amber-100 text-amber-800 animate-pulse'
                      : 'bg-emerald-100 text-emerald-800'
                  }`}
                >
                  {activeTicket.status === 'called' ? 'Called (Waiting for patient)' : 'In Consultation'}
                </span>
              ) : (
                <span className="text-xs text-slate-400">Idle / Ready</span>
              )}
            </div>

            {activeTicket ? (
              <div className="space-y-6">
                <div className="flex flex-wrap items-center justify-between gap-4 p-5 bg-sky-50/60 border border-sky-100 rounded-2xl">
                  <div>
                    <span className="text-xs uppercase font-bold text-sky-800 font-mono tracking-wider">
                      Queue Ticket
                    </span>
                    <div className="text-3xl font-black text-sky-950 font-mono">
                      {activeTicket.ticket_number || `Ticket #${activeTicket.queue_number}`}
                    </div>
                  </div>

                  <div className="text-right">
                    <div className="text-lg font-bold text-slate-900">
                      {activeTicket.appointment?.patient_name || 'Patient'}
                    </div>
                    <div className="text-xs text-slate-500 flex items-center justify-end gap-1 mt-0.5">
                      <Phone className="w-3 h-3" />
                      {activeTicket.appointment?.patient_phone || 'N/A'}
                    </div>
                  </div>
                </div>

                {/* Consultation Controls */}
                <div className="flex flex-wrap gap-3">
                  {activeTicket.status === 'called' && (
                    <>
                      <button
                        onClick={() => handleCallPatient(activeTicket.id)}
                        className="px-4 py-2.5 bg-amber-500 hover:bg-amber-600 text-white font-medium rounded-xl text-sm shadow-sm transition flex items-center gap-2"
                      >
                        <Volume2 className="w-4 h-4" />
                        Recall Ticket
                      </button>
                      <button
                        onClick={() => handleStartConsultation(activeTicket.id)}
                        className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-xl text-sm shadow-sm transition flex items-center gap-2"
                      >
                        <Play className="w-4 h-4" />
                        Start Consultation
                      </button>
                    </>
                  )}

                  {activeTicket.status === 'in_progress' && (
                    <div className="w-full space-y-4">
                      <div>
                        <label className="block text-xs font-semibold text-slate-700 mb-1.5">
                          Clinical Notes & Diagnosis
                        </label>
                        <textarea
                          rows={3}
                          placeholder="Enter consultation summary, prescriptions, or follow-up plans..."
                          value={consultationNotes}
                          onChange={(e) => setConsultationNotes(e.target.value)}
                          className="w-full p-3 border border-slate-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
                        />
                      </div>

                      <button
                        onClick={() => handleCompleteConsultation(activeTicket.id)}
                        className="px-6 py-2.5 bg-sky-600 hover:bg-sky-700 text-white font-semibold rounded-xl text-sm shadow-md transition flex items-center gap-2"
                      >
                        <Check className="w-4 h-4" />
                        Finish & Release Consultation
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center py-12 px-4 bg-slate-50 rounded-2xl border border-dashed border-slate-200">
                <Users className="w-12 h-12 text-slate-300 mx-auto mb-2" />
                <h3 className="text-sm font-semibold text-slate-700">No Patient in Room</h3>
                <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                  {waitingTickets.length > 0
                    ? `You have ${waitingTickets.length} patient(s) waiting in queue. Call the next patient to begin.`
                    : 'Your queue is currently clear. Checked-in patients will appear here automatically.'}
                </p>
                {waitingTickets.length > 0 && (
                  <button
                    onClick={() => handleCallPatient(waitingTickets[0].id)}
                    className="mt-4 px-5 py-2 bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold rounded-lg shadow-sm transition inline-flex items-center gap-1.5"
                  >
                    <Volume2 className="w-4 h-4" />
                    Call Next Patient ({waitingTickets[0].ticket_number || `#${waitingTickets[0].queue_number}`})
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Recently Completed */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-700 mb-4">
              Consultations Completed Today ({completedTickets.length})
            </h3>
            {completedTickets.length === 0 ? (
              <div className="text-xs text-slate-400 italic py-4">No completed consultations yet today.</div>
            ) : (
              <div className="space-y-2">
                {completedTickets.map((t) => (
                  <div
                    key={t.id}
                    className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100 text-xs"
                  >
                    <div className="flex items-center gap-3">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      <span className="font-mono font-bold text-slate-800">
                        {t.ticket_number || `#${t.queue_number}`}
                      </span>
                      <span className="font-medium text-slate-700">
                        {t.appointment?.patient_name || 'Patient'}
                      </span>
                    </div>
                    <div className="text-slate-400 font-mono">
                      Done at {t.completed_time ? new Date(t.completed_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'N/A'}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Waiting Queue List (Right 1 Column) */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 flex flex-col h-full">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Users className="w-4 h-4 text-sky-600" />
              Waiting List ({waitingTickets.length})
            </h2>
            <span className="text-[11px] font-mono bg-sky-50 text-sky-700 px-2 py-0.5 rounded font-bold">
              In Queue
            </span>
          </div>

          {isLoading ? (
            <div className="text-center py-8 text-xs text-slate-400">Updating queue...</div>
          ) : waitingTickets.length === 0 ? (
            <div className="text-center py-12 text-slate-400 text-xs italic">
              No patients currently waiting in line.
            </div>
          ) : (
            <div className="space-y-3 flex-1 overflow-y-auto">
              {waitingTickets.map((t, index) => (
                <div
                  key={t.id}
                  className={`p-3.5 rounded-xl border transition ${
                    index === 0
                      ? 'bg-sky-50/70 border-sky-200 ring-1 ring-sky-300/40'
                      : 'bg-white border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-sm font-black text-sky-900">
                      {t.ticket_number || `#${t.queue_number}`}
                    </span>
                    <span className="text-[10px] font-bold uppercase bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                      Pos #{index + 1}
                    </span>
                  </div>

                  <div className="text-xs font-semibold text-slate-800 mt-1">
                    {t.appointment?.patient_name || 'Patient'}
                  </div>

                  <div className="flex items-center justify-between mt-3 pt-2 border-t border-slate-100">
                    <div className="text-[11px] text-slate-400 flex items-center gap-1 font-mono">
                      <Clock className="w-3 h-3" />
                      Slot #{t.appointment?.slot_index}
                    </div>

                    {!activeTicket && (
                      <button
                        onClick={() => handleCallPatient(t.id)}
                        className="px-2.5 py-1 bg-sky-600 hover:bg-sky-700 text-white rounded text-[11px] font-bold transition flex items-center gap-1"
                      >
                        <Volume2 className="w-3 h-3" />
                        Call
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
