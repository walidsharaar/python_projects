# canvas.py
# Owns the Turtle screen: setup, title, result display, and exit.
# No game logic lives here — only presentation concerns.

import turtle
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FINISH_X


class Canvas:
    """Configures and manages the Turtle screen."""

    def __init__(self):
        self.screen = turtle.Screen()
        self.screen.setup(width=SCREEN_WIDTH, height=SCREEN_HEIGHT)
        self.screen.title("🐢 Turtle Racing!")
        self._draw_finish_line()

    def _draw_finish_line(self):
        """Draws a visible finish line on the right side of the track."""
        marker = turtle.Turtle()
        marker.hideturtle()
        marker.penup()
        marker.goto(FINISH_X, SCREEN_HEIGHT // 2)
        marker.pendown()
        marker.pensize(3)
        marker.pencolor("black")
        marker.goto(FINISH_X, -(SCREEN_HEIGHT // 2))

    def get_text_input(self, title: str, prompt: str) -> str | None:
        """Wraps screen.textinput — centralizes all popup calls."""
        return self.screen.textinput(title=title, prompt=prompt)

    def show_result(self, message: str, winner_color: str):
        """
        BUG FIX 2: Writes the result directly on the canvas instead of
        abusing textinput() as an alert box.
        """
        self.screen.title(f"GAME OVER: {winner_color.upper()} WON!")
        writer = turtle.Turtle()
        writer.hideturtle()
        writer.penup()
        writer.goto(0, 0)
        writer.color(winner_color)
        writer.write(message, align="center", font=("Arial", 14, "bold"))

    def wait_for_exit(self):
        """Keeps the window open until clicked."""
        print("Click the window to close.")
        self.screen.exitonclick()
