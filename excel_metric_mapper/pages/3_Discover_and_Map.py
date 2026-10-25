"""Page 3: Discover & Map — metric-centric mapping board."""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.discovery import find_metric_labels, find_month_headers
from core.mapping_actions import (
    bulk_approve_high_confidence,
    bulk_reject_ambiguous,
    candidate_key,
    coverage_summary,
    filter_candidates,
    set_winner,
    target_metrics_for_month,
)
from core.models import MappingCandidate
from core.scoring import propose_mappings
from core.session_state import init_session_state
from core.worksheet_preview import build_preview_dataframe, style_preview


def _ensure_map_focus_metric(metric_ids: list[str]) -> str | None:
    """Local helper so this page works even if Streamlit cached an older core.session_state."""
    init_session_state()
    if not metric_ids:
        st.session_state["map_focus_metric_id"] = None
        return None
    focus = st.session_state.get("map_focus_metric_id")
    if focus not in metric_ids:
        focus = metric_ids[0]
        st.session_state["map_focus_metric_id"] = focus
    return focus


def _format_option(c: MappingCandidate) -> str:
    flags = []
    if c.state == "approved":
        flags.append("✅")
    elif c.state == "ambiguous":
        flags.append("⚠️")
    elif c.state == "blocked":
        flags.append("🚫")
    if c.has_formula:
        flags.append("formula")
    flag = " ".join(flags)
    return (
        f"{flag} {c.workbook_name} / {c.sheet_name} → {c.target_value_cell} "
        f"({c.confidence:.0%})"
    )


st.set_page_config(page_title="Discover & Map", page_icon="🔍", layout="wide")
init_session_state()

st.title("🔍 Discover & Map")
st.caption(
    f"Target month **{st.session_state.target_month or '—'}** · "
    "Pick one target cell per metric (auto-discovery is a suggestion, not the final answer)."
)

if not st.session_state.source_metrics:
    st.warning("Load source data first.")
    if st.button("Go to Source Data"):
        st.switch_page("pages/1_Source_Data.py")
    st.stop()

if not st.session_state.workbooks:
    st.warning("Load at least one workbook.")
    if st.button("Go to Workbooks"):
        st.switch_page("pages/2_Workbooks.py")
    st.stop()

if not st.session_state.target_month:
    st.warning("Select a reporting month on the Source Data page.")
    st.stop()

metrics = target_metrics_for_month(
    st.session_state.source_metrics,
    st.session_state.target_month,
)

# --- Discovery controls ---
with st.container(border=True):
    st.subheader("Step 1 · Run discovery")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        max_rows = st.number_input("Scan rows", 10, 500, 120, key="disc_rows")
    with c2:
        max_cols = st.number_input("Scan cols", 10, 100, 40, key="disc_cols")
    with c3:
        min_confidence = st.slider("Min confidence to show", 0.0, 1.0, 0.45, 0.05)
    with c4:
        st.write("")
        run_discovery = st.button("Run discovery", type="primary", use_container_width=True)

if run_discovery:
    st.session_state.mapping_candidates = []
    st.session_state.month_headers = {}
    st.session_state.metric_labels = {}
    progress = st.progress(0.0, text="Starting…")
    step = 0
    total = max(1, len(st.session_state.workbooks) * 3)

    for workbook_name, workbook_path in st.session_state.workbooks.items():
        info = st.session_state.workbook_infos[workbook_name]
        headers, labels = [], []

        progress.progress(step / total, text=f"{workbook_name}: month headers…")
        for sheet_name in info.sheets:
            headers.extend(
                find_month_headers(
                    workbook_path,
                    sheet_name,
                    target_month=st.session_state.target_month,
                    max_rows=max_rows,
                    max_cols=max_cols,
                )
            )
        step += 1
        st.session_state.month_headers[workbook_name] = headers

        progress.progress(step / total, text=f"{workbook_name}: metric labels…")
        for sheet_name in info.sheets:
            labels.extend(
                find_metric_labels(
                    workbook_path,
                    sheet_name,
                    st.session_state.source_metrics,
                    max_rows=max_rows,
                    max_cols=max_cols,
                )
            )
        step += 1
        st.session_state.metric_labels[workbook_name] = labels

        progress.progress(step / total, text=f"{workbook_name}: propose mappings…")
        st.session_state.mapping_candidates.extend(
            propose_mappings(
                workbook_path=workbook_path,
                workbook_info=info,
                source_metrics=st.session_state.source_metrics,
                month_headers=headers,
                metric_labels=labels,
                target_month=st.session_state.target_month,
                min_confidence=min_confidence,
            )
        )
        step += 1

    progress.progress(1.0, text="Done")
    st.success(f"Found {len(st.session_state.mapping_candidates)} candidate(s).")
    st.rerun()

candidates: list[MappingCandidate] = st.session_state.mapping_candidates

if not candidates:
    st.info("Run discovery to generate suggestions, then confirm each metric on the board below.")
    st.stop()

# --- Coverage board ---
st.subheader("Step 2 · Metric coverage")
summary = coverage_summary(
    st.session_state.source_metrics,
    candidates,
    st.session_state.target_month,
)
summary_df = pd.DataFrame(summary)
st.dataframe(
    summary_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "status": st.column_config.TextColumn("Status", width="small"),
        "source_value": st.column_config.NumberColumn("Source value", format="%.4g"),
    },
)

mapped = sum(1 for r in summary if r["approved"] > 0)
st.progress(mapped / max(1, len(summary)), text=f"{mapped} of {len(summary)} metrics have an approved mapping")

# --- Bulk tools ---
with st.expander("Bulk actions", expanded=False):
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("Approve best match per metric (≥80%)", use_container_width=True):
            n = bulk_approve_high_confidence(candidates, 0.8)
            st.success(f"Approved {n} mapping(s).")
            st.rerun()
    with b2:
        if st.button("Reject all ambiguous", use_container_width=True):
            n = bulk_reject_ambiguous(candidates)
            st.success(f"Rejected {n} ambiguous candidate(s).")
            st.rerun()
    with b3:
        thr = st.number_input("Threshold", 0.0, 1.0, 0.85, 0.05, key="bulk_thr")
        if st.button(f"Approve best ≥ {thr:.0%}", use_container_width=True):
            n = bulk_approve_high_confidence(candidates, thr)
            st.success(f"Approved {n} mapping(s).")
            st.rerun()

# --- Metric-centric review ---
st.subheader("Step 3 · Review & choose target cell")

metric_ids = [m.metric_id for m in metrics]
focus_default = _ensure_map_focus_metric(metric_ids)
if focus_default is None:
    st.stop()

left, right = st.columns([1, 2], gap="large")

with left:
    focus = st.radio(
        "Source metric",
        metric_ids,
        index=metric_ids.index(focus_default),
        format_func=lambda mid: next(
            (f"{mid} · {r['status']}" for r in summary if r["metric_id"] == mid),
            mid,
        ),
        key="focus_metric_radio",
    )
    st.session_state["map_focus_metric_id"] = focus
    src = next(m for m in metrics if m.metric_id == focus)
    st.metric("Value to write", f"{src.value:g} {src.unit}")
    st.markdown(f"**{src.metric_name}**")

    related = [c for c in candidates if c.metric_id == focus]
    st.markdown(f"**{len(related)}** suggestion(s) for this metric")

with right:
    related = sorted(
        [c for c in candidates if c.metric_id == focus],
        key=lambda c: (-c.confidence, c.workbook_name, c.sheet_name, c.target_value_cell),
    )

    if not related:
        st.warning("No auto-match for this metric. Add a manual mapping below.")
    else:
        options = [candidate_key(c) for c in related]
        approved_keys = [candidate_key(c) for c in related if c.state == "approved"]
        default_idx = options.index(approved_keys[0]) if approved_keys else 0

        choice_key = st.radio(
            "Select the correct target (one per workbook)",
            options,
            index=default_idx,
            format_func=lambda k: _format_option(next(c for c in related if candidate_key(c) == k)),
            key=f"pick_{focus}",
        )
        chosen = next(c for c in related if candidate_key(c) == choice_key)

        d1, d2, d3 = st.columns(3)
        with d1:
            if st.button("Use this mapping", type="primary", use_container_width=True):
                set_winner(candidates, chosen)
                st.rerun()
        with d2:
            if st.button("Reject this option", use_container_width=True):
                chosen.state = "rejected"
                st.rerun()
        with d3:
            st.caption(f"State: **{chosen.state}** · Confidence **{chosen.confidence:.0%}**")

        with st.expander("Why this was suggested", expanded=False):
            st.write(chosen.match_evidence)
            if chosen.has_formula:
                st.error("Target cell contains a formula — choose another cell or edit the sheet.")
            if chosen.existing_value not in (None, ""):
                st.warning(f"Current cell value: {chosen.existing_value}")

        try:
            preview_df = build_preview_dataframe(chosen, radius=4)
            st.markdown("**Worksheet preview** (yellow = write here)")
            st.dataframe(style_preview(preview_df), use_container_width=True, height=320)
        except Exception as exc:
            st.error(f"Could not render preview: {exc}")

    st.markdown("---")
    st.markdown("**Manual override** — if discovery picked the wrong cell")
    with st.form("manual_map_form", clear_on_submit=True):
        m1, m2, m3 = st.columns(3)
        with m1:
            wb_name = st.selectbox("Workbook", list(st.session_state.workbooks.keys()))
        with m2:
            sheet = st.selectbox(
                "Sheet",
                list(st.session_state.workbook_infos[wb_name].sheets.keys()),
            )
        with m3:
            cell = st.text_input("Cell", placeholder="e.g. H12").strip().upper()
        notes = st.text_input("Note (optional)")
        if st.form_submit_button("Add manual mapping (auto-approved)"):
            if not cell:
                st.error("Enter a cell address.")
            else:
                info = st.session_state.workbook_infos[wb_name]
                manual = MappingCandidate(
                    workbook_path=st.session_state.workbooks[wb_name],
                    workbook_name=wb_name,
                    workbook_fingerprint=info.fingerprint,
                    sheet_name=sheet,
                    metric_id=src.metric_id,
                    metric_name=src.metric_name,
                    source_value=src.value,
                    source_unit=src.unit,
                    target_month=st.session_state.target_month,
                    orientation="horizontal",
                    metric_label_cell="MANUAL",
                    month_header_cell="MANUAL",
                    target_value_cell=cell,
                    confidence=1.0,
                    match_evidence=f"Manual mapping: {notes or 'user override'}",
                    state="approved",
                )
                candidates.append(manual)
                set_winner(candidates, manual)
                st.success(f"Mapped {src.metric_id} → {sheet}!{cell}")
                st.rerun()

st.markdown("---")
approved_count = sum(1 for c in candidates if c.state == "approved")
nav1, nav2, nav3 = st.columns([1, 2, 1])
with nav1:
    if st.button("← Workbooks"):
        st.switch_page("pages/2_Workbooks.py")
with nav3:
    if approved_count:
        if st.button(f"Preview {approved_count} change(s) →", type="primary"):
            st.session_state.proposed_changes = []
            st.switch_page("pages/4_Preview_Changes.py")
    else:
        st.button("Preview changes →", disabled=True)
