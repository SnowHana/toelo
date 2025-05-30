from pathlib import Path
import gpt4all
import streamlit as st
from typing_extensions import TypedDict
from langchain_community.utilities import SQLDatabase
from langchain_community.llms import GPT4All

from toelo.frontend.streamlit_app.display_data import get_player_data
from toelo.player_elo.database_connection import get_connection_string, DATABASE_CONFIG


db_uri = get_connection_string(DATABASE_CONFIG)
print(db_uri)

db = SQLDatabase.from_uri(db_uri)
print(db.dialect)
print(db.get_usable_table_names())


class State(TypedDict):
    question: str
    query: str
    result: str
    answer: str


from langchain.chat_models import init_chat_model

# Chat model
llm_path = Path.home() / Path("models") / "mistral-7b-openorca.Q4_0.gguf"
llm = GPT4All(model=str(llm_path), n_thread=8)

# Toolkit

# print(db.run("SELECT * FROM players_elo LIMIT 10;"))
# home = Path.home()
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
