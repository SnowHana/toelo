import numpy as np
import pandas as pd
from toelo.player_elo.display_data import (
    get_player_data,
    plot_top_elo_players,
    get_player_names,
)
import streamlit as st
import logging
import io

from toelo.player_elo.game_validator import validate_games
from toelo.player_elo.reset_players_elo import reset_init_players_elo_db
from toelo.player_elo.init_sql import init_sql_db
from toelo.player_elo.elo_updater import update_elo


def reset_db():
    """Recreate the entire SQL DB from scratch."""
    try:
        init_sql_db()
        # validate_games()
        st.success("Database reset successfully!")
    except ValueError as e:
        st.error(f"Error during database reset: {e}")


def reset_players_elo():
    """Reset the players ELO table of the DB."""
    try:
        reset_init_players_elo_db()
        st.success("Players ELO table reset successfully!")
    except Exception as e:
        st.error(f"Error during resetting player ELO table: {e}")


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


def display_player_data():
    st.title("Player Data")
    st.plotly_chart(plot_top_elo_players())

    query = "SELECT * FROM players_elo LIMIT 200;"
    data = get_player_data(query)
    st.dataframe(data)


def display_player_elo():
    st.title("Individual Players' ELO")

    # Text input with a key so we can track it
    player_name_q = st.text_input(
        "Enter the player name you want to search:", key="player_name"
    )

    st.write("Player name ", player_name_q)

    # # Confirm button
    # if st.button("Confirm"):
    #     st.session_state["confirmed_name"] = st.session_state["player_name"]

    # # Show result if confirmed
    # if "confirmed_name" in st.session_state:
    #     st.write("Current name is:", st.session_state["confirmed_name"])
    # Search database to get candidates of player_names
    # player_name_choices = get_player_names(player_name_q)
    # st.write(player_name_choices)
    # st.write("SUCCESS")
    # chart_data = pd.DataFrame(
    #     {
    #         "col1": np.random.randn(20),
    #         "col2": np.random.randn(20),
    #         "col3": np.random.choice(["A", "B", "C"], 20),
    #     }
    # )

    # st.line_chart(chart_data, x="col1", y="col2", color="col3")


def main():
    st.title("Football Player ELO Analyse")

    # Radio to pick which operation
    choice = st.radio(
        "Choose an action",
        (
            "Reset Database",
            "Reset Players ELO",
            "Run Analysis",
            "Display Data",
            "Display Player ELO",
        ),
    )

    # ========== RESET DB ==========
    if choice == "Reset Database":
        st.write("This will delete and recreate the whole DB from scratch.")
        if st.button("Confirm: Reset Database"):
            reset_db()

    # ========== RESET PLAYERS ELO ==========
    elif choice == "Reset Players ELO":
        st.write("This resets the 'players ELO' table in the DB.")
        if st.button("Confirm: Reset Players ELO"):
            reset_players_elo()

    # ========== RUN ANALYSIS (ELO UPDATE) ==========
    elif choice == "Run Analysis":
        st.write("Update ELO data.")
        # 1) Let the user pick how many games to process
        process_game_num = st.number_input(
            "Number of games to process", min_value=1, step=10
        )

        # 2) Button that triggers the ELO update
        if st.button("Run ELO Update"):
            update_players_elo(process_game_num)
    elif choice == "Display Data":
        st.write("Display Data.")
        if st.button("Confirm: Display Data"):
            display_player_data()
    elif choice == "Display Player ELO":
        st.write("Display Individual Player ELO")
        if st.button("Confirm: Display Individual Player ELO Data"):
            display_player_elo()


if __name__ == "__main__":
    main()
