# racer.py
# Models a single turtle racer.
# Each Racer instance is fully independent — unique color, position, and state.
# This is the "Instance Independence" principle: same blueprint, unique state.

import turtle
import random
from config import START_X, FINISH_X


class Racer:
    """
    Wraps a single Turtle instance and exposes only race-relevant behavior.
    The RaceTrack doesn't need to know anything about turtle internals.
    """

    def __init__(self, color: str, y_position: int):
        self.color = color
        self._turtle = turtle.Turtle(shape="turtle")
        self._turtle.color(color)
        self._turtle.penup()
        self._turtle.goto(x=START_X, y=y_position)

    def move(self):
        """Advances the racer by a random distance (simulates acceleration)."""
        distance = random.randint(0, 10)
        self._turtle.forward(distance)

    def has_finished(self) -> bool:
        """
        BUG FIX 4: Uses the config constant instead of a magic number.
        Returns True if this racer has crossed the finish line.
        """
        return self._turtle.xcor() >= FINISH_X
