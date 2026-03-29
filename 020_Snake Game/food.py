# food.py
# Models the food pellet. Inherits from Turtle for drawing.
# Owns only its appearance and respawn logic.

import turtle
import random
from config import FOOD_SPAWN_LIMIT


class Food(turtle.Turtle):
    """
    Inherits Turtle to gain built-in drawing and positioning.
    BUG FIX 1: Spawns within FOOD_SPAWN_LIMIT to stay clear of walls.
    """

    def __init__(self):
        super().__init__()
        self.shape("circle")
        self.penup()
        self.shapesize(stretch_len=0.5, stretch_wid=0.5)
        self.color("blue")
        self.speed("fastest")
        self.refresh()

    def refresh(self):
        """Moves food to a new random position safely inside the walls."""
        x = random.randint(-FOOD_SPAWN_LIMIT, FOOD_SPAWN_LIMIT)
        y = random.randint(-FOOD_SPAWN_LIMIT, FOOD_SPAWN_LIMIT)
        self.goto(x, y)
