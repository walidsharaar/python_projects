# snake.py
# Models the snake: its segments, movement, direction control, and extension.
# No screen, no score, no food — purely the snake's own state and behavior.

import turtle
from config import STARTING_POSITIONS, MOVE_DISTANCE, UP, DOWN, LEFT, RIGHT


class Snake:
    """
    Manages the snake's body segments and movement logic.
    Uses list slicing [1:] for clean tail-collision checks externally.
    """

    def __init__(self):
        self.segments: list[turtle.Turtle] = []
        self._create_snake()
        self.head = self.segments[0]

    def _create_snake(self):
        for position in STARTING_POSITIONS:
            self._add_segment(position)

    def _add_segment(self, position: tuple):
        segment = turtle.Turtle("square")
        segment.color("white")
        segment.penup()
        segment.goto(position)
        self.segments.append(segment)

    def extend(self):
        """Grows the snake by adding a segment at the tail's current position."""
        self._add_segment(self.segments[-1].position())

    def move(self):
        """
        Shifts each segment into the position of the one ahead of it,
        then advances the head forward.
        """
        for i in range(len(self.segments) - 1, 0, -1):
            new_x = self.segments[i - 1].xcor()
            new_y = self.segments[i - 1].ycor()
            self.segments[i].goto(new_x, new_y)
        self.head.forward(MOVE_DISTANCE)

    # --- Direction controls with 180° reversal guard ---
    def up(self):
        if self.head.heading() != DOWN:
            self.head.setheading(UP)

    def down(self):
        if self.head.heading() != UP:
            self.head.setheading(DOWN)

    def left(self):
        if self.head.heading() != RIGHT:
            self.head.setheading(LEFT)

    def right(self):
        if self.head.heading() != LEFT:
            self.head.setheading(RIGHT)
