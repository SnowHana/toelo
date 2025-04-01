from footy.player_elo.display_data import get_player_data
import streamlit as st
import logging
import io

from footy.player_elo.game_validator import validate_games
from footy.player_elo.reset_players_elo import reset_init_players_elo_db
from footy.player_elo.init_sql import init_sql_db
from footy.player_elo.elo_updater import update_elo


def reset_db():
    """Recreate the entire SQL DB from scratch."""
    try:
        init_sql_db()
        validate_games()
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
    query = "SELECT * FROM players_elo LIMIT 1000;"
    data = get_player_data(query)
    st.dataframe(data)


def main():
    st.title("Football Player ELO Analyse")

    # Radio to pick which operation
    choice = st.radio(
        "Choose an action",
        ("Reset Database", "Reset Players ELO", "Run Analysis", "Display Data"),
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


if __name__ == "__main__":
    main()
