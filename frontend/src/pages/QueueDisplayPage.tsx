import React, { useEffect, useState } from 'react';
import { QueueTicket, Doctor } from '../types';
import { apiRequest } from '../api/client';
import { useWebSocket } from '../hooks/useWebSocket';
import { 
  Tv, 
  Clock, 
  UserCheck, 
  Activity, 
  Stethoscope, 
  Volume2,
  Calendar
} from 'lucide-react';

export const QueueDisplayPage: React.FC = () => {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [doctorQueues, setDoctorQueues] = useState<{ [doctorId: number]: QueueTicket[] }>({});
  const [currentTime, setCurrentTime] = useState<string>(new Date().toLocaleTimeString());
  const [activeCallTicket, setActiveCallTicket] = useState<{ number: string; doctorName: string; room: string } | null>(null);

  // Connect to general queue broadcast channel via WebSocket
  const { isConnected } = useWebSocket('queue_updates', (msg) => {
    if (msg.type === 'ticket_called') {
      const ticket = msg.payload;
      setActiveCallTicket({
        number: ticket.ticket_number || `#${ticket.queue_number}`,
        doctorName: ticket.doctor_name || 'Assigned Physician',
        room: ticket.room_number || 'Room 101',
      });
      refreshAllQueues();
    } else if (msg.type === 'queue_updated' || msg.type === 'ticket_status_change') {
      refreshAllQueues();
    }
  });

  const refreshAllQueues = async () => {
    try {
      const res = await apiRequest<{ items: Doctor[] } | Doctor[]>('/api/v1/doctors');
      const docs = Array.isArray(res) ? res : res.items || [];
      setDoctors(docs);

      const queueMap: { [doctorId: number]: QueueTicket[] } = {};
      await Promise.all(
        docs.map(async (doc) => {
          try {
            const tickets = await apiRequest<QueueTicket[]>(`/api/v1/queue/doctor/${doc.id}`);
            queueMap[doc.id] = tickets || [];
          } catch {
            queueMap[doc.id] = [];
          }
        })
      );
      setDoctorQueues(queueMap);
    } catch (err) {
      console.error('Failed to refresh queue display:', err);
    }
  };

  useEffect(() => {
    refreshAllQueues();
    const clockInterval = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    }, 1000);

    const pollInterval = setInterval(() => {
      refreshAllQueues();
    }, 10000);

    return () => {
      clearInterval(clockInterval);
      clearInterval(pollInterval);
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col justify-between selection:bg-sky-500 selection:text-white">
      {/* Top Banner */}
      <header className="bg-slate-900 border-b border-slate-800 px-6 py-4 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-sky-500/20 border border-sky-400/30 flex items-center justify-center text-sky-400">
            <Tv className="w-6 h-6 animate-pulse" />
          </div>
          <div>
            <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2">
              CLINIC<span className="text-sky-400">Q</span>
              <span className="text-xs uppercase bg-sky-950 text-sky-400 border border-sky-800/80 px-2 py-0.5 rounded font-mono">
                Waiting Hall Monitor
              </span>
            </h1>
            <p className="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5">
              <span className={`inline-block w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-400 ring-2 ring-emerald-950' : 'bg-amber-400 animate-ping'}`} />
              {isConnected ? 'Real-Time Sync Connected' : 'Connecting to Live Dispatcher...'}
            </p>
          </div>
        </div>

        {/* Big Digital Clock */}
        <div className="flex items-center gap-6 font-mono">
          <div className="flex items-center gap-2 bg-slate-800/80 px-4 py-2 rounded-xl border border-slate-700/60 shadow-inner">
            <Calendar className="w-4 h-4 text-sky-400" />
            <span className="text-slate-300 text-sm font-sans">Today's Sessions</span>
          </div>
          <div className="flex items-center gap-2 bg-slate-900 px-5 py-2 rounded-xl border border-sky-500/30 text-2xl font-bold tracking-wider text-sky-400 shadow-[0_0_15px_rgba(56,189,248,0.15)]">
            <Clock className="w-5 h-5 text-sky-400" />
            <span>{currentTime}</span>
          </div>
        </div>
      </header>

      {/* Main Announcement Flash Banner (When ticket is called) */}
      {activeCallTicket && (
        <div className="bg-gradient-to-r from-sky-600 via-indigo-600 to-sky-600 px-6 py-4 border-y border-sky-300 shadow-xl animate-bounce">
          <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-white text-indigo-700 rounded-full shadow">
                <Volume2 className="w-8 h-8 animate-spin" />
              </div>
              <div>
                <div className="text-xs font-bold uppercase tracking-widest text-sky-100">NOW CALLING</div>
                <div className="text-4xl font-black text-white tracking-wider font-mono">
                  TICKET {activeCallTicket.number}
                </div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-xl font-bold text-white">Please proceed to {activeCallTicket.room}</div>
              <div className="text-sm text-sky-100">{activeCallTicket.doctorName}</div>
            </div>
          </div>
        </div>
      )}

      {/* Grid of Doctor Consultation Rooms */}
      <main className="flex-1 p-6 max-w-7xl mx-auto w-full">
        {doctors.length === 0 ? (
          <div className="h-64 flex flex-col items-center justify-center text-slate-500">
            <Activity className="w-12 h-12 mb-3 text-slate-700 animate-spin" />
            <p>Loading clinic room queues...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {doctors.map((doc) => {
              const tickets = doctorQueues[doc.id] || [];
              const servingTicket = tickets.find((t) => t.status === 'in_progress' || t.status === 'called');
              const waitingTickets = tickets.filter((t) => t.status === 'waiting' || t.status === 'checked_in');

              return (
                <div
                  key={doc.id}
                  className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-lg flex flex-col"
                >
                  {/* Doctor & Room Header */}
                  <div className="bg-slate-850 p-4 border-b border-slate-800 flex justify-between items-start">
                    <div>
                      <div className="flex items-center gap-1.5 text-sky-400 text-xs font-bold uppercase tracking-wider">
                        <Stethoscope className="w-3.5 h-3.5" />
                        {doc.specialty || 'General Practice'}
                      </div>
                      <h2 className="text-lg font-bold text-white mt-0.5">{doc.full_name}</h2>
                    </div>
                    <div className="text-right">
                      <span className="bg-sky-500/10 text-sky-300 border border-sky-500/20 px-2.5 py-1 rounded-lg text-xs font-mono font-bold">
                        ROOM {doc.room_number || '1'}
                      </span>
                    </div>
                  </div>

                  {/* Currently Serving Display */}
                  <div className="p-5 bg-slate-900/90 border-b border-slate-800/80">
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-1">
                      Currently Serving
                    </span>
                    {servingTicket ? (
                      <div className="flex items-center justify-between bg-sky-950/60 border border-sky-500/30 rounded-xl p-3">
                        <div className="font-mono text-3xl font-black text-sky-400">
                          {servingTicket.ticket_number || `Q-${servingTicket.queue_number}`}
                        </div>
                        <span className="text-xs uppercase font-bold px-2 py-1 bg-sky-500 text-slate-950 rounded">
                          {servingTicket.status === 'called' ? 'CALLED' : 'IN ROOM'}
                        </span>
                      </div>
                    ) : (
                      <div className="p-3 rounded-xl border border-slate-800 bg-slate-950/40 text-center text-slate-500 font-mono text-sm">
                        Waiting for next patient
                      </div>
                    )}
                  </div>

                  {/* Waiting Queue List */}
                  <div className="p-4 flex-1 flex flex-col justify-between">
                    <div>
                      <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2.5 flex items-center justify-between">
                        <span className="flex items-center gap-1">
                          <UserCheck className="w-3.5 h-3.5 text-slate-500" />
                          Next in Queue
                        </span>
                        <span className="text-sky-400 font-mono">{waitingTickets.length} waiting</span>
                      </div>

                      {waitingTickets.length === 0 ? (
                        <p className="text-xs text-slate-600 py-3 italic text-center">No patients waiting in queue</p>
                      ) : (
                        <div className="flex flex-wrap gap-2">
                          {waitingTickets.slice(0, 8).map((t, index) => (
                            <span
                              key={t.id}
                              className={`px-3 py-1.5 rounded-lg font-mono text-xs font-bold border ${
                                index === 0
                                  ? 'bg-amber-950/40 border-amber-500/40 text-amber-300'
                                  : 'bg-slate-800 border-slate-700 text-slate-300'
                              }`}
                            >
                              {t.ticket_number || `Q-${t.queue_number}`}
                            </span>
                          ))}
                          {waitingTickets.length > 8 && (
                            <span className="px-2 py-1 text-slate-500 text-xs self-center font-mono">
                              +{waitingTickets.length - 8} more
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>

      {/* Footer Instructions */}
      <footer className="bg-slate-900 border-t border-slate-800 px-6 py-3 text-center text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between gap-2">
        <p>Please take a seat and wait for your ticket number to appear on the screen.</p>
        <p className="font-mono text-slate-400">ClinicQ Real-Time Patient Flow System</p>
      </footer>
    </div>
  );
};
