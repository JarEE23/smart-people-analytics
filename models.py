import sqlite3
import os
import json
from pathlib import Path
from config import Config

def get_db_path():
    db_path = Path(Config.DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return str(db_path)

def get_db_connection():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS count_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    occurred_at TEXT NOT NULL,
    direction TEXT NOT NULL
        CHECK (direction IN ('IN', 'OUT')),
    track_id TEXT,
    confidence REAL
        CHECK (
            confidence IS NULL
            OR (confidence >= 0 AND confidence <= 1)
        ),
    source TEXT NOT NULL DEFAULT 'SIMULATED'
        CHECK (source IN ('SIMULATED', 'YOLO')),
    camera_id TEXT NOT NULL DEFAULT 'CAM-01',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_events_time
ON count_events (occurred_at);

CREATE INDEX IF NOT EXISTS idx_events_direction_time
ON count_events (direction, occurred_at);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT 'Percakapan baru',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL
        CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    evidence_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id)
        REFERENCES chat_sessions(id)
        ON DELETE CASCADE
);
"""

def init_db():
    conn = get_db_connection()
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()

# Event Data Access Helpers
def insert_event(occurred_at, direction, track_id=None, confidence=None, source='SIMULATED', camera_id='CAM-01'):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO count_events (occurred_at, direction, track_id, confidence, source, camera_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (occurred_at, direction, track_id, confidence, source, camera_id))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

def insert_events_batch(events):
    """Batch insert a list of event tuples or dicts"""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.executemany("""
            INSERT INTO count_events (occurred_at, direction, track_id, confidence, source, camera_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [(
            e['occurred_at'],
            e['direction'],
            e.get('track_id'),
            e.get('confidence'),
            e.get('source', 'SIMULATED'),
            e.get('camera_id', 'CAM-01')
        ) for e in events])
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()

def get_events(limit=50, offset=0, start_date=None, end_date=None, direction=None, source=None, camera_id=None):
    conn = get_db_connection()
    try:
        query = "SELECT * FROM count_events WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND occurred_at >= ?"
            params.append(f"{start_date} 00:00:00" if len(start_date) == 10 else start_date)
        if end_date:
            query += " AND occurred_at <= ?"
            params.append(f"{end_date} 23:59:59" if len(end_date) == 10 else end_date)
        if direction and direction.upper() in ('IN', 'OUT'):
            query += " AND direction = ?"
            params.append(direction.upper())
        if source and source.upper() in ('SIMULATED', 'YOLO'):
            query += " AND source = ?"
            params.append(source.upper())
        if camera_id:
            query += " AND camera_id = ?"
            params.append(camera_id)
            
        query += " ORDER BY occurred_at DESC, id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def count_filtered_events(start_date=None, end_date=None, direction=None, source=None, camera_id=None):
    conn = get_db_connection()
    try:
        query = "SELECT COUNT(*) as total FROM count_events WHERE 1=1"
        params = []
        
        if start_date:
            query += " AND occurred_at >= ?"
            params.append(f"{start_date} 00:00:00" if len(start_date) == 10 else start_date)
        if end_date:
            query += " AND occurred_at <= ?"
            params.append(f"{end_date} 23:59:59" if len(end_date) == 10 else end_date)
        if direction and direction.upper() in ('IN', 'OUT'):
            query += " AND direction = ?"
            params.append(direction.upper())
        if source and source.upper() in ('SIMULATED', 'YOLO'):
            query += " AND source = ?"
            params.append(source.upper())
        if camera_id:
            query += " AND camera_id = ?"
            params.append(camera_id)
            
        row = conn.execute(query, params).fetchone()
        return row['total'] if row else 0
    finally:
        conn.close()

# Chat Data Access Helpers
def create_chat_session(session_id, title="Percakapan baru"):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO chat_sessions (id, title) VALUES (?, ?)", (session_id, title))
        conn.commit()
        return session_id
    finally:
        conn.close()

def get_chat_sessions():
    conn = get_db_connection()
    try:
        rows = conn.execute("SELECT * FROM chat_sessions ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def get_chat_session(session_id):
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def insert_chat_message(session_id, role, content, evidence_json=None):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO chat_messages (session_id, role, content, evidence_json)
            VALUES (?, ?, ?, ?)
        """, (session_id, role, content, evidence_json))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

def get_chat_messages(session_id):
    conn = get_db_connection()
    try:
        rows = conn.execute("""
            SELECT * FROM chat_messages 
            WHERE session_id = ? 
            ORDER BY created_at ASC, id ASC
        """, (session_id,)).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            if d.get('evidence_json'):
                try:
                    d['evidence'] = json.loads(d['evidence_json'])
                except Exception:
                    d['evidence'] = None
            else:
                d['evidence'] = None
            result.append(d)
        return result
    finally:
        conn.close()

def delete_chat_session(session_id):
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
        conn.commit()
    finally:
        conn.close()
