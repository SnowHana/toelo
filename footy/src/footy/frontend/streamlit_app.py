import streamlit as st
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


def run_analysis():
    """Run your ELO updating/analysis process."""
    try:
        update_elo()
        st.success("Analysis completed successfully!")
    except Exception as e:
        st.error(f"Error during analysis: {e}")


def main():
    st.title("Football Database Management Tool")

    # Create a simple sidebar or radio buttons to choose the action
    choice = st.radio(
        "Choose an action", ("Reset Database", "Reset Players ELO", "Run Analysis")
    )

    if choice == "Reset Database":
        st.write("This will delete and recreate the whole DB from scratch.")
        if st.button("Confirm: Reset Database"):
            reset_db()

    elif choice == "Reset Players ELO":
        st.write("This resets the 'players ELO' table in the DB.")
        if st.button("Confirm: Reset Players ELO"):
            reset_players_elo()

    elif choice == "Run Analysis":
        st.write("Update ELO data.")
        if st.button("Run Analysis"):
            run_analysis()


if __name__ == "__main__":
    main()
