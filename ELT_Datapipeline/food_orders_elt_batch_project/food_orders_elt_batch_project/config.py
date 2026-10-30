"""Central configuration for the batch ELT pipeline."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_DIR = Path(__file__).resolve().parent
DATA_FILE = Path(os.getenv("FOOD_ORDERS_CSV", PROJECT_DIR / "data" / "food_orders.csv"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
RAW_DATABASE = os.getenv("RAW_DATABASE", "food_orders_raw_db")
ANALYTICS_DATABASE = os.getenv("ANALYTICS_DATABASE", "food_orders_analytics_db")

REPORT_DIR = Path(os.getenv("REPORT_DIR", PROJECT_DIR / "reports"))
REPORT_DIR.mkdir(parents=True, exist_ok=True)

SOURCE_COLUMNS = [
    "Order ID", "Customer ID", "Restaurant ID", "Order Date and Time",
    "Delivery Date and Time", "Order Value", "Delivery Fee", "Payment Method",
    "Discounts and Offers", "Commission Fee", "Payment Processing Fee",
    "Refunds/Chargebacks", "Weather Condition", "Order Channel"
]
DATETIME_COLUMNS = ["Order Date and Time", "Delivery Date and Time"]
FINANCIAL_COLUMNS = [
    "Order Value", "Delivery Fee", "Commission Fee",
    "Payment Processing Fee", "Refunds/Chargebacks"
]
CATEGORY_COLUMNS = [
    "Payment Method", "Discounts and Offers",
    "Weather Condition", "Order Channel"
]
