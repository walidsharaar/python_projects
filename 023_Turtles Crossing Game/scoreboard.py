from turtle import Turtle

FONT = ("Courier", 24, "normal")

class Scoreboard(Turtle):
    def __init__(self):
        super().__init__()
        self.level = 1
        self.hideturtle()
        self.penup()
        self.goto(-280, 250)
        self.update_scoreboard()

    def update_scoreboard(self):
        """Refreshes the level display on the screen."""
        self.clear()
        self.write(f"Level: {self.level}", align="left", font=FONT)

    def increase_level(self):
        """Increments the internal level counter and refreshes UI."""
        self.level += 1
        self.update_scoreboard()

    def game_over(self):
        """Displays a centralized game over message."""
        self.goto(0, 0)
        self.write("GAME OVER", align="center", font=FONT)