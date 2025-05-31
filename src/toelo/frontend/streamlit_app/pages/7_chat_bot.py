import streamlit as st
from toelo.chatbot.agent_chat_bot import AgentChatBot


def toggle_button(key: str, value: bool = True):
    st.session_state[key] = value


def ask_chatbot():
    if not st.session_state.q:
        q = st.text_input("Ask a question!: ")
        st.button("Confirm question", on_click=toggle_button, args=("q", q))
    else:
        res = st.session_state.agent.ask_question(st.session_state.q)
        st.write(res[-1])
        if st.button("Show entire step"):
            for c in res:
                st.write(c)


st.set_page_config(page_title="Ask AI", page_icon="📊")

st.markdown("# Ask AI")
st.sidebar.header("Ask AI")

# Init q and chat model
if "q" not in st.session_state:
    st.session_state.q = False

if "agent" not in st.session_state:
    st.session_state.agent = AgentChatBot()

ask_chatbot()
