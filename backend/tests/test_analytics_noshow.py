import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_audit_log_recorded_for_booking_actions(client: AsyncClient, seed_users, auth_headers):
    doctor = seed_users["doctor"]
    recept_headers = auth_headers("receptionist")
    admin_headers = auth_headers("admin")

    # 1. Book appointment
    book_resp = await client.post(
        "/api/v1/appointments",
        json={
            "doctor_id": doctor.id,
            "patient_name": "Audit Patient",
            "patient_phone": "+1-555-0301",
            "reason": "Annual Wellness Visit",
            "appointment_date": "2026-11-21",
            "start_time": "15:00:00",
        },
        headers=recept_headers,
    )
    assert book_resp.status_code == 201
    appt_id = book_resp.json()["id"]

    # 2. Reschedule appointment
    resched_resp = await client.post(
        f"/api/v1/appointments/{appt_id}/reschedule",
        json={"new_date": "2026-11-21", "new_start_time": "15:20:00"},
        headers=recept_headers,
    )
    assert resched_resp.status_code == 200

    # 3. Cancel appointment
    cancel_resp = await client.post(
        f"/api/v1/appointments/{appt_id}/cancel",
        json={"reason": "Patient requested cancellation via phone"},
        headers=recept_headers,
    )
    assert cancel_resp.status_code == 200

    # 4. Check audit logs as Admin
    audit_resp = await client.get("/api/v1/audit", headers=admin_headers)
    assert audit_resp.status_code == 200
    audit_data = audit_resp.json()
    items = audit_data["items"]
    actions = [log["action"] for log in items]

    assert "booking_created" in actions
    assert "booking_rescheduled" in actions
    assert "booking_cancelled" in actions


@pytest.mark.asyncio
async def test_noshow_background_job(client: AsyncClient, seed_users, auth_headers):
    doctor = seed_users["doctor"]
    recept_headers = auth_headers("receptionist")
    admin_headers = auth_headers("admin")

    # Book an appointment scheduled for past time today or yesterday
    book_resp = await client.post(
        "/api/v1/appointments",
        json={
            "doctor_id": doctor.id,
            "patient_name": "NoShow Patient",
            "patient_phone": "+1-555-0302",
            "reason": "Missed visit test",
            "appointment_date": "2026-11-20",  # Yesterday
            "start_time": "09:00:00",
        },
        headers=recept_headers,
    )
    assert book_resp.status_code == 201
    appt_id = book_resp.json()["id"]

    # Trigger no-show sweep endpoint (as background job does)
    job_resp = await client.post("/api/v1/jobs/run-noshow-sweep", headers=admin_headers)
    assert job_resp.status_code == 200
    res = job_resp.json()
    assert res["success"] is True
    assert res["updated_count"] >= 1

    # Verify appointment is now marked no_show
    appt_resp = await client.get(f"/api/v1/appointments/{appt_id}", headers=recept_headers)
    assert appt_resp.status_code == 200
    assert appt_resp.json()["status"] == "no_show"


@pytest.mark.asyncio
async def test_daily_summary_analytics(client: AsyncClient, seed_users, auth_headers):
    recept_headers = auth_headers("receptionist")
    response = await client.get(
        "/api/v1/analytics/daily-summary?date=2026-11-21",
        headers=recept_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["date"] == "2026-11-21"
    assert "total_appointments" in data
    assert "total_no_shows" in data
    assert "clinic_avg_wait_minutes" in data
    assert "doctors" in data
    assert len(data["doctors"]) >= 1
    doc_summary = data["doctors"][0]
    assert "doctor_name" in doc_summary
    assert "specialty" in doc_summary
    assert "room_number" in doc_summary
    assert "booked_count" in doc_summary
    assert "no_show_count" in doc_summary
    assert "avg_wait_minutes" in doc_summary
