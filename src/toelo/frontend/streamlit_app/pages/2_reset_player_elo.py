import streamlit as st
from toelo.player_elo.reset_players_elo import reset_init_players_elo_db


def reset_players_elo():
    """Reset the players ELO table of the DB."""
    try:
        reset_init_players_elo_db()
        st.success("Players ELO table reset successfully!")
    except Exception as e:
        st.error(f"Error during resetting player ELO table: {e}")


st.set_page_config(page_title="Reset Player ELO", page_icon="💿")

st.markdown("# Reset Player ELO")
st.sidebar.header("Reset Player ELO")

if st.button("Confirm: Reset ALL players ELO"):
    reset_players_elo()


# Streamlit widgets automatically run the script from top to bottom. Since
# this button is not connected to any other logic, it just causes a plain
# rerun.
st.button("Re-run")
