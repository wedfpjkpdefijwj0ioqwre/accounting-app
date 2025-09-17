# Accounting App

A simple web-based accounting application built with Python Flask and SQLite that allows you to track income and expenses with Excel import/export functionality.

## Features

- Add, view, and delete financial transactions
- Categorize transactions (income/expense)
- View current balance
- Export transactions to Excel
- Import transactions from Excel
- Responsive design for mobile and desktop

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation

1. Clone the repository or download the source code

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. Start the Flask development server:
   ```bash
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

## Excel Import Format

When importing transactions from Excel, make sure your file has the following columns:
- Date (YYYY-MM-DD format)
- Description (text)
- Amount (number)
- Category (text)
- Type (must be either 'income' or 'expense')

## License

This project is open source and available under the [MIT License](LICENSE).

## Screenshots

![Dashboard](screenshots/dashboard.png)
*Transaction list and balance overview*

![Add Transaction](screenshots/add-transaction.png)
*Add a new transaction form*
