# DataSentinel fixes

## Changes
- Upload history now records each explicit file-selection/upload event, including re-uploading the same filename and file size. Streamlit reruns for that same event do not create duplicate history rows.
- Column Health now displays null percentages and severity before and after cleaning.
- Profiled date-like text columns are identified as `datetime` for reporting without mutating the original data.
- Quality score now uses a continuous completeness calculation (non-null cells / total cells), so small missing-value rates no longer misleadingly show 100%.
- Statistical anomaly detection now combines Z-score and IQR fences, and flags duplicate rows and repeated `id` / `*_id` values.

## Validation performed
- Python compilation: `python -m compileall -q dashboard.py src` — passed.
- Profiler/anomaly smoke test: date inference, 93.75% score for 1 missing cell out of 16, duplicate ID detection, and IQR outlier detection — passed.

## Notes
- These checks validate source modules and core logic. A full interactive Streamlit/browser test against your own deployment credentials and database was not possible in this environment.
- Existing maps, analytics charts, history pages, authentication, and styling were retained; no redesign was performed.
