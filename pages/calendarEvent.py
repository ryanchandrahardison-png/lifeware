
import streamlit as st

data = st.session_state.data

is_edit = (
    st.session_state.calendar_new_mode is False and
    st.session_state.calendar_edit_index is not None
)

title_default = ""
desc_default = ""
status_default = "Scheduled"

if is_edit:
    idx = st.session_state.calendar_edit_index
    ev = data["calendar"][idx]
    title_default = ev.get("title","")
    desc_default = ev.get("description","")
    status_default = ev.get("status","Scheduled")

st.title("📅 Edit Event" if is_edit else "📅 Add Event")

with st.form("calendar_form"):
    title = st.text_input("Title", value=title_default)
    description = st.text_area("Description", value=desc_default)

    status = st.selectbox(
        "Status",
        ["Scheduled","Complete"],
        index=0 if status_default!="Complete" else 1
    )

    if is_edit:
        confirm_delete = st.checkbox("Confirm deletion")
    else:
        confirm_delete = False

    cols = st.columns(3)

    save = cols[0].form_submit_button("Save Changes" if is_edit else "Create Event")
    delete = cols[1].form_submit_button("Delete Event", disabled=not is_edit)
    back = cols[2].form_submit_button("Back to Calendar")

if back:
    st.switch_page("app.py")

if delete and is_edit:
    if not confirm_delete:
        st.error("Confirm deletion first")
    else:
        del data["calendar"][idx]
        st.switch_page("app.py")

if save:
    payload = {
        "title": title,
        "description": description,
        "status": status
    }

    if is_edit:
        data["calendar"][idx].update(payload)
    else:
        data["calendar"].append(payload)

    st.switch_page("app.py")
