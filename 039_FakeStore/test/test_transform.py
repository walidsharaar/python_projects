import pandas as pd
import pytest
from src.transform import transform_products, transform_users


@pytest.fixture
def sample_raw_products_df():
    """Fixture to provide mock raw API JSON data as a DataFrame."""
    return pd.DataFrame(
        [
            {
                "id": 1,
                "title": "Fjallraven Backpack",
                "price": 109.95,
                "description": "Your everyday bag",
                "category": "men's clothing",
                "rating": {"rate": 3.9, "count": 120},
            },
            {
                "id": 2,
                "title": "Casual Premium Slim Fit T-Shirt",
                "price": "22.3",  # String price to test type conversion
                "description": "Slim-fitting style",
                "category": "men's clothing",
                "rating": None,  # Malformed rating to test resilience
            },
        ]
    )


def test_transform_products_column_mapping_and_unnesting(
    sample_raw_products_df,
):
    """Verifies that rating dictionaries are correctly unnested and columns renamed."""
    df = transform_products(sample_raw_products_df)

    # Check that old columns are renamed/dropped and new ones exist
    assert "product_id" in df.columns
    assert "rating_rate" in df.columns
    assert "rating_count" in df.columns
    assert "rating" not in df.columns

    # Verify first record unnested values
    assert df.loc[df["product_id"] == 1, "rating_rate"].iloc[0] == 3.9
    assert df.loc[df["product_id"] == 1, "rating_count"].iloc[0] == 120


def test_transform_products_handles_missing_nested_dict(sample_raw_products_df):
    """Verifies that records with missing/None rating dicts do not crash transformation."""
    df = transform_products(sample_raw_products_df)

    # Record #2 had rating = None; rating_rate should be NaN/None
    record_2_rate = df.loc[df["product_id"] == 2, "rating_rate"].iloc[0]
    assert pd.isna(record_2_rate)


def test_transform_products_type_coercion(sample_raw_products_df):
    """Verifies that string prices are converted to numeric floats."""
    df = transform_products(sample_raw_products_df)

    assert pd.api.types.is_float_dtype(df["product_price"])
    assert df.loc[df["product_id"] == 2, "product_price"].iloc[0] == 22.30