import pandas as pd
from pathlib import Path
import os
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

# Define the base and data directories
BASE_DIR = Path.cwd()
DATA_DIR = BASE_DIR.parents[0] / "transfer_data"
CLUBS_FILE = "clubs.csv"
ELOS_FILE = "club_elos.csv"

# Load CSV data
clubs_df = pd.read_csv(os.path.join(DATA_DIR, CLUBS_FILE), sep=",", encoding="UTF-8")
elos_df = pd.read_csv(os.path.join(DATA_DIR, ELOS_FILE), sep=",", encoding="UTF-8")
elos_df = elos_df.head(632)  # Restrict the ELO data to the first 632 rows


# Define the fuzzy merge function
def fuzzy_merge(
    df_1, df_2, key1, key2, threshold=90, limit=2, scorer=fuzz.partial_ratio
):
    """
    Fuzzy merge two dataframes based on a similarity score.
    """
    s = df_2[key2].tolist()
    m = df_1[key1].apply(lambda x: process.extract(x, s, limit=limit, scorer=scorer))
    df_1["matches"] = m
    df_1["matches"] = df_1["matches"].apply(
        lambda x: ", ".join([i[0] for i in x if i[1] >= threshold])
    )

    df_1 = df_1.set_index(list(df_1)[0])
    df_1 = df_1.reset_index(drop=True)
    return df_1


# Initialize the unmatched dataframe
unmatched_df = elos_df.copy()

# Define different configurations for fuzzy_merge
configurations = [
    {"threshold": 85, "limit": 1, "scorer": fuzz.partial_ratio},
    {"threshold": 80, "limit": 1, "scorer": fuzz.partial_ratio},
    {"threshold": 75, "limit": 1, "scorer": fuzz.partial_ratio},
]

# Loop through each configuration and perform fuzzy matching
all_results = []
counter = 0
for config in configurations:
    # Perform fuzzy merge
    matched_df = fuzzy_merge(
        unmatched_df.copy(),
        clubs_df,
        "Club",
        "name",
        threshold=config["threshold"],
        limit=config["limit"],
        scorer=config["scorer"],
    )

    # Save the intermediate results for each iteration
    # Reset index
    # matched_df = matched_df.set_index(list(matched_df)[0])
    # matched_df = matched_df.reset_index(drop=True)
    # print(matched_df.columns)
    matched_df.to_csv(
        f"match_V{counter}.csv",
        index=True,
    )
    counter += 1

    # Filter out matched rows
    matched_clubs = matched_df[matched_df["matches"] != ""]
    matched_names = matched_clubs["matches"].str.split(", ").explode().unique()

    # Remove matched clubs from clubs_df and unmatched_df
    clubs_df = clubs_df[~clubs_df["name"].isin(matched_names)]
    unmatched_df = unmatched_df[~unmatched_df["Club"].isin(matched_clubs["Club"])]

    # Append current iteration's matched results to all_results
    all_results.append(matched_clubs)

# Combine all matched results and save
final_result = pd.concat(all_results, ignore_index=True)
final_result.to_csv("final_match.csv", index=False)

# Save unmatched entries
unmatched_df.to_csv("unmatched.csv", index=False)


# import pandas as pd
# from pathlib import Path
# import time
# import os

# from fuzzywuzzy import fuzz
# from fuzzywuzzy import process


# BASE_DIR = Path.cwd()

# # Build the path to the data directory
# DATA_DIR = BASE_DIR.parents[0] / "transfer_data"
# CLUBS_FILE = "clubs.csv"
# ELOS_FILE = "club_elos.csv"
# # res.to_csv(DATA_DIR / 'club_elos.csv')


# filepath = os.path.join(DATA_DIR, CLUBS_FILE)
# clubs_df = pd.read_csv(filepath, sep=",", encoding="UTF-8")
# elos_df = pd.read_csv(os.path.join(DATA_DIR, ELOS_FILE), sep=",", encoding="UTF-8")
# elos_df = elos_df.head(632)


# def fuzzy_merge(
#     df_1, df_2, key1, key2, threshold=90, limit=2, scorer=fuzz.partial_ratio
# ):
#     """
#     :param df_1: the left table to join
#     :param df_2: the right table to join
#     :param key1: key column of the left table
#     :param key2: key column of the right table
#     :param threshold: how close the matches should be to return a match, based on Levenshtein distance
#     :param limit: the amount of matches that will get returned, these are sorted high to low
#     :return: dataframe with both keys and matches
#     """
#     s = df_2[key2].tolist()

#     m = df_1[key1].apply(lambda x: process.extract(x, s, limit=limit, scorer=scorer))
#     df_1["matches"] = m

#     m2 = df_1["matches"].apply(
#         lambda x: ", ".join([i[0] for i in x if i[1] >= threshold])
#     )
#     df_1["matches"] = m2

#     return df_1


# # def fuzzy_merge2(df_1, df_2, key1, key2, threshold=90, limit=2):
# #     """
# #     :param df_1: the left table to join
# #     :param df_2: the right table to join
# #     :param key1: key column of the left table
# #     :param key2: key column of the right table
# #     :param threshold: how close the matches should be to return a match, based on Levenshtein distance
# #     :param limit: the amount of matches that will get returned, these are sorted high to low
# #     :return: dataframe with both keys and matches
# #     """
# #     s = df_2[key2].tolist()

# #     m = df_1[key1].apply(lambda x: process.extract(x, s, limit=limit, scorer=))
# #     df_1["matches"] = m

# #     m2 = df_1["matches"].apply(
# #         lambda x: ", ".join([i[0] for i in x if i[1] >= threshold])
# #     )
# #     df_1["matches"] = m2

# #     return df_1


# temp_elos_df = elos_df.copy().head(5)
# # df_result = fuzzy_merge(temp_elos_df, clubs_df, "Club", "name", threshold=85, limit=1)
# # df_unmatched = pd.concat([df_result["matches"], temp_elos_df["Club"]]).drop_duplicates(
# #     keep=False
# # )


# df_result = fuzzy_merge(elos_df, clubs_df, "Club", "name", threshold=85, limit=5)
# df_result.to_csv("match.csv")

# unmatched_df = df_result[df_result[["matches"]].isin(["NaN", 0, ""]).all(axis=1)]
# unmatched_df = unmatched_df.reset_index(drop=True)
# unmatched_df.to_csv("unmatched.csv")
# # df_unmatched.to_csv("unmatched.csv")
# # Example usage of fuzzy_merge

# # Identify unmatched teams

# # df_result.to_csv("match2.csv")
