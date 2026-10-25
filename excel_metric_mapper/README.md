# Excel Metric Mapper

A local-first Python application for discovering and populating monthly metrics in Excel workbooks safely.

## Features

### ✨ Smart Discovery
- Automatically finds month headers in horizontal and vertical layouts
- Recognizes various month formats (Excel dates, ISO strings, month names)
- Fuzzy matching for metric labels
- Confidence scoring for each mapping
- Ambiguity detection for duplicate labels

### 🔒 Safe Writing
- Creates output copies, never modifies originals
- Preserves formulas, charts, and formatting
- Blocks formula cell overwrites by default
- Verification after writing
- Detailed audit trail

### 📊 Flexible Input
- CSV or Excel source files
- Multiple target workbooks
- Multi-sheet workbooks
- Macro-enabled files (.xlsm)

### 🎯 User Control
- Review all mappings before applying
- Manual override for ambiguous cases
- Preview changes with warnings
- Dry-run mode

## Installation

### Prerequisites
- Python 3.11 or higher

### Setup

**Windows:**
```bash
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Usage

### Running the Application

```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`.

### Workflow

1. **Load Source Data**
   - Upload CSV or Excel file with normalized metrics
   - Columns required: `metric_id`, `metric_name`, `reporting_month`, `value`, `unit`
   - Select target reporting month

2. **Load Workbooks**
   - Upload one or more Excel workbooks (.xlsx or .xlsm)
   - Application inspects structure without modification

3. **Discover & Map**
   - Automatically discover month headers and metric labels
   - Review proposed mappings with confidence scores
   - Approve, reject, or manually adjust mappings
   - Handle ambiguous cases

4. **Preview Changes**
   - Review all approved changes before applying
   - Check for warnings (formulas, merged cells, overwrites)
   - Configure output directory

5. **Run & Audit**
   - Execute changes to create output workbooks
   - View execution results
   - Export audit report
   - Download updated files

## Sample Data

Sample workbooks and source data are included in the `excel_metric_mapper_sample_pack` directory:

- `source_metrics_oct_2026.csv`: Normalized source data
- `templates/01_energy_horizontal.xlsx`: Horizontal month layout
- `templates/02_vertical_months.xlsx`: Vertical month layout
- `templates/03_mixed_layouts_multi_sheet.xlsx`: Multiple sheets
- `templates/04_ambiguous_metric_requires_review.xlsx`: Ambiguous labels

Target month: October 2026 (`2026-10`)

## Testing

Run tests with pytest:

```bash
pytest -q
```

Run tests with verbose output:

```bash
pytest -v
```

Run specific test file:

```bash
pytest tests/test_month_parser.py -v
```

## Architecture

```
excel_metric_mapper/
├── app.py                      # Main Streamlit application
├── pages/
│   ├── 1_Source_Data.py        # Source data loading page
│   ├── 2_Workbooks.py          # Workbook loading page
│   ├── 3_Discover_and_Map.py   # Discovery and mapping page
│   ├── 4_Preview_Changes.py    # Change preview page
│   └── 5_Run_and_Audit.py      # Execution and audit page
├── core/
│   ├── models.py               # Data models
│   ├── month_parser.py         # Month normalization
│   ├── source_loader.py        # Source data loading
│   ├── workbook_inspector.py   # Workbook inspection
│   ├── discovery.py            # Discovery engine
│   ├── scoring.py              # Mapping scoring
│   ├── mapping_store.py        # SQLite storage
│   ├── writer.py               # Safe workbook writing
│   └── audit.py                # Audit logging
├── tests/
│   ├── test_month_parser.py
│   ├── test_discovery.py
│   ├── test_writer.py
│   └── test_mapping_store.py
├── data/                       # Uploaded files (temporary)
├── output/                     # Output workbooks
├── requirements.txt
└── README.md
```

## Data Models

### Source Data
Required columns:
- `metric_id`: Unique identifier (e.g., "M001")
- `metric_name`: Display name (e.g., "Energy Consumption")
- `reporting_month`: Month in YYYY-MM format
- `value`: Numeric value
- `unit`: Unit of measurement (e.g., "kWh", "m3")

### Mapping Candidate States
- `suggested`: Proposed by discovery engine
- `ambiguous`: Multiple matches found, needs review
- `approved`: User approved for writing
- `rejected`: User rejected
- `blocked`: Cannot be auto-approved (e.g., contains formula)
- `applied`: Successfully written
- `failed`: Write operation failed

## Limitations and Known Issues

### Excel Feature Preservation
- **Formulas**: Preserved but not recalculated. Excel will recalculate on open.
- **Charts**: Preserved, but may not update until workbook is opened in Excel.
- **Conditional Formatting**: Preserved where supported by openpyxl.
- **Macros**: Preserved in .xlsm files with `keep_vba=True`, but not executed.
- **Advanced Features**: Some Excel features (slicers, pivot tables, etc.) may not be fully preserved.

### Month Detection
- Focuses on common month formats
- May misidentify numeric values as Excel dates in edge cases
- Requires at least partial month information to detect

### Metric Matching
- Fuzzy matching threshold is configurable
- Very similar metric names may cause ambiguity
- Manual review recommended for low-confidence matches

### Performance
- Large workbooks (>1000 rows/columns) may take longer to scan
- Adjust `max_rows` and `max_cols` settings for faster discovery

## Troubleshooting

### Import Errors
If you get import errors, make sure you're in the correct directory and the virtual environment is activated:
```bash
cd excel_metric_mapper
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux
```

### Openpyxl Warnings
Openpyxl may show warnings about workbook features it doesn't support. These are informational and generally safe to ignore.

### Permission Errors
Ensure output directory has write permissions. On Windows, avoid writing to system directories.

### Memory Issues
For very large workbooks, consider:
- Reducing `max_rows` and `max_cols` in discovery settings
- Processing workbooks one at a time
- Increasing available system memory

## Contributing

This is a sample implementation. To extend:

1. Add new month format patterns in `month_parser.py`
2. Improve fuzzy matching in `discovery.py`
3. Add new confidence signals in `scoring.py`
4. Extend audit logging in `audit.py`

## License

This is a demonstration project. Adapt as needed for your use case.

## Safety Notice

**IMPORTANT:** This application is designed to be safe, but:
- Always backup your workbooks before using
- Review preview changes carefully
- Test with sample data first
- Verify output workbooks in Excel after generation
- Do not rely on this tool for mission-critical data without thorough testing

The application creates output copies by default and never modifies uploaded originals, but file system errors could occur in exceptional circumstances.
