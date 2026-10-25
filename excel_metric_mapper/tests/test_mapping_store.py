"""Tests for mapping store."""
import pytest
import tempfile
from pathlib import Path
from core.mapping_store import MappingStore
from core.models import MappingCandidate


class TestMappingStore:
    """Test persistent mapping storage."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        yield db_path
        
        Path(db_path).unlink(missing_ok=True)
    
    @pytest.fixture
    def store(self, temp_db):
        """Create a mapping store."""
        return MappingStore(temp_db)
    
    @pytest.fixture
    def sample_candidate(self):
        """Create a sample mapping candidate."""
        return MappingCandidate(
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
            match_evidence="Exact match at A2",
            state='approved'
        )
    
    def test_save_and_retrieve(self, store, sample_candidate):
        """Test saving and retrieving a mapping."""
        # Save
        mapping_id = store.save_mapping(sample_candidate)
        assert mapping_id > 0
        
        # Retrieve
        mappings = store.get_mappings(workbook_fingerprint="abc123")
        assert len(mappings) == 1
        assert mappings[0].metric_id == "M001"
        assert mappings[0].sheet_name == "Sheet1"
    
    def test_update_existing(self, store, sample_candidate):
        """Test updating an existing mapping."""
        # Save first time
        id1 = store.save_mapping(sample_candidate)
        
        # Update
        sample_candidate.confidence = 0.99
        id2 = store.save_mapping(sample_candidate)
        
        # Should update, not create new
        mappings = store.get_mappings(workbook_fingerprint="abc123")
        assert len(mappings) == 1
        assert mappings[0].confidence == 0.99
    
    def test_filter_by_sheet(self, store, sample_candidate):
        """Test filtering by sheet name."""
        # Save
        store.save_mapping(sample_candidate)
        
        # Add another mapping for different sheet
        sample_candidate.sheet_name = "Sheet2"
        sample_candidate.metric_id = "M002"
        store.save_mapping(sample_candidate)
        
        # Filter
        sheet1_mappings = store.get_mappings(sheet_name="Sheet1")
        assert len(sheet1_mappings) == 1
        assert sheet1_mappings[0].sheet_name == "Sheet1"
        
        sheet2_mappings = store.get_mappings(sheet_name="Sheet2")
        assert len(sheet2_mappings) == 1
        assert sheet2_mappings[0].sheet_name == "Sheet2"
    
    def test_delete_mapping(self, store, sample_candidate):
        """Test deleting a mapping."""
        # Save
        mapping_id = store.save_mapping(sample_candidate)
        
        # Verify exists
        mappings = store.get_mappings()
        assert len(mappings) == 1
        
        # Delete
        store.delete_mapping(mapping_id)
        
        # Verify deleted
        mappings = store.get_mappings()
        assert len(mappings) == 0
    
    def test_clear_all(self, store, sample_candidate):
        """Test clearing all mappings."""
        # Save multiple
        store.save_mapping(sample_candidate)
        sample_candidate.metric_id = "M002"
        store.save_mapping(sample_candidate)
        
        # Verify
        assert len(store.get_mappings()) == 2
        
        # Clear
        store.clear_all()
        
        # Verify empty
        assert len(store.get_mappings()) == 0
