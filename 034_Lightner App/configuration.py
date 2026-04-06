# Shared settings for the entire application
DB_SETTINGS = {
    'server': 'localhost',
    'database': 'GermanLeitnerDB',
    'driver': '{ODBC Driver 17 for SQL Server}'
}

# The Spaced Repetition Schedule (Days until next review)
LEITNER_SCHEDULE = {
    1: 1,   # Box 1: Review every 1 day
    2: 3,   # Box 2: Review every 3 days
    3: 7,   # Box 3: Review every 7 days
    4: 14,  # Box 4: Review every 14 days
    5: 30   # Box 5: Mastered (Review every 30 days)
}