from matplotlib import pyplot as plt
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from io import StringIO
import os
import time


class Scrape:
    def __init__(self) -> None:
        self.standings_url = "https://fbref.com/en/comps/9/Premier-League-Stats"

        self.team_urls = None
        self.__init_team_urls()

        self.squad_dfs = None
        self.__init_squad_dfs()

        self.player_df = None
        self.__init_player_df()

        self.squad_avg_df = None
        self.__init_avg_squad_df()

    def __init_team_urls(self) -> None:
        """Initialise and set team urls

        Args:

        Returns:
            None
        """
        data = requests.get(self.standings_url)
        soup = BeautifulSoup(data.text, features="lxml")
        standings_table = soup.select("table.stats_table")[0]

        # links store href of each team
        links = standings_table.find_all("a")
        links = [l.get("href") for l in links]
        links = [l for l in links if "/squads/" in l]

        self.team_urls = [f"https://fbref.com{l}" for l in links]

    def __init_squad_dfs(self) -> None:
        """Initialise and set squad_dfs"""

        squad_dfs = []

        for team_url in self.team_urls:
            data = requests.get(team_url)
            squads = pd.read_html(StringIO(data.text), match="Standard Stats")[0]
            squads = squads.droplevel(level=0, axis=1)

            # Get team name
            team_name = team_url.split("/")[-1].replace("-Stats", "").replace("-", " ")
            # Add a column team_name
            squads["team"] = team_name

            # Change index to lower case
            squads.columns = [c.lower() for c in squads.columns]
            squad_dfs.append(squads)

            time.sleep(1)

        self.squad_dfs = squad_dfs

    def __init_player_df(self) -> None:
        dfs_modified = []

        # Remove the last two rows from each DataFrame and append them to dfs_modified
        for df in self.squad_dfs:
            df_modified = df.iloc[:-2]  # Exclude the last two rows
            dfs_modified.append(df_modified)

        # Concatenate the modified DataFrames into a single DataFrame
        player_df = pd.concat(dfs_modified, ignore_index=True)

        self.player_df = player_df

    def __init_avg_squad_df(self) -> None:
        # Store avg info
        squad_avg_rows = []
        for df in self.squad_dfs:
            squad_avg_row = df.iloc[-2]
            squad_avg_rows.append(squad_avg_row)
        # Concatenate squad infos to a single df
        squad_avg_df = pd.concat(squad_avg_rows, axis=1).T
        # Remove columns with NaN values
        squad_avg_df = squad_avg_df.dropna(axis=1)
        squad_avg_df.set_index("team", inplace=True)

        self.squad_avg_df = squad_avg_df

    def store_info_to_csv(self):
        """Store squad info into 2 separate csv files.
        squad_avg.csv : will store avg info about squad
        squad.csv : will store info about players in all teams
        """
        self.player_df.to_csv("squad.csv", index=True)
        self.squad_avg_df.to_csv("squad_avg.csv", index=True)


class Squad:
    def __init__(self) -> None:
        # Check if csv file exists
        # NOTE: this will break if cwd changes....
        squad_path = "./squad.csv"
        squad_avg_path = "./squad_avg.csv"
        if not (os.path.isfile(squad_path) and os.path.isfile(squad_avg_path)):
            # File doesnt exist
            try:
                s = Scrape()
                s.store_info_to_csv()
            except:
                print("Error: Scraping didn't work properly.")
                exit(1)
            else:
                print("#######################################")
                print("Scraping process executed successfully.")
                print("#######################################")

        # File exists
        self.squad_avg_df = pd.read_csv(squad_avg_path, index_col=0)

    def squad_avg_df(self):
        return self.squad_avg_df

    def avg_feature_graph(self, feature: str):
        """Display avg graph of feature user selects

        Args:
            feature (str): feature
        """

        done = False

        while not done:
            if feature not in self.squad_avg_df.columns:
                feature = input("Type in valid feature")
            else:
                done = True

        self.squad_avg_df[feature] = self.squad_avg_df[feature].astype(float)
        ax = self.squad_avg_df[feature].plot(kind="bar", color="lightgreen")

        # Set the title and labels
        plt.title(f"Average {feature} of Players by Team")
        plt.xlabel("Team")
        plt.ylabel(f"Average {feature}")

        # for i, val in enumerate(df['age']):
        #     ax.text(i, val, str(val), ha='center', va='bottom')
        # plt.xticks(rotation=0)
        # Show the plot
        plt.show()

    def max_min_info(self):
        # Squad max min info
        infos = ["age", "gls", "ast", "g+a", "xg", "prgc"]

        print("Showing General Info about Premier League teams.")
        for info in infos:
            team_max_avg_age = self.squad_avg_df[info].idxmax()
            max_avg_age = self.squad_avg_df.loc[team_max_avg_age, info]

            team_min_avg_age = self.squad_avg_df[info].idxmin()
            min_avg_age = self.squad_avg_df.loc[team_min_avg_age, info]
            print(f"Max {info}: {team_max_avg_age} ({max_avg_age})")
            print(f"Min {info}: {team_min_avg_age} ({min_avg_age})")
            print("")


s = Squad()
# s.get_squad_df()
# s.avg_age_graph()

# s.squad_avg_df().columns
s.avg_feature_graph("")
s.max_min_info()
