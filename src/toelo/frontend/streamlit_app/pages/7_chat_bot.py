import streamlit as st
from toelo.frontend.streamlit_app.display_data import get_player_data
from langchain_community.llms import GPT4All
from pathlib import Path
from langchain_community.utilities import SQLDatabase
from toelo.player_elo.database_connection import get_connection_string, DATABASE_CONFIG

db_uri = get_connection_string(DATABASE_CONFIG)
print(db_uri)

db = SQLDatabase.from_uri(db_uri)
print(db.dialect)
print(db.get_usable_table_names())


# print(db.run("SELECT * FROM players_elo LIMIT 10;"))
# home = Path.home()
# model_path = Path.home() / Path("models") / "mistral-7b-openorca.Q4_0.gguf"
# print(model_path)
# model = GPT4All(model=str(model_path), n_threads=8)
# response = model.invoke("Once upon a time, ")

# print(response)
# def chat(query):
# query = """SELECT * FROM players_elo WHERE elo IS NOT NULL ORDER BY elo DESC LIMIT 200;"""


# st.set_page_config(page_title="ChatBot", page_icon="📊")

# st.markdown("# Have a chat")
# st.sidebar.header("Have a chat")

# prompt = st.text_input("Enter your prompt:")

# if st.button("Get Response"):
#     response = chat(prompt)
#     if response:
#         st.write(f"Response: {response}")
