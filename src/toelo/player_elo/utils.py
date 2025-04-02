import os
from pathlib import Path

import pandas as pd

BASE_ELO = 1500
ELO_RANGE = 300


def import_data_from_csv() -> dict:
    """Read data from csv files (prepared by transfermrkt dataset)

    Returns:
        list[pd.DataFrame] : list of dataframes (single csv to single dataframe)
    """

    # NOTE: This wont work for jupyter so we are using sth else for now
    # # Get the absolute path of the current script (jupyter dir)

    # NOTE: Later when we are converting this into an actual python file, comment this line
    # Define the base and data directories
    BASE_DIR = Path(__file__).resolve().parent
    # BASE_DIR = Path.cwd()
    DATA_DIR = BASE_DIR.parents[0] / "data" / "transfer_data"
    # import all files in Data folder and read into dataframes
    dataframes = {}

    # Actual reading csv flies
    for dirpath, dirname, filenames in os.walk(DATA_DIR):
        for filename in filenames:
            file = filename.split(".")[0]
            # file = file[0] + "_df"
            if file != "":
                filepath = os.path.join(dirpath, filename)
                df = pd.read_csv(filepath, sep=",", encoding="UTF-8")
                # exec(f"{file} = df.copy()")
                print(file, df.shape)
                dataframes[file] = df.copy()
    print("Data imported")

    return dataframes


def add_season_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean up date to datetime datatype
    Add month_year, season column based on date
    @param df:
    @return:
    """
    # Clean up player valuations
    df_copy = df.copy()
    df_copy["date"] = pd.to_datetime(df_copy["date"])
    if "season" not in df_copy.columns:
        # df_copy['month_year'] = df_copy['date'].apply(lambda x: f"08 {x.year}" if x >= pd.Timestamp(x.year, 7, 1)\
        #     else f"08 {x.year-1}")
        df_copy["season"] = df_copy["date"].apply(
            lambda x: (
                f"{x.year}" if x >= pd.Timestamp(x.year, 7, 1) else f"{x.year - 1}"
            )
        )
    # df_copy = df_copy.loc[df_copy.groupby(['season'])['date'].idxmin()] #Get value only at start of season
    return df_copy


def sort_df_by_date(df: pd.DataFrame) -> pd.DataFrame:
    """Sort dataframe by date
    It handles changing the date to datetime format as well

    Args:
        df (pd.DataFrame): Assume club_games_df have "date"

    Returns:
        pd.DataFrame: _description_
    """

    # NOTE: This is why it might fail? Chagne to index or columns if this fails
    if "date" not in df.columns:
        raise ValueError("The 'date' column does not exist in the DataFrame.")

    df["date"] = df["date"].str.strip()
    df["date"] = pd.to_datetime(df["date"], errors="coerce", format="%Y-%m-%d")
    df.dropna(subset=["date"], inplace=True)
    # Sort by date
    df = df.sort_values(by=["date"])

    return df


# print(multiprocessing.cpu_count() - 1 or 1)
