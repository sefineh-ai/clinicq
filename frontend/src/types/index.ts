export type Role = 'admin' | 'doctor' | 'receptionist' | 'patient';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  phone?: string;
  is_active: boolean;
  created_at: string;
}

export interface Doctor {
  id: number;
  user_id: number;
  specialty: string;
  room_number: string;
  full_name?: string;
  bio?: string;
  user?: User;
}

export interface Schedule {
  id: number;
  doctor_id: number;
  day_of_week: number;
  start_time: string;
  end_time: string;
  slot_duration_minutes: number;
  is_active: boolean;
}

export interface Slot {
  slot_index: number;
  start_time: string;
  end_time: string;
  is_booked: boolean;
  is_available?: boolean;
}

export type FreeSlot = Slot;

export type AppointmentStatus =
  | 'SCHEDULED'
  | 'CONFIRMED'
  | 'CHECKED_IN'
  | 'COMPLETED'
  | 'CANCELLED'
  | 'NO_SHOW'
  | 'scheduled'
  | 'confirmed'
  | 'checked_in'
  | 'completed'
  | 'cancelled'
  | 'no_show';

export interface Appointment {
  id: number;
  patient_id: number;
  doctor_id: number;
  appointment_date: string;
  slot_index: number;
  start_time: string;
  end_time: string;
  status: AppointmentStatus;
  booking_reference?: string;
  patient_name?: string;
  patient_phone?: string;
  booked_by_user_id?: number;
  created_at: string;
  patient?: User;
  doctor?: Doctor;
  ticket?: QueueTicket;
}

export type QueueTicketStatus =
  | 'WAITING'
  | 'CALLED'
  | 'IN_CONSULTATION'
  | 'COMPLETED'
  | 'NO_SHOW'
  | 'CANCELLED'
  | 'waiting'
  | 'called'
  | 'in_progress'
  | 'completed'
  | 'no_show'
  | 'cancelled'
  | 'checked_in';

export interface QueueTicket {
  id: number;
  appointment_id: number;
  ticket_number: string;
  queue_number?: number | string;
  doctor_id: number;
  patient_id: number;
  status: QueueTicketStatus;
  check_in_time: string;
  called_time?: string;
  consultation_start_time?: string;
  consultation_end_time?: string;
  completed_time?: string;
  queue_position?: number;
  estimated_wait_minutes?: number;
  appointment?: Appointment;
}

export interface DailySummaryDoctor {
  doctor_id: number;
  doctor_name: string;
  specialty: string;
  room_number?: string;
  total_bookings?: number;
  total_appointments?: number;
  completed_count?: number;
  no_show_count?: number;
  cancelled_count?: number;
  average_wait_minutes?: number;
  avg_wait_minutes?: number;
  average_consultation_minutes?: number;
  avg_consultation_minutes?: number;
}

export interface DailySummaryResponse {
  date: string;
  total_appointments?: number;
  total_bookings?: number;
  total_checked_in: number;
  total_completed?: number;
  total_no_shows?: number;
  no_show_count?: number;
  no_show_rate?: number;
  average_clinic_wait_minutes?: number;
  clinic_avg_wait_minutes?: number;
  doctor_metrics?: DailySummaryDoctor[];
  doctors?: DailySummaryDoctor[];
}

export interface AuditLog {
  id: number;
  user_id?: number | null;
  action: string;
  entity_name: string;
  entity_id?: string | number | null;
  ip_address?: string | null;
  details?: Record<string, any> | null;
  created_at: string;
}
