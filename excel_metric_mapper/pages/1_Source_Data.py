"""Page 1: Load Source Data."""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.source_loader import load_source_data, get_excel_sheets, detect_column_mapping, SourceDataError
from core.month_parser import normalize_month
from core.session_state import init_session_state

st.set_page_config(page_title="Source Data", page_icon="📂", layout="wide")
init_session_state()

st.title("📂 Load Source Data")
st.markdown("Upload your normalized source metrics file.")

# File upload
uploaded_file = st.file_uploader(
    "Upload CSV or Excel file",
    type=['csv', 'xlsx', 'xlsm', 'xls'],
    help="File should contain columns: metric_id, metric_name, reporting_month, value, unit"
)

if uploaded_file:
    # Save uploaded file temporarily
    temp_path = Path("excel_metric_mapper/data") / uploaded_file.name
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(temp_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    
    st.success(f"File uploaded: {uploaded_file.name}")
    
    # Sheet selection for Excel files
    sheet_name = None
    if uploaded_file.name.endswith(('.xlsx', '.xlsm', '.xls')):
        try:
            sheets = get_excel_sheets(str(temp_path))
            if len(sheets) > 1:
                sheet_name = st.selectbox("Select sheet", sheets)
            else:
                sheet_name = sheets[0]
                st.info(f"Using sheet: {sheet_name}")
        except Exception as e:
            st.error(f"Error reading Excel file: {str(e)}")
            st.stop()
    
    # Load and preview raw data
    try:
        if uploaded_file.name.endswith('.csv'):
            df_raw = pd.read_csv(temp_path)
        else:
            df_raw = pd.read_excel(temp_path, sheet_name=sheet_name)
        
        st.subheader("📋 Raw Data Preview")
        st.dataframe(df_raw.head(10), use_container_width=True)
        st.caption(f"Showing first 10 of {len(df_raw)} rows")
        
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        st.stop()
    
    # Column mapping
    st.subheader("🔗 Column Mapping")
    
    required_columns = ['metric_id', 'metric_name', 'reporting_month', 'value', 'unit']
    auto_mapping = detect_column_mapping(df_raw)
    
    if auto_mapping:
        st.success("✓ Columns auto-detected")
        mapping = auto_mapping
    else:
        st.warning("⚠️ Could not auto-detect all columns. Please map manually.")
        mapping = {}
        
        cols = st.columns(len(required_columns))
        for i, req_col in enumerate(required_columns):
            with cols[i]:
                file_col = st.selectbox(
                    f"Source column for `{req_col}`",
                    options=[''] + list(df_raw.columns),
                    key=f"map_{req_col}"
                )
                if file_col:
                    mapping[file_col] = req_col
    
    # Show mapping
    if mapping:
        st.markdown("**Column Mapping:**")
        for file_col, target_col in mapping.items():
            st.text(f"  {file_col} → {target_col}")
    
    # Load button
    if st.button("✅ Load and Validate Source Data", type="primary", use_container_width=True):
        try:
            with st.spinner("Loading and validating..."):
                df, metrics = load_source_data(
                    str(temp_path),
                    sheet_name=sheet_name,
                    column_mapping=mapping if mapping else None
                )
            
            # Store in session state
            st.session_state.source_data = df
            st.session_state.source_metrics = metrics
            
            st.success(f"✓ Loaded {len(metrics)} source metrics successfully!")
            
            # Show validated data
            st.subheader("✅ Validated Source Data")
            st.dataframe(df, use_container_width=True)
            
            # Extract unique months for selection
            unique_months = sorted(df['reporting_month'].unique())
            
            st.subheader("📅 Select Target Reporting Month")
            target_month = st.selectbox(
                "Choose the month to populate in target workbooks",
                options=unique_months,
                index=len(unique_months) - 1 if unique_months else 0
            )
            
            if target_month:
                st.session_state.target_month = target_month
                
                # Filter metrics for target month
                target_metrics = [m for m in metrics if m.reporting_month == target_month]
                
                st.info(f"Selected target month: **{target_month}** ({len(target_metrics)} metrics)")
                
                # Show target month metrics
                st.subheader(f"📊 Metrics for {target_month}")
                target_df = df[df['reporting_month'] == target_month]
                st.dataframe(target_df, use_container_width=True)
                
                # Summary statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Metrics", len(target_metrics))
                with col2:
                    st.metric("Unique Months", len(unique_months))
                with col3:
                    st.metric("Total Rows", len(df))
            
        except SourceDataError as e:
            st.error(f"❌ Validation Error: {str(e)}")
        except Exception as e:
            st.error(f"❌ Unexpected Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

# Show current state
if st.session_state.source_metrics:
    st.markdown("---")
    st.subheader("✅ Current Source Data Loaded")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Metrics", len(st.session_state.source_metrics))
    with col2:
        if st.session_state.target_month:
            target_count = sum(1 for m in st.session_state.source_metrics 
                             if m.reporting_month == st.session_state.target_month)
            st.metric(f"Metrics for {st.session_state.target_month}", target_count)
    
    if st.button("📋 View Loaded Data"):
        st.dataframe(st.session_state.source_data, use_container_width=True)
    
    # Next step
    st.success("Ready to load workbooks! →")
    if st.button("Next: Load Workbooks", type="primary"):
        st.switch_page("pages/2_Workbooks.py")
else:
    st.info("👆 Upload a source data file to get started")
