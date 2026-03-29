# canvas.py
# Responsible for screen initialization only.


import turtle


class Canvas:
    """
    Owns and configures the Turtle screen.
    Must be instantiated before any Turtle objects are created.
    """

    def __init__(self, title: str = "Hirst Painting", bg_color: str = "white"):
        self.screen = turtle.Screen()
        self.screen.title(title)
        self.screen.bgcolor(bg_color)
        self.screen.colormode(255)  # Enables standard (0–255) RGB values

    def wait_for_exit(self):
        """Keeps the window open until the user clicks."""
        print("Painting complete! Click the window to exit.")
        self.screen.exitonclick()
