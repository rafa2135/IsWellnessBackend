import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from database import Base  # Base declarativa definida en database.py

# ENUMS

class UserRole(str, enum.Enum):
    admin = "admin"
    cliente = "cliente"

class RoutineType(str, enum.Enum):
    manual = "manual"
    auto_ia = "auto_ia"

class RoutineStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    abandoned = "abandoned"

# HELPER FUNCTIONS / FUNCIONES DE AYUDA

def generate_uuid() -> str:
    """UUID como string; necesario para sincronizacion offline (Riesgo R05)."""
    return str(uuid.uuid4())

def get_utc_now() -> datetime:
    """Timestamp UTC consistente para toda la app (evita bugs de timezone)."""
    return datetime.now(timezone.utc)


# MODELS / TABLAS

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(150), nullable=True)  # nombre para mostrar (CU-09)
    # native_enum=False forces VARCHAR in DB, ensuring SQLite/MariaDB parity
    role = Column(Enum(UserRole, native_enum=False, length=50), default=UserRole.cliente, nullable=False) 
    position = Column(String(50), nullable=True)
    level = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationships / Relaciones
    routines = relationship("Routine", back_populates="user")
    metrics = relationship("Metric", back_populates="user")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")


class Goal(Base):
    """CU-02: Configurar Metas. para el Agente de IA (CU-05)."""

    __tablename__ = "goals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    objective = Column(String(255), nullable=False)  # ej. "Mejorar tiro de 3 puntos"
    target_days_per_week = Column(Integer, nullable=False, default=3)
    available_minutes = Column(Integer, nullable=True)  # tiempo disponible por sesion
    is_active = Column(Boolean, default=True, nullable=False)  # permite historial de metas
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationships / Relaciones
    user = relationship("User", back_populates="goals")


class Category(Base):
    __tablename__ = "categories"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)  # ej. "Tiro", "Pase", "Pliometria"
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationships / Relaciones
    exercises = relationship("Exercise", back_populates="category")


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    video_url = Column(String(255), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)  # soft delete (sync offline)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationships / Relaciones
    category = relationship("Category", back_populates="exercises")


class Routine(Base):
    __tablename__ = "routines"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    
    type = Column(Enum(RoutineType, native_enum=False, length=50), default=RoutineType.manual, nullable=False)
    status = Column(Enum(RoutineStatus, native_enum=False, length=20), default=RoutineStatus.pending, nullable=False)
    
    scheduled_date = Column(Date, nullable=False, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationships / Relaciones
    user = relationship("User", back_populates="routines")
    routine_exercises = relationship(
        "RoutineExercise", back_populates="routine", cascade="all, delete-orphan"
    )


class RoutineExercise(Base):
    """Tabla puente Routine <-> Exercise, con sets/reps/esfuerzo especificos."""

    __tablename__ = "routine_exercises"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    routine_id = Column(String(36), ForeignKey("routines.id"), nullable=False, index=True)
    exercise_id = Column(String(36), ForeignKey("exercises.id"), nullable=False, index=True)
    sets = Column(Integer, default=1, nullable=False)
    reps = Column(Integer, default=10, nullable=False)
    effort_rating = Column(Integer, nullable=True)  # escala 1-10, post-ejecucion (CU-07)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationships / Relaciones
    routine = relationship("Routine", back_populates="routine_exercises")
    exercise = relationship("Exercise")


class Metric(Base):
    """CU-08: Ingresar Resultado y Proyectar Progreso."""

    __tablename__ = "metrics"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    metric_type = Column(String(100), nullable=False)  # ej. "Free Throw(tiro libre) %", "Peso"
    value = Column(Float, nullable=False)
    recorded_date = Column(Date, nullable=False, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationships / Relaciones
    user = relationship("User", back_populates="metrics")