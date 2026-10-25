# Quick Start Guide

## Installation

1. **Create virtual environment:**
   ```bash
   py -m venv .venv
   ```

2. **Activate virtual environment:**
   ```bash
   .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   python -m pip install -r requirements.txt
   ```

## Running the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`.

## Testing

Run all tests:
```bash
pytest -q
```

Run specific test file:
```bash
pytest tests/test_month_parser.py -v
```

## Sample Workflow

1. **Start the application** (`streamlit run app.py`)

2. **Load source data:**
   - Navigate to "Load Source Data" page
   - Upload `../excel_metric_mapper_sample_pack/excel_metric_mapper_sample/source_metrics_oct_2026.csv`
   - Select target month: `2026-10`

3. **Load workbooks:**
   - Navigate to "Load Workbooks" page
   - Upload one or more sample templates from `../excel_metric_mapper_sample_pack/excel_metric_mapper_sample/templates/`

4. **Discover mappings:**
   - Navigate to "Discover & Map" page
   - Click "Run Discovery"
   - Review and approve suggested mappings
   - Handle ambiguous cases

5. **Preview changes:**
   - Navigate to "Preview Changes" page
   - Review all proposed changes
   - Check warnings

6. **Execute:**
   - Navigate to "Run & Audit" page
   - Click "Execute Changes"
   - Download updated workbooks from the output directory
   - Export audit report

## Troubleshooting

### Port Already in Use
If port 8501 is in use:
```bash
streamlit run app.py --server.port 8502
```

### Module Import Errors
Ensure you're in the correct directory and virtual environment is activated:
```bash
cd excel_metric_mapper
.venv\Scripts\activate
```

### Test File Cleanup Errors (Windows)
Windows file locking may cause test cleanup errors. These are non-critical - the tests themselves pass. Temp files will be cleaned up eventually by the OS.
