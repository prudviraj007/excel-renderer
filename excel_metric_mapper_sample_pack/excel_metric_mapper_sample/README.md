# Excel Metric Mapper — Sample Data Pack

## Files
- `source_metrics_oct_2026.csv`: normalized source metric data.
- `source_metrics_oct_2026.xlsx`: same source data as an Excel workbook, plus a Read Me sheet.
- `templates/01_energy_horizontal.xlsx`: horizontal months, blank October cells, formulas, chart, merged title, conditional formatting.
- `templates/02_vertical_months.xlsx`: vertical month rows, real Excel dates, multiple metrics in columns, formulas and chart.
- `templates/03_mixed_layouts_multi_sheet.xlsx`: multiple worksheets, mixed month formats, horizontal and vertical trends, summary cells.
- `templates/04_ambiguous_metric_requires_review.xlsx`: repeated metric label for different sites; should require user confirmation instead of guessing.

## Target reporting period
October 2026 (`2026-10`).

## Expected source metrics
M001 Energy Consumption = 1245.0 kWh
M002 Water Consumption = 876.0 m3
M003 Equipment Availability = 0.986 (display as 98.6%)
M004 Total Revenue = 5,450,000 SGD
M005 Carbon Emissions = 312.4 tCO2e
M006 Maintenance Cost = 18,450.75 SGD
M007 Cooling Energy = 732.8 kWh
M008 Power Factor = 0.947 (display as 94.7% if percentage formatting is appropriate)

## Important test expectations
1. Discover month headers in horizontal and vertical orientations.
2. Recognize month values stored as text, ISO strings, or Excel dates.
3. Match metric labels using exact and fuzzy matching, but do not auto-write ambiguous duplicate matches.
4. Do not overwrite formula cells without explicit approval.
5. Preserve workbook formatting, formulas, merged cells, charts, and conditional formatting as far as the selected library allows.
6. Create output copies by default; never overwrite uploaded originals.
7. Produce a proposed-changes preview and audit log.
8. Verify saved output by reopening it and checking the target cells.
9. If a new month column/row is missing, ask for configured behavior rather than silently adding one.
10. Treat the sample workbooks as test fixtures, not as proof that all Excel features are safely preserved.
