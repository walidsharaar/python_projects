# bet_manager.py
# Owns all betting logic: prompting the user, validating input, and
# determining win/loss. Keeping this separate means the race loop


from canvas import Canvas
from config import RACER_COLORS


class BetManager:
    """
    Handles user bet: prompting, validating, and evaluating the outcome.
    BUG FIX 3: Validates input — guards against None (Cancel) and invalid colors.
    """

    def __init__(self, canvas: Canvas):
        self.canvas = canvas
        self.user_bet: str | None = None

    def prompt_bet(self) -> bool:
        """
        Asks the user to place a bet. Re-prompts on invalid input.
        Returns True if a valid bet was placed, False if the user cancelled.
        """
        valid_colors = ", ".join(RACER_COLORS)

        while True:
            raw = self.canvas.get_text_input(
                title="🐢 Place Your Bet!",
                prompt=f"Which turtle will win?\nEnter a color: {valid_colors}"
            )

            # User pressed Cancel
            if raw is None:
                return False

            bet = raw.strip().lower()

            if bet in RACER_COLORS:
                self.user_bet = bet
                return True

            # BUG FIX 3: Inform the user and re-prompt instead of silently accepting
            self.canvas.get_text_input(
                title="Invalid Color",
                prompt=f"'{raw}' is not valid.\nValid options: {valid_colors}\n\nPress OK to try again."
            )

    def evaluate(self, winning_color: str) -> str:
        """Returns the result message based on the winning color vs the bet."""
        if self.user_bet == winning_color:
            return f"🎉 You WON! The {winning_color} turtle wins!"
        return f" You lost. The {winning_color} turtle wins!"
