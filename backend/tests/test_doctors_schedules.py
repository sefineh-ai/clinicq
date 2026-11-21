import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_doctors_list(client: AsyncClient, seed_users):
    response = await client.get("/api/v1/doctors")
    assert response.status_code == 200
    data = response.json()
    doctors = data.get("items", data) if isinstance(data, dict) else data
    assert len(doctors) >= 1
    assert doctors[0]["specialty"] == "General Medicine"
    assert doctors[0]["room_number"] == "Room 101"


@pytest.mark.asyncio
async def test_admin_create_doctor(client: AsyncClient, auth_headers):
    headers = auth_headers("admin")
    payload = {
        "email": "dr.new@test.com",
        "password": "Password123!",
        "full_name": "Dr. Sarah Adams",
        "specialty": "Pediatrics",
        "room_number": "Room 105",
        "bio": "Expert in pediatric care",
    }
    response = await client.post("/api/v1/doctors", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["specialty"] == "Pediatrics"
    assert data["room_number"] == "Room 105"
    assert data["user"]["email"] == "dr.new@test.com"


@pytest.mark.asyncio
async def test_receptionist_cannot_create_doctor(client: AsyncClient, auth_headers):
    headers = auth_headers("receptionist")
    payload = {
        "email": "dr.unauth@test.com",
        "password": "Password123!",
        "full_name": "Dr. Unauth",
        "specialty": "Neurology",
        "room_number": "Room 106",
    }
    response = await client.post("/api/v1/doctors", json=payload, headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_doctor_free_slots(client: AsyncClient, seed_users):
    doctor = seed_users["doctor"]
    # Saturday 2026-11-21
    response = await client.get(
        f"/api/v1/doctors/{doctor.id}/free-slots?date=2026-11-21"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["doctor_id"] == doctor.id
    assert data["date"] == "2026-11-21"
    assert data["slot_duration_minutes"] == 20
    assert len(data["slots"]) > 0
    # First slot should be 09:00:00
    first_slot = data["slots"][0]
    assert first_slot["start_time"] == "09:00:00"
    assert first_slot["is_available"] is True
