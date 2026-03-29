import sys
import requests
from question import Question


class QuizAPI:
    """
    Encapsulates all API concerns.
    Fetches questions from the Open Trivia Database and returns Question objects.
    Keeping this separate makes it easy to swap or mock in tests.
    """

    BASE_URL = "https://opentdb.com/api.php"

    def __init__(self, amount: int = 10, category: int = 18, q_type: str = "multiple"):
        self.params = {
            "amount": amount,
            "category": category,
            "type": q_type,
        }

    def fetch(self) -> list[Question]:
        """Fetches questions from the API and returns a list of Question objects."""
        try:
            response = requests.get(self.BASE_URL, params=self.params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # HTTP 200 doesn't guarantee success — check the API's own response code
            if data.get("response_code") != 0:
                raise ValueError(f"API returned response_code {data['response_code']}")

            questions = []
            for item in data["results"]:
                try:
                    q = Question(
                        q_text=item["question"],
                        q_answer=item["correct_answer"],
                        q_incorrects=item["incorrect_answers"],
                    )
                    questions.append(q)
                except (ValueError, KeyError) as e:
                    print(f"Skipping malformed question: {e}")

            if not questions:
                raise ValueError("No valid questions were loaded from the API.")

            return questions

        except requests.exceptions.RequestException as e:
            print(f"Network Error: {e}")
            sys.exit(1)
        except ValueError as e:
            print(f"Data Error: {e}")
            sys.exit(1)
