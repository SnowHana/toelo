import numpy as np

from utils import *

BASE_ELO = 1500
ELO_RANGE = 1000


# Create new df

# Create season column for players df...for each season he ran?
def init_players_elo_df(players_df: pd.DataFrame, player_valuations_df: pd.DataFrame) -> pd.DataFrame:
    """
    Init players elo df based on a players_df
    @param player_valuations_df:
    @param players_df:
    @return:
    """
    players_elo_df = players_df.copy()
    players_elo_df['elo'] = None
    # Find seasons player played for each season
    df_sorted = add_season_column(player_valuations_df)
    df_sorted = df_sorted.loc[df_sorted.groupby(['player_id', 'season'])['date'].idxmin()]
    # seasons = sorted(oldest_player_valuations_df['season'].unique())
    players_elo_df = players_elo_df.merge(
        df_sorted[['player_id', 'season']],
        on='player_id',
        how='left'
    )

    return players_elo_df


def is_enough_data_to_init_elo(appearances_df: pd.DataFrame, games_df: pd.DataFrame, players_elo_df: pd.DataFrame,
                               player_id, game_id):
    """
    Decide if we should use
    1. Squad's average ELO
    2. Player's market value of that time
    to initialize the player's ELO.
    Assumes the player's ELO needs initialization.
    @param appearances_df:
    @param games_df:
    @param players_elo_df:
    @param player_id:
    @param game_id:
    @return:
    """
    # Retrieve teammates (excluding the player themselves)
    teammates = appearances_df.loc[(appearances_df['game_id'] == game_id) & (appearances_df['player_id'] != player_id)]

    # Get the season of the game
    if game_id not in games_df['game_id'].values:
        return None  # Return None if the game_id is invalid

    season = games_df.loc[games_df['game_id'] == game_id, 'season'].iloc[0]

    if teammates.empty:
        # No teammates found, use player's market value for initialization
        return None
    else:
        # Pre-filter players_elo_df for teammates in the given season
        teammate_ids = teammates['player_id'].unique()
        teammate_elo_df = players_elo_df[(players_elo_df['player_id'].isin(teammate_ids)) &
                                         (players_elo_df['season'] == season)]

        # Drop rows without an ELO to handle missing values
        teammate_elos = teammate_elo_df['elo'].dropna()

        # Check if enough ELO data exists
        if len(teammate_elos) >= len(teammate_ids) / 2:
            # More than half of teammates have ELOs, so return their average
            return teammate_elos.mean()
        else:
            # Not enough data, use market value instead
            return None


def init_player_elo_with_player_value(player_valuations_df: pd.DataFrame, players_elo_df: pd.DataFrame, player_id,
                                      season, base_elo=BASE_ELO, elo_range=ELO_RANGE, season_valuations=None):
    """
    Initialize a player's ELO based on their market value for a given season.
    @param players_elo_df:
    @param player_valuations_df:
    @param player_id: The ID of the player.
    @param season: The season to calculate the ELO for.
    """
    # TODO: Later, to optimize, we can do sth like calculate z-score of all players by season
    # So that we don't have to repeat the process?
    # Get the player's market value for the specific season
    if season_valuations is None or season not in season_valuations:
        # print("Season Valuation not valid, or not in a season")
        return base_elo  # handle cases where season stats are unavailable
    season_mean = season_valuations[season]['mean']
    season_std = season_valuations[season]['std']
    # Convert season in the dataframe to the same type as the variable `season`
    player_valuations_df['season'] = player_valuations_df['season'].astype(type(season))

    # Now perform the query
    player_value = player_valuations_df.loc[(player_valuations_df['player_id'] == player_id) &
                                            (player_valuations_df['season'] == season), 'market_value_in_eur']

    if player_value.empty:
        # No market value available for this player in the given season, returning a base ELO
        # print('No player market value found, returning a base ELO')
        return base_elo
    else:
        # Get market values for all players in the season to normalize
        # season_values = player_valuations_df.loc[
        #     player_valuations_df['season'] == season, 'market_value_in_eur'].dropna()
        # season_values_log = np.log1p(season_values)  # Log transformation

        # Calculate the z-score for the player's market value
        # print(f"Market Value of player: {player_value.values[0]}")
        # print(f"Avg market value of players: {season_mean}")
        # print(f"Std dev. of players: {season_std}")

        # Calculate z-scores and cap them to prevent extreme ELOs
        # Compute the z-score using precomputed season stats
        player_z_score = (np.log1p(player_value.values[0]) - season_mean) / season_std
        # NOTE: Cap the z-score to prevent maximum ELOs
        # TODO: Think of better approach
        # e.g.) Ronaldo in 2015 gives ELO of 4800, Messi in 2012 gives ELO of 5400, which is not ideal
        # This doens't really work as well...

        # Calculate the player's ELO based on their z-score
        player_elo = base_elo + (player_z_score * (elo_range / 2))
        # print(f"Player ELO: {player_elo}")
        return player_elo


