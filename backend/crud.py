from datetime import datetime
from sqlalchemy.orm import Session

import ai
import models
import schemas


def get_users(db: Session) -> list[models.User]:
    return db.query(models.User).order_by(models.User.created_at.desc()).all()


def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_username(db: Session, username: str) -> models.User | None:
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(db: Session, user: schemas.UserCreate, hashed_password: str, is_admin: bool = False) -> models.User:
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        phone=user.phone,
        role=user.role or ("admin" if is_admin else "donor"),
        is_admin=is_admin or (user.role == "admin"),
        ngo_id=user.ngo_id,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_ngos(db: Session) -> list[models.NGO]:
    return db.query(models.NGO).order_by(models.NGO.name).all()


def get_ngo_by_name(db: Session, name: str) -> models.NGO | None:
    return db.query(models.NGO).filter(models.NGO.name == name).first()


def get_ngo_by_id(db: Session, ngo_id: int) -> models.NGO | None:
    return db.query(models.NGO).filter(models.NGO.id == ngo_id).first()


def create_ngo(db: Session, ngo: schemas.NGOCreate) -> models.NGO:
    db_ngo = models.NGO(
        name=ngo.name,
        city=ngo.city,
        address=ngo.address,
        contact_email=ngo.contact_email,
        phone=ngo.phone,
        latitude=ngo.latitude or 13.0827,
        longitude=ngo.longitude or 80.2707,
        available=ngo.available,
    )
    db.add(db_ngo)
    db.commit()
    db.refresh(db_ngo)
    return db_ngo


def update_ngo(db: Session, ngo_id: int, ngo_data: schemas.NGOCreate) -> models.NGO:
    ngo = get_ngo_by_id(db, ngo_id)
    if ngo is None:
        raise ValueError("NGO not found")
    ngo.name = ngo_data.name
    ngo.city = ngo_data.city
    ngo.address = ngo_data.address
    ngo.contact_email = ngo_data.contact_email
    ngo.phone = ngo_data.phone
    if ngo_data.latitude:
        ngo.latitude = ngo_data.latitude
    if ngo_data.longitude:
        ngo.longitude = ngo_data.longitude
    ngo.available = ngo_data.available
    db.commit()
    db.refresh(ngo)
    return ngo


def delete_ngo(db: Session, ngo_id: int) -> None:
    ngo = get_ngo_by_id(db, ngo_id)
    if ngo is None:
        raise ValueError("NGO not found")
    db.delete(ngo)
    db.commit()


def get_volunteers(db: Session) -> list[models.Volunteer]:
    return db.query(models.Volunteer).order_by(models.Volunteer.created_at.desc()).all()


def get_volunteer_by_id(db: Session, volunteer_id: int) -> models.Volunteer | None:
    return db.query(models.Volunteer).filter(models.Volunteer.id == volunteer_id).first()


def create_volunteer(db: Session, volunteer: schemas.VolunteerCreate) -> models.Volunteer:
    db_volunteer = models.Volunteer(
        name=volunteer.name,
        phone=volunteer.phone,
        email=volunteer.email,
        ngo_id=volunteer.ngo_id,
    )
    db.add(db_volunteer)
    db.commit()
    db.refresh(db_volunteer)
    return db_volunteer


def update_volunteer(db: Session, volunteer_id: int, volunteer_data: schemas.VolunteerCreate) -> models.Volunteer:
    volunteer = get_volunteer_by_id(db, volunteer_id)
    if volunteer is None:
        raise ValueError("Volunteer not found")
    volunteer.name = volunteer_data.name
    volunteer.phone = volunteer_data.phone
    volunteer.email = volunteer_data.email
    volunteer.ngo_id = volunteer_data.ngo_id
    db.commit()
    db.refresh(volunteer)
    return volunteer


def delete_volunteer(db: Session, volunteer_id: int) -> None:
    volunteer = get_volunteer_by_id(db, volunteer_id)
    if volunteer is None:
        raise ValueError("Volunteer not found")
    db.delete(volunteer)
    db.commit()


def get_donations(db: Session) -> list[models.Donation]:
    return db.query(models.Donation).order_by(models.Donation.created_at.desc()).all()


def get_donation_by_id(db: Session, donation_id: int) -> models.Donation | None:
    return db.query(models.Donation).filter(models.Donation.id == donation_id).first()


