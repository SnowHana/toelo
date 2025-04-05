# from pandas import DataFrame
import altair as alt
import pandas as pd
import streamlit as st
from toelo.player_elo.display_data import (
    get_indiv_player_elo_data,
    get_player_data,
    get_player_names,
    plot_top_elo_players,
)


def toggle_button(key: str, value: bool = True):
    st.session_state[key] = value


def get_player_name_q():
    player_name_q = st.text_input(
        "Enter the player name you want to search:",
    )
    st.write("Player name to search: ", player_name_q)

    st.button(
        "Confirm player name to search",
        on_click=toggle_button,
        args=("search_player_button_clicked", True),
    )

    return player_name_q


def draw_line_graphs(df_list: list[pd.DataFrame], ELO_OFFSET: int = 300) -> alt.Chart:
    """Draw a line graph of players ELO by season

    Args:
        df_list (list[pd.DataFrame]): _description_
        ELO_OFFSET (int, optional): _description_. Defaults to 300.

    Returns:
        alt.Chart: _description_
    """
    ELO_OFFSET = 300

    df = pd.concat(df_list)
    df.dropna(subset=["elo"], inplace=True)
    df = df.sort_values(by=["name", "season"], ascending=True)
    # sort_by_elo = df.sort_values('elo', ascending=True)
    # sort_by_elo['name_season'] = sort_by_elo['name'] + " - " + sort_by_elo['season'].astype(str)

    df["season"] = pd.to_datetime(df.season, format="%Y")
    chart_df = df[["season", "elo", "name"]]

    season_boundary = [min(chart_df["season"]), max(chart_df["season"])]
    elo_boundary = [
        min(chart_df["elo"]) - ELO_OFFSET,
        max(chart_df["elo"]) + ELO_OFFSET,
    ]

    # chart = (
    #     alt.Chart(chart_df)
    #     .mark_line(point=True)
    #     .encode(
    #         x=alt.X(
    #             "season:T",
    #             scale=alt.Scale(domain=season_boundary),
    #             axis=alt.Axis(format="%Y", title="Season"),
    #         ),
    #         y=alt.Y(
    #             "elo:Q",
    #             scale=alt.Scale(domain=elo_boundary),
    #             axis=alt.Axis(title="ELO"),
    #         ),
    #         color="name:N",
    #     )
    # )

    chart = (
        alt.Chart(chart_df)
        .mark_line(point=True)
        .encode(
            x=alt.X("season:T", title="Season"),
            y=alt.Y("elo:Q", title="ELO", scale=alt.Scale(domain=elo_boundary)),
            # color=alt.value("blue"),  # Single color since only one player
            color="name:N",
            tooltip=["season:T", "elo:Q", "name:N"],
        )
    ).interactive()
    return chart


def get_exact_player_name(player_name_q: str):

    # if st.session_state.search_player_button_clicked:
    # if True:
    # Search dataframe to get list of possible player names match
    player_name_choices = get_player_names(player_name_q)
    # User select the exact player name
    player_name = st.selectbox("Select a player name: ", player_name_choices)
    st.write("You chose ", player_name, "!")

    return player_name


def display_player_elo():
    st.title("Individual Players' ELO")

    # session state
    for key in [
        "search_player_button_clicked",
        "player_name_button_clicked",
        "add_another_button_clicked",
        "confirmed_players_data",
    ]:
        if key not in st.session_state:
            st.session_state[key] = False if "data" not in key else []
    # st.write(st.session_state.add_another_button_clicked)
    # ================ PLAYER INPUT FLOW ================
    if (
        st.session_state["add_another_button_clicked"]
        or len(st.session_state["confirmed_players_data"]) <= 0
    ):
        # 1. Add another OR initially
        player_name_q = st.text_input(
            "Enter the player name you want to search:",
        )

        # 2. Get and confirm player name queue
        if st.button("🔎 Confirm Player name to search"):
            st.session_state.search_player_button_clicked = True
            st.session_state.player_name_q = player_name_q

            # DEBUG
            st.write("Player name to search: ", st.session_state.player_name_q)

        # 3. Search and confirm exact player name
        if st.session_state.search_player_button_clicked:
            # Queue
            player_name = get_exact_player_name(st.session_state.player_name_q)
            # Confirm exact name choice
            if st.button("✅ Confirm EXACT Player name to analyse"):
                st.session_state.player_name = player_name
                st.session_state.player_name_button_clicked = True

        # 4. Confirmed player to analyse, get data
        if st.session_state.player_name_button_clicked:
            df = get_indiv_player_elo_data(st.session_state.player_name)
            st.session_state.confirmed_players_data.append(df)

            # Lastly, reset buttons
            st.session_state.search_player_button_clicked = False
            st.session_state.player_name_button_clicked = False
            st.session_state.add_another_button_clicked = False

    # ================ DISPLAY DATA ================
    if st.session_state.confirmed_players_data:
        st.write("Players added so far: ")
        for df in st.session_state.confirmed_players_data:
            st.write(df.head(1))

        # Add another button
        # if st.button("Add another player to analyse"):
        #     st.session_state.add_another_button_clicked = True
        #     st.write(st.session_state.add_another_button_clicked)
        st.button(
            "🏃‍♂️ Add another player to analyse",
            on_click=toggle_button,
            args=("add_another_button_clicked",),
        )

        if st.button("📊 Create line chart to comapre"):
            chart = draw_line_graphs(st.session_state.confirmed_players_data)
            st.altair_chart(chart)


st.session_state.setdefault("df_list", [])

st.set_page_config(page_title="Display Individual Player Data", page_icon="📊")

st.markdown("# Display Individual Player Data")
st.sidebar.header("Display Individual Player Data")

display_player_elo()


# Streamlit widgets automatically run the script from top to bottom. Since
# this button is not connected to any other logic, it just causes a plain
# rerun.
st.button("Re-run")
