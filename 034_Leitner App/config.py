# Updated config with common SQL Server variations
DB_CONFIG = {
    # Try '.', 'localhost', or '(localdb)\MSSQLLocalDB'
    'server': 'localhost', 
    'database': 'GermanLeitnerDB',
    # Check if you have 'ODBC Driver 17' or 'ODBC Driver 18' or 'SQL Server'
    'driver': '{ODBC Driver 17 for SQL Server}' 
}

BOX_INTERVALS = {1: 1, 2: 3, 3: 7, 4: 14, 5: 30}

COLORS = {
    'bg': '#f0f2f5',
    'primary': '#1a73e8',
    'accent': '#34a853',
    'text': '#202124'
}