from turtle import Turtle

STARTING_POSITION = (0, -280)
MOVE_DISTANCE = 10
FINISH_LINE_Y = 280
SIDE_BOUNDARY = 280 # Prevents going off-screen left/right

class Player(Turtle):
    def __init__(self):
        super().__init__()
        self.shape("turtle")
        self.penup()
        self.setheading(90)
        self.go_to_start()

    def go_up(self):
        self.setheading(90)
        self.forward(MOVE_DISTANCE)

    def go_down(self):
        # Prevent going below the starting area
        if self.ycor() > -280:
            self.setheading(270)
            self.forward(MOVE_DISTANCE)

    def go_left(self):
        if self.xcor() > -SIDE_BOUNDARY:
            self.setheading(180)
            self.forward(MOVE_DISTANCE)

    def go_right(self):
        if self.xcor() < SIDE_BOUNDARY:
            self.setheading(0)
            self.forward(MOVE_DISTANCE)

    def go_to_start(self):
        self.setheading(90) # Face up again
        self.goto(STARTING_POSITION)

    def is_at_finish_line(self):
        return self.ycor() > FINISH_LINE_Y