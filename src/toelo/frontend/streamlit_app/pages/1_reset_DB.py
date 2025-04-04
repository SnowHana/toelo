import streamlit as st
from toelo.player_elo.init_sql import init_sql_db


def reset_db():
    """Recreate the entire SQL DB from scratch."""
    try:
        init_sql_db()
        # validate_games()
        st.success("Database reset successfully!")
    except ValueError as e:
        st.error(f"Error during database reset: {e}")


st.set_page_config(page_title="Reset Database", page_icon="💿")

st.markdown("# Reset Databasse")
st.sidebar.header("Reset Database")

if st.button("Confirm: Reste entier database"):
    reset_db()


# Streamlit widgets automatically run the script from top to bottom. Since
# this button is not connected to any other logic, it just causes a plain
# rerun.
st.button("Re-run")
