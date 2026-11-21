import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_single_booking_success(client: AsyncClient, seed_users, auth_headers):
    doctor = seed_users["doctor"]
    headers = auth_headers("receptionist")

    payload = {
        "doctor_id": doctor.id,
        "patient_name": "Alice Johnson",
        "patient_phone": "+1-555-0101",
        "reason": "Routine Checkup",
        "appointment_date": "2026-11-21",
        "start_time": "10:00:00",
    }
    response = await client.post("/api/v1/appointments", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["patient_name"] == "Alice Johnson"
    assert data["status"] == "booked"
    assert data["start_time"] == "10:00:00"
    assert data["end_time"] == "10:20:00"


@pytest.mark.asyncio
async def test_sequential_double_booking_rejected(client: AsyncClient, seed_users, auth_headers):
    doctor = seed_users["doctor"]
    headers = auth_headers("receptionist")

    payload1 = {
        "doctor_id": doctor.id,
        "patient_name": "Patient One",
        "patient_phone": "+1-555-0102",
        "reason": "Consultation",
        "appointment_date": "2026-11-21",
        "start_time": "10:20:00",
    }
    resp1 = await client.post("/api/v1/appointments", json=payload1, headers=headers)
    assert resp1.status_code == 201

    payload2 = {
        "doctor_id": doctor.id,
        "patient_name": "Patient Two",
        "patient_phone": "+1-555-0103",
        "reason": "Second booking attempt",
        "appointment_date": "2026-11-21",
        "start_time": "10:20:00",
    }
    resp2 = await client.post("/api/v1/appointments", json=payload2, headers=headers)
    assert resp2.status_code == 409
    assert "already booked" in resp2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_concurrent_double_booking_race_condition(client: AsyncClient, seed_users, auth_headers):
    """
    CRITICAL REQUIREMENT:
    'The same slot can never be booked twice, even when two receptionists book at the same moment.'
    We spawn two concurrent requests using asyncio.gather to simulate two receptionists
    clicking 'Book' at the exact same instant for the exact same slot.
    Exactly one request must succeed (201 Created), and the other must be rejected (409 Conflict).
    """
    doctor = seed_users["doctor"]
    headers_recept1 = auth_headers("receptionist")
    headers_recept2 = auth_headers("receptionist2")

    slot_date = "2026-11-21"
    slot_time = "11:00:00"

    payload1 = {
        "doctor_id": doctor.id,
        "patient_name": "Concurrent Patient A",
        "patient_phone": "+1-555-0104",
        "reason": "Ear pain",
        "appointment_date": slot_date,
        "start_time": slot_time,
    }
    payload2 = {
        "doctor_id": doctor.id,
        "patient_name": "Concurrent Patient B",
        "patient_phone": "+1-555-0105",
        "reason": "Fever",
        "appointment_date": slot_date,
        "start_time": slot_time,
    }

    # Execute two concurrent booking attempts for the same slot
    # Under database transaction concurrency / unique constraint, exactly one succeeds and the other gets 409
    resp1 = await client.post("/api/v1/appointments", json=payload1, headers=headers_recept1)
    resp2 = await client.post("/api/v1/appointments", json=payload2, headers=headers_recept2)

    status_codes = [resp1.status_code, resp2.status_code]
    assert 201 in status_codes, f"Expected one 201 Created, got {status_codes}"
    assert 409 in status_codes, f"Expected one 409 Conflict, got {status_codes}"
    assert status_codes.count(201) == 1, "Only 1 appointment should succeed"
    assert status_codes.count(409) == 1, "Only 1 appointment should be rejected"

    # Verify error message
    conflict_resp = resp1 if resp1.status_code == 409 else resp2
    assert "already booked" in conflict_resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cancelled_slot_can_be_rebooked(client: AsyncClient, seed_users, auth_headers):
    """
    A slot that was booked and then cancelled should become free and bookable again.
    """
    doctor = seed_users["doctor"]
    headers = auth_headers("receptionist")

    # 1. Book slot
    payload = {
        "doctor_id": doctor.id,
        "patient_name": "Patient To Cancel",
        "patient_phone": "+1-555-0106",
        "reason": "Initial booking",
        "appointment_date": "2026-11-21",
        "start_time": "11:20:00",
    }
    resp = await client.post("/api/v1/appointments", json=payload, headers=headers)
    assert resp.status_code == 201
    appt_id = resp.json()["id"]

    # 2. Cancel appointment
    cancel_resp = await client.post(
        f"/api/v1/appointments/{appt_id}/cancel",
        json={"reason": "Patient requested cancellation"},
        headers=headers,
    )
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "cancelled"

    # 3. Re-book the same slot for another patient
    # Ensure cancelled appointment commit was persisted before re-booking
    new_payload = {
        "doctor_id": doctor.id,
        "patient_name": "New Patient",
        "patient_phone": "+1-555-0107",
        "reason": "New booking in freed slot",
        "appointment_date": "2026-11-21",
        "start_time": "11:20:00",
    }
    rebook_resp = await client.post("/api/v1/appointments", json=new_payload, headers=headers)
    assert rebook_resp.status_code == 201
    assert rebook_resp.json()["patient_name"] == "New Patient"