def init_player_elo(appearances_df: pd.DataFrame, games_df: pd.DataFrame, players_elo_df: pd.DataFrame, player_id,
                    game_id, season_valuations):
    """
    Init player's elo of player id, at game_id
    @param appearances_df:
    @param games_df:
    @param players_elo_df:
    @param season_valuations:
    @param player_id:
    @param game_id:
    @return:
    """
    # 1. Get player's club (at that time)
    player_appearance = appearances_df.loc[(appearances_df['game_id'] == game_id) \
                                           & (appearances_df['player_id'] == player_id)]
    if player_appearance.empty:
        # Error: No such player
        raise ValueError("No result found for player {} in game {}".format(player_id, game_id))
    club = player_appearance['player_club_id']

    # 2. and check if we have enough elo data of that club
    elo_value = is_enough_data_to_init_elo(appearances_df, games_df, players_elo_df, player_id, game_id)
    # season = games_df.loc[games_df['game_id'] == game_id]['season']
    season = games_df.loc[games_df['game_id'] == game_id, 'season'].iloc[0]
    if elo_value is None:
        # We need to manually calculate elo_value based on his market value of taht time
        # print(season)
        print("Init with player market value")
        elo_value = init_player_elo_with_player_value(player_valuations_df, players_elo_df, player_id, season,
                                                      season_valuations=season_valuations)

    # print(f"Elo value {elo_value} for player {player_id}")
    # 3. Now set player elo of that time
    players_elo_df.loc[(players_elo_df['player_id'] == player_id) \
                       & (players_elo_df['season'] == season), 'elo'] = elo_value
    # NOTE: We can also add feature like looking up player's elo of prev / next season.
    # Note, that, since we chronologically loop through games, his teammate's elo will be elo of that time!
    # However, be careful finding out which club he was playing for at THAT time.
    return players_elo_df


def get_player_elo(players_df: pd.DataFrame, player_id, game_id):
    """
    Get player {player_id} elo, and if elo is not initialised, it will initialise the player's elo.
    @param player_id: player's id
    @return: player['elo'], integer
    """
    player: pd.DataFrame = players_df.loc[players_df['player_id'] == player_id]
    # If there is multiple....
    if len(player) > 1:
        raise ValueError(f"Multiple results found for player {player_id}. Expected only one")
    elif len(player) == 0:
        raise ValueError(f"No results found for player {player_id}")

    # Nothing went wrong
    elo_value = player.get('elo')
    if elo_value is not None:
        # Elo value exists, do something with it
        # print(f"Elo value exists for player {player_id}!")
        return player['elo']
    else:
        # Handle the case where 'elo' column doesn't exist or is empty
        # print("Player DataFrame doesn't have an 'elo' column or values are empty")
        # print(f"Empty elo_value for player {player_id}, initialising.")
        return init_player_elo(appearances_df, games_df, players_elo_df, player_id, game_id, season_valuations)


