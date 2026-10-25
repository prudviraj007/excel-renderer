"""Source data loader and validator."""
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, List
from .models import SourceMetric


class SourceDataError(Exception):
    """Error loading or validating source data."""
    pass


def load_source_data(
    file_path: str,
    sheet_name: Optional[str] = None,
    column_mapping: Optional[dict] = None
) -> Tuple[pd.DataFrame, List[SourceMetric]]:
    """
    Load source data from CSV or Excel file.
    
    Args:
        file_path: Path to source file
        sheet_name: Sheet name for Excel files
        column_mapping: Optional mapping from file columns to expected columns
    
    Returns:
        Tuple of (DataFrame, List of SourceMetric objects)
    
    Raises:
        SourceDataError: If data cannot be loaded or validated
    """
    path = Path(file_path)
    
    if not path.exists():
        raise SourceDataError(f"File not found: {file_path}")
    
    # Load data
    try:
        if path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path)
        elif path.suffix.lower() in ['.xlsx', '.xlsm', '.xls']:
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                df = pd.read_excel(file_path)
        else:
            raise SourceDataError(f"Unsupported file format: {path.suffix}")
    except Exception as e:
        raise SourceDataError(f"Failed to load file: {str(e)}")
    
    # Apply column mapping if provided
    if column_mapping:
        df = df.rename(columns=column_mapping)
    
    # Validate required columns
    required_columns = ['metric_id', 'metric_name', 'reporting_month', 'value', 'unit']
    missing_columns = set(required_columns) - set(df.columns)
    
    if missing_columns:
        raise SourceDataError(
            f"Missing required columns: {', '.join(missing_columns)}. "
            f"Available columns: {', '.join(df.columns)}"
        )
    
    # Filter to required columns
    df = df[required_columns].copy()
    
    # Remove rows with missing critical values
    initial_count = len(df)
    df = df.dropna(subset=['metric_id', 'reporting_month', 'value'])
    
    if len(df) == 0:
        raise SourceDataError("No valid rows after removing missing values")
    
    if len(df) < initial_count:
        print(f"Warning: Removed {initial_count - len(df)} rows with missing values")
    
    # Normalize metric_id and metric_name
    df['metric_id'] = df['metric_id'].astype(str).str.strip()
    df['metric_name'] = df['metric_name'].fillna('').astype(str).str.strip()
    df['unit'] = df['unit'].fillna('').astype(str).str.strip()
    
    # Convert value to numeric
    try:
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
    except Exception as e:
        raise SourceDataError(f"Failed to convert values to numeric: {str(e)}")
    
    # Remove rows with non-numeric values
    non_numeric_mask = df['value'].isna()
    if non_numeric_mask.any():
        bad_count = non_numeric_mask.sum()
        print(f"Warning: Removed {bad_count} rows with non-numeric values")
        df = df[~non_numeric_mask]
    
    if len(df) == 0:
        raise SourceDataError("No valid numeric values found")
    
    # Normalize reporting_month to YYYY-MM format
    from .month_parser import normalize_month
    
    df['reporting_month'] = df['reporting_month'].apply(normalize_month)
    
    # Remove rows with invalid months
    invalid_months = df['reporting_month'].isna()
    if invalid_months.any():
        bad_count = invalid_months.sum()
        print(f"Warning: Removed {bad_count} rows with invalid month formats")
        df = df[~invalid_months]
    
    if len(df) == 0:
        raise SourceDataError("No valid reporting months found")
    
    # Check for duplicates
    duplicate_mask = df.duplicated(subset=['metric_id', 'reporting_month'], keep=False)
    if duplicate_mask.any():
        duplicates = df[duplicate_mask][['metric_id', 'metric_name', 'reporting_month', 'value']]
        raise SourceDataError(
            f"Found {duplicate_mask.sum()} duplicate metric_id + reporting_month combinations:\n"
            f"{duplicates.to_string(index=False)}"
        )
    
    # Create SourceMetric objects
    metrics = []
    for _, row in df.iterrows():
        try:
            metric = SourceMetric(
                metric_id=row['metric_id'],
                metric_name=row['metric_name'],
                reporting_month=row['reporting_month'],
                value=float(row['value']),
                unit=row['unit']
            )
            metrics.append(metric)
        except Exception as e:
            print(f"Warning: Failed to create SourceMetric from row: {row.to_dict()} - {str(e)}")
    
    if not metrics:
        raise SourceDataError("No valid metrics created from source data")
    
    return df, metrics


def get_excel_sheets(file_path: str) -> List[str]:
    """Get list of sheet names from an Excel file."""
    try:
        xl_file = pd.ExcelFile(file_path)
        return xl_file.sheet_names
    except Exception as e:
        raise SourceDataError(f"Failed to read Excel sheets: {str(e)}")


def detect_column_mapping(df: pd.DataFrame) -> Optional[dict]:
    """
    Attempt to detect column mapping from source file to expected columns.
    Returns mapping dict if successful, None otherwise.
    """
    expected_columns = ['metric_id', 'metric_name', 'reporting_month', 'value', 'unit']
    
    # Common aliases
    aliases = {
        'metric_id': ['id', 'metric id', 'metricid', 'metric code', 'code'],
        'metric_name': ['name', 'metric name', 'metricname', 'metric', 'description'],
        'reporting_month': ['month', 'date', 'period', 'reporting period', 'report month'],
        'value': ['amount', 'quantity', 'measure', 'measurement'],
        'unit': ['units', 'uom', 'unit of measure']
    }
    
    mapping = {}
    available_columns = [col.lower().strip() for col in df.columns]
    
    for expected_col in expected_columns:
        # Check exact match (case-insensitive)
        if expected_col in available_columns:
            original_col = df.columns[available_columns.index(expected_col)]
            mapping[original_col] = expected_col
            continue
        
        # Check aliases
        found = False
        for alias in aliases.get(expected_col, []):
            if alias in available_columns:
                original_col = df.columns[available_columns.index(alias)]
                mapping[original_col] = expected_col
                found = True
                break
        
        if not found:
            return None  # Cannot auto-detect all columns
    
    return mapping if len(mapping) == len(expected_columns) else None
