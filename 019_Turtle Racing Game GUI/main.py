# Day 19: Turtle Racing Game (GUI + OOP)
# Learning Goals: Coordinate Systems, Instances, and State Management.


from canvas import Canvas
from bet_manager import BetManager
from race_track import RaceTrack


def main():
    # 1. Screen must come first — before any Turtle object is created
    canvas = Canvas()

    # 2. Get and validate the user's bet
    bet_manager = BetManager(canvas)
    bet_placed = bet_manager.prompt_bet()

    if not bet_placed:
        print("No bet placed. Exiting.")
        canvas.wait_for_exit()
        return

    # 3. Build the track and run the race
    track = RaceTrack()
    winning_color = track.run()

    # 4. Evaluate the bet and display the result on the canvas
    result_message = bet_manager.evaluate(winning_color)
    canvas.show_result(result_message, winning_color)
    print(result_message)

    # 5. Keep window open
    canvas.wait_for_exit()


if __name__ == "__main__":
    main()
