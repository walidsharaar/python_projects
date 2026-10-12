from unittest.mock import MagicMock, patch
import pandas as pd
import pytest
import requests
from src.extract import fetch_products


@patch("src.extract.requests.get")
def test_fetch_products_success(mock_get):
    """Simulates a successful 200 OK REST API response."""
    # Create mock response object
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"id": 1, "title": "Test Product", "price": 10.0}
    ]
    mock_get.return_value = mock_response

    # Execute extraction
    df = fetch_products()

    # Assertions
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df["title"].iloc[0] == "Test Product"


@patch("src.extract.requests.get")
def test_fetch_products_timeout_handling(mock_get):
    """Simulates a network timeout and verifies the pipeline raises an Exception."""
    mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

    # Assert that the function raises a Timeout exception
    with pytest.raises(requests.exceptions.Timeout):
        fetch_products()