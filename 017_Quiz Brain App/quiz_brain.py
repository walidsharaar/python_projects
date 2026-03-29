from question import Question


class QuizBrain:
    """
    Manages the logic and flow of the multiple-choice quiz.
    Handles question progression, user input, answer checking, and scoring.
    """

    OPTIONS = ["A", "B", "C", "D"]

    def __init__(self, q_list: list[Question]):
        self.question_number = 0
        self.score = 0
        self.question_list = q_list

    def still_has_questions(self) -> bool:
        """Returns True if there are more questions remaining."""
        return self.question_number < len(self.question_list)

    def next_question(self):
        """Displays the next question, collects input, and checks the answer."""
        current_question = self.question_list[self.question_number]
        self.question_number += 1

        print(f"\nQ.{self.question_number}: {current_question.text}")

        choice_map = {}
        for letter, choice in zip(self.OPTIONS, current_question.choices):
            choice_map[letter] = choice
            print(f"   {letter}) {choice}")

        user_choice = self._get_valid_input()
        self._check_answer(choice_map[user_choice], current_question.correct_answer)

    def _get_valid_input(self) -> str:
        """Loops until the user enters a valid letter (A–D), with clear feedback."""
        while True:
            user_choice = input("Your answer (A, B, C, or D): ").strip().upper()
            if user_choice in self.OPTIONS:
                return user_choice
            print(f"   ❗ Invalid input '{user_choice}'. Please enter A, B, C, or D.")

    def _check_answer(self, selected: str, correct: str):
        """Compares the selected answer to the correct one and updates the score."""
        if selected == correct:
            self.score += 1
            print("CORRECT!")
        else:
            print(f"WRONG. The correct answer was: {correct}")

        print(f"Score: {self.score}/{self.question_number}")
        print("-" * 40)

    def get_final_report(self) -> str:
        """
        Returns a formatted summary string.
        QuizBrain owns its report — callers don't need to reach into .score directly.
        """
        total = len(self.question_list)
        pct = (self.score / total) * 100 if total else 0

        if pct >= 80:
            grade = "Excellent!"
        elif pct >= 50:
            grade = "Keep practicing!"
        else:
            grade = "Don't give up!"

        return (
            f"\n{'='*40}\n"
            f"  QUIZ COMPLETE\n"
            f"  Final Score: {self.score}/{total} ({pct:.0f}%)\n"
            f"  {grade}\n"
            f"{'='*40}"
        )
