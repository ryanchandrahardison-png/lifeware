import json
import streamlit as st

DEFAULT_DATA = {
    "actions": [],
    "calendar": [],
    "delegations": [],
    "routines": [],
    "archived": {},
}


def init_session_state() -> None:
    if "data" not in st.session_state:
        st.session_state.data = DEFAULT_DATA.copy()

    if "uploaded_sig" not in st.session_state:
        st.session_state.uploaded_sig = None

    if "calendar_edit_index" not in st.session_state:
        st.session_state.calendar_edit_index = None

    if "calendar_new_mode" not in st.session_state:
        st.session_state.calendar_new_mode = False



def normalize_loaded_data(loaded: dict) -> dict:
    result = dict(loaded) if isinstance(loaded, dict) else {}
    for key, default in DEFAULT_DATA.items():
        if key not in result:
            result[key] = default.copy() if isinstance(default, dict) else []

    for key in ["actions", "calendar", "delegations", "routines"]:
        if not isinstance(result.get(key), list):
            result[key] = []

    if not isinstance(result.get("archived"), dict):
        result["archived"] = {}

    return result



def load_uploaded_json_once(uploaded_file) -> bool:
    if uploaded_file is None:
        return False

    file_bytes = uploaded_file.getvalue()
    sig = (uploaded_file.name, len(file_bytes))
    if st.session_state.uploaded_sig == sig:
        return False

    loaded = json.loads(file_bytes.decode("utf-8"))
    st.session_state.data = normalize_loaded_data(loaded)
    st.session_state.uploaded_sig = sig
    st.session_state.calendar_edit_index = None
    st.session_state.calendar_new_mode = False
    return True



def export_current_json() -> str:
    return json.dumps(st.session_state.data, indent=2)
