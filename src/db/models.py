"""SQLAlchemy ORM models for the Deep Prospecting Engine."""

from sqlalchemy import Column, String, Text, DateTime, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.sql import func
import enum


class Base(DeclarativeBase):
    pass


class RunStatusEnum(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Project(Base):
    __tablename__ = "projects"

    project_id = Column(String(12), primary_key=True)
    client_name = Column(String(200), nullable=False)
    notes = Column(Text, default="")
    tags = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    runs = relationship("Run", back_populates="project", order_by="Run.created_at")
    saved_plays = relationship("SavedPlay", back_populates="project")


class Run(Base):
    __tablename__ = "runs"

    run_id = Column(String(12), primary_key=True)
    project_id = Column(String(12), ForeignKey("projects.project_id"), nullable=True)
    client_name = Column(String(200), nullable=False)
    status = Column(String(20), default="pending")
    current_step = Column(String(100), default="initialized")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    plays_count = Column(Integer, default=0)
    error = Column(Text, nullable=True)

    # Input fields
    past_sales_history = Column(Text, default="")
    base_research_prompt = Column(Text, default="")

    # Result fields stored as JSON
    deep_research_report = Column(Text, default="")
    client_vertical = Column(String(100), default="")
    client_domain = Column(String(100), default="")
    digital_maturity_summary = Column(Text, default="")
    competitor_proofs = Column(JSON, default=list)
    refined_plays = Column(JSON, default=list)
    one_pagers = Column(JSON, default=dict)
    strategic_plan = Column(Text, default="")
    errors = Column(JSON, default=list)

    project = relationship("Project", back_populates="runs")


class SavedPlay(Base):
    __tablename__ = "saved_plays"

    play_id = Column(String(12), primary_key=True)
    project_id = Column(String(12), ForeignKey("projects.project_id"), nullable=False)
    iteration_id = Column(String(12), nullable=False)  # run_id
    play_data = Column(JSON, nullable=False)
    notes = Column(Text, default="")
    saved_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="saved_plays")
