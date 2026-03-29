from quiz_api import QuizAPI
from quiz_brain import QuizBrain


def main():
    print("---  COMPUTER SCIENCE PRO QUIZ  ---")

    # Fetch questions via the API layer
    api = QuizAPI(amount=10, category=18)
    question_bank = api.fetch()

    # Hand the question bank to the quiz controller
    quiz = QuizBrain(question_bank)

    # Run the quiz loop
    while quiz.still_has_questions():
        quiz.next_question()

    # The brain owns its own final report
    print(quiz.get_final_report())


if __name__ == "__main__":
    main()
