import streamlit as st
from toelo.player_elo.display_data import get_player_data, plot_top_elo_players


def display_player_data():
    st.title("Player Data")
    st.plotly_chart(plot_top_elo_players())

    query = "SELECT * FROM players_elo LIMIT 200;"
    data = get_player_data(query)
    st.dataframe(data)


st.set_page_config(page_title="Display Player Data", page_icon="📊")

st.markdown("# Display Player Data")
st.sidebar.header("Display Player Data")

display_player_data()


# Streamlit widgets automatically run the script from top to bottom. Since
# this button is not connected to any other logic, it just causes a plain
# rerun.
st.button("Re-run")
