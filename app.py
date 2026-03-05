# -----------------------------
# Actions
# -----------------------------
if menu == "Actions":

    st.header("Actions")

    if "selected_action" not in st.session_state:
        st.session_state.selected_action = None

    # -------------------------
    # Detail View
    # -------------------------
    if st.session_state.selected_action is not None:

        idx = st.session_state.selected_action
        action = data["actions"][idx]

        st.subheader("Action Detail")

        st.write("Title:", action["title"])
        st.write("Context:", action["context"])
        st.write("Status:", action["status"])

        col1, col2 = st.columns(2)

        if col1.button("Mark Done"):
            data["actions"][idx]["status"] = "Done"
            st.rerun()

        if col2.button("Back"):
            st.session_state.selected_action = None
            st.rerun()

    # -------------------------
    # List View
    # -------------------------
    else:

        for i, item in enumerate(data["actions"]):

            cols = st.columns([6,2])

            if cols[0].button(item["title"], key=f"act_open_{i}"):
                st.session_state.selected_action = i
                st.rerun()

            cols[1].write(item["status"])

        st.divider()

        with st.form("add_action"):

            title = st.text_input("Action")
            context = st.text_input("Context", "@Computer")

            submitted = st.form_submit_button("Add Action")

            if submitted:

                data["actions"].append({
                    "title": title,
                    "context": context,
                    "status": "Open"
                })

                st.rerun()