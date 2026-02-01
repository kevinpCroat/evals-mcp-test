"""
Date range utilities for calculating business days and working with date ranges.
"""

from datetime import datetime, timedelta
from typing import List


def is_business_day(date: datetime) -> bool:
    """
    Check if a given date is a business day (Monday-Friday).

    Args:
        date: The date to check

    Returns:
        True if the date is a business day, False otherwise
    """
    # Monday is 0, Sunday is 6
    return date.weekday() < 5


def get_date_range(start_date: datetime, end_date: datetime) -> List[datetime]:
    """
    Generate a list of dates between start_date and end_date (inclusive).

    Args:
        start_date: The start date
        end_date: The end date

    Returns:
        List of datetime objects for each day in the range
    """
    if start_date > end_date:
        raise ValueError("start_date must be before or equal to end_date")

    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)

    return dates


def count_weekends(start_date: datetime, end_date: datetime) -> int:
    """
    Count the number of weekend days (Saturday and Sunday) in a date range.

    Args:
        start_date: The start date
        end_date: The end date

    Returns:
        Number of weekend days in the range
    """
    if start_date > end_date:
        raise ValueError("start_date must be before or equal to end_date")

    weekend_count = 0
    current_date = start_date

    while current_date <= end_date:
        # Saturday is 5, Sunday is 6
        if current_date.weekday() >= 5:
            weekend_count += 1
        current_date += timedelta(days=1)

    return weekend_count


def get_business_days(start_date: datetime, end_date: datetime) -> int:
    """
    Calculate the number of business days between two dates (inclusive).

    A business day is defined as Monday through Friday.

    Args:
        start_date: The start date
        end_date: The end date

    Returns:
        Number of business days in the range (inclusive)

    Raises:
        ValueError: If start_date is after end_date
    """
    if start_date > end_date:
        raise ValueError("start_date must be before or equal to end_date")

    # Simple approach: iterate through each day and count business days
    business_days = 0
    current_date = start_date

    while current_date <= end_date:
        if is_business_day(current_date):
            business_days += 1
        current_date += timedelta(days=1)

    return business_days