#
# def test_init_player_elo_with_market_value():
#     # Now Testing
#     sample_player_names = {'Lionel Messi': '2015', 'Ronaldo': '2015', 'Federico Valverde': '2020', 'Eric Dier': '2015', \
#                            'Nacho Fernández': '2020'}
#     # seasons = ['2015', '2015', '2020', '2020', '2020']
#     # ronaldo = players_df.loc[players_df['name'].str.contains('Lionel Messi')]
#     ronaldo = players_df.loc[players_df['name'].str.contains('Ronaldo')]
#     # ronaldo = players_df.loc[players_df['name'].str.contains('Federico Valverde')]
#     # ronaldo = players_df.loc[players_df['name'].str.contains('Eric Dier')]
#     # ronaldo = players_df.loc[players_df['name'].str.contains('Nacho Fernández')]
#     # season = '2020'
#     season = '2015'
#     ronaldo_id = ronaldo['player_id'].values[0]
#     ronaldo_games = appearances_df.loc[appearances_df['player_id'] == ronaldo_id]
#     print(ronaldo)
#     # print(ronaldo_games)
#     # res = is_enough_data_to_init_elo(appearances_df, games_df, players_elo_df, ronaldo_id,
#     #                                  ronaldo_games['game_id'].values[0])
#     # if res is None:
#     #     print("Not enough data of teammates to init ronlaod's elo based on them!")
#     # else:
#     #     print("We have enough data???")
#     for player_name, season in sample_player_names.items():
#         player = players_df.loc[players_df['name'].str.contains(player_name)]
#         player_id = player['player_id'].values[0]
#         ronaldo_games = appearances_df.loc[appearances_df['player_id'] == player_id]
#         print(f"Player {player['name'].values[0]} info.")
#         init_player_elo_with_player_value(player_valuations_df, players_elo_df, player_id, season \
#                                           , season_valuations=season_valuations)


def main():
    """
    Main fn.
    """
    # Define all DataFrames globally as empty initially
    global competitions_df, appearances_df, player_valuations_df, game_events_df
    global players_df, games_df, club_games_df, clubs_df, players_elo_df

    # Initialize each as empty DataFrame
    competitions_df = pd.DataFrame()
    appearances_df = pd.DataFrame()
    player_valuations_df = pd.DataFrame()
    game_events_df = pd.DataFrame()
    players_df = pd.DataFrame()
    games_df = pd.DataFrame()
    club_games_df = pd.DataFrame()
    clubs_df = pd.DataFrame()
    players_elo_df = pd.DataFrame()

    # Import CSV data
    dataframes = import_data_from_csv()  # Load dataframes from CSVs

    # Map your predefined variables to their respective keys in the dictionary
    variable_mapping = {
        'competitions_df': 'competitions',
        'appearances_df': 'appearances',
        'player_valuations_df': 'player_valuations',
        'game_events_df': 'game_events',
        'players_df': 'players',
        'games_df': 'games',
        'club_games_df': 'club_games',
        'clubs_df': 'clubs',
        'players_elo_df': 'players_elo'
    }

    # Update each predefined variable with its corresponding data from the dictionary
    for var_name, file_name in variable_mapping.items():
        if file_name in dataframes:
            globals()[var_name] = dataframes[file_name].copy()

    # for file_name, dataframe in dataframes.items():
    #     exec(f"{file_name} = dataframe.copy()")
    #     # print(file_name)
    #     # print(dataframe)
    #
    # dataframes = import_data_from_csv()  # Load dataframes from CSVs
    #
    # # Map your predefined variables to their respective keys in the dictionary
    # variable_mapping = {
    #     'competitions_df': 'competitions',
    #     'appearances_df': 'appearances',
    #     'player_valuations_df': 'player_valuations',
    #     'game_events_df': 'game_events',
    #     'players_df': 'players',
    #     'games_df': 'games',
    #     'club_games_df': 'club_games',
    #     'clubs_df': 'clubs',
    #     'players_elo_df': 'players_elo'
    # }
    #
    # # Update each predefined variable with its corresponding data from the dictionary
    # for var_name, file_name in variable_mapping.items():
    #     globals()[var_name] = dataframes.get(file_name, pd.DataFrame()).copy()

    # print(games_df)
    games_df = sort_df_by_date(games_df)
    games_df = add_season_column(games_df)
    player_valuations_df = add_season_column(player_valuations_df)

    players_elo_df = init_players_elo_df(players_df, player_valuations_df)
    # Calculate season_valuations
    season_valuations = {}
    for season in player_valuations_df['season'].unique():
        season_values = player_valuations_df.loc[
            player_valuations_df['season'] == season, 'market_value_in_eur'].dropna()
        season_values_log = np.log1p(season_values)
        season = np.int64(season)
        season_valuations[season] = {
            'mean': season_values_log.mean(),
            'std': season_values_log.std()
        }

    for index, row in appearances_df.sample(n=10).iterrows():
        player_id = row['player_id']
        game_id = row['game_id']
        init_player_elo(appearances_df, games_df, players_elo_df, player_id, game_id, season_valuations)

        print("##############################")
    print("DONE")
    #
    # sample_df = appearances_df.head(10)
    # for index, col in sample_df.iterrows():
    #     print(get_player_elo(col['player_id'], col['game_id']))


if __name__ == "__main__":
    main()