def get_filtered_donations(
    db: Session,
    food: str | None = None,
    ngo: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    start_dt: datetime | None = None,
    end_dt: datetime | None = None,
) -> list[models.Donation]:
    q = db.query(models.Donation)
    if food:
        q = q.filter(models.Donation.food.ilike(f"%{food}%"))
    if ngo:
        q = q.filter(models.Donation.ngo.ilike(f"%{ngo}%"))
    if priority:
        q = q.filter(models.Donation.priority.ilike(f"%{priority}%"))
    if status:
        q = q.filter(models.Donation.status == status)
    if start_dt:
        q = q.filter(models.Donation.created_at >= start_dt)
    if end_dt:
        q = q.filter(models.Donation.created_at <= end_dt)
    return q.order_by(models.Donation.created_at.desc()).all()


def get_donations_for_user(
    db: Session,
    donor_email: str,
    user_id: int | None = None,
    food: str | None = None,
    ngo: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    start_dt: datetime | None = None,
    end_dt: datetime | None = None,
) -> list[models.Donation]:
    if user_id:
        q = db.query(models.Donation).filter(
            (models.Donation.user_id == user_id) | (models.Donation.donor_email == donor_email)
        )
    else:
        q = db.query(models.Donation).filter(models.Donation.donor_email == donor_email)

    if food:
        q = q.filter(models.Donation.food.ilike(f"%{food}%"))
    if ngo:
        q = q.filter(models.Donation.ngo.ilike(f"%{ngo}%"))
    if priority:
        q = q.filter(models.Donation.priority == priority)
    if status:
        q = q.filter(models.Donation.status == status)
    if start_dt:
        q = q.filter(models.Donation.created_at >= start_dt)
    if end_dt:
        q = q.filter(models.Donation.created_at <= end_dt)
    return q.order_by(models.Donation.created_at.desc()).all()


def get_nearby_donations(
    db: Session,
    lat: float = 13.0827,
    lon: float = 80.2707,
) -> list[dict]:
    """
    Returns available donations sorted by Haversine distance to given coordinates, then priority urgency.
    """
    donations = db.query(models.Donation).filter(models.Donation.status == "AVAILABLE").all()
    results = []
    for d in donations:
        dist = ai.calculate_distance_km(lat, lon, d.latitude or 13.0827, d.longitude or 80.2707)
        d_dict = {
            "id": d.id,
            "user_id": d.user_id,
            "ngo_id": d.ngo_id,
            "food": d.food,
            "category": getattr(d, "category", "General"),
            "quantity": d.quantity,
            "cooked_time": d.cooked_time,
            "cooked_date": d.cooked_date,
            "elapsed_hours": getattr(d, "elapsed_hours", 0.0),
            "estimated_freshness_duration": getattr(d, "estimated_freshness_hours", 4.0),
            "storage_condition": getattr(d, "storage_condition", "Room Temperature"),
            "location": d.location,
            "latitude": d.latitude,
            "longitude": d.longitude,
            "freshness": d.freshness,
            "remaining_hours": d.remaining_hours,
            "priority": d.priority,
            "recommendation": getattr(d, "recommendation", None),
            "status": d.status,
            "ngo": d.ngo,
            "donor_name": d.donor_name,
            "donor_email": d.donor_email,
            "donor_phone": d.donor_phone,
            "created_at": d.created_at,
            "updated_at": d.updated_at,
            "distance_km": dist,
            "status_history": d.status_history,
        }
        results.append(d_dict)

    # Sort primarily by distance, secondarily by freshness (urgency)
    results.sort(key=lambda x: (x["distance_km"], -x["freshness"]))
    return results


