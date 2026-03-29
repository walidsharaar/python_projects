# hirst_painting.py


import random
from pen import Pen
from palette import HIRST_PALETTE


class HirstPainting:
    """
    Calculates dot positions and delegates drawing to a Pen instance.
    Changing the grid size, spacing, or palette doesn't affect any other class.
    """

    def __init__(
        self,
        pen: Pen,
        rows: int = 10,
        cols: int = 10,
        spacing: int = 50,
        dot_size: int = 20,
        palette: list[tuple] = HIRST_PALETTE,
    ):
        self.pen = pen
        self.rows = rows
        self.cols = cols
        self.spacing = spacing
        self.dot_size = dot_size
        self.palette = palette

    def _pick_color(self) -> tuple:
        """Randomly selects one color from the palette."""
        return random.choice(self.palette)

    def _calc_start(self) -> tuple[float, float]:
        """
        Computes the top-left starting coordinate so the grid is centered.
        Uses (n - 1) * spacing because n dots have (n-1) gaps between them.
        """
        start_x = -((self.cols - 1) * self.spacing) / 2
        start_y = -((self.rows - 1) * self.spacing) / 2
        return start_x, start_y

    def paint(self):
        """Iterates over the grid and draws each dot via the Pen."""
        start_x, start_y = self._calc_start()

        for row in range(self.rows):
            y = start_y + row * self.spacing

            for col in range(self.cols):
                x = start_x + col * self.spacing
                self.pen.goto(x, y)
                self.pen.draw_dot(self.dot_size, self._pick_color())
