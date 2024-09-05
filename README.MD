# Inventory Management System

This is a simple inventory management system built using FastAPI, Streamlit, and SQLite3.

## Project Structure

```
inventory_management_system/
│
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── database.py             # Database models and setup using SQLAlchemy
│   ├── util.py                 # Utility functions
│   ├── __init__.py             # Initialize the backend module
│   └── requirements.txt        # Backend dependencies (FastAPI, SQLAlchemy, etc.)
│
├── frontend/
│   ├── app.py                  # Streamlit application
│   ├── __init__.py             # Initialize the frontend module
│   └── requirements.txt        # Frontend dependencies (Streamlit, requests, etc.)
│
├── inventory.db                # SQLite database file (auto-generated)
│
├── .env                        # ENV file to store sensitive information (e.g., PASSWORD)
│
├── .gitignore                  # Git ignore file to ignore unnecessary files (e.g., inventory.db, __pycache__)
│
└── README.md                   # Project documentation

```


## Setup Instructions

### Backend (FastAPI)

1. Navigate to the `backend` directory:

    ```bash
    cd backend
    ```

2. Create a virtual environment and activate it:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Run the FastAPI server:

    ```bash
    uvicorn main:app --reload
    ```

### Frontend (Streamlit)

1. Navigate to the `frontend` directory:

    ```bash
    cd frontend
    ```

2. Create a virtual environment and activate it:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Run the Streamlit app:

    ```bash
    streamlit run app.py
    ```

## Usage

- Access the FastAPI documentation at `http://127.0.0.1:8000/docs`.
- Access the Streamlit app at `http://localhost:8501`.

## Features

- **Category Management**: 
    - Create, view, and update categories, with each category displaying its creation date. 
    - Categories can also be deleted when no longer needed.

- **Item Management**: 
    - Create, view, edit, delete, and search for items by name or description. 
    - Items include fields for quantity, category, and creation/last updated dates to track changes. 
    - Detailed logging tracks modifications to items, including changes in quantity and other fields.

- **Error Handling**: 
    - Provides clear and user-friendly error messages for failed operations, including specific error 
      handling for missing categories, items, or server errors.

- **Export Data to CSV**: 
    - The application allows users to export inventory data to CSV format for easy reporting, sharing, 
      or backup. 
    - Items within categories and search results can be downloaded directly from the web interface 
      using the "Download as CSV" button, available in both the category view and search results.

- **Action Logging**: 
    - The system logs key actions such as item creation, updates, and deletions.
    - Logs track changes made to items, including old and new values for fields such as name, 
      description, quantity, and category.

## Notes

- The project uses a simple password authentication for the Streamlit app. Update the password in `.env` as required.
- Make sure to start the FastAPI server before running the Streamlit app to ensure the frontend can communicate with the backend.
