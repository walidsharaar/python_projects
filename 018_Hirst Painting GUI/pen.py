# pen.py
# Responsible for creating and configuring the Turtle instance.


import turtle


class Pen:
    """
    Wraps and configures a Turtle instance for dot painting.
    Exposes only the actions the painter needs: goto and dot.
    """

    def __init__(self, speed: str = "fastest"):
        self.turtle = turtle.Turtle()
        self.turtle.speed(speed)
        self.turtle.penup()       # Never draw lines between dots
        self.turtle.hideturtle()  # Keep the canvas clean

    def goto(self, x: float, y: float):
        """Moves the pen to an absolute position without drawing."""
        self.turtle.goto(x, y)

    def draw_dot(self, size: int, color: tuple):
        """Stamps a filled circle at the current position."""
        self.turtle.dot(size, color)
