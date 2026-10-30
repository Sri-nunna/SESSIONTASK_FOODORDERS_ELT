"""MySQL connection and schema helpers."""
import mysql.connector
from mysql.connector import Error
from config import (
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD,
    RAW_DATABASE, ANALYTICS_DATABASE, SOURCE_COLUMNS
)

def server_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
        password=MYSQL_PASSWORD, autocommit=False
    )

def database_connection(database):
    return mysql.connector.connect(
        host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
        password=MYSQL_PASSWORD, database=database, autocommit=False
    )

def create_databases():
    conn = server_connection()
    try:
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{RAW_DATABASE}` CHARACTER SET utf8mb4")
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{ANALYTICS_DATABASE}` CHARACTER SET utf8mb4")
        conn.commit()
    finally:
        conn.close()

def create_raw_table():
    conn = database_connection(RAW_DATABASE)
    try:
        cur = conn.cursor()
        cols = ",\n".join(f"`{c}` LONGTEXT NULL" for c in SOURCE_COLUMNS)
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS raw_food_orders (
                source_row_number BIGINT NOT NULL PRIMARY KEY,
                {cols},
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()

def create_analytics_table():
    conn = database_connection(ANALYTICS_DATABASE)
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cleaned_food_orders (
                source_row_number BIGINT NOT NULL PRIMARY KEY,
                `Order ID` BIGINT NULL,
                `Customer ID` VARCHAR(40) NULL,
                `Restaurant ID` VARCHAR(40) NULL,
                `Order Date and Time` DATETIME NULL,
                `Delivery Date and Time` DATETIME NULL,
                `Order Value` DECIMAL(12,2) NULL,
                `Delivery Fee` DECIMAL(12,2) NULL,
                `Payment Method` VARCHAR(100) NULL,
                `Discounts and Offers` VARCHAR(150) NULL,
                `Commission Fee` DECIMAL(12,2) NULL,
                `Payment Processing Fee` DECIMAL(12,2) NULL,
                `Refunds/Chargebacks` DECIMAL(12,2) NULL,
                `Weather Condition` VARCHAR(80) NULL,
                `Order Channel` VARCHAR(80) NULL,
                `Delivery_Time_Minutes` DECIMAL(12,2) NULL,
                `Order_Date` DATE NULL,
                `Order_Hour` TINYINT NULL,
                `Platform_Net_Revenue` DECIMAL(12,2) NULL,
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_order_date (`Order_Date`),
                INDEX idx_restaurant (`Restaurant ID`)
            )
        """)
        conn.commit()
    finally:
        conn.close()
