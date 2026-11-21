from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from app.models.doctor import Doctor
from app.models.user import User, UserRole
from app.models.schedule import DoctorSchedule
from app.schemas.doctor import DoctorCreate, DoctorUpdate
from app.schemas.user import UserCreate
from app.core.security import get_password_hash
from app.core.exceptions import NotFoundException, ConflictException


async def get_doctor_by_id(db: AsyncSession, doctor_id: int) -> Doctor:
    stmt = (
        select(Doctor)
        .options(selectinload(Doctor.user), selectinload(Doctor.schedules))
        .where(Doctor.id == doctor_id)
    )
    result = await db.execute(stmt)
    doctor = result.scalar_one_or_none()
    if not doctor:
        raise NotFoundException(f"Doctor with ID {doctor_id} not found")
    return doctor


async def list_doctors(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    specialty: str | None = None,
    is_active: bool | None = None,
) -> tuple[list[Doctor], int]:
    stmt = select(Doctor).options(selectinload(Doctor.user), selectinload(Doctor.schedules))
    
    if specialty:
        stmt = stmt.where(Doctor.specialty.ilike(f"%{specialty}%"))
    if is_active is not None:
        stmt = stmt.where(Doctor.is_active == is_active)
        
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()
    
    stmt = stmt.order_by(Doctor.id).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    doctors = list(result.scalars().all())
    return doctors, total


async def create_doctor(db: AsyncSession, doctor_in: DoctorCreate) -> Doctor:
    user_id = doctor_in.user_id
    
    if doctor_in.user:
        user_create = doctor_in.user
    elif doctor_in.email and doctor_in.password:
        user_create = UserCreate(
            email=doctor_in.email,
            password=doctor_in.password,
            full_name=doctor_in.full_name or "Doctor",
            role=UserRole.DOCTOR,
        )
    else:
        user_create = None

    if user_create:
        # Create user account for doctor
        # Check if email already exists
        check_user = await db.execute(select(User).where(User.email == user_create.email))
        if check_user.scalar_one_or_none():
            raise ConflictException(f"A user with email '{user_create.email}' already exists.")
        
        new_user = User(
            email=user_create.email,
            full_name=user_create.full_name,
            role=UserRole.DOCTOR,
            hashed_password=get_password_hash(user_create.password),
            is_active=user_create.is_active,
        )
        db.add(new_user)
        await db.flush()
        user_id = new_user.id
    
    if not user_id:
        raise ConflictException("Either user_id or user object must be provided to create a doctor profile.")
    
    # Check if doctor already exists for this user
    existing_doc = await db.execute(select(Doctor).where(Doctor.user_id == user_id))
    if existing_doc.scalar_one_or_none():
        raise ConflictException(f"Doctor profile already exists for user ID {user_id}")
    
    doctor = Doctor(
        user_id=user_id,
        specialty=doctor_in.specialty,
        room_number=doctor_in.room_number,
        bio=doctor_in.bio,
        is_active=doctor_in.is_active,
    )
    db.add(doctor)
    await db.commit()
    return await get_doctor_by_id(db, doctor.id)


async def update_doctor(db: AsyncSession, doctor_id: int, doctor_update: DoctorUpdate) -> Doctor:
    doctor = await get_doctor_by_id(db, doctor_id)
    
    if doctor_update.specialty is not None:
        doctor.specialty = doctor_update.specialty
    if doctor_update.room_number is not None:
        doctor.room_number = doctor_update.room_number
    if doctor_update.bio is not None:
        doctor.bio = doctor_update.bio
    if doctor_update.is_active is not None:
        doctor.is_active = doctor_update.is_active
        
    await db.commit()
    return await get_doctor_by_id(db, doctor_id)
