from typing import Dict, List, Tuple

import psycopg

# Database configuration
DATABASE_CONFIG = {
    'dbname': 'football',
    'user': 'postgres',
    'password': '1234',
    'host': 'localhost',
    'port': '5432'
}

FULL_GAME_MINUTES = 90


# Connect to the database with connection pooling
def connect_to_db():
    """Establish a connection to the PostgreSQL database."""
    return psycopg.connect(**DATABASE_CONFIG)


# Optimized query to get goals scored in a game, grouped by club
def get_goals_in_game_per_club(cur, game_id: int) -> Dict[int, List[int]]:
    """Find goals per club in a single game."""
    cur.execute("""
        SELECT club_id, minute
        FROM game_events
        WHERE type = %s AND game_id = %s
    """, ('Goals', game_id))

    goals_by_club = {}
    for club_id, minute in cur.fetchall():
        goals_by_club.setdefault(club_id, []).append(minute)

    return goals_by_club


# Optimized query for getting player play times in a single call
def get_players_playing_time(cur, game_id: int) -> Dict[Tuple[int, int], Tuple[int, int]]:
    """Calculate playing time for each player in a game."""
    # Step 1: Get starting players' information (assumed to start at 0 and play until subbed out or full game)
    cur.execute("""
           SELECT player_club_id AS club_id, player_id, minutes_played
           FROM appearances
           WHERE game_id = %s
       """, (game_id,))

    starting_players = {}
    for club_id, player_id, minutes_played in cur.fetchall():
        # Start at minute 0, play until substituted out or full game
        end_time = minutes_played if minutes_played > 0 else FULL_GAME_MINUTES
        starting_players[(club_id, player_id)] = (0, end_time)

    # Step 2: Get substitution information
    cur.execute("""
           SELECT club_id, player_id, player_in_id, minute
           FROM game_events
           WHERE type = %s AND game_id = %s
       """, ('Substitutions', game_id))

    # Initialize play time dictionary with starting players
    play_time = starting_players.copy()

    for club_id, player_id, player_in_id, minute in cur.fetchall():
        # Update end time for the player who was subbed out
        if (club_id, player_id) in play_time:
            play_time[(club_id, player_id)] = (play_time[(club_id, player_id)][0], minute)

        # Set start and end times for the player who was subbed in
        play_time[(club_id, player_in_id)] = (minute, FULL_GAME_MINUTES)

    return play_time


# Calculate match impact for players based on goal differential while on pitch
def get_match_impact_players(cur, game_id: int) -> Dict[Tuple[int, int], int]:
    """Calculate goal differential impact for each player in a game."""
    goal_minutes = get_goals_in_game_per_club(cur, game_id)
    play_times = get_players_playing_time(cur, game_id)
    player_goal_impact = {}

    for (club_id, player_id), (start_time, end_time) in play_times.items():
        goals_scored = sum(1 for minute in goal_minutes.get(club_id, []) if start_time <= minute <= end_time)
        goals_conceded = sum(1 for opp_club_id, opp_minutes in goal_minutes.items()
                             if
                             opp_club_id != club_id and any(start_time <= minute <= end_time for minute in opp_minutes))
        player_goal_impact[(club_id, player_id)] = goals_scored - goals_conceded
    return player_goal_impact


# Calculate team rating based on player ELO and minutes played
def get_club_ratings_in_game(cur, game_id: int) -> Dict[int, float]:
    """Calculate the average ELO rating per team based on player participation."""
    cur.execute("""
        SELECT g.home_club_id, g.away_club_id
        FROM games g
        WHERE g.game_id = %s
    """, (game_id,))
    home_club_id, away_club_id = cur.fetchone()

    cur.execute("""
        SELECT a.player_club_id, a.minutes_played, e.elo
        FROM appearances a
        JOIN players_elo e ON a.player_id = e.player_id
        WHERE a.game_id = %s AND EXTRACT(YEAR FROM a.date::date) = e.season
    """, (game_id,))

    total_rating = {home_club_id: 0, away_club_id: 0}
    total_playtime = {home_club_id: 0, away_club_id: 0}
    for club_id, minutes_played, elo in cur.fetchall():
        total_rating[club_id] += minutes_played * elo
        total_playtime[club_id] += minutes_played

    return {
        club_id: total_rating[club_id] / total_playtime[club_id]
        for club_id in (home_club_id, away_club_id) if total_playtime[club_id] > 0
    }


def get_indiv_expectation(cur, game_id: int, opponent_club_id: int, player_id: int) -> float:
    """
    Calculate Individual Expectation E_A_i of a certain player (player_id)
    @param conn:
    @param game_id:
    @param opponent_club_id:
    @param player_id:
    @return:
    """
    # TODO: apply home adavantage
    club_ratings = get_club_ratings_in_game(cur, game_id)
    # Get player rating of that season
    cur.execute("""
            SELECT a.player_club_id, a.minutes_played, e.elo
            FROM appearances a
            JOIN players_elo e ON a.player_id = e.player_id
            WHERE a.game_id = %s AND EXTRACT(YEAR FROM a.date::date) = e.season AND e.player_id = %s
        """, (game_id, player_id))
    elo = cur.fetchone()[-1]
    mod = (club_ratings[opponent_club_id] - elo) / 400
    res = 1 / (1 + pow(10, mod))
    return res


def get_indiv_game_score(player_club_id: int, player_id: int,
                         players_match_impact: Dict[Tuple[int, int], int]) -> float:
    """
    Get S_A_i
    @param player_club_id:
    @param player_id:
    @param players_match_impact:
    @return:
    """
    if players_match_impact[(player_club_id, player_id)] > 0:
        # Win
        return 1
    elif players_match_impact[(player_club_id, player_id)] == 0:
        return 0.5
    else:
        # Lose
        return -1


def get_indiv_change(cur, game_id: int, player_club_id: int, opponent_club_id: int, player_id: int,
                     players_match_impact: Dict[Tuple[int, int], int], weight=1) -> float:
    gd = players_match_impact[(player_club_id, player_id)]
    change = weight * (
            get_indiv_game_score(player_club_id, player_id, players_match_impact)
            - get_indiv_expectation(cur, game_id, opponent_club_id, player_id))
    if gd == 0:
        change = change * pow(abs(gd), 1 / 3)
    else:
        change = change * 1

    return change


# Bulk load CSV data into a table using COPY for optimal performance
def load_csv_to_table(conn, csv_file: str, table_name: str):
    """Load data from a CSV file into the specified PostgreSQL table."""
    with conn.cursor() as cur, open(csv_file, 'r') as f:
        cur.copy_expert(f"COPY {table_name} FROM STDIN WITH CSV HEADER", f)
    print(f"Data from {csv_file} loaded into {table_name}")


# Sample usage with optimized queries and connection handling
try:
    conn = connect_to_db()
    with conn.cursor() as cur:
        # team_rating = get_club_ratings_in_game(cur, 3079452)
        # print("Team Ratings:", team_rating)
        # res = get_indiv_expectation(cur, 3079452, 131, 20506)
        # print(res)
        # get_goals_in_game_per_club(cur, 3079452)
        print(get_players_playing_time(cur, 3079452))
        players_match_impact = get_match_impact_players(cur, 3079452)
        print(players_match_impact)
        # print(get_indiv_game_score(150, 20506, players_match_impact))

except (psycopg.OperationalError, psycopg.ProgrammingError) as e:
    print(f"Database error: {e}")
finally:
    if conn:
        conn.close()
