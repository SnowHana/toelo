import subprocess
import sys
from pathlib import Path
from footy.player_elo.game_validator import validate_games
from footy.player_elo.reset_players_elo import reset_init_players_elo_db
from footy.player_elo.init_sql import init_sql_db
from footy.player_elo.elo_updater import update_elo


def reset_db():
    """
    Function to reset the database by executing necessary scripts.
    """
    # init_player_elo.py creates a csv file called player_elo.csv,
    # which had to be runned only ONCE, for entire development! So we don't have to run it again
    # when program is actually used.

    try:
        print("\nResetting database...")
        # Reset db
        init_sql_db()
        validate_games()
        # subprocess.run([sys.executable, str(script_reset_path)], check=True)
        print("Database reset successfully!\n")
    except ValueError as e:
        print(f"Error during database reset: {e}\n")


def reset_players_elo():
    """
    Resets the players ELO table of Postgresql DB
    """
    # Build the absolute path to init_player_elo.py
    try:
        print("\nResetting Players ELO table...")
        reset_init_players_elo_db()
        print("Players ELO Table reset successfully!\n")
    except subprocess.CalledProcessError as e:
        print(f"Error during database reset: {e}\n")


def run_analysis():
    try:
        print("\nRunning analysis...")
        update_elo()
        print("Analysis completed successfully!\n")
    except subprocess.CalledProcessError as e:
        print(f"Error during analysis: {e}\n")


def start_app():
    """
    Main function to display menu and handle user input.
    """
    while True:
        print("\nFootball Database Management Tool")
        print(
            "1. Reset Database : Delete and Create whole SQL DB from scratch. "
            "(Takes up to 3min, don't do this process unless you HAVE TO.)"
        )
        print("2. Reset Players ELO : Re-init. players ELO (Takes less than a minute)")
        print("3. Run Analysis : Continue on analysing ELO.")
        print("4. Exit")

        choice = input("Enter your choice (1/2/3/4): ").strip()

        if choice == "1":
            confirm = input("Do you really want to reset database? (y/n): ").strip()
            if confirm.lower() == "y":
                reset_db()
            else:
                print("Exiting...")
        elif choice == "2":
            reset_players_elo()
        elif choice == "3":
            run_analysis()
        elif choice == "4":
            print("Exiting the program. Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    start_app()
