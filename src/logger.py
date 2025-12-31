import sqlite3
import json
from datetime import datetime
import os

DB_PATH = "execution_logs.sqlite"

def init_log_db():
    """Initialize the execution logs table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            node_name TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            duration REAL,
            outcome TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_execution(session_id: str, node_name: str, start_time: float, end_time: float, outcome: any):
    """Log a node execution event to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    duration = end_time - start_time
    
    outcome_str = ""
    if isinstance(outcome, dict):
        try:
            outcome_str = json.dumps(outcome)
        except TypeError:
            outcome_str = str(outcome)
    else:
        outcome_str = str(outcome)

    cursor.execute("""
        INSERT INTO execution_logs (session_id, node_name, start_time, end_time, duration, outcome)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (session_id, node_name, datetime.fromtimestamp(start_time), datetime.fromtimestamp(end_time), duration, outcome_str))
    conn.commit()
    conn.close()

def get_logs_for_session(session_id: str):
    """Retrieve logs for a specific session."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT node_name, duration, outcome, start_time 
        FROM execution_logs 
        WHERE session_id = ? 
        ORDER BY id ASC
    """, (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows
