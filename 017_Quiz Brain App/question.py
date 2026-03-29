import html
import random


class Question:
    """Models a multiple-choice question with exactly 4 shuffled choices."""

    def __init__(self, q_text: str, q_answer: str, q_incorrects: list[str]):
        if len(q_incorrects) != 3:
            raise ValueError(
                f"Expected 3 incorrect answers, got {len(q_incorrects)}"
            )

        self.text = html.unescape(q_text)
        self.correct_answer = html.unescape(q_answer)

        self.choices = [html.unescape(ans) for ans in q_incorrects]
        self.choices.append(self.correct_answer)
        random.shuffle(self.choices)

    def get_correct_letter(self) -> str:
        """Returns the letter (A-D) that maps to the correct answer."""
        options = ["A", "B", "C", "D"]
        return options[self.choices.index(self.correct_answer)]

    def __repr__(self) -> str:
        return f"Question(text={self.text[:40]!r}...)"
