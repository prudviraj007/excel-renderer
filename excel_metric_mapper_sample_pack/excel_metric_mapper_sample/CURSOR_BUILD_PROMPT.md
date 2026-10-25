# Cursor Build Prompt — Excel Metric Mapper

Build a local-first Python UI application named **Excel Metric Mapper** that discovers monthly metric locations in varied Excel workbooks and safely populates the target reporting month from normalized source data.

## Product objective
Users provide a normalized source table and one or more Excel workbooks. Each workbook can contain multiple sheets, different layouts, month labels in different formats, formulas, charts, merged cells, and historical 12-month trends. The application must discover candidate metric/month cells, show evidence and confidence, let users approve or correct mappings in a visual UI, save approved mappings, preview changes, and write values into output copies without changing uploaded originals.

## Work in the existing repository
1. Inspect the current repository before changing anything.
2. If it is empty, initialize a clean project structure.
3. Implement a working MVP, not just mockups or pseudocode.
4. Add tests and run them. Fix failures before declaring completion.
5. Keep the app local-first; no external API or LLM is required for MVP.
6. Do not hard-code sample filenames or specific cell addresses.

## Suggested stack
- Python 3.11+
- Streamlit UI
- pandas for source data
- openpyxl for workbook inspection/writing
- RapidFuzz for metric label similarity
- SQLite for persistent mapping templates and audit log
- pytest for tests
- Optional: streamlit-aggrid or another maintained grid component only if installation is straightforward. If unavailable, create a useful worksheet preview using Streamlit dataframes plus cell coordinate selection controls.

## User workflows
### A. Load source data
- Upload CSV/XLSX or select a local file via an explicit file-picker approach supported by the app.
- Support a source sheet selector for XLSX.
- Normalize columns to: `metric_id`, `metric_name`, `reporting_month`, `value`, `unit`, with aliases and a UI mapping step if names differ.
- `metric_id` is preferred over metric name. Support YYYY-MM, Excel dates, and common month strings.
- Detect duplicate `(metric_id or normalized metric_name, reporting_month)` rows. Never silently choose or aggregate duplicates.
- Keep values as numeric where possible; support decimals, percentages, currency, and strings if explicitly allowed.
- Reporting month is selectable in UI and must be validated.

### B. Load target workbooks
- Accept multiple `.xlsx` and `.xlsm` files. Keep original files unchanged.
- For `.xlsm`, load with `keep_vba=True`. Clearly warn that advanced Excel features may not be fully preserved by openpyxl and provide a validation warning.
- List workbook and sheet inventory, dimensions, merged ranges, hidden sheets, formulas, tables, named ranges, and charts where accessible.
- Never execute macros or formulas.

### C. Discovery engine
Implement discovery as modular, testable functions, not logic embedded in Streamlit:
1. `inspect_workbook(path)`: workbook/sheet metadata and cell-level evidence.
2. `normalize_month(value)`: convert Excel dates, Python dates/datetimes, `YYYY-MM`, `YYYY-MM-DD`, `Jan-26`, `Jan'26`, `October 2026`, and similar common representations to `YYYY-MM`. Do not misclassify arbitrary numbers as dates.
3. `find_month_headers(...)`: find date/month candidates in rows and columns, including horizontal and vertical layouts. Keep cell coordinate, raw value, normalized month, row/column, and confidence.
4. `find_metric_labels(...)`: identify likely label cells using text cells and source metric names/IDs, including fuzzy matches. Preserve exact match score and evidence.
5. `find_candidate_regions(...)`: group contiguous monthly headers with nearby metric labels and data cells; support horizontal month columns and vertical month rows, and multiple regions on a sheet.
6. `propose_mappings(...)`: generate one candidate per source metric and target month, with workbook, sheet, metric identity, month header cell, target value cell, layout orientation, confidence, match evidence, existing value/formula, unit hints, and status.
7. Score using multiple signals: metric exact/fuzzy match, month header confidence, contiguous month sequence, data shape, unit hints, sheet/workbook names as weak hints, and whether target cell is formula/merged/locked if detectable.
8. Do not auto-approve ambiguous candidates. Repeated metric labels in separate site/region blocks must be marked ambiguous unless source data has matching site/region identifiers or user explicitly selects a candidate.
9. Include a deterministic baseline; LLM calls are out of scope for MVP.
10. Never write into a cell that is part of a merged range except the top-left anchor; never overwrite formulas silently.
11. If target month header is missing, do not silently append a month. Offer an explicit configurable action later; MVP should flag for manual review.
12. Do not infer that a blank cell is the target solely because it is blank.

### D. Interactive UI
Build a polished, practical Streamlit app with pages or tabs:
1. **Source Data** — upload, preview, select sheet, map source columns, choose reporting month.
2. **Workbooks** — upload multiple target files and inspect workbook/sheet inventory.
3. **Discover & Map** — run discovery; show candidate table with filters for confidence/status/workbook/sheet/metric. Provide explicit Approve, Reject, and Manual Map actions.
4. **Worksheet Preview** — show a grid-like preview with row/column headers, coordinate selection, selected cell details, month header cell, metric label cell, orientation, and existing value/formula. If a rich editable grid is unavailable, use a dataframe preview and coordinate input controls.
5. **Preview Changes** — show source value, target cell, existing value/formula, proposed value, formatting/unit notes, and overwrite warnings. User must explicitly confirm before applying.
6. **Run & Audit** — write output copies to a user-selected output directory; show successes, skips, errors, and downloadable CSV audit report.