def create_donation(
    db: Session,
    donation: schemas.DonationCreate,
    prediction: dict,
    user_id: int | None = None,
) -> models.Donation:
    db_donation = models.Donation(
        user_id=user_id,
        food=prediction["food"],
        category=prediction.get("category", "General"),
        quantity=donation.quantity or "10 portions",
        cooked_time=donation.cooked_time,
        cooked_date=prediction.get("cooked_date"),
        storage_condition=prediction.get("storage_condition", "Room Temperature"),
        location=donation.location or "Central Market, Chennai",
        latitude=donation.latitude or 13.0827,
        longitude=donation.longitude or 80.2707,
        estimated_freshness_hours=prediction.get("estimated_freshness_duration", 4.0),
        elapsed_hours=prediction.get("elapsed_hours", 0.0),
        freshness=prediction["freshness"],
        remaining_hours=prediction["remaining_hours"],
        priority=prediction["priority"],
        recommendation=prediction.get("recommendation"),
        status=prediction.get("status", "AVAILABLE"),
        ngo=prediction["ngo"],
        donor_name=donation.donor_name,
        donor_email=donation.donor_email,
        donor_phone=donation.donor_phone,
    )
    db.add(db_donation)
    db.commit()
    db.refresh(db_donation)

    # Initial status history record
    initial_history = models.DonationStatusHistory(
        donation_id=db_donation.id,
        status=db_donation.status,
        updated_by="Donor",
        note="Donation added by donor. Available for NGO pickup.",
    )
    db.add(initial_history)
    db.commit()
    db.refresh(db_donation)

    return db_donation



def update_donation_status(
    db: Session,
    donation_id: int,
    new_status: str,
    updated_by: str = "System",
    note: str | None = None,
    ngo_id: int | None = None,
) -> models.Donation:
    donation = get_donation_by_id(db, donation_id)
    if donation is None:
        raise ValueError("Donation record not found")

    donation.status = new_status
    if ngo_id:
        donation.ngo_id = ngo_id

    db.commit()

    # Append to audit history
    history = models.DonationStatusHistory(
        donation_id=donation.id,
        status=new_status,
        updated_by=updated_by,
        note=note or f"Status updated to {new_status}",
    )
    db.add(history)
    db.commit()
    db.refresh(donation)
    return donation


def get_admin_stats(db: Session) -> dict:
    donations = db.query(models.Donation).all()
    total = len(donations)

    return {
        "total_donations": total,
        "available_count": sum(1 for d in donations if d.status == "AVAILABLE"),
        "accepted_count": sum(1 for d in donations if d.status == "ACCEPTED"),
        "pickup_scheduled_count": sum(1 for d in donations if d.status == "PICKUP_SCHEDULED"),
        "picked_up_count": sum(1 for d in donations if d.status == "PICKED_UP"),
        "in_transit_count": sum(1 for d in donations if d.status == "IN_TRANSIT"),
        "delivered_count": sum(1 for d in donations if d.status == "DELIVERED"),
        "completed_count": sum(1 for d in donations if d.status == "COMPLETED"),
        "cancelled_count": sum(1 for d in donations if d.status == "CANCELLED"),
        "fresh_count": sum(1 for d in donations if d.priority == "Low" and d.status != "CANCELLED"),
        "medium_count": sum(1 for d in donations if d.priority == "Medium" and d.status != "CANCELLED"),
        "urgent_count": sum(1 for d in donations if d.priority == "High" and d.status != "CANCELLED"),
        "expired_count": sum(1 for d in donations if d.remaining_hours <= 0 or d.freshness == 0.0),
    }


def initialize_default_ngos(db: Session, default_names: list[str]) -> None:
    coords = [
        (13.0827, 80.2707, "Chennai Central"),
        (13.0418, 80.2341, "T. Nagar, Chennai"),
        (12.9716, 77.5946, "MG Road, Bangalore"),
        (13.0850, 80.2100, "Anna Nagar, Chennai"),
        (13.0067, 80.2571, "Adyar, Chennai"),
    ]
    for idx, name in enumerate(default_names):
        if not get_ngo_by_name(db, name):
            c = coords[idx % len(coords)]
            create_ngo(
                db,
                schemas.NGOCreate(
                    name=name,
                    city="Chennai" if "Chennai" in c[2] else "Bangalore",
                    address=c[2],
                    contact_email=f"contact@{name.lower().replace(' ', '')}.org",
                    phone=f"+91 98765 4321{idx}",
                    latitude=c[0],
                    longitude=c[1],
                    available=True,
                ),
            )


def initialize_default_admin(db: Session, username: str, email: str, password: str) -> None:
    if get_user_by_username(db, username) or get_user_by_email(db, email):
        return
    from security import get_password_hash

    hashed = get_password_hash(password)
    db_user = models.User(
        username=username,
        email=email,
        hashed_password=hashed,
        phone="+91 98765 00000",
        role="admin",
        is_admin=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)


