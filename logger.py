#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logging module for Martin Autofulfill
Manages operation logging to CSV and text log files
"""

import os
import csv
from datetime import datetime
import logging

# Configure directories
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Configure log file paths
CSV_LOG_FILE = os.path.join(LOG_DIR, "operations.csv")
LOG_FILE = os.path.join(LOG_DIR, "martin_autofulfill.log")

# Configure Python's default logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def initialize_csv_log():
    """Initialize the CSV log file if it doesn't exist"""
    if not os.path.exists(CSV_LOG_FILE):
        with open(CSV_LOG_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                'datetime',
                'order_id',
                'order_number',
                'customer',
                'operation',
                'result',
                'details'
            ])

def log_operation(order_id, order_number, customer, operation, result, details=""):
    """
    Log an operation to the CSV log file

    Args:
        order_id (int/str): Order ID
        order_number (str): Formatted order number (e.g., #1001)
        customer (str): Customer name
        operation (str): Operation type (e.g., process, ignore)
        result (str): Operation result (success or error)
        details (str): Additional operation details
    """
    # Ensure the file exists
    initialize_csv_log()

    # Current date and time
    datetime_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Write to CSV
    with open(CSV_LOG_FILE, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([
            datetime_str,
            order_id,
            order_number,
            customer,
            operation,
            result,
            details
        ])

    # Also log to system log
    status = "✅" if result == "success" else "❌"
    logger.info(f"{status} {operation.upper()} - Order {order_number} - Customer: {customer} - {result}")
    if details:
        logger.info(f"    Details: {details}")

def log_error(message, order_id=None, order_number=None):
    """
    Log an error message

    Args:
        message (str): Error message
        order_id (int/str): Order ID, if applicable
        order_number (str): Order number, if applicable
    """
    if order_id and order_number:
        logger.error(f"ERROR - Order {order_number} (ID: {order_id}): {message}")
    else:
        logger.error(f"ERROR: {message}")