### E. Persistent mapping templates
Use SQLite. Save mappings using stable identifiers and evidence, not only raw coordinates. Include:
- workbook fingerprint (filename plus structural signature; avoid relying on filename alone)
- worksheet name and structural signature
- metric_id / normalized metric name
- reporting layout/orientation
- month header row/column or header-cell locator
- metric label cell/locator
- target value cell/locator
- nearby label/context evidence
- confidence, user approval, created/updated timestamps
- last successful execution
On future runs, validate saved mappings against the current workbook structure and target month header before writing. If structure changed or confidence falls, require re-discovery/re-approval.

### F. Safe writing and preservation
- Default to writing a new copy of each workbook in an output directory. Never modify uploaded originals.
- Keep formulas intact; only write to approved target cells that are not formula cells unless user explicitly authorizes replacing the formula.
- Preserve existing number formats, styles, dimensions, merged cells, freeze panes, conditional formatting, and charts as far as openpyxl supports.
- Do not use `data_only=True` for the workbook object used to save edits. If cached formula values are needed for inspection, open a separate read-only copy with `data_only=True`.
- For formula cells, explain that openpyxl does not calculate formulas. If necessary, set workbook calculation mode to automatic where supported, but do not claim formulas have recalculated.
- Handle `.xlsx` and `.xlsm` separately and preserve VBA where possible.
- Save to temporary output then atomically move to final path.
- Reopen saved output and verify the expected target cell value; report verification failures.
- Ensure charts are not deliberately recreated or removed. Include warnings for workbook features that cannot be guaranteed.
- Never claim perfect preservation of all Excel features. Include a compatibility note in UI and README.

### G. Audit and error handling
Log each proposed and applied change: timestamp, source file, target workbook, worksheet, metric, reporting month, target cell, old value, new value, decision, confidence, user approval, outcome, and error.
Handle corrupt files, encrypted/password-protected files, unsupported formats, missing source metrics, duplicate source rows, formula target cells, ambiguous mappings, missing month headers, and permission errors with user-friendly messages.
Do not fail the whole batch because one workbook fails.

## Architecture suggestion
Create a maintainable structure similar to:
```
excel_metric_mapper/
  app.py
  pages/
    1_Source_Data.py
    2_Workbooks.py
    3_Discover_and_Map.py
    4_Preview_Changes.py
    5_Run_and_Audit.py
  core/
    source_loader.py
    month_parser.py
    workbook_inspector.py
    discovery.py
    scoring.py
    mapping_store.py
    writer.py
    audit.py
    models.py
  tests/
    test_month_parser.py
    test_discovery.py
    test_writer.py
    test_mapping_store.py
  data/
  output/
  requirements.txt
  README.md
  .gitignore
```
You may simplify the page structure if needed, but keep core logic separate from UI.

## Data models
Use dataclasses or Pydantic models for:
- SourceMetric
- MonthHeaderCandidate
- MetricLabelCandidate
- MappingCandidate
- ApprovedMapping
- ProposedChange
- ExecutionResult

Each mapping candidate should contain at least:
- workbook path/name and workbook fingerprint
- worksheet name
- metric ID/name and source value
- target reporting month
- orientation (`horizontal` or `vertical`)
- metric label cell
- month header cell
- target value cell
- confidence score (0–1)
- match evidence / explanation
- existing cell value and formula status
- state (`suggested`, `ambiguous`, `approved`, `rejected`, `blocked`, `applied`, `failed`)

## Tests and acceptance criteria
Use the sample data pack in `sample_data/` if present; otherwise create equivalent fixtures.
1. Parse common month formats correctly, including Excel date values and strings.
2. Discover horizontal monthly tables.
3. Discover vertical monthly tables.
4. Discover tables on multiple sheets in one workbook.
5. Identify a blank target month cell without confusing it with a formula cell.
6. Detect duplicate metric labels and mark them ambiguous.
7. Ensure formulas are never overwritten without explicit authorization.
8. Ensure the uploaded original workbook's hash is unchanged after execution.
9. Ensure output copies contain expected values in approved cells.
10. Ensure an existing cell's number format is retained after writing.
11. Verify formulas and charts remain present after save/reopen for sample workbooks; issue warnings where features cannot be guaranteed.
12. Test graceful handling of malformed files and duplicate source records.
13. Provide a sample run and clear local startup instructions.

## UI quality
- Use a clean layout with status badges, progress feedback, helpful empty states, and clear error messages.
- Show why each candidate was proposed, not only a confidence number.
- Keep low-confidence and ambiguous items out of the auto-apply path.
- Include an explicit confirmation step before any write operation.
- Include a dry-run mode.
- Never send workbook content to external services.

## Deliverables
- Complete runnable source code.
- `requirements.txt` with pinned or bounded dependencies.
- Tests and test results.
- README with setup, run, limitations, and sample workflow.
- Use these commands in README where appropriate:
  - Windows: `py -m venv .venv` then `.venv\Scripts\activate`
  - macOS/Linux: `python3 -m venv .venv` then `source .venv/bin/activate`
  - `python -m pip install -r requirements.txt`
  - `streamlit run app.py`
  - `pytest -q`
- At the end, summarize implemented features, files created, test results, and known limitations.

## First actions
Before coding, inspect the repository and list the current files. Then implement the MVP end-to-end. Prefer a working vertical slice (upload → discover → approve → preview → write output copy → verify) over broad but incomplete scaffolding.
