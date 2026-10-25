"""Tests for writer functionality."""
import pytest
from pathlib import Path
import tempfile
import shutil
from openpyxl import Workbook
from core.writer import write_changes, prepare_proposed_changes, _parse_cell_address
from core.models import ProposedChange, MappingCandidate


class TestParseCellAddress:
    """Test cell address parsing."""
    
    def test_simple_cell(self):
        """Test simple cell addresses."""
        assert _parse_cell_address("A1") == (1, 1)
        assert _parse_cell_address("B5") == (5, 2)
        assert _parse_cell_address("Z10") == (10, 26)
    
    def test_multi_letter_column(self):
        """Test multi-letter column addresses."""
        assert _parse_cell_address("AA1") == (1, 27)
        assert _parse_cell_address("AB10") == (10, 28)
    
    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert _parse_cell_address("a1") == (1, 1)
        assert _parse_cell_address("b5") == (5, 2)


class TestWriteChanges:
    """Test writing changes to workbooks."""
    
    @pytest.fixture
    def temp_workbook(self):
        """Create a temporary test workbook."""
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            wb = Workbook()
            sheet = wb.active
            sheet.title = "Sheet1"
            
            # Add some data
            sheet['A1'] = "Metric"
            sheet['B1'] = "October 2026"
            sheet['A2'] = "Energy Consumption"
            sheet['B2'] = 1000.0  # Existing value
            sheet['A3'] = "Water Consumption"
            sheet['B3'] = None  # Empty cell
            
            wb.save(tmp.name)
            wb.close()
            
            yield tmp.name
            
            # Cleanup
            Path(tmp.name).unlink(missing_ok=True)
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_write_simple_change(self, temp_workbook, temp_output_dir):
        """Test writing a simple change."""
        change = ProposedChange(
            workbook_path=temp_workbook,
            sheet_name="Sheet1",
            target_cell="B2",
            metric_id="M001",
            metric_name="Energy Consumption",
            source_value=1245.0,
            source_unit="kWh",
            existing_value=1000.0,
            existing_formula=None,
            has_formula=False,
            is_merged=False,
            proposed_value=1245.0,
            confidence=0.95
        )
        
        result = write_changes(
            workbook_path=temp_workbook,
            changes=[change],
            output_dir=temp_output_dir,
            dry_run=False
        )
        
        assert result.success
        assert result.changes_applied == 1
        assert result.changes_skipped == 0
        assert Path(result.output_path).exists()
    
    def test_dry_run(self, temp_workbook, temp_output_dir):
        """Test dry run mode."""
        change = ProposedChange(
            workbook_path=temp_workbook,
            sheet_name="Sheet1",
            target_cell="B3",
            metric_id="M002",
            metric_name="Water Consumption",
            source_value=876.0,
            source_unit="m3",
            existing_value=None,
            existing_formula=None,
            has_formula=False,
            is_merged=False,
            proposed_value=876.0,
            confidence=0.90
        )
        
        result = write_changes(
            workbook_path=temp_workbook,
            changes=[change],
            output_dir=temp_output_dir,
            dry_run=True
        )
        
        assert result.success
        assert "DRY RUN" in result.warnings[0]
    
    def test_skip_formula_cells(self, temp_workbook, temp_output_dir):
        """Test that formula cells are skipped."""
        change = ProposedChange(
            workbook_path=temp_workbook,
            sheet_name="Sheet1",
            target_cell="B2",
            metric_id="M001",
            metric_name="Energy Consumption",
            source_value=1245.0,
            source_unit="kWh",
            existing_value="=SUM(A1:A10)",
            existing_formula="=SUM(A1:A10)",
            has_formula=True,
            is_merged=False,
            proposed_value=1245.0,
            confidence=0.95
        )
        
        result = write_changes(
            workbook_path=temp_workbook,
            changes=[change],
            output_dir=temp_output_dir,
            dry_run=False
        )
        
        # Should skip the change
        assert result.changes_skipped == 1


class TestPrepareProposedChanges:
    """Test preparing proposed changes from candidates."""
    
    def test_prepare_approved_candidates(self):
        """Test preparing changes from approved candidates."""
        candidate = MappingCandidate(
            workbook_path="/path/to/workbook.xlsx",
            workbook_name="workbook.xlsx",
            workbook_fingerprint="abc123",
            sheet_name="Sheet1",
            metric_id="M001",
            metric_name="Energy Consumption",
            source_value=1245.0,
            source_unit="kWh",
            target_month="2026-10",
            orientation="horizontal",
            metric_label_cell="A2",
            month_header_cell="B1",
            target_value_cell="B2",
            confidence=0.95,
            match_evidence="Test evidence",
            existing_value=None,
            has_formula=False,
            is_merged=False,
            state='approved'
        )
        
        changes = prepare_proposed_changes([candidate])
        
        assert len(changes) == 1
        assert changes[0].target_cell == "B2"
        assert changes[0].proposed_value == 1245.0
    
    def test_skip_non_approved(self):
        """Test that non-approved candidates are skipped."""
        candidate = MappingCandidate(
            workbook_path="/path/to/workbook.xlsx",
            workbook_name="workbook.xlsx",
            workbook_fingerprint="abc123",
            sheet_name="Sheet1",
            metric_id="M001",
            metric_name="Energy Consumption",
            source_value=1245.0,
            source_unit="kWh",
            target_month="2026-10",
            orientation="horizontal",
            metric_label_cell="A2",
            month_header_cell="B1",
            target_value_cell="B2",
            confidence=0.95,
            match_evidence="Test evidence",
            state='suggested'  # Not approved
        )
        
        changes = prepare_proposed_changes([candidate])
        
        assert len(changes) == 0
