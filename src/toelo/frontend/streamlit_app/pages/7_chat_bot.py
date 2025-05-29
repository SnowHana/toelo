import streamlit as st
from openai import OpenAI, api_key
from toelo.frontend.streamlit_app.display_data import get_player_data
import os
from dotenv import load_dotenv, dotenv_values

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")


def chat(query):
    # query = """SELECT * FROM players_elo WHERE elo IS NOT NULL ORDER BY elo DESC LIMIT 200;"""

    client = OpenAI(api_key=api_key)

    response = client.responses.create(model="gpt-4o", input=query)
    # st.markdown(response.output_text)
    return response.output_text


st.set_page_config(page_title="ChatBot", page_icon="📊")

st.markdown("# Have a chat")
st.sidebar.header("Have a chat")

prompt = st.text_input("Enter your prompt:")

if st.button("Get Response"):
    response = chat(prompt)
    if response:
        st.write(f"Response: {response}")
