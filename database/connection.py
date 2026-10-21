
import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load environment variables from the project's root .env file
load_dotenv(
    os.path.join(os.path.dirname(__file__), "..", ".env")
)

def get_connection():
    """Create a new MySQL connection."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        return connection
    except Error as e:
        print(f"Database connection failed: {e}")
        raise
