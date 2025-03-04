from footy.player_elo.init_sql import init_sql_db
from footy.player_elo.elo_updater import update_elo
from footy.player_elo.reset_players_elo import reset_init_players_elo_db
import streamlit as st

import logging
import footy.player_elo.elo_updater as elo_updater
from streamlit.logger import get_logger


class StreamlitLogHandler(logging.Handler):
    def __init__(self, widget_update_func):
        super().__init__()
        self.widget_update_func = widget_update_func

    def emit(self, record):
        msg = self.format(record)
        self.widget_update_func(msg)


# def update_log_widget(msg):
#     if "log_history" not in st.session_state:
#         st.session_state.log_history = ""
#     st.session_state.log_history += msg + "\n"
#     st.empty().code(st.session_state.log_history, language="text")


def reset_db():
    try:
        init_sql_db()
        st.success("Reset DB successfully done.")
    except ValueError as e:
        st.error(f"Error during database reset: {e}")


def reset_elo():
    try:
        reset_init_players_elo_db()
        st.success("Reset ELO successfully done.")
    except Exception as e:
        st.error(f"Error during elo reset: {e}")


def run_analysis(process_game_num: int):
    try:
        logger = get_logger(elo_updater.__name__)

        handler = StreamlitLogHandler(st.empty().code)
        # handler = StreamlitLogHandler(st.container().code)
        logger.addHandler(handler)
        update_elo(process_game_num)

        st.success("ELO update completed!")
    except Exception as e:
        st.error(f"ELO update failed: {e}")


def main():
    st.title("Football ELO")
    choice = st.radio(
        "Select a function you wanna use",
        ["Reset DB", "Reset ELO", "Run Analysis", "Display Data"],
        captions=[
            "Reset entire Database and Reinitialise SQL database.",
            "Reset Players ELO to initial state.",
            "Keep running player analysis.",
            "Display analysed data.",
        ],
    )

    if choice == "Reset DB":
        st.write("This will delete and recreate the whole DB from scratch.")
        if st.button("Confirm: Reset Database"):
            reset_db()
    elif choice == "Reset ELO":
        st.write("This resets the 'players ELO' table in the DB.")
        if st.button("Confirm: Reset Players ELO"):
            reset_elo()
    elif choice == "Run Analysis":
        st.write("Update ELO Data")
        process_game_num = st.number_input(
            "Insert a number of games you wanna analyse", value=1, min_value=1, step=10
        )
        if st.button("Confirm: Run ELO Update"):

            run_analysis(process_game_num)


if __name__ == "__main__":
    main()
