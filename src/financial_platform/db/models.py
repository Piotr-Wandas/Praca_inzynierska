from __future__ import annotations
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Company(Base):
    __tablename__ = "company"
    __table_args__ = {"schema": "core"}
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    isin: Mapped[str | None] = mapped_column(String(16), unique=True)
    sector: Mapped[str | None] = mapped_column(String(100))

class IndexMembership(Base):
    __tablename__ = "index_membership"
    __table_args__ = (UniqueConstraint("company_id", "index_code", "valid_from", name="uq_index_membership"), {"schema": "core"})
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("core.company.id"), nullable=False)
    index_code: Mapped[str] = mapped_column(String(32), nullable=False, default="WIG20")
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date)
    source: Mapped[str] = mapped_column(String(300), nullable=False)

class IngestionRun(Base):
    __tablename__ = "ingestion_run"
    __table_args__ = {"schema": "metadata"}
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_name: Mapped[str] = mapped_column(String(80), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="started")
    checksum: Mapped[str | None] = mapped_column(String(64))
    details: Mapped[str | None] = mapped_column(Text)

class DailyPrice(Base):
    __tablename__ = "daily_price"
    __table_args__ = (UniqueConstraint("company_id", "trade_date", name="uq_daily_price"), {"schema": "core"})
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("core.company.id"), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    open: Mapped[Decimal] = mapped_column(Numeric(20,6), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(20,6), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(20,6), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(20,6), nullable=False)
    volume: Mapped[Decimal | None] = mapped_column(Numeric(24,2))
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

class FinancialFact(Base):
    __tablename__ = "financial_fact"
    __table_args__ = (UniqueConstraint("company_id", "concept_code", "period_end", "publication_date", name="uq_fin_fact_version"), {"schema": "core"})
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("core.company.id"), nullable=False)
    concept_code: Mapped[str] = mapped_column(String(80), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(24,4), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="PLN")
    period_start: Mapped[date | None] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    publication_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source_label: Mapped[str | None] = mapped_column(String(300))

class MacroObservation(Base):
    __tablename__ = "macro_observation"
    __table_args__ = (UniqueConstraint("series_code", "observation_date", "available_at", name="uq_macro_obs"), {"schema": "core"})
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    series_code: Mapped[str] = mapped_column(String(80), nullable=False)
    observation_date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(20,8), nullable=False)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

class TrainingRun(Base):
    __tablename__ = "training_run"
    __table_args__ = {"schema": "ml"}
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    target: Mapped[str] = mapped_column(String(80), nullable=False)
    git_commit: Mapped[str | None] = mapped_column(String(64))
    dataset_version: Mapped[str] = mapped_column(String(100), nullable=False)
    metrics_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Prediction(Base):
    __tablename__ = "prediction"
    __table_args__ = {"schema": "ml"}
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("core.company.id"), nullable=False)
    target: Mapped[str] = mapped_column(String(80), nullable=False)
    target_period_end: Mapped[date] = mapped_column(Date, nullable=False)
    cutoff_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    predicted_value: Mapped[Decimal] = mapped_column(Numeric(24,4), nullable=False)
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    dataset_version: Mapped[str] = mapped_column(String(100), nullable=False)
