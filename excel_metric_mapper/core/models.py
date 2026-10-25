"""Data models for Excel Metric Mapper."""
from dataclasses import dataclass, field
from typing import Optional, Literal
from datetime import datetime


@dataclass
class SourceMetric:
    """A metric from the source data."""
    metric_id: str
    metric_name: str
    reporting_month: str  # YYYY-MM format
    value: float
    unit: str
    
    def __post_init__(self):
        """Ensure value is numeric."""
        if not isinstance(self.value, (int, float)):
            try:
                self.value = float(self.value)
            except (ValueError, TypeError):
                raise ValueError(f"Cannot convert value to float: {self.value}")


@dataclass
class MonthHeaderCandidate:
    """A potential month header cell in a workbook."""
    sheet_name: str
    cell_address: str
    row: int
    col: int
    raw_value: any
    normalized_month: str  # YYYY-MM format
    confidence: float  # 0-1
    orientation: Literal['horizontal', 'vertical']  # horizontal = month in column, vertical = month in row
    evidence: str
    
    def __hash__(self):
        return hash((self.sheet_name, self.cell_address, self.normalized_month))


@dataclass
class MetricLabelCandidate:
    """A potential metric label cell in a workbook."""
    sheet_name: str
    cell_address: str
    row: int
    col: int
    label_text: str
    matched_metric_id: Optional[str]
    matched_metric_name: Optional[str]
    match_score: float  # 0-1
    match_type: Literal['exact_id', 'exact_name', 'fuzzy_name', 'none']
    evidence: str
    
    def __hash__(self):
        return hash((self.sheet_name, self.cell_address, self.label_text))


@dataclass
class MappingCandidate:
    """A proposed mapping from source metric to target cell."""
    # Identifiers
    workbook_path: str
    workbook_name: str
    workbook_fingerprint: str
    sheet_name: str
    
    # Source metric
    metric_id: str
    metric_name: str
    source_value: float
    source_unit: str
    target_month: str  # YYYY-MM
    
    # Target location
    orientation: Literal['horizontal', 'vertical']
    metric_label_cell: str
    month_header_cell: str
    target_value_cell: str
    
    # Confidence and evidence
    confidence: float  # 0-1
    match_evidence: str
    
    # Existing cell info
    existing_value: Optional[any] = None
    has_formula: bool = False
    is_merged: bool = False
    
    # Status
    state: Literal['suggested', 'ambiguous', 'approved', 'rejected', 'blocked', 'applied', 'failed'] = 'suggested'
    
    # Additional metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __hash__(self):
        return hash((self.workbook_path, self.sheet_name, self.metric_id, self.target_month, self.target_value_cell))


@dataclass
class ApprovedMapping:
    """A user-approved mapping saved in the database."""
    id: Optional[int] = None
    workbook_fingerprint: str = ""
    sheet_name: str = ""
    metric_id: str = ""
    metric_name: str = ""
    target_month: str = ""
    orientation: Literal['horizontal', 'vertical'] = 'horizontal'
    metric_label_cell: str = ""
    month_header_cell: str = ""
    target_value_cell: str = ""
    confidence: float = 0.0
    evidence: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_successful_execution: Optional[datetime] = None


@dataclass
class ProposedChange:
    """A change ready to be written to a workbook."""
    workbook_path: str
    sheet_name: str
    target_cell: str
    metric_id: str
    metric_name: str
    source_value: float
    source_unit: str
    existing_value: Optional[any]
    existing_formula: Optional[str]
    has_formula: bool
    is_merged: bool
    proposed_value: float
    confidence: float
    warnings: list[str] = field(default_factory=list)


@dataclass
class ExecutionResult:
    """Result of writing changes to a workbook."""
    workbook_path: str
    output_path: str
    success: bool
    changes_applied: int
    changes_skipped: int
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
