from datetime import datetime, timezone
from typing import Optional


def datetime_to_timestamp(dt: datetime) -> Optional[int]:
    """Datetime to timestamp in milliseconds."""
    return int(datetime.strftime(dt, '%s')) * 1000 if dt else None


def timestamp_to_datetime(timestamp_m: int) -> datetime:
    """Timestamp to datetime in milliseconds."""
    return datetime.fromtimestamp(timestamp_m/1000, timezone.utc)
