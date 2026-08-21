# import libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


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

#Box plot for Location_Type vs Sales
plt.figure(figsize=(8, 5))
sns.boxplot(x='Location_Type', y='Sales', data=df)
plt.title('Sales by Location Type (0=Rural, 1=Urban)')
plt.xlabel('Location Type')
plt.ylabel('Sales')
plt.show()

#Scatter plot with trend line for Store_Size vs Sales
plt.figure(figsize=(8, 5))
sns.regplot(x='Store_Size', y='Sales', data=df, scatter_kws={'alpha':0.5}, line_kws={'color':'red'})
plt.title('Store Size vs Sales')
plt.xlabel('Store Size')
plt.ylabel('Sales')
plt.show()

# Histogram of Sales
plt.figure(figsize=(10, 4))

plt.subplot(1, 2, 1)
sns.histplot(df['Sales'], kde=True, color='skyblue')
plt.title('Histogram of Sales')
plt.xlabel('Sales')
plt.ylabel('Frequency')

# Box plot of Sales
plt.subplot(1, 2, 2)
sns.boxplot(x=df['Sales'], color='lightgreen')
plt.title('Box Plot of Sales')
plt.xlabel('Sales')

plt.tight_layout()
plt.show()

# Define features (X) and target (y)
X = df.drop('Sales', axis=1)   # everything except Sales
y = df['Sales']    


# Split into 80% train, 20% test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print("Training set size:", X_train.shape)
print("Test set size:", X_test.shape)

# Create the model
model = LinearRegression()

# Train the model on the training data
model.fit(X_train, y_train)

print("Model trained successfully! ")


# Predict Sales on the test set
y_pred = model.predict(X_test)

# Compare first 5 predictions vs actual Sales
comparison = pd.DataFrame({
    'Actual Sales': y_test.values,
    'Predicted Sales': y_pred
})

print(comparison.head(10))

# Calculate evaluation metrics
mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
r2 = r2_score(y_test, y_pred)

#MAE: Average difference between predicted and actual Sales (in dollars). Lower is better.
#RMSE: Penalizes large errors more than MAE. Also in dollars. Lower is better.
#R2 Score: Proportion of variance in Sales explained by the model.

print(f"Mean Absolute Error (MAE): {mae:,.2f}")
print(f"Root Mean Squared Error (RMSE): {rmse:,.2f}")
print(f"R2 Score: {r2:.4f}")


# Create a dataframe of feature names and their coefficients
coeff_df = pd.DataFrame({
    'Feature': X.columns,
    'Coefficient': model.coef_
})
coeff_df['Abs_Coefficient'] = coeff_df['Coefficient'].abs()
coeff_df = coeff_df.sort_values('Abs_Coefficient', ascending=False)
print(coeff_df)

# Create a dataframe of feature names and their coefficients
coeff_df = pd.DataFrame({
    'Feature': X.columns,
    'Coefficient': model.coef_
})
coeff_df['Abs_Coefficient'] = coeff_df['Coefficient'].abs()
coeff_df = coeff_df.sort_values('Abs_Coefficient', ascending=False)
print(coeff_df)

# Correlation between numeric features (not dummies)
numeric_cols = ['Location_Type', 'Population_Density', 'Number_of_Competitors',
                'Average_Income_per_capita', 'Store_Size', 'Parking_Space',
                'Store_Age_Days', 'Weather_Hot', 'Weather_Moderate']

plt.figure(figsize=(10, 8))
sns.heatmap(df[numeric_cols].corr(), annot=True, cmap='coolwarm', fmt='.2f')
plt.title('Correlation Between Numeric Features')
plt.show()
