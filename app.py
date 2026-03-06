            if selected_rows:
                selected_display_idx = selected_rows[0]
                actual_idx = row_map[selected_display_idx]
                if top[1].button("Open Selected Event", key="open_selected_event"):
                    st.session_state.selected_calendar = actual_idx
                    st.session_state.calendar_mode = "form"
                    st.rerun()
            else:
                top[1].button(
                    "Open Selected Event",
                    disabled=True,
                    key="open_selected_event_disabled",
                )