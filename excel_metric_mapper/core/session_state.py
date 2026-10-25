"""Centralized Streamlit session state initialization."""
from pathlib import Path

import streamlit as st


def init_session_state() -> None:
    """
    Initialize all session keys used across pages.

    Call this at the top of app.py and every page script so direct page
    navigation does not raise AttributeError.
    """
    defaults = {
        "source_data": None,
        "source_metrics": [],
        "target_month": None,
        "workbooks": {},
        "workbook_infos": {},
        "month_headers": {},
        "metric_labels": {},
        "mapping_candidates": [],
        "approved_mappings": [],
        "proposed_changes": [],
        "execution_results": [],
        "output_directory": str(Path("output").resolve()),
        "execution_running": False,
        "map_focus_metric_id": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_session(key: str, default=None):
    """Safe read — never raises if the key was added after the server started."""
    init_session_state()
    return st.session_state.get(key, default)


def set_session(key: str, value) -> None:
    init_session_state()
    st.session_state[key] = value


def ensure_map_focus_metric(metric_ids: list[str]) -> str | None:
    """Return a valid focused metric id for the mapping board."""
    init_session_state()
    if not metric_ids:
        st.session_state["map_focus_metric_id"] = None
        return None
    focus = st.session_state.get("map_focus_metric_id")
    if focus not in metric_ids:
        focus = metric_ids[0]
        st.session_state["map_focus_metric_id"] = focus
    return focus


__all__ = [
    "init_session_state",
    "get_session",
    "set_session",
    "ensure_map_focus_metric",
]
