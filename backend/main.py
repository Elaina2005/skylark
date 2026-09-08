import csv
import io
import os
from datetime import datetime, timedelta, time

from fastapi import Depends, FastAPI, HTTPException, Security, status, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

import ai
import crud
import models
import schemas
import security
from database import Base, engine, SessionLocal, get_db

app = FastAPI(title="AI Food Donation Network")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token", auto_error=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_NGOS = [
    "Smile Foundation",
    "Food Bank",
    "Helping Hands",
    "Akshaya Patra",
    "Hope Trust",
]

DEFAULT_ADMIN = {
    "username": os.getenv("ADMIN_USERNAME", "admin"),
    "email": os.getenv("ADMIN_EMAIL", "admin@example.com"),
    "password": os.getenv("ADMIN_PASSWORD", "admin123"),
}


def authenticate_user(db: Session, username_or_email: str, password: str):
    user = crud.get_user_by_username(db, username_or_email)
    if user is None:
        user = crud.get_user_by_email(db, username_or_email)
    if user is None:
        return None
    if not security.verify_password(password, user.hashed_password):
        return None
    return user


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = security.decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    username: str | None = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = crud.get_user_by_username(db, username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_user_optional(token: str | None = Security(oauth2_scheme), db: Session = Depends(get_db)):
    if token is None:
        return None
    payload = security.decode_access_token(token)
    if payload is None:
        return None
    username: str | None = payload.get("sub")
    if username is None:
        return None
    return crud.get_user_by_username(db, username)


def get_current_admin(current_user: models.User = Depends(get_current_user)):
    if not current_user.is_admin and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user


@app.on_event("startup")
def initialize_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        crud.initialize_default_ngos(db, DEFAULT_NGOS)
        crud.initialize_default_admin(db, DEFAULT_ADMIN["username"], DEFAULT_ADMIN["email"], DEFAULT_ADMIN["password"])
    finally:
        db.close()


@app.get("/", summary="Health check")
def home():
    return {"message": "AI Food Donation & Tracking Network is running"}


@app.post("/token", response_model=schemas.Token)
@app.post("/login", response_model=schemas.Token)
def login_for_access_token(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/users", response_model=schemas.UserResponse, summary="Register a new user")
@app.post("/register", response_model=schemas.UserResponse, summary="Register a new user")
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, user.email) is not None:
        raise HTTPException(status_code=400, detail="Email already registered")
    if crud.get_user_by_username(db, user.username) is not None:
        raise HTTPException(status_code=400, detail="Username already taken")
    hashed_password = security.get_password_hash(user.password)
    return crud.create_user(db, user, hashed_password)


@app.get("/me", response_model=schemas.UserResponse, summary="Get current user")
def read_current_user(current_user: models.User = Depends(get_current_user)):
    return current_user


@app.get("/users", response_model=list[schemas.UserResponse], summary="List registered users")
def list_users(db: Session = Depends(get_db), _: models.User = Depends(get_current_admin)):
    return crud.get_users(db)


@app.get("/ngos", response_model=list[schemas.NGOResponse], summary="List available NGOs")
def list_ngos(db: Session = Depends(get_db)):
    return crud.get_ngos(db)


@app.post("/ngos", response_model=schemas.NGOResponse, summary="Create a new NGO")
def create_ngo(ngo: schemas.NGOCreate, db: Session = Depends(get_db), _: models.User = Depends(get_current_admin)):
    existing = crud.get_ngo_by_name(db, ngo.name)
    if existing:
        raise HTTPException(status_code=400, detail="NGO with this name already exists")
    return crud.create_ngo(db, ngo)


@app.put("/ngos/{ngo_id}", response_model=schemas.NGOResponse, summary="Update an NGO")
def update_ngo(ngo_id: int, ngo_data: schemas.NGOCreate, db: Session = Depends(get_db), _: models.User = Depends(get_current_admin)):
    try:
        return crud.update_ngo(db, ngo_id, ngo_data)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.delete("/ngos/{ngo_id}", status_code=204, summary="Delete an NGO")
def delete_ngo(ngo_id: int, db: Session = Depends(get_db), _: models.User = Depends(get_current_admin)):
    try:
        crud.delete_ngo(db, ngo_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/volunteers", response_model=list[schemas.VolunteerResponse], summary="List volunteers")
def list_volunteers(db: Session = Depends(get_db)):
    return crud.get_volunteers(db)


@app.post("/volunteers", response_model=schemas.VolunteerResponse, summary="Create a volunteer")
def create_volunteer(volunteer: schemas.VolunteerCreate, db: Session = Depends(get_db), _: models.User = Depends(get_current_admin)):
    return crud.create_volunteer(db, volunteer)


@app.put("/volunteers/{volunteer_id}", response_model=schemas.VolunteerResponse, summary="Update a volunteer")
def update_volunteer(volunteer_id: int, volunteer_data: schemas.VolunteerCreate, db: Session = Depends(get_db), _: models.User = Depends(get_current_admin)):
    try:
        return crud.update_volunteer(db, volunteer_id, volunteer_data)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.delete("/volunteers/{volunteer_id}", status_code=204, summary="Delete a volunteer")
def delete_volunteer(volunteer_id: int, db: Session = Depends(get_db), _: models.User = Depends(get_current_admin)):
    try:
        crud.delete_volunteer(db, volunteer_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/foods", response_model=list[schemas.FoodItemResponse], summary="Get list of foods from freshness dataset")
def get_foods():
    return ai.get_food_list()


@app.post("/predict", response_model=schemas.PredictionResponse, summary="Predict freshness and recommended NGO")
def predict(data: schemas.FoodRequest):
    try:
        result = ai.predict(data.food, data.cooked_time, data.cooked_date, data.storage_condition)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    lat = data.latitude or 13.0827
    lon = data.longitude or 80.2707
    dist = ai.calculate_distance_km(lat, lon, 13.0827, 80.2707)

    return {
        **result,
        "quantity": data.quantity or "10 portions",
        "location": data.location or "Central Market, Chennai",
        "latitude": lat,
        "longitude": lon,
        "distance_km": dist,
    }


@app.post("/donate", response_model=schemas.DonationResponse, summary="Save a donation record")
@app.post("/donations", response_model=schemas.DonationResponse, summary="Save a donation record")
def donate(
    data: schemas.DonationCreate,
    db: Session = Depends(get_db),
    current_user: models.User | None = Depends(get_current_user_optional),
):
    try:
        result = ai.predict(data.food, data.cooked_time, data.cooked_date, data.storage_condition)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    user_id = None
    if current_user:
        user_id = current_user.id
        if not data.donor_email:
            data.donor_email = current_user.email
        if not data.donor_name:
            data.donor_name = current_user.username

    donation = crud.create_donation(db, data, result, user_id=user_id)
    return donation



@app.get("/donations", response_model=list[schemas.DonationResponse], summary="List all donations")
def get_donations(
    db: Session = Depends(get_db),
    status: str | None = Query(None),
):
    if status:
        return crud.get_filtered_donations(db, status=status)
    return crud.get_donations(db)


@app.get("/donations/nearby", summary="List available food donations nearby sorted by distance")
def get_nearby_donations(
    lat: float = Query(13.0827),
    lon: float = Query(80.2707),
    db: Session = Depends(get_db),
):
    return crud.get_nearby_donations(db, lat=lat, lon=lon)


@app.get("/donations/{id}", response_model=schemas.DonationResponse, summary="Get donation by ID")
def get_donation(id: int, db: Session = Depends(get_db)):
    donation = crud.get_donation_by_id(db, id)
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    return donation


@app.get("/donations/{id}/tracking", response_model=list[schemas.DonationStatusHistoryResponse], summary="Get status tracking history")
@app.get("/donations/{id}/history", response_model=list[schemas.DonationStatusHistoryResponse], summary="Get status tracking history")
def get_donation_history(id: int, db: Session = Depends(get_db)):
    donation = crud.get_donation_by_id(db, id)
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    return donation.status_history


@app.put("/donations/{id}/status", response_model=schemas.DonationResponse, summary="Update donation status")
def update_donation_status(
    id: int,
    req: schemas.StatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: models.User | None = Depends(get_current_user_optional),
):
    updater = current_user.username if current_user else "Admin"
    try:
        return crud.update_donation_status(db, id, req.status, updated_by=updater, note=req.note)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/donations/{id}/request", response_model=schemas.DonationResponse, summary="NGO requests/accepts a donation")
@app.post("/donations/{id}/accept", response_model=schemas.DonationResponse, summary="NGO requests/accepts a donation")
def accept_donation(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User | None = Depends(get_current_user_optional),
):
    updater = current_user.username if current_user else "NGO"
    ngo_id = current_user.ngo_id if current_user else None
    try:
        return crud.update_donation_status(
            db,
            id,
            "ACCEPTED",
            updated_by=f"NGO: {updater}",
            note="Donation accepted by NGO for pickup.",
            ngo_id=ngo_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/donations/{id}/confirm-receipt", response_model=schemas.DonationResponse, summary="NGO confirms receipt of food donation")
def confirm_receipt(
    id: int,
    db: Session = Depends(get_db),
    current_user: models.User | None = Depends(get_current_user_optional),
):
    updater = current_user.username if current_user else "NGO"
    try:
        return crud.update_donation_status(
            db,
            id,
            "COMPLETED",
            updated_by=f"NGO: {updater}",
            note="Completed - Receipt confirmed by NGO",
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


def parse_date_param(value: str | None) -> datetime | None:
    if value is None or not value.strip():
        return None
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Date must be YYYY-MM-DD")


@app.get("/donations/me", response_model=list[schemas.DonationResponse], summary="List authenticated user's donations")
@app.get("/my-donations", response_model=list[schemas.DonationResponse], summary="List authenticated user's donations")
def get_my_donations(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    food: str | None = Query(None),
    ngo: str | None = Query(None),
    priority: str | None = Query(None),
    status: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
):
    start_dt = parse_date_param(start_date)
    end_dt = parse_date_param(end_date)
    if end_dt is not None:
        end_dt = datetime.combine(end_dt.date(), time.max)
    return crud.get_donations_for_user(
        db,
        current_user.email,
        user_id=current_user.id,
        food=food,
        ngo=ngo,
        priority=priority,
        status=status,
        start_dt=start_dt,
        end_dt=end_dt,
    )


@app.get("/admin/donations", response_model=list[schemas.DonationResponse], summary="Admin list donations with filters")
def admin_get_donations(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
    food: str | None = Query(None),
    ngo: str | None = Query(None),
    priority: str | None = Query(None),
    status: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
):
    start_dt = parse_date_param(start_date)
    end_dt = parse_date_param(end_date)
    if end_dt is not None:
        end_dt = datetime.combine(end_dt.date(), time.max)
    return crud.get_filtered_donations(
        db,
        food=food,
        ngo=ngo,
        priority=priority,
        status=status,
        start_dt=start_dt,
        end_dt=end_dt,
    )


@app.get("/admin/stats", response_model=schemas.AdminStats, summary="Get admin summary statistics")
def admin_get_stats(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
):
    return crud.get_admin_stats(db)


@app.get("/admin/donations/export", summary="Export donations as CSV file")
def admin_export_donations(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
    food: str | None = Query(None),
    ngo: str | None = Query(None),
    priority: str | None = Query(None),
    status: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
):
    start_dt = parse_date_param(start_date)
    end_dt = parse_date_param(end_date)
    if end_dt is not None:
        end_dt = datetime.combine(end_dt.date(), time.max)

    donations = crud.get_filtered_donations(
        db,
        food=food,
        ngo=ngo,
        priority=priority,
        status=status,
        start_dt=start_dt,
        end_dt=end_dt,
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Donation ID",
        "Food",
        "Category",
        "Quantity",
        "Donor",
        "NGO",
        "Cooking Time",
        "Elapsed Hours",
        "Estimated Freshness Duration",
        "Freshness Percentage",
        "Remaining Hours",
        "Storage Condition",
        "Priority",
        "Distance",
        "Status",
        "Created At",
        "Updated At",
    ])

    for d in donations:
        donor = d.donor_name or d.donor_email or "Anonymous"
        created_str = d.created_at.strftime("%Y-%m-%d %H:%M:%S") if d.created_at else ""
        updated_str = d.updated_at.strftime("%Y-%m-%d %H:%M:%S") if d.updated_at else ""
        cooked_info = f"{d.cooked_date or ''} {d.cooked_time}".strip()
        dist = ai.calculate_distance_km(13.0827, 80.2707, d.latitude or 13.0827, d.longitude or 80.2707)
        writer.writerow([
            d.id,
            d.food,
            getattr(d, "category", "General"),
            d.quantity,
            donor,
            d.ngo,
            cooked_info,
            getattr(d, "elapsed_hours", 0.0),
            getattr(d, "estimated_freshness_hours", 4.0),
            d.freshness,
            d.remaining_hours,
            getattr(d, "storage_condition", "Room Temperature"),
            d.priority,
            f"{dist} km",
            d.status,
            created_str,
            updated_str,
        ])


    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=donations.csv"},
    )


@app.post("/match", response_model=schemas.MatchResponse, summary="Match a donation to the best NGO")
def match(data: schemas.FoodRequest):
    try:
        result = ai.predict(data.food, data.cooked_time, data.cooked_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    lat = data.latitude or 13.0827
    lon = data.longitude or 80.2707
    dist = ai.calculate_distance_km(lat, lon, 13.0827, 80.2707)

    return {
        "recommended_ngo": result["ngo"],
        "freshness": result["freshness"],
        "remaining_hours": result["remaining_hours"],
        "priority": result["priority"],
        "status": "AVAILABLE",
        "distance_km": dist,
    }


