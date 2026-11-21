import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_patient_check_in_joins_queue(client: AsyncClient, seed_users, auth_headers):
    doctor = seed_users["doctor"]
    recept_headers = auth_headers("receptionist")

    # 1. Book an appointment
    book_payload = {
        "doctor_id": doctor.id,
        "patient_name": "Queue Patient 1",
        "patient_phone": "+1-555-0201",
        "reason": "Severe Cough",
        "appointment_date": "2026-11-21",
        "start_time": "14:00:00",
    }
    book_resp = await client.post("/api/v1/appointments", json=book_payload, headers=recept_headers)
    assert book_resp.status_code == 201
    appt_id = book_resp.json()["id"]

    # 2. Check in patient
    checkin_resp = await client.post(f"/api/v1/queue/check-in/{appt_id}", headers=recept_headers)
    assert checkin_resp.status_code == 200
    ticket = checkin_resp.json()
    assert ticket["status"] == "waiting"
    assert ticket["appointment_id"] == appt_id
    assert "ticket_number" in ticket
    assert ticket["check_in_time"] is not None

    # Verify appointment status updated to checked_in
    appt_resp = await client.get(f"/api/v1/appointments/{appt_id}", headers=recept_headers)
    assert appt_resp.status_code == 200
    assert appt_resp.json()["status"] == "checked_in"


@pytest.mark.asyncio
async def test_doctor_queue_workflow(client: AsyncClient, seed_users, auth_headers):
    """
    Test doctor calling next patient, starting consultation, and marking visit done.
    """
    doctor = seed_users["doctor"]
    recept_headers = auth_headers("receptionist")
    doc_headers = auth_headers("doctor")

    # Book and check in
    book_resp = await client.post(
        "/api/v1/appointments",
        json={
            "doctor_id": doctor.id,
            "patient_name": "Workflow Patient",
            "patient_phone": "+1-555-0202",
            "reason": "Blood Pressure Check",
            "appointment_date": "2026-11-21",
            "start_time": "14:20:00",
        },
        headers=recept_headers,
    )
    appt_id = book_resp.json()["id"]

    checkin_resp = await client.post(f"/api/v1/queue/check-in/{appt_id}", headers=recept_headers)
    ticket_id = checkin_resp.json()["id"]

    # Doctor views queue
    queue_resp = await client.get(f"/api/v1/queue/doctor/{doctor.id}", headers=doc_headers)
    assert queue_resp.status_code == 200
    queue = queue_resp.json()
    assert len(queue) >= 1
    assert any(t["id"] == ticket_id for t in queue)

    # Doctor calls patient
    call_resp = await client.post(f"/api/v1/queue/{ticket_id}/call", headers=doc_headers)
    assert call_resp.status_code == 200
    assert call_resp.json()["status"] == "called"
    assert call_resp.json()["called_time"] is not None

    # Doctor starts consultation
    start_resp = await client.post(f"/api/v1/queue/{ticket_id}/start", headers=doc_headers)
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "in_consultation"
    assert start_resp.json()["consultation_start_time"] is not None

    # Doctor marks visit done
    complete_resp = await client.post(f"/api/v1/queue/{ticket_id}/complete", headers=doc_headers)
    assert complete_resp.status_code == 200
    assert complete_resp.json()["status"] == "completed"
    assert complete_resp.json()["completed_time"] is not None

    # Verify appointment status is completed
    appt_resp = await client.get(f"/api/v1/appointments/{appt_id}", headers=doc_headers)
    assert appt_resp.status_code == 200
    assert appt_resp.json()["status"] == "completed"
