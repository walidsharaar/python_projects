"""
Shared settings for the simulated source systems.

- ONE fixed reference date: every run produces exactly the same data, today and in a year.
- History from December 2022: 2023, 2024 and 2025 are complete years, so every year
  from 2024 on has a complete prior year to compare with.
- A shared "market" of shops: some shops buy from both companies. Both generators take
  their customers from this list, so neither source system has to read the other one.
"""
import random
from datetime import date, timedelta

from faker import Faker

REFERENCE_DATE = date(2026, 11, 20)   # "today" of the simulation = Datenstand
HISTORY_START = date(2022, 12, 1)     # first order / invoice date

MARKET_SEED = 99
MARKET_SIZE = 280


def market() -> list[dict]:
    """All shops in the market: name, city, postcode. Same list on every run."""
    fake = Faker("de_DE")
    fake.seed_instance(MARKET_SEED)
    return [{"name": fake.company(), "city": fake.city(), "zipcode": fake.postcode()}
            for _ in range(MARKET_SIZE)]


def years_since_start(d: date) -> float:
    return (d - HISTORY_START).days / 365.25


def price_factor(d: date) -> float:
    """List prices rise by 3 % on 1 January of every year (2023 = 1.00)."""
    return 1.03 ** (d.year - 2023)


def weighted_dates(k: int, season: list[float], growth_per_year: float) -> list[date]:
    """
    k business dates between HISTORY_START and REFERENCE_DATE, drawn with
    - a seasonal pattern (one weight per month),
    - steady growth per year,
    - few orders on weekends.
    Uses the module-level random generator, so the caller's seed decides the result.
    """
    weekday_weight = (1.0, 1.0, 1.0, 1.0, 1.0, 0.15, 0.05)
    days, weights = [], []
    d = HISTORY_START
    while d <= REFERENCE_DATE:
        days.append(d)
        weights.append(season[d.month - 1]
                       * (1 + growth_per_year) ** years_since_start(d)
                       * weekday_weight[d.weekday()])
        d += timedelta(days=1)
    return sorted(random.choices(days, weights=weights, k=k))
