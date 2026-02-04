"""
SQLite-based persistent storage for MCP memory.
Stores episodic facts, conversation summaries, and user profiles across sessions.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager


class MemoryStorage:
    """
    Persistent storage layer for conversation memory.
    Uses SQLite for simplicity and portability.
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Store in backend/data directory
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, 'data')
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, 'memory.db')
        
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with self._get_conn() as conn:
            conn.executescript('''
                -- Episodic facts: specific facts learned about users
                CREATE TABLE IF NOT EXISTS episodic_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_id TEXT,
                    fact_type TEXT NOT NULL,
                    fact_key TEXT NOT NULL,
                    fact_value TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    source_turn INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(session_id, fact_type, fact_key)
                );
                
                -- Conversation summaries: compressed history
                CREATE TABLE IF NOT EXISTS conversation_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    turn_start INTEGER NOT NULL,
                    turn_end INTEGER NOT NULL,
                    summary TEXT NOT NULL,
                    key_topics TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(session_id, turn_start, turn_end)
                );
                
                -- User profiles: aggregated user information
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    profile_data TEXT NOT NULL,
                    total_sessions INTEGER DEFAULT 1,
                    total_turns INTEGER DEFAULT 0,
                    first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_seen TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Session metadata: track session-level info
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    start_time TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_activity TEXT DEFAULT CURRENT_TIMESTAMP,
                    turn_count INTEGER DEFAULT 0,
                    topics TEXT,
                    mood TEXT,
                    language TEXT DEFAULT 'hinglish'
                );
                
                -- Create indexes for fast lookups
                CREATE INDEX IF NOT EXISTS idx_facts_session ON episodic_facts(session_id);
                CREATE INDEX IF NOT EXISTS idx_facts_user ON episodic_facts(user_id);
                CREATE INDEX IF NOT EXISTS idx_summaries_session ON conversation_summaries(session_id);
            ''')
    
    @contextmanager
    def _get_conn(self):
        """Get database connection with auto-commit."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    # ===== SESSION OPERATIONS =====
    
    def create_or_update_session(
        self, 
        session_id: str, 
        user_id: str = None,
        language: str = 'hinglish'
    ) -> Dict[str, Any]:
        """Create or update session metadata."""
        with self._get_conn() as conn:
            now = datetime.now().isoformat()
            
            # Try to get existing session
            existing = conn.execute(
                'SELECT * FROM sessions WHERE session_id = ?',
                (session_id,)
            ).fetchone()
            
            if existing:
                conn.execute('''
                    UPDATE sessions 
                    SET last_activity = ?, turn_count = turn_count + 1
                    WHERE session_id = ?
                ''', (now, session_id))
                return dict(existing)
            else:
                conn.execute('''
                    INSERT INTO sessions (session_id, user_id, language, start_time, last_activity)
                    VALUES (?, ?, ?, ?, ?)
                ''', (session_id, user_id, language, now, now))
                return {
                    'session_id': session_id,
                    'user_id': user_id,
                    'language': language,
                    'turn_count': 0
                }
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session metadata."""
        with self._get_conn() as conn:
            row = conn.execute(
                'SELECT * FROM sessions WHERE session_id = ?',
                (session_id,)
            ).fetchone()
            return dict(row) if row else None
    
    # ===== EPISODIC FACTS =====
    
    def store_fact(
        self,
        session_id: str,
        fact_type: str,
        fact_key: str,
        fact_value: Any,
        user_id: str = None,
        confidence: float = 1.0,
        source_turn: int = None
    ):
        """Store or update an episodic fact."""
        with self._get_conn() as conn:
            now = datetime.now().isoformat()
            value_str = json.dumps(fact_value) if not isinstance(fact_value, str) else fact_value
            
            conn.execute('''
                INSERT INTO episodic_facts 
                (session_id, user_id, fact_type, fact_key, fact_value, confidence, source_turn, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id, fact_type, fact_key) 
                DO UPDATE SET 
                    fact_value = excluded.fact_value,
                    confidence = excluded.confidence,
                    updated_at = excluded.updated_at
            ''', (session_id, user_id, fact_type, fact_key, value_str, confidence, source_turn, now))
    
    def get_facts(
        self, 
        session_id: str, 
        fact_type: str = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get episodic facts for a session."""
        with self._get_conn() as conn:
            if fact_type:
                rows = conn.execute('''
                    SELECT * FROM episodic_facts 
                    WHERE session_id = ? AND fact_type = ?
                    ORDER BY updated_at DESC LIMIT ?
                ''', (session_id, fact_type, limit)).fetchall()
            else:
                rows = conn.execute('''
                    SELECT * FROM episodic_facts 
                    WHERE session_id = ?
                    ORDER BY updated_at DESC LIMIT ?
                ''', (session_id, limit)).fetchall()
            
            return [dict(row) for row in rows]
    
    def get_user_facts(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all facts for a user across sessions."""
        with self._get_conn() as conn:
            rows = conn.execute('''
                SELECT * FROM episodic_facts 
                WHERE user_id = ?
                ORDER BY updated_at DESC LIMIT ?
            ''', (user_id, limit)).fetchall()
            return [dict(row) for row in rows]
    
    # ===== CONVERSATION SUMMARIES =====
    
    def store_summary(
        self,
        session_id: str,
        turn_start: int,
        turn_end: int,
        summary: str,
        key_topics: List[str] = None
    ):
        """Store a conversation summary for a range of turns."""
        with self._get_conn() as conn:
            topics_str = json.dumps(key_topics) if key_topics else None
            
            conn.execute('''
                INSERT INTO conversation_summaries 
                (session_id, turn_start, turn_end, summary, key_topics)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(session_id, turn_start, turn_end) 
                DO UPDATE SET summary = excluded.summary, key_topics = excluded.key_topics
            ''', (session_id, turn_start, turn_end, summary, topics_str))
    
    def get_summaries(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all summaries for a session in chronological order."""
        with self._get_conn() as conn:
            rows = conn.execute('''
                SELECT * FROM conversation_summaries 
                WHERE session_id = ?
                ORDER BY turn_start ASC
            ''', (session_id,)).fetchall()
            
            results = []
            for row in rows:
                d = dict(row)
                if d.get('key_topics'):
                    d['key_topics'] = json.loads(d['key_topics'])
                results.append(d)
            return results
    
    # ===== USER PROFILES =====
    
    def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]):
        """Update aggregated user profile."""
        with self._get_conn() as conn:
            now = datetime.now().isoformat()
            profile_str = json.dumps(profile_data)
            
            existing = conn.execute(
                'SELECT * FROM user_profiles WHERE user_id = ?',
                (user_id,)
            ).fetchone()
            
            if existing:
                conn.execute('''
                    UPDATE user_profiles 
                    SET profile_data = ?, last_seen = ?, total_sessions = total_sessions + 1
                    WHERE user_id = ?
                ''', (profile_str, now, user_id))
            else:
                conn.execute('''
                    INSERT INTO user_profiles (user_id, profile_data, first_seen, last_seen)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, profile_str, now, now))
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile."""
        with self._get_conn() as conn:
            row = conn.execute(
                'SELECT * FROM user_profiles WHERE user_id = ?',
                (user_id,)
            ).fetchone()
            
            if row:
                d = dict(row)
                d['profile_data'] = json.loads(d['profile_data'])
                return d
            return None
    
    # ===== CLEANUP =====
    
    def clear_session(self, session_id: str):
        """Clear all memory data for a specific session."""
        with self._get_conn() as conn:
            conn.execute('DELETE FROM episodic_facts WHERE session_id = ?', (session_id,))
            conn.execute('DELETE FROM conversation_summaries WHERE session_id = ?', (session_id,))
            conn.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
    
    def cleanup_old_sessions(self, days: int = 30):
        """Remove sessions older than specified days."""
        with self._get_conn() as conn:
            cutoff = datetime.now().isoformat()[:10]  # Just date part
            
            # Get old session IDs
            old_sessions = conn.execute('''
                SELECT session_id FROM sessions 
                WHERE date(last_activity) < date(?, '-' || ? || ' days')
            ''', (cutoff, days)).fetchall()
            
            session_ids = [row['session_id'] for row in old_sessions]
            
            if session_ids:
                placeholders = ','.join('?' * len(session_ids))
                conn.execute(f'DELETE FROM episodic_facts WHERE session_id IN ({placeholders})', session_ids)
                conn.execute(f'DELETE FROM conversation_summaries WHERE session_id IN ({placeholders})', session_ids)
                conn.execute(f'DELETE FROM sessions WHERE session_id IN ({placeholders})', session_ids)
            
            return len(session_ids)


# Global instance
memory_storage = MemoryStorage()
