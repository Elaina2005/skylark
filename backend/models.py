from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, unique=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    role = Column(String, nullable=False, default="donor")  # "donor", "ngo", "admin"
    is_admin = Column(Boolean, nullable=False, default=False)
    ngo_id = Column(Integer, ForeignKey("ngos.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ngo_rel = relationship("NGO", backref="users")


class NGO(Base):
    __tablename__ = "ngos"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    city = Column(String, nullable=True)
    address = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    latitude = Column(Float, nullable=False, default=13.0827)
    longitude = Column(Float, nullable=False, default=80.2707)
    available = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    volunteers = relationship("Volunteer", back_populates="ngo")


class Volunteer(Base):
    __tablename__ = "volunteers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=True)
    ngo_id = Column(Integer, ForeignKey("ngos.id"), nullable=True)
    ngo = relationship("NGO", back_populates="volunteers")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Donation(Base):
    __tablename__ = "donations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ngo_id = Column(Integer, ForeignKey("ngos.id"), nullable=True)
    food = Column(String, nullable=False)
    category = Column(String, nullable=True, default="General")
    quantity = Column(String, nullable=False, default="10 portions")
    cooked_time = Column(String, nullable=False)
    cooked_date = Column(String, nullable=True)
    storage_condition = Column(String, nullable=True, default="Room Temperature")
    location = Column(String, nullable=True, default="Main City Area")
    latitude = Column(Float, nullable=False, default=13.0827)
    longitude = Column(Float, nullable=False, default=80.2707)
    estimated_freshness_hours = Column(Float, nullable=True, default=4.0)
    elapsed_hours = Column(Float, nullable=True, default=0.0)
    freshness = Column(Float, nullable=False)
    remaining_hours = Column(Float, nullable=False)
    priority = Column(String, nullable=False)
    recommendation = Column(String, nullable=True)
    status = Column(String, nullable=False, default="AVAILABLE")  # AVAILABLE, ACCEPTED, PICKUP_SCHEDULED, PICKED_UP, IN_TRANSIT, DELIVERED, COMPLETED, CANCELLED
    ngo = Column(String, nullable=False)
    donor_name = Column(String, nullable=True)
    donor_email = Column(String, nullable=True)
    donor_phone = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", backref="donations")
    ngo_rel = relationship("NGO", backref="donations")
    status_history = relationship("DonationStatusHistory", back_populates="donation", cascade="all, delete-orphan", order_by="DonationStatusHistory.created_at.asc()")



class DonationStatusHistory(Base):
    __tablename__ = "donation_status_history"

    id = Column(Integer, primary_key=True, index=True)
    donation_id = Column(Integer, ForeignKey("donations.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, nullable=False)
    updated_by = Column(String, nullable=False, default="System")
    note = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    donation = relationship("Donation", back_populates="status_history")


