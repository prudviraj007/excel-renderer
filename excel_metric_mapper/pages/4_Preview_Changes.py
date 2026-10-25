"""Page 4: Preview Changes."""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.writer import prepare_proposed_changes
from core.session_state import init_session_state

st.set_page_config(page_title="Preview Changes", page_icon="👁️", layout="wide")
init_session_state()

st.title("👁️ Preview Changes")
st.markdown("Review all approved mappings before applying changes.")

# Check prerequisites
if not st.session_state.mapping_candidates:
    st.warning("⚠️ Please discover mappings first")
    if st.button("← Go to Discover & Map"):
        st.switch_page("pages/3_Discover_and_Map.py")
    st.stop()

# Get approved candidates
approved_candidates = [c for c in st.session_state.mapping_candidates if c.state == 'approved']

if not approved_candidates:
    st.warning("⚠️ No approved mappings found")
    st.info("Go back to Discover & Map to approve some mappings")
    if st.button("← Go to Discover & Map"):
        st.switch_page("pages/3_Discover_and_Map.py")
    st.stop()

# Prepare proposed changes
st.session_state.proposed_changes = prepare_proposed_changes(approved_candidates)

st.success(f"✓ {len(st.session_state.proposed_changes)} changes ready to apply")

# Summary by workbook
st.subheader("📚 Changes by Workbook")

changes_by_workbook = {}
for change in st.session_state.proposed_changes:
    workbook_name = Path(change.workbook_path).name
    if workbook_name not in changes_by_workbook:
        changes_by_workbook[workbook_name] = []
    changes_by_workbook[workbook_name].append(change)

for workbook_name, changes in changes_by_workbook.items():
    with st.expander(f"📄 {workbook_name} ({len(changes)} changes)", expanded=True):
        # Group by sheet
        changes_by_sheet = {}
        for change in changes:
            if change.sheet_name not in changes_by_sheet:
                changes_by_sheet[change.sheet_name] = []
            changes_by_sheet[change.sheet_name].append(change)
        
        for sheet_name, sheet_changes in changes_by_sheet.items():
            st.markdown(f"**Sheet: {sheet_name}** ({len(sheet_changes)} changes)")
            
            # Create table
            data = []
            for change in sheet_changes:
                warnings_str = '; '.join(change.warnings) if change.warnings else ''
                
                data.append({
                    'Target Cell': change.target_cell,
                    'Metric ID': change.metric_id,
                    'Metric Name': change.metric_name[:30] + '...' if len(change.metric_name) > 30 else change.metric_name,
                    'Proposed Value': change.proposed_value,
                    'Unit': change.source_unit,
                    'Existing Value': str(change.existing_value)[:20] if change.existing_value else '(empty)',
                    'Formula': '⚠️' if change.has_formula else '',
                    'Merged': '⚠️' if change.is_merged else '',
                    'Confidence': f"{change.confidence:.2f}",
                    'Warnings': warnings_str
                })
            
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)

# Warnings summary
st.markdown("---")
st.subheader("⚠️ Warnings Summary")

total_warnings = sum(len(change.warnings) for change in st.session_state.proposed_changes)
formula_count = sum(1 for change in st.session_state.proposed_changes if change.has_formula)
merged_count = sum(1 for change in st.session_state.proposed_changes if change.is_merged)
overwrite_count = sum(1 for change in st.session_state.proposed_changes 
                     if change.existing_value is not None and change.existing_value != "")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if total_warnings > 0:
        st.warning(f"⚠️ {total_warnings} warnings")
    else:
        st.success("✓ No warnings")

with col2:
    if formula_count > 0:
        st.error(f"❌ {formula_count} formula cells")
    else:
        st.success("✓ No formulas")

with col3:
    if merged_count > 0:
        st.warning(f"⚠️ {merged_count} merged cells")
    else:
        st.success("✓ No merged cells")

with col4:
    if overwrite_count > 0:
        st.info(f"ℹ️ {overwrite_count} overwrites")
    else:
        st.success("✓ No overwrites")

# Warnings details
if total_warnings > 0:
    with st.expander("⚠️ View All Warnings"):
        for change in st.session_state.proposed_changes:
            if change.warnings:
                st.markdown(f"**{Path(change.workbook_path).name} / {change.sheet_name} / {change.target_cell}**")
                for warning in change.warnings:
                    st.text(f"  • {warning}")

# Output directory
st.markdown("---")
st.subheader("📁 Output Configuration")

col1, col2 = st.columns([3, 1])

with col1:
    output_dir = st.text_input(
        "Output directory",
        value=st.session_state.output_directory,
        help="Directory where updated workbooks will be saved"
    )
    st.session_state.output_directory = output_dir

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("📁 Use Default"):
        st.session_state.output_directory = str(Path("excel_metric_mapper/output").absolute())
        st.rerun()

# Create output directory if it doesn't exist
Path(output_dir).mkdir(parents=True, exist_ok=True)
st.success(f"✓ Output directory ready: {output_dir}")

# Preview mode
st.markdown("---")
st.subheader("🎬 Execution Mode")

col1, col2 = st.columns(2)

with col1:
    dry_run = st.checkbox("Dry run (don't actually write changes)", value=False)
    if dry_run:
        st.info("ℹ️ Dry run mode: Changes will be prepared but not written")
    else:
        st.warning("⚠️ Live mode: Changes will be written to output files")

with col2:
    create_backup = st.checkbox("Create backup of originals", value=True)
    if create_backup:
        st.info("ℹ️ Original files will be backed up before processing")

# Confirmation
st.markdown("---")
st.subheader("✅ Confirm and Proceed")

if formula_count > 0:
    st.error("❌ Cannot proceed: Some target cells contain formulas. Please review and reject those mappings.")
    if st.button("← Go Back to Review"):
        st.switch_page("pages/3_Discover_and_Map.py")
else:
    st.success("✓ All safety checks passed")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("← Back to Mappings", use_container_width=True):
            st.switch_page("pages/3_Discover_and_Map.py")
    
    with col2:
        pass  # Empty column for spacing
    
    with col3:
        if st.button("▶️ Proceed to Execute", type="primary", use_container_width=True):
            st.switch_page("pages/5_Run_and_Audit.py")

# Detailed change view
st.markdown("---")
st.subheader("🔍 Detailed Change View")

if st.session_state.proposed_changes:
    change_index = st.number_input(
        "Select change to view details",
        min_value=0,
        max_value=len(st.session_state.proposed_changes) - 1,
        value=0
    )
    
    if 0 <= change_index < len(st.session_state.proposed_changes):
        change = st.session_state.proposed_changes[change_index]
        
        with st.container(border=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Source Information**")
                st.text(f"Workbook: {Path(change.workbook_path).name}")
                st.text(f"Sheet: {change.sheet_name}")
                st.text(f"Target Cell: {change.target_cell}")
                st.text(f"Metric ID: {change.metric_id}")
                st.text(f"Metric Name: {change.metric_name}")
                st.text(f"Confidence: {change.confidence:.2f}")
            
            with col2:
                st.markdown("**Change Details**")
                st.text(f"Proposed Value: {change.proposed_value}")
                st.text(f"Unit: {change.source_unit}")
                st.text(f"Existing Value: {change.existing_value if change.existing_value else '(empty)'}")
                st.text(f"Has Formula: {'Yes' if change.has_formula else 'No'}")
                st.text(f"Is Merged: {'Yes' if change.is_merged else 'No'}")
            
            if change.warnings:
                st.markdown("**Warnings**")
                for warning in change.warnings:
                    st.warning(warning)
