import turtle
import pandas

# Setup the screen
screen = turtle.Screen()
screen.title("Afghanistan Provinces Game")

# Define the paths provided
image_path = r"D:\Projects\Python\python_projects\25_US State Game\assests\blank_afghanistan.gif"
data_path = r"D:\Projects\Python\python_projects\25_US State Game\assests\afghanistan_provinces.csv"

# Add the blank map as a shape to the turtle screen
screen.addshape(image_path)
turtle.shape(image_path)

# Load the province data
# Expected CSV format: province,x,y
data = pandas.read_csv(data_path)
all_provinces = data.province.to_list()
guessed_provinces = []

while len(guessed_provinces) < len(all_provinces):
    # Prompt user for input
    answer_province = screen.textinput(
        title=f"{len(guessed_provinces)}/{len(all_provinces)} Provinces Correct",
        prompt="What's another province's name?"
    )
    
    # Handle Cancel or "Exit"
    if answer_province is None or answer_province.title() == "Exit":
        # Create a CSV of provinces the user missed
        missing_provinces = [p for p in all_provinces if p not in guessed_provinces]
        new_data = pandas.DataFrame(missing_provinces)
        new_data.to_csv("provinces_to_learn.csv")
        break

    # Format the input to match the CSV casing (Title Case)
    answer_province = answer_province.title()

    # Check if the guess is correct and not already guessed
    if answer_province in all_provinces and answer_province not in guessed_provinces:
        guessed_provinces.append(answer_province)
        
        # Create a turtle to write the name on the map
        t = turtle.Turtle()
        t.hideturtle()
        t.penup()
        
        # Get the coordinates for the specific province
        province_data = data[data.province == answer_province]
        t.goto(int(province_data.x.iloc[0]), int(province_data.y.iloc[0]))
        t.write(answer_province, align="center", font=("Arial", 8, "normal"))

# Keep the window open until clicked
screen.exitonclick()