# main.py
# Entry point — wires all classes together and runs the program.


from canvas import Canvas
from pen import Pen
from hirst_painting import HirstPainting


def main():
    # 1. Screen must come first — before any Turtle object is created
    canvas = Canvas(title="Hirst Painting")

    # 2. Pen wraps the turtle instance
    pen = Pen(speed="fastest")

    # 3. Painting algorithm receives the pen as a dependency
    painting = HirstPainting(
        pen=pen,
        rows=10,
        cols=10,
        spacing=50,
        dot_size=20,
    )

    # 4. Draw and wait
    painting.paint()
    canvas.wait_for_exit()


if __name__ == "__main__":
    main()
