import requests
import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

class WeatherEngine:
    def __init__(self):
        # Professional practice: Get key from environment variable
        self.api_key = os.getenv("VISUAL_CROSSING_KEY")
        self.base_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"

    def fetch_weather(self, city: str = "Hamburg, Germany"):
        if not self.api_key:
            return {"error": "API Key missing! Create a .env file with VISUAL_CROSSING_KEY=your_key"}
        
        try:
            # We use 'metric' for Celsius. Change to 'us' for Fahrenheit.
            url = f"{self.base_url}{city}?unitGroup=metric&key={self.api_key}&contentType=json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError:
            return {"error": f"City '{city}' not found. Please check the spelling."}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {e}"}