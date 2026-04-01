import random
from turtle import Turtle

# --- CONSTANTS ---
COLORS = ["red", "orange", "yellow", "green", "blue", "purple"]
STARTING_MOVE_DISTANCE = 5
MOVE_INCREMENT = 5

class CarManager:
    def __init__(self):
        self.all_cars = []
        self.car_speed = STARTING_MOVE_DISTANCE

    def create_car(self):
        """Generates a new car at a random Y-coordinate on the right edge."""
        random_chance = random.randint(1, 6)
        if random_chance == 1:
            new_car = Turtle("square")
            new_car.shapesize(stretch_wid=1, stretch_len=2)
            new_car.penup()
            new_car.color(random.choice(COLORS))
            random_y = random.randint(-250, 250)
            new_car.goto(300, random_y)
            self.all_cars.append(new_car)

    def move_cars(self):
        """Moves all active cars to the left."""
        for car in self.all_cars:
            car.backward(self.car_speed)
            
    def level_up(self):
        """Increases the speed of all cars for the next level."""
        self.car_speed += MOVE_INCREMENT

    def clear_offscreen_cars(self):
        """Removes cars that are no longer visible to save memory."""
        for car in self.all_cars[:]: # Slice copy to avoid index errors during removal
            if car.xcor() < -320:
                car.hideturtle()
                self.all_cars.remove(car)