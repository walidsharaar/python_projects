import numpy as np
import pandas as pd
import pytest
from src.transform import transform_products


def test_transformed_products_data_quality():
    """Asserts strict business rules and database constraints on transformed data."""
    raw_data = pd.DataFrame(
        [
            {
                "id": 101,
                "title": "Solid Gold Petite Micropave",
                "price": 168.00,
                "description": "Satisfaction Guaranteed",
                "category": "jewelery",
                "rating": {"rate": 4.6, "count": 400},
            }
        ]
    )

    df = transform_products(raw_data)

    # Constraint 1: Primary key must not contain null values
    assert (
        df["product_id"].isnull().sum() == 0
    ), "Primary key product_id contains NULLs"

    # Constraint 2: Primary key must be unique (no duplicate rows)
    assert df["product_id"].is_unique, "Duplicate product_id values found"

    # Constraint 3: Prices must be strictly positive
    assert (
        df["product_price"] > 0
    ).all(), "Found products with non-positive price"

    # Constraint 4: Ratings must be between 0.0 and 5.0
    valid_ratings = df["rating_rate"].dropna()
    assert (
        (valid_ratings >= 0.0) & (valid_ratings <= 5.0)
    ).all(), "Rating rate out of 0.0 - 5.0 range"