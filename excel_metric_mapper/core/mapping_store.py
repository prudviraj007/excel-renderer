"""SQLite-based mapping storage."""
import sqlite3
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from .models import ApprovedMapping, MappingCandidate


class MappingStore:
    """Persistent storage for approved mappings."""
    
    def __init__(self, db_path: str = "mappings.db"):
        """Initialize the mapping store."""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workbook_fingerprint TEXT NOT NULL,
                    sheet_name TEXT NOT NULL,
                    metric_id TEXT NOT NULL,
                    metric_name TEXT,
                    target_month TEXT,
                    orientation TEXT,
                    metric_label_cell TEXT,
                    month_header_cell TEXT,
                    target_value_cell TEXT,
                    confidence REAL,
                    evidence TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    last_successful_execution TEXT,
                    UNIQUE(workbook_fingerprint, sheet_name, metric_id, target_month)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_fingerprint 
                ON mappings(workbook_fingerprint)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_metric 
                ON mappings(metric_id)
            """)
    
    def save_mapping(self, mapping: MappingCandidate) -> int:
        """
        Save or update an approved mapping.
        
        Returns:
            Mapping ID
        """
        with sqlite3.connect(self.db_path) as conn:
            now = datetime.now().isoformat()
            
            cursor = conn.execute("""
                INSERT INTO mappings (
                    workbook_fingerprint, sheet_name, metric_id, metric_name,
                    target_month, orientation, metric_label_cell, month_header_cell,
                    target_value_cell, confidence, evidence, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(workbook_fingerprint, sheet_name, metric_id, target_month)
                DO UPDATE SET
                    metric_name = excluded.metric_name,
                    orientation = excluded.orientation,
                    metric_label_cell = excluded.metric_label_cell,
                    month_header_cell = excluded.month_header_cell,
                    target_value_cell = excluded.target_value_cell,
                    confidence = excluded.confidence,
                    evidence = excluded.evidence,
                    updated_at = excluded.updated_at
            """, (
                mapping.workbook_fingerprint,
                mapping.sheet_name,
                mapping.metric_id,
                mapping.metric_name,
                mapping.target_month,
                mapping.orientation,
                mapping.metric_label_cell,
                mapping.month_header_cell,
                mapping.target_value_cell,
                mapping.confidence,
                mapping.match_evidence,
                now,
                now
            ))
            
            # Get the ID of the inserted/updated row
            mapping_id = cursor.lastrowid
            if mapping_id == 0:
                # Was an update, fetch the ID
                cursor = conn.execute("""
                    SELECT id FROM mappings 
                    WHERE workbook_fingerprint = ? 
                    AND sheet_name = ? 
                    AND metric_id = ?
                    AND target_month = ?
                """, (
                    mapping.workbook_fingerprint,
                    mapping.sheet_name,
                    mapping.metric_id,
                    mapping.target_month
                ))
                row = cursor.fetchone()
                mapping_id = row[0] if row else 0
            
            return mapping_id
    
    def get_mappings(
        self,
        workbook_fingerprint: Optional[str] = None,
        sheet_name: Optional[str] = None,
        metric_id: Optional[str] = None
    ) -> List[ApprovedMapping]:
        """Retrieve mappings with optional filters."""
        query = "SELECT * FROM mappings WHERE 1=1"
        params = []
        
        if workbook_fingerprint:
            query += " AND workbook_fingerprint = ?"
            params.append(workbook_fingerprint)
        
        if sheet_name:
            query += " AND sheet_name = ?"
            params.append(sheet_name)
        
        if metric_id:
            query += " AND metric_id = ?"
            params.append(metric_id)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            mappings = []
            for row in rows:
                mapping = ApprovedMapping(
                    id=row['id'],
                    workbook_fingerprint=row['workbook_fingerprint'],
                    sheet_name=row['sheet_name'],
                    metric_id=row['metric_id'],
                    metric_name=row['metric_name'],
                    target_month=row['target_month'],
                    orientation=row['orientation'],
                    metric_label_cell=row['metric_label_cell'],
                    month_header_cell=row['month_header_cell'],
                    target_value_cell=row['target_value_cell'],
                    confidence=row['confidence'],
                    evidence=row['evidence'],
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None,
                    last_successful_execution=datetime.fromisoformat(row['last_successful_execution']) if row['last_successful_execution'] else None
                )
                mappings.append(mapping)
            
            return mappings
    
    def update_execution_time(self, mapping_id: int):
        """Update the last successful execution time for a mapping."""
        with sqlite3.connect(self.db_path) as conn:
            now = datetime.now().isoformat()
            conn.execute("""
                UPDATE mappings 
                SET last_successful_execution = ?
                WHERE id = ?
            """, (now, mapping_id))
    
    def delete_mapping(self, mapping_id: int):
        """Delete a mapping."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM mappings WHERE id = ?", (mapping_id,))
    
    def clear_all(self):
        """Clear all mappings (for testing)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM mappings")
