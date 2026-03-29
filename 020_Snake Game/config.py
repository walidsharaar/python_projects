# config.py
# All magic numbers and constants in one place.
# Tuples used for immutable positional data.

SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Snake Game: Phase 2"
SCREEN_BG = "black"

STARTING_POSITIONS = [(0, 0), (-20, 0), (-40, 0)]
MOVE_DISTANCE = 20
GAME_SPEED = 0.1

# Headings
UP = 90
DOWN = 270
LEFT = 180
RIGHT = 0

# Walls trigger at ±295 — keep food safely inside
WALL_LIMIT = 295
# BUG FIX 1: Safe food spawn range (food radius + wall padding)
FOOD_SPAWN_LIMIT = 260

# Collision thresholds
FOOD_COLLISION_DIST = 15
# BUG FIX 2: Match segment size (20px squares) with a consistent threshold
SELF_COLLISION_DIST = 15

# Scoreboard
SCORE_X = 0
# BUG FIX 5: Pulled away from the top edge
SCORE_Y = 260
SCORE_FONT = ("Courier", 20, "normal")
SCORE_ALIGN = "center"
