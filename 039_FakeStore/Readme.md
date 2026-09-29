# Modular ETL Pipeline: Fake Store API to PostgreSQL

A modular, production-inspired Data Engineering ETL (Extract, Transform, Load) pipeline built using **Python**, **Pandas**, **SQLAlchemy**, and **PostgreSQL**. 

This pipeline extracts e-commerce product data from a public REST API, cleans and flattens nested JSON structures into tabular formats, and loads the transformed dataset into a relational PostgreSQL database.


## Tools & Technologies

* **Language:** Python 3.9+
* **Data Manipulation:** Pandas
* **Database Driver & ORM:** SQLAlchemy, `psycopg2-binary`
* **Database:** PostgreSQL
* **API Integration:** Requests
* **Environment Management:** `python-dotenv`
* **Install the requirement from txt file:** `pip install -r requirements.txt`

## Running the Pipeline

To execute the full ETL pipeline from extraction to database loading, run `main.py`:

## Future Enhancements

* Add containerization support with Docker and Docker Compose (PostgreSQL container).
* Implement automated scheduling using Prefect or Apache Airflow.
* Add unit and integration test coverage using `pytest`