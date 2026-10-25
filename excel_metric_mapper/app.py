"""Excel Metric Mapper - Main Streamlit Application."""
import streamlit as st
from pathlib import Path

from core.session_state import init_session_state

# Page configuration
st.set_page_config(
    page_title="Excel Metric Mapper",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_session_state()

# Title and description
st.title("📊 Excel Metric Mapper")
st.markdown("""
**Discover and populate monthly metrics in Excel workbooks safely.**

This application helps you:
- Load normalized source metrics
- Discover metric locations in varied Excel layouts
- Review and approve mappings with confidence scores
- Preview changes before writing
- Generate output copies without modifying originals
""")

# Sidebar navigation
st.sidebar.title("Navigation")
st.sidebar.markdown("---")

# Show current state
st.sidebar.subheader("Current State")

if st.session_state.source_metrics:
    st.sidebar.success(f"✓ {len(st.session_state.source_metrics)} source metrics loaded")
else:
    st.sidebar.info("○ No source data loaded")

if st.session_state.target_month:
    st.sidebar.success(f"✓ Target month: {st.session_state.target_month}")
else:
    st.sidebar.info("○ No target month selected")

if st.session_state.workbooks:
    st.sidebar.success(f"✓ {len(st.session_state.workbooks)} workbook(s) loaded")
else:
    st.sidebar.info("○ No workbooks loaded")

if st.session_state.mapping_candidates:
    approved = sum(1 for c in st.session_state.mapping_candidates if c.state == 'approved')
    st.sidebar.success(f"✓ {approved}/{len(st.session_state.mapping_candidates)} mappings approved")
else:
    st.sidebar.info("○ No mappings discovered")

st.sidebar.markdown("---")

# Workflow steps
st.sidebar.subheader("Workflow Steps")
st.sidebar.page_link("pages/1_Source_Data.py", label="1️⃣ Load Source Data")
st.sidebar.page_link("pages/2_Workbooks.py", label="2️⃣ Load Workbooks")
st.sidebar.page_link("pages/3_Discover_and_Map.py", label="3️⃣ Discover & Map")
st.sidebar.page_link("pages/4_Preview_Changes.py", label="4️⃣ Preview Changes")
st.sidebar.page_link("pages/5_Run_and_Audit.py", label="5️⃣ Run & Audit")

# Main content
st.header("Getting Started")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("1. Prepare Source Data")
    st.markdown("""
    Upload a CSV or Excel file with columns:
    - `metric_id`
    - `metric_name`
    - `reporting_month`
    - `value`
    - `unit`
    """)
    if st.button("📂 Load Source Data", use_container_width=True):
        st.switch_page("pages/1_Source_Data.py")

with col2:
    st.subheader("2. Upload Workbooks")
    st.markdown("""
    Upload one or more Excel workbooks (.xlsx or .xlsm) that need to be updated.
    
    The app will inspect them without modification.
    """)
    if st.button("📁 Load Workbooks", use_container_width=True):
        st.switch_page("pages/2_Workbooks.py")

with col3:
    st.subheader("3. Discover & Map")
    st.markdown("""
    Automatically discover:
    - Month headers
    - Metric labels
    - Target cells
    
    Review and approve mappings.
    """)
    if st.button("🔍 Discover Mappings", use_container_width=True):
        st.switch_page("pages/3_Discover_and_Map.py")

st.markdown("---")

st.header("Features")

col1, col2 = st.columns(2)

with col1:
    st.subheader("✨ Smart Discovery")
    st.markdown("""
    - Handles horizontal and vertical month layouts
    - Recognizes various month formats (Excel dates, ISO strings, month names)
    - Fuzzy matching for metric labels
    - Confidence scoring for each mapping
    - Ambiguity detection
    """)
    
    st.subheader("🔒 Safe Writing")
    st.markdown("""
    - Creates output copies, never modifies originals
    - Preserves formulas, charts, and formatting
    - Verification after writing
    - Detailed audit trail
    """)

with col2:
    st.subheader("📊 Flexible Input")
    st.markdown("""
    - CSV or Excel source files
    - Multiple target workbooks
    - Multi-sheet workbooks
    - Macro-enabled files (.xlsm)
    """)
    
    st.subheader("🎯 User Control")
    st.markdown("""
    - Review all mappings before applying
    - Manual override for ambiguous cases
    - Preview changes with warnings
    - Dry-run mode
    """)

st.markdown("---")

# Quick stats
if st.session_state.source_metrics or st.session_state.workbooks:
    st.header("Session Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Source Metrics", len(st.session_state.source_metrics))
    
    with col2:
        st.metric("Workbooks", len(st.session_state.workbooks))
    
    with col3:
        total_mappings = len(st.session_state.mapping_candidates)
        st.metric("Discovered Mappings", total_mappings)
    
    with col4:
        approved = sum(1 for c in st.session_state.mapping_candidates if c.state == 'approved')
        st.metric("Approved", approved)

# Footer
st.markdown("---")
st.caption("Excel Metric Mapper v1.0 - Local-first Python application")
