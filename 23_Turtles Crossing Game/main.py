# Day 23: Turtle Crossing Capstone
# Learning Goals: Modular OOP, Collision Detection, and Resource Management.

import time
from turtle import Screen
from player import Player
from car_manager import CarManager
from scoreboard import Scoreboard

def main():
    # --- Screen Setup ---
    screen = Screen()
    screen.setup(width=600, height=600)
    screen.tracer(0)  # Turns off animation updates for manual control
    screen.title("Turtle Crossing - Full Directional Controls")

    # --- Initialize Objects ---
    player = Player()
    car_manager = CarManager()
    scoreboard = Scoreboard()

    # --- Key Bindings for all directions ---
    screen.listen()
    screen.onkey(player.go_up, "Up")
    screen.onkey(player.go_down, "Down")
    screen.onkey(player.go_left, "Left")
    screen.onkey(player.go_right, "Right")

    # --- Main Game Loop ---
    game_is_on = True
    while game_is_on:
        time.sleep(0.1)
        screen.update()

        # Generate and move cars
        car_manager.create_car()
        car_manager.move_cars()

        # Check for collision with cars
        for car in car_manager.all_cars:
            if car.distance(player) < 20:
                game_is_on = False
                scoreboard.game_over()

        # Check if player reached the finish line
        if player.is_at_finish_line():
            player.go_to_start()
            car_manager.level_up()
            scoreboard.increase_level()

    screen.exitonclick()

if __name__ == "__main__":
    main()