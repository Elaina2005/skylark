import math
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

DATA_PATH = Path(__file__).resolve().parents[1] / "dataset" / "food_freshness.csv"
FALLBACK_DATA_PATH = Path(__file__).resolve().parents[1] / "dataset" / "food_safe_hours.csv"

DEFAULT_SAFE_HOURS = 4.0
DEFAULT_DISCLAIMER = (
    "Important: This is an estimated freshness/urgency score for this project based on food type, elapsed time "
    "and storage information. It is not a guarantee of food safety. Food should be handled, stored and inspected "
    "according to applicable food-safety requirements."
)

NGOS = [
    "Smile Foundation",
    "Food Bank",
    "Helping Hands",
    "Akshaya Patra",
    "Hope Trust",
]


def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates distance in kilometers between two latitude/longitude points using the Haversine formula.
    """
    if lat1 == lat2 and lon1 == lon2:
        return 0.0
    R = 6371.0  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)


def _load_food_dataset() -> dict[str, dict]:
    dataset = {}
    path_to_use = DATA_PATH if DATA_PATH.exists() else FALLBACK_DATA_PATH

    if not path_to_use.exists():
        return {}

    try:
        df = pd.read_csv(path_to_use)
        for _, row in df.iterrows():
            food_name = str(row.get("Food", "")).strip()
            if not food_name:
                continue
            food_key = food_name.lower()
            category = str(row.get("Category", "General")).strip()
            
            # Handle column name variations
            if "EstimatedFreshnessHours" in row:
                hours = float(row["EstimatedFreshnessHours"])
            elif "SafeHours" in row:
                hours = float(row["SafeHours"])
            else:
                hours = DEFAULT_SAFE_HOURS

            dataset[food_key] = {
                "food": food_name,
                "category": category,
                "estimated_freshness_hours": hours,
            }
        return dataset
    except Exception:
        return {}


FOOD_DATASET = _load_food_dataset()


def get_food_list() -> list[dict]:
    """
    Returns the complete list of available foods with Category and EstimatedFreshnessHours.
    """
    return [
        {
            "food": item["food"],
            "category": item["category"],
            "estimated_freshness_hours": item["estimated_freshness_hours"],
        }
        for item in FOOD_DATASET.values()
    ]


def predict(
    food: str,
    cooked_time: str,
    cooked_date: str | None = None,
    storage_condition: str = "Room Temperature",
) -> dict:
    """
    Calculates estimated freshness percentage, remaining duration, priority,
    recommendation, and matches recommended NGO based on food freshness dataset & storage condition.
    """
    if not food or not food.strip():
        raise ValueError("Food item selection is required")
    if not cooked_time or not cooked_time.strip():
        raise ValueError("Cooking time is required")

    food_key = food.strip().lower()

    if food_key not in FOOD_DATASET:
        # Check partial match
        matched_item = None
        for k, v in FOOD_DATASET.items():
            if k in food_key or food_key in k:
                matched_item = v
                break
        if not matched_item:
            raise ValueError(
                "This food is not currently available in our freshness dataset. "
                "Please select another food or contact the administrator."
            )
        food_meta = matched_item
    else:
        food_meta = FOOD_DATASET[food_key]

    food_clean = food_meta["food"]
    category = food_meta["category"]
    base_duration = food_meta["estimated_freshness_hours"]

    # Storage condition multiplier
    storage_clean = storage_condition.strip() if storage_condition else "Room Temperature"
    if storage_clean == "Refrigerated":
        storage_multiplier = 1.5
    elif storage_clean in ("Hot/Heated", "Heated"):
        storage_multiplier = 1.2
    else:
        storage_multiplier = 1.0
        storage_clean = "Room Temperature"

    adjusted_duration = round(base_duration * storage_multiplier, 2)

    now = datetime.now()

    # Determine date
    if cooked_date and cooked_date.strip():
        try:
            date_obj = datetime.strptime(cooked_date.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Cooking date must be in YYYY-MM-DD format")
    else:
        date_obj = now.date()

    # Parse time
    parsed_time = None
    for fmt in ("%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M:%S %p"):
        try:
            parsed_time = datetime.strptime(cooked_time.strip(), fmt).time()
            break
        except ValueError:
            pass

    if parsed_time is None:
        raise ValueError("Cooking time must be in HH:MM format (e.g. 14:30)")

    cooked_datetime = datetime.combine(date_obj, parsed_time)

    # Check future cooking time
    if cooked_datetime > now:
        raise ValueError("Cooking date and time cannot be in the future")

    # Calculate elapsed hours
    elapsed_hours = round((now - cooked_datetime).total_seconds() / 3600.0, 2)
    remaining_hours = max(0.0, round(adjusted_duration - elapsed_hours, 2))

    if remaining_hours <= 0:
        freshness = 0.0
        priority = "High"
        status = "Expired"
        recommendation = "Estimated freshness duration exceeded. Do not offer for donation without appropriate food-safety verification."
    else:
        freshness = round(max(0.0, min(100.0, ((adjusted_duration - elapsed_hours) / adjusted_duration) * 100)), 2)
        if freshness >= 70.0:
            priority = "Low"
            status = "AVAILABLE"
            recommendation = "Food is currently fresh. Donation can be arranged."
        elif freshness >= 40.0:
            priority = "Medium"
            status = "AVAILABLE"
            recommendation = "Donation recommended soon."
        else:
            priority = "High"
            status = "AVAILABLE"
            recommendation = "Urgent donation required."

    # NGO matching logic
    if priority == "High" or status == "Expired":
        ngo = NGOS[0]  # Smile Foundation
    elif priority == "Medium":
        ngo = NGOS[2]  # Helping Hands
    else:
        ngo = NGOS[1]  # Food Bank

    return {
        "food": food_clean,
        "category": category,
        "cooked_date": str(date_obj),
        "cooked_time": cooked_time.strip(),
        "elapsed_hours": elapsed_hours,
        "estimated_freshness_duration": adjusted_duration,
        "base_freshness_hours": base_duration,
        "storage_condition": storage_clean,
        "freshness": freshness,
        "remaining_hours": remaining_hours,
        "priority": priority,
        "status": status,
        "recommendation": recommendation,
        "ngo": ngo,
        "disclaimer": DEFAULT_DISCLAIMER,
    }