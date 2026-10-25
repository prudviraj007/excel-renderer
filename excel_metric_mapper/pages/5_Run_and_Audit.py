"""Page 5: Run and Audit."""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.writer import write_changes, create_backup, prepare_proposed_changes
from core.audit import AuditLogger
from core.session_state import init_session_state

st.set_page_config(page_title="Run & Audit", page_icon="🚀", layout="wide")
init_session_state()

st.title("🚀 Run & Audit")
st.markdown("Execute approved changes and view audit trail.")

# Rebuild change list from approved mappings if user skipped preview
if not st.session_state.proposed_changes:
    approved = [c for c in st.session_state.mapping_candidates if c.state == "approved"]
    if approved:
        st.session_state.proposed_changes = prepare_proposed_changes(approved)

if not st.session_state.proposed_changes:
    st.warning("No approved changes to apply. Approve mappings on Discover & Map first.")
    if st.button("← Go to Discover & Map"):
        st.switch_page("pages/3_Discover_and_Map.py")
    st.stop()

# Initialize audit logger
audit_logger = AuditLogger()

# Execution section
st.subheader("⚡ Execute Changes")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Changes", len(st.session_state.proposed_changes))

with col2:
    workbook_count = len(set(Path(c.workbook_path).name for c in st.session_state.proposed_changes))
    st.metric("Workbooks", workbook_count)

with col3:
    st.metric("Output Directory", "Ready")

# Execution options
dry_run = st.checkbox("Dry run (simulate only)", value=False, key="dry_run_execute")

if dry_run:
    st.info("ℹ️ Dry run mode: No files will be modified")

# Execute button
if st.button("▶️ Execute Changes", type="primary", use_container_width=True, disabled=st.session_state.get('execution_running', False)):
    st.session_state.execution_running = True
    st.session_state.execution_results = []
    
    # Group changes by workbook
    changes_by_workbook = {}
    for change in st.session_state.proposed_changes:
        if change.workbook_path not in changes_by_workbook:
            changes_by_workbook[change.workbook_path] = []
        changes_by_workbook[change.workbook_path].append(change)
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_workbooks = len(changes_by_workbook)
    results = []
    
    for i, (workbook_path, changes) in enumerate(changes_by_workbook.items()):
        workbook_name = Path(workbook_path).name
        status_text.text(f"Processing {workbook_name}...")
        
        try:
            # Create backup if requested
            if not dry_run:
                backup_dir = Path(st.session_state.output_directory) / "backups"
                backup_path = create_backup(workbook_path, str(backup_dir))
                st.info(f"Created backup: {Path(backup_path).name}")
            
            # Write changes
            result = write_changes(
                workbook_path=workbook_path,
                changes=changes,
                output_dir=st.session_state.output_directory,
                dry_run=dry_run
            )
            
            results.append(result)
            
            # Log to audit
            if not dry_run:
                audit_logger.log_execution(result)
                for change in changes:
                    audit_logger.log_change(change, result.success)
            
        except Exception as e:
            st.error(f"Error processing {workbook_name}: {str(e)}")
        
        progress_bar.progress((i + 1) / total_workbooks)
    
    status_text.text("✓ Execution complete!")
    st.session_state.execution_results = results
    st.session_state.execution_running = False
    st.rerun()

# Display results
if st.session_state.execution_results:
    st.markdown("---")
    st.subheader("📊 Execution Results")
    
    total_applied = sum(r.changes_applied for r in st.session_state.execution_results)
    total_skipped = sum(r.changes_skipped for r in st.session_state.execution_results)
    total_errors = sum(len(r.errors) for r in st.session_state.execution_results)
    total_warnings = sum(len(r.warnings) for r in st.session_state.execution_results)
    successful_workbooks = sum(1 for r in st.session_state.execution_results if r.success)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Changes Applied", total_applied, delta=None)
    
    with col2:
        st.metric("Changes Skipped", total_skipped, delta=None)
    
    with col3:
        st.metric("Errors", total_errors, delta=None)
    
    with col4:
        st.metric("Successful Workbooks", f"{successful_workbooks}/{len(st.session_state.execution_results)}")
    
    # Individual results
    for result in st.session_state.execution_results:
        workbook_name = Path(result.workbook_path).name
        output_name = Path(result.output_path).name
        
        if result.success:
            icon = "✅"
            color = "green"
        else:
            icon = "❌"
            color = "red"
        
        with st.expander(f"{icon} {workbook_name}", expanded=not result.success):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**Output:** `{output_name}`")
                st.markdown(f"**Applied:** {result.changes_applied}")
                st.markdown(f"**Skipped:** {result.changes_skipped}")
                st.markdown(f"**Execution Time:** {result.execution_time:.2f}s")
                st.markdown(f"**Timestamp:** {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            
            with col2:
                if result.success:
                    st.success("✓ Success")
                else:
                    st.error("✗ Failed")
            
            # Errors
            if result.errors:
                st.markdown("**Errors:**")
                for error in result.errors:
                    st.error(error)
            
            # Warnings
            if result.warnings:
                st.markdown("**Warnings:**")
                for warning in result.warnings:
                    st.warning(warning)
    
    # Download audit report
    st.markdown("---")
    st.subheader("📥 Export Audit Report")
    
    if st.button("Export Audit Log to CSV"):
        audit_path = Path(st.session_state.output_directory) / f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        audit_logger.export_to_csv(str(audit_path))
        st.success(f"✓ Audit report saved: {audit_path.name}")
        
        # Show download link
        with open(audit_path, 'rb') as f:
            st.download_button(
                label="Download Audit Report",
                data=f,
                file_name=audit_path.name,
                mime='text/csv'
            )
    
    # Output directory link
    st.info(f"📁 Output files saved to: `{st.session_state.output_directory}`")

# Audit log viewer
st.markdown("---")
st.subheader("📜 Recent Audit Log")

recent_logs = audit_logger.get_recent_logs(limit=50)

if recent_logs:
    df = pd.DataFrame(recent_logs)
    
    # Format timestamp
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Select relevant columns
    display_columns = [
        'timestamp', 'workbook_path', 'sheet_name', 'metric_id', 
        'target_cell', 'new_value', 'outcome'
    ]
    display_columns = [col for col in display_columns if col in df.columns]
    
    st.dataframe(
        df[display_columns],
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No audit logs found")

# Reset and start over
st.markdown("---")
st.subheader("🔄 Start Over")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🏠 Back to Home"):
        st.switch_page("app.py")

with col2:
    if st.button("🔙 Back to Preview"):
        st.switch_page("pages/4_Preview_Changes.py")

with col3:
    if st.button("🗑️ Clear Session"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        init_session_state()
        st.success("Session cleared")
        st.rerun()
