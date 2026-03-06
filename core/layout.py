
import streamlit as st
import json

def sidebar_file_controls(data):
    uploaded = st.sidebar.file_uploader("Upload GTD JSON", type="json")

    if uploaded is not None:
        loaded = json.loads(uploaded.getvalue().decode("utf-8"))
        for k in ["actions","calendar","delegations","routines"]:
            if k not in loaded:
                loaded[k] = []
        st.session_state.data = loaded
        st.sidebar.success("GTD file loaded")

    export_json = json.dumps(st.session_state.data, indent=2)

    st.sidebar.download_button(
        "Download Updated GTD",
        export_json,
        "gtd_updated.json",
        "application/json"
    )
