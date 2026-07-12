from datetime import date, datetime
from typing import Union


def parse_date(date_val: Union[date, str]) -> date:
    """Parse a date value (either date object or ISO string YYYY-MM-DD) into a date object."""
    if isinstance(date_val, date) and not isinstance(date_val, datetime):
        return date_val
    if isinstance(date_val, datetime):
        return date_val.date()
    if isinstance(date_val, str):
        # Strip any time/zone part if present
        date_str = date_val.split("T")[0]
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    raise ValueError(f"Invalid date value type: {type(date_val)}")


def is_date_expired(expiry_date: Union[date, str]) -> bool:
    """Check if the given expiry date is in the past compared to today."""
    parsed_expiry = parse_date(expiry_date)
    return parsed_expiry < date.today()
