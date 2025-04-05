import streamlit as st
import io
import logging

from toelo.player_elo.elo_updater import update_elo


def update_players_elo(process_game_num: int):

    # 2a) Capture logs in a string buffer
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    logger = logging.getLogger()  # root logger
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    # Show a spinner while the function is running
    with st.spinner("Running ELO update..."):
        try:
            update_elo(process_game_num)  # <-- Single, long process
            st.success("ELO update completed!")
        except Exception as e:
            st.error(f"ELO update failed: {e}")

    # 2c) Retrieve logs from the buffer and display them
    handler.flush()
    log_text = log_stream.getvalue()
    st.text_area("Log Output", log_text, height=300)

    # 2d) Remove the handler to avoid duplicate logs
    logger.removeHandler(handler)


st.set_page_config(page_title="Run ELO Analysis", page_icon="🔬")

st.markdown("# Run ELO Analysis")
st.sidebar.header("Run ELO Analysis")
process_game_num = st.number_input("Number of games to process", min_value=1, step=10)
if st.button("Run ELO Update"):
    update_players_elo(process_game_num)


# Streamlit widgets automatically run the script from top to bottom. Since
# this button is not connected to any other logic, it just causes a plain
# rerun.
st.button("Re-run")
