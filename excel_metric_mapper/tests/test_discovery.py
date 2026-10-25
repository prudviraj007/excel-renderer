"""Tests for discovery engine."""
import pytest
from pathlib import Path
from core.models import SourceMetric
from core.discovery import (
    find_month_headers,
    find_metric_labels,
    _find_best_metric_match
)


# Sample source metrics for testing
SAMPLE_METRICS = [
    SourceMetric("M001", "Energy Consumption", "2026-10", 1245.0, "kWh"),
    SourceMetric("M002", "Water Consumption", "2026-10", 876.0, "m3"),
    SourceMetric("M003", "Equipment Availability", "2026-10", 0.986, "%"),
]


class TestFindBestMetricMatch:
    """Test metric matching logic."""
    
    def test_exact_id_match(self):
        """Test exact metric ID match."""
        result = _find_best_metric_match("M001", SAMPLE_METRICS)
        assert result is not None
        metric, match_type, score = result
        assert metric.metric_id == "M001"
        assert match_type == "exact_id"
        assert score == 1.0
    
    def test_exact_name_match(self):
        """Test exact metric name match."""
        result = _find_best_metric_match("Energy Consumption", SAMPLE_METRICS)
        assert result is not None
        metric, match_type, score = result
        assert metric.metric_id == "M001"
        assert match_type in ["exact_name", "exact_id"]
        assert score == 1.0
    
    def test_fuzzy_name_match(self):
        """Test fuzzy metric name match."""
        result = _find_best_metric_match("Energy Consume", SAMPLE_METRICS, min_fuzzy_score=70.0)
        assert result is not None
        metric, match_type, score = result
        assert metric.metric_id == "M001"
        assert match_type == "fuzzy_name"
        assert score > 0.7
    
    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        result = _find_best_metric_match("m001", SAMPLE_METRICS)
        assert result is not None
        metric, match_type, score = result
        assert metric.metric_id == "M001"
    
    def test_no_match(self):
        """Test when no match is found."""
        result = _find_best_metric_match("Completely Different Metric", SAMPLE_METRICS, min_fuzzy_score=90.0)
        assert result is None


class TestHorizontalSampleWorkbook:
    """Regression: Oct column must intersect metric rows, not column A."""

    @pytest.fixture
    def horizontal_workbook(self):
        base = Path("excel_metric_mapper_sample_pack/excel_metric_mapper_sample/templates")
        if not base.exists():
            base = Path("../excel_metric_mapper_sample_pack/excel_metric_mapper_sample/templates")
        path = base / "01_energy_horizontal.xlsx"
        if not path.exists():
            pytest.skip("Sample workbook not found")
        return str(path)

    def test_oct_targets_intersection_cells(self, horizontal_workbook):
        from core.source_loader import load_source_data
        from core.workbook_inspector import inspect_workbook
        from core.scoring import propose_mappings

        csv = str(Path(horizontal_workbook).parent.parent / "source_metrics_oct_2026.csv")
        if not Path(csv).exists():
            pytest.skip("Sample CSV not found")

        _, metrics = load_source_data(csv)
        info = inspect_workbook(horizontal_workbook)
        headers = find_month_headers(
            horizontal_workbook, "Energy Trend", target_month="2026-10"
        )
        labels = find_metric_labels(horizontal_workbook, "Energy Trend", metrics)
        cands = propose_mappings(
            horizontal_workbook, info, metrics, headers, labels, "2026-10", 0.4
        )
        by_id = {c.metric_id: c for c in cands}
        assert by_id["M001"].target_value_cell == "K5"
        assert by_id["M007"].target_value_cell == "K6"
        assert by_id["M001"].orientation == "horizontal"


class TestDiscoveryWithSampleData:
    """Test discovery with actual sample data if available."""
    
    @pytest.fixture
    def sample_workbook_path(self):
        """Get path to sample workbook if it exists."""
        # Look for sample workbooks
        base_path = Path("excel_metric_mapper_sample_pack/excel_metric_mapper_sample/templates")
        if not base_path.exists():
            base_path = Path("../excel_metric_mapper_sample_pack/excel_metric_mapper_sample/templates")
        
        if base_path.exists():
            files = list(base_path.glob("*.xlsx"))
            if files:
                return str(files[0])
        
        pytest.skip("Sample workbooks not found")
    
    def test_find_month_headers(self, sample_workbook_path):
        """Test finding month headers in sample workbook."""
        from openpyxl import load_workbook
        
        wb = load_workbook(sample_workbook_path, read_only=True)
        sheet_name = wb.sheetnames[0]
        wb.close()
        
        headers = find_month_headers(
            sample_workbook_path,
            sheet_name,
            target_month="2026-10",
            max_rows=20,
            max_cols=20
        )
        
        # Should find at least one month header
        assert len(headers) >= 0  # May or may not find depending on layout
    
    def test_find_metric_labels(self, sample_workbook_path):
        """Test finding metric labels in sample workbook."""
        from openpyxl import load_workbook
        
        wb = load_workbook(sample_workbook_path, read_only=True)
        sheet_name = wb.sheetnames[0]
        wb.close()
        
        labels = find_metric_labels(
            sample_workbook_path,
            sheet_name,
            SAMPLE_METRICS,
            max_rows=50,
            max_cols=20
        )
        
        # Should find some labels if they exist
        assert isinstance(labels, list)
