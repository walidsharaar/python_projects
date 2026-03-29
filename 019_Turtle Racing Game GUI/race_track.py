# race_track.py
# Owns the racers list and the main game loop.
# Knows nothing about the screen, betting, or user input —
# it only manages movement and detects a winner.

from racer import Racer
from config import RACER_COLORS, RACER_Y_POSITIONS


class RaceTrack:
    """
    Creates racers and runs the race loop.
    BUG FIX 4: Racer count is derived from config — no magic numbers.
    BUG FIX 1: Winner detection exits the loop cleanly on the same tick.
    """

    def __init__(self):
        self.racers: list[Racer] = []
        self._setup_racers()

    def _setup_racers(self):
        """
        BUG FIX 4: Uses zip(RACER_COLORS, RACER_Y_POSITIONS) so the count is
        always consistent — adding a color automatically adds a racer.
        """
        for color, y_pos in zip(RACER_COLORS, RACER_Y_POSITIONS):
            self.racers.append(Racer(color=color, y_position=y_pos))

    def run(self) -> str:
        """
        Runs the race loop and returns the winning color.
        BUG FIX 1: Checks has_finished() before moving — winner is detected
        the moment they cross, not one iteration later.
        """
        while True:
            for racer in self.racers:
                if racer.has_finished():
                    return racer.color   # Immediately returns — no extra iteration
                racer.move()
