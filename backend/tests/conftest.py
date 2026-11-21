import asyncio
import os
import sys
from datetime import date, time
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.core.deps import get_db
from app.database import Base
from app.models.user import User, UserRole
from app.models.doctor import Doctor
from app.models.schedule import DoctorSchedule
from app.core.security import get_password_hash, create_access_token

# Use SQLite with aiosqlite for testing
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def init_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def seed_users(db_session: AsyncSession):
    # Admin
    admin = User(
        email="admin@test.com",
        hashed_password=get_password_hash("AdminPass123!"),
        full_name="Admin Test",
        role=UserRole.ADMIN,
        is_active=True,
    )
    # Receptionist 1
    recept1 = User(
        email="recept1@test.com",
        hashed_password=get_password_hash("ReceptPass123!"),
        full_name="Receptionist One",
        role=UserRole.RECEPTIONIST,
        is_active=True,
    )
    # Receptionist 2 (for race condition tests)
    recept2 = User(
        email="recept2@test.com",
        hashed_password=get_password_hash("ReceptPass123!"),
        full_name="Receptionist Two",
        role=UserRole.RECEPTIONIST,
        is_active=True,
    )
    # Doctor User
    doc_user = User(
        email="doc@test.com",
        hashed_password=get_password_hash("DocPass123!"),
        full_name="Dr. Test Doctor",
        role=UserRole.DOCTOR,
        is_active=True,
    )
    db_session.add_all([admin, recept1, recept2, doc_user])
    await db_session.flush()

    # Doctor Profile
    doctor = Doctor(
        user_id=doc_user.id,
        specialty="General Medicine",
        room_number="Room 101",
        bio="Test doctor profile",
        is_active=True,
    )
    db_session.add(doctor)
    await db_session.flush()

    # Doctor Schedules (Monday - Sunday, 09:00 - 17:00, 20-min slots)
    for day in range(7):
        db_session.add(
            DoctorSchedule(
                doctor_id=doctor.id,
                day_of_week=day,
                start_time=time(9, 0),
                end_time=time(17, 0),
                slot_duration_minutes=20,
                is_active=True,
            )
        )

    await db_session.commit()
    return {
        "admin": admin,
        "recept1": recept1,
        "recept2": recept2,
        "doc_user": doc_user,
        "doctor": doctor,
    }


@pytest.fixture
def auth_headers(seed_users):
    def _get_headers(role: str):
        if role == "admin":
            user = seed_users["admin"]
        elif role == "receptionist":
            user = seed_users["recept1"]
        elif role == "receptionist2":
            user = seed_users["recept2"]
        elif role == "doctor":
            user = seed_users["doc_user"]
        else:
            raise ValueError(f"Unknown role {role}")

        token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role.value}
        )
        return {"Authorization": f"Bearer {token}"}

    return _get_headers
