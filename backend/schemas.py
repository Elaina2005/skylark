from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class FoodItemResponse(BaseModel):
    food: str
    category: str
    estimated_freshness_hours: float


class FoodRequest(BaseModel):
    food: str = Field(..., example="Biryani")
    quantity: str = Field("10 portions", example="20 portions")
    cooked_time: str = Field(..., example="14:30")
    cooked_date: str | None = Field(None, example="2026-08-27")
    storage_condition: str = Field("Room Temperature", example="Room Temperature")  # Room Temperature, Refrigerated, Hot/Heated
    location: str | None = Field("Central Market, Chennai", example="Anna Nagar, Chennai")
    latitude: float | None = Field(13.0827, example=13.0827)
    longitude: float | None = Field(80.2707, example=80.2707)


class PredictionResponse(BaseModel):
    food: str
    category: str = "General"
    quantity: str = "10 portions"
    cooked_date: str | None = None
    cooked_time: str
    elapsed_hours: float = 0.0
    estimated_freshness_duration: float = 4.0
    base_freshness_hours: float | None = None
    storage_condition: str = "Room Temperature"
    location: str | None = None
    latitude: float = 13.0827
    longitude: float = 80.2707
    freshness: float
    remaining_hours: float
    priority: str
    status: str = "AVAILABLE"
    recommendation: str = "Donation can be arranged."
    ngo: str
    distance_km: float | None = None

    disclaimer: str = (
        "Important: This is an estimated freshness/urgency score for this project based on food type, elapsed time "
        "and storage information. It is not a guarantee of food safety. Food should be handled, stored and inspected "
        "according to applicable food-safety requirements."
    )



class MatchResponse(BaseModel):
    recommended_ngo: str
    freshness: float
    remaining_hours: float
    priority: str
    status: str = "AVAILABLE"
    distance_km: float | None = None


class UserCreate(BaseModel):
    username: str = Field(..., example="donor123")
    email: EmailStr = Field(..., example="donor@example.com")
    password: str = Field(..., min_length=6, example="strongpassword")
    phone: str | None = Field(None, example="+919876543210")
    role: str = Field("donor", example="donor")  # "donor", "ngo", "admin"
    ngo_id: int | None = Field(None, example=1)


class UserLogin(BaseModel):
    username: str = Field(..., example="donor123")
    password: str = Field(..., example="strongpassword")


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    phone: str | None
    role: str = "donor"
    is_admin: bool
    ngo_id: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class NGOCreate(BaseModel):
    name: str = Field(..., example="Hope Trust")
    city: str | None = Field(None, example="Bangalore")
    address: str | None = Field(None, example="12 MG Road, Bangalore")
    contact_email: EmailStr | None = Field(None, example="contact@hopetrust.org")
    phone: str | None = Field(None, example="+919876543211")
    latitude: float | None = Field(13.0827, example=13.0827)
    longitude: float | None = Field(80.2707, example=80.2707)
    available: bool = Field(True, example=True)


class NGOResponse(NGOCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class VolunteerCreate(BaseModel):
    name: str = Field(..., example="Rahul")
    phone: str = Field(..., example="+919876543210")
    email: EmailStr | None = Field(None, example="rahul@example.com")
    ngo_id: int | None = Field(None, example=1)


class VolunteerResponse(VolunteerCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class DonationCreate(FoodRequest):
    donor_name: str | None = Field(None, example="Maya")
    donor_email: EmailStr | None = Field(None, example="maya@example.com")
    donor_phone: str | None = Field(None, example="+919876543212")


class DonationStatusHistoryResponse(BaseModel):
    id: int
    donation_id: int
    status: str
    updated_by: str
    note: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class DonationResponse(PredictionResponse):
    id: int
    user_id: int | None = None
    ngo_id: int | None = None
    donor_name: str | None
    donor_email: EmailStr | None
    donor_phone: str | None
    created_at: datetime
    updated_at: datetime | None = None
    status_history: list[DonationStatusHistoryResponse] = []

    class Config:
        from_attributes = True


class StatusUpdateRequest(BaseModel):
    status: str = Field(..., example="ACCEPTED")
    note: str | None = Field(None, example="Pickup scheduled by admin")


class AdminStats(BaseModel):
    total_donations: int
    available_count: int
    accepted_count: int
    pickup_scheduled_count: int
    picked_up_count: int
    in_transit_count: int
    delivered_count: int
    completed_count: int
    cancelled_count: int
    fresh_count: int
    medium_count: int
    urgent_count: int
    expired_count: int


