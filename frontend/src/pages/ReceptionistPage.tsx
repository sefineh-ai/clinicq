import React, { useEffect, useState } from 'react';
import { Appointment, QueueTicket, Doctor } from '../types';
import { apiRequest } from '../api/client';
import { useWebSocket } from '../hooks/useWebSocket';
import { 
  UserCheck, 
  Search, 
  Calendar, 
  Clock, 
  Ticket, 
  AlertCircle, 
  CheckCircle2, 
  Phone,
  RefreshCw
} from 'lucide-react';

export const ReceptionistPage: React.FC = () => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [selectedDoctorId, setSelectedDoctorId] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDate, setSelectedDate] = useState<string>('2026-11-21');
  const [isLoading, setIsLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [checkedInTickets, setCheckedInTickets] = useState<{ [apptId: number]: QueueTicket }>({});

  const { isConnected } = useWebSocket('reception_updates', () => {
    fetchAppointments();
  });

  const fetchAppointments = async () => {
    setIsLoading(true);
    try {
      const res = await apiRequest<{ items: Appointment[] } | Appointment[]>(
        `/api/v1/appointments?date=${selectedDate}`
      );
      const list = Array.isArray(res) ? res : res.items || [];
      setAppointments(list);
    } catch (err: any) {
      console.error('Failed to load appointments:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const fetchDoctors = async () => {
      try {
        const res = await apiRequest<{ items: Doctor[] } | Doctor[]>('/api/v1/doctors');
        setDoctors(Array.isArray(res) ? res : res.items || []);
      } catch (e) {
        console.error(e);
      }
    };
    fetchDoctors();
  }, []);

  useEffect(() => {
    fetchAppointments();
  }, [selectedDate]);

  const handleCheckIn = async (appointmentId: number) => {
    setActionMessage(null);
    try {
      const ticket = await apiRequest<QueueTicket>(`/api/v1/queue/check-in/${appointmentId}`, {
        method: 'POST',
      });
      setCheckedInTickets((prev) => ({ ...prev, [appointmentId]: ticket }));
      setActionMessage({
        type: 'success',
        text: `Patient checked in successfully! Ticket ${ticket.ticket_number || `#${ticket.queue_number}`} generated.`,
      });
      fetchAppointments();
    } catch (err: any) {
      setActionMessage({
        type: 'error',
        text: err.message || 'Failed to check-in patient.',
      });
    }
  };

  const filteredAppointments = appointments.filter((appt) => {
    if (selectedDoctorId !== 'all' && appt.doctor_id !== Number(selectedDoctorId)) {
      return false;
    }
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    const patientName = (appt.patient_name || appt.patient?.full_name || '').toLowerCase();
    const patientPhone = (appt.patient_phone || appt.patient?.phone || '').toLowerCase();
    const ref = (appt.booking_reference || '').toLowerCase();

    return (
      patientName.includes(query) ||
      patientPhone.includes(query) ||
      ref.includes(query)
    );
  });

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
            <UserCheck className="w-8 h-8 text-sky-600" />
            Reception & Patient Check-in
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Check-in booked patients upon arrival to assign queue sequence numbers and broadcast to waiting room monitors.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchAppointments}
            disabled={isLoading}
            className="px-3.5 py-2 border border-slate-300 rounded-lg text-sm text-slate-700 bg-white hover:bg-slate-50 flex items-center gap-1.5 shadow-sm"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
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

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm mb-6 flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2 text-sm text-slate-600">
          <Calendar className="w-4 h-4 text-sky-600" />
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="border border-slate-300 rounded-lg px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
        </div>

        <div className="flex items-center gap-2 text-sm text-slate-600">
          <span>Doctor:</span>
          <select
            value={selectedDoctorId}
            onChange={(e) => setSelectedDoctorId(e.target.value)}
            className="border border-slate-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
          >
            <option value="all">All Doctors</option>
            {doctors.map((d) => (
              <option key={d.id} value={d.id}>
                {d.full_name} ({d.specialty})
              </option>
            ))}
          </select>
        </div>

        <div className="flex-1 min-w-[200px] relative">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by patient name, phone, or code..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
          />
        </div>
      </div>

      {/* Appointments List */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex justify-between items-center bg-slate-50">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-700">
            Appointments for {selectedDate} ({filteredAppointments.length})
          </h2>
          <span className="text-xs text-slate-500 flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-emerald-500' : 'bg-slate-400'}`} />
            Live sync {isConnected ? 'active' : 'idle'}
          </span>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-slate-500 text-sm animate-pulse">Loading appointments...</div>
        ) : filteredAppointments.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            No appointments scheduled or found for this date.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-100/70 text-xs uppercase font-semibold text-slate-700 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3">Slot / Time</th>
                  <th className="px-6 py-3">Patient Details</th>
                  <th className="px-6 py-3">Physician</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {filteredAppointments.map((appt) => {
                  const isCheckedIn = appt.status === 'checked_in' || !!checkedInTickets[appt.id];
                  const ticket = checkedInTickets[appt.id];

                  return (
                    <tr key={appt.id} className="hover:bg-slate-50/80 transition">
                      <td className="px-6 py-4 font-mono font-medium text-slate-900 whitespace-nowrap">
                        <div className="flex items-center gap-1.5">
                          <Clock className="w-4 h-4 text-sky-600" />
                          <span>Slot #{appt.slot_index}</span>
                        </div>
                        <div className="text-xs text-slate-400 font-sans mt-0.5">{appt.appointment_date}</div>
                      </td>

                      <td className="px-6 py-4">
                        <div className="font-bold text-slate-900">{appt.patient_name}</div>
                        <div className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
                          <Phone className="w-3 h-3" />
                          {appt.patient_phone}
                        </div>
                        {appt.booking_reference && (
                          <div className="text-[11px] font-mono text-sky-700 font-semibold mt-1">
                            Ref: {appt.booking_reference}
                          </div>
                        )}
                      </td>

                      <td className="px-6 py-4 text-slate-800">
                        <div className="font-medium">
                          {appt.doctor?.full_name || `Doctor #${appt.doctor_id}`}
                        </div>
                        <div className="text-xs text-slate-500">
                          {appt.doctor?.specialty || 'General'}
                        </div>
                      </td>

                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${
                            isCheckedIn
                              ? 'bg-emerald-100 text-emerald-800'
                              : appt.status === 'cancelled'
                              ? 'bg-rose-100 text-rose-800'
                              : appt.status === 'completed'
                              ? 'bg-indigo-100 text-indigo-800'
                              : 'bg-amber-100 text-amber-800'
                          }`}
                        >
                          {isCheckedIn ? 'Checked-In' : appt.status}
                        </span>
                        {ticket && (
                          <div className="text-xs font-mono font-bold text-emerald-700 mt-1">
                            Ticket: {ticket.ticket_number || `#${ticket.queue_number}`}
                          </div>
                        )}
                      </td>

                      <td className="px-6 py-4 text-right whitespace-nowrap">
                        {isCheckedIn ? (
                          <button
                            disabled
                            className="px-3 py-1.5 bg-slate-100 text-slate-400 text-xs font-medium rounded-lg cursor-not-allowed flex items-center gap-1 ml-auto"
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            Checked In
                          </button>
                        ) : appt.status === 'cancelled' ? (
                          <span className="text-xs text-slate-400 italic">Cancelled</span>
                        ) : (
                          <button
                            onClick={() => handleCheckIn(appt.id)}
                            className="px-3.5 py-1.5 bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold rounded-lg shadow-sm transition flex items-center gap-1.5 ml-auto"
                          >
                            <Ticket className="w-3.5 h-3.5" />
                            Check-In
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
