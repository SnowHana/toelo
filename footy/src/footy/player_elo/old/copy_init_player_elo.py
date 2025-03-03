import os
from pathlib import Path

import numpy as np
import pandas as pd

BASE_ELO = 1500
ELO_RANGE = 300


class PlayerEloInitializer:
    """Initialize Player ELO based on various criteria."""

    def __init__(self, base_dir: Path = None, base_elo=BASE_ELO, elo_range=ELO_RANGE):
        self.elo_range = elo_range
        self.base_elo = base_elo
        self.base_dir = base_dir or Path(__file__).resolve().parent
        self.data_dir = self.base_dir.parents[0] / 'data' / 'transfer_data'
        self.dataframes = self._import_dataframes()

        # Assign dataframes
        self.appearances_df = self.dataframes.get('appearances_df')
        self.games_df = self.dataframes.get('games_df')
        self.players_df = self.dataframes.get('players_df')
        self.player_valuations_df = self.dataframes.get('player_valuations_df')
        self.players_elo_df = self.dataframes.get('players_elo_df', self._init_players_elo_df())

        # Initialize season valuations
        self.season_valuations = self._init_season_valuations()

    def _import_dataframes(self) -> dict:
        """Read data from CSV files and store as DataFrames."""
        dataframes = {}
        for dirpath, _, filenames in os.walk(self.data_dir):
            for filename in filenames:
                file_key = f"{filename.split('.')[0]}_df"
                filepath = os.path.join(dirpath, filename)
                dataframes[file_key] = pd.read_csv(filepath, sep=",", encoding="UTF-8")
        return dataframes

    def _init_players_elo_df(self) -> pd.DataFrame:
        """Initialize an empty DataFrame for players ELO."""
        return pd.DataFrame(columns=['player_id', 'season', 'elo'])

    def _init_season_valuations(self) -> dict:
        """Initialize season valuations (e.g., average and standard deviation of player values)."""
        season_valuations = {}
        if self.player_valuations_df is not None:
            for season, group in self.player_valuations_df.groupby('season'):
                season_valuations[season] = {
                    'mean': group['market_value_in_eur'].mean(),
                    'std': group['market_value_in_eur'].std()
                }
        return season_valuations

    def _fill_season_gaps(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fill season gaps for each player individually, ensuring each player has continuous season entries
        from their minimum to maximum season.
        """
        # Check for required columns
        if 'player_id' not in df.columns or 'season' not in df.columns:
            raise ValueError("Dataframe must contain 'player_id' and 'season' columns.")

        # Store original data types
        original_dtypes = df.dtypes

        # Store columns to preserve other than `elo`
        other_columns = df.columns.difference(['elo']).tolist()

        # Create a list to store filled data for each player
        filled_dfs = []

        # Process each player individually
        for player_id, group in df.groupby('player_id'):
            min_season, max_season = group['season'].min(), group['season'].max()
            if pd.isna(min_season) or pd.isna(max_season):
                continue

            # Reindex seasons to fill the gaps
            group = group.set_index('season')
            df_filled = group.reindex(np.arange(min_season, max_season + 1))

            # Forward fill missing values
            df_filled = df_filled.ffill()

            # Reset index and restore player_id
            df_filled = df_filled.reset_index()
            df_filled['player_id'] = player_id

            # Append the filled data for this player
            filled_dfs.append(df_filled)

        # Concatenate all filled data into one DataFrame
        filled_df = pd.concat(filled_dfs, ignore_index=True)

        # Restore original data types
        for col in filled_df.columns:
            if col in original_dtypes:
                filled_df[col] = filled_df[col].astype(original_dtypes[col])

        return filled_df

    def is_enough_data_to_init_elo(self, player_id: int) -> bool:
        """
        Check if there is enough data to initialize ELO for a given player.
        """
        player_data = self.player_valuations_df[self.player_valuations_df['player_id'] == player_id]
        return len(player_data) > 0

    def calculate_initial_elo(self, player_id: int) -> float:
        """
        Calculate the initial ELO for a player based on their market value.
        """
        player_data = self.player_valuations_df[self.player_valuations_df['player_id'] == player_id]
        if player_data.empty:
            return self.base_elo

        # Use the latest available market value
        latest_valuation = player_data.sort_values(by='date', ascending=False).iloc[0]
        market_value = latest_valuation['market_value_in_eur']

        # Normalize market value to calculate ELO
        mean = self.season_valuations[latest_valuation['season']]['mean']
        std = self.season_valuations[latest_valuation['season']]['std']
        if std == 0:
            return self.base_elo

        z_score = (market_value - mean) / std
        elo = self.base_elo + z_score * self.elo_range
        return max(0, elo)  # Ensure ELO is not negative

    def update_player_elo(self, player_id: int, season: int, new_elo: float):
        """
        Update the ELO of a player for a specific season.
        """
        if 'player_id' not in self.players_elo_df.columns or 'season' not in self.players_elo_df.columns:
            raise ValueError("Players ELO DataFrame must contain 'player_id' and 'season' columns.")

        # Update or insert the ELO value
        condition = (self.players_elo_df['player_id'] == player_id) & (self.players_elo_df['season'] == season)
        if condition.any():
            self.players_elo_df.loc[condition, 'elo'] = new_elo
        else:
            new_row = {'player_id': player_id, 'season': season, 'elo': new_elo}
            self.players_elo_df = pd.concat([self.players_elo_df, pd.DataFrame([new_row])], ignore_index=True)

    def init_all_players_elo(self) -> pd.DataFrame:
        """Initialize ELO for all players."""
        for player_id in self.players_df['player_id'].unique():
            if self.is_enough_data_to_init_elo(player_id):
                initial_elo = self.calculate_initial_elo(player_id)
                latest_season = self.player_valuations_df[self.player_valuations_df['player_id'] == player_id][
                    'season'].max()
                self.update_player_elo(player_id, latest_season, initial_elo)

        # Fill season gaps for all players
        self.players_elo_df = self._fill_season_gaps(self.players_elo_df)
        return self.players_elo_df


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir.parents[0] / 'data' / 'transfer_data'
    df = pd.read_csv(os.path.join(data_dir, 'players_elo.csv'))
    initializer = PlayerEloInitializer(base_dir=base_dir)
    res = initializer._fill_season_gaps(df)
    data_path = os.path.join(data_dir, 'players_elo_copy.csv')
    res.to_csv(data_path, index=False)
