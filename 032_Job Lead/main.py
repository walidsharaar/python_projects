import sys
import os
import pandas as pd
import re
from datetime import datetime
from sqlalchemy import create_engine, text

class SQLServerConnector:
    """
    Handles connections to Microsoft SQL Server using SQLAlchemy.
    Includes logic to ensure the target database exists.
    """
    def __init__(self, server, database, driver="ODBC Driver 17 for SQL Server"):
        self.server = server
        self.database = database
        self.driver = driver
        
        # Connection string for 'master' to check/create the target DB
        self.base_url = (
            f"mssql+pyodbc://{self.server}/master?"
            f"driver={self.driver}&trusted_connection=yes&TrustServerCertificate=yes"
        )
        
        # Final target connection string
        self.target_url = (
            f"mssql+pyodbc://{self.server}/{self.database}?"
            f"driver={self.driver}&trusted_connection=yes&TrustServerCertificate=yes"
        )
        
        self._ensure_database_exists()
        self.engine = create_engine(self.target_url)

    def _ensure_database_exists(self):
        """Checks if the database exists; creates it if not."""
        print(f"Connecting to server '{self.server}' to check for database '{self.database}'...")
        temp_engine = create_engine(self.base_url)
        try:
            with temp_engine.connect() as conn:
                # Set isolation level to AUTOCOMMIT to allow CREATE DATABASE
                conn = conn.execution_options(isolation_level="AUTOCOMMIT")
                
                query = text("SELECT database_id FROM sys.databases WHERE name = :db_name")
                result = conn.execute(query, {"db_name": self.database}).fetchone()
                
                if not result:
                    print(f"Database '{self.database}' not found. Creating it now...")
                    conn.execute(text(f"CREATE DATABASE [{self.database}]"))
                    print(f"Database '{self.database}' created successfully.")
                else:
                    print(f"Database '{self.database}' verified.")
        except Exception as e:
            print(f"Error during database verification: {e}")
        finally:
            temp_engine.dispose()

    def get_engine(self):
        return self.engine

