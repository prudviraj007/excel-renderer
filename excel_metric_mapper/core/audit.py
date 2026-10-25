"""Audit logging for changes."""
import csv
import sqlite3
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from .models import ProposedChange, ExecutionResult, MappingCandidate


class AuditLogger:
    """Audit logger for tracking all changes."""
    
    def __init__(self, db_path: str = "audit.db"):
        """Initialize the audit logger."""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Create audit table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    workbook_path TEXT NOT NULL,
                    sheet_name TEXT NOT NULL,
                    metric_id TEXT NOT NULL,
                    metric_name TEXT,
                    reporting_month TEXT,
                    target_cell TEXT,
                    old_value TEXT,
                    new_value REAL,
                    decision TEXT,
                    confidence REAL,
                    user_approved BOOLEAN,
                    outcome TEXT,
                    error TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON audit_log(timestamp DESC)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_workbook 
                ON audit_log(workbook_path)
            """)
    
    def log_proposal(self, candidate: MappingCandidate):
        """Log a proposed mapping."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO audit_log (
                    timestamp, workbook_path, sheet_name, metric_id, metric_name,
                    reporting_month, target_cell, old_value, new_value,
                    decision, confidence, user_approved, outcome
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                candidate.workbook_path,
                candidate.sheet_name,
                candidate.metric_id,
                candidate.metric_name,
                candidate.target_month,
                candidate.target_value_cell,
                str(candidate.existing_value) if candidate.existing_value is not None else None,
                candidate.source_value,
                candidate.state,
                candidate.confidence,
                candidate.state == 'approved',
                'proposed'
            ))
    
    def log_change(self, change: ProposedChange, success: bool, error: Optional[str] = None):
        """Log an applied change."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO audit_log (
                    timestamp, workbook_path, sheet_name, metric_id, metric_name,
                    reporting_month, target_cell, old_value, new_value,
                    decision, confidence, user_approved, outcome, error
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                change.workbook_path,
                change.sheet_name,
                change.metric_id,
                change.metric_name,
                None,  # reporting_month not in ProposedChange
                change.target_cell,
                str(change.existing_value) if change.existing_value is not None else None,
                change.proposed_value,
                'applied',
                change.confidence,
                True,
                'success' if success else 'failed',
                error
            ))
    
    def log_execution(self, result: ExecutionResult):
        """Log execution result."""
        with sqlite3.connect(self.db_path) as conn:
            # Log summary
            conn.execute("""
                INSERT INTO audit_log (
                    timestamp, workbook_path, sheet_name, metric_id, metric_name,
                    reporting_month, target_cell, old_value, new_value,
                    decision, confidence, user_approved, outcome, error
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.timestamp.isoformat(),
                result.workbook_path,
                'EXECUTION_SUMMARY',
                '',
                f"Applied: {result.changes_applied}, Skipped: {result.changes_skipped}",
                None,
                result.output_path,
                None,
                None,
                'execution',
                None,
                None,
                'success' if result.success else 'failed',
                '; '.join(result.errors) if result.errors else None
            ))
    
    def export_to_csv(self, output_path: str, start_date: Optional[str] = None):
        """Export audit log to CSV."""
        query = "SELECT * FROM audit_log"
        params = []
        
        if start_date:
            query += " WHERE timestamp >= ?"
            params.append(start_date)
        
        query += " ORDER BY timestamp DESC"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            if not rows:
                return
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                for row in rows:
                    writer.writerow(dict(row))
    
    def get_recent_logs(self, limit: int = 100) -> List[dict]:
        """Get recent audit log entries."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM audit_log 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
