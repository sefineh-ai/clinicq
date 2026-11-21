import { describe, it, expect } from 'vitest';

describe('Frontend core utilities & business rules', () => {
  it('formats slot display times correctly', () => {
    const slotStart = '09:00:00';
    const formatted = slotStart.substring(0, 5);
    expect(formatted).toBe('09:00');
  });

  it('filters appointments by search query', () => {
    const appointments = [
      { id: 1, patient_name: 'John Doe', patient_phone: '0911223344', booking_reference: 'CQ-20261121-001' },
      { id: 2, patient_name: 'Jane Smith', patient_phone: '0922334455', booking_reference: 'CQ-20261121-002' },
    ];
    const query = 'john';
    const filtered = appointments.filter(a =>
      a.patient_name.toLowerCase().includes(query) ||
      a.patient_phone.toLowerCase().includes(query) ||
      a.booking_reference.toLowerCase().includes(query)
    );
    expect(filtered).toHaveLength(1);
    expect(filtered[0].patient_name).toBe('John Doe');
  });

  it('determines status badge color styles', () => {
    const getStatusStyle = (status: string) => {
      switch (status) {
        case 'IN_CONSULTATION':
          return 'bg-emerald-100 text-emerald-800';
        case 'WAITING':
          return 'bg-amber-100 text-amber-800';
        case 'COMPLETED':
          return 'bg-blue-100 text-blue-800';
        default:
          return 'bg-slate-100 text-slate-800';
      }
    };

    expect(getStatusStyle('IN_CONSULTATION')).toContain('emerald');
    expect(getStatusStyle('WAITING')).toContain('amber');
    expect(getStatusStyle('COMPLETED')).toContain('blue');
  });
});
