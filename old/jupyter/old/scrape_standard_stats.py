from urllib.request import Request, urlopen
from urllib.error import URLError
from bs4 import BeautifulSoup
import time
import pandas as pd
import random

STANDINGS_URL = "https://fbref.com/en/comps/9/Premier-League-Stats"
BIG5_PLYAERS_URL = "https://fbref.com/en/comps/Big5/2023-2024/stats/players/2023-2024-Big-5-European-Leagues-Stats"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
]


# Scrape data, use Request
class Scrape:
    """ """

    def __init__(self, standings_url, sleep_time=2) -> None:
        # self.headers = {
        #     "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36",
        #     "Accept-Language": "en-US,en;q=0.5",
        #     "Referer": "http://google.com",  # Optional, mimics the referer if needed
        #     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        #     "Connection": "keep-alive",  # Helps maintain a persistent connection
        # }
        self.sleep_time = sleep_time
        self.standings_url = standings_url
        self.team_urls = None

    def _fetch_standings_page(self, url: str) -> Request:
        tries = 3  # Number of retries
        for attempt in range(tries):
            try:
                req = Request(
                    url,
                    headers={
                        "User-Agent": random.choice(USER_AGENTS),
                        "Accept-Language": "en-US,en;q=0.5",
                        "Referer": "http://google.com",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                        "Connection": "keep-alive",
                    },
                )
                return urlopen(req).read()
            except URLError as e:
                print(f"Error fetching URL: {url}, Error: {e}")
                if attempt < tries - 1:
                    print("Retrying...")
                    time.sleep(self.sleep_time)  # Wait before retrying
                else:
                    print("Max retries reached. Skipping.")
                    return None

    # def _fetch_html(self, url: str):
    #     res = self._fetch_standings_page(url)
    #     return urlopen(res).read()

    def _parse_standings_page(self, url: str) -> BeautifulSoup:
        html_page = self._fetch_standings_page(url)
        soup = BeautifulSoup(html_page, "html.parser")

        return soup

    def get_teams_urls(self, url: str) -> None:
        soup = self._parse_standings_page(url)

        try:
            standings_table = soup.select("table.stats_table")[0]
            links = standings_table.find_all("a")
            links = [l.get("href") for l in links]
        except IndexError:
            print("Error: Could not find standings table index.")
            return []
        links = [l for l in links if "/squads/" in l]
        team_urls = [f"https://fbref.com{l}" for l in links]
        self.team_urls = team_urls

    def _get_player_urls(self, team_url: str) -> list[str]:
        soup = self._parse_standings_page(team_url)
        # NOTE: This could break if fbref changes their html code
        table = soup.find("table", {"id": "stats_standard_9"})
        # headers= [th.get_text() for th in table.find_all('th')]
        links = []

        # Extract link
        for tr in table.find_all("tr")[1:]:  # Skip the header row
            # cells = [td.get_text() for td in tr.find_all('td')]
            link = tr.find("a", href=True)["href"] if tr.find("a", href=True) else None
            link = f"https://fbref.com{link}" if link else None
            links.append(link)  # Append the link to the row

        # First link is none
        links = links[1:]

        return links

    def _scrape_team_ss(self, team_url) -> pd.DataFrame:

        team_name = team_url.split("/")[-1].replace("-Stats", "").replace("-", " ")
        links = self._get_player_urls(team_url)

        ss_df = pd.read_html(
            self._fetch_standings_page(team_url), match="Standard Stats"
        )[0]
        ss_df.columns = ss_df.columns.droplevel()
        ss_df["Link"] = links
        # Add a team name
        ss_df["Team"] = team_name

        # So that we dont get banned...
        time.sleep(self.sleep_time)

        return ss_df

    def scrape_all_teams_ss(self) -> pd.DataFrame:
        # Set self.team_urls if None
        if self.team_urls is None:
            self.get_teams_urls(self.standings_url)

        if not self.team_urls:
            print("No team URLs found, returning an empty DataFrame.")
            return pd.DataFrame()

        ss_dfs = [self._scrape_team_ss(url) for url in self.team_urls]
        return pd.concat(ss_dfs)

    def _add_per_90s_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add -90 tag to column standing for a per 90 stats
        Assume that first half stands for entire season stat, and last half stands for per 90s stat


        Args:
            df (pd.DataFrame): _description_

        Returns:
            pd.DataFrame: modified column index
        """

        duplicate_columns = df.columns[df.columns.duplicated()]
        occured = []
        cols = []
        count = 1
        stat_90s = False
        for column in df.columns:
            if not stat_90s:
                if column in duplicate_columns and column in occured:
                    # Means we are now in 90s stats
                    cols.append(f"{column}-90")
                    continue
                else:
                    occured.append(column)
                    cols.append(column)
            else:
                cols.append(f"{column}-90")

        df.columns = cols

        return df

    def scrape_big5_players_ss(self, big5_url) -> pd.DataFrame:
        """Scrape big 5 players standard stats data from fbref

        Args:
            big5_url (_type_): fbref url of big5 players standard stats

        Returns:
            pd.DataFrame: _description_
        """

        html_page = self._fetch_standings_page(big5_url)
        # soup = self._parse_standings_page(big5_url)
        try:
            df = pd.read_html(html_page)[0]
            df.columns = df.columns.droplevel()
            # Drop Rk Player Natio etc stuff
            df = df[df["Rk"] != "Rk"]
            # Drop first RK row cuz we dont really need it
            df = df.drop("Rk", axis=1)
            # Make index cts
            df.reset_index(drop=True, inplace=True)

            # Drop Match column cuz they dont do anything atm
            df = df.drop("Matches", axis=1)

            # Add -90 to per 90s stat
            df = self._add_per_90s_columns(df)

            # Save it to csv
            df.to_csv("standard_stats_big5.csv")
        except Exception as e:
            print(f"ERROR: Sth went wrong during cleaning df {e}")

        return df

    def save_csv(self, file_path: str = "standard_stats.csv") -> None:
        try:
            self.scrape_all_teams_ss().to_csv(file_path)
            print(f"Data saved to {file_path}.")
        except Exception as e:
            print(f"Error saving file {file_path}: {e}")


scraper = Scrape(STANDINGS_URL, 2)
# scraper.get_teams_urls()
# res = scraper._scrape_team_ss("https://fbref.com/en/squads/8602292d/Aston-Villa-Stats")
# print(res)
scraper.scrape_big5_players_ss(BIG5_PLYAERS_URL)