def get_job_data():
    """
    Scrapes LinkedIn, Indeed, and Google Jobs for multiple keywords in Hamburg.
    Cleans corrupted URLs that include dates and salary info.
    """
    try:
        from jobspy import scrape_jobs
    except ImportError:
        print("Error: 'python-jobspy' is not installed. Please run: pip install python-jobspy")
        return pd.DataFrame()

    # List of keywords to search for
    search_terms = ["Industriekaufmann", "Ausbildung", "Büromanagement"]
    target_sites = ["linkedin", "indeed", "google"]
    all_jobs_list = []

    for term in search_terms:
        print(f"Starting job search for '{term}' in Hamburg (LinkedIn, Indeed, Google)...")
        try:
            jobs = scrape_jobs(
                site_name=target_sites,
                search_term=term,
                location="Hamburg, Germany",
                results_wanted=30, 
                hours_old=24,     # Last 7 days
                country_indeed='germany'
            )
            
            if jobs is not None and not jobs.empty:
                all_jobs_list.append(jobs)
        except Exception as e:
            print(f"Warning: Scrape for '{term}' encountered an issue: {e}")
            continue

    if not all_jobs_list:
        print("No jobs found for any of the criteria.")
        return pd.DataFrame()

    try:
        # Combine all results
        combined_jobs = pd.concat(all_jobs_list, ignore_index=True)

        # 1. Clean URLs immediately to prevent corruption from trailing data (,2026-04-01...)
        def clean_url(url, site):
            if pd.isna(url): return ""
            # Convert to string and take the first part before any comma
            raw_url = str(url).split(',')[0].strip()
            # Remove artifacts like brackets/quotes from stringified lists
            raw_url = raw_url.replace('[', '').replace(']', '').replace("'", "").replace('"', '')
            
            # Google Job ID Fix
            if site == 'google' and not raw_url.startswith('http'):
                return f"https://www.google.com/search?q=jobs&ibp=htl;jobs#fpstate=tldetail&htidocid={raw_url}"
            
            # Indeed/LinkedIn URL validation (must start with http)
            # If the library returns an ID for indeed, format it correctly
            if site == 'indeed' and not raw_url.startswith('http') and len(raw_url) > 5:
                return f"https://de.indeed.com/viewjob?jk={raw_url}"
                
            return raw_url

        combined_jobs['job_url'] = combined_jobs.apply(lambda x: clean_url(x['job_url'], x['site']), axis=1)

        # 2. Format Salary safely
        def format_salary(row):
            min_v = row.get('min_amount')
            max_v = row.get('max_amount')
            if pd.notna(min_v) and pd.notna(max_v):
                return f"{min_v} - {max_v} {row.get('currency', 'EUR')} ({row.get('interval', 'yearly')})"
            elif pd.notna(min_v):
                return f"From {min_v} {row.get('currency', 'EUR')}"
            return "Not Disclosed"

        combined_jobs['SalaryInfo'] = combined_jobs.apply(format_salary, axis=1)

        # 3. Standardize Dates
        combined_jobs['date_posted'] = pd.to_datetime(combined_jobs['date_posted'], errors='coerce').dt.normalize()
        combined_jobs['date_posted'] = combined_jobs['date_posted'].fillna(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))
        
        # 4. Final Selection & Renaming
        final_df = combined_jobs[['site', 'title', 'company', 'location', 'job_url', 'date_posted', 'SalaryInfo']].copy()
        final_df.columns = ['Site', 'JobTitle', 'Company', 'Location', 'JobURL', 'DatePosted', 'Salary']
        
        # 5. Deduplication
        final_df = final_df[final_df['JobURL'].str.startswith('http', na=False)]
        final_df = final_df.drop_duplicates(subset=['JobURL'])
        
        print(f"Successfully scraped {len(final_df)} unique jobs in total.")
        return final_df
        
    except Exception as e:
        print(f"Data processing error: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def save_to_csv(df):
    """Saves findings to a CSV file."""
    if df.empty: return
    filename = f"job_search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    try:
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"CSV backup created: {os.path.abspath(filename)}")
    except Exception as e:
        print(f"Error saving CSV: {e}")

def save_to_sql_server(df):
    """Saves jobs to the MS SQL Server database."""
    server = 'DESKTOP-59A1RG2'
    database = 'JobLeadsDB'
    try:
        connector = SQLServerConnector(server, database)
        engine = connector.get_engine()
        with engine.begin() as conn:
            conn.execute(text("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Jobs' AND xtype='U')
                CREATE TABLE Jobs (
                    ID INT IDENTITY(1,1) PRIMARY KEY,
                    Site NVARCHAR(50),
                    JobTitle NVARCHAR(255),
                    Company NVARCHAR(255),
                    Location NVARCHAR(100),
                    JobURL NVARCHAR(MAX),
                    Salary NVARCHAR(255),
                    DatePosted DATETIME,
                    ScrapedAt DATETIME DEFAULT GETDATE()
                )
                ELSE IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('Jobs') AND name = 'Salary')
                ALTER TABLE Jobs ADD Salary NVARCHAR(255);
            """))
            try:
                existing_urls_df = pd.read_sql("SELECT JobURL FROM Jobs", conn)
                existing_urls = set(existing_urls_df['JobURL'].tolist())
            except:
                existing_urls = set()

            new_jobs = df[~df['JobURL'].isin(existing_urls)]
            if not new_jobs.empty:
                new_jobs.to_sql('Jobs', conn, if_exists='append', index=False, chunksize=50)
                print(f"SQL Update: {len(new_jobs)} records added.")
            else:
                print("No new jobs to add to SQL Server.")
    except Exception as e:
        print(f"SQL Error: {e}")

if __name__ == "__main__":
    job_df = get_job_data()
    if not job_df.empty:
        save_to_sql_server(job_df)
        save_to_csv(job_df)
    else:
        print("Process finished with no data.")