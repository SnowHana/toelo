# %%
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import matplotlib.pyplot as plt
from io import StringIO

# %%

squad_df = pd.read_csv("squad.csv", index_col=0)

# %%

squad_df

# %%
squad_df


# %%
def squad_ages_df() -> pd.DataFrame:
    squad_rows = []
    for df in squad_dfs:
        squad_row = df.iloc[-2]
        squad_rows.append(squad_row)
    # Concatenate squad infos to a single df
    squad_df = pd.concat(squad_rows, axis=1).T
    # Remove columns with NaN values
    squad_df = squad_df.dropna(axis=1)
    squad_df.set_index("team", inplace=True)

    return squad_df


# %%


def plot_squad_ages() -> None:
    team_urls = get_team_urls(standings_url)
    squad_dfs = get_squad_dfs(team_urls)
    squad_df = squad_ages_df(squad_dfs)

    squad_df["age"] = squad_df["age"].astype(float)

    ax = squad_df["age"].plot(kind="bar", color="lightgreen")

    plt.title("Average Age of Players by Team")
    plt.xlabel("Team")
    plt.ylabel("Average Age")

    # for i, val in enumerate(df['age']):
    # ax.text(i, val, str(val), ha='center', va='bottom')
    # plt.xticks(rotation=0)
    plt.show()


store_squad_dfs()
# plot_squad_ages()
