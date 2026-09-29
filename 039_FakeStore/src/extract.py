import pandas as pd
import requests

BASE_URL = "https://fakestoreapi.com"

def fetch_products():
    """
    Fetches product data from the API.

    Returns:
        pd.DataFrame: A DataFrame containing product data.
    """
    url=f'{BASE_URL}/products'
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses
    
    data=response.json()  # Ensure the response is in JSON format
    product_df=pd.DataFrame(data)
    return product_df

def extract_users():
    """
    Fetches user data from the API.

    Returns:
        pd.DataFrame: A DataFrame containing user data.
    """
    url=f'{BASE_URL}/users'
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses
    
    data = response.json()  # Ensure the response is in JSON format
    user_df=pd.DataFrame(data)
    return user_df

