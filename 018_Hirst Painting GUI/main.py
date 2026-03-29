# Day 18: Hirst Painting Project (Turtle GUI) — OOP Refactor

import turtle
import random


# --- STEP 1: DATA ---
# Tuples are used here intentionally — colors are constant, immutable data.
HIRST_PALETTE = [
    (202, 164, 109), (238, 240, 245), (150, 75,  49),
    (223, 201, 135), (52,  107, 132), (179, 77,  103),
    (145, 154, 149), (14,  70,  90),  (232, 228, 236),
    (198, 142, 158), (213, 198, 208),
]


# --- STEP 2: CLASS ---
class HirstPainting:
    """
    Encapsulates the screen, turtle, and painting logic.
    Separating setup from drawing makes each piece independently testable.
    """

    def __init__(
        self,
        rows: int = 10,
        cols: int = 10,
        spacing: int = 50,
        dot_size: int = 20,
        palette: list[tuple] = HIRST_PALETTE,
    ):
        self.rows = rows
        self.cols = cols
        self.spacing = spacing
        self.dot_size = dot_size
        self.palette = palette

        # BUG FIX 2: Screen initialized first, before the turtle
        self.screen = turtle.Screen()
        self.screen.title("Hirst Painting")
        self.screen.colormode(255)

        self.pen = turtle.Turtle()
        self.pen.speed("fastest")
        self.pen.penup()
        self.pen.hideturtle()

    def _pick_color(self) -> tuple:
        """Internal helper — keeps random logic in one place."""
        return random.choice(self.palette)

    def _calc_start(self) -> tuple[float, float]:
        """
        BUG FIX 1: Uses (n - 1) * spacing so the grid is truly centered.
        The span between n dots is (n-1) gaps, not n gaps.
        """
        start_x = -((self.cols - 1) * self.spacing) / 2
        start_y = -((self.rows - 1) * self.spacing) / 2
        return start_x, start_y

    def paint(self):
        """Draws the dot grid. Each row is a fresh goto — no heading changes needed."""
        start_x, start_y = self._calc_start()

        for row in range(self.rows):
            y = start_y + row * self.spacing

            for col in range(self.cols):
                x = start_x + col * self.spacing
                # BUG FIX 3: Use goto per dot — no setheading() needed at all
                self.pen.goto(x, y)
                self.pen.dot(self.dot_size, self._pick_color())

    def wait_for_exit(self):
        """Keeps the window open until the user clicks."""
        print("Painting complete! Click the window to exit.")
        self.screen.exitonclick()


# --- STEP 3: ENTRY POINT ---
if __name__ == "__main__":
    painting = HirstPainting(rows=10, cols=10, spacing=50, dot_size=20)
    painting.paint()
    painting.wait_for_exit()