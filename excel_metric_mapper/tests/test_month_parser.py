"""Tests for month parser."""
import pytest
from datetime import datetime, date
from core.month_parser import normalize_month, is_likely_month_value


class TestNormalizeMonth:
    """Test month normalization."""
    
    def test_iso_format_yyyy_mm(self):
        """Test YYYY-MM format."""
        assert normalize_month("2026-10") == "2026-10"
        assert normalize_month("2023-01") == "2023-01"
    
    def test_iso_format_yyyy_mm_dd(self):
        """Test YYYY-MM-DD format."""
        assert normalize_month("2026-10-15") == "2026-10"
        assert normalize_month("2023-01-01") == "2023-01"
    
    def test_datetime_objects(self):
        """Test datetime and date objects."""
        assert normalize_month(datetime(2026, 10, 1)) == "2026-10"
        assert normalize_month(date(2026, 10, 15)) == "2026-10"
    
    def test_excel_date_numbers(self):
        """Test Excel serial date numbers."""
        # Excel date 44927 = 2023-01-01
        # Excel date 46385 = 2026-12-01
        result = normalize_month(44927)
        assert result is not None  # Should parse to some valid month
        assert len(result) == 7  # YYYY-MM format
    
    def test_month_abbreviations(self):
        """Test month abbreviation formats."""
        assert normalize_month("Jan-26") == "2026-01"
        assert normalize_month("Oct'26") == "2026-10"
        assert normalize_month("Dec-23") == "2023-12"
    
    def test_month_names_with_year(self):
        """Test full month names with year."""
        assert normalize_month("October 2026") == "2026-10"
        assert normalize_month("Jan 2026") == "2026-01"
    
    def test_invalid_inputs(self):
        """Test invalid inputs return None."""
        assert normalize_month(None) is None
        assert normalize_month("") is None
        assert normalize_month("not a date") is None
        assert normalize_month(123) is None  # Not a valid Excel date
        assert normalize_month("xyz-abc") is None


class TestIsLikelyMonthValue:
    """Test month detection."""
    
    def test_detects_datetime(self):
        """Test detection of datetime objects."""
        assert is_likely_month_value(datetime(2026, 10, 1))
        assert is_likely_month_value(date(2026, 10, 15))
    
    def test_detects_iso_strings(self):
        """Test detection of ISO date strings."""
        assert is_likely_month_value("2026-10")
        assert is_likely_month_value("2026-10-15")
    
    def test_detects_month_names(self):
        """Test detection of month names."""
        assert is_likely_month_value("October")
        assert is_likely_month_value("Oct")
        assert is_likely_month_value("October 2026")
        assert is_likely_month_value("Oct-26")
    
    def test_detects_excel_dates(self):
        """Test detection of Excel date numbers."""
        assert is_likely_month_value(44927)
        assert is_likely_month_value(46385)
    
    def test_rejects_invalid(self):
        """Test rejection of invalid values."""
        assert not is_likely_month_value(None)
        assert not is_likely_month_value("")
        assert not is_likely_month_value(123)  # Too small for Excel date
        assert not is_likely_month_value(100000)  # Too large
        assert not is_likely_month_value("random text")
