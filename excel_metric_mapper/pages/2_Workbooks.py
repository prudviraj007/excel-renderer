"""Page 2: Load Workbooks."""
import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.workbook_inspector import inspect_workbook
from core.session_state import init_session_state

st.set_page_config(page_title="Workbooks", page_icon="📁", layout="wide")
init_session_state()

st.title("📁 Load Target Workbooks")
st.markdown("Upload Excel workbooks that need to be updated with metric values.")

# Check prerequisites
if not st.session_state.source_metrics:
    st.warning("⚠️ Please load source data first")
    if st.button("← Go to Source Data"):
        st.switch_page("pages/1_Source_Data.py")
    st.stop()

if not st.session_state.target_month:
    st.warning("⚠️ Please select a target month first")
    if st.button("← Go to Source Data"):
        st.switch_page("pages/1_Source_Data.py")
    st.stop()

# File upload
uploaded_files = st.file_uploader(
    "Upload Excel workbooks (.xlsx or .xlsm)",
    type=['xlsx', 'xlsm'],
    accept_multiple_files=True,
    help="Upload one or more workbooks to be updated. Originals will not be modified."
)

if uploaded_files:
    st.info(f"Uploaded {len(uploaded_files)} file(s)")
    
    if st.button("🔍 Inspect Workbooks", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, uploaded_file in enumerate(uploaded_files):
            status_text.text(f"Inspecting {uploaded_file.name}...")
            
            # Save to temp location
            temp_path = Path("excel_metric_mapper/data") / uploaded_file.name
            temp_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(temp_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            
            # Inspect workbook
            try:
                info = inspect_workbook(str(temp_path), deep_scan=True)
                st.session_state.workbooks[uploaded_file.name] = str(temp_path)
                st.session_state.workbook_infos[uploaded_file.name] = info
            except Exception as e:
                st.error(f"Error inspecting {uploaded_file.name}: {str(e)}")
            
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        status_text.text("✓ Inspection complete!")
        st.success(f"Inspected {len(uploaded_files)} workbook(s)")

# Display loaded workbooks
if st.session_state.workbooks:
    st.markdown("---")
    st.subheader("📚 Loaded Workbooks")
    
    for workbook_name, workbook_path in st.session_state.workbooks.items():
        info = st.session_state.workbook_infos.get(workbook_name)
        
        with st.expander(f"📄 {workbook_name}", expanded=True):
            if info:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Path:** `{workbook_path}`")
                    st.markdown(f"**Fingerprint:** `{info.fingerprint[:16]}...`")
                    st.markdown(f"**Sheets:** {len(info.sheets)}")
                    
                    if info.is_macro_enabled:
                        st.warning("⚠️ Macro-enabled workbook (.xlsm)")
                    
                    # Show warnings
                    if info.warnings:
                        for warning in info.warnings:
                            st.warning(f"⚠️ {warning}")
                
                with col2:
                    if st.button(f"❌ Remove", key=f"remove_{workbook_name}"):
                        del st.session_state.workbooks[workbook_name]
                        del st.session_state.workbook_infos[workbook_name]
                        st.rerun()
                
                # Sheet details
                st.markdown("**📋 Sheets:**")
                sheet_data = []
                for sheet_name, sheet_info in info.sheets.items():
                    sheet_data.append({
                        'Sheet': sheet_name,
                        'Rows': sheet_info.max_row,
                        'Columns': sheet_info.max_col,
                        'Hidden': '✓' if sheet_info.hidden else '',
                        'Formulas': '✓' if sheet_info.has_formulas else '',
                        'Charts': '✓' if sheet_info.has_charts else '',
                        'Merged Cells': len(sheet_info.merged_ranges),
                    })
                
                import pandas as pd
                st.dataframe(pd.DataFrame(sheet_data), use_container_width=True, hide_index=True)
            else:
                st.error("Workbook info not available")
    
    # Summary
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Workbooks Loaded", len(st.session_state.workbooks))
    
    with col2:
        total_sheets = sum(len(info.sheets) for info in st.session_state.workbook_infos.values())
        st.metric("Total Sheets", total_sheets)
    
    with col3:
        macro_enabled = sum(1 for info in st.session_state.workbook_infos.values() if info.is_macro_enabled)
        st.metric("Macro-Enabled", macro_enabled)
    
    # Next step
    st.markdown("---")
    st.success("Ready to discover mappings! →")
    if st.button("Next: Discover & Map", type="primary"):
        st.switch_page("pages/3_Discover_and_Map.py")

else:
    st.info("👆 Upload workbooks to inspect them")
    
    # Show loaded state
    if st.session_state.source_metrics and st.session_state.target_month:
        st.success(f"✓ Source data loaded: {len(st.session_state.source_metrics)} metrics")
        st.success(f"✓ Target month: {st.session_state.target_month}")
