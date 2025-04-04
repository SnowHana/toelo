import streamlit as st
from toelo.player_elo.display_data import (
    get_indiv_player_elo_data,
    get_player_data,
    get_player_names,
    plot_top_elo_players,
)


def display_player_elo():
    st.title("Individual Players' ELO")

    # To manage Show/Hide of player graph and player name selection box
    if "button_clicked" not in st.session_state:
        st.session_state.button_clicked = False

    def toggle_button():
        st.session_state.button_clicked = not st.session_state.button_clicked

    # Text input with a key so we can track it
    player_name_q = st.text_input(
        "Enter the player name you want to search:", key="player_name"
    )
    st.write("Player name ", player_name_q)

    st.button("Confirm", on_click=toggle_button)
    # Confirm button
    if st.session_state.button_clicked:
        player_name_choices = get_player_names(player_name_q)
        player_name = st.selectbox("Select a player name: ", player_name_choices)
        st.write("You chose ", player_name, "!")
        # Now get data of that player
        data = get_indiv_player_elo_data(player_name)
        st.line_chart(
            data=data,
            x="season",
            y="elo",
        )

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
