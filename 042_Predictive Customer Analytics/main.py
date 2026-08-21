# import libraries
import pandas as pd
import numpy as np
from io import StringIO
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score

# Use pd.read_csv and add an 'r' before the string to make it a raw path
df = pd.read_csv(
    r'D:\Tutorials\Customer Predictive Analytics\data\fast_food_stores_regression.csv'
)
# check the dataframe and evaluate the first 10 rows
#print(df.head(10))

# Replace '.' and '/' with '-'
df['Opening_Date'] = df['Opening_Date'].astype(str).str.replace(r'[./]', '-', regex=True)

# Parse as date with dayfirst=True
df['Opening_Date'] = pd.to_datetime(df['Opening_Date'], dayfirst=True, errors='coerce')

# Check if any dates failed to parse
#print(df['Opening_Date'].isna().sum())   # Should be 0

# Store_ID is just an identifier → drop
df = df.drop(columns=['Store_ID'])

# City has too many unique values for only 25 rows → drop to avoid overfitting
# State can be kept, but we will handle it carefully
df = df.drop(columns=['City'])

# Extract year and month
df['Opening_Year'] = df['Opening_Date'].dt.year
df['Opening_Month'] = df['Opening_Date'].dt.month

# Cyclical encoding for month (captures seasonality without assuming linearity)
df['Month_sin'] = np.sin(2 * np.pi * df['Opening_Month'] / 12)
df['Month_cos'] = np.cos(2 * np.pi * df['Opening_Month'] / 12)

# Drop original date
df = df.drop(columns=['Opening_Date'])

df['Location_Urban'] = (df['Location_Type'] == 'Urban').astype(int)
df = df.drop(columns=['Location_Type'])


weather_dummies = pd.get_dummies(df['Weather_Conditions'], prefix='Weather', drop_first=True)
df = pd.concat([df, weather_dummies], axis=1)
df = df.drop(columns=['Weather_Conditions'])



state_dummies = pd.get_dummies(df['State'], prefix='State', drop_first=True)
df = pd.concat([df, state_dummies], axis=1)
df = df.drop(columns=['State'])


# Number of competitors per 1,000 people in the surrounding density
df['Competitors_per_1000_density'] = df['Number_of_Competitors'] / (df['Population_Density'] + 1) * 1000



# Show only the most important columns for readability
preview_cols = [
    'Population_Density', 'Number_of_Competitors', 'Average_Income_per_capita',
    'Store_Size', 'Parking_Space', 'Sales', 'Location_Urban',
    'Weather_Hot', 'Weather_Moderate', 'Opening_Year', 'Opening_Month',
    'Competitors_per_1000_density'
]
print(df[preview_cols].head())
X = df.drop(columns=['Sales'])
y = df['Sales']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = LinearRegression()
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

print('R²:', r2_score(y_test, y_pred))
print('RMSE:', np.sqrt(mean_squared_error(y_test, y_pred)))
scores = cross_val_score(model, X, y, cv=5, scoring='r2')
print('Cross-validated R²:', scores)
print('Mean R²:', scores.mean())

#print(df.head(10))