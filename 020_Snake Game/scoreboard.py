# scoreboard.py
# Inherits from Turtle to draw score text on the canvas.
# Owns only score state and its own rendering — nothing else.

import turtle
from config import SCORE_X, SCORE_Y, SCORE_FONT, SCORE_ALIGN


class Scoreboard(turtle.Turtle):
    """
    Inherits Turtle for text-drawing capability.
    BUG FIX 5: Positioned at SCORE_Y (260) — safe distance from top wall.
    BUG FIX 3: game_over() is idempotent — safe to call multiple times.
    """

    def __init__(self):
        super().__init__()
        self.score = 0
        self._game_over_shown = False  # BUG FIX 3: guard flag
        self.color("white")
        self.penup()
        self.hideturtle()
        self.goto(SCORE_X, SCORE_Y)
        self._render()

    def _render(self):
        """Clears and redraws the score text."""
        self.clear()
        self.write(f"Score: {self.score}", align=SCORE_ALIGN, font=SCORE_FONT)

    def increase_score(self):
        self.score += 1
        self._render()

    def game_over(self):
        """
        BUG FIX 3: Guard ensures 'GAME OVER' is written exactly once,
        even if both wall and self-collision trigger in the same tick.
        """
        if self._game_over_shown:
            return
        self._game_over_shown = True
        self.goto(0, 0)
        self.write("GAME OVER", align=SCORE_ALIGN, font=SCORE_FONT)
