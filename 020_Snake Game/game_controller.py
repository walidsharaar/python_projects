# game_controller.py
# Owns the game loop and all collision detection.
# Wires Snake, Food, and Scoreboard together without knowing their internals.
# BUG FIX 4: All setup and loop logic moved out of module-level globals.

import turtle
import time
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, SCREEN_BG,
    GAME_SPEED, WALL_LIMIT, FOOD_COLLISION_DIST, SELF_COLLISION_DIST,
)
from snake import Snake
from food import Food
from scoreboard import Scoreboard


class GameController:
    """
    Sets up the screen, binds controls, and runs the game loop.
    Collision detection lives here — not scattered in individual models.
    """

    def __init__(self):
        # Screen first — always before any Turtle object
        self.screen = turtle.Screen()
        self.screen.setup(width=SCREEN_WIDTH, height=SCREEN_HEIGHT)
        self.screen.bgcolor(SCREEN_BG)
        self.screen.title(SCREEN_TITLE)
        self.screen.tracer(0)

        self.snake = Snake()
        self.food = Food()
        self.scoreboard = Scoreboard()
        self.game_is_on = True

        self._bind_controls()

    def _bind_controls(self):
        self.screen.listen()
        self.screen.onkey(self.snake.up, "Up")
        self.screen.onkey(self.snake.down, "Down")
        self.screen.onkey(self.snake.left, "Left")
        self.screen.onkey(self.snake.right, "Right")

    def _check_food_collision(self):
        if self.snake.head.distance(self.food) < FOOD_COLLISION_DIST:
            self.food.refresh()
            self.snake.extend()
            self.scoreboard.increase_score()

    def _check_wall_collision(self):
        if (abs(self.snake.head.xcor()) > WALL_LIMIT or
                abs(self.snake.head.ycor()) > WALL_LIMIT):
            self.game_is_on = False
            self.scoreboard.game_over()

    def _check_self_collision(self):
        """
        Uses list slicing [1:] to skip the head — the Pythonic way
        to iterate only over the tail segments.
        BUG FIX 2: SELF_COLLISION_DIST = 15 for consistent detection.
        BUG FIX 3: game_over() guard in Scoreboard prevents double-write.
        """
        for segment in self.snake.segments[1:]:
            if self.snake.head.distance(segment) < SELF_COLLISION_DIST:
                self.game_is_on = False
                self.scoreboard.game_over()

    def run(self):
        """Main game loop."""
        while self.game_is_on:
            self.screen.update()
            time.sleep(GAME_SPEED)
            self.snake.move()
            self._check_food_collision()
            self._check_wall_collision()
            self._check_self_collision()

        self.screen.exitonclick()
