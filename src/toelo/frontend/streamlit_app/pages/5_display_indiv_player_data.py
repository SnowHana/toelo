import streamlit as st
from toelo.player_elo.display_data import (
    get_indiv_player_elo_data,
    get_player_data,
    get_player_names,
    plot_top_elo_players,
)


def toggle_button(button_name: str):
    # st.session_state.search_player_button_clicked = not st.session_state.search_player_button_clicked
    st.session_state[button_name] = not st.session_state[button_name]


def get_player_name_q(label_id: int):
    player_name_q = st.text_input(
        "Enter the player name you want to search:",
        key=f"name_q_{label_id}",
    )
    st.write("Player name ", player_name_q)

    st.button(
        "Confirm player name to search",
        on_click=toggle_button,
        args=("search_player_button_clicked",),
        key=f"search_button_{label_id}",
    )


def display_player_elo():
    st.title("Individual Players' ELO")

    # To manage Show/Hide of player graph and player name selection box
    if "search_player_button_clicked" not in st.session_state:
        st.session_state.search_player_button_clicked = False

    if "players_list_button_clicked" not in st.session_state:
        st.session_state.players_list_button_clicked = False

    # Enter list of player names
    data_list = []
    label_id = 0
    # while not st.session_state.players_list_button_clicked:
    #     # Text input with a key so we can track it
    #     player_name_q = st.text_input(
    #         "Enter the player name you want to search:",
    #         key=f"name_q_{label_id}",
    #     )
    #     st.write("Player name ", player_name_q)

    #     st.button(
    #         "Confirm player name to search",
    #         on_click=toggle_button,
    #         args="search_player_button_clicked",
    #         key=f"search_button_{label_id}",
    #     )

    # Get player name q
    player_name_q = get_player_name_q(label_id)

    if st.session_state.search_player_button_clicked:
        # Search dataframe to get list of possible player names match
        player_name_choices = get_player_names(player_name_q)
        # User select the exact player name
        player_name = st.selectbox("Select a player name: ", player_name_choices)
        st.write("You chose ", player_name, "!")
        # Append  to data list...
        data = get_indiv_player_elo_data(player_name)
        data_list.append(data)

        # Confirm if this is all we need.
        st.button(
            "Confirm Players to compare ELO",
            on_click=toggle_button,
            args=("players_list_button_clicked",),
            key=f"players_list_{label_id}",
        )

        # Lastly toggle player search button
        toggle_button("search_player_button_clicked")
        label_id += 1

    if st.session_state.players_list_button_clicked:
        # Confirm players list
        # Now get data of that player
        # Uhm chart...
        st.write("CHART GOES HERE")
        # st.line_chart(
        #     data=data,
        #     x="season",
        #     y="elo",
        # )

        # If this button is clicked, our button will be true...

    else:
        st.write("Click the button to see something special.")

    #     st.session_state["confirmed_name"] = st.session_state["player_name"]

    # # Show result if confirmed
    # if "confirmed_name" in st.session_state:
    #     st.write("Current name is:", st.session_state["confirmed_name"])
    # Search database to get candidates of player_names
    # st.write("SUCCESS")
    # chart_data = pd.DataFrame(
    #     {
    #         "col1": np.random.randn(20),
    #         "col2": np.random.randn(20),
    #         "col3": np.random.choice(["A", "B", "C"], 20),
    #     }
    # )

    # st.line_chart(chart_data, x="col1", y="col2", color="col3")


st.set_page_config(page_title="Display Individual Player Data", page_icon="📊")

st.markdown("# Display Individual Player Data")
st.sidebar.header("Display Individual Player Data")

display_player_elo()


# Streamlit widgets automatically run the script from top to bottom. Since
# this button is not connected to any other logic, it just causes a plain
# rerun.
st.button("Re-run")
