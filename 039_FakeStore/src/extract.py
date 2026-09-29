import logging
import pandas as pd
import requests

BASE_URL = "https://fakestoreapi.com"

# Set up logger for extraction operations
logger = logging.getLogger(__name__)


def fetch_products():
    """Fetches product data from the REST API safely with timeouts and error handling.

    Returns:
        pd.DataFrame: A DataFrame containing product data, or empty DataFrame
        on failure.
    """
    url = f"{BASE_URL}/products"
    try:
        logger.info(f"Extracting products from {url}...")
        # Timeout set to 10 seconds to prevent hanging
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        logger.info(f"Successfully fetched {len(data)} product records.")
        return pd.DataFrame(data)

    except requests.exceptions.Timeout:
        logger.error(
            "Request timed out while trying to reach Fake Store API (products)."
        )
        raise
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred during products extraction: {http_err}")
        raise
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Network error during products extraction: {req_err}")
        raise
    except ValueError as json_err:
        logger.error(f"Failed to parse JSON response for products: {json_err}")
        raise


def extract_users():
    """Fetches user data from the REST API safely with timeouts and error handling.

    Returns:
        pd.DataFrame: A DataFrame containing user data, or empty DataFrame on
        failure.
    """
    url = f"{BASE_URL}/users"
    try:
        logger.info(f"Extracting users from {url}...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()
        logger.info(f"Successfully fetched {len(data)} user records.")
        return pd.DataFrame(data)

    except requests.exceptions.Timeout:
        logger.error(
            "Request timed out while trying to reach Fake Store API (users)."
        )
        raise
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred during users extraction: {http_err}")
        raise
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Network error during users extraction: {req_err}")
        raise
    except ValueError as json_err:
        logger.error(f"Failed to parse JSON response for users: {json_err}")
        raise