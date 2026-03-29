# Day 19: Turtle Racing Game (GUI + OOP)
# Learning Goals: Coordinate Systems, Instances, and State Management.


import turtle as t
import random

# --- STEP 1: CONFIGURATION & SETUP ---

class RaceManager:
    """Manages the game state, screen, and betting logic."""
    def __init__(self):
        self.screen = t.Screen()
        # Setting up the 'Canvas' size
        self.screen.setup(width=500, height=400)
        self.is_race_on = False
        self.user_bet = ""
        self.colors = ["red", "orange", "yellow", "green", "blue", "purple"]
        self.all_turtles = []

    def get_user_bet(self):
        """Captures the user's prediction via a popup UI."""
        self.user_bet = self.screen.textinput(
            title="Make your bet", 
            prompt=f"Which turtle will win the race? Enter a color ({', '.join(self.colors)}):"
        ).lower()
        if self.user_bet:
            self.is_race_on = True

    def setup_racers(self):
        """Creates turtle instances and positions them at the starting line."""
        y_positions = [-70, -40, -10, 20, 50, 80]
        
        for turtle_index in range(0, 6):
            # Each 'new_turtle' is an independent OBJECT (Instance)
            new_turtle = t.Turtle(shape="turtle")
            new_turtle.color(self.colors[turtle_index])
            new_turtle.penup()
            # Move to coordinates (x, y) -> Starting line is at -230 on X-axis
            new_turtle.goto(x=-230, y=y_positions[turtle_index])
            self.all_turtles.append(new_turtle)

    def start_race(self):
        """The main game loop managing movement and collision detection with the finish line."""
        while self.is_race_on:
            for turtle in self.all_turtles:
                # 230 is the 'Finish Line' (500 width / 2 = 250, minus turtle size)
                if turtle.xcor() > 230:
                    self.is_race_on = False
                    winning_color = turtle.pencolor()
                    
                    # Determine the message for the popup
                    if winning_color == self.user_bet:
                        message = f"You've won! The {winning_color} turtle is the winner!"
                    else:
                        message = f"You've lost! The {winning_color} turtle is the winner!"
                    
                   
                    # or simply print to console. Since Turtle doesn't have a native 
                    # 'alert', we'll use a title update and a final popup.
                    self.screen.title(f"GAME OVER: {winning_color.upper()} WON!")
                    
                    # This creates a final popup window to announce the winner
                    self.screen.textinput(title="Race Results", prompt=f"{message}\n\nPress OK to finish.")
                    
                    break
                
                # Each turtle moves a random amount (Simulating acceleration)
                rand_distance = random.randint(0, 10)
                turtle.forward(rand_distance)

# --- STEP 2: EXECUTION ---

if __name__ == "__main__":
    # Instantiate our manager object
    manager = RaceManager()
    
    # 1. Setup the track and racers
    manager.setup_racers()
    
    # 2. Get the bet from the user
    manager.get_user_bet()
    
    # 3. Trigger the race logic
    manager.start_race()
    
    # Close window on click
    manager.screen.exitonclick()

