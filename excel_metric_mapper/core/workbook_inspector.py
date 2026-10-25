"""Workbook inspection utilities."""
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
import openpyxl


class WorkbookInfo:
    """Container for workbook metadata."""
    
    def __init__(self, path: str):
        self.path = path
        self.name = Path(path).name
        self.fingerprint = self._calculate_fingerprint()
        self.sheets: Dict[str, SheetInfo] = {}
        self.is_macro_enabled = path.endswith('.xlsm')
        self.warnings: List[str] = []
    
    def _calculate_fingerprint(self) -> str:
        """Calculate a fingerprint based on file name and basic structure."""
        # For now, use filename + size as fingerprint
        # In production, could include sheet names and dimensions
        path = Path(self.path)
        size = path.stat().st_size if path.exists() else 0
        content = f"{path.name}:{size}"
        return hashlib.md5(content.encode()).hexdigest()


class SheetInfo:
    """Container for worksheet metadata."""
    
    def __init__(self, name: str):
        self.name = name
        self.max_row = 0
        self.max_col = 0
        self.merged_ranges: List[str] = []
        self.hidden = False
        self.has_formulas = False
        self.has_charts = False
        self.tables: List[str] = []
        self.named_ranges: List[str] = []


def inspect_workbook(path: str, deep_scan: bool = True) -> WorkbookInfo:
    """
    Inspect an Excel workbook and extract metadata.
    
    Args:
        path: Path to workbook
        deep_scan: If True, perform detailed cell scanning
    
    Returns:
        WorkbookInfo object with metadata
    """
    info = WorkbookInfo(path)
    
    try:
        # Load workbook
        keep_vba = path.endswith('.xlsm')
        wb = load_workbook(path, read_only=False, keep_vba=keep_vba, data_only=False)
        
        if keep_vba:
            info.warnings.append(
                "Macro-enabled workbook (.xlsm). Advanced Excel features may not be fully preserved."
            )
        
        # Inspect each sheet
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            sheet_info = SheetInfo(sheet_name)
            
            # Basic dimensions
            sheet_info.max_row = sheet.max_row
            sheet_info.max_col = sheet.max_column
            sheet_info.hidden = sheet.sheet_state == 'hidden'
            
            # Merged cells
            if hasattr(sheet, 'merged_cells'):
                sheet_info.merged_ranges = [str(merged_range) for merged_range in sheet.merged_cells.ranges]
            
            # Check for formulas and charts
            if deep_scan and sheet.max_row > 0:
                for row in sheet.iter_rows(max_row=min(sheet.max_row, 100)):
                    for cell in row:
                        if cell.value and isinstance(cell.value, str) and cell.value.startswith('='):
                            sheet_info.has_formulas = True
                            break
                    if sheet_info.has_formulas:
                        break
            
            # Charts
            if hasattr(sheet, '_charts') and sheet._charts:
                sheet_info.has_charts = True
            
            # Tables
            if hasattr(sheet, 'tables'):
                sheet_info.tables = list(sheet.tables.keys())
            
            info.sheets[sheet_name] = sheet_info
        
        # Named ranges (workbook level)
        if hasattr(wb, 'defined_names') and wb.defined_names:
            try:
                for name in wb.defined_names:
                    # Store at workbook level or distribute to sheets
                    pass
            except:
                pass  # Skip if named ranges can't be accessed
        
        wb.close()
        
    except Exception as e:
        info.warnings.append(f"Error inspecting workbook: {str(e)}")
    
    return info


def get_cell_value(sheet, row: int, col: int) -> Tuple[any, bool]:
    """
    Get cell value and whether it contains a formula.
    
    Args:
        sheet: openpyxl worksheet
        row: 1-indexed row number
        col: 1-indexed column number
    
    Returns:
        Tuple of (value, is_formula)
    """
    cell = sheet.cell(row=row, column=col)
    value = cell.value
    is_formula = isinstance(value, str) and value.startswith('=')
    return value, is_formula


def is_cell_merged(sheet, row: int, col: int) -> bool:
    """Check if a cell is part of a merged range."""
    cell_coordinate = f"{get_column_letter(col)}{row}"
    
    if hasattr(sheet, 'merged_cells'):
        for merged_range in sheet.merged_cells.ranges:
            if cell_coordinate in merged_range:
                return True
    
    return False


def get_merged_range_anchor(sheet, row: int, col: int) -> Optional[Tuple[int, int]]:
    """
    Get the top-left anchor cell of a merged range.
    
    Returns:
        Tuple of (row, col) for anchor, or None if not merged
    """
    cell_coordinate = f"{get_column_letter(col)}{row}"
    
    if hasattr(sheet, 'merged_cells'):
        for merged_range in sheet.merged_cells.ranges:
            if cell_coordinate in merged_range:
                # Get min row and col from range
                return merged_range.min_row, merged_range.min_col
    
    return None


def scan_worksheet_cells(
    sheet,
    max_rows: Optional[int] = None,
    max_cols: Optional[int] = None
) -> List[Dict]:
    """
    Scan worksheet cells and return non-empty cells with metadata.
    
    Args:
        sheet: openpyxl worksheet
        max_rows: Maximum rows to scan (None = all)
        max_cols: Maximum columns to scan (None = all)
    
    Returns:
        List of dicts with cell info
    """
    cells = []
    
    scan_rows = max_rows if max_rows else sheet.max_row
    scan_cols = max_cols if max_cols else sheet.max_column
    
    for row in range(1, scan_rows + 1):
        for col in range(1, scan_cols + 1):
            cell = sheet.cell(row=row, column=col)
            
            if cell.value is not None and cell.value != "":
                cell_info = {
                    'row': row,
                    'col': col,
                    'address': cell.coordinate,
                    'value': cell.value,
                    'is_formula': isinstance(cell.value, str) and cell.value.startswith('='),
                    'is_merged': is_cell_merged(sheet, row, col),
                    'data_type': cell.data_type,
                }
                cells.append(cell_info)
    
    return cells
