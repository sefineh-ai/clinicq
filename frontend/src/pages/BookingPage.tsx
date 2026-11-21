import React, { useEffect, useState } from 'react';
import { Doctor, FreeSlot, Appointment } from '../types';
import { apiRequest } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { Calendar, Clock, Stethoscope, AlertCircle, CheckCircle, ChevronRight, User } from 'lucide-react';

export const BookingPage: React.FC = () => {
  const { user } = useAuth();
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [selectedDoctorId, setSelectedDoctorId] = useState<number | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>('2026-11-21');
  const [slots, setSlots] = useState<FreeSlot[]>([]);
  const [selectedSlotTime, setSelectedSlotTime] = useState<string | null>(null);
  
  // Patient details for guest/receptionist booking or logged in user
  const [patientName, setPatientName] = useState('');
  const [patientPhone, setPatientPhone] = useState('');
  const [patientEmail, setPatientEmail] = useState('');
  
  const [isLoadingDoctors, setIsLoadingDoctors] = useState(false);
  const [isLoadingSlots, setIsLoadingSlots] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successBooking, setSuccessBooking] = useState<Appointment | null>(null);

  useEffect(() => {
    if (user && user.role === 'patient') {
      setPatientName(user.full_name || '');
      setPatientEmail(user.email || '');
      setPatientPhone(user.phone || '');
    }
  }, [user]);

  useEffect(() => {
    const fetchDoctors = async () => {
      setIsLoadingDoctors(true);
      try {
        const res = await apiRequest<{ items: Doctor[] } | Doctor[]>('/api/v1/doctors');
        const list = Array.isArray(res) ? res : res.items || [];
        setDoctors(list);
        if (list.length > 0 && !selectedDoctorId) {
          setSelectedDoctorId(list[0].id);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load doctors');
      } finally {
        setIsLoadingDoctors(false);
      }
    };

    fetchDoctors();
  }, []);

  useEffect(() => {
    if (!selectedDoctorId || !selectedDate) return;

    const fetchSlots = async () => {
      setIsLoadingSlots(true);
      setSelectedSlotTime(null);
      setError(null);
      try {
        const res = await apiRequest<{ slots: FreeSlot[] } | FreeSlot[]>(
          `/api/v1/doctors/${selectedDoctorId}/free-slots?date=${selectedDate}`
        );
        const freeSlots = Array.isArray(res) ? res : res.slots || [];
        setSlots(freeSlots);
      } catch (err: any) {
        setSlots([]);
        setError(err.message || 'No available schedule found for this date.');
      } finally {
        setIsLoadingSlots(false);
      }
    };

    fetchSlots();
  }, [selectedDoctorId, selectedDate]);

  const handleBook = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDoctorId || !selectedSlotTime) {
      setError('Please choose a doctor and a slot time.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const payload = {
        doctor_id: selectedDoctorId,
        appointment_date: selectedDate,
        start_time: selectedSlotTime,
        reason: 'General outpatient consultation',
        patient_name: patientName,
        patient_phone: patientPhone,
        patient_email: patientEmail || undefined,
      };

      const result = await apiRequest<Appointment>('/api/v1/appointments', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      setSuccessBooking(result);
    } catch (err: any) {
      // Handles 409 Conflict gracefully (e.g. race condition)
      setError(err.message || 'Booking conflict: Slot was taken. Please select another slot.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const selectedDoctor = doctors.find((d) => d.id === selectedDoctorId);

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6">
      <div className="mb-8">
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
          Book an Outpatient Consultation
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          Select an available doctor, pick a date, choose a 15-minute slot, and reserve your ticket immediately.
        </p>
      </div>

      {successBooking ? (
        <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-8 text-center shadow-sm">
          <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-10 h-10" />
          </div>
          <h2 className="text-2xl font-bold text-emerald-900">Appointment Confirmed!</h2>
          <p className="text-emerald-800 mt-2">
            Your appointment has been registered with booking code:
          </p>
          <div className="mt-4 inline-block bg-white px-6 py-3 rounded-xl border border-emerald-300 font-mono text-xl font-bold text-emerald-700 shadow-sm">
            {successBooking.booking_reference || `APT-${successBooking.id}`}
          </div>

          <div className="mt-6 text-sm text-slate-700 max-w-md mx-auto bg-white/70 rounded-xl p-4 border border-emerald-100 text-left space-y-2">
            <div className="flex justify-between">
              <span className="text-slate-500">Doctor:</span>
              <span className="font-semibold">{selectedDoctor?.full_name || `Doctor #${selectedDoctorId}`}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Date & Slot:</span>
              <span className="font-semibold">{successBooking.appointment_date} (Slot #{successBooking.slot_index})</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Patient:</span>
              <span className="font-semibold">{successBooking.patient_name}</span>
            </div>
          </div>

          <div className="mt-8 flex justify-center gap-4">
            <button
              onClick={() => {
                setSuccessBooking(null);
                setSelectedSlotTime(null);
              }}
              className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg shadow-sm transition"
            >
              Book Another Appointment
            </button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleBook} className="space-y-8">
          {error && (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-start gap-3 text-rose-800 text-sm">
              <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold">Unable to complete booking</p>
                <p className="mt-0.5">{error}</p>
              </div>
            </div>
          )}

          {/* Doctor Selection */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <label className="block text-sm font-semibold text-slate-800 mb-3 flex items-center gap-2">
              <Stethoscope className="w-4 h-4 text-sky-600" />
              1. Choose a Doctor & Department
            </label>
            {isLoadingDoctors ? (
              <div className="py-6 text-center text-slate-500 text-sm animate-pulse">Loading doctors...</div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {doctors.map((doc) => {
                  const isSelected = selectedDoctorId === doc.id;
                  return (
                    <button
                      type="button"
                      key={doc.id}
                      onClick={() => setSelectedDoctorId(doc.id)}
                      className={`text-left p-4 rounded-xl border transition-all ${
                        isSelected
                          ? 'border-sky-600 bg-sky-50/70 ring-2 ring-sky-500/20'
                          : 'border-slate-200 hover:border-slate-300 bg-white'
                      }`}
                    >
                      <div className="font-bold text-slate-900">{doc.user?.full_name || doc.full_name || `Dr. #${doc.id}`}</div>
                      <div className="text-xs text-sky-700 font-medium mt-0.5">{doc.specialty}</div>
                      <div className="text-xs text-slate-500 mt-2 flex items-center gap-1">
                        {doc.room_number ? (doc.room_number.startsWith('Room') ? doc.room_number : `Room ${doc.room_number}`) : 'Room TBD'}
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Date & Slot Selection */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
              <label className="text-sm font-semibold text-slate-800 flex items-center gap-2">
                <Calendar className="w-4 h-4 text-sky-600" />
                2. Select Date & Free Time Slot
              </label>
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="px-3 py-1.5 border border-slate-300 rounded-lg text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>

            {isLoadingSlots ? (
              <div className="py-8 text-center text-slate-500 text-sm animate-pulse">
                Checking live slot availability...
              </div>
            ) : slots.length === 0 ? (
              <div className="p-6 text-center bg-slate-50 rounded-xl text-slate-500 text-sm">
                No active schedule or all slots are booked for this date. Please pick another date.
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                {slots.map((s, idx) => {
                  const isAvailable = s.is_available;
                  const isSelected = selectedSlotTime === s.start_time;

                  return (
                    <button
                      key={`${s.start_time}-${idx}`}
                      type="button"
                      disabled={!isAvailable}
                      onClick={() => setSelectedSlotTime(s.start_time)}
                      className={`p-3 rounded-xl border text-center transition ${
                        !isAvailable
                          ? 'bg-slate-100 border-slate-200 text-slate-400 cursor-not-allowed'
                          : isSelected
                          ? 'bg-sky-600 border-sky-600 text-white shadow-sm ring-2 ring-sky-300'
                          : 'bg-white border-slate-200 text-slate-800 hover:border-sky-400 hover:bg-sky-50/50'
                      }`}
                    >
                      <div className="font-mono text-sm font-bold flex items-center justify-center gap-1">
                        <Clock className="w-3.5 h-3.5" />
                        {s.start_time.substring(0, 5)}
                      </div>
                      <div className="text-xs mt-1">
                        {isAvailable ? (isSelected ? 'Selected' : 'Available') : 'Booked'}
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Patient Details Form */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
              <User className="w-4 h-4 text-sky-600" />
              3. Patient Information
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Full Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. John Doe"
                  value={patientName}
                  onChange={(e) => setPatientName(e.target.value)}
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-600 mb-1">Phone Number *</label>
                <input
                  type="tel"
                  required
                  placeholder="e.g. +1 555-0192"
                  value={patientPhone}
                  onChange={(e) => setPatientPhone(e.target.value)}
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-xs font-medium text-slate-600 mb-1">Email (Optional)</label>
                <input
                  type="email"
                  placeholder="e.g. john@example.com"
                  value={patientEmail}
                  onChange={(e) => setPatientEmail(e.target.value)}
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>
            </div>
          </div>

          {/* Submit */}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={isSubmitting || !selectedSlotTime}
              className="px-6 py-3 bg-sky-600 hover:bg-sky-700 disabled:bg-slate-300 text-white font-semibold rounded-xl shadow-md transition flex items-center gap-2"
            >
              {isSubmitting ? 'Reserving Slot...' : 'Confirm Appointment'}
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </form>
      )}
    </div>
  );
};
