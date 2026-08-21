# import libraries
import pandas as pd



# Use pd.read_csv and add an 'r' before the string to make it a raw path
df = pd.read_csv(
    r'D:\Tutorials\Customer Predictive Analytics\data\fast_food_stores_regression.csv'
)
# check the dataframe and evaluate the first 10 rows
#print(df.head(10))

# Drop the Store_ID column
df = df.drop('Store_ID', axis=1)

# Check the first few rows to confirm it's gone
#print(df.head())

# Count missing values in each column
print(df.isnull().sum())

# Show data type of each column
print(df.dtypes)

# Check unique values in text columns
print("Location_Type:", df['Location_Type'].unique())
print("Weather_Conditions:", df['Weather_Conditions'].unique())
print("State:", df['State'].unique())
print("City:", df['City'].unique()[:10])   # show only first 10 to avoid huge list
# Show all unique values in Opening_Date
#print(df['Opening_Date'].unique())

# Show first 30 unique date strings
#print(df['Opening_Date'].unique()[:30])

# Number of unique date strings
print(len(df['Opening_Date'].unique()))

# Check if every Opening_Date matches dd-mm-yyyy pattern
pattern_check = df['Opening_Date'].str.match(r'^\d{2}-\d{2}-\d{4}$')
print("All match dd-mm-yyyy:", pattern_check.all())

# Convert string dates to actual datetime objects
df['Opening_Date'] = pd.to_datetime(df['Opening_Date'], format='%d-%m-%Y')

# Choose a reference date (today's date)
reference_date = pd.Timestamp.now().normalize()

# Create a numeric column: how many days since the store opened
df['Store_Age_Days'] = (reference_date - df['Opening_Date']).dt.days

# Check the result
print(df[['Opening_Date', 'Store_Age_Days']].head(10))


# Count how many dates failed to parse
print("NaT count:", df['Opening_Date'].isna().sum())


# Convert categorical columns to numbers 

# drop cities  for now, as they are too many to encode
df = df.drop('City', axis=1)

df['Location_Type'] = df['Location_Type'].map({'Rural': 0, 'Urban': 1})

# Create dummy variables, dropping first to avoid redundancy
weather_dummies = pd.get_dummies(df['Weather_Conditions'], prefix='Weather', drop_first=True)

# Add these new columns to df
df = pd.concat([df, weather_dummies], axis=1)

# Drop the original text column
df = df.drop('Weather_Conditions', axis=1)

state_dummies = pd.get_dummies(df['State'], prefix='State', drop_first=True)

df = pd.concat([df, state_dummies], axis=1)

df = df.drop('State', axis=1)


print(df.head(10))
print(df.columns)
print(df.shape)


# Drop Opening_Date column
df = df.drop('Opening_Date', axis=1)

# Find columns that are boolean (True/False) and convert them to integers (0/1)
bool_cols = df.select_dtypes(include='bool').columns
df[bool_cols] = df[bool_cols].astype(int)

# Check that all columns are now numeric
print(df.dtypes)

# Check for any non-numeric columns left
non_numeric = df.select_dtypes(exclude=['int64', 'float64']).columns
print("Non-numeric columns:", non_numeric)

# Preview the cleaned dataframe
print(df.head())

# Exploratory Data Analysis (EDA) – Part 1

# Summary statistics for all numeric columns
print(df.describe())

# Correlation of every feature with Sales (sorted)
corr_with_sales = df.corr()['Sales'].sort_values(ascending=False)
print("\nCorrelation with Sales:\n")
print(corr_with_sales)